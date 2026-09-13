# Phase 0 Research: countOrgBgpStats

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Use `mistapi.api.v1.orgs.stats_-_bgp_peers.countOrgBgpStats(apisession,
org_id, distinct=None, state=None, limit=100)`.

**Rationale**: The enriched per-endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_stats_bgp_peers_count.md` documents the SDK
path as `mistapi.api.v1.orgs.stats_-_bgp_peers.countOrgBgpStats()`. The HTTP
contract is `GET /api/v1/orgs/{org_id}/stats/bgp_peers/count` with one required path
parameter (`org_id`) and three optional query parameters (`state`, `distinct`,
`limit` default 100). The 200 response is a single object with `distinct` (string),
`start` / `end` / `total` / `limit` (int32), and `results` -- an array of bucket
objects each carrying a required `count` integer plus arbitrary string-valued
`additionalProperties` whose key matches the requested `distinct` field
(e.g. `vrf_name`, `state`, `neighbor_as`). The SDK returns the parsed JSON body via
`.data` on the response wrapper, matching the convention of every other
`mistapi.api.v1.orgs.stats_-_*` function already used in MistHelper.

**Alternatives Considered**:

- *Direct REST via `requests` with manual auth header* -- rejected; violates the
  Constitution constraint that `mistapi` is the sole permitted interface to Mist
  Cloud and would duplicate retry / rate-limit logic that `mistapi.APISession`
  already provides.
- *Call `searchOrgBgpStats` and aggregate client-side* -- rejected; pulls the full
  peer list (potentially thousands of rows) just to count them, defeating the
  point of the dedicated `/count` endpoint and burning the 5,000 calls/hour token
  budget.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` with key
`(org_id, distinct_field, distinct_value, state_filter)`.

**Rationale**: The endpoint returns aggregate bucket rows, not entities with stable
UUIDs. Each row is uniquely identified by the org it was queried against, the
`distinct` field selected (e.g. `vrf_name`), the actual distinct value reported in
the bucket (e.g. `default`), and the optional `state` query filter that produced
the count. Composite-PK upsert (`INSERT OR REPLACE`) gives clean re-run behavior:
re-counting the same org with the same distinct field overwrites prior buckets
rather than duplicating them, while changing the `distinct` field or `state`
filter creates new rows for the new slice. A surrogate `auto_increment_with_unique`
PK would silently accumulate duplicates on repeated runs unless the unique
constraint was set to exactly this 4-tuple -- which is just a composite PK by
another name. A pure `natural_pk` is impossible because the API supplies no row
identifier.

**Alternatives Considered**:

- *`natural_pk` on `(distinct_field, distinct_value)`* -- rejected; collides across
  orgs and across `state` slices.
- *`composite_pk` with `query_timestamp` included* -- rejected for the bucket
  table; storing every poll as a new row turns the count endpoint into an
  unbounded time series and breaks the upsert semantics every other count
  endpoint in the codebase will use. A separate small `*_runs` summary table
  captures per-invocation metadata (start, end, total, limit, timestamp) without
  bloating the bucket table.
- *`auto_increment_with_unique`* -- rejected for the same reason; the four-column
  unique constraint required to dedupe is functionally identical to a composite
  PK and adds an unused surrogate column.

## Research Task 3: Output Filename and SQLite Table

**Decision**: CSV filename `data/org_bgp_stats_count_{org_id}_{distinct}.csv`;
SQLite bucket table `org_bgp_stats_count`; SQLite summary table
`org_bgp_stats_count_runs`.

**Rationale**: The CSV filename embeds the `org_id` and the `distinct` field so
that running the menu against multiple distinct slices (e.g. `vrf_name`,
`neighbor_as`, `state`) produces side-by-side files instead of overwriting. The
SQLite table names follow the existing convention used by adjacent stats exports
(`org_<resource>_<verb>` -- e.g. `org_devices_stats`, `org_bgp_stats` for the
search endpoint, so `org_bgp_stats_count` is the natural extension). A second
small `*_runs` table records one row per invocation with the response-level scalars
(`distinct`, `start`, `end`, `limit`, `total`) joined back to the bucket rows via
`(org_id, distinct_field, state_filter)`. This separation keeps the bucket table
compact while still preserving query metadata for debugging.

**Alternatives Considered**:

- *Single flat table mixing bucket rows and run metadata* -- rejected; either
  repeats scalar metadata on every bucket row (storage waste, update anomalies)
  or leaves NULL columns on rows that do not need them.
- *No SQLite table -- CSV only* -- rejected; breaks the multi-backend invariant
  required by `DataExporter.write_with_format_selection()`.
- *Filename without `distinct` token* -- rejected; would silently overwrite a
  prior CSV when the user runs against a different distinct field.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place at menu number **96**, inside the Interactive Safe / Viewers
cluster (92-96) immediately adjacent to the existing org-stats block (80-91) and
above spec 500's proposed slot 95.

**Rationale**: Per the project menu taxonomy documented in
`.github/copilot-instructions.md`: 80-91 are Stats, 92-96 are Viewers, 97-101 are
Resource Intensive, and 154-194 are Destructive. A count endpoint is a small,
read-only viewer over aggregated stats and therefore belongs in the 92-96 viewer
slice. Slot 95 is provisionally claimed by spec 500
(`GetOrgLicenseAsyncClaimStatus`); slot 96 is the next free integer in the same
cluster. The proposal will be re-verified at `/speckit.tasks` time; if 96
collides with another in-flight feature branch, the task generator picks the next
free integer in the same cluster.

**Alternatives Considered**:

- *Append to the destructive block 154-194* -- rejected; the endpoint is GET
  only, no write side-effect, and placing read-only operations in the
  destructive block would force unrelated confirmation prompts.
- *Squeeze into 80-91 stats block* -- rejected; that block is already saturated
  and reserved for the existing per-device / per-site stats exports.
- *Defer to a future menu re-numbering pass* -- rejected; the spec must ship a
  concrete number so the README operation count and CHANGELOG entry can be
  written deterministically.

## Research Task 5: Required User Prompts

**Decision**: Four prompts, all via `safe_input()`. Defaults supplied from `.env`
where available.

| Order | Prompt label                              | Required? | Default source                | Validation                              |
|-------|-------------------------------------------|-----------|-------------------------------|-----------------------------------------|
| 1     | `Org ID (UUID)`                           | Yes       | `MIST_ORG_ID` env var         | Mist UUID regex; reject empty           |
| 2     | `BGP state filter (blank = all)`          | No        | blank                         | Accept blank or one of `established` / `idle` / `connect` / `active` / `opensent` / `openconfirm` |
| 3     | `Distinct attribute (default: vrf_name)`  | Yes       | literal `vrf_name`            | Non-empty string                        |
| 4     | `Limit (default: 100)`                    | No        | literal `100`                 | Integer 1..1000                         |

**Rationale**: `org_id` is the only path parameter and is therefore required; it
defaults to `MIST_ORG_ID` from `.env` so a junior NOC engineer running in
single-org mode never has to paste a UUID. `state` is optional in the API and is
typically left blank to count peers across all states; offering it as the second
prompt with a blank default keeps the common case one keystroke long. `distinct`
is technically optional in the API but practically required -- without it the API
returns one bucket totalling all peers, which is the same information as `total`
in the summary header and not worth exporting -- so MistHelper supplies a sensible
default (`vrf_name`, the most common slice) but always sends a value. `limit`
defaults to the API's own default (100) but is exposed so power users can request
larger result sets up to the documented 1000 cap. All four prompts pass through
`safe_input()` with explicit `context=` strings (`org_bgp_count:org_id`,
`:state`, `:distinct`, `:limit`) so EOF in an SSH or container session exits 0
without a traceback.

**Alternatives Considered**:

- *No prompts -- pull everything from `.env`* -- rejected; the `distinct` and
  `state` parameters are intentionally per-invocation choices, and embedding
  them in `.env` would force file edits every time a NOC engineer wanted a
  different slice.
- *Single combined "give me a JSON blob of parameters" prompt* -- rejected;
  violates the safety-first principle (one decision per prompt), is harder for
  junior NOC engineers to use correctly, and breaks EOF-handling semantics.
- *Skip the `limit` prompt and hard-code 1000* -- rejected; surprises users who
  expect the API's documented default of 100 and silently changes back-end cost
  on every invocation.
