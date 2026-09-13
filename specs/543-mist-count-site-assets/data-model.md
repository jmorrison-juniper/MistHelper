# Phase 1 Data Model: countSiteAssets

The Mist API endpoint `GET /api/v1/sites/{site_id}/stats/assets/count` returns a
single envelope object containing pagination metadata plus an array of bucket
results. MistHelper persists this as two related entities.

## Entity 1: SiteAssetsCountSummary

Represents the response envelope (one row per invocation).

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| misthelper_internal_id | INTEGER | autoincrement | SQLite rowid. Not exposed externally. |
| site_id | TEXT (UUID) | path param | Logical scope; FK to sites table when present. |
| distinct | TEXT | response field | The distinct attribute used for grouping. |
| limit | INTEGER | response field | Page size honored by the API. |
| total | INTEGER | response field | Total distinct buckets matched by the query. |
| start | INTEGER (epoch s) | response field | Window start emitted by API. |
| end | INTEGER (epoch s) | response field | Window end emitted by API. |
| captured_at | INTEGER (epoch s) | client | `int(time.time())` at MistHelper invocation. |

Primary key (logical): `(site_id, distinct, captured_at)` enforced as a UNIQUE
constraint; PK column is `misthelper_internal_id` (autoincrement).
Foreign keys: `site_id` -> `sites.id` (soft / informational; not enforced by
SQLite in this monolith).

## Entity 2: SiteAssetsCountResults

Represents one bucket inside the `results` array (N rows per invocation).

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| site_id | TEXT (UUID) | path param | Repeats from envelope so the table is self-contained. |
| distinct | TEXT | envelope echo | Repeats from envelope for the same reason. |
| bucket_value | TEXT | `results[i].<distinct-key>` | The distinct attribute value for this bucket. May be empty string if the API returns an unnamed bucket. |
| count | INTEGER | `results[i].count` | Required field per OpenAPI schema. |
| captured_at | INTEGER (epoch s) | client | Joins to the summary row. |

Primary key: `(site_id, distinct, bucket_value, captured_at)`. composite_pk.
Foreign key: `(site_id, distinct, captured_at)` -> `site_assets_count_summary`
unique constraint (soft / informational).

## State Transitions

N/A -- this is a read-only HTTP GET endpoint. Each invocation produces an
immutable snapshot. There is no edit, draft, or lifecycle.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS site_assets_count_summary (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    distinct TEXT NOT NULL,
    limit_value INTEGER,
    total INTEGER,
    start_ts INTEGER,
    end_ts INTEGER,
    captured_at INTEGER NOT NULL,
    UNIQUE (site_id, distinct, captured_at)
);

CREATE INDEX IF NOT EXISTS idx_site_assets_count_summary_site
    ON site_assets_count_summary (site_id);

CREATE TABLE IF NOT EXISTS site_assets_count_results (
    site_id TEXT NOT NULL,
    distinct TEXT NOT NULL,
    bucket_value TEXT NOT NULL DEFAULT '',
    count INTEGER NOT NULL,
    captured_at INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, bucket_value, captured_at)
);

CREATE INDEX IF NOT EXISTS idx_site_assets_count_results_site
    ON site_assets_count_results (site_id);
```

Note: SQL identifiers `limit`, `start`, `end` are reserved words in some SQL
dialects -- columns are stored as `limit_value`, `start_ts`, `end_ts` to keep
the DDL portable. The Python-side flattener maps from the API field names.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteAssets"] = {
    "type": "composite_pk",
    "primary_key": ["site_id", "distinct", "bucket_value", "captured_at"],
    "indexes": ["site_id"],
    "tables": {
        "site_assets_count_summary": {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
            "unique": ["site_id", "distinct", "captured_at"],
            "indexes": ["site_id"],
        },
        "site_assets_count_results": {
            "type": "composite_pk",
            "primary_key": ["site_id", "distinct", "bucket_value", "captured_at"],
            "indexes": ["site_id"],
        },
    },
}
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` shape in `MistHelper.py` does
not yet support per-operation multi-table descriptors, the implementation task
adapts the entry to the actual schema -- the principle (composite PK on results,
auto-increment with unique on summary) remains the contract.
