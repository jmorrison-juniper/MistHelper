# Phase 1 Data Model: countSiteWirelessClients

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_clients_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing a count snapshot of wireless
clients at a site, grouped by a caller-selected distinct attribute. MistHelper splits
this into two logical entities for clean multi-backend persistence.

### Entity 1: `WirelessClientCountSummary`

One row per (site, distinct field, time window) count query.

| Field            | Type     | Source                  | PK? | FK?           | Notes |
|------------------|----------|-------------------------|-----|---------------|-------|
| `site_id`        | TEXT     | MistHelper context      | YES | sites.id      | UUID supplied by user; injected before write. |
| `distinct`       | TEXT     | API `distinct`          | YES | --            | Group-by field name actually used by the server (`ssid`, `ap`, `ip`, `vlan`, `hostname`, `os`, `model`, or `device`). |
| `window_start`   | INTEGER  | API `start`             | YES | --            | Epoch seconds at the start of the count window. Echoed by the API even when the caller passed a relative string. |
| `window_end`     | INTEGER  | API `end`               | YES | --            | Epoch seconds at the end of the count window. |
| `total`          | INTEGER  | API `total`             | --  | --            | Total distinct values matched (may exceed the `results` array length when `total > limit`). |
| `limit_used`     | INTEGER  | API `limit`             | --  | --            | Server-side cap on the `results` array length for this snapshot. |
| `result_count`   | INTEGER  | len(API `results`)      | --  | --            | Convenience count of rows actually returned in `results`. |
| `polled_at_utc`  | TEXT     | MistHelper clock        | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `WirelessClientCountResult`

Zero-or-more rows per (site, distinct field, time window). Source: each element of the
API `results` array.

| Field             | Type    | Source                                   | PK? | FK?                                                       | Notes |
|-------------------|---------|------------------------------------------|-----|-----------------------------------------------------------|-------|
| `site_id`         | TEXT    | MistHelper context                       | YES | site_wireless_client_count_summary.site_id              | UUID. |
| `distinct`        | TEXT    | API `distinct`                           | YES | site_wireless_client_count_summary.distinct             | Echoes the summary row's group-by field. |
| `window_start`    | INTEGER | API `start`                              | YES | site_wireless_client_count_summary.window_start         | Joins to summary. |
| `window_end`      | INTEGER | API `end`                                | YES | site_wireless_client_count_summary.window_end           | Joins to summary. |
| `distinct_value`  | TEXT    | `results[].{<distinct field>}`           | YES | --                                                        | The per-row group-by value. The Mist schema uses `additionalProperties: string` for this slot, so the field name varies per query (`ssid`, `hostname`, etc.) but the value is always a string. MistHelper normalizes it to the column name `distinct_value` for SQL compatibility. |
| `count`           | INTEGER | API `results[].count`                    | --  | --                                                        | Number of wireless clients with this distinct value during the window. |
| `polled_at_utc`   | TEXT    | MistHelper clock                         | --  | --                                                        | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *clients* at the Mist site come and
go, but MistHelper does not drive or model those transitions; it merely captures count
snapshots. Each poll overwrites the prior snapshot for the same
(site_id, distinct, window_start, window_end) tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (site, distinct field, time window) count query.
CREATE TABLE IF NOT EXISTS site_wireless_client_count_summary (
    site_id              TEXT     NOT NULL,
    distinct             TEXT     NOT NULL,
    window_start         INTEGER  NOT NULL,
    window_end           INTEGER  NOT NULL,
    total                INTEGER,
    limit_used           INTEGER,
    result_count         INTEGER,
    polled_at_utc        TEXT,
    PRIMARY KEY (site_id, distinct, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_wc_count_summary_distinct
    ON site_wireless_client_count_summary (distinct);

-- Results table: zero-or-more rows per (site, distinct field, window, distinct value).
CREATE TABLE IF NOT EXISTS site_wireless_client_count_results (
    site_id              TEXT     NOT NULL,
    distinct             TEXT     NOT NULL,
    window_start         INTEGER  NOT NULL,
    window_end           INTEGER  NOT NULL,
    distinct_value       TEXT     NOT NULL,
    count                INTEGER,
    polled_at_utc        TEXT,
    PRIMARY KEY (site_id, distinct, window_start, window_end, distinct_value),
    FOREIGN KEY (site_id, distinct, window_start, window_end)
        REFERENCES site_wireless_client_count_summary
            (site_id, distinct, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_wc_count_results_value
    ON site_wireless_client_count_results (distinct_value);

CREATE INDEX IF NOT EXISTS idx_wc_count_results_count
    ON site_wireless_client_count_results (count);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL
directly. The reserved SQL word `distinct` is a valid SQLite column identifier (it is
only reserved in `SELECT` syntax position), but consumers writing ad hoc queries must
quote it: `SELECT "distinct", total FROM site_wireless_client_count_summary;`.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (site, distinct, time window) count query.
    'countSiteWirelessClients': {                                                   # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': [                                                            # stable across polls of same query
            'site_id', 'distinct', 'window_start', 'window_end',
        ],
        'indexes': ['distinct'],                                                    # fast filter by group-by field
        'table': 'site_wireless_client_count_summary',                              # target SQLite table for summary rows
    },

    # Per-distinct-value detail rows from the results[] array.
    'countSiteWirelessClientsResults': {                                            # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of summary FK + distinct_value
        'primary_key': [                                                            # uniquely identifies one count datum
            'site_id', 'distinct', 'window_start', 'window_end',
            'distinct_value',
        ],
        'indexes': ['distinct_value', 'count'],                                     # fast lookup by group-by value or count
        'table': 'site_wireless_client_count_results',                              # target SQLite table for detail rows
    },
}
```

The `countSiteWirelessClientsResults` key is a MistHelper-internal identifier (the Mist
API has no operationId for it -- it is a flattened sub-array of the parent response).
This pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays (precedent: `getOrgLicenseAsyncClaimStatusDetails`).
