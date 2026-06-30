# Phase 0 Research: getOrgCapturingStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/utilities/GET_orgs_org_id_pcaps_capture.md`
(enriched OpenAPI doc for `GET /api/v1/orgs/{org_id}/pcaps/capture`).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.pcaps.capture.getOrgCapturingStatus(apisession,
org_id)`. The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not a list, not paginated).
Required path parameter: `org_id` (UUID string). No query parameters. No request body.

Top-level response keys per the enriched doc (200 OK):

- `id` (string UUID, readOnly, REQUIRED) -- unique capture instance id.
- `type` (string enum, REQUIRED) -- one of `client`, `gateway`, `new_assoc`,
  `radiotap`, `radiotap,wired`, `wired`, `wireless`.
- `format` (string) -- `stream` (to Mist cloud) or `tzsp` (to remote Wireshark host).
- `ap_mac` (string|null), `client_mac` (string|null), `ssid` (string|null).
- `duration` (int seconds), `started_time` (int epoch seconds).
- `max_num_packets` (int), `max_pkt_len` (int), `num_packets` (int), `includes_mcast`
  (bool).
- `aps` (string[]) -- target AP MACs; `failed` (string[]) -- APs whose config attempt
  failed; `ok` (string[]) -- APs successfully configured.
- `switches` (string[]), `gateways` (string[]), `mxedges` (string[]).
- `tcpdump_expression`, `radiotap_tcpdump_expression`, `scan_tcpdump_expression`,
  `wired_tcpdump_expression`, `wireless_tcpdump_expression` (strings; only the ones
  matching the active `type` are populated).
- `tzsp_host` (string), `tzsp_port` (int 1-65535) -- only when `format=tzsp`.
- `pcap_aps` (object) -- map keyed by AP MAC -> nested object
  `{band, bandwidth, channel, tcpdump_expression}`. This nested map is the
  per-AP technical detail and must be flattened to its own table.

404 Behavior (from Gotchas section of enriched doc): "Returns 404 if no capture is
currently active." MistHelper treats this as a benign WARNING and writes zero rows.

**Rationale**:
The spec.md names the SDK path as `mistapi.api.v1.orgs.pcaps.capture` (URL-based).
The enriched per-endpoint doc lists `mistapi.api.v1.utilities.pcaps.getOrgCapturingStatus()`
under the `Utilities PCAPs` OpenAPI tag. The mistapi SDK historically organizes
modules by URL path, not OpenAPI tag (verified by adjacent endpoints under the same
URL: `POST /api/v1/orgs/{org_id}/pcaps/capture` ->
`mistapi.api.v1.orgs.pcaps.capture`, `DELETE /api/v1/orgs/{org_id}/pcaps/capture` ->
same). The spec.md is the authoritative feature contract and names the URL-based
path, so we follow it. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.pcaps import capture; help(capture)"` inside
the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/pcaps/capture`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`mistapi.api.v1.utilities.pcaps`).*
   Rejected -- the SDK organizes modules by URL path, not OpenAPI tag. The spec.md
   (authoritative) names the URL-based path. If the SDK truly exposes the function
   only under the `utilities` package on the installed `mistapi` version, the
   implementation imports both paths defensively (`try: ... except ImportError:`)
   but treats `mistapi.api.v1.orgs.pcaps.capture` as the canonical location.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural_pk** strategy on the capture instance UUID for the summary table,
and a **composite_pk** strategy on the per-AP detail table:

- `org_pcap_capture_status`: PK = `id` (the capture UUID supplied by the API).
  Indexes: `org_id`, `type`, `started_time`.
- `org_pcap_capture_status_aps`: PK = `(org_id, capture_id, ap_mac)` -- one row per
  target AP. `capture_id` is the parent summary's `id`; `ap_mac` is the dictionary
  key from `pcap_aps`. Indexes: `capture_id`, `ap_mac`.

Both tables receive `org_id` injected by MistHelper before the upsert (the Mist
response does not echo `org_id` back but MistHelper always knows which org the call
targeted -- the same pattern used by adjacent org-scope reads).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk` for the
summary and `composite_pk` for the per-AP detail.

**Rationale**:
The endpoint reports the *current* state of an active capture, identified by a
stable UUID `id` that is declared `readOnly` and is REQUIRED in the response schema
-- it does not change between polls of the same capture. Re-running the menu item
against the same org while a capture is in flight must update the existing summary
row rather than append duplicates, which `natural_pk` on `id` provides via `INSERT
OR REPLACE`. The nested `pcap_aps` map naturally produces one row per AP MAC; the
composite key `(org_id, capture_id, ap_mac)` guarantees uniqueness even if the same
AP MAC participates in captures across multiple orgs over the SQLite file's
lifetime.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots and defeats the upsert behavior the spec requires.
2. *`composite_pk` on `(org_id, id)` for the summary table.* Rejected -- `id` is
   already a Mist-generated UUID guaranteed unique across the platform, so adding
   `org_id` to the PK is redundant. `org_id` is kept as an index column for fast
   per-org filtering.
3. *Single combined table with all summary fields plus a nullable `ap_mac`.*
   Rejected -- when no per-AP detail is present (or when `pcap_aps` is absent in a
   future response variant), the design would require nullable PK columns and a
   sentinel value. Splitting into summary + detail tables keeps both clean.
4. *`natural_pk` on `id` for both tables (per-AP table keyed by a synthesized id).*
   Rejected -- the per-AP records have no Mist-supplied ID. Their natural key is the
   parent capture id plus the AP MAC.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_capturing_status.csv`
- CSV (per-AP detail): `data/org_<org_id_short>_capturing_status_aps.csv`
- SQLite tables: `org_pcap_capture_status` and `org_pcap_capture_status_aps`
- `org_id_short` is the first 8 hex characters of the org UUID -- the convention
  already used by adjacent org exports in MistHelper for human-readable filenames
  without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgCapturingStatus"` for the summary write and
`"getOrgCapturingStatusAps"` for the per-AP detail write. Both strings are the
lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other `PacketCaptureManager` outputs and by the
adjacent license / inventory exports under `data/`. Two output files / two SQLite
tables keep the schema clean and let an operator query the summary without joining
when they only need to know "is a capture running and what type". The
`getOrgCapturingStatusAps` operationId is MistHelper-internal -- Mist has no
distinct operationId for the per-AP sub-array; this is the same pattern used by
other endpoints whose response contains nested maps (see Plan 500 / data-model.md
for prior art).

**Alternatives Considered**:

1. *Single output file with JSON-encoded `pcap_aps` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else
   in MistHelper.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and `ls` output unnecessarily. The 8-character short form is enough to
   disambiguate locally.
3. *Filename `pcap_status` (shorter).* Rejected -- `capturing_status` matches the
   Mist operationId verbatim and makes grep across `data/` deterministic.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the top of the
Interactive Safe cluster (60-96) and directly below the Resource-Intensive block
that begins at 97. Category label: "Interactive Safe -- PCAPs". The menu method
lives on `PacketCaptureManager`, the class that already owns the start/stop org
PCAP menu items, so a NOC engineer scrolling the menu finds all PCAP operations
under one owner.

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive (which includes PCAP starts/stops at
134-135), 154-194 Destructive. This endpoint is a single GET that returns a small
JSON object describing whether a capture is active, prompts for one identifier
(`org_id`), and writes a small file -- it belongs in the safe / interactive-safe
range rather than the active-PCAP block at 134-135. Slot 96 is the highest
unallocated integer in the Interactive Safe cluster and is the natural home for the
read-only status check. The number is provisional: at `/speckit.tasks` time,
MistHelper.py is grep'd for the latest allocated menu integer and 96 is shifted
forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside the active-PCAP block (134-135).* Rejected -- those operations are
   active capture controls that briefly hold device resources. A passive status
   check has a different risk profile and should be visually grouped with the safe
   reads.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET with no pagination and a tiny payload. It is not resource-intensive.
3. *Append above the destructive cluster (195+).* Rejected -- placing a read-only
   status check above the destructive block at 194 visually mis-signals the risk
   level to a junior NOC engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_capturing_status:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log WARNING and return
   early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the prompt.

**Rationale**:
The endpoint is purely org-scoped (`/orgs/{org_id}/pcaps/capture`). There are no
query parameters, no site or device IDs, and no destructive confirmation. Asking
for a single value keeps the menu fast and matches the lightweight nature of a
status poll. Junior NOC engineers can leave `MIST_ORG_ID` set in `.env` and answer
every prompt by pressing Enter.

**Alternatives Considered**:

1. *Add an "include per-AP detail? (Y/n)" prompt to skip the second write when only
   the summary is needed.* Rejected -- the per-AP map is bounded by the AP count in
   the active capture (typically 1-20 APs, never more than a few hundred), so the
   write cost is negligible and the prompt would add keystrokes without
   operational value. The detail table is always populated when `pcap_aps` is
   non-empty.
2. *Add an output filename override prompt.* Rejected -- the deterministic
   `org_<short>_capturing_status[_aps]` naming scheme makes results easy to find
   under `data/` and prevents accidental clobbering of unrelated exports.
3. *Skip the prompt entirely when `MIST_ORG_ID` is set.* Rejected -- always prompt
   (with the env-var default pre-filled) so the operator always knows which org
   they targeted, in line with the safety-first principle.
