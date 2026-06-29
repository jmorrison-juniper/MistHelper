# Phase 0 Research: countOrgWirelessClients

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format. No item is left as
NEEDS CLARIFICATION; every open question is answered here.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_clients_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK using the canonical URL-aligned module path:
`mistapi.api.v1.orgs.clients.count.countOrgWirelessClients(apisession, org_id,
distinct=None, mac=None, hostname=None, device=None, os=None, model=None, ap=None,
vlan=None, ssid=None, ip=None, start=None, end=None, duration="1d", limit=100)`.

The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed JSON body.
The body is a single JSON object (NOT a list, NOT paginated in the search sense) with the
following top-level keys per the enriched doc:

- `distinct` (string) -- echoes the grouping attribute the caller requested.
- `start` (int32, epoch seconds) -- inclusive start of the time window the API actually
  used.
- `end` (int32, epoch seconds) -- exclusive end of the time window the API actually used.
- `limit` (int32) -- maximum bucket count returned (defaults to 100).
- `total` (int32) -- total number of distinct buckets matched (may exceed `limit`).
- `results` (array of `count_result` objects) -- each item has a required `count` field
  plus `additionalProperties: string` carrying the bucket label (e.g., `{count: 17,
  ssid: "Corp-Guest"}` when `distinct=ssid`).

Path parameter: `org_id` (UUID string, required).

Query parameters (all optional, see contract for full table): `distinct`, `mac`,
`hostname`, `device`, `os`, `model`, `ap`, `vlan`, `ssid`, `ip`, `start`, `end`,
`duration` (default `1d`), `limit` (default 100).

**Rationale**:
The enriched per-endpoint doc records the SDK as
`mistapi.api.v1.orgs.clients_-_wireless.countOrgWirelessClients()`. That literal module
name (`clients_-_wireless` with a hyphen and underscores) is not a legal Python
identifier and reflects the OpenAPI *tag* rather than the URL path. The mistapi SDK
generates module paths from the URL, not the tag (confirmed by spec.md naming
`mistapi.api.v1.orgs.clients.count` and by adjacent endpoints under
`/orgs/{org_id}/clients/...` living in `mistapi.api.v1.orgs.clients`). The spec.md is the
authoritative contract for this feature, so we follow it. Final verification at
implementation time via `python -c "from mistapi.api.v1.orgs.clients import count;
help(count)"` inside the venv; if the SDK actually places the function elsewhere (e.g.,
under `mistapi.api.v1.orgs.clients_wireless`), the import is corrected and the
remaining design holds unchanged.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/orgs/{org_id}/clients/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the tag-derived module path (`...clients_-_wireless...`).* Rejected -- the
   hyphen makes it not a valid Python identifier, and the SDK organizes modules by URL,
   not by tag.
3. *Call the SDK without `distinct` and post-process buckets in Python.* Rejected --
   the endpoint exists precisely to push grouping into the API; doing it in Python
   would require a full client list and waste the token budget.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy across two separate output tables:

- `org_wireless_clients_count_envelope`: PK = `(org_id, distinct, start, end)` -- one row
  per (org, distinct attribute, time window) capturing the API envelope (`distinct`,
  `start`, `end`, `limit`, `total`, plus MistHelper-injected `polled_at_utc`).
- `org_wireless_clients_count_results`: PK = `(org_id, distinct, start, end, bucket)` --
  one row per bucket within an envelope. `bucket` is the value of the grouped attribute
  (e.g., the SSID name when `distinct=ssid`, the hostname when `distinct=hostname`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables. `org_id` is injected by MistHelper before each upsert (Mist does not return
`org_id` in the body but MistHelper always knows which org the call targeted). The
`bucket` value is extracted from the dynamic `additionalProperties` key on each
`count_result` object -- the API does not name the attribute key directly inside the
result item, but the envelope's top-level `distinct` field tells us which key in the
result holds the bucket label.

**Rationale**:
The endpoint is a snapshot of an aggregated query over a time window. The same query run
again at the same end time produces the same buckets, so `(org_id, distinct, start,
end)` is the natural identity of an envelope and `(org_id, distinct, start, end,
bucket)` is the natural identity of a bucket within it. `INSERT OR REPLACE` cleanly
upserts a re-run for the same window. Splitting into envelope + results tables keeps
schemas simple and prevents nullable PK columns when the user is only interested in the
total/count summary.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on a single combined table.* Rejected -- would let
   repeated polls accumulate duplicate snapshots, defeating the upsert behaviour the
   spec requires.
2. *`natural_pk` on `(start, end, bucket)` alone (omit org_id).* Rejected -- a single
   MistHelper deployment may target multiple orgs; the time window is not unique across
   orgs.
3. *Single table with JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention everywhere else in
   MistHelper.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (envelope): `data/org_<org_id_short>_wireless_clients_count_envelope.csv`
- CSV (results):  `data/org_<org_id_short>_wireless_clients_count_results.csv`
- SQLite tables: `org_wireless_clients_count_envelope` and
  `org_wireless_clients_count_results`
- `org_id_short` is the first 8 hex characters of the org UUID -- already the convention
  used by adjacent client-search exports in MistHelper for human-readable filenames
  without leaking the full UUID into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countOrgWirelessClients"` for the envelope write and
`"countOrgWirelessClientsResults"` for the results write. DataExporter uses each string
as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES` to find the correct PK columns
and target table.

**Rationale**:
Matches the naming pattern used by `searchOrgWirelessClients` and adjacent count
endpoints (`countOrgWiredClients`, `countOrgWanClients`). Two output artifacts keep the
schema clean: a one-row envelope captures `total`, `start`, `end`, `limit`, and the
requested `distinct` field; the results table holds the buckets and is what a user
typically pivots on.

**Alternatives Considered**:

1. *Single output file with JSON-encoded results column.* Rejected -- breaks SQL
   queryability and forces every consumer to re-parse JSON.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell history
   and `ls` output unnecessarily; the 8-char short form is sufficient locally.
3. *Tag-based filename `clients_wireless_count_*`.* Rejected -- diverges from the
   operationId-based convention used elsewhere in MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting inside the Safe Org Exports /
Org Clients cluster, immediately adjacent to the existing `searchOrgWirelessClients`
menus (66-72) and just above the Resource Intensive cluster (97-101 + 153). The category
label is "Safe Org Exports -- Clients (Counts)".

**Rationale**:
Per `.github/copilot-instructions.md` the menu ranges are: 1-59 Safe Org Exports, 60-96
Interactive Safe, 97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-150
Interactive, 154-194 Destructive. Count endpoints are conceptually identical to search
endpoints but return aggregates only -- they are read-only, fast, and safe; they belong
inside the safe-export band. 96 is the next free integer at the top of the Interactive
Safe band, keeps the new operation visually adjacent to its `search` counterparts, and
stays far away from the destructive cluster. The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated menu integer and
96 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Append at 195+ after the destructive block.* Rejected -- placing a read-only count
   above the destructive block visually mis-signals risk level to a junior NOC engineer
   scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   non-paginated GET that returns a small aggregated JSON object; it does not warrant
   the Resource Intensive label.
3. *Reuse one of the existing search menu numbers and overload it with a `count` mode.*
   Rejected -- violates the one-operation-one-menu-number convention used everywhere
   else in MistHelper and complicates `--menu N` automation.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly four** values via `safe_input()`, all
with sensible defaults:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"count_org_wireless_clients:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   when present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.
2. `distinct` -- prompt: `"Distinct field [ssid|hostname|os|device|model|ap|vlan|ip|mac|
   (blank for none)]: "`, context: `"count_org_wireless_clients:distinct"`. Default:
   blank (no grouping -- API returns a single bucket aggregating the entire population).
   The value is whitelisted against the enum before being sent; an unknown value triggers
   a `WARNING` and re-prompts once before aborting.
3. `duration` -- prompt: `"Duration window (e.g. 1d, 7d, 2w) [1d]: "`, context:
   `"count_org_wireless_clients:duration"`. Default: `1d`. Passed straight through to
   the SDK as the `duration` query parameter; `start`/`end` are intentionally not asked
   to keep the prompt count low and match the Mist API's own default behavior. A future
   enhancement can add explicit `start`/`end` prompts behind a flag.
4. `limit` -- prompt: `"Result limit [100]: "`, context:
   `"count_org_wireless_clients:limit"`. Default: `100`. Parsed via `int(...)` inside a
   `try/except`; non-numeric input logs a `WARNING` and re-prompts once before aborting.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is org-scoped only -- no site, device, or template IDs are involved. Four
prompts is the minimum that still lets a junior NOC engineer pivot the answer on the
attribute they actually care about (SSID, OS, AP, etc.) without forcing them to type a
full query string or memorize epoch math. Defaults match the API's own defaults so a
quick `[Enter, Enter, Enter, Enter]` invocation returns a meaningful single-bucket
24-hour total.

**Alternatives Considered**:

1. *Ask only for `org_id` and always group by SSID.* Rejected -- removes flexibility
   the endpoint exists to provide.
2. *Ask for every query parameter individually (mac, hostname, device, os, model, ap,
   vlan, ssid, ip, start, end).* Rejected -- floods a junior NOC engineer with 11 prompts
   for a read-only count and provides marginal value over the four-prompt design. The
   most common filters can be added as a single optional `filter_expression` prompt in
   a follow-up spec if real users ask.
3. *Read prompt defaults from a JSON config file.* Rejected -- introduces a new file
   and config surface; `.env` plus inline defaults are sufficient and consistent with
   every other safe-export menu item.
