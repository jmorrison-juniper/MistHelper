# Phase 1 Data Model: countSiteWirelessClientSessions

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_clients_sessions_count.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing an aggregated count of
wireless client sessions at a site, grouped by a user-selected distinct
attribute over a time window. MistHelper splits this into two logical entities
for clean multi-backend persistence.

### Entity 1: `SessionCountSummary`

One row per (site, distinct_field, start, end) tuple.

| Field           | Type    | Source                  | PK? | FK?            | Notes |
|-----------------|---------|-------------------------|-----|----------------|-------|
| `site_id`       | TEXT    | MistHelper context      | YES | sites.id       | UUID supplied by user; injected before write. |
| `distinct_field`| TEXT    | API `distinct`          | YES | --             | The grouping attribute echoed by the API (`ssid`, `ap`, `band`, `client_family`, `client_manufacture`, `client_model`, `client_os`, `wlan_id`). |
| `start`         | INTEGER | API `start`             | YES | --             | Epoch seconds at start of the count window. |
| `end`           | INTEGER | API `end`               | YES | --             | Epoch seconds at end of the count window. |
| `limit`         | INTEGER | API `limit`             | --  | --             | Max rows the API was asked to return in `results`. |
| `total`         | INTEGER | API `total`             | --  | --             | Total number of unique values seen for the distinct attribute over the window. |
| `result_count`  | INTEGER | len(API `results`)      | --  | --             | Convenience count of the `results` array length (may be <= `total` when `limit` truncates). |
| `duration_str`  | TEXT    | MistHelper input        | --  | --             | The `duration` value the user supplied (`1d`, `7d`, etc.) for audit traceability. |
| `polled_at_utc` | TEXT    | MistHelper clock        | --  | --             | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `SessionCountResult`

Zero or more rows per (site, distinct_field, start, end, distinct_value). One
row per element of the API `results` array.

| Field            | Type    | Source                    | PK? | FK?                                                         | Notes |
|------------------|---------|---------------------------|-----|-------------------------------------------------------------|-------|
| `site_id`        | TEXT    | MistHelper context        | YES | session_count_summary.site_id                              | UUID. |
| `distinct_field` | TEXT    | API `distinct`            | YES | session_count_summary.distinct_field                       | Joins to summary. |
| `start`          | INTEGER | API `start`               | YES | session_count_summary.start                                | Joins to summary. |
| `end`            | INTEGER | API `end`                 | YES | session_count_summary.end                                  | Joins to summary. |
| `distinct_value` | TEXT    | API `results[].<distinct>`| YES | --                                                          | The observed grouping value (e.g. `Guest-WiFi` when `distinct=ssid`, an AP MAC when `distinct=ap`). Extracted from the dynamic key in each result object. |
| `count`          | INTEGER | API `results[].count`     | --  | --                                                          | Number of wireless sessions observed for this distinct_value within the window. |
| `polled_at_utc`  | TEXT    | MistHelper clock          | --  | --                                                          | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only aggregate endpoint. The underlying *sessions* on the
Mist side are an ever-growing log, but MistHelper does not drive or model
session state; it merely captures count snapshots. Each poll overwrites the
prior snapshot for the same
(site_id, distinct_field, start, end[, distinct_value]) tuple via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (site, distinct grouping, time window).
CREATE TABLE IF NOT EXISTS site_wireless_session_count_summary (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    start            INTEGER  NOT NULL,
    end              INTEGER  NOT NULL,
    limit            INTEGER,
    total            INTEGER,
    result_count     INTEGER,
    duration_str     TEXT,
    polled_at_utc    TEXT,
    PRIMARY KEY (site_id, distinct_field, start, end)
);

CREATE INDEX IF NOT EXISTS idx_session_count_summary_field
    ON site_wireless_session_count_summary (distinct_field);

-- Results table: zero-or-more rows per summary row.
CREATE TABLE IF NOT EXISTS site_wireless_session_count_results (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    start            INTEGER  NOT NULL,
    end              INTEGER  NOT NULL,
    distinct_value   TEXT     NOT NULL,
    count            INTEGER,
    polled_at_utc    TEXT,
    PRIMARY KEY (site_id, distinct_field, start, end, distinct_value),
    FOREIGN KEY (site_id, distinct_field, start, end)
        REFERENCES site_wireless_session_count_summary(site_id, distinct_field, start, end)
);

CREATE INDEX IF NOT EXISTS idx_session_count_results_value
    ON site_wireless_session_count_results (distinct_value);

CREATE INDEX IF NOT EXISTS idx_session_count_results_count
    ON site_wireless_session_count_results (count);
```

Note: `limit` and `end` are SQL reserved words in some dialects. SQLite tolerates
them as unquoted column names but, when these tables are mirrored into ArangoDB
or any future SQL backend, the DataExporter quoting layer wraps the identifiers
defensively. MistHelper does not run the DDL directly --
`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing).

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (two single
inserts into the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (site, distinct grouping, time window).
    'countSiteWirelessClientSessions': {                                            # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['site_id', 'distinct_field', 'start', 'end'],               # uniquely identifies a count window
        'indexes': ['distinct_field'],                                              # fast filter by grouping attribute
        'table': 'site_wireless_session_count_summary',                             # target SQLite table for summary rows
    },

    # Per-distinct-value result rows produced from the API `results` array.
    'countSiteWirelessClientSessionsResults': {                                     # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of summary FK + distinct_value
        'primary_key': ['site_id', 'distinct_field', 'start', 'end',                # joins back to the summary row
                        'distinct_value'],                                          # plus one row per observed value
        'indexes': ['distinct_value', 'count'],                                     # fast lookup by value or by count
        'table': 'site_wireless_session_count_results',                             # target SQLite table for result rows
    },
}
```

The `countSiteWirelessClientSessionsResults` key is a MistHelper-internal
identifier (the Mist API has no operationId for it -- it is a flattened
sub-array of the parent response). This pattern matches how MistHelper already
splits other endpoints whose response contains nested arrays of equal grain
(e.g. `getOrgLicenseAsyncClaimStatusDetails` from spec 500).
