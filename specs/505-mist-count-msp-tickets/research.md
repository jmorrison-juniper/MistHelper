# Phase 0 Research: countMspTickets

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-28

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id_tickets_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.msps.tickets.count.countMspTickets(apisession, msp_id,
distinct=None, limit=100, page=1)`. The SDK returns a `mistapi.APIResponse` object whose
`.data` attribute is the parsed JSON body. The body is a single JSON object with the
following top-level keys per the doc:

- `distinct` (string) -- the attribute that buckets were grouped by (echoes the request).
- `start` (int32) -- window start epoch (set by the SDK / server, not user input).
- `end` (int32) -- window end epoch.
- `limit` (int32) -- the page size in effect for this response.
- `total` (int32) -- total number of distinct buckets across all pages.
- `results` (array, uniqueItems=true) -- one element per distinct value. Each element is
  an object with a required `count` integer plus arbitrary string-valued additional
  properties whose key is the distinct attribute name (e.g. `{count: 42, status: "open"}`
  when `distinct=status`).

Required path parameter: `msp_id` (UUID string).
Optional query parameters: `distinct` (string, defaults to server-side bucket attribute
if omitted) and `limit` (integer, defaults to 100). The endpoint supports `page`-based
pagination per the doc, but MistHelper requests a single page sized to `limit` for the
v1 menu item; deeper pagination is out of scope for this spec.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.msps.tickets.countMspTickets()`. The mistapi SDK consistently generates
module paths from the OpenAPI URL, not the tag, and `/msps/{msp_id}/tickets/count` maps
one-for-one to `mistapi.api.v1.msps.tickets.count`. Final verification happens at
implementation time via
`python -c "from mistapi.api.v1.msps.tickets import count; help(count)"` inside the
venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}/tickets/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Stream all pages by looping `page=1..N` until empty.* Rejected for the v1 menu item
   because the doc lists `limit` default = 100 and ticket-count distinct buckets are
   bounded by attribute cardinality (usually <50). Multi-page retrieval is added in a
   follow-up spec only if a real MSP exceeds 100 buckets.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `msp_tickets_count_summary`: PK = `(msp_id, distinct_attr)` -- one row per
  (MSP, distinct attribute) snapshot. Re-running the menu item against the same
  `msp_id` with the same `distinct_attr` upserts the summary in place.
- `msp_tickets_count_buckets`: PK = `(msp_id, distinct_attr, bucket_value)` -- one row
  per distinct bucket. `bucket_value` is the string value of the additional property
  whose key equals `distinct_attr` (for example, when `distinct=status`, a result
  `{count: 7, status: "open"}` becomes a row with `bucket_value="open"` and `count=7`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables, with `msp_id` injected by MistHelper before the upsert (Mist does not echo
`msp_id` inside the body but MistHelper always knows which MSP the call targeted).

**Rationale**:
The endpoint reports a *current* distinct-attribute count. Re-polling the same MSP for
the same distinct attribute must update the existing rows rather than accumulate
duplicates. `(msp_id, distinct_attr)` uniquely identifies a summary snapshot, and
`(msp_id, distinct_attr, bucket_value)` uniquely identifies one bucket inside that
snapshot. `INSERT OR REPLACE` on those PKs gives the upsert behavior the spec requires.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots, defeating the upsert behavior the spec requires.
2. *Single combined table with one row per bucket and a duplicated summary column set.*
   Rejected -- the summary fields (`start`, `end`, `total`, `limit`) repeat once per
   bucket row in that design, wasting space and complicating queries that want only the
   summary. The two-table split is consistent with how MistHelper handles other
   nested-array responses (e.g., spec 500 splits async-claim summary vs. detail).
3. *Include `polled_at_utc` in the PK to preserve history.* Rejected -- the spec's
   acceptance scenario 3 explicitly demands upsert (no duplicates) on repeated runs.
   History capture is a separate non-functional concern handled by ArangoDB graph
   edges or external retention tooling, not by primary-key design.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/msp_<msp_id_short>_tickets_count_summary.csv`
- CSV (buckets): `data/msp_<msp_id_short>_tickets_count_buckets.csv`
- SQLite tables: `msp_tickets_count_summary` and `msp_tickets_count_buckets`
- `msp_id_short` is the first 8 hex characters of the MSP UUID -- matches the same
  short-id convention used by adjacent org exports in MistHelper for human-readable
  filenames that do not leak full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countMspTickets"` (matching the operationId) for the bucket write and
`"countMspTicketsSummary"` (MistHelper-internal sub-table key) for the summary write.
DataExporter uses those strings as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The summary plus buckets split keeps each output file small and queryable. The short-id
naming and the `msp_` prefix prevent collisions with org-scoped exports that use
`org_` and site-scoped exports that use `site_`. Splitting into two `api_function_name`
keys lets DataExporter pick the correct PK strategy automatically without inspecting the
row shape.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used elsewhere in
   MistHelper.
2. *Full MSP UUID in the filename.* Rejected -- leaks the MSP UUID into shell history
   and `ls` output unnecessarily. The first eight characters disambiguate locally.
3. *Reuse the operationId for both tables.* Rejected -- two tables need two PK
   strategies. The MistHelper convention is one `api_function_name` per logical
   destination table.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 88**, sitting inside the Interactive Safe
cluster (60-96). The category label is "Interactive Safe -- MSP Operations".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-150 Interactive, 151-152 Continuous, 154-194 Destructive.
MSP-tag operations are read-only enumerations at MSP scope and are best grouped inside
60-96 alongside other interactive-safe site/org viewers. Number 88 is a currently-free
slot well clear of the `--test` skip list (90-100) so the new menu item is exercised by
the standard quality-gate sweep. Number is provisional -- at `/speckit.tasks` time,
`MistHelper.py` is grep'd for the latest allocated menu integer and 88 is shifted
forward to the next free integer in the same cluster if a conflict exists with an
in-flight feature branch (spec 500 reserves 95; specs 501-504 may reserve other slots
in the same cluster).

**Alternatives Considered**:

1. *Slot inside Safe Org Exports (1-59).* Rejected -- this is MSP-scoped, not org-scoped,
   and MistHelper already groups MSP operations separately from org exports for clarity.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single GET
   that returns a small JSON object bounded by the `limit` query parameter (default
   100). It belongs in the safe cluster.
3. *Append to the end (e.g., 195).* Rejected -- placing a read-only MSP count above the
   destructive cluster (154-194) visually mis-signals risk level to a junior NOC
   engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **up to three** values via `safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context:
   `"msp_tickets_count:msp_id"`. Default: the value of `MIST_MSP_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.
2. `distinct_attr` -- prompt:
   `"Distinct attribute to count by [status]: "`, context:
   `"msp_tickets_count:distinct"`. Default: `status` (the most common bucket attribute
   on MSP ticket dashboards). Pressing Enter accepts the default. Trimmed of leading /
   trailing whitespace before sending.
3. `limit` -- prompt: `"Limit (max buckets) [100]: "`, context:
   `"msp_tickets_count:limit"`. Default: `100` (matches the Mist API default per the
   doc). Cast to `int` inside a `try/except` block; on `ValueError`, log `WARNING` and
   fall back to 100.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_MSP_ID` -- optional default for prompt 1.

**Rationale**:
Mist's ticket-count endpoint is MSP-scoped. Org, site, and device IDs are not involved.
The `distinct` query parameter materially changes which buckets the response contains,
so asking the user keeps the menu item flexible (status / priority / org_id are the
common bucket attributes). The `limit` parameter has a sensible Mist-side default but
is exposed so an operator can shrink it for slow links or expand it when they know an
MSP's bucket cardinality is high.

**Alternatives Considered**:

1. *Hard-code `distinct=status`.* Rejected -- different MSPs care about different
   attributes, and a hard-coded value silently hides that flexibility from the operator.
2. *Skip the `limit` prompt and always pass the API default.* Rejected -- the SDK omits
   the parameter when `None` is passed and applies its own default. Explicit prompting
   makes the active limit visible in the run transcript, which helps the operator
   correlate the `total` summary field against the returned bucket count.
3. *Add a fourth prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`.
