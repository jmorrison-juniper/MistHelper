# Phase 1 Data Model: countSiteWirelessClientEvents

**Feature**: 567-mist-count-site-wireless-client-events
**Date**: 2026-06-29
**Source schema**: 200 response in
`documentation/api/sites/GET_sites_site_id_clients_events_count.md`.

---

## Entities

The endpoint returns one logical object (`CountResponse`) containing an envelope and
an array of `CountResult` rows. MistHelper persists these as two tables.

### Entity 1: CountResponseSummary

One row per query invocation. Captures the envelope metadata returned alongside the
grouping buckets.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `site_id` | TEXT (UUID) | yes | menu prompt | Path parameter; foreign key to `sites.id` |
| `distinct` | TEXT | yes | response.distinct | The grouping attribute echoed by the API |
| `start` | INTEGER | yes | response.start | Window start, epoch seconds (int32) |
| `end` | INTEGER | yes | response.end | Window end, epoch seconds (int32) |
| `limit` | INTEGER | yes | response.limit | Max buckets returned by the API |
| `total` | INTEGER | yes | response.total | Total event count summed across all buckets |
| `query_duration` | TEXT | no | menu prompt | The `duration` value the user supplied (for example `"1d"`); NULL if the user supplied explicit `start`/`end` |
| `retrieved_at` | INTEGER | yes | computed | Local epoch seconds at which MistHelper persisted the row |

**Primary key**: composite `(site_id, distinct, start, end)`.

**Foreign keys**:

- `site_id` references the locally cached `sites.id` SQLite table populated by menu 1
  (`listOrgSites`) -- enforced at the application layer, not as a SQLite FOREIGN KEY,
  to keep partial-cache scenarios working.

### Entity 2: CountResultBucket

One row per grouping bucket. Captures the per-attribute-value count.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `site_id` | TEXT (UUID) | yes | menu prompt | Identifies the parent summary row |
| `distinct` | TEXT | yes | summary.distinct | Identifies the parent summary row |
| `bucket_key` | TEXT | yes | response.results[i].<distinct value> | The actual attribute value for this bucket (for example the SSID name when `distinct=ssid`) |
| `count` | INTEGER | yes | response.results[i].count | Number of events in this bucket |
| `start` | INTEGER | yes | response.start | Window start, epoch seconds (echoed into each bucket for upsert keying) |
| `end` | INTEGER | yes | response.end | Window end, epoch seconds (echoed into each bucket for upsert keying) |
| `retrieved_at` | INTEGER | yes | computed | Local epoch seconds when MistHelper persisted the row |

**Primary key**: composite `(site_id, distinct, bucket_key, start, end)`.

**Foreign keys**:

- `(site_id, distinct, start, end)` references
  `site_wireless_client_events_count_summary` -- enforced at the application layer.

---

## State Transitions

N/A -- this is a read-only endpoint. Rows are inserted (or upserted on repeat) by the
MistHelper menu method and are never mutated in place. The endpoint has no concept of
status or lifecycle. The composite primary key gives natural idempotency: re-running
the same query against the same window simply refreshes the count for that
(site, distinct, bucket_key, window) tuple.

---

## SQLite DDL

```sql
-- Summary table: one row per (site, distinct, start, end) query
CREATE TABLE IF NOT EXISTS site_wireless_client_events_count_summary (
    site_id         TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    start           INTEGER NOT NULL,
    end             INTEGER NOT NULL,
    limit           INTEGER NOT NULL,
    total           INTEGER NOT NULL,
    query_duration  TEXT,
    retrieved_at    INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_swcec_summary_site
    ON site_wireless_client_events_count_summary (site_id);

CREATE INDEX IF NOT EXISTS idx_swcec_summary_retrieved
    ON site_wireless_client_events_count_summary (retrieved_at);

-- Results table: one row per bucket within a summary row
CREATE TABLE IF NOT EXISTS site_wireless_client_events_count_results (
    site_id         TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    bucket_key      TEXT    NOT NULL,
    count           INTEGER NOT NULL,
    start           INTEGER NOT NULL,
    end             INTEGER NOT NULL,
    retrieved_at    INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, bucket_key, start, end)
);

CREATE INDEX IF NOT EXISTS idx_swcec_results_site
    ON site_wireless_client_events_count_results (site_id);

CREATE INDEX IF NOT EXISTS idx_swcec_results_distinct
    ON site_wireless_client_events_count_results (site_id, distinct);

CREATE INDEX IF NOT EXISTS idx_swcec_results_count
    ON site_wireless_client_events_count_results (count DESC);
```

`DataExporter` issues `INSERT OR REPLACE` against these tables on every run, so the
composite primary key drives clean upserts without duplicates.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (around line 1672, alphabetically among the `countSite*` siblings):

```python
'countSiteWirelessClientEvents': {                           # operationId from spec.md
    'type': 'composite_pk',                                  # time-series style aggregation
    'primary_key': [                                         # composite key columns in order
        'site_id',                                           # site under inspection
        'distinct',                                          # grouping attribute requested
        'bucket_key',                                        # group-value for this row
        'start',                                             # window start epoch seconds
        'end',                                               # window end epoch seconds
    ],
    'indexes': [                                             # secondary indexes for analytics
        'site_id',                                           # all buckets for one site
        'distinct',                                          # all rows for one grouping
        'count',                                             # rank buckets by count desc
    ],
    'tables': {                                              # two-table emission pattern
        'summary': 'site_wireless_client_events_count_summary',
        'results': 'site_wireless_client_events_count_results',
    },
},
```

Every line above carries an inline comment, satisfying Constitution Principle VI.
