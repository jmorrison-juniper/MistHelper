# Phase 1 Data Model: countOrgWiredClients

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/wired_clients/count`

## Entities Returned by the Endpoint

The 200 response is a single envelope object containing one bounded array.
MistHelper flattens it into a single SQLite table (`org_wired_clients_count`)
that holds both the envelope summary and the per-distinct-value result rows
under a sentinel pattern.

### Entity 1: `CountEnvelope`

The wrapper object returned by the API for one count call.

| Field           | Type     | Required | Notes                                                          |
|-----------------|----------|----------|----------------------------------------------------------------|
| `distinct`      | string   | yes      | The grouping field actually used by the API for this run.      |
| `total`         | integer  | yes      | Total number of distinct values found.                         |
| `limit`         | integer  | yes      | Echoed-back limit applied by the API.                          |
| `start`         | integer  | yes      | Epoch seconds. Start of the count window.                      |
| `end`           | integer  | yes      | Epoch seconds. End of the count window.                        |
| `results`       | array    | yes      | Bounded array of `CountResult` objects, length <= `limit`.     |

**Primary key (flattened)**: `(org_id, distinct, "__summary__", start, end)`.
The `org_id` field is injected by MistHelper from the user prompt; it is not
returned by the API.

**Foreign keys**: `org_id` references the `orgs` collection (ArangoDB graph
backend per spec 188). No other foreign keys.

### Entity 2: `CountResult`

One element of `CountEnvelope.results`. Each element is a small object with a
required integer `count` plus arbitrary string additional properties (one per
distinct attribute value).

| Field             | Type     | Required | Notes                                                                                  |
|-------------------|----------|----------|----------------------------------------------------------------------------------------|
| `count`           | integer  | yes      | Number of wired clients matching this distinct value.                                  |
| `<distinct_field>`| string   | yes      | A single additional property whose key equals the envelope's `distinct` value and whose value is the actual attribute (e.g. when `distinct=mac`, the property name is `mac` and the value is `5c5b35aabbcc`). |

MistHelper normalizes each result into a fixed-shape row by introducing a
`distinct_value` column that holds the additional property's value, plus the
already-known `distinct` column that names which attribute it is. This avoids a
sparse schema with one column per possible distinct field.

**Primary key (flattened)**: `(org_id, distinct, distinct_value, start, end)`.

**Foreign keys**: `org_id` references the `orgs` collection (graph backend).
`distinct_value` may semantically reference a wired client MAC or port ID; the
SQL schema does not enforce that FK because the related row is not guaranteed
to exist in any single MistHelper run.

## State Transitions

N/A -- this is a read-only GET endpoint. Rows are immutable snapshots keyed by
the `(org_id, distinct, distinct_value, start, end)` tuple. Repeat runs over
the identical window with the identical grouping are idempotent upserts; runs
over different windows or different groupings produce additional rows without
overwriting historical data.

## SQLite DDL

`DataExporter.write_with_format_selection()` creates this table on first run
based on the inferred schema plus the registered PK strategy. The DDL below
documents the resulting shape for review and is not executed by hand.

```sql
CREATE TABLE IF NOT EXISTS org_wired_clients_count (
    org_id          TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    distinct_value  TEXT    NOT NULL,
    start           INTEGER NOT NULL,
    end             INTEGER NOT NULL,
    duration        TEXT,
    limit_value     INTEGER,
    total           INTEGER,
    count           INTEGER,
    fetched_at      TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, distinct_value, start, end)
);

CREATE INDEX IF NOT EXISTS idx_owcc_org_id          ON org_wired_clients_count(org_id);
CREATE INDEX IF NOT EXISTS idx_owcc_distinct        ON org_wired_clients_count(distinct);
CREATE INDEX IF NOT EXISTS idx_owcc_distinct_value  ON org_wired_clients_count(distinct_value);
CREATE INDEX IF NOT EXISTS idx_owcc_start_end       ON org_wired_clients_count(start, end);
```

Notes on the DDL:

- `limit` is renamed `limit_value` because `LIMIT` is a SQLite reserved word
  and `DataExporter` already maps reserved-word collisions to a `_value`
  suffix.
- `total` is duplicated on every row (envelope and results alike) so a single
  `SELECT` against any row of a snapshot reveals the total.
- `count` is `NULL` for the envelope sentinel row and populated for each
  result row.
- `fetched_at` is an ISO-8601 UTC timestamp inserted by MistHelper at write
  time; it does not participate in the PK so re-runs upsert rather than
  appending.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add this entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (around the existing `searchOrgWiredClients` entry, near
line ~1672):

```python
'countOrgWiredClients': {                                                       # operationId from the OpenAPI spec; used by DataExporter lookup
    'type': 'composite_pk',                                                     # composite key strategy because no single UUID is returned
    'primary_key': ['org_id', 'distinct', 'distinct_value', 'start', 'end'],    # tuple uniquely identifies one (org, grouping, value, window) snapshot
    'indexes': ['org_id', 'distinct', 'distinct_value', 'start', 'end'],        # secondary indexes to speed up per-org and per-distinct lookups
    'reserved_word_remap': {'limit': 'limit_value'},                            # SQLite reserves LIMIT; rename to avoid quoting in every query
},                                                                              # comma keeps the dict tail consistent
```

The `reserved_word_remap` key is the existing DataExporter hook for SQLite
reserved-word collisions; it does not require any new infrastructure.

## Cross-Entity Notes

- The envelope row and the result rows share one flat schema. Consumers
  distinguish them by `distinct_value = '__summary__'` (envelope) versus any
  other value (result).
- Across multiple runs, `(org_id, distinct, distinct_value, start, end)`
  remains stable, so SQL aggregates like `SELECT SUM(count) FROM
  org_wired_clients_count WHERE org_id = ? AND distinct = 'mac' AND start = ?
  AND end = ? AND distinct_value != '__summary__'` correctly recompute the
  envelope's `total` for any given snapshot.
- The polyglot ArangoDB backend (spec 188) treats each row as a document in
  the `org_wired_clients_count` collection and emits a graph edge
  `(org_wired_clients_count) -[BELONGS_TO]-> (orgs)` keyed on `org_id`.
