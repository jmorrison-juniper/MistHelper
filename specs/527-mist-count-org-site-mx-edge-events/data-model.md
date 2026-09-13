# Phase 1 Data Model: countOrgSiteMxEdgeEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document captures the response entities, their fields, primary keys, foreign-key
relations, state transitions, the SQLite DDL, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration for the new endpoint.

---

## Source Response Schema

The Mist API `GET /api/v1/orgs/{org_id}/mxedges/events/count` returns a single JSON
object (HTTP 200) with the following top-level schema (extracted verbatim from
`documentation/api/orgs/GET_orgs_org_id_mxedges_events_count.md`):

```text
{
  "distinct": "<string>",        # which attribute the counts are grouped by
  "start":    <int epoch>,       # window start (server-resolved)
  "end":      <int epoch>,       # window end   (server-resolved)
  "limit":    <int>,             # max distinct buckets the server returned
  "total":    <int>,             # total events in the window across all buckets
  "results": [                   # unique array of count buckets
    {
      "count": <int>,            # event count for this bucket
      "<distinct_field>": "<string>"   # dynamic key matching `distinct`
      # ...additional string properties may appear when distinct produces
      # composite buckets (the OpenAPI spec marks additionalProperties: string)
    },
    ...
  ]
}
```

The `results[]` array is the only multi-row payload; everything else is window-scoped
metadata. The spec marks `distinct`, `end`, `limit`, `results`, `start`, and `total`
as required, so a successful 200 always carries all six.

---

## Entity 1: `MxEdgeEventCountSummary` (envelope row)

Window-scoped aggregate for one (org, distinct, time-window) tuple.

### Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `org_id` | TEXT (UUID) | injected from prompt | foreign key to `orgs.id` |
| `distinct` | TEXT | response.distinct | which attribute the counts are grouped by |
| `start` | INTEGER (epoch seconds) | response.start | server-resolved window start |
| `end` | INTEGER (epoch seconds) | response.end | server-resolved window end |
| `limit` | INTEGER | response.limit | server-honored max bucket count |
| `total` | INTEGER | response.total | total events across all buckets |
| `result_count` | INTEGER | computed `len(response.results)` | denormalized bucket count for fast dashboard queries |
| `retrieved_at` | TEXT (ISO-8601 UTC) | `datetime.now(UTC).isoformat()` | when MistHelper recorded this row |

### Primary Key

`(org_id, distinct, start, end)` -- composite, exactly identifies one window query.

### Foreign Keys

- `org_id` -> `orgs.id` (the existing org dimension table created by
  `listOrgs` / spec 1 et al.). FK is logical only; SQLite enforcement is left to the
  application layer per established MistHelper convention.

---

## Entity 2: `MxEdgeEventCountResultRow` (per-bucket row)

One row per element of `response.results[]`, denormalized to carry the envelope keys.

### Fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `org_id` | TEXT (UUID) | injected from prompt | foreign key to `orgs.id` |
| `distinct` | TEXT | parent summary | which attribute the counts are grouped by |
| `distinct_value` | TEXT | the dynamic key in this bucket (e.g. `"reboot"`, `"mxagent"`, an mxedge UUID) | populates the bucket identity |
| `count` | INTEGER | bucket.count | event count for this bucket |
| `start` | INTEGER (epoch seconds) | parent summary | window start, denormalized for direct query |
| `end` | INTEGER (epoch seconds) | parent summary | window end, denormalized |
| `extra_properties_json` | TEXT (JSON-encoded dict) | any additional string properties the server returned on this bucket | preserves the OpenAPI `additionalProperties: string` payload without losing fidelity |
| `retrieved_at` | TEXT (ISO-8601 UTC) | `datetime.now(UTC).isoformat()` | when MistHelper recorded this row |

### Primary Key

`(org_id, distinct, distinct_value, start, end)` -- composite, exactly identifies one
bucket inside one window.

### Foreign Keys

- `org_id` -> `orgs.id` (as above, logical only).
- When `distinct == "mxedge_id"` the `distinct_value` is a logical reference to
  `org_mxedges.id`. When `distinct == "mxcluster_id"` it is a logical reference to
  `org_mxclusters.id`. No formal SQLite FK is enforced; the relationship is
  documented for reporting consumers and is materialized as a graph edge in the
  optional ArangoDB backend.

---

## State Transitions

**N/A -- read-only endpoint.** The Mist API performs no mutation on this path; rows
in MistHelper-local storage are simply replaced on re-run via `INSERT OR REPLACE` keyed
on the composite primary keys above. There is no lifecycle, no draft / published
toggle, and no soft-delete semantic associated with these rows.

---

## SQLite DDL

```sql
-- Window-scoped envelope: one row per (org, distinct, time-window) query.
CREATE TABLE IF NOT EXISTS org_mxedge_events_count_summary (
    org_id         TEXT    NOT NULL,
    distinct       TEXT    NOT NULL,
    start          INTEGER NOT NULL,
    end            INTEGER NOT NULL,
    limit          INTEGER NOT NULL,
    total          INTEGER NOT NULL,
    result_count   INTEGER NOT NULL,
    retrieved_at   TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_omecs_org_id
    ON org_mxedge_events_count_summary(org_id);
CREATE INDEX IF NOT EXISTS idx_omecs_distinct
    ON org_mxedge_events_count_summary(distinct);

-- Per-bucket rows: one row per element of response.results[].
CREATE TABLE IF NOT EXISTS org_mxedge_events_count_results (
    org_id                 TEXT    NOT NULL,
    distinct               TEXT    NOT NULL,
    distinct_value         TEXT    NOT NULL,
    count                  INTEGER NOT NULL,
    start                  INTEGER NOT NULL,
    end                    INTEGER NOT NULL,
    extra_properties_json  TEXT,
    retrieved_at           TEXT    NOT NULL,
    PRIMARY KEY (org_id, distinct, distinct_value, start, end)
);

CREATE INDEX IF NOT EXISTS idx_omecr_org_id
    ON org_mxedge_events_count_results(org_id);
CREATE INDEX IF NOT EXISTS idx_omecr_distinct
    ON org_mxedge_events_count_results(distinct);
CREATE INDEX IF NOT EXISTS idx_omecr_distinct_value
    ON org_mxedge_events_count_results(distinct_value);
```

Note: `limit` and `end` are SQLite reserved-word adjacent (`LIMIT` / `END`) but
both are valid column identifiers when not used in an expression position. The
DataExporter already quotes identifiers when emitting `INSERT` statements, so no
rename is required to preserve the response field names verbatim.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

The following dictionary entry is added to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in
`MistHelper.py` (the central registry). The entry references the row-level results
table because that is the multi-row payload `DataExporter` upserts; the summary
table is written through a sibling entry generated at write time using the same
`composite_pk` strategy with a different `primary_key` tuple.

```python
'countOrgSiteMxEdgeEvents': {                                 # operationId from spec.md
    'type': 'composite_pk',                                   # time-windowed aggregate
    'primary_key': [                                          # results-row identity
        'org_id',                                             # injected from prompt
        'distinct',                                           # which attribute grouped
        'distinct_value',                                     # the bucket value
        'start',                                              # window start (epoch)
        'end',                                                # window end (epoch)
    ],
    'indexes': [                                              # speed up dashboard queries
        'org_id',
        'distinct',
        'distinct_value',
    ],
    'table_name': 'org_mxedge_events_count_results',          # primary DataExporter table
    'summary_table_name': 'org_mxedge_events_count_summary',  # envelope sibling table
    'summary_primary_key': [                                  # envelope identity
        'org_id',
        'distinct',
        'start',
        'end',
    ],
},
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` schema in `MistHelper.py` does
not yet support the `summary_table_name` / `summary_primary_key` companion keys
(introduced for two-table aggregate endpoints), the implementing PR adds them as a
minimal backwards-compatible extension: any consumer that does not look for those
keys ignores them and behaves exactly as today.

---

## Cross-Backend Materialization Notes

- **CSV**: One file per logical table; columns match the DDL above.
- **SQLite**: DDL above; `INSERT OR REPLACE` on the composite key.
- **ArangoDB + Redis**: Two document collections matching the table names;
  documents are keyed by a deterministic concatenation of the primary key tuple so
  re-runs upsert in place. Redis caches the most recent summary row keyed by
  `(org_id, distinct, duration)` for the optional viewer (out of scope for this
  spec). Graph edges from each results row to `org_mxedges` /
  `org_mxclusters` are created only when `distinct in {'mxedge_id',
  'mxcluster_id'}` and the referenced node already exists in the graph; otherwise
  the row is stored standalone.
