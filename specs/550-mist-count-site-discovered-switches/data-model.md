# Phase 1 Data Model: countSiteDiscoveredSwitches

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_stats_discovered_switches_count.md`
(200 OK body).

## Entities

The endpoint returns a single JSON envelope describing the count of unmanaged switches
discovered at a site, optionally grouped by a `distinct` attribute. MistHelper splits
this into two logical entities for clean multi-backend persistence.

### Entity 1: `DiscoveredSwitchesCountSummary`

One row per (site, distinct attribute, time window) poll.

| Field            | Type    | Source                    | PK? | FK?            | Notes |
|------------------|---------|---------------------------|-----|----------------|-------|
| `site_id`        | TEXT    | MistHelper context        | YES | sites.id       | UUID supplied by user; injected before write. |
| `distinct`       | TEXT    | API `distinct`            | YES | --             | Echoed grouping attribute; normalized to `""` when ungrouped. |
| `start`          | INTEGER | API `start`               | YES | --             | Epoch seconds, start of the counted window. |
| `end`            | INTEGER | API `end`                 | YES | --             | Epoch seconds, end of the counted window. |
| `duration`       | TEXT    | MistHelper request param  | --  | --             | The duration string the caller sent (e.g. `1d`, `7d`). |
| `limit`          | INTEGER | API `limit`               | --  | --             | Echoed limit applied to the `results` array. |
| `total`          | INTEGER | API `total`               | --  | --             | Total count across all groups. |
| `group_count`    | INTEGER | len(API `results`)        | --  | --             | Convenience count of the `results` array length. |
| `polled_at_utc`  | TEXT    | MistHelper clock          | --  | --             | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `DiscoveredSwitchesCountGroup`

One row per element of the API `results` array. When the caller does not group
(`distinct` blank), the API returns a single result with `count = total` and no extra
properties; that row still lands here so the group table is always populated.

| Field            | Type    | Source                  | PK? | FK?                                                  | Notes |
|------------------|---------|-------------------------|-----|------------------------------------------------------|-------|
| `site_id`        | TEXT    | MistHelper context      | YES | discovered_switches_count_summary.site_id           | UUID. |
| `distinct`       | TEXT    | MistHelper context      | YES | discovered_switches_count_summary.distinct          | Echoed grouping attribute; normalized to `""` when ungrouped. |
| `start`          | INTEGER | API `start`             | YES | discovered_switches_count_summary.start             | Joins to summary window. |
| `end`            | INTEGER | API `end`               | YES | discovered_switches_count_summary.end               | Joins to summary window. |
| `group_value`    | TEXT    | API `results[].<distinct>` | YES | --                                                | Resolved value of the distinct attribute (e.g. `juniper`, `EX2300`); `""` when ungrouped. |
| `count`          | INTEGER | API `results[].count`   | --  | --                                                   | Per-group count. |
| `extra_attrs_json` | TEXT  | API `results[]` minus `count` and known fields | -- | --                              | Any additional string properties present on the group object, JSON-encoded for forward compatibility. |
| `polled_at_utc`  | TEXT    | MistHelper clock        | --  | --                                                   | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *site* state (how many switches are
discovered, which vendors are present) changes over time on the Mist side, but
MistHelper does not drive or model those transitions; it merely captures snapshots.
Each poll overwrites the prior snapshot for the same
`(site_id, distinct, start, end)` summary tuple and the same
`(site_id, distinct, start, end, group_value)` group tuple via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (site, distinct attribute, time window).
CREATE TABLE IF NOT EXISTS site_discovered_switches_count_summary (
    site_id        TEXT     NOT NULL,
    distinct       TEXT     NOT NULL,
    start          INTEGER  NOT NULL,
    end            INTEGER  NOT NULL,
    duration       TEXT,
    limit          INTEGER,
    total          INTEGER,
    group_count    INTEGER,
    polled_at_utc  TEXT,
    PRIMARY KEY (site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_dsc_summary_site
    ON site_discovered_switches_count_summary (site_id);

CREATE INDEX IF NOT EXISTS idx_dsc_summary_distinct
    ON site_discovered_switches_count_summary (distinct);

-- Groups table: one or more rows per (site, distinct, window, group_value).
CREATE TABLE IF NOT EXISTS site_discovered_switches_count_groups (
    site_id           TEXT     NOT NULL,
    distinct          TEXT     NOT NULL,
    start             INTEGER  NOT NULL,
    end               INTEGER  NOT NULL,
    group_value       TEXT     NOT NULL,
    count             INTEGER,
    extra_attrs_json  TEXT,
    polled_at_utc     TEXT,
    PRIMARY KEY (site_id, distinct, start, end, group_value),
    FOREIGN KEY (site_id, distinct, start, end)
        REFERENCES site_discovered_switches_count_summary(site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_dsc_groups_group_value
    ON site_discovered_switches_count_groups (group_value);
```

Note: the column names `start`, `end`, `distinct`, and `limit` are SQLite reserved-ish
keywords. SQLite tolerates them as column identifiers without quoting, but the
DataExporter wraps them in double quotes when constructing parameterized
`INSERT OR REPLACE` statements to remain portable to any future backend swap.

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (two inserts in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (site, distinct, time window) for the discovered switches count.
    'countSiteDiscoveredSwitches': {                                                # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['site_id', 'distinct', 'start', 'end'],                     # uniquely identifies one polled window
        'indexes': ['site_id', 'distinct'],                                         # fast filter by site or grouping attr
        'table': 'site_discovered_switches_count_summary',                          # target SQLite table for summary rows
    },

    # Per-group rows split out of the parent response's results array.
    'countSiteDiscoveredSwitchesGroups': {                                          # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of summary FK + group value
        'primary_key': ['site_id', 'distinct', 'start', 'end', 'group_value'],      # uniquely identifies a group snapshot
        'indexes': ['group_value'],                                                 # fast lookup by vendor/model/version
        'table': 'site_discovered_switches_count_groups',                           # target SQLite table for group rows
    },
}
```

The `countSiteDiscoveredSwitchesGroups` key is a MistHelper-internal identifier (the
Mist API has no operationId for it -- it is a flattened sub-array of the parent
response). This pattern matches how MistHelper already splits other endpoints whose
response contains nested arrays.
