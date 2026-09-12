# Phase 1 Data Model: getOrgLicensesSummary

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Source**: `documentation/api/orgs/GET_orgs_org_id_licenses.md`

## Overview

The endpoint returns a single composite JSON object with two arrays
(`licenses[]`, `amendments[]`) and four maps (`entitled`, `fully_loaded`,
`summary`, `usages`). The flatten step turns the composite object into four
logical row sets, each persisted to its own table. All fields are read-only
per the OpenAPI schema; there are no state transitions to model.

## Entities

### Entity 1: `license_sub` (subscription)

Source: `response.licenses[]`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | string (UUID) | Subscription UUID. **Primary key.** Stable across runs. |
| `org_id` | string (UUID) | Owning org. **Foreign key** -> `orgs.id`. Indexed. |
| `type` | string | License type code (e.g. `SUB-MAN`). Indexed. |
| `subscription_id` | string | External subscription identifier. |
| `order_id` | string | External order identifier. |
| `quantity` | integer | Total devices entitled under this subscription. |
| `remaining_quantity` | integer | Unconsumed devices on this subscription. |
| `start_time` | integer (epoch s) | License term start. |
| `end_time` | integer (epoch s) | License term end. |
| `created_time` | number (epoch s) | When Mist created the record. |
| `modified_time` | number (epoch s) | Last modification time. |

**State transitions**: N/A -- read-only endpoint.
**Validation**: `id` must be a UUID; `start_time` <= `end_time` when both
present; `remaining_quantity` <= `quantity` when both present (validation is
documentary only, not enforced by the flatten step).

### Entity 2: `license_amendment`

Source: `response.amendments[]`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | string (UUID) | Amendment UUID. **Primary key.** Stable across runs. |
| `org_id` | string (UUID) | Owning org (injected by flatten step). **Foreign key** -> `orgs.id`. Indexed. |
| `subscription_id` | string | Subscription the amendment applies to. Indexed. |
| `type` | string | License type code the amendment grants/adjusts. |
| `quantity` | integer | Quantity delta from the amendment. |
| `start_time` | integer (epoch s) | Amendment term start. |
| `end_time` | integer (epoch s) | Amendment term end. |
| `created_time` | number (epoch s) | When Mist created the amendment. |
| `modified_time` | number (epoch s) | Last modification time. |

**State transitions**: N/A -- read-only endpoint.

### Entity 3: `license_summary_count`

Source: `response.summary` map. Flatten step iterates `summary.items()` and
emits one row per `(license_type, count)` pair.

| Field | Type | Notes |
|-------|------|-------|
| `org_id` | string (UUID) | Owning org (injected by flatten step). Part of composite PK. **Foreign key** -> `orgs.id`. |
| `license_type` | string | License type code (e.g. `SUB-MAN`). Part of composite PK. |
| `consumed_count` | integer | Number of licenses of this type currently consumed. |
| `snapshot_time` | integer (epoch s) | Wall-clock epoch at fetch time (injected by flatten step). |

**State transitions**: N/A -- snapshot replaced on each upsert.

### Entity 4: `license_usage_count`

Source: `response.entitled`, `response.fully_loaded`, and `response.usages`
maps. Flatten step stacks all three into one table with a `metric` column
that discriminates the source map.

| Field | Type | Notes |
|-------|------|-------|
| `org_id` | string (UUID) | Owning org (injected by flatten step). Part of composite PK. **Foreign key** -> `orgs.id`. |
| `license_type` | string | License type code (e.g. `SUB-MAN`). Part of composite PK. |
| `metric` | string | One of `entitled`, `fully_loaded`, `usages`. Part of composite PK. |
| `value` | integer | Numeric value from the source map. |
| `snapshot_time` | integer (epoch s) | Wall-clock epoch at fetch time (injected by flatten step). |

**State transitions**: N/A -- snapshot replaced on each upsert.

## SQLite DDL

```sql
-- Created automatically by DataExporter on first run.
-- Shown here for reviewer reference and for ArangoDB schema mirroring.

CREATE TABLE IF NOT EXISTS org_licenses_subscriptions (
    id                  TEXT PRIMARY KEY,                -- subscription UUID (natural)
    org_id              TEXT NOT NULL,                   -- owning org UUID
    type                TEXT,                            -- license type code (e.g. SUB-MAN)
    subscription_id     TEXT,                            -- external subscription identifier
    order_id            TEXT,                            -- external order identifier
    quantity            INTEGER,                         -- total entitled count
    remaining_quantity  INTEGER,                         -- unconsumed count
    start_time          INTEGER,                         -- license term start (epoch s)
    end_time            INTEGER,                         -- license term end (epoch s)
    created_time        REAL,                            -- Mist record creation time
    modified_time       REAL                             -- Mist record modification time
);
CREATE INDEX IF NOT EXISTS idx_org_licenses_subs_org  ON org_licenses_subscriptions(org_id);
CREATE INDEX IF NOT EXISTS idx_org_licenses_subs_type ON org_licenses_subscriptions(type);

CREATE TABLE IF NOT EXISTS org_licenses_amendments (
    id              TEXT PRIMARY KEY,                    -- amendment UUID (natural)
    org_id          TEXT NOT NULL,                       -- owning org UUID
    subscription_id TEXT,                                -- amended subscription
    type            TEXT,                                -- license type code
    quantity        INTEGER,                             -- quantity delta
    start_time      INTEGER,                             -- amendment term start (epoch s)
    end_time        INTEGER,                             -- amendment term end (epoch s)
    created_time    REAL,                                -- Mist record creation time
    modified_time   REAL                                 -- Mist record modification time
);
CREATE INDEX IF NOT EXISTS idx_org_licenses_amend_org ON org_licenses_amendments(org_id);
CREATE INDEX IF NOT EXISTS idx_org_licenses_amend_sub ON org_licenses_amendments(subscription_id);

CREATE TABLE IF NOT EXISTS org_licenses_summary_counts (
    org_id          TEXT NOT NULL,                       -- owning org UUID
    license_type    TEXT NOT NULL,                       -- license type code
    consumed_count  INTEGER,                             -- currently consumed count
    snapshot_time   INTEGER,                             -- fetch wall-clock epoch s
    PRIMARY KEY (org_id, license_type)                   -- composite natural identity
);

CREATE TABLE IF NOT EXISTS org_licenses_usage_counts (
    org_id          TEXT NOT NULL,                       -- owning org UUID
    license_type    TEXT NOT NULL,                       -- license type code
    metric          TEXT NOT NULL,                       -- entitled | fully_loaded | usages
    value           INTEGER,                             -- numeric value from source map
    snapshot_time   INTEGER,                             -- fetch wall-clock epoch s
    PRIMARY KEY (org_id, license_type, metric)           -- composite natural identity
);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

```python
# Add to the ENDPOINT_PRIMARY_KEY_STRATEGIES dictionary in MistHelper.py
# (near line ~1672, alphabetical by operationId within its cluster).
"getOrgLicensesSummary": {                                 # one operationId, four output tables
    "type": "multi_table",                                 # composite endpoint produces multiple row sets
    "child_tables": {                                      # one entry per logical row set
        "org_licenses_subscriptions": {                    # licenses[] -> stable UUID
            "type": "natural_pk",                          # use API-provided UUID
            "primary_key": ["id"],                         # subscription UUID
            "indexes": ["org_id", "type"],                 # common query patterns
        },
        "org_licenses_amendments": {                       # amendments[] -> stable UUID
            "type": "natural_pk",                          # use API-provided UUID
            "primary_key": ["id"],                         # amendment UUID
            "indexes": ["org_id", "subscription_id"],      # join to subscriptions
        },
        "org_licenses_summary_counts": {                   # summary map -> business identity
            "type": "composite_pk",                        # no stable UUID per map entry
            "primary_key": ["org_id", "license_type"],     # one row per (org, type)
            "indexes": ["license_type"],                   # cross-org rollup queries
        },
        "org_licenses_usage_counts": {                     # entitled/fully_loaded/usages stacked
            "type": "composite_pk",                        # no stable UUID per map entry
            "primary_key": ["org_id", "license_type", "metric"],  # discriminate by metric name
            "indexes": ["license_type", "metric"],         # filter by metric or by type
        },
    },
}
```
