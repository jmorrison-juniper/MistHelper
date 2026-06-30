# Phase 1 Data Model: countSiteBgpStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/sites/GET_sites_site_id_stats_bgp_peers_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing a count aggregation of BGP peer
statistics at a site, grouped by a distinct attribute. MistHelper flattens the response
into two logical entities for clean multi-backend persistence: an envelope row that
captures metadata about the count query (window, limit, total), and zero-or-more bucket
rows (one per distinct value).

### Entity 1: `BgpStatsCountBucket`

One row per (site, distinct_field, distinct_value). This is the primary entity. Source:
each element of the API `results` array.

| Field             | Type    | Source                                          | PK? | FK?           | Notes |
|-------------------|---------|-------------------------------------------------|-----|---------------|-------|
| `site_id`         | TEXT    | MistHelper context (user prompt)                | YES | sites.id      | UUID; injected before write -- not echoed in the API body. |
| `distinct_field`  | TEXT    | API top-level `distinct`                        | YES | --            | The attribute the API grouped by (e.g. `state`, `neighbor_as`, `vrf_name`). |
| `distinct_value`  | TEXT    | API `results[*]` non-`count` property           | YES | --            | The bucket label. Extracted generically as the single non-`count` key in each bucket dict. |
| `count`           | INTEGER | API `results[*].count`                          | --  | --            | The bucket count itself. |
| `state_filter`    | TEXT    | User prompt 2 (`state`)                         | --  | --            | The BGP state filter passed to the API on this run (NULL when no filter). Stored for audit. |
| `window_start`    | INTEGER | API top-level `start`                           | --  | --            | Epoch seconds, start of the count window. |
| `window_end`      | INTEGER | API top-level `end`                             | --  | --            | Epoch seconds, end of the count window. |
| `window_total`    | INTEGER | API top-level `total`                           | --  | --            | Total bucket count available (may exceed `limit`). |
| `applied_limit`   | INTEGER | API top-level `limit`                           | --  | --            | The row limit the API actually applied. |
| `polled_at_utc`   | TEXT    | MistHelper clock (`datetime.utcnow().isoformat()`) | -- | --         | ISO8601 UTC poll timestamp, for audit. |

Each bucket row is fully self-describing: the envelope metadata (`window_start`,
`window_end`, `window_total`, `applied_limit`) is denormalized into every row so SQL
queries against this single table need no JOIN to recover the query context.

### Entity 2: `BgpStatsCountEnvelope` (logical only)

Conceptually the API response carries one envelope object describing the query
(`distinct`, `start`, `end`, `limit`, `total`). MistHelper does **not** persist this as
a separate table -- its fields are denormalized into every `BgpStatsCountBucket` row
(see entity 1) so a single table is enough to answer "what was the BGP state
distribution at site X at time T?" without joins.

This is a deliberate simplification: with average bucket counts under 100 (per the API
default `limit`), the denormalization cost is negligible and the SQL ergonomics gain is
material.

## State Transitions

N/A -- this is a read-only endpoint. The underlying BGP peer state on the Mist side
transitions continuously (peers come up, go down, reset), but MistHelper does not drive
or model those transitions; it merely captures count snapshots. Each poll overwrites the
prior snapshot for the same `(site_id, distinct_field, distinct_value)` tuple via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Single bucket table: one row per (site, distinct_field, distinct_value).
CREATE TABLE IF NOT EXISTS site_bgp_stats_count (
    site_id          TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    distinct_value   TEXT     NOT NULL,
    count            INTEGER,
    state_filter     TEXT,
    window_start     INTEGER,
    window_end       INTEGER,
    window_total     INTEGER,
    applied_limit    INTEGER,
    polled_at_utc    TEXT,
    PRIMARY KEY (site_id, distinct_field, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_site_bgp_stats_count_state_filter
    ON site_bgp_stats_count (state_filter);

CREATE INDEX IF NOT EXISTS idx_site_bgp_stats_count_distinct_field
    ON site_bgp_stats_count (distinct_field);

CREATE INDEX IF NOT EXISTS idx_site_bgp_stats_count_site
    ON site_bgp_stats_count (site_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (single insert in the dict literal, no structural change to the
dictionary itself).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One bucket row per (site, distinct attribute, bucket value).
    # Re-running with the same site + distinct upserts existing buckets cleanly.
    'countSiteBgpStats': {                                                          # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['site_id', 'distinct_field', 'distinct_value'],             # uniquely identifies one bucket
        'indexes': ['state_filter', 'distinct_field', 'site_id'],                   # speed up post-import filtering
        'table': 'site_bgp_stats_count',                                            # target SQLite table for bucket rows
    },
}
```

Notes on the registration:

- The `type` is `composite_pk` because the natural identifier of a bucket is a tuple
  of three business fields, not a server-supplied UUID and not an arbitrary auto-
  increment. This guarantees `INSERT OR REPLACE` upsert semantics on repeated polls.
- The `indexes` list deliberately omits `distinct_value` -- it is already the third
  column of the PK and so already indexed by the primary key index.
- The `table` value matches the DDL above; if any future MistHelper refactor changes
  the table name, both this dict entry and the DDL must move together.
