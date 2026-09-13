# Phase 1 Data Model: countOrgSites

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)

## Entity Overview

The endpoint returns one wrapping envelope object containing an array of count
buckets. MistHelper flattens this into two related entities so each table stays
flat-CSV friendly and SQLite-upsertable.

### Entity 1: `org_sites_count_summary`

One row per envelope (per call) capturing the request context and aggregate total.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `org_id` | TEXT (UUID) | injected by MistHelper (path parameter) | Primary key part. Foreign key to logical `orgs.id` in graph backends. |
| `distinct` | TEXT | response `distinct` | The grouping field name the API echoed back. Primary key part. |
| `start` | INTEGER (epoch seconds) | response `start` | Resolved start of the query window. Primary key part. |
| `end` | INTEGER (epoch seconds) | response `end` | Resolved end of the query window. Primary key part. |
| `limit` | INTEGER | response `limit` | Echoed page size limit. |
| `total` | INTEGER | response `total` | Sum across all buckets (constitutes the canonical answer to "how many sites match"). |
| `results_count` | INTEGER | computed `len(response["results"])` | Number of distinct buckets returned. Convenience field for fast SQL filters. |
| `captured_at` | TEXT (ISO 8601) | computed at call time | Wall-clock when MistHelper captured the snapshot. Useful when re-running with different `duration` values. |

**Primary Key**: `(org_id, distinct, start, end)` (composite)
**Foreign Keys**: `org_id` -> logical `orgs.id`

### Entity 2: `org_sites_count_results`

One row per bucket returned in the response `results[]` array.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `org_id` | TEXT (UUID) | injected by MistHelper | Primary key part + FK to summary. |
| `distinct` | TEXT | parent envelope | Primary key part + FK to summary. |
| `start` | INTEGER | parent envelope | Primary key part + FK to summary. |
| `end` | INTEGER | parent envelope | Primary key part + FK to summary. |
| `bucket_key` | TEXT | dynamic key from bucket (the value of the `distinct` field) | Primary key part. Always stringified for portability across distinct kinds. |
| `count` | INTEGER | bucket `count` | The per-bucket count (the only schema-fixed field in the bucket). |
| `captured_at` | TEXT (ISO 8601) | inherited from summary | For point-in-time analysis. |

**Primary Key**: `(org_id, distinct, start, end, bucket_key)` (composite)
**Foreign Keys**: `(org_id, distinct, start, end)` -> `org_sites_count_summary`

## State Transitions

**N/A -- read-only endpoint.** The Mist API exposes no lifecycle for count
snapshots. Each call produces an independent, immutable result; re-running with
the same parameters either re-fetches identical data (no change) or refreshes the
`captured_at` plus any drift in `total` / per-bucket `count`. Upsert semantics via
the composite primary key are the only state-management mechanism required.

## SQLite DDL

The DDL below is what `DataExporter` will materialize on the first successful run
when the SQLite backend is active. The two tables are created with `IF NOT EXISTS`
so subsequent runs are no-ops.

```sql
CREATE TABLE IF NOT EXISTS org_sites_count_summary (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL,
    start         INTEGER NOT NULL,
    end           INTEGER NOT NULL,
    limit         INTEGER,
    total         INTEGER NOT NULL,
    results_count INTEGER NOT NULL,
    captured_at   TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_sites_count_summary_org
    ON org_sites_count_summary(org_id);
CREATE INDEX IF NOT EXISTS idx_org_sites_count_summary_distinct
    ON org_sites_count_summary(distinct);

CREATE TABLE IF NOT EXISTS org_sites_count_results (
    org_id      TEXT    NOT NULL,
    distinct    TEXT    NOT NULL,
    start       INTEGER NOT NULL,
    end         INTEGER NOT NULL,
    bucket_key  TEXT    NOT NULL,
    count       INTEGER NOT NULL,
    captured_at TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end, bucket_key),
    FOREIGN KEY (org_id, distinct, start, end)
        REFERENCES org_sites_count_summary(org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_sites_count_results_org
    ON org_sites_count_results(org_id);
CREATE INDEX IF NOT EXISTS idx_org_sites_count_results_bucket
    ON org_sites_count_results(bucket_key);
```

Note: `distinct`, `start`, `end`, `limit`, and `count` are reserved SQL keywords;
the existing `DataExporter` already quotes column names when emitting DDL and DML
so the literal names above are safe.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

The dictionary lives at approximately line 1672 of `MistHelper.py`. Add the
following entry alongside the other `*OrgSites*` operations.

```python
"countOrgSites": {
    "type": "composite_pk",
    "primary_key": ["org_id", "distinct", "start", "end"],
    "child_tables": {
        "org_sites_count_results": {
            "type": "composite_pk",
            "primary_key": ["org_id", "distinct", "start", "end", "bucket_key"],
        }
    },
    "indexes": ["org_id", "distinct"],
    "table_name": "org_sites_count_summary",
    "description": (
        "Mist count by distinct attribute of sites -- one summary row plus N "
        "result-bucket rows per call. Upserts by (org_id, distinct, start, end)."
    ),
},
```

Every line of the entry will carry an inline `#` comment in the actual code edit
(per Constitution Principle VI), omitted here for readability of the data-model
document.
