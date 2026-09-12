# Phase 1 Data Model: countOrgJsiSirt

**Feature**: 519-mist-count-org-jsi-sirt
**Date**: 2026-06-28
**Source**: `documentation/api/orgs/GET_orgs_org_id_jsi_sirt_count.md` (200 response
schema).

## Entities

The endpoint returns two logical entities: a `SirtCountResponse` envelope and an inner
`SirtCountResult` row. MistHelper persists only the flattened rows -- the envelope
fields are denormalized onto every row so each SQLite row is fully self-describing for
ad-hoc query without joins.

### Entity 1: SirtCountResponse (envelope, not stored as a row)

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `distinct` | string | yes | response.distinct | Echo of the request `distinct` query param. |
| `end` | integer (epoch s) | yes | response.end | Window end resolved by the API. |
| `start` | integer (epoch s) | yes | response.start | Window start resolved by the API. |
| `limit` | integer | yes | response.limit | Echo of the request `limit` (default 100). |
| `total` | integer | yes | response.total | Total count across all groups. |
| `results` | array<SirtCountResult> | yes | response.results | The per-group rows. |

State transitions: **N/A -- read-only endpoint**. The response is an immutable snapshot
of the moment the API processed the request.

### Entity 2: SirtCountResult (persisted row)

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `org_id` | TEXT | yes | request path param | Part of composite PK. |
| `distinct` | TEXT | yes | envelope.distinct | Part of composite PK; one of `jsa_updated_date`, `models`, `severity`, `versions`. |
| `group_value` | TEXT | yes | dynamic property name in `results[i]` (the property paired with `count`) | Part of composite PK; the value the row is grouped by. |
| `count` | INTEGER | yes | results[i].count | The aggregated count for this group. |
| `start_epoch` | INTEGER | yes | envelope.start | Part of composite PK; window start. |
| `end_epoch` | INTEGER | yes | envelope.end | Part of composite PK; window end. |
| `limit` | INTEGER | yes | envelope.limit | Echo for traceability. |
| `total` | INTEGER | yes | envelope.total | Snapshot total at extraction time. |
| `fetched_at` | INTEGER (epoch s) | yes | `int(time.time())` at write | Audit column; not part of PK. |

Foreign keys: `org_id` is a logical foreign key to the existing `org` table populated
by the org-listing menu items. No formal `FOREIGN KEY` constraint is added because
MistHelper's SQLite layer uses logical references only -- the operator may extract
SIRT counts before ever listing orgs.

State transitions: **N/A -- read-only endpoint**. Repeated runs update the row
in place via the composite PK upsert.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_jsi_sirt_count (
    org_id      TEXT    NOT NULL,
    distinct    TEXT    NOT NULL,
    group_value TEXT    NOT NULL,
    count       INTEGER NOT NULL,
    start_epoch INTEGER NOT NULL,
    end_epoch   INTEGER NOT NULL,
    limit       INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    fetched_at  INTEGER NOT NULL,
    PRIMARY KEY (org_id, distinct, group_value, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_org_jsi_sirt_count_org      ON org_jsi_sirt_count(org_id);
CREATE INDEX IF NOT EXISTS idx_org_jsi_sirt_count_distinct ON org_jsi_sirt_count(distinct);
CREATE INDEX IF NOT EXISTS idx_org_jsi_sirt_count_group    ON org_jsi_sirt_count(group_value);
```

Note: the column name `distinct` and `limit` are SQL reserved-ish words; MistHelper's
existing `DataExporter` layer already quotes column identifiers when generating the
`INSERT OR REPLACE` statement, so no rename is required. If the SQLite version on a
target host rejects the unquoted identifier, the implementation falls back to
`"distinct"` quoted columns via the same path used elsewhere in the codebase.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
"countOrgJsiSirt": {
    "type": "composite_pk",
    "primary_key": [
        "org_id",
        "distinct",
        "group_value",
        "start_epoch",
        "end_epoch",
    ],
    "indexes": ["org_id", "distinct", "group_value"],
    "table_name": "org_jsi_sirt_count",
},
```

This entry is inserted into the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (around
line ~1672 of `MistHelper.py`) alongside the other `count*` operation entries in
alphabetical order under `countOrg...`. The `table_name` key is set explicitly so
`DataExporter.write_with_format_selection()` does not have to derive a name from the
operationId at runtime.

## Flatten algorithm

For each `result` dict in `response.data["results"]`:

1. Extract `count` directly.
2. Identify the single non-`count` key in the dict -- this is the dynamic group label
   whose name equals `response.data["distinct"]`. Read its value into `group_value`.
3. Combine with the denormalized envelope fields (`org_id`, `distinct`, `start_epoch`,
   `end_epoch`, `limit`, `total`) and the audit timestamp to produce one flat row.
4. Pass the list of flat rows to `DataExporter.write_with_format_selection()`.

If the API returns an empty `results` array, no rows are written; the menu method
emits an `INFO` log line ("countOrgJsiSirt returned 0 groups for org %s distinct=%s")
and exits 0 without raising.
