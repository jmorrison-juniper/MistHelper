# Phase 1 Data Model: countSiteSwOrGwPorts

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_stats_ports_count.md` (200 OK body, lines
66-124).

## Entities

The endpoint returns a single JSON envelope describing counts of switch/gateway port
records at a site, optionally bucketed by a `distinct` field. MistHelper splits the
envelope into two logical entities for clean multi-backend persistence: one row for
the envelope itself and one row per bucket in the `results[]` array.

### Entity 1: `SitePortCountSummary`

One row per (site, distinct dimension, time window). Captures the envelope fields
returned alongside the bucket list.

| Field             | Type     | Source                | PK? | FK?               | Notes |
|-------------------|----------|-----------------------|-----|-------------------|-------|
| `site_id`         | TEXT     | MistHelper context    | YES | sites.id          | UUID supplied by user; injected before write. |
| `distinct_field`  | TEXT     | API `distinct`        | YES | --                | Echo of the user-supplied `distinct` query parameter (for example `up`, `speed`, `poe_on`). |
| `window_start`    | INTEGER  | API `start`           | YES | --                | Epoch seconds. Start of the count window. |
| `window_end`      | INTEGER  | API `end`             | YES | --                | Epoch seconds. End of the count window. |
| `result_limit`    | INTEGER  | API `limit`           | --  | --                | Echo of the `limit` query parameter (default 100). |
| `total`           | INTEGER  | API `total`           | --  | --                | Total number of distinct buckets across all pages. |
| `bucket_count`    | INTEGER  | `len(API results)`    | --  | --                | Convenience count of buckets actually returned on this page. |
| `polled_at_utc`   | TEXT     | MistHelper clock      | --  | --                | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `SitePortCountResult`

Zero or more rows per envelope. Each element of the API `results[]` array is one
`count_result` object containing `count` plus additional string properties that name
the bucket. MistHelper materializes those additional properties into a single
`bucket_label` column (concatenated `key=value;key=value` if more than one extra
property is present) so the schema stays flat across all possible distinct values.

| Field            | Type    | Source                          | PK? | FK?                                                | Notes |
|------------------|---------|---------------------------------|-----|----------------------------------------------------|-------|
| `site_id`        | TEXT    | MistHelper context              | YES | site_port_count_summary.site_id                    | UUID. |
| `distinct_field` | TEXT    | API envelope `distinct`         | YES | site_port_count_summary.distinct_field             | Joins to summary. |
| `window_start`   | INTEGER | API envelope `start`            | YES | site_port_count_summary.window_start               | Joins to summary. |
| `window_end`     | INTEGER | API envelope `end`              | YES | site_port_count_summary.window_end                 | Joins to summary. |
| `bucket_label`   | TEXT    | results[i] additional props     | YES | --                                                 | Stringified bucket identifier (e.g. `"true"`, `"1000"`, `"Kumar-Acc-SW.mist.local"`). |
| `bucket_count`   | INTEGER | results[i].count                | --  | --                                                 | The count for this bucket. |
| `bucket_extras`  | TEXT    | results[i] (json-encoded)       | --  | --                                                 | Optional. JSON-encoded original additional-property dict, preserved for audit when a bucket carries multiple labels. |
| `polled_at_utc`  | TEXT    | MistHelper clock                | --  | --                                                 | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying port stats on the Mist side
mutate continuously, but MistHelper does not drive or model those transitions; it
merely captures count snapshots. Each poll overwrites the prior snapshot for the same
(site, distinct, window) tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Envelope table: one row per (site, distinct dimension, time window).
CREATE TABLE IF NOT EXISTS site_port_count_summary (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    window_start     INTEGER  NOT NULL,
    window_end       INTEGER  NOT NULL,
    result_limit     INTEGER,
    total            INTEGER,
    bucket_count     INTEGER,
    polled_at_utc    TEXT,
    PRIMARY KEY (site_id, distinct_field, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_site_port_count_summary_site
    ON site_port_count_summary (site_id);
CREATE INDEX IF NOT EXISTS idx_site_port_count_summary_distinct
    ON site_port_count_summary (distinct_field);

-- Bucket table: zero-or-more rows per envelope.
CREATE TABLE IF NOT EXISTS site_port_count_results (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    window_start     INTEGER  NOT NULL,
    window_end       INTEGER  NOT NULL,
    bucket_label     TEXT     NOT NULL,
    bucket_count     INTEGER,
    bucket_extras    TEXT,
    polled_at_utc    TEXT,
    PRIMARY KEY (site_id, distinct_field, window_start, window_end, bucket_label),
    FOREIGN KEY (site_id, distinct_field, window_start, window_end)
        REFERENCES site_port_count_summary(site_id, distinct_field, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_site_port_count_results_label
    ON site_port_count_results (bucket_label);
CREATE INDEX IF NOT EXISTS idx_site_port_count_results_count
    ON site_port_count_results (bucket_count);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal -- no structural
change):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Envelope row per (site, distinct dimension, time window).
    'countSiteSwOrGwPorts': {                                                       # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': [                                                            # stable identifier per poll
            'site_id',                                                              # injected by MistHelper
            'distinct_field',                                                       # echoed from request, normalized
            'window_start',                                                         # epoch seconds from envelope
            'window_end',                                                           # epoch seconds from envelope
        ],
        'indexes': ['site_id', 'distinct_field'],                                   # fast filter by site or dimension
        'table': 'site_port_count_summary',                                         # target SQLite table for summary
    },

    # Bucket rows produced from the envelope's results[] array.
    'countSiteSwOrGwPortsResults': {                                                # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of envelope FK + bucket label
        'primary_key': [                                                            # uniquely identifies a bucket snapshot
            'site_id',
            'distinct_field',
            'window_start',
            'window_end',
            'bucket_label',
        ],
        'indexes': ['bucket_label', 'bucket_count'],                                # fast lookup and ordering by size
        'table': 'site_port_count_results',                                         # target SQLite table for bucket rows
    },
}
```

The `countSiteSwOrGwPortsResults` key is a MistHelper-internal identifier -- the Mist
API has no operationId for it because it is a flattened sub-array of the parent
response. This pattern matches how MistHelper already splits other envelope-with-array
endpoints (for example the claim-status summary/details pair in spec 500).
