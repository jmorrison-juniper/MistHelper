# Phase 1 Data Model: countOrgJsiPbn

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_jsi_pbn_count.md` (200 OK body, schema
title `response_count`).

## Entities

The endpoint returns a single JSON object: a count envelope (`distinct`, `start`,
`end`, `limit`, `total`) plus an array `results` whose elements each combine a
required integer `count` with one additional string property whose key matches the
request `distinct` value and whose value is the per-group label (the
`additionalProperties: {type: string}` clause in the schema).

MistHelper collapses this into a single denormalized entity for clean SQLite /
CSV / ArangoDB persistence -- the small envelope (six scalars) is copied onto
each row so a single table answers both "what groups exist" and "what window was
queried".

### Entity 1: `PbnCountRow`

One row per `results[i]` (i.e. per group within the queried window).

| Field           | Type     | Source                       | PK? | FK?         | Notes |
|-----------------|----------|------------------------------|-----|-------------|-------|
| `org_id`        | TEXT     | MistHelper context           | YES | `sites.org_id` | UUID supplied by user; injected before write. |
| `distinct_field`| TEXT     | API `distinct` (envelope)    | YES | --          | Echoes the request grouping field: `versions`, `models`, `customer_risk`, `bug_type`. |
| `group_value`   | TEXT     | `results[i][<distinct_field>]` (additionalProperties) | YES | -- | The actual grouping label, e.g. `"23.4R1"` when `distinct_field="versions"`. NULL when the server omits the property (rare). |
| `window_start`  | INTEGER  | API `start` (envelope)       | YES | --          | Epoch seconds the server honored for the window start. |
| `window_end`    | INTEGER  | API `end` (envelope)         | YES | --          | Epoch seconds the server honored for the window end. |
| `count`         | INTEGER  | `results[i].count`           | --  | --          | Number of PBN advisories in this group within the window. |
| `total`         | INTEGER  | API `total` (envelope)       | --  | --          | Total advisories across all groups in this window. Denormalized for query simplicity. |
| `limit_used`    | INTEGER  | API `limit` (envelope)       | --  | --          | The `limit` value the server honored (may differ from request if clamped). |
| `polled_at_utc` | TEXT     | MistHelper clock             | --  | --          | ISO8601 UTC timestamp of the poll, for audit. |

State transitions: **N/A -- read-only endpoint**. Each invocation overwrites the
matching `(org_id, distinct_field, group_value, window_start, window_end)` row
via `INSERT OR REPLACE`; a different time window or a different `distinct_field`
produces a fresh row, preserving history.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_jsi_pbn_count (
    org_id          TEXT    NOT NULL,
    distinct_field  TEXT    NOT NULL,
    group_value     TEXT    NOT NULL DEFAULT '',
    window_start    INTEGER NOT NULL,
    window_end      INTEGER NOT NULL,
    count           INTEGER NOT NULL,
    total           INTEGER,
    limit_used      INTEGER,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, distinct_field, group_value, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_jsi_pbn_count_org
    ON org_jsi_pbn_count (org_id);
CREATE INDEX IF NOT EXISTS idx_jsi_pbn_count_distinct
    ON org_jsi_pbn_count (distinct_field);
CREATE INDEX IF NOT EXISTS idx_jsi_pbn_count_window
    ON org_jsi_pbn_count (window_start, window_end);
```

`group_value` is `NOT NULL DEFAULT ''` so SQLite primary key uniqueness still
holds when the API omits the additional-property field (the empty string slot is
distinct from any real group label).

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Insert the following entry into the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (the canonical dict near line ~1672):

```python
'countOrgJsiPbn': {                                    # operationId from OpenAPI
    'type': 'composite_pk',                            # aggregate with history dimensions
    'primary_key': [                                    # five-column composite key
        'org_id',                                       # caller-supplied UUID
        'distinct_field',                               # echoes request `distinct`
        'group_value',                                  # per-group label
        'window_start',                                 # epoch seconds, window start
        'window_end',                                   # epoch seconds, window end
    ],
    'indexes': [                                        # query accelerators
        'org_id',                                       # filter by org
        'distinct_field',                               # filter by grouping field
        'window_start',                                 # filter by window start
        'window_end',                                   # filter by window end
    ],
    'table_name': 'org_jsi_pbn_count',                  # SQLite / ArangoDB collection
},
```

## Relationships

- `org_id` is a logical foreign key to the same column on `org_sites` /
  `org_inventory` / any other org-scoped table; not declared as a SQL `FOREIGN
  KEY` because MistHelper avoids cross-table referential constraints to keep
  multi-backend semantics simple.
- No relationship to JSI inventory or PBN search tables is declared; queries
  that need both join in user space on `org_id`.

## Validation Rules

- `distinct_field` must be one of `versions`, `models`, `customer_risk`,
  `bug_type` (enforced client-side before the API call).
- `org_id` must match the Mist UUID shape (enforced client-side).
- `count`, `total`, `limit_used`, `window_start`, `window_end` must be
  non-negative integers when present (server-side guarantee per OpenAPI schema).
