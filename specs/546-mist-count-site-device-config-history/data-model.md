# Phase 1 Data Model: countSiteDeviceConfigHistory

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_devices_config_history_count.md`
(200 OK body).

## Entities

The endpoint returns a single JSON object describing an aggregated count of
device-config-history records for a site, grouped by a caller-selected
distinct field. MistHelper splits this into two logical entities for clean
multi-backend persistence.

### Entity 1: `ConfigHistoryCountSummary`

One row per `(site, distinct_field, window_start, window_end, polled_at_utc)`.
This captures the query parameters echoed back by the API plus the top-level
counts.

| Field            | Type     | Source                    | PK? | FK?            | Notes |
|------------------|----------|---------------------------|-----|----------------|-------|
| `site_id`        | TEXT     | MistHelper context        | YES | sites.id       | UUID supplied by user; injected before write (API does not echo it in the body). |
| `distinct_field` | TEXT     | API `distinct`            | YES | --             | The grouping key the user requested (e.g., `mac`). |
| `window_start`   | INTEGER  | API `start`               | YES | --             | Epoch seconds; lower bound of the time window resolved by the API. |
| `window_end`     | INTEGER  | API `end`                 | YES | --             | Epoch seconds; upper bound of the time window resolved by the API. |
| `polled_at_utc`  | TEXT     | MistHelper clock          | YES | --             | ISO8601 UTC timestamp of the poll. Preserves history across repeated runs. |
| `limit_param`    | INTEGER  | API `limit`               | --  | --             | Echo of the `limit` query parameter (default 100). |
| `total`          | INTEGER  | API `total`               | --  | --             | Total distinct values matched by the query (may exceed `limit_param`). |
| `result_count`   | INTEGER  | len(API `results`)        | --  | --             | Convenience -- number of result rows actually returned. |
| `mac_filter`     | TEXT     | MistHelper context        | --  | --             | Echo of the optional `mac` filter the user supplied; empty when omitted. |
| `duration_param` | TEXT     | MistHelper context        | --  | --             | Echo of the optional `duration` query parameter the user supplied. |

### Entity 2: `ConfigHistoryCountResult`

Zero-or-more rows per summary. Source: each element of the API `results`
array. Each result has a required `count` plus arbitrary string-valued
additional properties keyed by the distinct field name (e.g., when
`distinct=mac`, each result is `{"mac": "aabbccddeeff", "count": 42}`).
MistHelper flattens the dynamic distinct-field key into a generic
`distinct_value` column for stable schema across runs.

| Field            | Type     | Source                    | PK? | FK?                                                       | Notes |
|------------------|----------|---------------------------|-----|-----------------------------------------------------------|-------|
| `site_id`        | TEXT     | MistHelper context        | YES | site_device_config_history_count_summary.site_id          | UUID. |
| `distinct_field` | TEXT     | API `distinct`            | YES | site_device_config_history_count_summary.distinct_field   | Joins to summary. |
| `distinct_value` | TEXT     | API results[].<distinct>  | YES | --                                                        | The dynamic value associated with the distinct field (e.g., a MAC). |
| `window_start`   | INTEGER  | API `start`               | YES | site_device_config_history_count_summary.window_start     | Joins to summary. |
| `window_end`     | INTEGER  | API `end`                 | YES | site_device_config_history_count_summary.window_end       | Joins to summary. |
| `polled_at_utc`  | TEXT     | MistHelper clock          | YES | site_device_config_history_count_summary.polled_at_utc    | Joins to summary. |
| `count`          | INTEGER  | API results[].count       | --  | --                                                        | Number of config history records in this bucket. |
| `extra_fields_json` | TEXT  | API results[] extras      | --  | --                                                        | JSON-encoded dict of any *additional* string properties on the result item beyond the declared distinct field. Lossless capture for forward compatibility. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying device config history on
the Mist side grows monotonically, but MistHelper does not drive or model
those transitions; it merely captures snapshots. Each poll inserts a new
`(site_id, distinct_field, window_start, window_end, polled_at_utc)` summary
row plus its result rows. Repeating a poll with an identical clock value
(unlikely outside scripted testing) upserts via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (site, query params, poll moment).
CREATE TABLE IF NOT EXISTS site_device_config_history_count_summary (
    site_id           TEXT     NOT NULL,
    distinct_field    TEXT     NOT NULL,
    window_start      INTEGER  NOT NULL,
    window_end        INTEGER  NOT NULL,
    polled_at_utc     TEXT     NOT NULL,
    limit_param       INTEGER,
    total             INTEGER,
    result_count      INTEGER,
    mac_filter        TEXT,
    duration_param    TEXT,
    PRIMARY KEY (site_id, distinct_field, window_start, window_end, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_chc_summary_site
    ON site_device_config_history_count_summary (site_id);
CREATE INDEX IF NOT EXISTS idx_chc_summary_distinct
    ON site_device_config_history_count_summary (distinct_field);

-- Results table: zero-or-more rows per summary.
CREATE TABLE IF NOT EXISTS site_device_config_history_count_results (
    site_id           TEXT     NOT NULL,
    distinct_field    TEXT     NOT NULL,
    distinct_value    TEXT     NOT NULL,
    window_start      INTEGER  NOT NULL,
    window_end        INTEGER  NOT NULL,
    polled_at_utc     TEXT     NOT NULL,
    count             INTEGER  NOT NULL,
    extra_fields_json TEXT,
    PRIMARY KEY (site_id, distinct_field, distinct_value, window_start, window_end, polled_at_utc),
    FOREIGN KEY (site_id, distinct_field, window_start, window_end, polled_at_utc)
        REFERENCES site_device_config_history_count_summary
            (site_id, distinct_field, window_start, window_end, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_chc_results_value
    ON site_device_config_history_count_results (distinct_value);
CREATE INDEX IF NOT EXISTS idx_chc_results_count
    ON site_device_config_history_count_results (count);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (site, query params, poll moment) for the count
    # aggregation returned by GET /api/v1/sites/{site_id}/devices/config_history/count.
    'countSiteDeviceConfigHistory': {                                              # operationId from OpenAPI
        'type': 'composite_pk',                                                    # composite of business identifiers + poll clock
        'primary_key': [                                                           # ordered key columns
            'site_id',                                                             # site scope (injected from user input)
            'distinct_field',                                                      # which field the API grouped by
            'window_start',                                                        # echoed lower bound of the time window
            'window_end',                                                          # echoed upper bound of the time window
            'polled_at_utc',                                                       # local poll timestamp -- preserves history
        ],
        'indexes': ['site_id', 'distinct_field'],                                  # fast filter by site or grouping field
        'table': 'site_device_config_history_count_summary',                       # target SQLite table for summary rows
    },

    # Per-bucket result rows (one row per element of results[] in the
    # response). MistHelper-internal sub-table key (no Mist operationId).
    'countSiteDeviceConfigHistoryResults': {                                       # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                    # composite of summary FK + distinct_value
        'primary_key': [                                                           # ordered key columns
            'site_id',                                                             # site scope
            'distinct_field',                                                      # which field the API grouped by
            'distinct_value',                                                      # the bucket value (e.g., a device MAC)
            'window_start',                                                        # joins to summary
            'window_end',                                                          # joins to summary
            'polled_at_utc',                                                       # joins to summary
        ],
        'indexes': ['distinct_value', 'count'],                                    # common query patterns
        'table': 'site_device_config_history_count_results',                       # target SQLite table for result rows
    },
}
```

The `countSiteDeviceConfigHistoryResults` key is a MistHelper-internal
identifier (the Mist API has no operationId for it -- it is a flattened
sub-array of the parent response). This mirrors the established
two-strategy pattern used for other endpoints whose body contains a primary
object plus a nested array (see the reference plan for
`GetOrgLicenseAsyncClaimStatus`).
