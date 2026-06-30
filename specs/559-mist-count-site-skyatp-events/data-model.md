# Phase 1 Data Model: countSiteSkyatpEvents

**Feature**: 559-mist-count-site-skyatp-events
**Source schema**: `documentation/api/sites/GET_sites_site_id_skyatp_events_count.md`
(200 response, `Result of Count`).

## Entities Returned by the Endpoint

### Entity 1: SkyatpCountEnvelope

Top-level wrapper around the bucket array. Captures the query that produced the
counts. Persisted once per API call by inlining its fields onto every bucket row
(denormalised wide-table pattern used elsewhere in MistHelper, e.g.
`org_licenses_summary`).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| distinct | string | Yes | Attribute used to bucket the counts (e.g. `type`, `threat_level`). |
| start | integer (epoch seconds) | Yes | Start of the time window the count covers. |
| end | integer (epoch seconds) | Yes | End of the time window. |
| limit | integer | Yes | Server-side cap on the number of buckets returned (default 100). |
| total | integer | Yes | Sum of all bucket counts across the window. |
| results | array of CountBucket | Yes | Bucket list -- see Entity 2. |

### Entity 2: CountBucket (child of envelope)

One element of the `results` array. The bucket's identity is the value of the
`distinct` attribute -- exposed via `additionalProperties` (a single dynamic string
key whose name equals the `distinct` value chosen by the caller, and whose value is
the bucket label).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| count | integer | Yes | Number of Sky ATP events in this bucket within the window. |
| `<distinct-name>` | string | Yes (dynamic) | The bucket label, e.g. `type="mw"` when `distinct=type`. Captured into the generic column `bucket_value` after flattening. |

### Persistence Shape (Flattened Row)

Each bucket is flattened into one wide row that carries both the envelope fields and
the bucket's own values. This avoids a parent/child two-table schema and matches the
DataExporter contract (one filename = one CSV = one SQLite table).

| Column | Type | Source |
|--------|------|--------|
| misthelper_internal_id | INTEGER | Auto-increment primary key (synthetic). |
| site_id | TEXT | Path parameter the user supplied. |
| distinct | TEXT | Envelope `distinct`. |
| bucket_value | TEXT | Value of the dynamic `additionalProperties` field. NULL if absent. |
| count | INTEGER | Bucket `count`. |
| start_epoch | INTEGER | Envelope `start`. |
| end_epoch | INTEGER | Envelope `end`. |
| limit | INTEGER | Envelope `limit`. |
| total | INTEGER | Envelope `total`. |
| fetched_at | TEXT (ISO 8601 UTC) | MistHelper insertion timestamp. |

**Foreign keys**: `site_id` references `sites.id` when the `sites` table exists in
the local SQLite (it is created the first time menu 1-7 is run). No hard FK
constraint is declared (consistent with the rest of MistHelper's local schema, which
relies on soft references for cross-table joins).

## State Transitions

**N/A -- read-only endpoint.** The data model is append-with-upsert. Each run of the
menu item performs an `INSERT OR REPLACE` against the unique constraint
`(site_id, distinct, bucket_value, start_epoch, end_epoch)`, so re-running with the
same window updates `count` and `fetched_at` in place; running with a new window
inserts a new row.

## SQLite DDL Snippet

```sql
CREATE TABLE IF NOT EXISTS site_skyatp_events_count (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id        TEXT    NOT NULL,
    distinct       TEXT    NOT NULL,
    bucket_value   TEXT,
    count          INTEGER NOT NULL,
    start_epoch    INTEGER NOT NULL,
    end_epoch      INTEGER NOT NULL,
    limit          INTEGER,
    total          INTEGER,
    fetched_at     TEXT    NOT NULL,
    UNIQUE (site_id, distinct, bucket_value, start_epoch, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_site_skyatp_events_count_site
    ON site_skyatp_events_count (site_id);
CREATE INDEX IF NOT EXISTS idx_site_skyatp_events_count_distinct
    ON site_skyatp_events_count (distinct);
CREATE INDEX IF NOT EXISTS idx_site_skyatp_events_count_start
    ON site_skyatp_events_count (start_epoch);
```

The DDL is emitted automatically by `DatabaseSchemaUtils` from the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry below; it is shown here for reference only
and is not hand-written into MistHelper.py.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Dict Entry

Append the following entry inside the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in
`MistHelper.py` (currently anchored near line 3353 next to the sibling
`searchSiteSkyatpEvents` entry):

```python
"countSiteSkyatpEvents": {                                       # New PK strategy for menu 195
    "type": "auto_increment_with_unique",                        # Buckets have no API-issued UUID
    "primary_key": ["misthelper_internal_id"],                   # Synthetic autoincrement row id
    "unique_constraints": [                                      # Logical identity of a bucket row
        ["site_id", "distinct", "bucket_value", "start_epoch", "end_epoch"]
    ],
    "indexes": ["site_id", "distinct", "start_epoch"],           # Common query columns
    "description": "Site Sky ATP event counts bucketed by distinct attribute",
},
```

Every executable line in this entry carries an inline comment per Constitution
Principle VI. The structure matches the existing `getOrgLicensesSummary` and
`getOrgLicensesBySite` entries (hybrid auto-increment + unique).
