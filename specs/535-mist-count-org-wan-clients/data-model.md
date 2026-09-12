# Phase 1 Data Model: countOrgWanClients

The endpoint returns a single aggregate count envelope containing an
array of count buckets. The model below captures both the envelope-level
metadata and the bucket-level rows that MistHelper persists.

## Entities

### Entity 1 -- CountEnvelope (request/response metadata)

This entity is *not* a row in the bucket table; it is the envelope
returned by the API. MistHelper writes its scalar fields onto each
bucket row so that re-runs over different time windows remain
distinguishable.

| Field           | Type    | Source                          | Notes                                                |
|-----------------|---------|---------------------------------|------------------------------------------------------|
| `distinct`      | string  | response `distinct`             | Echo of the requested distinct dimension.            |
| `start_epoch`   | integer | response `start`                | Epoch seconds, int32.                                |
| `end_epoch`     | integer | response `end`                  | Epoch seconds, int32.                                |
| `limit_value`   | integer | response `limit`                | Echo of requested `limit`.                           |
| `total`         | integer | response `total`                | Total matching records before bucketing.             |

State transitions: **N/A -- read-only endpoint.**

### Entity 2 -- CountBucket (one row per result item)

| Field                     | Type    | Source                              | PK / FK                                  | Notes                                                                 |
|---------------------------|---------|-------------------------------------|------------------------------------------|-----------------------------------------------------------------------|
| `misthelper_internal_id`  | integer | autoincrement                       | PRIMARY KEY                              | Surrogate key per project convention.                                 |
| `org_id`                  | string  | request path param                  | FK -> `sites.org_id` (logical, not enforced) | UUID stamped at write time.                                       |
| `distinct_field`          | string  | request `distinct` query param      | part of UNIQUE                           | Name of the dimension being counted (e.g. `mfg`, `hostname`).         |
| `distinct_value`          | string  | response `results[i]` additional property | part of UNIQUE                       | The bucket label; column name in the API payload varies by request.   |
| `count`                   | integer | response `results[i].count`         |                                          | Required by API contract.                                             |
| `start_epoch`             | integer | response `start`                    | part of UNIQUE                           | Time window start (epoch seconds).                                    |
| `end_epoch`               | integer | response `end`                      | part of UNIQUE                           | Time window end (epoch seconds).                                      |
| `limit_value`             | integer | response `limit`                    |                                          | Echo of requested limit for traceability.                             |
| `total`                   | integer | response `total`                    |                                          | Pre-bucketing total for the same window.                              |
| `fetched_at`              | text    | `datetime.utcnow().isoformat()`     |                                          | ISO 8601 UTC, written by `DataExporter`.                              |

State transitions: **N/A -- read-only endpoint. Rows are upserted on the
unique tuple; existing rows are replaced on re-run within the same
time window.**

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS count_org_wan_clients (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id          TEXT    NOT NULL,
    distinct_field  TEXT    NOT NULL,
    distinct_value  TEXT    NOT NULL,
    count           INTEGER NOT NULL,
    start_epoch     INTEGER NOT NULL,
    end_epoch       INTEGER NOT NULL,
    limit_value     INTEGER,
    total           INTEGER,
    fetched_at      TEXT    NOT NULL,
    UNIQUE (org_id, distinct_field, distinct_value, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_count_org_wan_clients_org
    ON count_org_wan_clients (org_id);
CREATE INDEX IF NOT EXISTS idx_count_org_wan_clients_window
    ON count_org_wan_clients (start_epoch, end_epoch);
CREATE INDEX IF NOT EXISTS idx_count_org_wan_clients_distinct
    ON count_org_wan_clients (distinct_field, distinct_value);
```

The `INSERT OR REPLACE` upsert path in `DataExporter` targets the
`UNIQUE (org_id, distinct_field, distinct_value, start_epoch, end_epoch)`
constraint, satisfying Acceptance Scenario 3 in `spec.md` (no duplicate
rows on repeated runs).

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add the following entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in
`MistHelper.py` (around line ~1672):

```python
"countOrgWanClients": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraint": [
        "org_id",
        "distinct_field",
        "distinct_value",
        "start_epoch",
        "end_epoch",
    ],
    "indexes": ["org_id", "start_epoch", "end_epoch", "distinct_field"],
},
```

## Foreign-key notes

The `org_id` column is a logical foreign key onto the `sites` /
`orgs_*` tables already populated by other MistHelper menu items.
SQLite foreign-key enforcement is *not* enabled in MistHelper
(matches the rest of the codebase); the relationship is documented
here for ArangoDB graph edge construction (per spec 188).
