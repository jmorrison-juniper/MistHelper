# Phase 1 Data Model: countSiteWanClients

**Feature**: 563-mist-count-site-wan-clients
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)

## Entities

The endpoint returns a single envelope object containing a `results` array. We model
this as two related entities so that the multi-backend exporter can persist a flat
row-per-bucket projection while preserving the per-invocation context.

### Entity 1: `WanClientCountSummary` (one row per invocation)

The request / response envelope. One row is written per call to the menu item.

| Field            | Type    | Source                       | PK | FK | Notes |
|------------------|---------|------------------------------|----|----|-------|
| `site_id`        | TEXT    | path parameter               | Y  | -> `sites(id)` | Mist site UUID |
| `distinct`       | TEXT    | response `distinct`          | Y  |    | Echoed facet name; empty string if not supplied |
| `start_epoch`    | INTEGER | response `start`             | Y  |    | UTC epoch seconds |
| `end_epoch`      | INTEGER | response `end`               | Y  |    | UTC epoch seconds |
| `limit_value`    | INTEGER | response `limit`             |    |    | Echoed `limit` query parameter |
| `total`          | INTEGER | response `total`             |    |    | Total matched clients across all buckets |
| `bucket_count`   | INTEGER | derived (`len(results)`)     |    |    | Convenience column for quick scans |
| `duration_input` | TEXT    | user input (echoed)          |    |    | `1d`, `7d`, etc. -- recorded for forensics |
| `fetched_at`     | INTEGER | UTC epoch at call time       |    |    | Insertion timestamp for audit |

Primary key: composite `(site_id, distinct, start_epoch, end_epoch)`.

### Entity 2: `WanClientCountBucket` (one row per `results[]` element)

Each bucket row from the response.

| Field            | Type    | Source                                                | PK | FK | Notes |
|------------------|---------|-------------------------------------------------------|----|----|-------|
| `site_id`        | TEXT    | path parameter                                        | Y  | -> `sites(id)` | Mist site UUID |
| `distinct`       | TEXT    | response `distinct`                                   | Y  | -> `site_wan_clients_count_summary(distinct)` | Facet name |
| `start_epoch`    | INTEGER | response `start`                                      | Y  | -> summary | Window start |
| `end_epoch`      | INTEGER | response `end`                                        | Y  | -> summary | Window end |
| `distinct_value` | TEXT    | the non-`count` key inside each `results[]` element   | Y  |    | The facet value (MAC, IP, hostname, etc.). Stringified for column safety. |
| `count`          | INTEGER | response `results[].count`                            |    |    | Per-bucket client count |
| `fetched_at`     | INTEGER | UTC epoch at call time                                |    |    | Insertion timestamp for audit |

Primary key: composite `(site_id, distinct, start_epoch, end_epoch, distinct_value)`.

The relationship `WanClientCountBucket.(site_id, distinct, start_epoch, end_epoch)` ->
`WanClientCountSummary.(site_id, distinct, start_epoch, end_epoch)` is enforced by
shared composite key values; SQLite-level FK constraints are not added because the two
tables are co-written in a single exporter call and the existing MistHelper schema
convention is to keep cross-table FKs out of generated DDL.

## State Transitions

**N/A -- read-only endpoint.** No state machine. Each invocation produces an
idempotent upsert keyed by the composite PK; identical inputs within the same window
update only `total`, `bucket_count`, and `fetched_at`, and refresh bucket counts in
place.

## SQLite DDL

```sql
-- Envelope row, one per invocation.
CREATE TABLE IF NOT EXISTS site_wan_clients_count_summary (
    site_id         TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    start_epoch     INTEGER NOT NULL,
    end_epoch       INTEGER NOT NULL,
    limit_value     INTEGER,
    total           INTEGER,
    bucket_count    INTEGER,
    duration_input  TEXT,
    fetched_at      INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_wcc_summary_site ON site_wan_clients_count_summary(site_id);
CREATE INDEX IF NOT EXISTS idx_wcc_summary_window ON site_wan_clients_count_summary(start_epoch, end_epoch);

-- One row per bucket returned in results[].
CREATE TABLE IF NOT EXISTS site_wan_clients_count_buckets (
    site_id         TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    start_epoch     INTEGER NOT NULL,
    end_epoch       INTEGER NOT NULL,
    distinct_value  TEXT    NOT NULL,
    count           INTEGER NOT NULL,
    fetched_at      INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, start_epoch, end_epoch, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_wcc_buckets_site ON site_wan_clients_count_buckets(site_id);
CREATE INDEX IF NOT EXISTS idx_wcc_buckets_facet ON site_wan_clients_count_buckets(distinct);
CREATE INDEX IF NOT EXISTS idx_wcc_buckets_count ON site_wan_clients_count_buckets(count);
```

`DataExporter.write_with_format_selection()` creates the tables on first run and
performs `INSERT OR REPLACE` upserts on subsequent runs, matching the documented
hybrid primary-key behavior in `.github/copilot-instructions.md` (Database Strategy
section).

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add this entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py`
(near line ~1672, alphabetically among the `c*` operationIds):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteWanClients'] = {
    # Aggregated time-windowed count endpoint -- no API-issued stable id, so a
    # composite of (site, facet, window, facet-value) gives clean idempotent upserts.
    'type': 'composite_pk',
    'primary_key': [
        'site_id',         # which site the count belongs to
        'distinct',        # which facet the buckets are grouped by
        'start_epoch',     # window start, UTC epoch seconds
        'end_epoch',       # window end, UTC epoch seconds
        'distinct_value',  # the per-bucket facet value
    ],
    'indexes': [
        'site_id',         # most common filter for ad-hoc queries
        'distinct',        # second-most common filter (per-facet rollups)
        'start_epoch',     # window-based scans
    ],
}
```

Every line in this dict entry carries an inline comment per Constitution Principle VI
(NON-NEGOTIABLE).

## ArangoDB / Redis Notes

`DataExporter` maps the two SQLite tables 1:1 to ArangoDB collections of the same
names. Redis caches the most recent summary row keyed by
`mist:wan_clients_count_summary:<site_id>:<distinct>:<start_epoch>:<end_epoch>` with a
TTL governed by the existing `MIST_CACHE_TTL_SECONDS` setting. No new graph edges are
required for this read-only endpoint (the `sites` collection already supports the
implicit `(site_id) -> site` relationship used by other site-scoped exports).
