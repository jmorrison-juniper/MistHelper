# Phase 1 Data Model: countOrgWebhooksDeliveries

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)

This document captures the entities returned by
`GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count`, their MistHelper
persistence shape, the SQLite DDL used to materialize them, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration that drives the upsert behavior.

## Entities

The endpoint returns one logical envelope object plus an embedded array of bucket
objects. MistHelper splits these into two persisted entities.

### Entity 1: CountSummary (envelope, one row per query)

| Field            | Type    | Source                          | Required | Notes |
|------------------|---------|---------------------------------|----------|-------|
| org_id           | TEXT    | Injected by MistHelper          | Yes      | UUID; PK component; FK -> `orgs.id` |
| webhook_id       | TEXT    | Injected by MistHelper          | Yes      | UUID; PK component; FK -> `org_webhooks.id` |
| distinct_field   | TEXT    | Response body `distinct`        | Yes      | PK component; the field name the count was grouped by |
| start_epoch      | INTEGER | Response body `start`           | Yes      | PK component; absolute window start, epoch seconds |
| end_epoch        | INTEGER | Response body `end`             | Yes      | PK component; absolute window end, epoch seconds |
| limit_value      | INTEGER | Response body `limit`           | Yes      | Echo of the limit query parameter |
| total            | INTEGER | Response body `total`           | Yes      | Grand total of deliveries matching the filter set |
| bucket_count     | INTEGER | Computed (`len(results)`)        | Yes      | Number of bucket rows for this envelope |
| query_topic      | TEXT    | Query echo (request)            | No       | Captured client-side; NULL when not supplied |
| query_status     | TEXT    | Query echo (request)            | No       | Captured client-side; NULL when not supplied |
| query_status_code| INTEGER | Query echo (request)            | No       | Captured client-side; NULL when not supplied |
| query_error      | TEXT    | Query echo (request)            | No       | Captured client-side; NULL when not supplied |
| collected_at     | INTEGER | Computed at write time          | Yes      | Epoch seconds when MistHelper persisted the row |

**Primary key**: `(org_id, webhook_id, distinct_field, start_epoch, end_epoch)`.
**Foreign keys**: `org_id` references the canonical org export tables;
`webhook_id` references `org_webhooks(id)` populated by `listOrgWebhooks` (menu 47).
Neither FK is enforced at the SQLite layer (MistHelper does not enable foreign-key
constraints) but the analytical contract is documented here.

The column is named `distinct_field` rather than `distinct` to avoid colliding with the
SQL reserved word; the response body key on the wire is still `distinct`.

### Entity 2: CountBucket (one row per `results` array entry)

| Field            | Type    | Source                          | Required | Notes |
|------------------|---------|---------------------------------|----------|-------|
| org_id           | TEXT    | Injected by MistHelper          | Yes      | UUID; PK component |
| webhook_id       | TEXT    | Injected by MistHelper          | Yes      | UUID; PK component |
| distinct_field   | TEXT    | Response body `distinct`        | Yes      | PK component; identifies which envelope this bucket belongs to |
| start_epoch      | INTEGER | Response body `start`           | Yes      | PK component |
| end_epoch        | INTEGER | Response body `end`             | Yes      | PK component |
| bucket_value     | TEXT    | Response item `<distinct-name>` | Yes      | PK component; the value of the distinct-named property on the bucket (e.g. `succeeded` when `distinct=status`) |
| count            | INTEGER | Response item `count`           | Yes      | Number of deliveries in this bucket |
| extra_json       | TEXT    | Response item (remainder)       | No       | JSON-encoded remainder of free-form string properties on the bucket object (the API schema's `additionalProperties`); empty `{}` when no extras |
| collected_at     | INTEGER | Computed at write time          | Yes      | Epoch seconds when MistHelper persisted the row |

**Primary key**:
`(org_id, webhook_id, distinct_field, start_epoch, end_epoch, bucket_value)`.
**Foreign keys**: composite FK
`(org_id, webhook_id, distinct_field, start_epoch, end_epoch) ->
org_webhook_deliveries_count_summary(...)`. Not enforced at the SQLite layer; documented
here for the analytical contract.

## State Transitions

N/A -- this is a read-only endpoint. There are no client-driven state transitions on
the Mist side. The MistHelper-side lifecycle is:

1. **Not collected** -- no row in either table.
2. **Collected** -- a row exists in `org_webhook_deliveries_count_summary` and zero or
   more matching rows in `org_webhook_deliveries_count_buckets`. Re-running the menu
   item with the same `(org_id, webhook_id, distinct_field, start_epoch, end_epoch)`
   tuple upserts via `INSERT OR REPLACE`; counts in `total` and per-bucket `count`
   reflect the latest poll. Buckets that disappear between polls (e.g. a previously
   present `topic=ping` bucket that drops to zero and is excluded from the next
   response) are **not** deleted by this menu item -- they remain in the table with
   their last observed count. Stale bucket reaping is intentionally out of scope; a
   follow-up spec may add a `--prune` option if operationally needed.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_webhook_deliveries_count_summary (
    org_id            TEXT    NOT NULL,
    webhook_id        TEXT    NOT NULL,
    distinct_field    TEXT    NOT NULL,
    start_epoch       INTEGER NOT NULL,
    end_epoch         INTEGER NOT NULL,
    limit_value       INTEGER NOT NULL,
    total             INTEGER NOT NULL,
    bucket_count      INTEGER NOT NULL,
    query_topic       TEXT,
    query_status      TEXT,
    query_status_code INTEGER,
    query_error       TEXT,
    collected_at      INTEGER NOT NULL,
    PRIMARY KEY (org_id, webhook_id, distinct_field, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_owdc_summary_webhook
    ON org_webhook_deliveries_count_summary (webhook_id);

CREATE INDEX IF NOT EXISTS idx_owdc_summary_org_window
    ON org_webhook_deliveries_count_summary (org_id, start_epoch, end_epoch);

CREATE TABLE IF NOT EXISTS org_webhook_deliveries_count_buckets (
    org_id         TEXT    NOT NULL,
    webhook_id     TEXT    NOT NULL,
    distinct_field TEXT    NOT NULL,
    start_epoch    INTEGER NOT NULL,
    end_epoch      INTEGER NOT NULL,
    bucket_value   TEXT    NOT NULL,
    count          INTEGER NOT NULL,
    extra_json     TEXT,
    collected_at   INTEGER NOT NULL,
    PRIMARY KEY (
        org_id, webhook_id, distinct_field, start_epoch, end_epoch, bucket_value
    )
);

CREATE INDEX IF NOT EXISTS idx_owdc_buckets_webhook
    ON org_webhook_deliveries_count_buckets (webhook_id);

CREATE INDEX IF NOT EXISTS idx_owdc_buckets_distinct_value
    ON org_webhook_deliveries_count_buckets (distinct_field, bucket_value);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (currently around line 1672, per `.github/copilot-instructions.md`).
The dictionary key is the Mist operationId; the value is a dict with `type`,
`primary_key`, `indexes`, and an optional `tables` mapping when the operationId
materializes into more than one table:

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countOrgWebhooksDeliveries"] = {
    "type": "composite_pk",
    "tables": {
        "org_webhook_deliveries_count_summary": {
            "primary_key": [
                "org_id",
                "webhook_id",
                "distinct_field",
                "start_epoch",
                "end_epoch",
            ],
            "indexes": [
                "webhook_id",
                ["org_id", "start_epoch", "end_epoch"],
            ],
        },
        "org_webhook_deliveries_count_buckets": {
            "primary_key": [
                "org_id",
                "webhook_id",
                "distinct_field",
                "start_epoch",
                "end_epoch",
                "bucket_value",
            ],
            "indexes": [
                "webhook_id",
                ["distinct_field", "bucket_value"],
            ],
        },
    },
}
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` structure does not yet support the
`tables` sub-mapping (verify at implementation time by inspecting an existing
multi-table operationId such as `getOrgLicenseAsyncClaimStatus`), register two separate
operationId-suffixed keys (`countOrgWebhooksDeliveries:summary` and
`countOrgWebhooksDeliveries:buckets`), each of `type: composite_pk` with a single
`primary_key` list. Both registration shapes deliver the same upsert semantics; the
choice is purely a function of which dictionary structure the existing code already
supports.
