# Phase 0 Research: countSiteMxEdgeEvents

**Feature**: 552-mist-count-site-mx-edge-events
**Spec**: [spec.md](./spec.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_mxedges_events_count.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the SDK as
`mistapi.api.v1.sites.mxedges.events.count.countSiteMxEdgeEvents(apisession, site_id, distinct=None, mxedge_id=None, mxcluster_id=None, type=None, service=None, start=None, end=None, duration="1d", limit=100)`
and treat the returned `mistapi.APIResponse` object's `.data` attribute as the
parsed JSON envelope (an object containing `distinct`, `start`, `end`, `limit`,
`total`, and `results[]`).

**Rationale**: The enriched per-endpoint documentation at
`documentation/api/sites/GET_sites_site_id_mxedges_events_count.md` lists the
SDK entry as `mistapi.api.v1.sites.mxedges.countSiteMxEdgeEvents()`. The
canonical mistapi 0.59 layout mirrors the OpenAPI path, so the implementation
import is `from mistapi.api.v1.sites.mxedges.events import count as count_mod`
followed by `count_mod.countSiteMxEdgeEvents(...)`. Either form resolves the same
underlying callable; the implementation will use whichever module path the
installed mistapi version exposes (verified at code time with a one-line REPL
check). Required path parameter is `site_id`. All nine query parameters
(`distinct`, `mxedge_id`, `mxcluster_id`, `type`, `service`, `start`, `end`,
`duration`, `limit`) are optional; the SDK default for `duration` is `"1d"` and
for `limit` is `100`. The response is a single JSON object, not a list -- the
existing `flatten_dict()` helper is sufficient; no pagination plumbing is
required because the count endpoint returns one envelope per call.

**Alternatives Considered**:
- *Direct HTTP via `requests`*: Rejected. Constitution Technology & Compatibility
  Constraints forbid direct HTTP calls when a mistapi method exists.
- *Call the sibling `searchSiteMxEdgeEvents` and aggregate client-side*: Rejected.
  That endpoint returns full event payloads (heavy, paginated) when the user
  only wants counts. Using the dedicated count endpoint is faster and respects
  Mist API rate limits.
- *Treat `results[]` as a list of typed entities with a fixed schema*: Rejected.
  Each `results[i]` is `{count: int, <distinct_field>: str}` where the second
  key is dynamic (driven by the `distinct` query parameter). The flattener must
  preserve `additionalProperties` as a generic `bucket_key` / `bucket_value`
  pair.

## Research Task 2: Primary Key Strategy

**Decision**: Use **two** entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES` --
one `composite_pk` strategy for the envelope row and one `composite_pk`
strategy for the bucket rows -- registered against a single
`countSiteMxEdgeEvents` operationId via a list of table definitions.

For the envelope: PK = `(site_id, distinct, start, end)` -- the same site
queried again with the same grouping attribute and time window must upsert (no
duplicates), but a different `distinct` value or time window produces a new row.

For each bucket: PK = `(site_id, distinct, start, end, bucket_key, bucket_value)`
-- one row per `(envelope, distinct attribute, value)` triple. `bucket_key` is the
dynamic attribute name from the response (mirrors the `distinct` request param);
`bucket_value` is the observed string value.

**Rationale**: The response is a time-windowed aggregate with no stable
server-issued UUID, so `natural_pk` with a single API field does not fit. The
fields `(site_id, distinct, start, end)` together form a deterministic
identifier for a given count slice; re-running the same query overwrites the
prior slice rather than producing duplicate rows. The bucket-level PK extends
this with `(bucket_key, bucket_value)` so every distinct grouping value gets
its own upsertable row. This matches the precedent already in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for other Mist `/.../count` endpoints
(time-series aggregates use composite keys over the time window plus the
grouping fields).

**Alternatives Considered**:
- *natural_pk on a synthetic hash of the query params*: Rejected. Less
  discoverable; SQL queries against the table would have to recompute the
  hash to find a known slice.
- *auto_increment_with_unique on the same tuple*: Rejected. Auto-increment
  adds a meaningless surrogate column without any benefit over a direct
  composite PK; the composite tuple is small and stable.
- *Single combined table with a `row_type` discriminator*: Rejected. Mixing
  envelope and bucket rows in one table forces SQL consumers to filter on
  `row_type` for every query and complicates the CSV output. Two narrow
  tables are clearer.

## Research Task 3: Output Filename and SQLite Table

**Decision**: Default output filenames are
`data/site_mxedge_events_count_summary.csv` and
`data/site_mxedge_events_count_buckets.csv`. SQLite tables are
`site_mxedge_events_count_summary` and `site_mxedge_events_count_buckets`
inside `data/mist_data.db`. ArangoDB collections take the same names.

**Rationale**: The filename matches the existing snake_case convention used by
adjacent Mist Edge menu items (`site_mxedges_inventory.csv`,
`site_mxedge_events_search.csv`). The `_count_` infix matches the OpenAPI path
segment so future maintainers can match path -> file by inspection. Splitting
summary and buckets into two files mirrors the data model (one envelope per
call; many buckets per envelope) and lets CSV consumers join on the
`(site_id, distinct, start, end)` composite key without a discriminator column.

**Alternatives Considered**:
- *Single flat file with the envelope fields duplicated on every bucket row*:
  Rejected. Duplicates 5 columns of metadata per bucket, inflates row size,
  and obscures the actual data shape returned by the API.
- *Use the operationId verbatim
  (`count_site_mx_edge_events_summary.csv`)*: Rejected. The MistHelper
  convention is path-based snake_case, not operationId-based, because
  filenames are read by humans browsing `data/` and the path form is more
  recognizable.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation at menu number **96** in the Safe Org
Exports / SLE / Mist Edge cluster.

**Rationale**: The current menu layout (per `agents.md` and `README.md`):
- 1-59  Safe Org Exports
- 60-72 Safe Site Devices
- 73-79 Insights
- 80-91 Stats
- 92-95 Viewers
- 96    Next free slot (current proposal)
- 97-101 Resource Intensive
- 102-123 WebSocket
- 124-150 Interactive
- 151-152 Continuous
- 154-194 Destructive

Menu 96 sits at the boundary between safe read-only exports and resource-heavy
operations. The count endpoint is light, fast, and read-only -- the safer side
of that boundary -- so 96 is the natural slot. It is also adjacent to existing
Mist Edge menu items so a user already in that area finds it quickly. At
`/speckit.tasks` time the menu list is re-verified; if another in-flight branch
has already claimed 96, the next free integer in the same cluster (97 if the
resource-intensive band has room, otherwise 156 in the new-additions tail) is
used.

**Alternatives Considered**:
- *Place in the WebSocket cluster (102-123)*: Rejected. The endpoint is plain
  HTTP, not a websocket stream. Mis-categorization confuses the user.
- *Place at the end of the menu (e.g., 195)*: Rejected. The menu grows
  fastest at the safe-exports end; adding to the tail orphans the new item
  from related operations.

## Research Task 5: Required User Prompts

**Decision**: Prompt the user via `safe_input()` for the following, in order:

1. `site_id` -- required; validated against the Mist UUID shape before the
   SDK call. No `.env` fallback because sites are not pre-bound to the
   session.
2. `distinct` -- optional; default `type`. Accepted values: any string the
   Mist API treats as a groupable attribute. Common choices documented in
   `quickstart.md` are `type`, `service`, `mxedge_id`, `mxcluster_id`.
3. `duration` -- optional; default `1d`. Accepted values: relative strings
   like `1h`, `1d`, `7d`, `2w`. Mutually exclusive with `start` / `end`.
4. `mxedge_id` -- optional; blank means no filter.
5. `mxcluster_id` -- optional; blank means no filter.
6. `type` -- optional; blank means no filter. Only meaningful when
   `distinct != "type"`.
7. `service` -- optional; blank means no filter.
8. `limit` -- optional; default `100`. Integer cap on returned buckets.

The `MIST_HOST` and `MIST_API_TOKEN` values come from `.env` via the existing
`mistapi.APISession` -- they are never prompted. `org_id` is *not* required for
this endpoint (the path is site-scoped, not org-scoped) but the session must
already be authenticated for an org that owns the target site.

**Rationale**: Mirrors the prompt order used by the sibling
`searchSiteMxEdgeEvents` menu item so users familiar with that workflow find
the new menu predictable. Defaults match the Mist API defaults documented in
`documentation/api/sites/GET_sites_site_id_mxedges_events_count.md` (`duration=1d`,
`limit=100`) so an "accept all defaults" path produces a meaningful result.
`safe_input()` with explicit `context=` strings keeps the operation tolerant of
SSH / container EOF.

**Alternatives Considered**:
- *Bundle every optional filter into one comma-separated prompt*: Rejected.
  Junior NOC engineers (the target audience per the constitution Audience
  Standard) are better served by one prompt per concept, even at the cost of
  extra keystrokes.
- *Hardcode `distinct=type` and skip the prompt*: Rejected. The whole value
  of a count endpoint is the choice of grouping attribute. Removing the
  prompt would force operators to edit code for every common use case.
