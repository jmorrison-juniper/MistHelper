# Phase 0 Research: countSiteBgpStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_stats_bgp_peers_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.stats.bgp_peers.count.countSiteBgpStats(apisession,
site_id, state=None, distinct=None, limit=100)`. The SDK returns a `mistapi.APIResponse`
object whose `.data` attribute is the parsed JSON body. The body is a single JSON object
(not paginated at the SDK level but the response itself embeds `start`/`end`/`limit`
fields), with the following top-level keys per the doc:

- `distinct` (string) -- the distinct attribute the API actually grouped by.
- `start` (int32 epoch seconds) -- start of the window the count covers.
- `end` (int32 epoch seconds) -- end of the window the count covers.
- `limit` (int32) -- the effective row limit applied (default 100).
- `total` (int32) -- total number of buckets available (may exceed `limit`).
- `results` (array, uniqueItems=true) -- one element per distinct bucket. Each element is
  an object with a required `count` (int32) field plus additional string properties whose
  names depend on the `distinct` argument (e.g. when `distinct=state` the bucket object
  is `{"state": "Established", "count": 7}`; when `distinct=neighbor_as` the bucket is
  `{"neighbor_as": "65000", "count": 3}`).

Required path parameter: `site_id` (UUID string).
Optional query parameters: `state` (string filter -- restricts the dataset before
counting), `distinct` (string -- the attribute to group by; defaults to a server-side
value when omitted), `limit` (integer; SDK default 100).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.sites.stats_-_bgp_peers.countSiteBgpStats()` (using a tag-derived dotted
name). The mistapi SDK historically generates module paths from the URL (Python cannot
import a module containing `-`), so the runtime path is
`mistapi.api.v1.sites.stats.bgp_peers.count`. The spec.md names exactly that path. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.stats.bgp_peers import count; help(count)"` inside
the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/stats/bgp_peers/count`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...sites.stats_-_bgp_peers...`).* Rejected --
   Python identifier rules forbid `-` in module names; the SDK normalizes the path from
   the URL, and the spec.md (the authoritative feature contract) names the URL-based
   path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table `site_bgp_stats_count`:

- PK = `(site_id, distinct_field, distinct_value)`
  - `site_id` is the UUID supplied by the user; MistHelper injects it before write (the
    API does not echo it in the body).
  - `distinct_field` is the value of the `distinct` query argument actually used for the
    call (the API echoes it back in the top-level `distinct` field, so MistHelper reads
    it from there rather than re-using the caller's input).
  - `distinct_value` is the bucket-specific value pulled from each `results[]` element
    (e.g. `"Established"` when `distinct=state`). MistHelper extracts this generically
    by taking the single non-`count` key out of each bucket dict.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`. The
`indexes` list includes `state` (so post-import queries can filter by BGP state quickly)
and `distinct_field` (so callers can scope to all rows from a particular grouping run).

**Rationale**:
The endpoint reports *current-state* counts grouped by an attribute. Re-running the menu
item with the same `distinct` parameter must update existing buckets rather than append
duplicate rows. `(site_id, distinct_field, distinct_value)` is the natural identifier:
- Two different sites cannot share a bucket row (the `site_id` distinguishes them).
- Two different distinct groupings (e.g. `state` vs `neighbor_as`) live side by side in
  the same table -- `distinct_field` separates them.
- Within one grouping, `distinct_value` is the unique bucket label (the OpenAPI schema
  declares `results` as `uniqueItems=true`, guaranteeing this).

`INSERT OR REPLACE` upserts every poll's view of the counts.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots, defeating the upsert behavior the spec requires.
2. *`natural_pk` on a single column derived from concatenating site/distinct/value.*
   Rejected -- breaks SQL query ergonomics. Composite PKs let users filter by
   `distinct_field` or `site_id` alone without parsing a synthetic key.
3. *Composite PK that includes a `polled_at_utc` timestamp.* Rejected for the primary
   row table -- that would defeat upsert and accumulate history. (A `polled_at_utc`
   field is still stored as a non-key column for audit, so the latest poll time is
   visible per row.)

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_bgp_stats_count_<distinct_field>.csv`
- SQLite table: `site_bgp_stats_count` (single table, all distinct groupings share it,
  separated by the `distinct_field` PK column).
- `site_id_short` is the first 8 hex characters of the site UUID -- already the
  convention used by adjacent site-scoped exports in MistHelper for human-readable
  filenames without leaking full UUIDs into shell history.
- `<distinct_field>` is the actual grouping attribute (e.g. `state`, `neighbor_as`,
  `vrf_name`), sanitized via `str.replace("/", "_").lower()` for filesystem safety.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countSiteBgpStats"` (matching the operationId). The DataExporter uses that string
as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent site-scoped stats exports
(`site_<short>_bgp_peers_search.csv`, `site_<short>_gateway_metrics.csv`). A single
SQLite table keeps schema migrations minimal -- the same `site_bgp_stats_count` table
serves every distinct grouping a user might pick. CSV filenames are differentiated by
`<distinct_field>` so successive runs with different groupings produce inspectable side-
by-side files in `data/` without overwriting each other.

**Alternatives Considered**:

1. *One SQLite table per `distinct` value (`site_bgp_stats_count_state`,
   `site_bgp_stats_count_neighbor_as`, ...).* Rejected -- explodes the schema and forces
   a new DDL emit every time a user picks a new `distinct` parameter. The single-table
   plus-`distinct_field`-column design handles all groupings uniformly.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell history
   and `ls` output unnecessarily. The 8-char short form is enough to disambiguate
   locally.
3. *JSON-encoded `results` array in one row.* Rejected -- breaks SQL queryability and
   conflicts with the flattening convention used everywhere else in MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting inside the Site Stats cluster
(80-91 per the copilot-instructions menu table). Category label: "Safe Site Exports --
Stats (BGP)".

**Rationale**:
The copilot-instructions menu range table lists:
1-59 Safe Org Exports, 60-96 Interactive Safe (60-72 Site devices, 73-79 Insights,
**80-91 Stats**, 92-96 Viewers), 97-101 + 153 Resource Intensive, 102-123 WebSocket,
124-152 Interactive, 154-194 Destructive. A BGP peer **count** operation belongs in the
Stats sub-cluster, so 91 is the natural slot -- the highest still-free Stats integer
before the Viewers range begins at 92. The number is provisional -- at `/speckit.tasks`
time, `MistHelper.py` is grep'd for the latest allocated menu integer and 91 is shifted
forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Viewers (92-96).* Rejected -- this endpoint returns a count aggregation,
   not a live viewer / dashboard. It is a stats query and belongs in the Stats
   sub-range.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single GET
   that returns at most `limit` (default 100) small bucket rows. It is not long-running.
3. *Append at end (e.g. 195).* Rejected -- the destructive cluster ends at 194, and
   placing a read-only stats count above the destructive block visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **up to four** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context: `"count_site_bgp_stats:site_id"`.
   Default: the value of `MIST_SITE_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `state` -- prompt: `"BGP state filter (blank for all): "`, context:
   `"count_site_bgp_stats:state"`. Default: empty string (no filter). Passed to the SDK
   as `state=None` when blank; otherwise as the user's string verbatim.
3. `distinct` -- prompt:
   `"Distinct attribute to count by [state | neighbor_as | vrf_name | type] (default: state): "`,
   context: `"count_site_bgp_stats:distinct"`. Default: `state`. Passed to the SDK as
   `distinct=<value>`. The four suggested values reflect the most operationally useful
   groupings; the SDK accepts any string the API will recognize.
4. `limit` -- prompt: `"Row limit (1-1000, default 100): "`, context:
   `"count_site_bgp_stats:limit"`. Default: `100`. Coerced to int, clamped to
   `[1, 1000]`. Passed to the SDK as `limit=<int>`.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.
- `MIST_ORG_ID` -- not consumed by this endpoint, but loaded as part of the standard
  MistHelper bootstrap.

**Rationale**:
Mist's BGP-stats-count endpoint is site-scoped (no org_id in the URL). The other three
parameters are optional but operationally important: `state` filters the dataset before
counting; `distinct` controls the grouping axis; `limit` caps the result rows. Asking
the user keeps the menu item flexible while still working zero-touch when defaults are
accepted (Enter through every prompt produces `state=None, distinct=state, limit=100` --
the most common "what is the distribution of BGP peer states at this site?" query).

**Alternatives Considered**:

1. *Single prompt for `site_id` only; hard-code `distinct=state`.* Rejected -- the
   endpoint's whole purpose is configurable grouping; collapsing to one grouping wastes
   the API's flexibility and forces a second menu item for every other grouping.
2. *Free-form prompt for query parameters (`?state=...&distinct=...`).* Rejected --
   error-prone for a junior NOC engineer; structured prompts with defaults are safer.
3. *Skip `limit` and rely on SDK default.* Rejected -- exposing `limit` lets operators
   sample large groupings without code change and lets the test sweep run with `limit=1`
   for a fast smoke test.
