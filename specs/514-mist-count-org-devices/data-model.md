# Phase 1 Data Model: countOrgDevices

Read-only endpoint. State transitions: **N/A -- read-only endpoint**. The data model
captures the snapshot persisted to the multi-backend store per invocation.

## Entities

### Entity 1: CountEnvelope (summary)

Represents one invocation of the endpoint -- the wrapper object returned by the SDK.

| Field           | Type        | Required | Source            | Notes                                                                   |
|-----------------|-------------|----------|-------------------|-------------------------------------------------------------------------|
| run_id          | INTEGER     | Yes      | MistHelper-local  | Monotonic per-invocation id; auto-assigned by DataExporter.             |
| org_id          | TEXT (UUID) | Yes      | User prompt       | Mist organization UUID; foreign-key target for results rows.            |
| distinct        | TEXT        | Yes      | API + user prompt | The grouping field used for aggregation (e.g. `model`).                 |
| start           | INTEGER     | Yes      | API response      | Window start, epoch seconds.                                            |
| end             | INTEGER     | Yes      | API response      | Window end, epoch seconds.                                              |
| limit           | INTEGER     | Yes      | API response      | Page size used for the query.                                           |
| total           | INTEGER     | Yes      | API response      | Total distinct group count (across all pages).                          |
| collected_at    | TEXT (ISO)  | Yes      | MistHelper-local  | ISO-8601 UTC timestamp of the collection event.                         |

**Primary Key**: composite `(org_id, distinct, start, end)`.
**Foreign Keys**: none outbound; `CountResult.run_id` references `CountEnvelope.run_id`.

### Entity 2: CountResult (one row per result bucket)

Represents one entry in the API `results[]` array -- a single (group_value, count) pair.

| Field           | Type        | Required | Source            | Notes                                                                   |
|-----------------|-------------|----------|-------------------|-------------------------------------------------------------------------|
| run_id          | INTEGER     | Yes      | MistHelper-local  | Foreign key to `CountEnvelope.run_id`.                                  |
| org_id          | TEXT (UUID) | Yes      | User prompt       | Denormalized for query convenience; matches envelope.                   |
| distinct        | TEXT        | Yes      | User prompt       | Denormalized for query convenience; matches envelope.                   |
| start           | INTEGER     | Yes      | API response      | Denormalized window start for composite key.                            |
| distinct_value  | TEXT        | Yes      | API response      | The actual group value (from `additionalProperties` keyed by distinct). |
| count           | INTEGER     | Yes      | API response      | Number of devices in this group.                                        |
| collected_at    | TEXT (ISO)  | Yes      | MistHelper-local  | ISO-8601 UTC timestamp; matches envelope row.                           |

**Primary Key**: composite `(org_id, distinct, start, distinct_value)`.
**Foreign Keys**: `run_id` references `org_devices_count_summary.run_id` (logical FK;
not enforced by SQLite in the existing schema, but documented for downstream graph
backend).

### Flatten Strategy

The OpenAPI `results[]` items declare `count` as the only required typed field, with
`additionalProperties: {type: string}` carrying the actual grouping value under a key
whose name equals the `distinct` parameter (for example, when `distinct=model` the
result entry looks like `{"count": 42, "model": "AP43"}`). The flatten routine reads the
`distinct` parameter from the request, then for each result entry extracts
`entry["count"]` and `entry[distinct]` into the canonical `count` / `distinct_value`
columns. This produces a stable two-column schema regardless of which `distinct` field
the operator chose.

## SQLite DDL

```sql
-- Envelope table: one row per invocation (time-windowed snapshot).
CREATE TABLE IF NOT EXISTS org_devices_count_summary (
    run_id        INTEGER NOT NULL,
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL,
    start         INTEGER NOT NULL,
    end           INTEGER NOT NULL,
    limit         INTEGER NOT NULL,
    total         INTEGER NOT NULL,
    collected_at  TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_devices_count_summary_org
    ON org_devices_count_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_org_devices_count_summary_collected
    ON org_devices_count_summary (collected_at);

-- Results table: one row per (group_value, count) pair within an invocation.
CREATE TABLE IF NOT EXISTS org_devices_count_results (
    run_id          INTEGER NOT NULL,
    org_id          TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    start           INTEGER NOT NULL,
    distinct_value  TEXT    NOT NULL,
    count           INTEGER NOT NULL,
    collected_at    TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_org_devices_count_results_org
    ON org_devices_count_results (org_id);
CREATE INDEX IF NOT EXISTS idx_org_devices_count_results_distinct
    ON org_devices_count_results (distinct, distinct_value);
```

`INSERT OR REPLACE` is used by DataExporter so re-running the same query inside the same
time window is idempotent; running it again outside the window produces a new snapshot
row instead of overwriting history.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (the centralized config near line ~1672):

```python
'countOrgDevices': {  # operationId from the OpenAPI spec
    'type': 'composite_pk',
    'tables': {
        # Envelope (one row per invocation per time window).
        'org_devices_count_summary': {
            'primary_key': ['org_id', 'distinct', 'start', 'end'],
            'indexes': ['org_id', 'collected_at'],
        },
        # Per-group result rows.
        'org_devices_count_results': {
            'primary_key': ['org_id', 'distinct', 'start', 'distinct_value'],
            'indexes': ['org_id', 'distinct', 'distinct_value'],
        },
    },
    'upsert_mode': 'INSERT OR REPLACE',  # idempotent within the same time window
    'notes': 'Composite PK includes time-window bounds so successive runs preserve '
             'historical snapshots while same-window re-runs are idempotent.',
},
```

This entry is the single source of truth used by `DataExporter` across all three
backends (CSV header order, SQLite DDL generation, and ArangoDB collection upsert
semantics).
