# Phase 0 Research: countSiteNacClientEvents

This document records the five Phase 0 decisions that ground the implementation plan
for the Mist API endpoint `GET /api/v1/sites/{site_id}/nac_clients/events/count`
(operationId `countSiteNacClientEvents`). Source-of-truth doc:
`documentation/api/sites/GET_sites_site_id_nac_clients_events_count.md`.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the endpoint through the `mistapi` SDK module
`mistapi.api.v1.sites.nac_clients.events.count` using the call:

```python
mistapi.api.v1.sites.nac_clients.events.count.countSiteNacClientEvents(
    mist_session,            # APISession built from MIST_HOST + MIST_API_TOKEN in .env
    site_id,                 # UUID string, required path parameter
    distinct="type",         # optional - default "type"; accepts any NAC event distinct field
    type=None,               # optional - filter by a specific NAC event type (see listNacEventsDefinitions)
    start=None,              # optional - epoch seconds or relative string ("-1d", "-1w")
    end=None,                # optional - epoch seconds or relative string ("now", "-1h")
    duration="1d",           # optional - default "1d"; accepts "7d", "2w", etc.
    limit=100,               # optional - default 100; caps the number of distinct buckets returned
)
```

The function returns a `mistapi.APIResponse` whose `.data` attribute is a single JSON
envelope object with six keys: `distinct`, `start`, `end`, `limit`, `total`, and
`results` (an array of `{count, <distinct_field_value>}` objects).

**Rationale**: The enriched per-endpoint doc lists the SDK module verbatim
(`mistapi.api.v1.sites.clients_-_nac.countSiteNacClientEvents()` is the legacy doc
spelling; the canonical Python import path is `mistapi.api.v1.sites.nac_clients.events.count`,
matching how other site / nac_clients / events / count endpoints are exposed in
`mistapi` 0.59+). The query-parameter set and defaults (`distinct`, `type`, `start`,
`end`, `duration=1d`, `limit=100`) come directly from the doc's Query Parameters table.
The response envelope shape is taken verbatim from the doc's 200 JSON schema.

**Alternatives Considered**:
- Calling the raw HTTP endpoint via `requests`: rejected -- violates Constitution
  dependency rule that `mistapi` is the sole permitted interface to Mist Cloud.
- Reusing the org-level counterpart `countOrgNacClientEvents` and filtering client-side
  by `site_id`: rejected -- the org endpoint requires the user to know an `org_id` and
  forces extra rows over the wire; the site-scoped endpoint is the correct least-privilege
  choice for a site-bound question.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` with primary key
`(site_id, distinct_attribute, distinct_value, query_window_start, query_window_end)`
for the per-bucket results table, and `composite_pk` with primary key
`(site_id, distinct_attribute, query_window_start, query_window_end)` for the summary
envelope table.

**Rationale**: The API response carries no stable record-level UUID -- each "result"
row is an aggregated bucket `{count, <field_value>}` valid only for a specific
`(site, distinct attribute, time window)` tuple. Two re-runs of the same query (same
site, same distinct attribute, same window) must upsert into the same rows so SQLite
does not accumulate duplicates. Including the query window in the PK lets the user
re-run the same count over a different window (for example yesterday vs today) and
keep both rows side-by-side for trending. This matches the documented
`composite_pk` pattern used by other time-series Mist endpoints registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:
- `natural_pk` on a single field: rejected -- no API-provided stable UUID exists on
  these aggregate rows.
- `auto_increment_with_unique` on `misthelper_internal_id`: rejected -- would let two
  identical re-runs create duplicate rows, defeating the user-visible "upsert" guarantee
  required by `searchSiteNacClientEvents`-adjacent operations.
- Omitting `query_window_start / query_window_end` from the PK: rejected -- a user who
  changes `duration` from `1d` to `7d` would silently clobber the prior result.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- Primary CSV / SQLite table for envelope: `site_nac_client_events_count_summary`
  (file `data/site_nac_client_events_count_summary.csv` when CSV backend is active).
- Secondary CSV / SQLite table for per-bucket results:
  `site_nac_client_events_count_results`
  (file `data/site_nac_client_events_count_results.csv` when CSV backend is active).
- The `api_function_name=` argument passed to `DataExporter.write_with_format_selection`
  is `"countSiteNacClientEvents"` -- the operationId verbatim, so PK strategy lookup
  works.

**Rationale**: Two tables are required because the response is a one-summary /
N-results envelope, not a flat list. The naming pattern mirrors existing site-scoped
exports (snake_case, prefixed with the entity scope `site_`, followed by the resource
`nac_client_events`, followed by the operation `count`, suffixed with `_summary` or
`_results`). Passing the operationId as `api_function_name` is the documented hook for
`DataExporter` to consult `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:
- A single flattened table with the envelope columns repeated on every result row:
  rejected -- denormalizes the data, bloats SQLite storage, and complicates SQL queries
  ("which distinct attribute was queried?" requires GROUP BY on a redundant column).
- File names without the `summary` / `results` suffix: rejected -- would collide with
  the existing `searchSiteNacClientEvents` output naming.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new menu item at **operation number 96** in the
"Interactive Safe Site" cluster (60-96). Final number is re-verified at task time by
grepping the monolith for the highest registered menu integer; if 96 is taken by an
in-flight feature branch the next free integer in the same cluster is used.

**Rationale**: The agents.md menu table defines the canonical category ranges:
60-72 site devices, 73-79 insights, 80-91 stats, 92-96 viewers, 97-101 resource
intensive. The new operation is site-scoped, read-only, and returns aggregate counts
-- a natural fit for the upper-end viewers / safe-site interactive block. Placing it
at 96 keeps it inside the default `--test` sweep range and adjacent to other
NAC-related read-only viewers, so users discover it next to
`searchSiteNacClientEvents`.

**Alternatives Considered**:
- 20-26 events block: rejected -- those operations are org-scoped event exports; the
  new operation requires a `site_id`, so site cluster placement is clearer for users.
- 97-101 resource-intensive block: rejected -- the endpoint is server-side aggregated,
  bounded by `limit=100`, and typically completes in <5s; it does not warrant the
  resource-intensive label.
- A new cluster: rejected -- agents.md explicitly defines five existing clusters; a
  sixth would require category-range bookkeeping changes outside the scope of this spec.

## Research Task 5: Required User Prompts

**Decision**: Prompt the user through `safe_input()` for the following five inputs, in
order, with sensible defaults so most users can press Enter to accept:

| Prompt | Source | Default | safe_input context= |
|--------|--------|---------|---------------------|
| `site_id` (UUID) | user | none (required, validated against UUID shape) | `"site_nac_events_count:site_id"` |
| `distinct` (event field to group by) | user | `type` | `"site_nac_events_count:distinct"` |
| `type` (filter to a specific NAC event type, optional) | user | empty (no filter) | `"site_nac_events_count:type"` |
| `duration` (time window, e.g. `1d`, `7d`, `2w`) | user | `1d` | `"site_nac_events_count:duration"` |
| `limit` (max distinct buckets returned, 1-1000) | user | `100` | `"site_nac_events_count:limit"` |

Credentials (`MIST_HOST`, `MIST_API_TOKEN`) come from `.env` via the existing
`mistapi.APISession` construction at MistHelper start-up -- never prompted, never
logged. `start` / `end` are not prompted directly; the user supplies `duration` instead,
matching the convention of adjacent search / count menu items. Power users who need an
exact `start` / `end` can edit the resulting code path or supply `start=<epoch>` via
`--menu 96 --start <epoch>` once CLI override support lands (out of scope for this spec).

**Rationale**: The constitution requires every user-facing input to flow through
`safe_input()` with an explicit context string for SSH / container EOF handling.
Defaults match the upstream Mist API defaults (`distinct=type` is the most common NAC
event grouping; `duration=1d` is the API default; `limit=100` is the API default), so
the menu is one-keypress friendly for the common case. Validating `site_id` against
the Mist UUID shape *before* the API call avoids a wasted round-trip and gives the
user a clearer error message.

**Alternatives Considered**:
- Prompt for `org_id` and let the user select a site from a list: rejected -- the
  org-to-sites picker is already available as a separate menu item; forcing it here
  doubles the prompt count and breaks the one-keypress flow for users who already
  have a `site_id` from earlier in the session.
- Skip optional prompts entirely and hard-code defaults: rejected -- the `distinct`
  parameter is the single most useful knob on this endpoint; hiding it would make the
  menu item nearly useless for any grouping other than `type`.
- Prompt for raw `start` and `end` epoch values: rejected -- error-prone for junior
  NOC engineers who think in relative windows ("last 24h"); `duration` is friendlier
  and the API accepts it directly.
