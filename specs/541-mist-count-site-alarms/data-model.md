# Phase 1 Data Model: countSiteAlarms

This document captures the entities returned by
`GET /api/v1/sites/{site_id}/alarms/count`, the SQLite DDL that persists them, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration that drives clean upserts.

## Entities returned by the endpoint

The 200 response body (per
`documentation/api/sites/GET_sites_site_id_alarms_count.md`) is a single JSON object
with the shape:

```json
{
  "distinct": "type",
  "start": 1711000000,
  "end":   1711086400,
  "limit": 100,
  "total": 232,
  "results": [
    { "count": 120, "type": "rogue_client" },
    { "count":  80, "type": "device_disconnected" },
    { "count":  32, "type": "auth_failure" }
  ]
}
```

The payload flattens into two logical entities:

### Entity A: `SiteAlarmCountSummary` (one row per call)

| Field      | Type     | Source                          | Notes                                     |
|------------|----------|---------------------------------|-------------------------------------------|
| site_id    | string   | path parameter (added on flatten) | UUID; identifies the scope of the count |
| distinct   | string   | response.distinct               | Grouping field that was applied           |
| start      | integer  | response.start                  | Epoch seconds, window start               |
| end        | integer  | response.end                    | Epoch seconds, window end                 |
| limit      | integer  | response.limit                  | Effective limit applied                   |
| total      | integer  | response.total                  | Sum of all bucket counts                  |
| fetched_at | integer  | client-side                     | Epoch seconds at fetch time (provenance)  |

**Primary key**: composite `(site_id, distinct, start, end)`.
**Foreign keys**: `site_id` references `org_sites.id` (existing MistHelper table).

### Entity B: `SiteAlarmCountBucket` (one row per item in `results[]`)

| Field          | Type    | Source                          | Notes                                            |
|----------------|---------|---------------------------------|--------------------------------------------------|
| site_id        | string  | path parameter (added on flatten) | UUID; bucket scope                              |
| distinct       | string  | response.distinct               | Echoed for join convenience                       |
| distinct_value | string  | results[*].<distinct field>     | The bucket key value (e.g. `rogue_client`)        |
| count          | integer | results[*].count                | Bucket size                                       |
| start          | integer | response.start                  | Echoed window start                               |
| end            | integer | response.end                    | Echoed window end                                 |
| fetched_at     | integer | client-side                     | Epoch seconds at fetch time (provenance)          |

Because the OpenAPI schema marks the bucket object with
`additionalProperties: {type: string}`, the bucket key column (`distinct_value`) is
typed as TEXT regardless of which Mist field the user picks for `distinct`.

**Primary key**: composite `(site_id, distinct, distinct_value, start, end)`.
**Foreign keys**: `(site_id, distinct, start, end)` references
`site_alarms_count_summary` -- not enforced by SQLite by default, but documented for
downstream consumers and ArangoDB graph edge generation.

## State transitions

**N/A -- read-only endpoint.** The records are observations of a counter at a point in
time. Each rerun for the same `(site_id, distinct, start, end)` window upserts the
summary row and refreshes the bucket rows for that window. Older windows are retained
in the table for historical comparison.

## SQLite DDL

```sql
-- Summary: one row per call
CREATE TABLE IF NOT EXISTS site_alarms_count_summary (
    site_id     TEXT    NOT NULL,
    distinct    TEXT    NOT NULL,
    start       INTEGER NOT NULL,
    end         INTEGER NOT NULL,
    limit       INTEGER,
    total       INTEGER,
    fetched_at  INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_site_alarms_count_summary_site
    ON site_alarms_count_summary (site_id);

CREATE INDEX IF NOT EXISTS idx_site_alarms_count_summary_fetched
    ON site_alarms_count_summary (fetched_at);

-- Buckets: one row per results[] item
CREATE TABLE IF NOT EXISTS site_alarms_count_buckets (
    site_id        TEXT    NOT NULL,
    distinct       TEXT    NOT NULL,
    distinct_value TEXT    NOT NULL,
    count          INTEGER NOT NULL,
    start          INTEGER NOT NULL,
    end            INTEGER NOT NULL,
    fetched_at     INTEGER NOT NULL,
    PRIMARY KEY (site_id, distinct, distinct_value, start, end)
);

CREATE INDEX IF NOT EXISTS idx_site_alarms_count_buckets_site
    ON site_alarms_count_buckets (site_id);

CREATE INDEX IF NOT EXISTS idx_site_alarms_count_buckets_distinct
    ON site_alarms_count_buckets (distinct, distinct_value);
```

`DataExporter.write_with_format_selection()` issues `INSERT OR REPLACE` against both
tables, so reruns upsert cleanly without violating the composite primary keys.

## ENDPOINT_PRIMARY_KEY_STRATEGIES registration

Two entries are added under the operationId `countSiteAlarms` -- one per flattened
table. The DataExporter uses the `api_function_name` keyword to disambiguate which
strategy applies to the file it is writing.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteAlarms"] = {  # New operationId entry
    "summary": {                                          # Summary table strategy
        "type": "composite_pk",                           # Composite PK -> INSERT OR REPLACE upsert
        "primary_key": ["site_id", "distinct", "start", "end"],  # Uniquely identifies a window
        "indexes": ["site_id", "fetched_at"],            # Helpers for join + retention queries
        "table": "site_alarms_count_summary",             # SQLite target table
    },
    "buckets": {                                          # Bucket table strategy
        "type": "composite_pk",                           # Composite PK -> INSERT OR REPLACE upsert
        "primary_key": [                                  # Bucket uniqueness across reruns
            "site_id",                                    # Site scope
            "distinct",                                   # Grouping field used
            "distinct_value",                             # Bucket key value
            "start",                                      # Window start
            "end",                                        # Window end
        ],
        "indexes": ["site_id", "distinct", "distinct_value"],  # Common query patterns
        "table": "site_alarms_count_buckets",             # SQLite target table
    },
}
```

When the implementation lands in `MistHelper.py` the dict insertion above is placed
alphabetically inside the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` constant (near
line ~1672), preserving the file's current 5-Item-Rule structure.
