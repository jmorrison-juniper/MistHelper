# Phase 1 Data Model: countOrgSwOrGwPorts

**Spec**: [spec.md](./spec.md)  **Plan**: [plan.md](./plan.md)
**Endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_stats_ports_count.md`

## Entity Map

The 200 response is a single envelope object wrapping a `results[]` array. MistHelper
flattens the envelope metadata onto every result row so each persisted record is
self-describing.

### Entity 1: `count_envelope` (transient -- not persisted as a separate table)

| Field    | Type    | Notes                                                |
|----------|---------|------------------------------------------------------|
| distinct | string  | The grouping attribute the user requested.           |
| start    | integer | Window start, epoch seconds.                         |
| end      | integer | Window end, epoch seconds.                           |
| limit    | integer | Page size used by the API (default 100).             |
| total    | integer | Total distinct buckets the server saw in the window. |
| results  | array   | One `count_result` per distinct bucket.              |

Primary key: none on its own -- the envelope is decomposed during flatten.
Foreign keys: `org_id` (path parameter, injected by the menu method).

### Entity 2: `count_result` (the row written to CSV / SQLite / ArangoDB)

| Field                   | Type     | Notes                                                                                          |
|-------------------------|----------|------------------------------------------------------------------------------------------------|
| misthelper_internal_id  | integer  | Auto-increment surrogate. PRIMARY KEY.                                                         |
| org_id                  | text     | UUID of the org. Injected from path parameter.                                                 |
| distinct_field          | text     | The OpenAPI `distinct` value the user supplied (e.g. `port_id`, `mac`, `neighbor_system_name`).|
| distinct_value          | text     | The bucket value returned by the API in the additionalProperties slot of `count_result`.       |
| count                   | integer  | Required field per OpenAPI -- number of ports in this bucket.                                  |
| start_epoch             | integer  | Copied from envelope.start.                                                                    |
| end_epoch               | integer  | Copied from envelope.end.                                                                      |
| limit                   | integer  | Copied from envelope.limit.                                                                    |
| total                   | integer  | Copied from envelope.total (same on every row of a run).                                       |
| site_id_filter          | text     | NULL when the user did not filter by site; UUID otherwise.                                     |
| up_filter               | text     | NULL / "true" / "false" depending on what the user selected.                                   |
| duration_filter         | text     | The duration string the user supplied (e.g. `1d`, `7d`).                                       |
| retrieved_at_utc        | text     | ISO-8601 UTC timestamp set by MistHelper at flatten time.                                      |

Primary key: `misthelper_internal_id` (auto-increment surrogate).
Unique index for upsert: `(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`.
Foreign keys: `org_id` references the `orgs` vertex in the ArangoDB graph (no FK
constraint enforced in SQLite per established MistHelper pattern); `site_id_filter`
references the `sites` vertex when not NULL.

## State Transitions

**N/A -- read-only endpoint.** No mutation, no state machine. Each menu invocation
produces a fresh snapshot scoped to (org_id, distinct_field, time window). Re-running
the menu with identical parameters overwrites the matching SQLite rows via the unique
index; the CSV backend appends a new timestamped file each run.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_stats_ports_count (
    misthelper_internal_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id                  TEXT    NOT NULL,
    distinct_field          TEXT    NOT NULL,
    distinct_value          TEXT    NOT NULL,
    count                   INTEGER NOT NULL,
    start_epoch             INTEGER NOT NULL,
    end_epoch               INTEGER NOT NULL,
    limit_used              INTEGER,
    total                   INTEGER,
    site_id_filter          TEXT,
    up_filter               TEXT,
    duration_filter         TEXT,
    retrieved_at_utc        TEXT    NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_org_stats_ports_count_natural
    ON org_stats_ports_count (
        org_id,
        distinct_field,
        distinct_value,
        start_epoch,
        end_epoch
    );

CREATE INDEX IF NOT EXISTS ix_org_stats_ports_count_org
    ON org_stats_ports_count (org_id);

CREATE INDEX IF NOT EXISTS ix_org_stats_ports_count_field
    ON org_stats_ports_count (distinct_field);
```

Note: the column is named `limit_used` rather than `limit` because `LIMIT` is a SQLite
reserved word; the `DataExporter` is expected to rename `envelope.limit ->
column.limit_used` at flatten time.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Dictionary Entry

```python
"countOrgSwOrGwPorts": {                                # Mist operationId key
    "type": "auto_increment_with_unique",               # Surrogate PK + unique tuple
    "primary_key": ["misthelper_internal_id"],          # Auto-increment surrogate
    "unique_index": [                                   # Natural identity tuple
        "org_id",                                       # Scope: the org we queried
        "distinct_field",                               # What we grouped by
        "distinct_value",                               # The grouped value
        "start_epoch",                                  # Window start
        "end_epoch",                                    # Window end
    ],
    "indexes": [                                        # Secondary indexes
        "org_id",                                       # Fast lookup by org
        "distinct_field",                               # Fast lookup by group field
    ],
    "table": "org_stats_ports_count",                   # Target SQLite / Arango name
},
```

Insertion site: alongside the existing org-stats entries inside the global
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dict near line ~1672 of `MistHelper.py` (per
`.github/copilot-instructions.md` Database Strategy section).
