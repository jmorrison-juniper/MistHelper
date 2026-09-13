# Phase 0 Research: countOrgAssetsByDistanceField

This document captures the research decisions made before producing the Phase 1
design artifacts. Each task follows the Decision / Rationale / Alternatives
Considered format mandated by the constitution.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the endpoint through the `mistapi` SDK call

```python
mistapi.api.v1.orgs.stats_assets.countOrgAssetsByDistanceField(
    mist_session=session,
    org_id=org_id,
    distinct=distinct_field,
    limit=limit,
)
```

The call returns a `mistapi.APIResponse` whose `.data` attribute is a dict with
the shape documented in
`documentation/api/orgs/GET_orgs_org_id_stats_assets_count.md`:

```text
{
  "distinct": "<field name echoed back>",
  "start":    <epoch seconds>,
  "end":      <epoch seconds>,
  "limit":    <int, default 100>,
  "total":    <int, total assets matched>,
  "results":  [ { "count": <int>, "<distinct>": "<value>" }, ... ]
}
```

`results[]` carries one bucket per distinct value; each bucket has a required
`count` field plus the distinct attribute key as an extra string property
(OpenAPI `additionalProperties: { type: string }`).

**Rationale**: The enriched per-endpoint doc lists the canonical SDK module as
`mistapi.api.v1.orgs.stats_-_assets.countOrgAssetsByDistanceField()`. The
hyphen-dash in the URL fragment is a doc-rendering artefact -- in Python the
module path is `mistapi.api.v1.orgs.stats_assets`. Pagination is supported via
`limit` (and `page` if the response indicates more buckets), but for a count
endpoint the default limit of 100 is sufficient for nearly all distinct fields
and matches what adjacent count endpoints (e.g. `countOrgDevicesByDistinct`)
use.

**Alternatives Considered**:

- *Raw `requests.get` against the URL template.* Rejected -- violates the
  established constraint that the `mistapi` SDK is the sole permitted Mist
  Cloud interface (authentication, retry, rate-limit metrics, and host
  selection are already centralised there).
- *Auto-paginate with `page` until `len(results) < limit`.* Rejected for v1
  scope. The default `limit=100` covers every distinct field exposed by the
  Mist asset stats endpoint today; auto-pagination can be added later if a
  user reports truncation. Keeping the first cut single-page also preserves
  the <=5s performance budget.

## Research Task 2: Primary Key Strategy

**Decision**: Use **two related tables** with distinct PK strategies:

- `org_assets_count_summary` -- `composite_pk` on
  `('org_id', 'distinct', 'start', 'end')`. One summary row per invocation
  window.
- `org_assets_count_results` -- `composite_pk` on
  `('org_id', 'distinct', 'start', 'end', 'bucket_value')`. One bucket row
  per distinct value within that window.

Register a single entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` under the
operationId `countOrgAssetsByDistanceField` describing the summary table; the
results table is created on first write by `DataExporter` using the same
composite-key extension.

**Rationale**: The endpoint returns an aggregate envelope with no natural UUID
(`results[]` items lack any stable identifier other than the distinct value
itself). The `(org_id, distinct, start, end)` tuple is stable per invocation
window and lets `INSERT OR REPLACE` upsert cleanly when the user re-runs the
menu item over the same window. The `auto_increment_with_unique` strategy
would have worked for the summary but loses the natural query key
(`WHERE org_id=? AND distinct=?`) that downstream reporting needs.

**Alternatives Considered**:

- *Single flat table joining summary + bucket on every row.* Rejected --
  denormalises the envelope fields (`limit`, `total`, `start`, `end`) into
  every bucket row, inflating SQLite size and breaking the established
  two-table pattern used by similar count endpoints.
- *`auto_increment_with_unique` on the summary only.* Rejected -- the surrogate
  key offers no semantic value and complicates re-runs (each run produces a
  new row even when nothing changed).

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV summary file: `data/org_<org_id>_assets_count_<distinct>_summary.csv`
- CSV results file: `data/org_<org_id>_assets_count_<distinct>_results.csv`
- SQLite tables: `org_assets_count_summary` and `org_assets_count_results`
  (both in `data/mist_data.db`)
- ArangoDB collections (when polyglot backend active):
  `org_assets_count_summary` (document) and `org_assets_count_results`
  (document, edge-linked to the summary by composite key)
- Redis keys: `mh:org:<org_id>:assets_count:<distinct>:summary` and
  `mh:org:<org_id>:assets_count:<distinct>:results` (TTL per existing cache
  policy)

**Rationale**: Filenames follow the established `org_<org_id>_<entity>_<...>`
convention used by adjacent stats exports. Including the `<distinct>` field
in the filename keeps runs against different distinct attributes from
overwriting each other on the CSV backend. SQLite table names are
distinct-agnostic because the `distinct` column inside the row already
discriminates.

**Alternatives Considered**:

- *Omit `<distinct>` from the filename.* Rejected -- a user who runs the
  menu twice (once with `distinct=map_id`, once with `distinct=mac`) would
  silently overwrite the first CSV.
- *Per-distinct SQLite tables (one per distinct field).* Rejected --
  explodes the schema and breaks the "one operation = one logical table"
  convention.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation in the **Stats** cluster (existing
range 80-91) at proposed menu number **91**, immediately before the viewer
block (92-96).

**Rationale**: The endpoint is a server-side aggregate over org-scoped
asset stats -- functionally adjacent to the existing `org_*_stats` operations
in 80-91. The next free integer at the time of writing is 91; the slot keeps
the existing categorical grouping intact (Stats then Viewers then resource-
intensive then WebSocket). The exact number will be re-verified at
`/speckit.tasks` time so that any number reused by a parallel in-flight
spec is detected before the implementation PR opens.

**Alternatives Considered**:

- *Place in the Safe Org Exports cluster (1-59).* Rejected -- that cluster
  holds simple list/get exports, not aggregate counts; mis-categorisation
  would make discovery harder.
- *Defer assignment until task generation.* Rejected -- the plan must commit
  to a concrete proposal so reviewers can sanity-check overlap with sibling
  feature branches.

## Research Task 5: Required User Prompts

**Decision**:

| Prompt          | Source                             | Context label                       | Default / Validation |
|-----------------|-------------------------------------|-------------------------------------|----------------------|
| `org_id`        | `safe_input()` (with `.env` fallback to `MIST_ORG_ID`) | `org_assets_count:org_id`   | Required; Mist UUID shape validated before SDK call. |
| `distinct`      | `safe_input()`                      | `org_assets_count:distinct`         | Optional; if blank, the API default (server-decided, typically `map_id`) is used. Free-text but trimmed and lower-cased. |
| `limit`         | `safe_input()`                      | `org_assets_count:limit`            | Optional; coerced to int; defaults to 100 if blank or non-numeric. |

API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) are loaded from `.env` by
the existing `mistapi.APISession` -- the menu method never prompts for them
and never logs them.

**Rationale**: The endpoint requires only `org_id` (path) and accepts two
optional query parameters. Following the established MistHelper convention,
required identifiers come from prompts (with `.env` fallback for unattended
runs), and credentials come exclusively from `.env`. `safe_input()` ensures
SSH/container EOF exits cleanly per Principle III.

**Alternatives Considered**:

- *Prompt for `MIST_ORG_ID` even when present in `.env`.* Rejected -- breaks
  the unattended-run pattern used by `--test` mode and by SSH automation.
- *Hard-code `distinct=map_id`.* Rejected -- one of the main values of this
  endpoint is letting the operator pivot the count by different attributes
  (e.g. `mac`, `device_name`, `map_id`) without writing custom code.
