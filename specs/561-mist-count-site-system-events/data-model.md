# Phase 1 Data Model: countSiteSystemEvents

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_events_system_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing a count aggregation of
site-scoped system events grouped by a caller-supplied distinct attribute. MistHelper
flattens the nested `results[]` array into one row per distinct-value bucket plus
captures the query envelope as columns on each row, so a single tabular entity is
sufficient for clean multi-backend persistence.

### Entity 1: `SystemEventCountBucket`

One row per (site, distinct attribute, time window, distinct value) tuple.

| Field                | Type     | Source                       | PK? | FK?            | Notes |
|----------------------|----------|------------------------------|-----|----------------|-------|
| `site_id`            | TEXT     | MistHelper context           | YES | sites.id       | UUID supplied by user; injected before write -- API does not echo it. |
| `distinct_attribute` | TEXT     | API `distinct`               | YES | --             | Attribute name the count is grouped by (e.g., `type`, `device_type`, `model`). |
| `window_start`       | INTEGER  | API `start`                  | YES | --             | Epoch seconds, start of the count window. |
| `window_end`         | INTEGER  | API `end`                    | YES | --             | Epoch seconds, end of the count window. |
| `distinct_value`     | TEXT     | API `results[].<distinct>`   | YES | --             | The bucket key. Extracted from the dynamic property whose name equals `distinct_attribute`. |
| `count`              | INTEGER  | API `results[].count`        | --  | --             | Number of events in this bucket. Required by API schema. |
| `limit_applied`      | INTEGER  | API `limit`                  | --  | --             | Bucket cap that was applied (default 100). Audit field. |
| `window_total`       | INTEGER  | API `total`                  | --  | --             | Total events counted across all buckets in this window. Audit field, denormalized intentionally so a single-row query can show the bucket's share of total. |
| `bucket_extra_json`  | TEXT     | API `results[].*` minus key  | --  | --             | JSON-encoded blob of any additional string properties present on the bucket beyond `count` and the distinct key, in case Mist returns extra context (the OpenAPI schema declares `additionalProperties: string`). Empty `{}` when none. |
| `polled_at_utc`      | TEXT     | MistHelper clock             | --  | --             | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *events* on the Mist side are
themselves immutable once recorded, but late-arriving events can shift bucket counts
within an open window. MistHelper does not model that movement; it captures snapshots.
Each poll over the same (site, distinct_attribute, window_start, window_end,
distinct_value) tuple overwrites the prior row via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per bucket of a counted system-events query.
CREATE TABLE IF NOT EXISTS site_system_events_count (
    site_id              TEXT     NOT NULL,
    distinct_attribute   TEXT     NOT NULL,
    window_start         INTEGER  NOT NULL,
    window_end           INTEGER  NOT NULL,
    distinct_value       TEXT     NOT NULL,
    count                INTEGER  NOT NULL,
    limit_applied        INTEGER,
    window_total         INTEGER,
    bucket_extra_json    TEXT,
    polled_at_utc        TEXT,
    PRIMARY KEY (
        site_id,
        distinct_attribute,
        window_start,
        window_end,
        distinct_value
    )
);

CREATE INDEX IF NOT EXISTS idx_site_system_events_count_site
    ON site_system_events_count (site_id);

CREATE INDEX IF NOT EXISTS idx_site_system_events_count_attr_value
    ON site_system_events_count (distinct_attribute, distinct_value);
```

`DataExporter.write_with_format_selection()` emits the equivalent DDL on first write
per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert,
Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (one insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per bucket of a site system-events count query.
    'countSiteSystemEvents': {                                                      # operationId from OpenAPI
        'type': 'composite_pk',                                                     # composite of business-key fields
        'primary_key': [                                                            # five-tuple uniquely identifies a bucket
            'site_id',                                                              # injected from MistHelper context
            'distinct_attribute',                                                   # echoes API `distinct`
            'window_start',                                                         # echoes API `start` epoch
            'window_end',                                                           # echoes API `end` epoch
            'distinct_value',                                                       # bucket key extracted by flatten
        ],
        'indexes': [                                                                # secondary indexes for common queries
            'site_id',                                                              # filter all buckets for a site
            'distinct_attribute',                                                   # filter by pivot attribute
        ],
        'table': 'site_system_events_count',                                        # target SQLite table
    },
}
```

The single-entry registration is sufficient because the response has no nested arrays
beyond `results[]`, which is already the row-producing dimension of the table. No
MistHelper-internal sub-table id is needed for this endpoint.
