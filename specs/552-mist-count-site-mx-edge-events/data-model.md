# Phase 1 Data Model: countSiteMxEdgeEvents

**Feature**: 552-mist-count-site-mx-edge-events
**Source**: `documentation/api/sites/GET_sites_site_id_mxedges_events_count.md`

## Entities

The endpoint returns a single JSON envelope. MistHelper splits it into two
logical entities for clean persistence and CSV output.

### Entity 1: `MxEdgeEventCountSummary` (envelope)

One row per `(site_id, distinct, start, end)` slice. Captures the request
window metadata and the total event count.

| Field             | Type    | Source                  | Notes                                                                |
|-------------------|---------|-------------------------|----------------------------------------------------------------------|
| `site_id`         | TEXT    | request path param      | PK component; UUID of the queried site                               |
| `distinct`        | TEXT    | response `distinct`     | PK component; grouping attribute echoed by the API                   |
| `start`           | INTEGER | response `start`        | PK component; epoch seconds (int32)                                  |
| `end`             | INTEGER | response `end`          | PK component; epoch seconds (int32)                                  |
| `total`           | INTEGER | response `total`        | Total event count across all buckets                                 |
| `limit`           | INTEGER | response `limit`        | Echoed bucket cap from the request                                   |
| `bucket_count`    | INTEGER | `len(results)`          | Number of buckets returned (derived; helpful for CSV consumers)      |
| `retrieved_at`    | INTEGER | runtime                 | Epoch seconds when MistHelper fetched the row (audit / freshness)    |

**Primary key**: composite `(site_id, distinct, start, end)`.

**Foreign keys**: `site_id` references the `sites` table populated by
`listOrgSites` (menu 1) when SQLite is the backend. Enforcement is logical
only -- SQLite foreign keys are not enabled by default in MistHelper; the
relationship is documented for ArangoDB graph edges and for human readers.

**State transitions**: N/A -- read-only endpoint. Each run upserts the row;
no lifecycle states exist.

### Entity 2: `MxEdgeEventCountBucket` (per-distinct-value row)

One row per `results[*]` item. Each bucket is a `{count, <distinct_attr>: str}`
pair where the attribute name varies by request (driven by the `distinct`
query parameter).

| Field            | Type    | Source                                       | Notes                                              |
|------------------|---------|----------------------------------------------|----------------------------------------------------|
| `site_id`        | TEXT    | parent envelope                              | PK component (FK to summary)                       |
| `distinct`       | TEXT    | parent envelope                              | PK component (FK to summary)                       |
| `start`          | INTEGER | parent envelope                              | PK component (FK to summary)                       |
| `end`            | INTEGER | parent envelope                              | PK component (FK to summary)                       |
| `bucket_key`     | TEXT    | response `results[i]` non-`count` key name   | PK component; equals `distinct` for valid replies  |
| `bucket_value`   | TEXT    | response `results[i]` non-`count` key value  | PK component; the actual grouping value            |
| `count`          | INTEGER | response `results[i].count`                  | Event count for this bucket                        |
| `retrieved_at`   | INTEGER | runtime                                      | Epoch seconds; mirrors the envelope value          |

**Primary key**: composite
`(site_id, distinct, start, end, bucket_key, bucket_value)`.

**Foreign keys**: `(site_id, distinct, start, end)` references the summary
table -- documented logical FK; not DDL-enforced (matches MistHelper precedent).

**State transitions**: N/A -- read-only endpoint.

## SQLite DDL

```sql
-- Envelope: one row per (site, distinct, time-window) slice.
CREATE TABLE IF NOT EXISTS site_mxedge_events_count_summary (
    site_id      TEXT    NOT NULL,           -- Site UUID from the request path
    distinct     TEXT    NOT NULL,           -- Grouping attribute (e.g. type, service)
    start        INTEGER NOT NULL,           -- Window start epoch seconds
    end          INTEGER NOT NULL,           -- Window end epoch seconds
    total        INTEGER NOT NULL,           -- Total events across all buckets
    "limit"      INTEGER NOT NULL,           -- Bucket cap echoed by the API
    bucket_count INTEGER NOT NULL,           -- Number of buckets returned (derived)
    retrieved_at INTEGER NOT NULL,           -- Audit timestamp of this MistHelper run
    PRIMARY KEY (site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_mxedge_count_summary_site
    ON site_mxedge_events_count_summary(site_id);
CREATE INDEX IF NOT EXISTS idx_mxedge_count_summary_distinct
    ON site_mxedge_events_count_summary(distinct);

-- Buckets: one row per (envelope, grouping value).
CREATE TABLE IF NOT EXISTS site_mxedge_events_count_buckets (
    site_id      TEXT    NOT NULL,           -- FK to summary
    distinct     TEXT    NOT NULL,           -- FK to summary
    start        INTEGER NOT NULL,           -- FK to summary
    end          INTEGER NOT NULL,           -- FK to summary
    bucket_key   TEXT    NOT NULL,           -- Dynamic attribute name from results[i]
    bucket_value TEXT    NOT NULL,           -- Observed grouping value
    count        INTEGER NOT NULL,           -- Event count for this bucket
    retrieved_at INTEGER NOT NULL,           -- Audit timestamp of this MistHelper run
    PRIMARY KEY (site_id, distinct, start, end, bucket_key, bucket_value)
);

CREATE INDEX IF NOT EXISTS idx_mxedge_count_buckets_site
    ON site_mxedge_events_count_buckets(site_id);
CREATE INDEX IF NOT EXISTS idx_mxedge_count_buckets_value
    ON site_mxedge_events_count_buckets(bucket_value);
```

Notes:
- `"limit"` is quoted because `limit` is a SQLite reserved word.
- `INSERT OR REPLACE` (MistHelper's standard upsert for composite_pk
  strategies) overwrites a slice on re-run without producing duplicate rows.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

The implementation registers the operationId once with a two-table strategy
list (matching the precedent for other endpoints that split a single API
response across multiple SQLite tables):

```python
'countSiteMxEdgeEvents': {                       # OperationId from OpenAPI
    'type': 'composite_pk',                       # Time-windowed aggregate, no UUID
    'tables': [                                   # Two tables: envelope + buckets
        {
            'name': 'site_mxedge_events_count_summary',   # Envelope rows
            'primary_key': [                              # Deterministic per slice
                'site_id', 'distinct', 'start', 'end',
            ],
            'indexes': ['site_id', 'distinct'],           # Filter-by-site / by-grouping
        },
        {
            'name': 'site_mxedge_events_count_buckets',   # Per-bucket rows
            'primary_key': [                              # Extends summary PK with bucket pair
                'site_id', 'distinct', 'start', 'end',
                'bucket_key', 'bucket_value',
            ],
            'indexes': ['site_id', 'bucket_value'],       # Filter-by-site / by-value
        },
    ],
},
```

Behavior: On every menu invocation, `DataExporter.write_with_format_selection()`
upserts the envelope row first and then upserts each bucket row. Re-running
the menu against the same `(site_id, distinct, start, end)` slice overwrites
the prior result without producing duplicate rows; running it against a new
slice (different grouping or new time window) appends new rows alongside the
existing data.
