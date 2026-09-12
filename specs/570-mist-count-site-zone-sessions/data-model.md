# Phase 1 Data Model: countSiteZoneSessions

**Feature**: 570-mist-count-site-zone-sessions
**Date**: 2026-06-29
**Source schema**: `documentation/api/sites/GET_sites_site_id_zone_type_count.md` (200 response)

## Entities

The endpoint returns a single envelope object with one nested array. Two logical
entities are modelled below.

### Entity 1: `CountEnvelope`

Top-level object describing the query parameters echoed by the server and the size of
the result set. Persisted as columns on every row (de-normalized for analyst
convenience) rather than as a separate table -- one envelope per call would create a
table of one row per run and force a JOIN for every analyst query, which contradicts
the catalogue intent of the menu.

| Field      | Type    | Source        | Notes                                                |
|------------|---------|---------------|------------------------------------------------------|
| distinct   | string  | response root | Echo of the distinct attribute requested             |
| start      | integer | response root | Epoch seconds, inclusive lower bound of the window   |
| end        | integer | response root | Epoch seconds, inclusive upper bound of the window   |
| limit      | integer | response root | Server-applied cap on `results[]` length             |
| total      | integer | response root | Total distinct values found before the limit was applied |

### Entity 2: `count_result` (one per row in `results[]`)

| Field          | Type    | Source                                | Notes                                                  |
|----------------|---------|---------------------------------------|--------------------------------------------------------|
| count          | integer | `results[*].count` (required)         | Number of zone session events matching the distinct value |
| distinct_value | string  | `results[*].<distinct attribute>`     | Value of the requested distinct attribute (e.g. zone_id) |

The OpenAPI schema declares `additionalProperties: { type: string }` on each
`count_result`, so the distinct attribute appears as an opaque string-typed key. The
flattener reads the requested `distinct` argument back from the envelope and uses it to
pluck the corresponding value into `distinct_value`.

### Foreign Keys

| Column        | References                                            | Notes                                |
|---------------|-------------------------------------------------------|--------------------------------------|
| site_id       | `listOrgSites.id`                                     | Site that owns the zone collection   |
| distinct_value (when distinct=`zone_id`)  | `listSiteZones.id`         | Zone the count belongs to            |
| distinct_value (when distinct=`map_id`)   | `listSiteMaps.id`          | Map the count belongs to             |

These foreign-key relationships are advisory (no DB-level FK constraint is enforced in
SQLite) because the `distinct_value` column type depends on the `distinct` column for
its semantic meaning.

## State Transitions

N/A -- read-only endpoint. The persisted rows are immutable count snapshots over a
declared `start..end` window. Re-running the menu for the same window upserts; running
it for a new window inserts new rows.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS site_zone_session_counts (
    site_id        TEXT    NOT NULL,
    zone_type      TEXT    NOT NULL,
    distinct       TEXT    NOT NULL,
    distinct_value TEXT    NOT NULL,
    count          INTEGER NOT NULL,
    start          INTEGER NOT NULL,
    end            INTEGER NOT NULL,
    limit          INTEGER,
    total          INTEGER,
    retrieved_at   TEXT,
    PRIMARY KEY (site_id, zone_type, distinct, distinct_value, start, end)
);

CREATE INDEX IF NOT EXISTS idx_site_zone_session_counts_site_id
    ON site_zone_session_counts (site_id);
CREATE INDEX IF NOT EXISTS idx_site_zone_session_counts_zone_type
    ON site_zone_session_counts (zone_type);
CREATE INDEX IF NOT EXISTS idx_site_zone_session_counts_distinct
    ON site_zone_session_counts (distinct);
CREATE INDEX IF NOT EXISTS idx_site_zone_session_counts_distinct_value
    ON site_zone_session_counts (distinct_value);
CREATE INDEX IF NOT EXISTS idx_site_zone_session_counts_total
    ON site_zone_session_counts (total);
```

`DataExporter.write_with_format_selection()` derives the table name from the
operationId and the column list from the first flattened row, then executes
`INSERT OR REPLACE INTO site_zone_session_counts (...) VALUES (...)` for every row,
giving the upsert semantics required by FR-005 and Acceptance Scenario 3 in the spec.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Insert the following entry into the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (located at line 3019) in the "Zone session search" neighborhood near
`searchSiteZoneSessions` (line 3317):

```python
"countSiteZoneSessions": {                                                   # Aggregated counts of zone sessions per distinct attribute.
    "type": "composite_pk",                                                  # Counts re-emerge per window; composite key preserves history.
    "primary_key": [                                                         # Tuple uniquely identifies one count measurement.
        "site_id",                                                           # Site that owns the zone collection.
        "zone_type",                                                         # zones or rssizones.
        "distinct",                                                          # Which attribute the rows are grouped by.
        "distinct_value",                                                    # The literal value of that attribute for the row.
        "start",                                                             # Window lower bound (epoch seconds).
        "end",                                                               # Window upper bound (epoch seconds).
    ],
    "indexes": [                                                             # Analyst-driven query patterns.
        "site_id",                                                           # Per-site distribution.
        "zone_type",                                                         # Split zones from rssizones.
        "distinct",                                                          # Filter by grouping attribute.
        "distinct_value",                                                    # Drill-down on a single value.
        "total",                                                             # Top-N by total.
    ],
    "unique_constraints": [],                                                # PK already enforces uniqueness.
    "description": "Aggregated counts of site zone sessions by distinct attribute and time window",  # Catalogue description.
},
```

Inline comments on every executable key/value satisfy Constitution Principle VI.
