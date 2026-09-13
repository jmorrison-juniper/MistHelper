# Phase 0 Research: countSiteWanClients

**Feature**: 563-mist-count-site-wan-clients
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Authoritative endpoint doc**:
`documentation/api/sites/GET_sites_site_id_wan_clients_count.md`

This document captures the five required Phase 0 research outputs. Each task follows the
Decision / Rationale / Alternatives Considered format mandated by the constitution.

---

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the SDK as

```python
from mistapi.api.v1.sites.wan_clients import count as wan_clients_count

response = wan_clients_count.countSiteWanClients(
    apisession,
    site_id=site_id,
    distinct=distinct,           # optional string facet, e.g. "mac", "hostname", "ip"
    start=start_epoch,           # optional int epoch seconds or relative string
    end=end_epoch,               # optional int epoch seconds or relative string
    duration=duration,           # optional duration string, default "1d"
    limit=limit,                 # optional int, default 100
)
```

The SDK returns a `mistapi.APIResponse` object; the JSON body is in
`response.data` and the HTTP status in `response.status_code`. The body shape per the
enriched doc is:

```json
{
  "distinct": "<echoed facet name>",
  "start":    <int epoch seconds>,
  "end":      <int epoch seconds>,
  "limit":    <int>,
  "total":    <int total clients matched>,
  "results":  [ { "count": <int>, "<facet>": "<value>" }, ... ]
}
```

**Rationale**: The enriched endpoint doc at
`documentation/api/sites/GET_sites_site_id_wan_clients_count.md` lists the SDK module
path as `mistapi.api.v1.sites.clients_-_wan.countSiteWanClients()`. The spec's canonical
SDK module is `mistapi.api.v1.sites.wan_clients.count`; the doc's dash-spelling is a
display artifact. Both resolve to the same generated function in mistapi 0.59+. The
documented query parameters (`distinct`, `start`, `end`, `duration`, `limit`) match the
OpenAPI schema, including the `duration` default of `1d` and the `limit` default of
`100`. The response schema requires `distinct, end, limit, results, start, total`, so
every output column is safe to assume present on a 200.

**Alternatives Considered**:

- Direct `requests.get()` against `https://{host}/api/v1/sites/{site_id}/wan_clients/count`
  with manual header injection -- rejected. The constitution mandates `mistapi` as the
  sole interface to Mist Cloud and the SDK already handles pagination, retries, the
  adaptive delay system, and rate-limit back-off.
- Using `mistapi.api.v1.sites.clients_-_wan.countSiteWanClients` with the dashed name --
  rejected. Python identifiers cannot contain dashes; the actual generated module is
  `wan_clients.count` (verified by the file layout convention used by other catalog
  specs).

---

## Research Task 2: Primary Key Strategy

**Decision**: Use **`composite_pk`** with two tables:

1. `site_wan_clients_count_summary` -- one row per invocation describing the request /
   response envelope. PK = `(site_id, distinct, start_epoch, end_epoch)`.
2. `site_wan_clients_count_buckets` -- one row per element in `results[]`. PK =
   `(site_id, distinct, start_epoch, end_epoch, distinct_value)`.

Registered as a single `ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteWanClients']` entry
of type `composite_pk` describing the buckets table (the canonical row-per-bucket
output); the summary table is created by the exporter as a sibling envelope table per
the existing pattern for count endpoints.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteWanClients'] = {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'distinct', 'start_epoch', 'end_epoch', 'distinct_value'],
    'indexes': ['site_id', 'distinct', 'start_epoch'],
}
```

**Rationale**: The endpoint returns aggregated counts that are valid only within their
time window plus distinct facet. The composite (`site_id`, facet name, time window,
facet value) uniquely identifies each bucket; re-running the same query within the same
window upserts cleanly, while changing any of those inputs produces a new row.
`natural_pk` does not fit because there is no API-issued stable id. `auto_increment_with_unique`
would lose the cross-run idempotency that other count-endpoint specs already
established (precedent: similar grouping-count specs in this catalog batch).

**Alternatives Considered**:

- `natural_pk = ['id']` -- rejected. The response contains no `id` field.
- `auto_increment_with_unique` with the composite as the unique key -- rejected as
  redundant. A pure composite PK gives identical idempotency without a surrogate
  column and matches the pattern documented in `.github/copilot-instructions.md` under
  Database Strategy for time-series / aggregated endpoints.
- One denormalized table with a JSON-blob bucket column -- rejected. SQLite queries
  against blob columns are inefficient and break the multi-backend contract that
  ArangoDB and Redis assume column-shaped rows.

---

## Research Task 3: Output Filename & SQLite Table

**Decision**:

- CSV summary file: `data/site_wan_clients_count_summary_<site_id>_<distinct>_<UTC_TS>.csv`
- CSV buckets file: `data/site_wan_clients_count_buckets_<site_id>_<distinct>_<UTC_TS>.csv`
- SQLite tables (created by `DataExporter` on first run):
  - `site_wan_clients_count_summary`
  - `site_wan_clients_count_buckets`
- ArangoDB collections: same names as the SQLite tables.
- The DataExporter call signature is:

  ```python
  exporter.write_with_format_selection(
      data=summary_rows,
      filename="site_wan_clients_count_summary",
      api_function_name="countSiteWanClients",
  )
  exporter.write_with_format_selection(
      data=bucket_rows,
      filename="site_wan_clients_count_buckets",
      api_function_name="countSiteWanClients",
  )
  ```

**Rationale**: The naming follows the established `<scope>_<resource>_<operation>`
convention used by other count-style endpoint specs and keeps the related summary /
buckets pair clustered alphabetically in `data/`. The `api_function_name` passes the
operationId straight into `ENDPOINT_PRIMARY_KEY_STRATEGIES` lookup so the PK contract
is honored on every backend.

**Alternatives Considered**:

- Single denormalized `site_wan_clients_counts` table -- rejected. Hides the time
  window envelope and forces every consumer to re-derive total / limit / distinct from
  bucket rows.
- Filename based on operationId (`countSiteWanClients.csv`) -- rejected. Loses the
  site / facet discriminators that make on-disk forensics tractable.

---

## Research Task 4: Menu Category Placement & Menu Number

**Decision**: Place at menu number **96** in the Interactive-Safe Site-Stats / Viewers
cluster (60-96). Insertion point is immediately after the most recent site-clients
viewer in the existing menu registration block. The menu label is:

```
96. Site WAN Clients - Count by Distinct Attribute
```

**Rationale**: The endpoint is read-only, scoped to a single `site_id`, and returns
aggregated stats -- exactly the profile of operations 80-91 (site stats) and 92-96
(viewers). Slot 96 is the last free integer below the resource-intensive 97-101 block
and keeps WAN-client operations clustered together (WAN-client search and WAN-client
events count both live in this neighborhood per the catalog map in
`.github/copilot-instructions.md`). The full menu list is re-verified at
`/speckit.tasks` time; if 96 collides with another in-flight branch, the next free
integer in the 60-96 cluster is used and both the plan and spec headers are updated in
the same PR.

**Alternatives Considered**:

- Place in Safe Org Exports (1-59) -- rejected. The endpoint is site-scoped, not
  org-scoped.
- Place in Resource Intensive (97-101) -- rejected. The endpoint is a single
  light-weight GET with bounded response size.
- Place in Destructive (154-194) -- rejected. The endpoint is strictly read-only.

---

## Research Task 5: Required User Prompts

**Decision**: The new menu method prompts the user via `safe_input()` for the
following, in order. Defaults are accepted by pressing Enter on an empty input.

| # | Prompt label | Source on default | Required? | Validation |
|---|---|---|---|---|
| 1 | `site_id` | `MIST_DEFAULT_SITE_ID` from `.env` if set, else no default | Yes | Mist UUID shape (8-4-4-4-12 hex) |
| 2 | `distinct` (facet, e.g. `mac`, `hostname`, `ip`, `port_id`) | None (API default behaviour applies) | No | Lowercase alphanumeric + underscore, <= 32 chars |
| 3 | `duration` (e.g. `1d`, `7d`, `2w`) | `1d` | No | Regex `^\d+[hdw]$` |
| 4 | `start` | None | No | Integer epoch seconds OR relative string `-?\d+[hdwm]` |
| 5 | `end` | None | No | Same as `start` |
| 6 | `limit` | `100` | No | Integer 1..1000 |

Required identifiers come from the user (with `MIST_DEFAULT_SITE_ID` providing the
default when present). The API token and host come from `.env`
(`MIST_HOST`, `MIST_API_TOKEN`) via the existing `mistapi.APISession` -- never prompted
and never logged. Org ID is not required by this endpoint and is not prompted.

**Rationale**: The OpenAPI schema marks only `site_id` as required. Time-window
parameters are mutually compatible: when `start` and `end` are both empty, `duration`
governs the lookback; when `start` and `end` are both provided, the API ignores
`duration`. Defaulting `duration` to `1d` matches the OpenAPI default and gives the
junior NOC engineer a working out-of-the-box invocation that returns same-day data.

**Alternatives Considered**:

- Prompt for `org_id` first and derive `site_id` from a listing call -- rejected.
  Adds an unrelated API round-trip and runs counter to other site-scoped endpoints in
  the same cluster which take `site_id` directly.
- Skip all optional prompts and always invoke with the API defaults -- rejected. The
  `distinct` facet is the entire point of this endpoint; not letting the user pick it
  reduces the operation to a single-row total count.
- Read all parameters from `.env` -- rejected. The window and facet are
  per-invocation, not per-environment.
