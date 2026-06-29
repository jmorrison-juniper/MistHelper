# Phase 1 Data Model: countOrgJsiAssetsAndContracts

**Feature**: Mist API GET `/api/v1/orgs/{org_id}/jsi/inventory/count`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Source of Truth

The response schema below is taken verbatim from
`documentation/api/orgs/GET_orgs_org_id_jsi_inventory_count.md` (the enriched per-
endpoint documentation generated from the Mist OpenAPI 3 spec).

## Response Envelope (Entity 1: CountSummary)

The endpoint returns a single JSON object describing the aggregate counting run.

| Field      | Type    | Required | Description                                                      |
|------------|---------|----------|------------------------------------------------------------------|
| `distinct` | string  | Yes      | The field the server bucketed counts by (echoes the request).    |
| `total`    | integer | Yes      | Total number of items considered before bucketing.               |
| `limit`    | integer | Yes      | Echo of the `limit` query parameter (server-applied).            |
| `start`    | integer | Yes      | Start of the window (epoch seconds; server-set).                 |
| `end`      | integer | Yes      | End of the window (epoch seconds; server-set).                   |
| `results`  | array   | Yes      | Bucketed counts -- see Entity 2 below.                           |

### MistHelper-added fields on the summary row

| Field                    | Type    | Origin                                  |
|--------------------------|---------|------------------------------------------|
| `misthelper_internal_id` | integer | SQLite autoincrement PK                  |
| `org_id`                 | text    | Path parameter the caller supplied       |
| `retrieved_at_epoch`     | integer | `int(time.time())` at flatten time       |
| `retrieved_at_iso`       | text    | ISO 8601 string -- analyst-friendly      |

**Primary key**: `misthelper_internal_id` (auto-increment).
**Unique constraint**: `(org_id, distinct, retrieved_at_epoch)` -- one summary per
poll per `(org, distinct)` pair.
**Foreign keys**: none (top-level table).

## Bucket Rows (Entity 2: CountBucketResult)

Each element of `results[]` is an object with one required field plus dynamic
attributes determined by the request's `distinct` value.

| Field          | Type    | Required | Description                                         |
|----------------|---------|----------|-----------------------------------------------------|
| `count`        | integer | Yes      | Number of JSI inventory items in this bucket.       |
| *(additional)* | string  | No       | Dynamic property whose key is `distinct` and whose value is the bucket label (e.g. `model: "EX4400-48P"`). The OpenAPI schema declares `additionalProperties: {type: string}`. |

### MistHelper-added fields on bucket rows

| Field                    | Type    | Origin                                                        |
|--------------------------|---------|---------------------------------------------------------------|
| `misthelper_internal_id` | integer | SQLite autoincrement PK                                       |
| `org_id`                 | text    | Path parameter the caller supplied                            |
| `distinct_field`         | text    | The `distinct` query argument (e.g. `"model"`)                |
| `distinct_value`         | text    | The bucket label extracted from the dynamic property          |
| `count`                  | integer | Copied verbatim from the API row                              |
| `retrieved_at_epoch`     | integer | `int(time.time())` at flatten time (matches the summary row)  |
| `retrieved_at_iso`       | text    | ISO 8601 string                                               |
| `raw_extra_json`         | text    | JSON dump of any *other* additional properties (defensive)    |

**Primary key**: `misthelper_internal_id` (auto-increment).
**Unique constraint**: `(org_id, distinct_field, distinct_value)` -- latest count
per bucket wins (`INSERT OR REPLACE`).
**Foreign keys**: logical FK on `(org_id, distinct_field, retrieved_at_epoch)`
joining the latest matching summary row, not enforced at the SQLite layer (SQLite
foreign keys are off by default in MistHelper to keep ingest fast).

## State Transitions

N/A -- read-only endpoint. The two tables are append-then-upsert; no row-level
state machine, no archive, no soft-delete.

## SQLite DDL

```sql
-- Summary envelope: one row per (org, distinct) per poll.
CREATE TABLE IF NOT EXISTS org_jsi_inventory_count_summary (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id               TEXT    NOT NULL,
    distinct             TEXT    NOT NULL,
    total                INTEGER NOT NULL,
    "limit"              INTEGER NOT NULL,  -- quoted: SQL reserved word
    start                INTEGER NOT NULL,
    "end"                INTEGER NOT NULL,  -- quoted: SQL reserved word
    retrieved_at_epoch   INTEGER NOT NULL,
    retrieved_at_iso     TEXT    NOT NULL,
    UNIQUE (org_id, distinct, retrieved_at_epoch)
);

CREATE INDEX IF NOT EXISTS idx_jsi_count_summary_org
    ON org_jsi_inventory_count_summary (org_id);

-- Bucket counts: one row per (org, distinct_field, distinct_value).
CREATE TABLE IF NOT EXISTS org_jsi_inventory_count_results (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id              TEXT    NOT NULL,
    distinct_field      TEXT    NOT NULL,
    distinct_value      TEXT,                -- may be NULL when server omits the bucket label
    count               INTEGER NOT NULL,
    retrieved_at_epoch  INTEGER NOT NULL,
    retrieved_at_iso    TEXT    NOT NULL,
    raw_extra_json      TEXT,
    UNIQUE (org_id, distinct_field, distinct_value)
);

CREATE INDEX IF NOT EXISTS idx_jsi_count_results_org_field
    ON org_jsi_inventory_count_results (org_id, distinct_field);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (next to the existing inventory-count / JSI entries):

```python
"countOrgJsiAssetsAndContracts": {                            # operationId from OpenAPI spec
    "type": "auto_increment_with_unique",                     # no stable Mist UUID per bucket
    "primary_key": ["misthelper_internal_id"],                # synthetic PK column
    "fan_out": [                                              # endpoint writes to two tables
        {
            "table": "org_jsi_inventory_count_summary",       # envelope row
            "unique": ["org_id", "distinct", "retrieved_at_epoch"],
            "indexes": ["org_id"],
        },
        {
            "table": "org_jsi_inventory_count_results",       # bucket rows
            "unique": ["org_id", "distinct_field", "distinct_value"],
            "indexes": ["org_id", "distinct_field"],
        },
    ],
    "notes": "JSI inventory bucketed count; aggregate -- no per-bucket Mist UUID.",
},
```

If the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` schema in `MistHelper.py` does not
yet support a `fan_out` list (older single-table entries), the schema is extended in
the same PR following the existing convention used for other two-table fan-outs
(e.g. the alarms `summary` + `details` pair under spec 500).

## Volume Estimates

- **Summary**: 1 row per menu invocation. A typical operator runs the menu <=10
  times per day. Annual growth: ~3,650 rows -- trivial.
- **Bucket rows**: bounded by the request's `limit` (default 100, max 1000).
  Re-runs upsert, so steady-state size is bounded by the cardinality of the
  `distinct` field (typically <=200 for `model`, `<5` for `family`, etc.). Annual
  storage well under 1 MB.
