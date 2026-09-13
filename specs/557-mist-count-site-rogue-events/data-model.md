# Phase 1 Data Model: countSiteRogueEvents

This document specifies the entities returned by `GET /api/v1/sites/{site_id}/rogues/events/count`,
the SQLite DDL used to persist them, and the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
registration that drives upsert behavior across all storage backends.

## Entities

The endpoint returns one summary block plus an array of count results. MistHelper
splits these into two logical entities -- one row in a summary table and N rows in
a results table -- to keep the SQLite schema normalized and the upsert tuples
clean.

### Entity 1: `RogueEventCountSummary`

Captures the request envelope: which site, which grouping attribute, which time
window, and the overall row count.

| Field                       | Type    | Source                  | Nullable | Notes                                            |
|-----------------------------|---------|-------------------------|----------|--------------------------------------------------|
| misthelper_internal_id      | INTEGER | auto-increment          | No       | Surrogate primary key                            |
| site_id                     | TEXT    | path param              | No       | UUID of the site (foreign key to `sites.id`)     |
| distinct                    | TEXT    | response.distinct       | No       | Grouping attribute (e.g. `type`, `ssid`, `bssid`)|
| start                       | INTEGER | response.start          | No       | Epoch seconds (window start)                     |
| end                         | INTEGER | response.end            | No       | Epoch seconds (window end)                       |
| limit                       | INTEGER | response.limit          | No       | Page size echoed by the server                   |
| total                       | INTEGER | response.total          | No       | Total rogue events in the window                 |
| retrieved_at_utc            | TEXT    | client clock            | No       | ISO-8601 UTC timestamp of the run                |

**Primary key**: `misthelper_internal_id` (auto-increment).
**Unique constraint**: `(site_id, distinct, start, end)`.
**Foreign key**: `site_id` references `sites(id)` when the sites table is present;
the constraint is advisory only in SQLite when the parent row has not yet been
ingested.

### Entity 2: `RogueEventCountResult`

One row per distinct value returned by the server. The `additionalProperties: string`
clause in the OpenAPI schema means the row carries the count plus one or more
attribute columns whose names match the chosen `distinct` value (for `distinct=type`
the row is `{count: 42, type: "honeypot"}`).

| Field                       | Type    | Source                     | Nullable | Notes                                                |
|-----------------------------|---------|----------------------------|----------|------------------------------------------------------|
| misthelper_internal_id      | INTEGER | auto-increment             | No       | Surrogate primary key                                |
| summary_id                  | INTEGER | parent summary surrogate   | No       | Foreign key to `site_rogue_events_count_summary.misthelper_internal_id` |
| site_id                     | TEXT    | path param (denormalized)  | No       | Carried for index efficiency                         |
| distinct                    | TEXT    | response.distinct (denorm.)| No       | Carried for index efficiency                         |
| distinct_value              | TEXT    | results[i].<distinct>      | Yes      | E.g. `"honeypot"`, `"lan"`, channel `"36"`           |
| count                       | INTEGER | results[i].count           | No       | Aggregated count                                     |
| start                       | INTEGER | parent.start (denorm.)     | No       | Window start (carried for upsert tuple)              |
| end                         | INTEGER | parent.end (denorm.)       | No       | Window end                                           |
| retrieved_at_utc            | TEXT    | client clock               | No       | ISO-8601 UTC timestamp                               |

**Primary key**: `misthelper_internal_id` (auto-increment).
**Unique constraint**: `(site_id, distinct, distinct_value, start, end)`.
**Foreign key**: `summary_id` references
`site_rogue_events_count_summary(misthelper_internal_id)`.

### State Transitions

N/A -- this is a read-only Mist API endpoint. Rows are inserted or replaced on each
invocation; no in-place mutation, no state machine, no soft-delete column. The
adaptive-delay subsystem treats every invocation as independent.

## SQLite DDL

```sql
-- Auto-created by DataExporter on first run for SQLite backend.

CREATE TABLE IF NOT EXISTS site_rogue_events_count_summary (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id                TEXT    NOT NULL,
    distinct               TEXT    NOT NULL,
    start                  INTEGER NOT NULL,
    end                    INTEGER NOT NULL,
    limit                  INTEGER NOT NULL,
    total                  INTEGER NOT NULL,
    retrieved_at_utc       TEXT    NOT NULL,
    UNIQUE (site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_srecs_site_id
    ON site_rogue_events_count_summary (site_id);
CREATE INDEX IF NOT EXISTS idx_srecs_distinct
    ON site_rogue_events_count_summary (distinct);
CREATE INDEX IF NOT EXISTS idx_srecs_start
    ON site_rogue_events_count_summary (start);

CREATE TABLE IF NOT EXISTS site_rogue_events_count_results (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id             INTEGER NOT NULL,
    site_id                TEXT    NOT NULL,
    distinct               TEXT    NOT NULL,
    distinct_value         TEXT,
    count                  INTEGER NOT NULL,
    start                  INTEGER NOT NULL,
    end                    INTEGER NOT NULL,
    retrieved_at_utc       TEXT    NOT NULL,
    UNIQUE (site_id, distinct, distinct_value, start, end),
    FOREIGN KEY (summary_id)
        REFERENCES site_rogue_events_count_summary (misthelper_internal_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_srecr_site_id
    ON site_rogue_events_count_results (site_id);
CREATE INDEX IF NOT EXISTS idx_srecr_distinct
    ON site_rogue_events_count_results (distinct);
CREATE INDEX IF NOT EXISTS idx_srecr_summary
    ON site_rogue_events_count_results (summary_id);
```

Note: `distinct`, `end`, and `limit` are SQLite reserved or contextual keywords but
are valid as column identifiers without quoting in modern SQLite. `DataExporter`
quotes them defensively on insert; the DDL above relies on the parser's column
context.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
# Registered in MistHelper.py near other Sites Rogues entries (search neighborhood
# of searchSiteRogueEvents). Two strategy entries because the response is split
# into two tables; both use auto_increment_with_unique because the aggregation has
# no stable server-supplied id.

ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteRogueEvents_summary"] = {
    "type": "auto_increment_with_unique",                    # No natural id; aggregation
    "primary_key": ["misthelper_internal_id"],               # Surrogate
    "unique": ["site_id", "distinct", "start", "end"],       # One summary per window per group
    "indexes": ["site_id", "distinct", "start"],             # Common read paths
}

ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteRogueEvents_results"] = {
    "type": "auto_increment_with_unique",                    # No natural id; aggregation
    "primary_key": ["misthelper_internal_id"],               # Surrogate
    "unique": [                                              # One count per bucket per window
        "site_id",
        "distinct",
        "distinct_value",
        "start",
        "end",
    ],
    "indexes": ["site_id", "distinct", "summary_id"],        # FK + grouping reads
}
```

The `_summary` / `_results` suffix convention matches the existing pattern used for
other one-to-many Mist responses (e.g. `getOrgLicensesSummary` /
`getOrgLicensesBySite`). The two registrations let `DataExporter.write_with_format_selection`
route each list passed in `data` to the correct table on the same SQLite connection
in a single transaction.
