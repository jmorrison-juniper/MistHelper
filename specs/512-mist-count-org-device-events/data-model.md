# Phase 1 Data Model: CountOrgDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contract**: [contracts/count_org_device_events.md](./contracts/count_org_device_events.md)

This document captures the entities, primary keys, foreign keys, state model, SQLite
DDL, and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry for the new menu operation.

## Entities

The endpoint response is a single top-level summary object containing one `results[]`
array. MistHelper flattens this into two related tables.

### Entity 1: `OrgDeviceEventsCountSummary` (one row per query)

| Field | Type | Source | PK? | FK? | Description |
|-------|------|--------|-----|-----|-------------|
| `org_id` | TEXT | path param | YES | -> `orgs.id` (logical) | Mist organization UUID |
| `distinct` | TEXT | query param echoed in response | YES | -- | The attribute used for grouping (e.g. `type`, `model`) |
| `start` | INTEGER | response field (epoch seconds) | YES | -- | Window start time |
| `end` | INTEGER | response field (epoch seconds) | YES | -- | Window end time |
| `limit` | INTEGER | response field | -- | -- | The `limit` echoed by the API (default 100) |
| `total` | INTEGER | response field | -- | -- | Total event count across all distinct groups in the window |
| `result_row_count` | INTEGER | derived (len of `results[]`) | -- | -- | MistHelper-added field: number of distinct groups returned (informational) |
| `retrieved_at_epoch` | INTEGER | MistHelper clock | -- | -- | UTC epoch when the row was fetched (for audit) |

### Entity 2: `OrgDeviceEventsCountResults` (N rows per query, one per group)

| Field | Type | Source | PK? | FK? | Description |
|-------|------|--------|-----|-----|-------------|
| `org_id` | TEXT | inherited from summary | YES | -> `org_device_events_count_summary.org_id` | Mist organization UUID |
| `distinct` | TEXT | inherited from summary | YES | -> `org_device_events_count_summary.distinct` | Attribute used for grouping |
| `start` | INTEGER | inherited from summary | YES | -> `org_device_events_count_summary.start` | Window start time |
| `end` | INTEGER | inherited from summary | YES | -> `org_device_events_count_summary.end` | Window end time |
| `result_key` | TEXT | `results[i]` `additionalProperties` value | YES | -- | Value of the distinct attribute (e.g. `AP_DISCONNECTED` when `distinct=type`) |
| `count` | INTEGER | `results[i].count` | -- | -- | Number of events in this group |
| `retrieved_at_epoch` | INTEGER | MistHelper clock | -- | -- | UTC epoch when the row was fetched (for audit) |

**Notes**:
- The OpenAPI schema declares `results[]` items as `{ count: int }` with
  `additionalProperties: string`. The actual key name of the `additionalProperties` value
  depends on the requested `distinct` field. MistHelper extracts the first non-`count`
  key from each result object and stores its value as `result_key`.
- The summary table is a single-row-per-query snapshot. Repeated runs with the same
  `(org_id, distinct, start, end)` tuple replace the previous row via SQLite
  `INSERT OR REPLACE`.
- The results table is a multi-row-per-query expansion. Repeated runs with the same
  `(org_id, distinct, start, end, result_key)` tuple replace the previous row.

## Relationships

```text
OrgDeviceEventsCountSummary  1 ----< N  OrgDeviceEventsCountResults
   PK (org_id, distinct, start, end)        PK (org_id, distinct, start, end, result_key)
                                            FK (org_id, distinct, start, end) -> summary
```

Foreign-key constraint is enforced **logically** (the summary row is always written first
in the same transaction as the results rows) rather than via a SQLite `FOREIGN KEY`
clause, to match the existing MistHelper schema convention of avoiding cross-table
constraints in the local fallback database.

## State Transitions

**N/A -- read-only endpoint.** The HTTP method is `GET` and the response is a point-in-
time count snapshot. There is no entity lifecycle, no create / update / delete, and no
server-side state to track. The only client-side state is the upsert overwrite behavior
described above (newer snapshot replaces older snapshot for the same key tuple).

## SQLite DDL

```sql
-- Summary table: one row per (org, distinct, window) query
CREATE TABLE IF NOT EXISTS org_device_events_count_summary (
    org_id TEXT NOT NULL,                 -- Mist organization UUID
    distinct TEXT NOT NULL,               -- attribute used for grouping
    start INTEGER NOT NULL,               -- window start epoch seconds
    end INTEGER NOT NULL,                 -- window end epoch seconds
    limit_value INTEGER,                  -- API limit echoed in response
    total INTEGER,                        -- total events across all groups
    result_row_count INTEGER,             -- number of distinct groups returned
    retrieved_at_epoch INTEGER NOT NULL,  -- when this snapshot was fetched
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_dev_evt_count_sum_org
    ON org_device_events_count_summary(org_id);

-- Results table: N rows per (org, distinct, window) query, one per group
CREATE TABLE IF NOT EXISTS org_device_events_count_results (
    org_id TEXT NOT NULL,                 -- Mist organization UUID
    distinct TEXT NOT NULL,               -- attribute used for grouping
    start INTEGER NOT NULL,               -- window start epoch seconds
    end INTEGER NOT NULL,                 -- window end epoch seconds
    result_key TEXT NOT NULL,             -- value of the distinct attribute for this row
    count INTEGER NOT NULL,               -- events in this group
    retrieved_at_epoch INTEGER NOT NULL,  -- when this snapshot was fetched
    PRIMARY KEY (org_id, distinct, start, end, result_key)
);

CREATE INDEX IF NOT EXISTS idx_org_dev_evt_count_res_org
    ON org_device_events_count_results(org_id);

CREATE INDEX IF NOT EXISTS idx_org_dev_evt_count_res_distinct
    ON org_device_events_count_results(distinct, result_key);
```

**Notes on DDL**:
- SQLite reserves the keyword `LIMIT`. The column is named `limit_value` in the table
  even though the JSON field is `limit`, to avoid quoting issues. The Python flattener
  performs the rename.
- `distinct` is *not* a reserved SQLite keyword in column position; it is reserved only
  in `SELECT DISTINCT` context. Quoting is unnecessary but the application uses
  parameterized queries throughout.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

```python
# In MistHelper.py, near line ~1672 in the ENDPOINT_PRIMARY_KEY_STRATEGIES dict:

"countOrgDeviceEvents": {
    "type": "composite_pk",                                # No API UUID; tuple identifies a snapshot
    "tables": {                                            # Two related tables produced from one response
        "org_device_events_count_summary": {               # Top-level summary row
            "primary_key": ["org_id", "distinct", "start", "end"],
            "indexes": ["org_id"],
        },
        "org_device_events_count_results": {               # Per-group detail rows
            "primary_key": ["org_id", "distinct", "start", "end", "result_key"],
            "indexes": ["org_id", "distinct"],
        },
    },
    "upsert_mode": "INSERT OR REPLACE",                    # Newer snapshot overwrites older
    "notes": (                                             # Operator-facing context
        "Read-only count endpoint. The same (org, distinct, window) tuple "
        "overwrites; a different window inserts a new snapshot."
    ),
},
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` schema only supports single-table
entries (one operationId -> one table), the implementation registers two entries instead
(`countOrgDeviceEvents__summary` and `countOrgDeviceEvents__results`) keyed by the
`api_function_name` argument that `DataExporter.write_with_format_selection()` receives.
The decision between the two registration shapes is made at task generation time after
inspecting the current dict structure in `MistHelper.py`.
