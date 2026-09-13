# Phase 1 Data Model: countOrgAssetsByDistanceField

This document defines the entities produced by the endpoint, their persistence
shape, and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration.

## Entities

### Entity 1: AssetCountSummary

One row per invocation window. Represents the envelope returned by the API.

| Field      | Type    | Source                | Nullable | Notes                                           |
|------------|---------|-----------------------|----------|-------------------------------------------------|
| `org_id`   | TEXT    | Path parameter (echo) | No       | UUID; injected by MistHelper, not in response.  |
| `distinct` | TEXT    | Response `distinct`   | No       | Echo of the requested distinct field name.      |
| `start`    | INTEGER | Response `start`      | No       | Epoch seconds (int32).                          |
| `end`      | INTEGER | Response `end`        | No       | Epoch seconds (int32).                          |
| `limit`    | INTEGER | Response `limit`      | No       | Page-size echo (int32, server default 100).     |
| `total`    | INTEGER | Response `total`      | No       | Total asset count across all distinct values.   |
| `bucket_n` | INTEGER | `len(results)`        | No       | Convenience count of buckets in this window.    |
| `fetched_at` | TEXT  | MistHelper            | No       | ISO 8601 UTC timestamp of the SDK call.         |

- **Primary Key**: composite `(org_id, distinct, start, end)`.
- **Foreign Keys**: none (root entity).
- **Indexes**: `(org_id)`, `(distinct)`, `(fetched_at)` for time-range queries.

### Entity 2: AssetCountResult

One row per bucket in `results[]`. Each row links back to a summary row.

| Field          | Type    | Source                       | Nullable | Notes                                           |
|----------------|---------|------------------------------|----------|-------------------------------------------------|
| `org_id`       | TEXT    | Path parameter (echo)        | No       | UUID; injected.                                 |
| `distinct`     | TEXT    | Summary echo                 | No       | Same field name as parent summary.              |
| `start`        | INTEGER | Summary echo                 | No       | Epoch seconds.                                  |
| `end`          | INTEGER | Summary echo                 | No       | Epoch seconds.                                  |
| `bucket_value` | TEXT    | `results[i][<distinct>]`     | Yes      | Stringified value of the distinct attribute. May be empty when API returns nulls. |
| `count`        | INTEGER | `results[i].count`           | No       | Asset count in this bucket; required by schema. |
| `fetched_at`   | TEXT    | MistHelper                   | No       | Same timestamp as the parent summary row.       |

- **Primary Key**: composite `(org_id, distinct, start, end, bucket_value)`.
- **Foreign Keys**: `(org_id, distinct, start, end)` -> `AssetCountSummary`.
- **Indexes**: `(org_id, distinct)` for fast pivot queries.

## State Transitions

N/A -- this is a read-only GET endpoint. No state machine; each invocation is
an independent point-in-time read. Re-running the menu with identical scope
upserts existing rows; running with a different `distinct` or different time
window inserts new rows without disturbing prior runs.

## SQLite DDL

```sql
-- Summary envelope (one row per invocation window)
CREATE TABLE IF NOT EXISTS org_assets_count_summary (
    org_id      TEXT    NOT NULL,
    distinct    TEXT    NOT NULL,
    start       INTEGER NOT NULL,
    end         INTEGER NOT NULL,
    limit       INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    bucket_n    INTEGER NOT NULL,
    fetched_at  TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_assets_count_summary_org
    ON org_assets_count_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_org_assets_count_summary_distinct
    ON org_assets_count_summary (distinct);
CREATE INDEX IF NOT EXISTS idx_org_assets_count_summary_fetched
    ON org_assets_count_summary (fetched_at);

-- Per-bucket result rows (one row per distinct value within a window)
CREATE TABLE IF NOT EXISTS org_assets_count_results (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL,
    start         INTEGER NOT NULL,
    end           INTEGER NOT NULL,
    bucket_value  TEXT    NOT NULL DEFAULT '',
    count         INTEGER NOT NULL,
    fetched_at    TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end, bucket_value),
    FOREIGN KEY (org_id, distinct, start, end)
        REFERENCES org_assets_count_summary (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_assets_count_results_pivot
    ON org_assets_count_results (org_id, distinct);
```

> Note: `distinct`, `start`, `end`, and `limit` are reserved or quasi-reserved
> words in some SQL dialects but are valid unquoted identifiers in SQLite.
> `DataExporter` already handles this elsewhere; no quoting workaround needed.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
'countOrgAssetsByDistanceField': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'distinct', 'start', 'end'],
    'indexes': ['org_id', 'distinct', 'fetched_at'],
    'description': (
        'Org BLE-asset count grouped by a distinct attribute. '
        'Composite key (org_id, distinct, start, end) lets repeated '
        'runs over the same window upsert cleanly while runs against '
        'different distinct fields or windows accumulate side by side.'
    ),
    'related_tables': [
        {
            'name': 'org_assets_count_results',
            'type': 'composite_pk',
            'primary_key': ['org_id', 'distinct', 'start', 'end', 'bucket_value'],
            'indexes': ['org_id', 'distinct'],
            'description': 'Per-distinct-value bucket rows for the summary above.',
        },
    ],
},
```

The `related_tables` key follows the existing pattern used by other multi-table
operations in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; `DataExporter` consumes it to
create both tables on first write.
