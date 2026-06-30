# Phase 1 Data Model: countOrgTunnelsStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

This document describes the entities returned by `countOrgTunnelsStats`, the flattening
applied by MistHelper, the SQLite DDL produced on first run, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration.

## Source Response Shape (from documentation/api/orgs/GET_orgs_org_id_stats_tunnels_count.md)

```json
{
  "distinct": "wxtunnel_id",
  "start": 1719600000,
  "end":   1719603600,
  "limit": 100,
  "total": 23,
  "results": [
    {"count": 42, "wxtunnel_id": "abc-123"},
    {"count":  5, "wxtunnel_id": "def-456"}
  ]
}
```

Required top-level keys: `distinct`, `start`, `end`, `limit`, `total`, `results`.
Each `results[i]` object has a required `count` (int) plus exactly one additional
string property whose key is the value of the top-level `distinct` field and whose
value is the discriminator (group-by value) for that count bucket.

## Entities

### Entity 1: `TunnelStatsCountRow` (flattened result row)

One row per element of `results[]`. MistHelper denormalizes the per-call envelope
(`distinct`, `start`, `end`, `limit`, `total`) into every row for trivial
queryability.

| Field            | Type     | Source                                     | Notes                                                     |
| ---------------- | -------- | ------------------------------------------ | --------------------------------------------------------- |
| `org_id`         | TEXT     | MistHelper (injected before upsert)        | UUID. PK component. FK to org-level tables.               |
| `query_type`     | TEXT     | Request param `type` (or `"none"`)         | One of `wxtunnel`, `wan`, `none`. PK component.           |
| `query_distinct` | TEXT     | Response top-level `distinct`              | Echoes the requested distinct attribute. PK component.    |
| `distinct_value` | TEXT     | The one non-`count` key/value on each row  | The group-by value. PK component.                         |
| `count`          | INTEGER  | Response `results[i].count`                | Required by schema.                                       |
| `query_start`    | INTEGER  | Response top-level `start`                 | Epoch seconds.                                            |
| `query_end`      | INTEGER  | Response top-level `end`                   | Epoch seconds.                                            |
| `query_limit`    | INTEGER  | Response top-level `limit`                 | Row cap actually applied.                                 |
| `query_total`    | INTEGER  | Response top-level `total`                 | Total distinct values in the org (may exceed `limit`).    |
| `collected_at`   | INTEGER  | MistHelper (`time.time()` cast to int)     | Epoch seconds the row was written.                        |

**Primary key**: `(org_id, query_type, query_distinct, distinct_value)`.
**Foreign keys**: `org_id` references the org-level identifier convention used across
MistHelper tables (no enforced FK constraint in SQLite, but documented for graph
backend edge construction).

### Entity 2: `TunnelStatsCountEnvelope` (NOT persisted as its own table)

The top-level envelope is intentionally denormalized into every `TunnelStatsCountRow`
rather than stored separately. Rationale: the envelope is tiny (5 ints + 1 string),
storing it once per row keeps queries simple and avoids a JOIN for the most common
use case (`SELECT distinct_value, count FROM org_tunnels_stats_count WHERE org_id=?
AND query_type=? AND query_distinct=? ORDER BY count DESC`).

## State Transitions

N/A -- this is a read-only GET endpoint. Rows are upserted on every poll;
`INSERT OR REPLACE` semantics (driven by the composite PK) overwrite older snapshots
in place. There is no lifecycle, no soft-delete, no archival flag.

## SQLite DDL (created on first run by DataExporter)

```sql
CREATE TABLE IF NOT EXISTS org_tunnels_stats_count (
    org_id          TEXT    NOT NULL,
    query_type      TEXT    NOT NULL,
    query_distinct  TEXT    NOT NULL,
    distinct_value  TEXT    NOT NULL,
    count           INTEGER NOT NULL,
    query_start     INTEGER,
    query_end       INTEGER,
    query_limit     INTEGER,
    query_total     INTEGER,
    collected_at    INTEGER NOT NULL,
    PRIMARY KEY (org_id, query_type, query_distinct, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_org_tunnels_stats_count_org
    ON org_tunnels_stats_count (org_id);
CREATE INDEX IF NOT EXISTS idx_org_tunnels_stats_count_collected
    ON org_tunnels_stats_count (collected_at);
```

The two secondary indexes accelerate the two most common queries:
("show me everything for org X") and ("show me the most recent snapshot").

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following block to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (alphabetized within the dictionary; canonical entry shown):

```python
'countOrgTunnelsStats': {                                   # operationId from OpenAPI; matches DataExporter lookup key
    'type': 'composite_pk',                                  # repeated polls must upsert, not append
    'primary_key': [                                         # 4-column composite PK
        'org_id',                                            # MistHelper-injected org context
        'query_type',                                        # wxtunnel / wan / none
        'query_distinct',                                    # group-by attribute echoed by API
        'distinct_value',                                    # group-by value for this bucket
    ],
    'indexes': [                                             # non-PK secondary indexes for hot queries
        'org_id',                                            # per-org fan-out queries
        'collected_at',                                      # latest-snapshot queries
    ],
    'table_name': 'org_tunnels_stats_count',                 # SQLite table created on first write
}
```

Every line above carries an inline comment per Constitution VI (Inline Comments,
NON-NEGOTIABLE). The dictionary key string MUST exactly match the `api_function_name`
argument passed to `DataExporter.write_with_format_selection()` at the call site.

## Validation Rules Enforced Before Persist

- `org_id`: must be a 36-character UUID matching the existing `is_valid_uuid()`
  helper; otherwise the row is dropped and a `WARNING` is logged.
- `query_type`: coerced to lowercase; must be one of `wxtunnel`, `wan`, or the
  literal `none`. Any other value is replaced with `none` and a `WARNING` is
  emitted.
- `query_distinct`: must be in the type-specific enum from Research Task 1; if not,
  the row is logged at `WARNING` and dropped (the response should never deliver an
  out-of-enum distinct field, but defense-in-depth catches API regressions).
- `distinct_value`: cast to `str()` (the OpenAPI `additionalProperties: {type:
  string}` guarantees this, but defensive coercion costs nothing).
- `count`: cast to `int`; negatives are clamped to `0` with a `WARNING`.
- `collected_at`: set to `int(time.time())` at write time inside MistHelper.

## ArangoDB / Redis Backend Notes

When the polyglot backend is active, the row is additionally:

1. Upserted as a vertex `org_tunnels_stats_count/<org_id>:<query_type>:<query_distinct>:<distinct_value>`
   in ArangoDB (key = the composite PK joined by `:`).
2. Edged to the `orgs/<org_id>` vertex with edge collection `org_tunnels_stats_edge`.
3. Cached in Redis under key `tunnels_count:<org_id>:<query_type>:<query_distinct>`
   with TTL `300` seconds (consistent with adjacent stats caches).

These steps are handled transparently by `DataExporter` -- no menu-method code is
needed beyond the standard `write_with_format_selection()` call.
