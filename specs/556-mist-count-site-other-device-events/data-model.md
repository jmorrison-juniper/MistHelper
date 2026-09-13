# Phase 1 Data Model: countSiteOtherDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Contract**: [contracts/count_site_other_device_events.md](./contracts/count_site_other_device_events.md)

## Entities

The endpoint returns a single JSON object (the `OtherDeviceEventsCountEnvelope`)
containing one repeated child entity (the `OtherDeviceEventsCountResult`).
MistHelper persists each as its own SQLite table so the summary row and the
per-group detail rows do not have to share a schema.

### Entity 1: `OtherDeviceEventsCountEnvelope` (summary, one row per run)

Captured fields (top-level keys in the 200 response):

| Field | JSON Type | Python Type | Required | Notes |
|-------|-----------|-------------|----------|-------|
| `site_id` | n/a (caller-supplied) | `str` | Yes | Foreign key to the site that the menu invocation targeted. Injected by MistHelper so the row is self-contained. |
| `distinct` | string | `str` | Yes | Attribute that the API grouped counts by (e.g. `"type"`, `"mac"`, `"model"`). |
| `start` | integer (epoch s) | `int` | Yes | Start of the queried window as returned by the API. |
| `end` | integer (epoch s) | `int` | Yes | End of the queried window as returned by the API. |
| `limit` | integer | `int` | Yes | Max number of distinct groups returned (mirrors the request `limit`). |
| `total` | integer | `int` | Yes | Total number of distinct groups the API observed (may exceed `limit`). |
| `captured_at` | n/a (injected) | `int` (epoch s) | Yes | UTC epoch seconds at which the row was written. Injected by MistHelper for run history. |

**Primary Key**: surrogate `misthelper_internal_id` autoincrement, with a
`UNIQUE(site_id, distinct, start, end)` index so re-runs upsert cleanly.

**Foreign Keys**: `site_id` references the `sites` table populated by the
existing `listOrgSites` exporter (foreign key is logical -- enforced at
application layer, not via SQLite `FOREIGN KEY` constraints because the
multi-backend exporter must remain backend-agnostic).

**State Transitions**: N/A -- read-only endpoint. Each call produces a new
row (or upserts an existing one); rows are never mutated by MistHelper after
write.

### Entity 2: `OtherDeviceEventsCountResult` (per-group detail, N rows per run)

Captured fields (one per item in the `results` array):

| Field | JSON Type | Python Type | Required | Notes |
|-------|-----------|-------------|----------|-------|
| `site_id` | n/a (caller-supplied) | `str` | Yes | Injected; same value as the parent summary row. |
| `distinct` | n/a (caller-supplied) | `str` | Yes | Injected; same value as the parent summary row. Identifies which attribute `group_value` represents. |
| `start` | n/a (caller-supplied) | `int` | Yes | Injected; same window as parent. |
| `end` | n/a (caller-supplied) | `int` | Yes | Injected; same window as parent. |
| `group_value` | string | `str` | Yes | The actual value of the `distinct` attribute for this group (e.g. the event type name, the MAC string, the model string). Sourced from whichever key in the result object is not `count`. |
| `count` | integer | `int` | Yes | Number of events observed for this distinct group within the window. The only field the API guarantees by name. |
| `captured_at` | n/a (injected) | `int` (epoch s) | Yes | UTC epoch seconds; matches the parent summary row's `captured_at` for the same run. |

**Primary Key**: composite `(site_id, distinct, start, end, group_value)`.

**Foreign Keys**: `(site_id, distinct, start, end)` references the matching
unique tuple in `site_other_device_events_count_summary`. Logical foreign key
only (see Entity 1 note).

**State Transitions**: N/A -- read-only endpoint.

## SQLite DDL

The two tables below are created automatically on first write by
`DataExporter`; the DDL is documented here so reviewers can verify the schema
matches the entity model. Column types use SQLite's flexible type affinity --
strings stored as `TEXT`, epochs and counts as `INTEGER`.

```sql
-- Summary: one row per (site_id, distinct, start, end) run combination.
CREATE TABLE IF NOT EXISTS site_other_device_events_count_summary (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Surrogate PK for auto_increment_with_unique strategy
    site_id                TEXT    NOT NULL,                    -- Caller-supplied site UUID
    distinct               TEXT    NOT NULL,                    -- The attribute name the API grouped by
    start                  INTEGER NOT NULL,                    -- Window start, epoch seconds
    end                    INTEGER NOT NULL,                    -- Window end, epoch seconds
    "limit"                INTEGER NOT NULL,                    -- Max groups returned (column quoted; LIMIT is reserved)
    total                  INTEGER NOT NULL,                    -- Total distinct groups the API saw
    captured_at            INTEGER NOT NULL,                    -- UTC epoch when row was written
    UNIQUE (site_id, distinct, start, end)                      -- Composite uniqueness for clean upsert
);

-- Details: one row per distinct group in the results array.
CREATE TABLE IF NOT EXISTS site_other_device_events_count_results (
    site_id      TEXT    NOT NULL,                              -- Caller-supplied site UUID
    distinct     TEXT    NOT NULL,                              -- Same as parent summary
    start        INTEGER NOT NULL,                              -- Window start, epoch seconds
    end          INTEGER NOT NULL,                              -- Window end, epoch seconds
    group_value  TEXT    NOT NULL,                              -- The value of the distinct attribute for this row
    count        INTEGER NOT NULL,                              -- Event count for this group
    captured_at  INTEGER NOT NULL,                              -- UTC epoch when row was written
    PRIMARY KEY (site_id, distinct, start, end, group_value)    -- Composite PK upserts cleanly on re-run
);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the entry below to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (the dictionary lives near line ~1672 per the agent guide).
The exporter consults this entry on every write to choose between
`INSERT`, `INSERT OR REPLACE`, and surrogate-key insertion.

```python
'countSiteOtherDeviceEvents': {                                # operationId is the lookup key
    'type': 'composite_pk',                                    # Default routing for the per-group results table
    'primary_key': ['site_id', 'distinct', 'start', 'end', 'group_value'],  # Composite PK on the results table
    'summary_table': {                                         # Optional sibling table for the run-level summary row
        'type': 'auto_increment_with_unique',                  # Surrogate PK with UNIQUE constraint
        'primary_key': ['misthelper_internal_id'],             # Internal auto-increment PK
        'unique_index': ['site_id', 'distinct', 'start', 'end'],  # Logical uniqueness for clean upsert
    },
    'indexes': ['site_id', 'distinct', 'captured_at'],         # Secondary indexes for common NOC queries
    'table_name': 'site_other_device_events_count_results',    # Override default snake_case derivation
    'summary_table_name': 'site_other_device_events_count_summary',  # Override for the summary sibling
}
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in MistHelper.py
does not yet support a nested `summary_table` block, the implementer's first
task is to extend the strategy-handling code in `DataExporter` to honor it --
this is an additive change with no impact on any sibling endpoint. The
existing `composite_pk` and `auto_increment_with_unique` routings already work
in isolation; the new field simply binds the two together for endpoints that
return both a summary envelope and a per-group results array.
