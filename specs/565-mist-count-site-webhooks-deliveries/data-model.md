# Phase 1 Data Model: countSiteWebhooksDeliveries

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_webhooks_webhook_id_events_count.md`
(200 OK body).

## Entities

The endpoint returns a single JSON object: a count envelope plus an array of bucket
rows. MistHelper splits this into two logical entities for clean multi-backend
persistence.

### Entity 1: `WebhookDeliveriesCountSummary`

One row per (site, webhook, query window, filter combination). Captures the envelope
fields plus all input filter parameters so a snapshot is self-describing without
joining elsewhere.

| Field            | Type     | Source                                | PK? | FK?                              | Notes |
|------------------|----------|---------------------------------------|-----|----------------------------------|-------|
| `site_id`        | TEXT     | MistHelper context (prompt)           | YES | sites.id                         | UUID; injected before write. |
| `webhook_id`     | TEXT     | MistHelper context (prompt)           | YES | site_webhooks.id                 | UUID; injected before write. |
| `distinct`       | TEXT     | API `distinct` (echo of request)      | YES | --                               | Field used for bucketing; `_overall` if request had no `distinct`. |
| `start`          | INTEGER  | API `start`                           | YES | --                               | Epoch seconds; window start. |
| `end`            | INTEGER  | API `end`                             | YES | --                               | Epoch seconds; window end. |
| `status`         | TEXT     | MistHelper context (prompt)           | YES | --                               | Filter echo. Empty string when filter not set. |
| `status_code`    | INTEGER  | MistHelper context (prompt)           | YES | --                               | Filter echo. `-1` sentinel when filter not set. |
| `error`          | TEXT     | MistHelper context (prompt)           | YES | --                               | Filter echo. Empty string when filter not set. |
| `topic`          | TEXT     | MistHelper context (prompt)           | YES | --                               | Filter echo. Empty string when filter not set. |
| `limit`          | INTEGER  | API `limit`                           | --  | --                               | Echo of bucket cap used by Mist. |
| `total`          | INTEGER  | API `total`                           | --  | --                               | Total deliveries in window before bucketing. |
| `bucket_count`   | INTEGER  | len(API `results`)                    | --  | --                               | Convenience cardinality of the bucket array. |
| `duration`       | TEXT     | MistHelper context (prompt)           | --  | --                               | Window duration echo (e.g., `1d`); for audit only. |
| `polled_at_utc`  | TEXT     | MistHelper clock                      | --  | --                               | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `WebhookDeliveriesCountBucket`

Zero or more rows per `WebhookDeliveriesCountSummary`. One row per element of the API
`results` array.

| Field            | Type     | Source                          | PK? | FK?                                                 | Notes |
|------------------|----------|---------------------------------|-----|-----------------------------------------------------|-------|
| `site_id`        | TEXT     | MistHelper context              | YES | webhook_count_summary.site_id                       | UUID. |
| `webhook_id`     | TEXT     | MistHelper context              | YES | webhook_count_summary.webhook_id                    | UUID. |
| `distinct`       | TEXT     | API `distinct`                  | YES | webhook_count_summary.distinct                      | Bucket field name; `_overall` when no distinct. |
| `start`          | INTEGER  | API `start`                     | YES | webhook_count_summary.start                         | Epoch seconds. |
| `end`            | INTEGER  | API `end`                       | YES | webhook_count_summary.end                           | Epoch seconds. |
| `bucket_value`   | TEXT     | API `results[].<distinct>`      | YES | --                                                  | Value of the `distinct` key inside this bucket; `_overall` when no distinct. |
| `count`          | INTEGER  | API `results[].count`           | --  | --                                                  | Deliveries that fall into this bucket. |
| `extra_fields`   | TEXT     | API `results[]` additional props| --  | --                                                  | JSON-encoded leftover string properties on the bucket (for audit). |
| `polled_at_utc`  | TEXT     | MistHelper clock                | --  | --                                                  | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *deliveries* on the Mist side are
created and aged out by the webhook subsystem, but MistHelper does not drive or model
those transitions; it captures snapshots. Each poll overwrites the prior snapshot for
the same (site, webhook, distinct, start, end, status, status_code, error, topic) tuple
via SQLite `INSERT OR REPLACE`, and overwrites the prior bucket rows that share the
same parent snapshot.

## SQLite DDL

```sql
-- Summary table: one row per (site, webhook, query window, filter combination).
CREATE TABLE IF NOT EXISTS site_webhook_deliveries_count_summary (
    site_id         TEXT     NOT NULL,
    webhook_id      TEXT     NOT NULL,
    distinct        TEXT     NOT NULL,
    start           INTEGER  NOT NULL,
    end             INTEGER  NOT NULL,
    status          TEXT     NOT NULL DEFAULT '',
    status_code     INTEGER  NOT NULL DEFAULT -1,
    error           TEXT     NOT NULL DEFAULT '',
    topic           TEXT     NOT NULL DEFAULT '',
    limit           INTEGER,
    total           INTEGER,
    bucket_count    INTEGER,
    duration        TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (site_id, webhook_id, distinct, start, end,
                 status, status_code, error, topic)
);

CREATE INDEX IF NOT EXISTS idx_webhook_count_summary_topic
    ON site_webhook_deliveries_count_summary (topic);

CREATE INDEX IF NOT EXISTS idx_webhook_count_summary_window
    ON site_webhook_deliveries_count_summary (start, end);

-- Bucket table: zero-or-more rows per parent summary snapshot.
CREATE TABLE IF NOT EXISTS site_webhook_deliveries_count_buckets (
    site_id         TEXT     NOT NULL,
    webhook_id      TEXT     NOT NULL,
    distinct        TEXT     NOT NULL,
    start           INTEGER  NOT NULL,
    end             INTEGER  NOT NULL,
    bucket_value    TEXT     NOT NULL,
    count           INTEGER  NOT NULL,
    extra_fields    TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (site_id, webhook_id, distinct, start, end, bucket_value),
    FOREIGN KEY (site_id, webhook_id, distinct, start, end)
        REFERENCES site_webhook_deliveries_count_summary
                   (site_id, webhook_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_webhook_count_buckets_count
    ON site_webhook_deliveries_count_buckets (count);

CREATE INDEX IF NOT EXISTS idx_webhook_count_buckets_value
    ON site_webhook_deliveries_count_buckets (bucket_value);
```

Note: SQLite reserves the words `limit`, `end`, `start`, and `distinct`. They are valid
column identifiers as bare words in `CREATE TABLE` because SQLite is lenient, but every
SELECT/INSERT against them must double-quote: `SELECT "limit", "end" FROM ...`.
`DataExporter.write_with_format_selection()` already handles this for known reserved
words. The DDL above is the canonical form; the DataExporter emits the equivalent
statement on first write per backend.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert into the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (site, webhook, query window, filter combination).
    'countSiteWebhooksDeliveries': {                                              # operationId from OpenAPI
        'type': 'composite_pk',                                                   # composite of business fields
        'primary_key': [                                                          # stable identifier for one snapshot
            'site_id', 'webhook_id', 'distinct',                                  # query target + bucket field
            'start', 'end',                                                       # window
            'status', 'status_code', 'error', 'topic',                            # filter knobs (echoed back)
        ],
        'indexes': ['topic', 'start', 'end'],                                     # common query filters
        'table': 'site_webhook_deliveries_count_summary',                         # target SQLite table
    },

    # Per-bucket rows produced from the API results[] array.
    'countSiteWebhooksDeliveriesBuckets': {                                       # MistHelper-internal sub-table key
        'type': 'composite_pk',                                                   # composite of parent FK + bucket value
        'primary_key': [                                                          # uniquely identifies a single bucket
            'site_id', 'webhook_id', 'distinct',
            'start', 'end',
            'bucket_value',
        ],
        'indexes': ['count', 'bucket_value'],                                     # fast lookup by magnitude or label
        'table': 'site_webhook_deliveries_count_buckets',                         # target SQLite table
    },
}
```

The `countSiteWebhooksDeliveriesBuckets` key is a MistHelper-internal identifier (the
Mist API has no operationId for the inner array). This pattern mirrors the reference
plan (spec 500), which uses the same split-key convention for endpoints whose response
contains a nested array.
