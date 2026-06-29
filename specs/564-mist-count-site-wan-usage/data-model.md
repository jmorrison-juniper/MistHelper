# Phase 1 Data Model: countSiteWanUsage

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_wan_usages_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON envelope describing the distinct-value count of
WAN usage records at a site over a time window. MistHelper flattens this envelope into
one logical entity (`WanUsageCountRow`) so the output table can be queried directly
with a single SQL statement -- no joins required.

### Entity 1: `WanUsageCountRow`

One row per (site, grouping dimension, time window, distinct value of the grouping
dimension).

| Field            | Type     | Source                       | PK? | FK?           | Notes |
|------------------|----------|------------------------------|-----|---------------|-------|
| `site_id`        | TEXT     | MistHelper context           | YES | sites.id      | UUID supplied by the caller; injected before write. |
| `distinct_field` | TEXT     | API `distinct`               | YES | --            | The field the API grouped by (`mac`, `peer_mac`, `port_id`, `peer_port_id`, `policy`, `tenant`, `path_type`). |
| `window_start`   | INTEGER  | API `start`                  | YES | --            | Epoch seconds, effective window start. |
| `window_end`     | INTEGER  | API `end`                    | YES | --            | Epoch seconds, effective window end. |
| `distinct_value` | TEXT     | `results[].<distinct_field>` | YES | --            | The grouping field's value on this row (e.g., a MAC string when `distinct_field=mac`). |
| `count`          | INTEGER  | `results[].count`            | --  | --            | Number of WAN usage records observed for this distinct value in the window. |
| `limit_effective`| INTEGER  | API `limit`                  | --  | --            | Effective server-side `limit` used (default 100). |
| `total_distinct` | INTEGER  | API `total`                  | --  | --            | Total distinct values the server has available (may exceed the rows returned when capped by `limit`). |
| `polled_at_utc`  | TEXT     | MistHelper clock             | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |
| `raw_extra_json` | TEXT     | `results[]` extra props      | --  | --            | JSON-encoded dict of any additional string-typed properties returned in the same row (the schema declares `additionalProperties: string`). Empty `{}` when none. |

The `count_result` schema declares `additionalProperties: {type: string}`, meaning the
API may return string-typed sidecar fields alongside `count` (for example, when
`distinct=mac` the row also carries a `mac` string equal to the MAC address). The
primary string sidecar -- the one whose key matches `distinct_field` -- is copied
into `distinct_value`. Any *other* sidecar string properties are preserved verbatim
as a JSON blob in `raw_extra_json` so MistHelper does not silently discard data the
server returned.

## State Transitions

N/A -- this is a read-only endpoint. The Mist server computes the count on demand
from underlying WAN usage records. Each poll overwrites the prior snapshot for the
same `(site_id, distinct_field, window_start, window_end, distinct_value)` tuple via
SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Site-scoped WAN usage distinct-count rows.
CREATE TABLE IF NOT EXISTS site_wan_usage_counts (
    site_id           TEXT     NOT NULL,
    distinct_field    TEXT     NOT NULL,
    window_start      INTEGER  NOT NULL,
    window_end        INTEGER  NOT NULL,
    distinct_value    TEXT     NOT NULL,
    count             INTEGER,
    limit_effective   INTEGER,
    total_distinct    INTEGER,
    polled_at_utc     TEXT,
    raw_extra_json    TEXT,
    PRIMARY KEY (site_id, distinct_field, window_start, window_end, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_site_wan_usage_counts_field
    ON site_wan_usage_counts (distinct_field);

CREATE INDEX IF NOT EXISTS idx_site_wan_usage_counts_window
    ON site_wan_usage_counts (window_start, window_end);

CREATE INDEX IF NOT EXISTS idx_site_wan_usage_counts_count
    ON site_wan_usage_counts (count);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Site-scoped distinct count of WAN usage records, keyed by
    # (site, grouping field, window, distinct value).
    'countSiteWanUsage': {                                                          # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': [                                                            # five-field natural identity
            'site_id',                                                              # MistHelper-injected site UUID
            'distinct_field',                                                       # which dimension the API grouped by
            'window_start',                                                         # effective epoch start of the window
            'window_end',                                                           # effective epoch end of the window
            'distinct_value',                                                       # the grouping dimension's row value
        ],
        'indexes': [                                                                # secondary indexes for common filters
            'distinct_field',                                                       # fast filter by grouping dimension
            'window_start',                                                         # time-range scans use this index
            'count',                                                                # rank rows by observed count
        ],
        'table': 'site_wan_usage_counts',                                           # target SQLite table for all rows
    },
}
```

No MistHelper-internal sub-table key is required: the Mist response is a single
envelope with a single results array, and the flattening preserves every server
field on every row. The `additionalProperties: string` overflow is handled in-band by
the `raw_extra_json` TEXT column rather than by creating a second table.
