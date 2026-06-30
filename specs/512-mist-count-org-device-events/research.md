# Phase 0 Research: CountOrgDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Source endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_devices_events_count.md`

This document records the Phase 0 research decisions that anchor the Phase 1 design.
Each task is presented in Decision / Rationale / Alternatives Considered form.

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.devices.events.count.countOrgDeviceEvents(mist_session, org_id, distinct=None, site_id=None, ap=None, apfw=None, model=None, text=None, timestamp=None, type=None, start=None, end=None, duration="1d", limit=100)`
exactly once per menu invocation. Pass `org_id` from `safe_input()`, default `distinct` to
`"type"` (the most operationally useful grouping), and default the time window to
`duration="1d"` (matches the API default). All other query parameters are left at the SDK
default (`None`) unless the user opts in via the prompt sequence.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_devices_events_count.md`) declares:
- HTTP: `GET /api/v1/orgs/{org_id}/devices/events/count`
- Required path param: `org_id` (string)
- Optional query params (12): `distinct`, `site_id`, `ap`, `apfw`, `model`, `text`,
  `timestamp`, `type`, `start`, `end`, `duration` (default `1d`), `limit` (default `100`).
- Response 200 schema: object with `distinct`, `end`, `limit`, `results[]`, `start`,
  `total`. `results[]` items have a required `count: int` plus `additionalProperties:
  string` keyed by the distinct attribute value.
- mistapi SDK call form: `mistapi.api.v1.orgs.devices.countOrgDeviceEvents(...)` per the
  doc's "mistapi SDK" section. The fully qualified module path is
  `mistapi.api.v1.orgs.devices.events.count`.

The endpoint is a count summary, not raw events -- response volume is bounded by `limit`,
making the single-call pattern sufficient (no pagination loop required for the v1 menu
item; if user data exceeds `limit=100` distinct groups, the next iteration of the menu
can expose a `--limit` override).

**Alternatives Considered**:
- *Auto-iterate all 12 optional filters into a guided wizard*: Rejected. Over-prompting
  violates the junior-NOC audience standard ("Fred Rogers meets NASA/JPL"). The
  three-prompt sequence (org / distinct / duration) covers the 90% case; advanced
  filtering belongs to a future power-user mode.
- *Default `distinct=None` (no grouping)*: Rejected. With no distinct key, the response
  collapses to a single total which duplicates what other dashboard metrics already
  provide. Defaulting to `type` produces an immediately useful event-type breakdown.

## Research Task 2: Primary Key Strategy

**Decision**: Use **`composite_pk`** with primary key
`["org_id", "distinct", "start", "end", "result_key"]` on the detail table
(`org_device_events_count_results`) and `composite_pk` with primary key
`["org_id", "distinct", "start", "end"]` on the summary table
(`org_device_events_count_summary`). The `result_key` column is the value of the
`additionalProperties` string in each `results[]` row (e.g. `type="AP_DISCONNECTED"`).

**Rationale**: The endpoint response is a time-window aggregation, not an entity catalog.
The natural identity of one row is the tuple `(org_id, distinct_attribute, time_window,
grouped_value)`. There is no API-supplied stable UUID, so `natural_pk` is not applicable.
`auto_increment_with_unique` would create duplicates on re-run because no business key
prevents inserts. `composite_pk` enables `INSERT OR REPLACE` upsert semantics so repeated
runs of the same `(org, distinct, window)` overwrite stale aggregates rather than
accumulating duplicates -- which is exactly the behavior NOC engineers expect for a
"refresh the count" workflow.

**Alternatives Considered**:
- *`auto_increment_with_unique` with internal `misthelper_internal_id`*: Rejected. Would
  retain stale snapshots and pollute SQLite. The whole point of a count endpoint is "give
  me the current breakdown."
- *Drop-and-recreate the table on every run*: Rejected. Destroys historical snapshots
  that an operator may want to diff. The composite-PK upsert is the right balance: the
  same `(org, distinct, window)` overwrites, but a different window inserts a new row,
  preserving history.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- Summary CSV file: `data/org_device_events_count_summary.csv`
- Detail CSV file: `data/org_device_events_count_results.csv`
- SQLite tables: `org_device_events_count_summary`, `org_device_events_count_results`
- Both written via one call to `DataExporter.write_with_format_selection(rows, filename,
  api_function_name="countOrgDeviceEvents")`, invoked twice -- once per logical table.

**Rationale**: Names follow the existing convention in the safe-org-export cluster
(snake_case, prefixed with the operation domain). The summary / results split mirrors the
JSON response structure exactly (one top-level object containing one `results[]` array),
keeping the flattening logic trivial and the schema obvious to a junior reader. The
`api_function_name` argument lets `DataExporter` look up the correct PK strategy from
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for each table.

**Alternatives Considered**:
- *Single flattened table with summary fields duplicated on every detail row*: Rejected.
  Wastes storage, complicates upserts (the summary fields like `total` are scalars, not
  per-row), and produces a confusing CSV for the junior-NOC audience.
- *Embed the `results[]` array as a JSON-encoded string column in a single summary row*:
  Rejected. CSV consumers (Excel, Power BI, ad-hoc scripts) cannot pivot on a JSON blob.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Propose menu number **195**, classified under **Safe Org Exports / Events
Counts**. Adjacent existing operations: `searchOrgDeviceEvents` (used internally by
menus 13, 15, 83 per the enriched doc).

**Rationale**: The existing menu cluster ranges (per
`.github/copilot-instructions.md`):
- 1-59 Safe Org Exports (events 20-26)
- 60-96 Interactive Safe (stats 80-91)
- 97-101, 153 Resource Intensive
- 102-150 WebSocket / Interactive
- 154-194 Destructive (firmware, reboots, VC, etc.)

The events cluster at 20-26 is logically the natural home but is full. The stats cluster
at 80-91 is also full. The next sequential free integer above the destructive ceiling
(194) is **195**, which keeps numbering monotonic and avoids forcing a renumber of any
existing menu. The new operation is read-only, lightweight, and non-destructive, so it
does not need to live inside the destructive block.

**Alternatives Considered**:
- *Insert at 26.5 / renumber events cluster*: Rejected. Renumbering breaks every existing
  user-facing reference (docs, scripts, muscle memory) and inflates the diff to dozens of
  unrelated lines.
- *Reuse a "deprecated" number*: Rejected. There are no documented deprecated slots; the
  full menu inventory is in use.
- *Wait for a free slot in cluster 20-26 or 80-91*: Rejected. Blocks the spec on
  unrelated work. The placement is revisited at `/speckit.tasks` time and can be moved if
  a free slot opens.

## Research Task 5: Required User Prompts (Which from User, Which from `.env`)

**Decision**: Three `safe_input()` prompts. All other configuration is read from `.env`
or defaulted in code.

| Prompt | Source | Default | Context String |
|--------|--------|---------|----------------|
| `org_id` | `safe_input()`, pre-filled from `MIST_ORG_ID` env var if set | `MIST_ORG_ID` from `.env` | `"org_device_events_count:org_id"` |
| `distinct` | `safe_input()` (allow-list: `type`, `model`, `ap`, `apfw`, `site_id`, `text`, `timestamp`) | `"type"` | `"org_device_events_count:distinct"` |
| `duration` | `safe_input()` (e.g. `1d`, `7d`, `2w`) | `"1d"` | `"org_device_events_count:duration"` |

| Source | Value |
|--------|-------|
| `.env` | `MIST_HOST`, `MIST_API_TOKEN`, `MIST_ORG_ID` (default org), `MIST_PAGE_LIMIT` |
| Code default | `limit=100` (matches API default), `start=None`, `end=None` (the SDK
                  converts `duration` into a relative window) |
| Not prompted | `site_id`, `ap`, `apfw`, `model`, `text`, `timestamp`, `type` -- all
                  remain `None` in v1; future enhancement adds an advanced-filter
                  sub-prompt. |

**Rationale**: Three prompts is the smallest set that exposes the operationally useful
controls (which org, which grouping, which time window) while keeping the menu flow
short enough for SSH / container sessions where every line of output matters. The
`distinct` allow-list enforces the validate-early principle from the Constitution
(Safety-First). `org_id` falling back to `MIST_ORG_ID` matches the convention used by
the adjacent license export operations and reduces friction for single-org operators.

**Alternatives Considered**:
- *No prompts, pure `.env` config*: Rejected. Hides intent at run time; the operator
  cannot tell from the log line which org / distinct key was queried.
- *Full 12-parameter prompt sequence*: Rejected. Drowns the junior-NOC audience in
  optional fields; 9 of the 12 query params are rarely useful for a count breakdown.
- *Interactive UUID picker (list orgs / sites first, let user choose)*: Rejected for v1.
  Adds an extra API call (`listSites`) and complicates the method past the 25-line limit.
  Belongs to a future picker-mode enhancement.
