# Phase 0 Research: countSiteDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/sites/{site_id}/devices/events/count`
**Source doc**: `documentation/api/sites/GET_sites_site_id_devices_events_count.md`

This Phase 0 document resolves the open implementation decisions required
before Phase 1 design. Every decision is grounded in the enriched per-
endpoint doc above and the existing patterns visible in `MistHelper.py`.

## Research Task 1: SDK function signature & behavior

**Decision**: Call
`mistapi.api.v1.sites.devices.countSiteDeviceEvents(apisession, site_id, distinct, model, type, type_code, start, end, duration, limit)`
through the canonical `mistapi` SDK, passing only those query parameters
that the user supplied. All optional parameters are passed as `None` when
the user skipped them, so the SDK omits them from the wire request.

**Rationale**:

- The enriched doc (`documentation/api/sites/GET_sites_site_id_devices_events_count.md`)
  explicitly lists the SDK call path as
  `mistapi.api.v1.sites.devices.countSiteDeviceEvents()`. The spec.md
  refers to `mistapi.api.v1.sites.devices.events.count` as the module path
  but the function lives one level up at `...sites.devices`. The doc is
  authoritative because it was generated from the live SDK; the spec
  citation is a paraphrase.
- Parameters per the OpenAPI source: one required path parameter
  (`site_id`) plus eight optional query parameters
  (`distinct`, `model`, `type`, `type_code`, `start`, `end`, `duration`,
  `limit`). Defaults documented: `duration=1d`, `limit=100`.
- The response is a Mist "count envelope" object with five scalar fields
  (`distinct`, `start`, `end`, `limit`, `total`) and one array
  (`results[]`) whose entries are `count_result` objects with a required
  `count` integer plus an open `additionalProperties: string` map carrying
  the distinct-field value (for example `{"count": 42, "model": "AP43"}`).
- The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the
  decoded JSON envelope. This matches every other count-style operation
  already present in MistHelper.

**Alternatives Considered**:

- *Direct `requests.get(...)` with a hand-built URL*: Rejected -- violates
  the project constraint that `mistapi` is the sole permitted interface to
  Mist Cloud and would bypass adaptive rate limiting.
- *Use `search_mist_data` MCP analogue*: Rejected -- MCP tools are
  agent-side; runtime production code goes through the SDK.

## Research Task 2: Primary Key Strategy

**Decision**: Use `auto_increment_with_unique` with a `UNIQUE` constraint
across
`(site_id, distinct_field, distinct_value, window_start, window_end, filter_model, filter_type, filter_type_code)`.

**Rationale**:

- The endpoint returns an aggregate, not a stable Mist-assigned entity ID.
  Each row in `results[]` is keyed only by an arbitrary distinct-field
  value plus the integer count. Without the surrounding query envelope the
  row cannot be uniquely identified.
- `natural_pk` is rejected because there is no API-provided UUID.
- `composite_pk` could work, but two of the natural identity fields
  (`start`, `end`) accept relative strings like `-1d` that get resolved to
  different epoch integers on every call -- the resolved integers from the
  response envelope (`response.start`, `response.end`) ARE stable for one
  call but vary day to day, so a pure composite PK would still grow
  unbounded across runs. `auto_increment_with_unique` lets the same logical
  bucket upsert cleanly across re-runs while still letting time-series
  data accumulate when the user deliberately changes the window.
- This matches the documented strategy already used for similar aggregate
  endpoints in MistHelper (`getOrgLicensesSummary`, `countOrgSites`, etc.).

**Alternatives Considered**:

- *`natural_pk` on `(site_id, distinct_value)`*: Rejected -- collides when
  the user re-runs with a different time window or different filter set.
- *`composite_pk` on the full filter tuple*: Rejected because relative
  time strings make the tuple unstable across days even for the same
  logical question.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV / JSON filename: `data/site_device_events_count_<site_id>_<YYYYMMDD-HHMMSS>.csv`
- SQLite table name: `site_device_events_count`
- One row per `results[]` bucket. Envelope fields (`distinct`, `start`,
  `end`, `limit`, `total`) are copied onto every row so each row is
  self-describing and joinable.

**Rationale**:

- Follows the existing naming convention used for adjacent site-device
  exports (`site_devices_<site_id>_<timestamp>.csv`,
  `site_device_stats_<site_id>_<timestamp>.csv`).
- Snake-case operationId-derived table name keeps `DataExporter` mapping
  trivial.
- Flattening one row per bucket avoids storing JSON arrays inside SQLite
  cells, which makes downstream SQL queries natural
  (`SELECT distinct_value, count FROM site_device_events_count WHERE
  site_id = ? AND distinct_field = 'model' ORDER BY count DESC`).

**Alternatives Considered**:

- *One row per envelope (entire `results[]` array as JSON)*: Rejected --
  defeats the SQLite-as-query-store pattern and makes ArangoDB graph edges
  awkward.
- *Two separate tables (envelope + results)*: Rejected -- adds an
  unnecessary join for a small, self-contained aggregate.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Register the new operation as menu number **89** inside the
existing **Stats** cluster (operations 80-91 per the AI Agent Instructions
menu category table).

**Rationale**:

- The `agents.md` Menu Categories table defines 80-91 as Stats and 92-96
  as Viewers. A device-event count is conceptually a statistic, so 80-91
  is the correct cluster.
- 89 is the next free integer below the Viewers boundary at 92, matching
  the "append at the end of the relevant cluster" pattern already used by
  recent additions in the same range.
- The neighbor at menu 15 (`searchOrgDeviceEvents`) is an org-level search,
  not a site-level count, so placing the new count operation at 89 keeps
  org search and site count cleanly separated and avoids renumbering
  existing items.

**Alternatives Considered**:

- *Adjacent to menu 15 in the Org Events cluster*: Rejected -- this is a
  site-level call, not an org-level call. Mixing scopes inside one cluster
  hurts discoverability for junior NOC engineers.
- *In the Resource-Intensive cluster (97-101)*: Rejected -- the operation
  is light (a single aggregate call) and does not loop or paginate
  heavily.
- *Append at the end of the menu (currently 194)*: Rejected -- destructive
  operations occupy 154-194, and a read-only count belongs in the safe
  range below 92.

The exact number is re-verified at `/speckit.tasks` time; if 89 collides
with an unmerged feature branch, the next free integer in 80-91 is used.

## Research Task 5: Required user prompts

**Decision**: Collect inputs in this order, all through `safe_input()`:

1. `site_id` -- required, validated against the Mist UUID shape.
2. `distinct` -- optional string (default empty -> Mist API picks `model`
   per its documented default behavior); offered as a short pick-list
   (`model`, `type`, `type_code`, `device_id`, etc.) for NOC clarity.
3. `time_window` -- a single composite prompt that accepts either a
   duration shortcut (`1d`, `7d`, `2w`) OR explicit `start` / `end`
   epoch values; default `1d`.
4. `extra_filters` -- one prompt offering optional `model`, `type`, and
   `type_code` filters; each empty input means "no filter".
5. `limit` -- optional integer (default 100, API maximum); a non-numeric
   input is treated as "use default" and logged at DEBUG.

Mist credentials (`MIST_HOST`, `MIST_API_TOKEN`) come exclusively from
`.env` via `mistapi.APISession`; they are never prompted and never logged.

**Rationale**:

- Keeps the prompt count to <=5 distinct inputs so the menu remains
  usable in a small SSH terminal.
- Groups the four time-window-related parameters (`start`, `end`,
  `duration`) under one composite prompt, reducing perceived complexity
  for the junior-NOC target audience.
- `safe_input()` with explicit `context=` strings ensures EOF in SSH /
  container exits cleanly with code 0 and a meaningful log line
  (Constitution Principle III, NON-NEGOTIABLE).
- Validating `site_id` shape before any API call prevents 404 round-trips
  on obvious typos and produces a clearer error message than the SDK
  default.

**Alternatives Considered**:

- *Prompt for every query parameter individually*: Rejected -- eight
  prompts is too many for a single menu and overwhelms NOC engineers.
- *Read all filters from a config file*: Rejected -- adds a config layer
  outside `.env` that other menus do not require.
- *Hard-code `distinct=model`*: Rejected -- the whole value of this
  endpoint is choosing the distinct field per question.
