# Phase 1 Data Model: countOrgTickets

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_tickets_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing aggregated ticket counts
bucketed by a chosen distinct attribute. MistHelper splits this into two logical
entities for clean multi-backend persistence.

### Entity 1: `OrgTicketsCountSummary`

One row per (org, distinct selection, poll). Captures the audit envelope -- the
total bucket count, the limit applied, and the server-reported time window -- so
that historical trend analysis remains possible across repeated polls.

| Field            | Type     | Source                          | PK? | FK?           | Notes |
|------------------|----------|---------------------------------|-----|---------------|-------|
| `org_id`         | TEXT     | MistHelper context              | YES | sites.org_id  | UUID supplied by user; injected before write. |
| `distinct_field` | TEXT     | API `distinct` (or sentinel)    | YES | --            | Echo of the distinct field used. Sentinel `"__server_default__"` when the caller did not supply a value. |
| `polled_at_utc`  | TEXT     | MistHelper clock                | YES | --            | ISO8601 UTC timestamp of the poll. Part of the PK so each poll is preserved for audit. |
| `start_epoch`    | INTEGER  | API `start`                     | --  | --            | Epoch seconds -- start of the result window. |
| `end_epoch`      | INTEGER  | API `end`                       | --  | --            | Epoch seconds -- end of the result window. |
| `limit_applied`  | INTEGER  | API `limit`                     | --  | --            | Echo of the limit the server actually applied. |
| `total_buckets`  | INTEGER  | API `total`                     | --  | --            | Total number of distinct buckets matched. |
| `result_count`   | INTEGER  | len(API `results`)              | --  | --            | Convenience count of rows in the embedded results array (after server-side limit). |

### Entity 2: `OrgTicketsCountResult`

Zero or more rows per (org, distinct selection). One row per bucket returned in the
API `results` array. Re-polling the same org with the same `distinct` field upserts
in place so the count column always reflects the latest snapshot.

| Field            | Type     | Source                                | PK? | FK?                                                 | Notes |
|------------------|----------|---------------------------------------|-----|-----------------------------------------------------|-------|
| `org_id`         | TEXT     | MistHelper context                    | YES | org_tickets_count_summary.org_id                    | UUID. |
| `distinct_field` | TEXT     | API `distinct` (or sentinel)          | YES | org_tickets_count_summary.distinct_field            | Joins to summary. |
| `bucket_value`   | TEXT     | results[].<distinct-key> additionalProp | YES | --                                                | The string value of the bucket key (e.g. `"open"` when `distinct=status`). Coerced to string for PK stability. |
| `count`          | INTEGER  | results[].count                       | --  | --                                                  | Number of tickets in this bucket. |
| `polled_at_utc`  | TEXT     | MistHelper clock                      | --  | --                                                  | ISO8601 UTC timestamp of the latest poll that produced this row. Updated on upsert. |

## State Transitions

N/A -- this is a read-only aggregate endpoint. The summary table accumulates one row
per poll (audit trail). The results table is overwritten in place per
(org, distinct_field, bucket_value) via SQLite `INSERT OR REPLACE`, so the current
view of the bucket counts is always available without scanning history.

## SQLite DDL

```sql
-- Summary table: one row per (org, distinct selection, poll). Accumulates history.
CREATE TABLE IF NOT EXISTS org_tickets_count_summary (
    org_id           TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    polled_at_utc    TEXT     NOT NULL,
    start_epoch      INTEGER,
    end_epoch        INTEGER,
    limit_applied    INTEGER,
    total_buckets    INTEGER,
    result_count     INTEGER,
    PRIMARY KEY (org_id, distinct_field, polled_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_tickets_count_summary_distinct
    ON org_tickets_count_summary (distinct_field);

-- Results table: zero-or-more rows per (org, distinct selection, bucket value).
-- Re-polled buckets upsert in place; the count column always reflects the latest snapshot.
CREATE TABLE IF NOT EXISTS org_tickets_count_results (
    org_id           TEXT     NOT NULL,
    distinct_field   TEXT     NOT NULL,
    bucket_value     TEXT     NOT NULL,
    count            INTEGER,
    polled_at_utc    TEXT,
    PRIMARY KEY (org_id, distinct_field, bucket_value),
    FOREIGN KEY (org_id, distinct_field)
        REFERENCES org_tickets_count_summary(org_id, distinct_field)
);

CREATE INDEX IF NOT EXISTS idx_tickets_count_results_distinct
    ON org_tickets_count_results (distinct_field);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (a single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (org, distinct selection, poll). Accumulates history.
    'countOrgTickets': {                                                            # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields plus poll timestamp
        'primary_key': ['org_id', 'distinct_field', 'polled_at_utc'],               # one row per poll, audit-friendly
        'indexes': ['distinct_field'],                                              # fast filter by which field was bucketed
        'table': 'org_tickets_count_summary',                                       # target SQLite table for summary rows
    },

    # Per-bucket result rows. Upserts so each (org, distinct_field, bucket_value) has one row.
    'countOrgTicketsResults': {                                                     # MistHelper-internal sub-table identifier
        'type': 'composite_pk',                                                     # composite of summary FK plus bucket key
        'primary_key': ['org_id', 'distinct_field', 'bucket_value'],                # uniquely identifies a bucket within a distinct selection
        'indexes': ['distinct_field'],                                              # fast lookup by which field the bucket belongs to
        'table': 'org_tickets_count_results',                                       # target SQLite table for per-bucket rows
    },
}
```

The `countOrgTicketsResults` key is a MistHelper-internal identifier (the Mist API
has no operationId for it -- it is the flattened sub-array of the parent response).
This pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays (see spec 500's
`getOrgLicenseAsyncClaimStatusDetails`).
