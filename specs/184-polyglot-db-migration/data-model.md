# Data Model: Polyglot Database Migration

**Feature**: 184-polyglot-db-migration | **Date**: 2026-04-20

## ArangoDB Collections (Document)

### Sites

| Field | Type | Source | Notes |
| - | - | - | - |
| `_key` | string | Mist API `id` (UUID) | Natural PK |
| `org_id` | string | API | Indexed |
| `name` | string | API | Indexed |
| `country_code` | string | API | Indexed |
| `timezone` | string | API | |
| `address` | string | API | |
| `latlng` | object | API | `{lat, lng}` |
| `_misthelper_updated_at` | integer | System | Unix epoch of last upsert |
| `_misthelper_deleted_at` | integer | System | Null if active; epoch if soft-deleted |

**Validation**: `_key` must be a valid UUID (max 254 bytes). `org_id` required.

### Devices

| Field | Type | Source | Notes |
| - | - | - | - |
| `_key` | string | Mist API `id` (UUID) | Natural PK |
| `org_id` | string | API | Indexed |
| `site_id` | string | API | Indexed, foreign ref to Sites |
| `name` | string | API | Indexed |
| `mac` | string | API | Indexed |
| `serial` | string | API | |
| `model` | string | API | |
| `type` | string | API | `ap`, `switch`, `gateway` |
| `version` | string | API | Firmware version |
| `_misthelper_updated_at` | integer | System | Unix epoch |
| `_misthelper_deleted_at` | integer | System | Soft-delete timestamp |

**Validation**: `_key` must be valid UUID. `site_id` must reference existing Sites collection.

### Templates

Covers AP templates, network templates, RF templates, gateway templates, device profiles.

| Field | Type | Source | Notes |
| - | - | - | - |
| `_key` | string | Mist API `id` (UUID) | Natural PK |
| `org_id` | string | API | Indexed |
| `name` | string | API | Indexed |
| `template_type` | string | System | `ap`, `network`, `rf`, `gateway`, `device_profile` |
| `body` | object | API | Full template configuration (flattened) |
| `_misthelper_updated_at` | integer | System | |
| `_misthelper_deleted_at` | integer | System | |

### ConfigSnapshots

Versioned configuration snapshots stored on change and periodically.

| Field | Type | Source | Notes |
| - | - | - | - |
| `_key` | string | System | Auto-generated (UUID or hash) |
| `entity_type` | string | System | `site`, `wlan`, `template`, etc. |
| `entity_id` | string | System | Reference to source entity `_key` |
| `org_id` | string | API | Indexed |
| `timestamp` | integer | System | Unix epoch when snapshot was taken |
| `config_hash` | string | System | SHA-256 of config body (dedup) |
| `config_body` | object | System | Full config at snapshot time |
| `trigger` | string | System | `webhook`, `periodic`, `manual` |
| `_misthelper_updated_at` | integer | System | |

**Validation**: `config_hash` used to skip duplicate snapshots. `entity_id` must exist in the referenced entity collection.

### Generic Document Collections

All other `natural_pk` and `auto_increment_with_unique` entities follow this pattern:

| Field | Type | Source | Notes |
| - | - | - | - |
| `_key` | string | Mist API `id` or auto-generated | PK |
| `org_id` | string | API | Indexed |
| All API fields | varies | API | Flattened via `DataProcessingUtils.flatten_dict()` |
| `_misthelper_updated_at` | integer | System | |
| `_misthelper_deleted_at` | integer | System | |

Applies to: WLANs, PSKs, Networks, Services, Webhooks, Admins, API Tokens, Licenses, Alarms, Events, Audit Logs.

## ArangoDB Collections (Edge)

### OrgContainsSite

| Field | Type | Notes |
| - | - | - |
| `_from` | string | `orgs/<org_id>` |
| `_to` | string | `sites/<site_id>` |

### SiteContainsDevice

| Field | Type | Notes |
| - | - | - |
| `_from` | string | `sites/<site_id>` |
| `_to` | string | `devices/<device_id>` |

### TemplateAssignedToSite

| Field | Type | Notes |
| - | - | - |
| `_from` | string | `templates/<template_id>` |
| `_to` | string | `sites/<site_id>` |

### DeviceHasPort

| Field | Type | Notes |
| - | - | - |
| `_from` | string | `devices/<device_id>` |
| `_to` | string | `ports/<port_id>` |

### Graph Definition

```
Graph: "mist_network_topology"
Vertex Collections: orgs, sites, devices, templates, ports
Edge Definitions:
  - OrgContainsSite: orgs → sites
  - SiteContainsDevice: sites → devices
  - TemplateAssignedToSite: templates → sites
  - DeviceHasPort: devices → ports
```

## Redis TimeSeries Keys

### Key Naming Convention

```
{metric_category}:{entity_id}:{metric_name}
```

Examples:
- `device_stats:ap-uuid-123:cpu_usage`
- `device_stats:ap-uuid-123:memory_usage`
- `port_stats:switch-uuid:ge-0/0/1:traffic_in`
- `sle:site-uuid-456:successful_connect`
- `client_stats:site-uuid:client_count`

### Labels (applied to every key)

| Label | Source | Purpose |
| - | - | - |
| `org_id` | API | Organization filter |
| `site_id` | API | Site filter |
| `device_id` | API | Device filter (if applicable) |
| `metric_name` | System | Metric type filter |
| `metric_category` | System | Category filter (`device_stats`, `port_stats`, `sle`, `client_stats`) |

### Downsampling Tiers

| Tier | Granularity | Retention | Aggregation | Destination Key Suffix |
| - | - | - | - | - |
| Raw | As ingested | 7 days | N/A | (source key) |
| Hourly | 1 hour | 90 days | `avg` | `:avg_1h` |
| Daily | 1 day | 365 days | `avg` | `:avg_1d` |

Compaction rules are created automatically when a new TimeSeries key is created.

### Retention Policy Config

| Setting | Source | Default |
| - | - | - |
| `REDIS_RAW_RETENTION_DAYS` | `.env` | `7` |
| `REDIS_HOURLY_RETENTION_DAYS` | `.env` | `90` |
| `REDIS_DAILY_RETENTION_DAYS` | `.env` | `365` |
| `ARANGO_MAX_STORAGE_GB` | `.env` | `50` |
| `RETENTION_CHECK_INTERVAL_HOURS` | `.env` | `6` |

## State Transitions

### Entity Lifecycle

```
[Not Exists] → INSERT → [Active]
[Active] → UPSERT (data changed) → [Active] (updated_at refreshed)
[Active] → Removed from Mist API → [Soft-Deleted] (deleted_at set)
[Soft-Deleted] → Re-appears in Mist API → [Active] (deleted_at cleared)
[Soft-Deleted] → Retention rollover → [Purged] (document removed)
```

### Backend Availability States

```
[All Backends Up] → Normal operation (ArangoDB + Redis + CSV)
[ArangoDB Down] → Degraded mode (Redis + CSV only, log warning)
[Redis Down] → Degraded mode (ArangoDB + CSV only, log warning)
[Both Down] → CSV-only mode (log error, no crash)
[Standalone Mode] → CSV-only (no connection attempts)
```
