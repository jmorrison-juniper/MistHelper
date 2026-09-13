# Phase 0 Research: countOrgSiteMxEdgeEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

This document resolves all unknowns required to enter Phase 1 design for the new menu
item that wraps `GET /api/v1/orgs/{org_id}/mxedges/events/count`. Each section uses the
Decision / Rationale / Alternatives Considered format mandated by the SpecKit plan
template. No `NEEDS CLARIFICATION` markers remain after this document; every choice is
concrete and actionable.

---

## Research Task 1: SDK Function Signature and Behavior

**Source**:
`documentation/api/orgs/GET_orgs_org_id_mxedges_events_count.md` (enriched per-endpoint
doc generated from the Mist OpenAPI 3 spec).

### Decision

The implementation invokes the SDK as:

```python
import mistapi
from mistapi.api.v1.orgs.mxedges.events import count as mxedge_events_count_module

response = mxedge_events_count_module.countOrgSiteMxEdgeEvents(
    mist_session,            # mistapi.APISession populated from .env
    org_id,                  # path parameter (UUID string)
    distinct=distinct,       # optional: which attribute to bucket by
    mxedge_id=mxedge_id,     # optional: filter to a single mxedge
    mxcluster_id=mxcluster,  # optional: filter to a single mxedge cluster
    type=event_type,         # optional: event type name (see listDeviceEventsDefinitions)
    service=service,         # optional: service running on the mxedge
    start=start_epoch,       # optional: start time (epoch seconds or relative string)
    end=end_epoch,           # optional: end time (epoch seconds or relative string)
    duration=duration,       # optional: like "1d" / "7d" / "2w", default "1d"
    limit=limit,             # optional: max distinct buckets returned, default 100
)
data = response.data         # decoded JSON body (dict)
```

The SDK function lives at the module path
`mistapi.api.v1.orgs.mxedges.events.count` (confirmed by the spec's
`mistapi SDK module` field). The enriched documentation also lists the alias
`mistapi.api.v1.orgs.mxedges.countOrgSiteMxEdgeEvents()`; both refer to the same
generated function via mistapi's nested-module re-export. The canonical fully-qualified
path is used in the implementation.

The response object is a `mistapi.APIResponse` with a `.data` attribute holding the
decoded JSON. The body is a single dict containing the keys `distinct`, `start`, `end`,
`limit`, `total`, and `results[]` -- no pagination loop is required because the array is
already bounded by `limit` (default 100, server-side cap typically applies).

### Rationale

The endpoint follows the standard "count by distinct" pattern used across the Mist API
(searchable / countable resources). Other operations in MistHelper that call
`/count` endpoints (for example the corresponding switch / AP / client variants) use the
same one-shot non-paginated GET pattern; reusing that pattern keeps the new method
consistent with adjacent code and avoids reinventing pagination logic for an endpoint
that is intentionally aggregate-only.

### Alternatives Considered

- **Wrap the lower-level `mistapi.APISession.mist_get(path)` call directly.** Rejected
  because it bypasses the typed SDK, breaks the project's "mistapi is the only
  permitted Mist API interface" rule (constitution Technology & Compatibility
  Constraints), and would require manual construction of the query string for all
  nine optional parameters.
- **Treat the endpoint as paginated and loop until empty.** Rejected because the
  enriched doc shows `limit` is a max bucket count, not a page size; the response has
  no `next` cursor. Looping would either repeat the same aggregate or hammer the API
  for no incremental data.

---

## Research Task 2: Primary Key Strategy

### Decision

Register `countOrgSiteMxEdgeEvents` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with
**`composite_pk`** type, producing two physical tables (summary + results) with the
following primary keys:

- `org_mxedge_events_count_summary`:
  `primary_key = ['org_id', 'distinct', 'start', 'end']`
- `org_mxedge_events_count_results`:
  `primary_key = ['org_id', 'distinct', 'distinct_value', 'start', 'end']`

The dict entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for the operationId itself uses the
results-table key (the row-level data) because that is the multi-row payload the
DataExporter writes:

```python
'countOrgSiteMxEdgeEvents': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'distinct', 'distinct_value', 'start', 'end'],
    'indexes': ['org_id', 'distinct', 'distinct_value'],
},
```

### Rationale

The endpoint returns an aggregate with no server-assigned UUID. Each result row is a
pair `(distinct_value, count)` valid for the requested time window. Composite PK on
`(org_id, distinct, distinct_value, start, end)` gives:

1. **Idempotent upserts**: Re-running the menu item for the same window updates the
   existing row in place via `INSERT OR REPLACE`, exactly as the database strategy
   section of the project guide prescribes.
2. **Time-series safety**: Different time windows for the same `(org, distinct,
   distinct_value)` produce distinct rows, preserving history.
3. **Distinct-attribute pivoting**: Different `distinct` values for the same window
   produce distinct rows, so the same backing table holds counts grouped by
   `type`, `service`, `mxedge_id`, etc. simultaneously.

### Alternatives Considered

- **`natural_pk` on a server-provided `id`.** Rejected -- the response schema has no
  per-result `id` field; results are dynamic key/value pairs.
- **`auto_increment_with_unique` (synthetic id + unique index on the same tuple).**
  Rejected because composite_pk is cleaner: the natural keys are already the right
  shape, and a synthetic id adds no information while complicating
  cross-table joins.
- **Single flat table with one row per (window, distinct, value) and the envelope
  duplicated into every row.** Rejected because the summary fields (`total`, `limit`)
  are window-scoped and duplicating them N times is wasteful and confusing for
  downstream reporting; a two-table summary + results split is the established
  pattern for count endpoints in MistHelper.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV summary file**: `data/org_mxedge_events_count_summary.csv`
- **CSV results file**: `data/org_mxedge_events_count_results.csv`
- **SQLite tables** (inside `data/mist_data.db`):
  - `org_mxedge_events_count_summary`
  - `org_mxedge_events_count_results`
- **ArangoDB collections** (when polyglot backend is enabled):
  - `org_mxedge_events_count_summary` (document collection)
  - `org_mxedge_events_count_results` (document collection, edge-linked to
    `org_mxedges` and `orgs` via existing graph helpers)

The `DataExporter.write_with_format_selection()` call is invoked twice -- once for the
summary row, once for the results array -- with the `api_function_name` argument set to
`'countOrgSiteMxEdgeEvents'` so the central PK strategy lookup works for both writes.

### Rationale

The two-table split mirrors the response shape (envelope + array) and matches the
naming convention already used in MistHelper for aggregate endpoints (`*_summary`
holds window-scoped metadata; `*_results` holds the per-bucket rows). Lower-snake-case
table names match every other table in `data/mist_data.db`. Adding a hyphenless,
lowercase prefix `org_mxedge_events_count_` makes the pair easy to discover by tab-
completion alongside the existing `org_mxedge_events_search_*` tables produced by spec
500's adjacent endpoint.

### Alternatives Considered

- **Single denormalized table** `org_mxedge_events_count_flat.csv` with envelope
  columns repeated on every results row. Rejected for the reason given in Research
  Task 2 (waste + confusion) and because it makes the SQLite primary key longer than
  necessary.
- **Generic shared table** `mist_event_counts` shared with switch / AP / client count
  endpoints. Rejected because each `/count` endpoint has different distinct-field
  semantics and combining them would force a `source_endpoint` discriminator column
  on every read, hurting both clarity and query performance.

---

## Research Task 4: Menu Category Placement and Next Available Number

### Decision

Place the new menu item at **operation number 58** under the **Safe Org Exports**
category (range 1-59 per the project menu taxonomy). The menu label is:

> **58. Count organization Mist Edge events by distinct attribute**

The item sits adjacent to the existing Events cluster (20-26) and the Mist Edge cluster
(implicit within 8-19 inventory and 56-59 misc). The full menu list is re-verified
during task generation; if 58 collides with an in-flight feature branch, the next free
integer inside the 1-59 range is selected.

### Rationale

The endpoint is a strictly read-only GET that returns aggregated counts. It belongs in
the Safe Org Exports band, not the Interactive Safe band (60-96), because it requires
no interactive viewer (60-92 viewers, 92-96 viewer subset). Operation 58 is the lowest
unclaimed slot at the end of the safe-exports range observed in current `MistHelper.py`
and matches the convention of grouping mxedge operations near each other.

### Alternatives Considered

- **Place at op 96 alongside spec 500's GetOrgLicenseAsyncClaimStatus (op 95).**
  Rejected because spec 500 belongs to the license cluster; this endpoint belongs to
  the events / mxedge cluster.
- **Place in the resource-intensive band (97-101).** Rejected because the endpoint
  returns a small aggregate bounded by `limit`, not a long-running paginated dump.
- **Place in the destructive band (154-194).** Rejected outright -- GET endpoints
  are never destructive.

---

## Research Task 5: Required User Prompts

### Decision

The menu method collects the following inputs via `safe_input()`. Each prompt has an
explicit `context=` string to make EOF traces searchable in SSH / container session
logs.

| Order | Prompt label | Variable | Source | Required | Default if blank |
|-------|--------------|----------|--------|----------|------------------|
| 1 | "Organization ID (UUID)" | `org_id` | user input | yes | reject + reprompt |
| 2 | "Distinct attribute (type / service / mxedge_id / mxcluster_id)" | `distinct` | user input | no | `type` |
| 3 | "Mist Edge ID filter (blank to skip)" | `mxedge_id` | user input | no | omit param |
| 4 | "Mist Edge cluster ID filter (blank to skip)" | `mxcluster_id` | user input | no | omit param |
| 5 | "Event type filter (blank to skip)" | `event_type` | user input | no | omit param |
| 6 | "Service filter (blank to skip)" | `service` | user input | no | omit param |
| 7 | "Duration like 1d / 7d / 2w (blank for 1d)" | `duration` | user input | no | `1d` |
| 8 | "Result limit (blank for 100, max 1000)" | `limit` | user input | no | `100` |

`MIST_HOST` and `MIST_API_TOKEN` come exclusively from `.env`; neither is ever
prompted from the user, logged, or stored in `data/`. The `org_id` may default from the
`MIST_ORG_ID` environment variable when present, in which case prompt 1 shows the
default and accepts a blank to confirm.

### Rationale

The required path parameter is only `org_id`; everything else is optional per the
OpenAPI spec. Prompting for every optional filter lets the junior NOC engineer drive
the call without consulting the API docs, while accepting blank to skip keeps the
common case (default-bucket-by-type for the last day) a five-keystroke operation.
Defaulting `distinct` to `type` matches the most common operational question ("what
event types are firing on my mist edges?"). Defaulting `duration` to `1d` matches the
Mist API server-side default and keeps the result set small and fast.

### Alternatives Considered

- **Single combined free-form filter prompt.** Rejected because parsing arbitrary
  filter strings is error-prone, and the junior NOC engineer audience benefits from
  a guided, one-question-at-a-time flow.
- **Read every filter from CLI flags only (`--menu 58 --distinct=type --duration=7d`).**
  Rejected because MistHelper's primary interaction model is interactive; CLI flags
  remain available via the standard `--menu <num>` invocation for automation, but the
  interactive prompts are the documented path.
- **Prompt for `start` + `end` epoch timestamps individually.** Rejected because the
  `duration` shorthand covers the common operational windows (`1d`, `7d`, `2w`) and
  the Mist API accepts relative strings via the same field. Power users who need a
  precise window can still set `start` / `end` via the CLI flag path in a future
  enhancement.
