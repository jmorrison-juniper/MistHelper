# Phase 1 Data Model: countOrgSystemEvents

Source: `documentation/api/orgs/GET_orgs_org_id_events_system_count.md`
Plan: [plan.md](./plan.md)

## Entities

The endpoint returns one envelope entity (`CountResult`) that contains
zero or more child entities (`CountBucket`). MistHelper persists both
in a single flattened table because the bucket count is small (one row
per distinct-field value) and querying joined data is rare.

### Entity 1: CountResult (response envelope)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `distinct` | string | API response | The distinct field name the count was grouped by; blank when the user did not request grouping |
| `start` | integer (epoch seconds) | API response | Lower bound of the window the API actually applied |
| `end` | integer (epoch seconds) | API response | Upper bound of the window the API actually applied |
| `limit` | integer | API response | Page size echoed back |
| `total` | integer | API response | Total bucket count across all pages |
| `results` | array of CountBucket | API response | Per-bucket counts (flattened into rows on persistence) |

**Primary Key**: synthesized `misthelper_internal_id` (auto-increment).
**Unique constraint**: `(org_id, distinct, start_epoch, end_epoch)` --
re-running with identical scope upserts in place.
**Foreign Keys**: `org_id` references `orgs.id` (logical, not enforced
by SQLite since `orgs` is mirrored from the API rather than owned).

### Entity 2: CountBucket (child of CountResult.results)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `count` | integer | API response (required) | Number of system events in this bucket |
| `<distinct_value>` | string | API response (additionalProperties) | Bucket label -- the value of the distinct field; column name in the flattened row is `bucket_value` |

**Primary Key**: rows are denormalized into the same SQLite row as the
envelope; the unique constraint above plus `bucket_value` keeps the
combined identity unique.

## Field-by-Field Mapping (flattened row)

The DataExporter flattens the envelope + each bucket into one row per
bucket. Below is the canonical row schema persisted to SQLite, CSV,
and ArangoDB.

| Column | Type | Origin | Nullable |
|--------|------|--------|----------|
| `misthelper_internal_id` | INTEGER PRIMARY KEY AUTOINCREMENT | local | no |
| `org_id` | TEXT | prompt / `.env` | no |
| `distinct` | TEXT | response.distinct | yes (blank when ungrouped) |
| `start_epoch` | INTEGER | response.start | no |
| `end_epoch` | INTEGER | response.end | no |
| `limit_value` | INTEGER | response.limit | no |
| `total` | INTEGER | response.total | no |
| `bucket_value` | TEXT | response.results[i].<distinct field> | yes |
| `count` | INTEGER | response.results[i].count | no |
| `captured_at` | INTEGER | `time.time()` at fetch | no |
| `mist_endpoint` | TEXT | constant `"countOrgSystemEvents"` | no |

`limit_value` is renamed from `limit` to avoid colliding with the
SQLite reserved word.

## State Transitions

**N/A -- read-only endpoint.** The MistHelper rows are an immutable
snapshot of an upstream aggregation. Subsequent runs with identical
`(org_id, distinct, start_epoch, end_epoch)` replace the prior row via
the unique constraint and `INSERT OR REPLACE` semantics; runs with a
different time window or distinct field create new rows. No
client-side state machine is required.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS count_org_system_events (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id        TEXT    NOT NULL,
    "distinct"    TEXT,
    start_epoch   INTEGER NOT NULL,
    end_epoch     INTEGER NOT NULL,
    limit_value   INTEGER NOT NULL,
    total         INTEGER NOT NULL,
    bucket_value  TEXT,
    count         INTEGER NOT NULL,
    captured_at   INTEGER NOT NULL,
    mist_endpoint TEXT    NOT NULL DEFAULT 'countOrgSystemEvents',
    UNIQUE (org_id, "distinct", start_epoch, end_epoch, bucket_value)
);

CREATE INDEX IF NOT EXISTS idx_count_org_system_events_org
    ON count_org_system_events (org_id);
CREATE INDEX IF NOT EXISTS idx_count_org_system_events_captured
    ON count_org_system_events (captured_at);
```

The `"distinct"` column name is quoted because it is a SQLite reserved
word.

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict
in `MistHelper.py` (approximate line 1672):

```python
"countOrgSystemEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraint": [
        "org_id",
        "distinct",
        "start_epoch",
        "end_epoch",
        "bucket_value",
    ],
    "indexes": ["org_id", "captured_at"],
    "table_name": "count_org_system_events",
},
```

## Validation Rules

- `org_id` MUST be a UUID string; the SDK raises if it is malformed.
- `start_epoch` <= `end_epoch`; the API rejects inverted windows with
  HTTP 400, which MistHelper surfaces as a logged warning per the
  spec's edge-case list.
- `count` MUST be `>= 0`; negative counts indicate an upstream bug and
  trigger a `logging.warning(...)` with the raw response.
- `bucket_value` is set to NULL only when `distinct` is also NULL.

## Out of Model

- No relationship table to `searchOrgSystemEvents` results. The two
  endpoints are queried independently and their tables are joined
  client-side when needed.
- No retention policy is encoded in the model. Pruning old snapshots is
  handled by the operator via existing SQLite maintenance tooling.
