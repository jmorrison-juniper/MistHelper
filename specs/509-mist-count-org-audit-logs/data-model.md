# Phase 1 Data Model: countOrgAuditLogs

This document enumerates the entities returned by
`GET /api/v1/orgs/{org_id}/logs/count` and how MistHelper persists them.

## Entities

### Entity 1: AuditLogCountSummary

The wrapper object describing the aggregation request that produced the buckets.

| Field           | Type          | Source           | Notes                                            |
|-----------------|---------------|------------------|--------------------------------------------------|
| `org_id`        | string (UUID) | request context  | Injected client-side; not in API response body.  |
| `distinct`      | string        | response.distinct | Echo of the grouping field requested.           |
| `window_start`  | integer       | response.start   | Epoch seconds (signed int32 per OpenAPI).        |
| `window_end`    | integer       | response.end     | Epoch seconds (signed int32 per OpenAPI).        |
| `limit`         | integer       | response.limit   | Server-applied bucket cap (default 100).         |
| `total`         | integer       | response.total   | Total audit-log events in the window.            |
| `bucket_count`  | integer       | len(results)     | Derived; useful for trend queries.               |

**Primary key**: `(org_id, distinct, window_start, window_end)` -- composite.
**Foreign keys**: `org_id` references the conceptual `orgs` row maintained by the
existing `listOrgs` exporter (no enforced SQL FK -- MistHelper SQLite tables are
de-normalised flat tables per project convention).

### Entity 2: AuditLogCountBucket

One row per distinct-field bucket in the aggregation result.

| Field           | Type          | Source                     | Notes                                              |
|-----------------|---------------|----------------------------|----------------------------------------------------|
| `org_id`        | string (UUID) | request context            | Injected client-side.                              |
| `distinct`      | string        | response.distinct          | Echoed from summary.                               |
| `bucket_value`  | string        | results[i].<distinct field> | Value of the additional-property key (per schema). |
| `count`         | integer       | results[i].count           | Required per OpenAPI `count_result.required`.      |
| `window_start`  | integer       | response.start             | Same as summary -- denormalised for upsert key.    |
| `window_end`    | integer       | response.end               | Same as summary -- denormalised for upsert key.    |

**Primary key**: `(org_id, distinct, bucket_value, window_start, window_end)` --
composite.
**Foreign keys**: `(org_id, distinct, window_start, window_end)` logically references
`AuditLogCountSummary` (no enforced SQL FK; same denormalised convention as above).

## State Transitions

N/A -- this endpoint is read-only (HTTP GET). The MistHelper menu method produces a
snapshot of the current Mist Cloud aggregation each time it is invoked. There is no
local state machine; the SQLite tables accumulate time-series snapshots keyed by the
composite primary keys above.

## SQLite DDL

DataExporter creates these tables on first run; the DDL is documented here for
reviewers and for the contracts checklist.

```sql
CREATE TABLE IF NOT EXISTS org_audit_logs_count_summary (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL,
    window_start  INTEGER NOT NULL,
    window_end    INTEGER NOT NULL,
    limit_value   INTEGER NOT NULL,
    total         INTEGER NOT NULL,
    bucket_count  INTEGER NOT NULL,
    inserted_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (org_id, distinct, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_audit_count_summary_org_window
    ON org_audit_logs_count_summary (org_id, window_start, window_end);

CREATE TABLE IF NOT EXISTS org_audit_logs_count_buckets (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL,
    bucket_value  TEXT    NOT NULL,
    count         INTEGER NOT NULL,
    window_start  INTEGER NOT NULL,
    window_end    INTEGER NOT NULL,
    inserted_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (org_id, distinct, bucket_value, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_audit_count_buckets_distinct
    ON org_audit_logs_count_buckets (org_id, distinct, window_start);
```

Note: SQL identifier `limit` is reserved in SQLite, so the column is renamed
`limit_value` for portability. The Python flattener maps `response.limit` ->
`limit_value` before handing the row to DataExporter.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py`:

```python
'countOrgAuditLogs': {                              # operationId from the Mist OpenAPI spec
    'type': 'composite_pk',                         # No API-provided UUID -- use a composite key
    'tables': {                                     # Two output tables; each gets its own PK
        'org_audit_logs_count_summary': {           # Wrapper row -- one per (org, distinct, window)
            'primary_key': [                        # Composite key captures every aggregation knob
                'org_id',                           # Org scope
                'distinct',                         # Grouping field
                'window_start',                     # Window start epoch
                'window_end',                       # Window end epoch
            ],
            'indexes': [                            # Speed up time-series scans
                'org_id',
                'window_start',
            ],
        },
        'org_audit_logs_count_buckets': {           # Bucket row -- one per distinct value
            'primary_key': [                        # Includes bucket_value to allow many rows per window
                'org_id',
                'distinct',
                'bucket_value',
                'window_start',
                'window_end',
            ],
            'indexes': [                            # Filter by org + distinct for quick lookups
                'org_id',
                'distinct',
            ],
        },
    },
},
```

Every executable line carries an inline comment per Constitution Principle VI.
