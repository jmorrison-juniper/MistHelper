# Phase 1 Data Model: countOrgNacClientEvents

**Feature**: `521-mist-count-org-nac-client-events`
**Source endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_nac_clients_events_count.md`

## 1. Response Entities

The endpoint returns a single JSON object (the *result envelope*) whose
`results` array contains one entity per distinct group (the *count row*).

### Entity A: ResultEnvelope (top-level response object)

| Field      | Type             | Required | Notes                                                                 |
|------------|------------------|----------|-----------------------------------------------------------------------|
| `distinct` | string           | Yes      | Echo of the `distinct` query parameter -- the attribute grouped by.   |
| `start`    | integer (int32)  | Yes      | Effective epoch-second start of the queried window.                   |
| `end`     | integer (int32)  | Yes      | Effective epoch-second end of the queried window.                     |
| `limit`    | integer (int32)  | Yes      | Effective row cap that was applied to `results`.                      |
| `total`    | integer (int32)  | Yes      | Total event count across all groups (sum of `count` across `results`).|
| `results`  | array of CountRow| Yes      | Per-group count rows -- see Entity B.                                 |

**Primary key**: N/A. The envelope is never persisted as a row. Its scalar
fields are denormalized into every persisted `CountRow` so each row is
self-describing (see Entity B's `start_epoch`, `end_epoch`, `query_limit`,
`query_distinct_field`).

**Foreign keys**: `org_id` (path parameter) is denormalized into every
persisted row; references `orgs.id` in the broader MistHelper schema.

### Entity B: CountRow (per-group count, persisted as one SQLite row)

| Field                  | Type            | Required | Source                                | Notes                                                                                              |
|------------------------|-----------------|----------|---------------------------------------|----------------------------------------------------------------------------------------------------|
| `misthelper_internal_id`| integer        | Yes      | SQLite AUTOINCREMENT                  | Surrogate PK -- never echoed to CSV / ArangoDB consumers.                                          |
| `org_id`               | string (UUID)   | Yes      | Path parameter, denormalized          | The org whose events were counted.                                                                 |
| `distinct_field`       | string          | Yes      | Envelope `distinct`, denormalized     | One of `type`, `nas_vendor`, `vlan`, `ssid`, `port_type`, `auth_type`.                             |
| `distinct_value`       | string          | Yes      | `results[i].<distinct_field>`         | The value of the grouped attribute for this row (e.g. `auth_success`, `juniper-mist`, `100`).      |
| `count`                | integer         | Yes      | `results[i].count`                    | Number of NAC client events seen in the window matching `distinct_field = distinct_value`.         |
| `start_epoch`          | integer         | Yes      | Envelope `start`, denormalized        | Effective window start in epoch seconds.                                                           |
| `end_epoch`            | integer         | Yes      | Envelope `end`, denormalized          | Effective window end in epoch seconds.                                                             |
| `query_limit`          | integer         | Yes      | Envelope `limit`, denormalized        | Limit applied to `results`.                                                                        |
| `query_total`          | integer         | Yes      | Envelope `total`, denormalized        | Total events across all groups for this query (same value on every row of the same query).         |
| `event_type_filter`    | string          | No       | Caller-supplied `type` query param    | Echoed for traceability; NULL if no filter was applied.                                            |
| `fetched_at`           | timestamp (ISO) | Yes      | MistHelper local clock at write time  | When the row was last upserted; updated on every re-run of the same query.                         |

**Primary key**: `misthelper_internal_id` (AUTOINCREMENT surrogate).

**Unique index** (the natural composite key that drives upsert semantics):
`UNIQUE (org_id, distinct_field, distinct_value, start_epoch, end_epoch)`.

**Foreign keys**: `org_id` references `orgs.id` (logical reference; no FK
constraint is added because `orgs` may not exist locally when this operation
runs standalone).

## 2. State Transitions

N/A -- read-only endpoint. Rows are inserted on first observation of a
`(org_id, distinct_field, distinct_value, start_epoch, end_epoch)` tuple and
updated in place on subsequent runs of the same query. No state machine, no
lifecycle, no soft-delete.

## 3. SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_nac_client_events_count (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id                 TEXT    NOT NULL,
    distinct_field         TEXT    NOT NULL,
    distinct_value         TEXT    NOT NULL,
    count                  INTEGER NOT NULL,
    start_epoch            INTEGER NOT NULL,
    end_epoch              INTEGER NOT NULL,
    query_limit            INTEGER NOT NULL,
    query_total            INTEGER NOT NULL,
    event_type_filter      TEXT,
    fetched_at             TEXT    NOT NULL,
    UNIQUE (org_id, distinct_field, distinct_value, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_org_nac_evt_cnt_org
    ON org_nac_client_events_count (org_id);
CREATE INDEX IF NOT EXISTS idx_org_nac_evt_cnt_field
    ON org_nac_client_events_count (distinct_field);
CREATE INDEX IF NOT EXISTS idx_org_nac_evt_cnt_window
    ON org_nac_client_events_count (start_epoch, end_epoch);
```

Upsert SQL pattern used by `DataExporter` for this strategy:

```sql
INSERT OR REPLACE INTO org_nac_client_events_count (
    org_id, distinct_field, distinct_value, count,
    start_epoch, end_epoch, query_limit, query_total,
    event_type_filter, fetched_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

## 4. `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

To be inserted into the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (around line 1672):

```python
"countOrgNacClientEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_index": [
        "org_id",
        "distinct_field",
        "distinct_value",
        "start_epoch",
        "end_epoch",
    ],
    "indexes": [
        "org_id",
        "distinct_field",
        "start_epoch",
    ],
},
```

This entry is the contract between the menu method and
`DataExporter.write_with_format_selection(...)` -- the exporter inspects the
`type` field to choose its insert strategy, the `unique_index` to construct
the upsert constraint, and `indexes` to issue secondary `CREATE INDEX`
statements on first-run table creation.
