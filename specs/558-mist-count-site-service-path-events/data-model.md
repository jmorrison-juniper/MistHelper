# Phase 1 Data Model: countSiteServicePathEvents

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_services_events_count.md` (200 OK
body).

## Entities

The endpoint returns a single JSON envelope describing a grouped count of
Service Path Events for a site, plus an array of per-bucket result rows.
MistHelper flattens this into one logical entity for clean multi-backend
persistence: each output row represents one bucket of the count, tagged with
the query envelope it belongs to.

### Entity 1: `ServicePathEventCountBucket`

One row per (site, distinct field, bucket value, query window). The envelope
fields (`distinct`, `start`, `end`, `limit`, `total`) are denormalized onto
every bucket row so that no join is required to interpret a single row's
context.

| Field             | Type    | Source                | PK? | FK?         | Notes |
|-------------------|---------|-----------------------|-----|-------------|-------|
| `site_id`         | TEXT    | MistHelper context    | YES | sites.id    | UUID supplied by user; injected before write. Mist does not echo this in the body. |
| `distinct_field`  | TEXT    | API `distinct`        | YES | --          | The grouping field name (`type`, `vpn_name`, `vpn_path`, `policy`, `port_id`, `model`, `version`, `mac`). Echoes the query parameter. |
| `distinct_value`  | TEXT    | API `results[].<distinct>` | YES | -- | The actual bucket label. Found in each `results[]` element under a key whose name equals `distinct_field`. |
| `start`           | INTEGER | API `start`           | YES | --          | Window start, epoch seconds. Part of PK so multiple snapshots over different windows coexist. |
| `end`             | INTEGER | API `end`             | YES | --          | Window end, epoch seconds. Part of PK alongside `start`. |
| `count`           | INTEGER | API `results[].count` | --  | --          | Number of events in this bucket within the window. Required by the API schema. |
| `limit`           | INTEGER | API `limit`           | --  | --          | Echoes the `limit` query parameter the server applied (default 100). |
| `total`           | INTEGER | API `total`           | --  | --          | Total events across all buckets in the window. Identical across all rows of one query. |
| `polled_at_utc`   | TEXT    | MistHelper clock      | --  | --          | ISO8601 UTC timestamp of the poll, for audit. |

Note: the `results[]` items in the API response use the *value* of the
`distinct` query parameter as the key holding the bucket label (e.g. with
`distinct=type`, each item is `{"count": 42, "type": "GW_SERVICE_PATH_DOWN"}`).
MistHelper's flatten step reads `item[distinct_field]` to populate
`distinct_value`, then discards the original variable-named key so the SQLite
schema is fixed regardless of which distinct field the user chose.

## State Transitions

N/A -- this is a read-only endpoint. Repeated polls of the same
(site, distinct field, window) tuple overwrite the prior snapshot via SQLite
`INSERT OR REPLACE`. Polls with different windows or different distinct
fields add new rows without disturbing existing ones.

## SQLite DDL

```sql
-- Count-by-distinct buckets for site service-path events.
CREATE TABLE IF NOT EXISTS site_service_path_events_count (
    site_id           TEXT     NOT NULL,
    distinct_field    TEXT     NOT NULL,
    distinct_value    TEXT     NOT NULL,
    start             INTEGER  NOT NULL,
    end               INTEGER  NOT NULL,
    count             INTEGER  NOT NULL,
    limit             INTEGER,
    total             INTEGER,
    polled_at_utc     TEXT,
    PRIMARY KEY (site_id, distinct_field, distinct_value, start, end)
);

-- Speed up "show me all type=GW_SERVICE_PATH_DOWN buckets across windows" queries.
CREATE INDEX IF NOT EXISTS idx_svc_path_events_count_field_value
    ON site_service_path_events_count (distinct_field, distinct_value);

-- Speed up "latest window per site" lookups.
CREATE INDEX IF NOT EXISTS idx_svc_path_events_count_site_end
    ON site_service_path_events_count (site_id, end);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing).
MistHelper does not run the DDL directly.

Note on the reserved word `end`: SQLite accepts `end` as a column name when
not used as a keyword in context (e.g., inside a CREATE TABLE column list and
inside a PRIMARY KEY tuple). If portability to a stricter SQL dialect is ever
required, the column is renamed to `window_end` (and `start` to
`window_start`) without changing the conceptual schema. The CSV header
follows the SQLite column names.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Aggregated count buckets keyed by (site, distinct field, bucket value, window).
    'countSiteServicePathEvents': {                                                   # operationId from OpenAPI
        'type': 'composite_pk',                                                       # PK is composite of business fields
        'primary_key': [                                                              # five-tuple uniquely identifies one bucket of one query
            'site_id',                                                                # injected by MistHelper (not in body)
            'distinct_field',                                                         # echoes the query parameter
            'distinct_value',                                                         # bucket label from results[]
            'start',                                                                  # window start, server-confirmed
            'end',                                                                    # window end, server-confirmed
        ],
        'indexes': [                                                                  # query-shaping hints for SQLite + ArangoDB backends
            'distinct_field',                                                         # "all buckets of this distinct field"
            'distinct_value',                                                         # "all windows for this bucket value"
            'end',                                                                    # "latest window first"
        ],
        'table': 'site_service_path_events_count',                                    # target SQLite table
    },
}
```

The single key `countSiteServicePathEvents` covers the only output table this
menu item produces. No MistHelper-internal sub-table identifiers are needed
because the response has no nested arrays beyond `results[]` (which is the
flattened entity itself).
