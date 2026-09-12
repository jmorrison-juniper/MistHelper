# API Contract: Config

**Prefix**: `/api/v1/config`
**Maps to**: US-1 (time-travel), US-2 (versioning/diff/rollback), US-6 (drift)

---

## Endpoints

### GET /api/v1/config/revisions

List configuration revisions for an entity.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `entity_id` | UUID | Yes | Device/site/WLAN UUID |
| `entity_type` | string | No | Filter by type (device, site, wlan, etc.) |
| `from` | ISO 8601 | No | Start of time range |
| `to` | ISO 8601 | No | End of time range |
| `actor` | string | No | Filter by actor identity |
| `page` | int | No | Page number (default: 1) |
| `per_page` | int | No | Items per page (default: 50) |

**Response** (200 OK):
```json
{
  "data": [
    {
      "revision_id": 12345,
      "entity_type": "device",
      "entity_id": "abc-123",
      "captured_at": "2026-03-05T14:05:00Z",
      "content_hash": "sha256:a1b2c3...",
      "actor": "operator@example.com",
      "source": "sync"
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 142 }
}
```

---

### GET /api/v1/config/revisions/{revision_id}

Get a specific revision with its full configuration payload.

**Path Parameters**:
- `revision_id` (int): Revision identifier

**Query Parameters**:
- `org_id` (UUID, required): Organization scope

**Response** (200 OK):
```json
{
  "data": {
    "revision_id": 12345,
    "entity_type": "device",
    "entity_id": "abc-123",
    "captured_at": "2026-03-05T14:05:00Z",
    "content_hash": "sha256:a1b2c3...",
    "actor": "operator@example.com",
    "config_payload": {
      "name": "AP-Lobby-01",
      "radio_config": { ... },
      "ip_config": { ... }
    }
  }
}
```

---

### POST /api/v1/config/diff

Compute a field-level diff between two revisions.

**Request**:
```json
{
  "org_id": "abc-123",
  "old_revision_id": 12340,
  "new_revision_id": 12345
}
```

**Response** (200 OK):
```json
{
  "data": {
    "old_revision_id": 12340,
    "new_revision_id": 12345,
    "entity_id": "abc-123",
    "changes": [
      {
        "path": "radio_config.band_24.power",
        "old_value": 10,
        "new_value": 15,
        "change_type": "value_changed"
      },
      {
        "path": "ip_config.dns_servers[1]",
        "old_value": null,
        "new_value": "8.8.4.4",
        "change_type": "item_added"
      }
    ],
    "summary": {
      "fields_changed": 1,
      "fields_added": 1,
      "fields_removed": 0
    }
  }
}
```

**Performance**: SC-003 requires <3s for configs up to 50KB.

---

### GET /api/v1/config/time-travel

Retrieve the state of an entity at a specific point in time.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `entity_id` | UUID | Yes | Device/site UUID |
| `entity_type` | string | Yes | "device", "site", etc. |
| `timestamp` | ISO 8601 | Yes | Target point in time |
| `include_status` | bool | No | Include device status snapshot |
| `include_health` | bool | No | Include health metrics |

**Response** (200 OK):
```json
{
  "data": {
    "entity_id": "abc-123",
    "entity_type": "device",
    "queried_timestamp": "2026-03-04T14:05:00Z",
    "actual_timestamp": "2026-03-04T14:03:22Z",
    "config": {
      "name": "AP-Lobby-01",
      "radio_config": { ... }
    },
    "status": {
      "operational_state": "connected",
      "port_states": { ... },
      "client_count": 23
    },
    "health": {
      "sle_scores": { ... },
      "signal_strength_avg": -62
    }
  }
}
```

**Response** (404 — data outside retention window):
```json
{
  "errors": [{
    "code": "DATA_EXPIRED",
    "message": "No data available for 2025-01-01T00:00:00Z",
    "detail": "Oldest available timestamp: 2025-12-06T00:00:00Z"
  }]
}
```

**Performance**: SC-001 requires <5s response time.

---

### POST /api/v1/config/install-from-revision

Push a historical configuration revision back to the target device(s).

**Request**:
```json
{
  "org_id": "abc-123",
  "revision_id": 12340,
  "target_entity_ids": ["device-uuid-1", "device-uuid-2"],
  "confirm": true,
  "reason": "Reverting WLAN change that caused client connectivity drops"
}
```

**Response** (202 Accepted — job queued):
```json
{
  "data": {
    "job_id": "job-uuid-456",
    "status": "pending",
    "target_count": 2,
    "revision_id": 12340,
    "message": "Install-from-revision job queued"
  }
}
```

**Response** (400 — confirmation missing):
```json
{
  "errors": [{
    "code": "CONFIRMATION_REQUIRED",
    "message": "This operation will push revision 12340 to 2 devices",
    "detail": "Set confirm=true to proceed"
  }]
}
```

---

### GET /api/v1/config/baselines

List defined baselines for an organization.

**Query Parameters**:
- `org_id` (UUID, required)
- `entity_type` (string, optional): Filter by scope type
- `page`, `per_page`

**Response** (200 OK):
```json
{
  "data": [
    {
      "baseline_id": "baseline-uuid",
      "entity_type": "site",
      "entity_scope": "site-uuid",
      "updated_at": "2026-03-01T10:00:00Z",
      "updated_by": "admin@example.com"
    }
  ]
}
```

---

### POST /api/v1/config/baselines

Create or update a baseline (intended state).

**Request**:
```json
{
  "org_id": "abc-123",
  "entity_type": "site",
  "entity_scope": "site-uuid",
  "config_payload": { ... }
}
```

---

### POST /api/v1/config/baselines/{baseline_id}/accept-drift

Accept current drift as the new baseline.

**Request**:
```json
{
  "alert_id": "drift-alert-uuid",
  "confirm": true,
  "reason": "Intentional VLAN change approved by CAB"
}
```

---

### POST /api/v1/config/baselines/{baseline_id}/remediate

Push the baseline config back to drifted devices.

**Request**:
```json
{
  "alert_ids": ["drift-alert-uuid-1", "drift-alert-uuid-2"],
  "confirm": true,
  "reason": "Unauthorized change detected, restoring baseline"
}
```
