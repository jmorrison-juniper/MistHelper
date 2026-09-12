# Phase 1 Data Model: countOrgBgpStats

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) |
**Research**: [research.md](./research.md)

## Entities Returned by the Endpoint

The 200 response is a single envelope object with two logical layers:

1. **Run summary** -- top-level scalars describing the count query and its window.
2. **Bucket rows** -- one element per distinct value, each carrying a `count`
   integer plus arbitrary string-valued `additionalProperties` whose key matches
   the requested `distinct` field.

MistHelper flattens this into two related tables (one row per invocation for the
summary, one row per bucket for the buckets).

### Entity 1: `OrgBgpStatsCountRun` (summary, one row per API invocation)

| Field             | Type    | Notes                                                            |
|-------------------|---------|------------------------------------------------------------------|
| `org_id`          | TEXT    | UUID, supplied by user (path parameter). Part of PK.             |
| `distinct_field`  | TEXT    | The `distinct` query parameter sent. Part of PK.                 |
| `state_filter`    | TEXT    | The `state` query parameter sent; `""` (empty string) when blank. Part of PK. |
| `limit_requested` | INTEGER | The `limit` query parameter sent.                                |
| `limit_returned`  | INTEGER | `limit` echoed by the API in the response envelope.              |
| `start_epoch`     | INTEGER | `start` from the response envelope (int32 epoch seconds).        |
| `end_epoch`       | INTEGER | `end` from the response envelope (int32 epoch seconds).          |
| `total`           | INTEGER | `total` matching rows reported by the API (pre-`limit`).         |
| `bucket_count`    | INTEGER | `len(results)` after MistHelper materialization.                 |
| `query_timestamp` | INTEGER | MistHelper-supplied Unix epoch seconds when the call was issued. |

- **Primary key**: `(org_id, distinct_field, state_filter)`
- **Foreign keys**: none (this table is the parent; bucket rows reference it).
- **State transitions**: N/A -- read-only endpoint; each invocation upserts a
  fresh summary row.

### Entity 2: `OrgBgpStatsCountBucket` (per-distinct-value row)

| Field             | Type    | Notes                                                                                  |
|-------------------|---------|----------------------------------------------------------------------------------------|
| `org_id`          | TEXT    | UUID, copied from the run. Part of PK.                                                 |
| `distinct_field`  | TEXT    | Same as run. Part of PK.                                                               |
| `distinct_value`  | TEXT    | The value at `result[distinct_field]` (or the only non-`count` key in `additionalProperties`). Part of PK. |
| `state_filter`    | TEXT    | Same as run. Part of PK.                                                               |
| `count`           | INTEGER | `result.count` -- always present (required by schema).                                 |
| `extra_attrs_json`| TEXT    | JSON-serialized leftover `additionalProperties` keys (rare; empty JSON object when none). |
| `query_timestamp` | INTEGER | Same as the parent run row (denormalized for join-free queries).                       |

- **Primary key**: `(org_id, distinct_field, distinct_value, state_filter)`
- **Foreign keys**: `(org_id, distinct_field, state_filter)` references
  `org_bgp_stats_count_runs(org_id, distinct_field, state_filter)`.
- **State transitions**: N/A -- read-only endpoint; repeated runs upsert the
  same composite key.

## State Transitions

N/A -- read-only endpoint. Each invocation is independent. Repeated runs against
the same `(org_id, distinct_field, state_filter)` tuple upsert both the summary
row and its bucket rows by composite PK.

## SQLite DDL Snippet

The DDL below is generated automatically by `DataExporter` from the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry on first run; it is reproduced here for
reviewer reference. Every executable line carries an inline comment per
Constitution VI.

```sql
-- Run summary table: one row per (org, distinct field, state filter) tuple
CREATE TABLE IF NOT EXISTS org_bgp_stats_count_runs (           -- Parent table for count runs
    org_id           TEXT    NOT NULL,                          -- Mist org UUID (path param)
    distinct_field   TEXT    NOT NULL,                          -- Selected grouping attribute
    state_filter     TEXT    NOT NULL DEFAULT '',               -- Blank string when API param unset
    limit_requested  INTEGER NOT NULL,                          -- limit sent on the request
    limit_returned   INTEGER NOT NULL,                          -- limit echoed in the envelope
    start_epoch      INTEGER NOT NULL,                          -- Response envelope start (int32)
    end_epoch        INTEGER NOT NULL,                          -- Response envelope end (int32)
    total            INTEGER NOT NULL,                          -- API-reported total matching rows
    bucket_count     INTEGER NOT NULL,                          -- len(results) after materialization
    query_timestamp  INTEGER NOT NULL,                          -- Unix epoch when MistHelper called
    PRIMARY KEY (org_id, distinct_field, state_filter)          -- Composite upsert key
);

-- Bucket table: one row per distinct value bucket
CREATE TABLE IF NOT EXISTS org_bgp_stats_count (                -- Detail table for bucket rows
    org_id           TEXT    NOT NULL,                          -- Mist org UUID (matches parent)
    distinct_field   TEXT    NOT NULL,                          -- Grouping attribute (matches parent)
    distinct_value   TEXT    NOT NULL,                          -- Bucket value reported by API
    state_filter     TEXT    NOT NULL DEFAULT '',               -- State filter (matches parent)
    count            INTEGER NOT NULL,                          -- Peers in this bucket
    extra_attrs_json TEXT    NOT NULL DEFAULT '{}',             -- Any leftover additionalProperties
    query_timestamp  INTEGER NOT NULL,                          -- Denormalized run timestamp
    PRIMARY KEY (org_id, distinct_field, distinct_value, state_filter),  -- Composite upsert key
    FOREIGN KEY (org_id, distinct_field, state_filter)          -- Link back to summary row
        REFERENCES org_bgp_stats_count_runs(org_id, distinct_field, state_filter)
        ON DELETE CASCADE                                       -- Drop buckets when run is purged
);

-- Helpful secondary index for "what did peer X look like in org Y" lookups
CREATE INDEX IF NOT EXISTS idx_org_bgp_stats_count_org           -- Speed up per-org bucket scans
    ON org_bgp_stats_count(org_id);                              -- Single-column covering index
```

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (the dict whose insertion point is documented at line ~1672 by
`.github/copilot-instructions.md`). Every executable line carries an inline
comment per Constitution VI.

```python
'countOrgBgpStats': {                                            # operationId -> strategy lookup
    'type': 'composite_pk',                                      # Aggregate buckets, no natural UUID
    'primary_key': [                                             # Composite key for INSERT OR REPLACE
        'org_id',                                                # Disambiguate across orgs
        'distinct_field',                                        # Slice axis selected by user
        'distinct_value',                                        # Specific bucket value
        'state_filter',                                          # State filter narrowing the slice
    ],
    'indexes': [                                                 # Secondary indexes for analytics
        'org_id',                                                # Per-org bucket scans
        'distinct_field',                                        # Find every slice for a field
    ],
    'tables': {                                                  # Two-table layout used by DataExporter
        'summary': 'org_bgp_stats_count_runs',                   # Parent: one row per invocation
        'detail': 'org_bgp_stats_count',                         # Child: one row per bucket
    },
},
```
