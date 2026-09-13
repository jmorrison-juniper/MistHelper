# Phase 1 Data Model: countOrgWanClientEvents

**Feature**: 534-mist-count-org-wan-client-events
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Entities Returned by the Endpoint

The 200-response is a single JSON object (the "count summary envelope")
that contains zero or more rows of grouped-by-distinct counts in its
`results[]` array. MistHelper flattens this into two related entities for
persistence.

### Entity 1: WanClientEventsCountSummary (envelope)

One row per (org_id, distinct, start, end) request tuple.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `misthelper_internal_id` | INTEGER | yes (PK) | auto-increment | local-only synthetic key |
| `org_id` | TEXT | yes | path param | Mist org UUID (FK to org records) |
| `distinct` | TEXT | yes | response `distinct` | echoes the request grouping attribute |
| `start` | INTEGER | yes | response `start` | epoch seconds, server-resolved |
| `end` | INTEGER | yes | response `end` | epoch seconds, server-resolved |
| `limit` | INTEGER | yes | response `limit` | row cap actually applied |
| `total` | INTEGER | yes | response `total` | total events matching the filter (sum of all counts before limit) |
| `event_type_filter` | TEXT | no | request `type` | NULL when caller passed no filter |
| `duration_requested` | TEXT | no | local | original user duration string, useful for diffing relative-time runs |
| `fetched_at` | INTEGER | yes | local | epoch seconds when MistHelper recorded the row |

Primary key: `misthelper_internal_id` (auto-increment).
Unique constraint: (`org_id`, `distinct`, `start`, `end`,
`COALESCE(event_type_filter, '')`).
Foreign keys: `org_id` references the organization records produced by
`listOrgs` / similar (not enforced as a hard FK constraint, since
MistHelper SQLite tables are loosely coupled).

### Entity 2: WanClientEventsCountResult (per-distinct-value row)

One row per element of `results[]` in the response. The shape per item is:
`{ "count": <int>, "<distinct>": "<value>" }` -- a required integer count
plus exactly one sibling key whose name is whatever the caller passed as
`distinct`. MistHelper normalizes the variable sibling key into a constant
column named `value`.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `misthelper_internal_id` | INTEGER | yes (PK) | auto-increment | local-only synthetic key |
| `summary_id` | INTEGER | yes | local | FK to `WanClientEventsCountSummary.misthelper_internal_id` |
| `org_id` | TEXT | yes | path param | duplicated for query convenience |
| `distinct` | TEXT | yes | response `distinct` | echoes the request grouping attribute |
| `value` | TEXT | yes | response `results[i].<distinct>` | the grouping value for this row |
| `count` | INTEGER | yes | response `results[i].count` | event count for this group |
| `start` | INTEGER | yes | parent envelope | duplicated for query convenience |
| `end` | INTEGER | yes | parent envelope | duplicated for query convenience |
| `fetched_at` | INTEGER | yes | local | epoch seconds when recorded |

Primary key: `misthelper_internal_id` (auto-increment).
Unique constraint: (`org_id`, `distinct`, `start`, `end`, `value`).
Foreign key: `summary_id` -> `WanClientEventsCountSummary.misthelper_internal_id`.

## State Transitions

**N/A -- read-only endpoint.** The Mist API call is a pure GET aggregation
with no server-side state change. MistHelper's local representation has
exactly two states per row: *absent* (never fetched) and *present* (fetched
at least once). Re-running the menu item with the same (org_id, distinct,
start, end, value) tuple upserts in place via the unique constraint; no
intermediate states exist.

## SQLite DDL

```sql
-- Envelope: one row per request window.
CREATE TABLE IF NOT EXISTS org_wan_client_events_count_summary (
    misthelper_internal_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id                  TEXT    NOT NULL,
    distinct                TEXT    NOT NULL,
    start                   INTEGER NOT NULL,
    end                     INTEGER NOT NULL,
    limit                   INTEGER NOT NULL,
    total                   INTEGER NOT NULL,
    event_type_filter       TEXT,
    duration_requested      TEXT,
    fetched_at              INTEGER NOT NULL,
    UNIQUE (org_id, distinct, start, end, COALESCE(event_type_filter, ''))
);

CREATE INDEX IF NOT EXISTS idx_wan_evt_cnt_sum_org
    ON org_wan_client_events_count_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_wan_evt_cnt_sum_window
    ON org_wan_client_events_count_summary (start, end);

-- Per-distinct-value rows.
CREATE TABLE IF NOT EXISTS org_wan_client_events_count_results (
    misthelper_internal_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id              INTEGER NOT NULL,
    org_id                  TEXT    NOT NULL,
    distinct                TEXT    NOT NULL,
    value                   TEXT    NOT NULL,
    count                   INTEGER NOT NULL,
    start                   INTEGER NOT NULL,
    end                     INTEGER NOT NULL,
    fetched_at              INTEGER NOT NULL,
    UNIQUE (org_id, distinct, start, end, value),
    FOREIGN KEY (summary_id)
        REFERENCES org_wan_client_events_count_summary (misthelper_internal_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wan_evt_cnt_res_summary
    ON org_wan_client_events_count_results (summary_id);
CREATE INDEX IF NOT EXISTS idx_wan_evt_cnt_res_org_value
    ON org_wan_client_events_count_results (org_id, value);
```

Note: the `INSERT OR REPLACE` upsert semantics used elsewhere in MistHelper
work in tandem with the `UNIQUE` constraints above; the auto-increment PK
is overwritten on collision so repeated runs do not bloat the row count.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
"countOrgWanClientEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraints": [
        ["org_id", "distinct", "start", "end", "event_type_filter"],
        ["org_id", "distinct", "start", "end", "value"],
    ],
    "indexes": [
        "org_id",
        "distinct",
        "start",
        "end",
        "value",
    ],
    "tables": {
        "summary": "org_wan_client_events_count_summary",
        "results": "org_wan_client_events_count_results",
    },
},
```

This entry is inserted into the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (around
line 1672 per the AI-Agent Instructions). The two-table form mirrors the
pattern used by spec 500 (`GetOrgLicenseAsyncClaimStatus`) and is supported
by `DataExporter.write_with_format_selection()` when the caller passes the
`api_function_name="countOrgWanClientEvents"` kwarg.

## Field-Level Validation Rules

- `org_id`: must match the Mist UUID regex
  `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`.
  Invalid -> log WARNING, return early.
- `distinct`: must be one of the documented attributes (`type`, `mac`,
  `gateway`, `port_id`, `wan_ip`). Invalid -> log WARNING, return early.
- `event_type_filter`: free-form string passed through; empty/None
  bypasses the filter.
- `start`/`end`: integer epoch seconds or relative-time strings
  (`-1d`, `-2h`, `now`); validated by the SDK, not MistHelper.
- `duration_requested`: free-form string, accepted only when neither
  `start` nor `end` are supplied; defaults to `"1d"`.
- `limit`: integer in [1, 1000]; coerced to 100 if blank.
- `fetched_at`: filled by MistHelper using `int(time.time())` at write
  time; never read from the API.
