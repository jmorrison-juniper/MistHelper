# API Contract: Sync & Inventory

**Prefix**: `/api/v1/sync`
**Maps to**: US-1 (time-travel / inventory sync), US-6 (drift detection), FR-001-004,
FR-011, FR-024

---

## Endpoints

### GET /api/v1/sync/status

Get current sync state for an organization.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `entity_type` | string | No | Filter: device, site, wlan, network, etc. |
| `sync_state` | string | No | Filter: synced, stale, error |

**Response** (200 OK):
```json
{
  "data": {
    "org_id": "abc-123",
    "overall_state": "synced",
    "last_full_sync": "2026-03-06T01:00:00Z",
    "next_poll_at": "2026-03-06T01:05:00Z",
    "entity_counts": {
      "device": {"total": 450, "synced": 448, "stale": 2, "error": 0},
      "site": {"total": 30, "synced": 30, "stale": 0, "error": 0},
      "wlan": {"total": 12, "synced": 12, "stale": 0, "error": 0}
    }
  }
}
```

---

### GET /api/v1/sync/ledger

List sync ledger entries (detailed sync history).

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `entity_type` | string | No | Filter by entity type |
| `outcome` | string | No | Filter: ok, partial, error |
| `from`, `to` | ISO 8601 | No | Time range |
| `page`, `per_page` | int | No | Pagination |

**Response** (200 OK):
```json
{
  "data": [
    {
      "ledger_id": "ledger-uuid",
      "org_id": "abc-123",
      "trigger": "webhook",
      "entity_type": "device",
      "entities_fetched": 450,
      "entities_changed": 3,
      "outcome": "ok",
      "duration_ms": 2340,
      "started_at": "2026-03-06T01:00:00Z",
      "completed_at": "2026-03-06T01:00:02Z"
    }
  ]
}
```

---

### POST /api/v1/sync/trigger

Force an immediate sync for an organization or entity type.

**Request**:
```json
{
  "org_id": "abc-123",
  "entity_types": ["device", "wlan"]
}
```

**Response** (202 Accepted):
```json
{
  "data": {
    "task_id": "celery-task-uuid",
    "status": "queued",
    "estimated_duration_seconds": 15
  }
}
```

---

## Inventory Endpoints

### GET /api/v1/inventory/orgs

List cached organizations with summary stats.

**Response** (200 OK):
```json
{
  "data": [
    {
      "org_id": "abc-123",
      "name": "Acme Corp",
      "msp_id": "msp-uuid",
      "site_count": 30,
      "device_count": 450,
      "last_synced_at": "2026-03-06T01:00:00Z"
    }
  ]
}
```

**Performance**: SC-001 requires <3s for 100-org summary.

---

### GET /api/v1/inventory/sites

List cached sites with device counts.

**Query Parameters**:
- `org_id` (UUID, required)
- `name` (string, optional — partial match)
- `country_code` (string, optional)
- `page`, `per_page`

---

### GET /api/v1/inventory/devices

List cached devices with status.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `site_id` | UUID | No | Filter by site |
| `type` | string | No | Filter: ap, switch, gateway |
| `model` | string | No | Filter by device model |
| `firmware_version` | string | No | Filter by firmware |
| `status` | string | No | Filter: connected, disconnected |
| `page`, `per_page` | int | No | Pagination |

**Response** (200 OK):
```json
{
  "data": [
    {
      "device_id": "device-uuid",
      "org_id": "abc-123",
      "site_id": "site-uuid",
      "name": "AP-Lobby-01",
      "type": "ap",
      "model": "AP45",
      "serial": "A1234567890",
      "mac": "aa:bb:cc:dd:ee:ff",
      "firmware_version": "0.14.29388",
      "status": "connected",
      "ip_address": "10.1.1.100",
      "last_seen": "2026-03-06T01:00:00Z",
      "uptime_seconds": 864000,
      "last_config_synced_at": "2026-03-06T00:55:00Z"
    }
  ]
}
```

---

### GET /api/v1/inventory/devices/{device_id}

Get detailed device record with latest config snapshot.

---

## Drift Alerts

### GET /api/v1/drift/alerts

List drift alerts (FR-011).

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `alert_type` | string | No | See data-model.md Alert Type Enumeration |
| `severity` | string | No | low, medium, high, critical |
| `acknowledged` | boolean | No | Filter by ack state |
| `from`, `to` | ISO 8601 | No | Detection time range |
| `page`, `per_page` | int | No | Pagination |

**Response** (200 OK):
```json
{
  "data": [
    {
      "alert_id": "alert-uuid",
      "org_id": "abc-123",
      "alert_type": "config_drift",
      "severity": "medium",
      "entity_type": "device",
      "entity_id": "device-uuid",
      "entity_name": "AP-Lobby-01",
      "baseline_id": "baseline-uuid",
      "diff_summary": {
        "changes": 2,
        "paths_changed": [
          "radio_config.band_24.power",
          "radio_config.band_5.channel"
        ]
      },
      "acknowledged": false,
      "detected_at": "2026-03-06T01:02:00Z"
    }
  ]
}
```

**Performance**: SC-003 requires alerting within 5 minutes of change
detection.

---

### GET /api/v1/drift/alerts/{alert_id}

Get drift alert detail with full diff payload.

**Response** (200 OK):
```json
{
  "data": {
    "alert_id": "alert-uuid",
    "org_id": "abc-123",
    "alert_type": "config_drift",
    "severity": "medium",
    "entity_type": "device",
    "entity_id": "device-uuid",
    "entity_name": "AP-Lobby-01",
    "baseline_id": "baseline-uuid",
    "diff_detail": {
      "changes": [
        {
          "path": "radio_config.band_24.power",
          "change_type": "value_changed",
          "old_value": 10,
          "new_value": 15
        },
        {
          "path": "radio_config.band_5.channel",
          "change_type": "value_changed",
          "old_value": 36,
          "new_value": 149
        }
      ]
    },
    "notification_sent": true,
    "acknowledged": false,
    "detected_at": "2026-03-06T01:02:00Z"
  }
}
```

---

### POST /api/v1/drift/alerts/{alert_id}/acknowledge

Acknowledge a drift alert.

**Request**:
```json
{
  "comment": "Expected change from maintenance window MW-2026-042."
}
```

---

## Webhook Receiver

### POST /api/v1/webhooks/mist

Receive Mist Cloud webhook events.

This endpoint is registered with the Mist API via
`mistapi.api.v1.orgs.webhooks.createOrgWebhook()`. It accepts
Mist-standard webhook payloads for topics: `audits`, `device-events`,
`alarms`, `device-updowns`.

**Request** (Mist webhook payload):
```json
{
  "topic": "device-events",
  "events": [
    {
      "org_id": "abc-123",
      "site_id": "site-uuid",
      "device_id": "device-uuid",
      "device_name": "AP-Lobby-01",
      "type": "AP_CONFIGURED",
      "timestamp": 1709683200
    }
  ]
}
```

**Response** (200 OK):
```json
{"received": true}
```

**Behavior**:
- Validates `X-Mist-Signature-v2` header (HMAC-SHA256)
- Enqueues a targeted sync task for affected entities
- Returns 200 immediately (processing is async)
- Idempotent — duplicate events are detected and skipped

---

## Network Policies

### GET /api/v1/policies

List network policies (FR-024).

**Query Parameters**:
- `org_id` (UUID, required)
- `lifecycle_state` (string, optional): draft, active, expired
- `scope_site_id` (UUID, optional)
- `page`, `per_page`

---

### POST /api/v1/policies

Create a network policy.

**Request**:
```json
{
  "org_id": "abc-123",
  "name": "Guest VLAN Isolation",
  "description": "Ensure guest VLAN cannot reach corporate subnets",
  "scope": {"site_ids": ["site-uuid-1", "site-uuid-2"]},
  "rules": [
    {
      "entity_type": "network",
      "field_path": "isolation",
      "operator": "equals",
      "expected_value": true
    }
  ],
  "recertification_interval_days": 90,
  "enforcement_mode": "alert"
}
```

---

### POST /api/v1/policies/{policy_id}/recertify

Recertify a policy before expiration.

**Request**:
```json
{
  "confirm": true,
  "comment": "Annual review completed. Policy still valid."
}
```
