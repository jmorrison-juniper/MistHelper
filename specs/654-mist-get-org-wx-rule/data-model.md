# Phase 1 Data Model: getOrgWxRule

**Feature**: 654-mist-get-org-wx-rule
**Date**: 2026-07-01
**Source schema**: `documentation/api/orgs/GET_orgs_org_id_wxrules_wxrule_id.md`
(OpenAPI `Wrule` object)

## Entities Returned by the Endpoint

The endpoint returns exactly one entity: a `Wrule` (WxLAN Rule) object.

### Entity: `Wrule` (WxLAN Rule Detail)

| Field            | Type              | Notes / Constraints                                                                                          |
|------------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `id`             | string (uuid)     | **Primary key**. Stable across the lifetime of the rule. `readOnly`.                                         |
| `org_id`         | string (uuid)     | Foreign key -> `orgs.id`. `readOnly`. Present when rule is org-scoped.                                       |
| `site_id`        | string (uuid)     | Foreign key -> `sites.id`. `readOnly`. Present when the rule is anchored to a site.                          |
| `template_id`    | string (uuid)     | Foreign key -> WLAN template. Present only for Org Level WxRule.                                             |
| `for_site`       | boolean           | `readOnly`. True when the rule targets a specific site rather than the org.                                  |
| `enabled`        | boolean           | Default `true`. Whether the rule is currently active.                                                        |
| `order`          | integer (int32)   | Required in schema. `>0` values match first (higher number = higher priority). `-1` means match LAST.        |
| `action`         | string            | Enum: `allow`, `block`. Terminal action when the rule matches.                                               |
| `apply_tags`     | array[string]     | List of WxTag names / IDs applied on match.                                                                  |
| `blocked_apps`   | array[string]     | Always-blocked application keys (overrides `action`). Examples: `mist`, `all-videos`.                        |
| `src_wxtags`     | array[string]     | Required in schema. WxTag UUIDs whose members are the source scope for match.                                |
| `dst_wxtags`     | array[string]     | Destination WxTag UUIDs.                                                                                     |
| `dst_allow_wxtags` | array[string]   | Destination WxTag UUIDs explicitly allowed access.                                                           |
| `dst_deny_wxtags`  | array[string]   | Destination WxTag UUIDs explicitly denied access.                                                            |
| `created_time`   | number (epoch)    | `readOnly`. Row creation timestamp on the Mist Cloud side.                                                   |
| `modified_time`  | number (epoch)    | `readOnly`. Last upstream modification timestamp.                                                            |

### Primary Key

- **Type**: `natural_pk`
- **Columns**: `["id"]`
- **Justification**: `id` is a Mist Cloud-issued UUID guaranteed stable per rule (same
  key type used by `listOrgWxRules`).

### Foreign Keys

- `org_id`  -> logical FK to the `orgs` table (row-scoped filter; no SQLite FK
  constraint is enforced because MistHelper does not maintain a canonical org
  registry locally).
- `site_id` -> logical FK to a `sites` table row (only when populated).
- `template_id` -> logical FK to a WLAN-template row (only when populated).

## State Transitions

**N/A -- read-only endpoint.** The MistHelper menu item never mutates cloud state.
The local SQLite row lifecycle is:

- On first observation: `INSERT` new row keyed by `id`.
- On subsequent observations of the same `id`: `INSERT OR REPLACE` (upsert),
  overwriting the previous snapshot. The upstream `modified_time` field records
  when the rule was last edited on Mist; MistHelper does not track history of
  local overwrites.

## SQLite DDL

The DataExporter generates the following table on first run:

```sql
CREATE TABLE IF NOT EXISTS org_wxrule_detail (
    id              TEXT    PRIMARY KEY,     -- natural PK: Mist-issued rule UUID
    org_id          TEXT,                    -- owning organization UUID
    site_id         TEXT,                    -- owning site UUID (nullable)
    template_id     TEXT,                    -- owning WLAN template UUID (nullable)
    for_site        INTEGER,                 -- boolean 0/1
    enabled         INTEGER,                 -- boolean 0/1
    "order"         INTEGER,                 -- match priority; -1 means LAST
    action          TEXT,                    -- enum: allow / block
    apply_tags      TEXT,                    -- JSON-encoded list[str]
    blocked_apps    TEXT,                    -- JSON-encoded list[str]
    src_wxtags      TEXT,                    -- JSON-encoded list[str]
    dst_wxtags      TEXT,                    -- JSON-encoded list[str]
    dst_allow_wxtags TEXT,                   -- JSON-encoded list[str]
    dst_deny_wxtags TEXT,                    -- JSON-encoded list[str]
    created_time    REAL,                    -- epoch seconds
    modified_time   REAL,                    -- epoch seconds
    misthelper_run_ts REAL                   -- local ingest timestamp (added by DataExporter)
);

CREATE INDEX IF NOT EXISTS idx_org_wxrule_detail_org_id
    ON org_wxrule_detail (org_id);
CREATE INDEX IF NOT EXISTS idx_org_wxrule_detail_site_id
    ON org_wxrule_detail (site_id);
CREATE INDEX IF NOT EXISTS idx_org_wxrule_detail_template_id
    ON org_wxrule_detail (template_id);
CREATE INDEX IF NOT EXISTS idx_org_wxrule_detail_order
    ON org_wxrule_detail ("order");
```

Notes:
- `order` is quoted because it is a reserved SQLite keyword.
- Array fields are serialized as JSON strings on write to preserve fidelity; the
  same encoding is used by the existing `listOrgWxRules` output.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Insert the following key/value pair into the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (adjacent to the existing `listOrgWxRules` entry at
line ~3969):

```python
"getOrgWxRule": {                                # operationId from mistapi SDK
    "type": "natural_pk",                        # Mist issues stable UUID for each rule
    "primary_key": ["id"],                       # single-column PK; same as list endpoint
    "indexes": [                                 # accelerate common analyst filters
        "org_id",                                # rules scoped to an organization
        "site_id",                               # rules anchored to a specific site
        "template_id",                           # rules attached to a WLAN template
        "order",                                 # match-priority ordering scans
    ],
    "unique_constraints": [],                    # PK covers uniqueness
    "description": "Detail of a single organization WxLAN rule",  # human-readable audit hint
},
```
