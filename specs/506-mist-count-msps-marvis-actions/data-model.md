# Phase 1 Data Model: countMspsMarvisActions

**Feature**: 506-mist-count-msps-marvis-actions
**Date**: 2026-06-28
**Endpoint**: `GET /api/v1/msps/{msp_id}/suggestion/count`

## Entities Returned by the Endpoint

The response body is a single JSON object with the following top-level fields:

| Field      | Type    | Description                                                     |
|------------|---------|-----------------------------------------------------------------|
| `distinct` | string  | The distinct attribute the API counted by (echoes the query).   |
| `limit`    | integer | The effective row cap (echoes the query, default 100).          |
| `total`    | integer | Number of distinct buckets returned.                            |
| `results`  | array   | Per-bucket rows -- each carries a `count` plus one dynamic key. |

This is decomposed into two MistHelper entities:

### Entity 1: `MspMarvisActionsCountSummary`

The envelope describing the query and its overall total.

| Field                | Type     | Required | Notes                                                |
|----------------------|----------|----------|------------------------------------------------------|
| `misthelper_internal_id` | integer  | yes (PK) | auto-increment surrogate                        |
| `msp_id`             | string   | yes      | Mist UUID supplied by the user                       |
| `distinct_attribute` | string   | yes      | Mirrors response `distinct`                          |
| `limit`              | integer  | yes      | Mirrors response `limit`                             |
| `total`              | integer  | yes      | Mirrors response `total`                             |
| `snapshot_timestamp` | string   | yes      | ISO-8601 UTC of the request, set by MistHelper       |

- **Primary key**: `misthelper_internal_id` (auto-increment).
- **Unique constraint**: `(msp_id, distinct_attribute, snapshot_timestamp)`.
- **Foreign key**: `msp_id` references the conceptual MSP entity (not enforced
  in SQLite; ArangoDB graph edge added in a future spec).

### Entity 2: `MspMarvisActionsCountResult`

One row per bucket inside `results[]`.

| Field                | Type     | Required | Notes                                                       |
|----------------------|----------|----------|-------------------------------------------------------------|
| `misthelper_internal_id` | integer  | yes (PK) | auto-increment surrogate                               |
| `msp_id`             | string   | yes      | Same MSP UUID as the parent summary row                     |
| `distinct_attribute` | string   | yes      | Matches the parent summary `distinct_attribute`             |
| `distinct_value`     | string   | yes      | The dynamic key value (e.g. a status UUID, a category name) |
| `count`              | integer  | yes      | Count for this bucket                                       |
| `snapshot_timestamp` | string   | yes      | Same value as the parent summary row                        |

- **Primary key**: `misthelper_internal_id` (auto-increment).
- **Unique constraint**: `(msp_id, distinct_attribute, distinct_value, snapshot_timestamp)`.
- **Foreign key (logical)**: `(msp_id, distinct_attribute, snapshot_timestamp)`
  references `MspMarvisActionsCountSummary`. Not declared as a SQL FK to avoid
  cross-backend brittleness; ArangoDB will model this with a graph edge.

## State Transitions

N/A -- read-only endpoint. No state is mutated server-side. MistHelper inserts
new immutable snapshot rows on every invocation; historical snapshots are
preserved by the `snapshot_timestamp` component of the unique constraint.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS msp_marvis_actions_count_summary (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    msp_id                 TEXT    NOT NULL,
    distinct_attribute     TEXT    NOT NULL,
    limit                  INTEGER NOT NULL,
    total                  INTEGER NOT NULL,
    snapshot_timestamp     TEXT    NOT NULL,
    UNIQUE (msp_id, distinct_attribute, snapshot_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_msp_marvis_count_summary_msp
    ON msp_marvis_actions_count_summary (msp_id);
CREATE INDEX IF NOT EXISTS idx_msp_marvis_count_summary_snapshot
    ON msp_marvis_actions_count_summary (snapshot_timestamp);

CREATE TABLE IF NOT EXISTS msp_marvis_actions_count_results (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    msp_id                 TEXT    NOT NULL,
    distinct_attribute     TEXT    NOT NULL,
    distinct_value         TEXT    NOT NULL,
    count                  INTEGER NOT NULL,
    snapshot_timestamp     TEXT    NOT NULL,
    UNIQUE (msp_id, distinct_attribute, distinct_value, snapshot_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_msp_marvis_count_results_msp
    ON msp_marvis_actions_count_results (msp_id);
CREATE INDEX IF NOT EXISTS idx_msp_marvis_count_results_attribute
    ON msp_marvis_actions_count_results (distinct_attribute);
CREATE INDEX IF NOT EXISTS idx_msp_marvis_count_results_snapshot
    ON msp_marvis_actions_count_results (snapshot_timestamp);
```

> Note: the column name `limit` is a SQLite reserved word in some contexts.
> `DataExporter` quotes identifiers when emitting DDL; the safe alternative
> `effective_limit` is acceptable if the project-wide quoting rule changes.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (currently near line 1672):

```python
'countMspsMarvisActions': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique': ['msp_id', 'distinct_attribute', 'distinct_value', 'snapshot_timestamp'],
    'indexes': ['msp_id', 'distinct_attribute', 'snapshot_timestamp'],
    'tables': {
        'summary': 'msp_marvis_actions_count_summary',
        'results': 'msp_marvis_actions_count_results',
    },
}
```

The `tables` sub-dictionary is consumed by `DataExporter` when the operation
emits two related sheets/tables. If `DataExporter` does not yet read that key,
the menu method passes the table name explicitly per write call using
`api_function_name="countMspsMarvisActions_summary"` /
`api_function_name="countMspsMarvisActions_results"`.
