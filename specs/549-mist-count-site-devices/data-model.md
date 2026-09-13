# Phase 1 Data Model: countSiteDevices

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_devices_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON "count envelope" describing the result of an
aggregate count of devices at a site, optionally bucketed by a `distinct` field.
MistHelper splits this into two logical entities for clean multi-backend
persistence: a per-poll summary row and zero-or-more bucket rows.

### Entity 1: `SiteDevicesCountSummary` (in-memory only; not persisted as a separate row)

The envelope-level metadata (`distinct`, `start`, `end`, `limit`, `total`) is
denormalized into every bucket row so that one SQL `SELECT` against
`site_devices_count` recovers full poll context. No separate summary table is
materialized; this avoids an unnecessary JOIN for the common "show me the latest
counts" query.

| Field            | Type    | Source              | Notes |
|------------------|---------|---------------------|-------|
| `distinct`       | TEXT    | API `distinct`      | Grouping dimension echoed by server. |
| `start_epoch`    | INTEGER | API `start`         | Start of time window (epoch seconds). |
| `end_epoch`      | INTEGER | API `end`           | End of time window (epoch seconds). |
| `limit_applied` | INTEGER | API `limit`         | Server-honored page size. |
| `total_buckets`  | INTEGER | API `total`         | Total distinct buckets matched. |

### Entity 2: `SiteDevicesCountBucket`

One row per element of the `results[]` array. This is the primary persisted entity.

| Field            | Type    | Source                       | PK? | FK?                | Notes |
|------------------|---------|------------------------------|-----|--------------------|-------|
| `site_id`        | TEXT    | MistHelper context           | YES | sites.id           | UUID supplied by user; injected before write. |
| `distinct_field` | TEXT    | API `distinct`               | YES | --                 | Grouping dimension actually used (e.g. `model`). |
| `bucket_value`   | TEXT    | API `results[].<distinct>`   | YES | --                 | Value of the additional-property string slot (e.g. `"AP43"`). When the server returns a total-only row with no discriminator, the literal string `"__total__"`. |
| `polled_at_utc`  | TEXT    | MistHelper clock             | YES | --                 | ISO8601 UTC timestamp of this poll (preserves historical snapshots). |
| `count`          | INTEGER | API `results[].count`        | --  | --                 | Required per the count_result schema; the number of devices in this bucket. |
| `start_epoch`    | INTEGER | API `start`                  | --  | --                 | Denormalized from envelope. |
| `end_epoch`      | INTEGER | API `end`                    | --  | --                 | Denormalized from envelope. |
| `limit_applied`  | INTEGER | API `limit`                  | --  | --                 | Denormalized from envelope. |
| `total_buckets`  | INTEGER | API `total`                  | --  | --                 | Denormalized from envelope. |
| `raw_bucket`     | TEXT    | json.dumps(results[i])       | --  | --                 | JSON blob of the raw bucket dict, for forensic reuse when a new `distinct` dimension appears that MistHelper does not yet model. |

## State Transitions

N/A -- this is a read-only endpoint. Each poll produces a fresh set of rows
identified by `polled_at_utc`. SQLite `INSERT OR REPLACE` upserts on the composite
key; the inclusion of `polled_at_utc` in the PK means historical snapshots
accumulate over time rather than overwrite each other (different timestamp =
different key = different row).

## SQLite DDL

```sql
-- Single table holds all distinct-field results from countSiteDevices.
-- distinct_field is a discriminator column so one physical table serves all
-- bucketing dimensions (model, version, hostname, mxedge_id, lldp_*, etc.).
CREATE TABLE IF NOT EXISTS site_devices_count (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    bucket_value     TEXT     NOT NULL,
    polled_at_utc    TEXT     NOT NULL,
    count            INTEGER  NOT NULL,
    start_epoch      INTEGER,
    end_epoch        INTEGER,
    limit_applied    INTEGER,
    total_buckets    INTEGER,
    raw_bucket       TEXT,
    PRIMARY KEY (site_id, distinct_field, bucket_value, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_site_devices_count_site
    ON site_devices_count (site_id);

CREATE INDEX IF NOT EXISTS idx_site_devices_count_distinct_field
    ON site_devices_count (distinct_field);

CREATE INDEX IF NOT EXISTS idx_site_devices_count_polled
    ON site_devices_count (polled_at_utc);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not execute the DDL directly from the menu method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py`. No structural change to the dict; just one new
top-level key.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per (site, distinct-field, bucket-value, poll-time) -- preserves
    # historical snapshots while preventing intra-poll duplicates.
    'countSiteDevices': {                                                           # operationId from OpenAPI doc
        'type': 'composite_pk',                                                     # natural composite key, no surrogate id
        'primary_key': [                                                            # four-column composite PK
            'site_id',                                                              # MistHelper-injected (not in API body)
            'distinct_field',                                                       # echo of server-applied grouping dim
            'bucket_value',                                                         # additional-property string slot
            'polled_at_utc',                                                        # ISO8601 UTC -- enables trend history
        ],
        'indexes': [                                                                # support common ad-hoc queries
            'site_id',                                                              # filter by site
            'distinct_field',                                                       # filter by grouping dimension
            'polled_at_utc',                                                        # latest-snapshot queries
        ],
        'table': 'site_devices_count',                                              # shared table for all distinct fields
    },
}
```

The shared-table design (one physical SQLite table, `distinct_field` as a
discriminator column) matches the pattern already used by
`searchSiteDeviceEvents` and `searchSiteAlarms` in MistHelper. It avoids the
N-tables-for-N-dimensions trap and lets the operator run a single
`SELECT * FROM site_devices_count WHERE site_id = ? AND distinct_field = 'model'
ORDER BY polled_at_utc DESC` to chart any dimension over time.
