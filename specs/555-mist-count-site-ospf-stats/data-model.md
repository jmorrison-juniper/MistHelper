# Phase 1 Data Model: countSiteOspfStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_stats_ospf_peers_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object whose `results` array is the only payload
that varies per call. MistHelper models this as **one** logical entity -- the
flattened distinct-count bucket. The other top-level fields (`distinct`, `start`,
`end`, `limit`, `total`) are echoed back into every row as context so the SQLite
table is self-contained and a junior NOC engineer can query without joining.

### Entity 1: `SiteOspfPeerCountBucket`

One row per distinct bucket returned in the `results[]` array, per (org, site,
distinct attribute, time window).

| Field                | Type    | Source                                       | PK? | FK?                  | Notes |
|----------------------|---------|----------------------------------------------|-----|----------------------|-------|
| `org_id`             | TEXT    | MistHelper session context                   | YES | sites.org_id         | UUID; injected before write because the body does not include it. |
| `site_id`            | TEXT    | MistHelper context (user-supplied path param)| YES | sites.id             | UUID of the queried site. |
| `distinct_attribute` | TEXT    | API top-level `distinct` (or `default`)      | YES | --                   | Group-by attribute used for this query. Stored as the literal `default` when the user omitted the prompt. |
| `bucket_key`         | TEXT    | bucket[distinct_attribute] (or empty string) | YES | --                   | The actual attribute value for this bucket (for example a neighbor router-id when distinct=neighbor). Empty string for buckets where the attribute is null. |
| `window_start`       | INTEGER | API top-level `start` (epoch seconds)        | YES | --                   | Resolved to absolute epoch seconds client-side before the call so the PK is stable. |
| `window_end`         | INTEGER | API top-level `end` (epoch seconds)          | YES | --                   | Same as above. |
| `count`              | INTEGER | bucket `count`                               | --  | --                   | Aggregate count for this bucket. Required by API schema. |
| `total_buckets`      | INTEGER | API top-level `total`                        | --  | --                   | Total distinct buckets across all pages for the query. Echoed into every row. |
| `page_limit`         | INTEGER | API top-level `limit`                        | --  | --                   | Page size used for the API call (echoes the request). |
| `bucket_attributes_json` | TEXT | bucket extra string keys serialized to JSON| --  | --                   | When Mist returns additional string attributes on a bucket beyond `count` and the distinct key (per the `additionalProperties: {type: string}` schema), they are captured here for completeness without expanding the column list. |
| `polled_at_utc`      | TEXT    | MistHelper clock (datetime.now(UTC))         | --  | --                   | ISO-8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying OSPF peer state on the Mist side
transitions through neighbor states (Down / Init / 2-Way / ExStart / Exchange /
Loading / Full per RFC 2328), but MistHelper does not drive or model those
transitions; it merely captures the aggregate count per state per poll. Each poll of
the same (org, site, distinct_attribute, bucket_key, window_start, window_end) tuple
overwrites the prior snapshot via SQLite `INSERT OR REPLACE`. Different windows
accumulate as separate rows -- intentional, so a NOC engineer can compare last-hour
versus last-day counts without losing either snapshot.

## SQLite DDL

```sql
-- One row per distinct OSPF peer count bucket per (org, site, distinct, window).
CREATE TABLE IF NOT EXISTS site_ospf_peers_count (
    org_id                  TEXT     NOT NULL,
    site_id                 TEXT     NOT NULL,
    distinct_attribute      TEXT     NOT NULL,
    bucket_key              TEXT     NOT NULL,
    window_start            INTEGER  NOT NULL,
    window_end              INTEGER  NOT NULL,
    count                   INTEGER  NOT NULL,
    total_buckets           INTEGER,
    page_limit              INTEGER,
    bucket_attributes_json  TEXT,
    polled_at_utc           TEXT,
    PRIMARY KEY (org_id, site_id, distinct_attribute, bucket_key, window_start, window_end)
);

-- Fast filter by org/site (most common operational query).
CREATE INDEX IF NOT EXISTS idx_site_ospf_count_org_site
    ON site_ospf_peers_count (org_id, site_id);

-- Fast filter by distinct attribute (compare counts for the same site over time).
CREATE INDEX IF NOT EXISTS idx_site_ospf_count_distinct
    ON site_ospf_peers_count (site_id, distinct_attribute, window_end);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert with a unique index over the PK tuple, Redis via key
namespacing that mirrors the PK tuple). MistHelper does not run the DDL directly --
the DataExporter is the single point of database contact per Principle II.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py`. This is a single insert in the dict literal -- no
structural change to the dictionary itself.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Aggregated OSPF peer counts per (org, site, distinct attribute, bucket, window).
    'countSiteOspfStats': {                                                           # operationId from OpenAPI
        'type': 'composite_pk',                                                       # PK is composite of business fields
        'primary_key': [                                                              # full composite PK tuple
            'org_id',                                                                 # injected from active mistapi session
            'site_id',                                                                # user-supplied path parameter
            'distinct_attribute',                                                     # the group-by attribute (or literal 'default')
            'bucket_key',                                                             # the actual attribute value in this bucket
            'window_start',                                                           # resolved epoch seconds, stable across re-poll
            'window_end',                                                             # resolved epoch seconds, stable across re-poll
        ],
        'indexes': [                                                                  # query-time secondary indexes
            'org_id',                                                                 # filter by org (multi-tenant deployments)
            'site_id',                                                                # filter by site (single-site review)
            'distinct_attribute',                                                     # compare same site across attributes
        ],
        'table': 'site_ospf_peers_count',                                             # target SQLite / ArangoDB collection
    },
}
```

The single PK strategy entry covers both the CSV writer (which uses the PK fields to
deduplicate on append) and the SQLite / ArangoDB writers (which use
`INSERT OR REPLACE` on the same tuple). No sub-table or auxiliary entry is needed
because the response is a single flat list of buckets; the nested object inside each
bucket is captured verbatim in `bucket_attributes_json` rather than exploded into
extra tables.
