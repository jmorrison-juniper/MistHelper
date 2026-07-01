# Phase 1 Data Model: getOrgService

**Feature**: 637-mist-get-org-service
**Date**: 2026-06-30

## Entity Inventory

The endpoint returns exactly one entity: **Service** (an application definition used by Mist
Gateway service policies and security rules).

### Entity: Service

Fields extracted from the 200-response schema in
`documentation/api/orgs/GET_orgs_org_id_services_service_id.md`:

| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| `id` | string (uuid) | No | **Primary key.** API-provided, `readOnly`, globally unique in the org. |
| `org_id` | string (uuid) | No | **Foreign key** -> logical `orgs.id` (org table). `readOnly`. |
| `name` | string | Yes | Human-readable service name. |
| `description` | string | Yes | Free-text description. |
| `type` | string | Yes | Enum: `app_categories`, `apps`, `custom`, `urls`. |
| `traffic_type` | string | Yes | Default `data_best_effort`; values from listTrafficTypes. |
| `traffic_class` | string | Yes | Enum when traffic_type=custom: `best_effort`, `high`, `low`, `medium`. |
| `failover_policy` | string | Yes | Enum: `non_revertible`, `none`, `revertible`. |
| `addresses` | JSON array<string> | Yes | IPv4/IPv6 subnets when type=custom. Stored as JSON text in SQLite. |
| `hostnames` | JSON array<string> | Yes | Web-filter hostnames when type=custom. JSON text. |
| `urls` | JSON array<string> | Yes | URL list when type=urls. JSON text. |
| `apps` | JSON array<string> | Yes | Application list when type=apps. JSON text. |
| `app_categories` | JSON array<string> | Yes | Category list when type=app_categories. JSON text. |
| `app_subcategories` | JSON array<string> | Yes | Sub-category list. JSON text. |
| `specs` | JSON array<object> | Yes | Array of `{port_range, protocol}` objects when type=custom. JSON text. |
| `dscp` | JSON object | Yes | SSR-only DSCP value or variable. JSON text. |
| `max_jitter` | JSON object | Yes | SSR-only jitter target. JSON text. |
| `max_latency` | JSON object | Yes | SSR-only latency target. JSON text. |
| `max_loss` | JSON object | Yes | SSR-only loss target. JSON text. |
| `client_limit_up` | integer | Yes | 0..107374182. Per-client uplink cap. |
| `client_limit_down` | integer | Yes | 0..107374182. Per-client downlink cap. |
| `service_limit_up` | integer | Yes | 0..107374182. Aggregate uplink cap. |
| `service_limit_down` | integer | Yes | 0..107374182. Aggregate downlink cap. |
| `sle_enabled` | boolean | Yes | Whether SLE measurement is on. Default false. |
| `ssr_relaxed_tcp_state_enforcement` | boolean | Yes | SSR flag, default false. |
| `created_time` | number (epoch) | Yes | `readOnly`. |
| `modified_time` | number (epoch) | Yes | `readOnly`. |

**Nested entity: service_spec** (inside `specs` array). Flattened into a JSON blob rather than
promoted to its own table because it has no independent identity and no relationships beyond its
parent Service row.

## Relationships

- `Service.org_id` -> logical `orgs.id` (not enforced by SQLite FK constraint; parent org table
  is not always populated in this DB).
- Downstream, `Service.id` is referenced by `service_policy.services[]` (owned by
  `listOrgServicePolicies`), but that reverse edge is maintained by the service-policies
  endpoint, not here.

## State Transitions

**N/A -- read-only endpoint.** This is a GET. State is owned by the Mist API. MistHelper only
mirrors the current snapshot into local storage via `INSERT OR REPLACE`.

## SQLite DDL

The `org_services` table is created once by `DataExporter` on first write. This endpoint reuses
it (no migration). Reference DDL (for documentation only -- actual creation is handled by the
exporter's schema-generation path, which introspects the PK strategy):

```sql
-- Table shared by listOrgServices (menu 4) and getOrgService (menu 195).
CREATE TABLE IF NOT EXISTS org_services (
    id           TEXT PRIMARY KEY,        -- API UUID, natural key from getOrgService.id
    org_id       TEXT NOT NULL,           -- parent org UUID, indexed for org-scoped queries
    name         TEXT,                    -- human-readable service label
    description  TEXT,                    -- operator-supplied notes
    type         TEXT,                    -- enum: app_categories | apps | custom | urls
    traffic_type TEXT,                    -- traffic classification for QoS
    traffic_class TEXT,                   -- best_effort | high | low | medium
    failover_policy TEXT,                 -- non_revertible | none | revertible
    addresses    TEXT,                    -- JSON array of CIDR strings
    hostnames    TEXT,                    -- JSON array of web-filter hostnames
    urls         TEXT,                    -- JSON array of URLs
    apps         TEXT,                    -- JSON array of app IDs
    app_categories TEXT,                  -- JSON array of category names
    app_subcategories TEXT,               -- JSON array of sub-category names
    specs        TEXT,                    -- JSON array of {port_range, protocol}
    dscp         TEXT,                    -- JSON object, SSR only
    max_jitter   TEXT,                    -- JSON object, SSR only
    max_latency  TEXT,                    -- JSON object, SSR only
    max_loss     TEXT,                    -- JSON object, SSR only
    client_limit_up   INTEGER,            -- bytes/sec cap per client uplink
    client_limit_down INTEGER,            -- bytes/sec cap per client downlink
    service_limit_up  INTEGER,            -- bytes/sec cap aggregate uplink
    service_limit_down INTEGER,           -- bytes/sec cap aggregate downlink
    sle_enabled  INTEGER,                 -- boolean stored as 0/1
    ssr_relaxed_tcp_state_enforcement INTEGER,  -- boolean stored as 0/1
    created_time REAL,                    -- epoch seconds, API readOnly
    modified_time REAL,                   -- epoch seconds, API readOnly
    ingested_at  REAL DEFAULT (strftime('%s','now'))  -- MistHelper ingestion timestamp
);

CREATE INDEX IF NOT EXISTS idx_org_services_org_id ON org_services(org_id);   -- fast org-scoped scan
CREATE INDEX IF NOT EXISTS idx_org_services_name   ON org_services(name);     -- fast name search
CREATE INDEX IF NOT EXISTS idx_org_services_type   ON org_services(type);     -- filter by service type
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add to `MistHelper.py` `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict (currently line ~4768 where
`listOrgServices` lives, immediately before or after that entry to keep sibling operations
adjacent):

```python
"getOrgService": {                                 # Single-service point read (menu 195).
    "type": "natural_pk",                          # id is API-provided UUID, globally unique.
    "primary_key": ["id"],                         # matches listOrgServices strategy for shared table.
    "indexes": ["org_id", "name", "type"],         # standard lookup dimensions for services.
    "unique_constraints": [],                      # id PK already enforces uniqueness.
    "description": "Single Org Service definition by UUID",  # surfaced by DataExporter diagnostics.
},
```
