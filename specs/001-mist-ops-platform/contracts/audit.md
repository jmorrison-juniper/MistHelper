# API Contract: Audit

**Prefix**: `/api/v1/audit`
**Maps to**: US-4 (change audit trail), FR-008, FR-009, FR-032, FR-035

---

## Endpoints

### GET /api/v1/audit/records

Query the change audit trail with filters.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `entity_type` | string | No | Filter by entity type (device, wlan, etc.) |
| `entity_id` | UUID | No | Filter by specific entity |
| `actor` | string | No | Filter by actor identity |
| `change_type` | string | No | "create", "update", "delete", "restore" |
| `from` | ISO 8601 | No | Start of time range |
| `to` | ISO 8601 | No | End of time range |
| `page` | int | No | Page number (default: 1) |
| `per_page` | int | No | Items per page (default: 50) |

**Response** (200 OK):
```json
{
  "data": [
    {
      "record_id": 56789,
      "timestamp": "2026-03-05T14:05:00Z",
      "actor": "operator@example.com",
      "entity_type": "wlan",
      "entity_id": "wlan-uuid",
      "change_type": "update",
      "old_values": {
        "ssid": "Guest-WiFi",
        "vlan_id": 100
      },
      "new_values": {
        "ssid": "Guest-WiFi-v2",
        "vlan_id": 200
      },
      "revision_id": 12345,
      "job_id": null
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 847 }
}
```

**Performance**: SC-006 requires <5s for 12 months of data.

---

### GET /api/v1/audit/records/{record_id}

Get a single audit record with full old/new values.

**Query Parameters**:
- `org_id` (UUID, required)

**Response** (200 OK):
```json
{
  "data": {
    "record_id": 56789,
    "timestamp": "2026-03-05T14:05:00Z",
    "actor": "operator@example.com",
    "entity_type": "wlan",
    "entity_id": "wlan-uuid",
    "change_type": "update",
    "old_values": { ... },
    "new_values": { ... },
    "revision_id": 12345,
    "job_id": null
  }
}
```

---

### POST /api/v1/audit/export

Export filtered audit records as a downloadable file.

**Request**:
```json
{
  "org_id": "abc-123",
  "format": "csv",
  "filters": {
    "entity_type": "wlan",
    "from": "2025-01-01T00:00:00Z",
    "to": "2026-01-01T00:00:00Z",
    "actor": "operator@example.com"
  }
}
```

**Response** (202 Accepted — async export):
```json
{
  "data": {
    "export_id": "export-uuid",
    "status": "generating",
    "estimated_records": 847,
    "format": "csv"
  }
}
```

**GET /api/v1/audit/export/{export_id}** — poll for completion:
```json
{
  "data": {
    "export_id": "export-uuid",
    "status": "completed",
    "download_url": "/api/v1/audit/export/export-uuid/download",
    "record_count": 847,
    "file_size_bytes": 125000
  }
}
```

**Performance**: SC-012 requires <30s for 12 months.

---

### GET /api/v1/audit/correlations

Query incident-change correlations.

**Query Parameters**:
- `org_id` (UUID, required)
- `incident_type` (string, optional): "alarm", "sle_degradation"
- `from` / `to` (ISO 8601, optional)
- `min_confidence` (float, optional): Minimum confidence score (0-1)
- `page`, `per_page`

**Response** (200 OK):
```json
{
  "data": [
    {
      "correlation_id": "corr-uuid",
      "incident_type": "sle_degradation",
      "incident_id": "mist-alarm-id",
      "incident_at": "2026-03-05T14:10:00Z",
      "change_revision_id": 12345,
      "change_job_id": null,
      "confidence_score": 0.85,
      "detection_method": "temporal",
      "detected_at": "2026-03-05T14:12:00Z"
    }
  ]
}
```

**Performance**: SC-016 requires correlation within 2 minutes.

---

### POST /api/v1/audit/compliance-packs

Generate a compliance audit evidence package.

**Request**:
```json
{
  "org_id": "abc-123",
  "framework": "pci_dss",
  "date_range_start": "2025-01-01T00:00:00Z",
  "date_range_end": "2026-01-01T00:00:00Z",
  "export_format": "json"
}
```

**Response** (202 Accepted):
```json
{
  "data": {
    "pack_id": "pack-uuid",
    "status": "generating",
    "framework": "pci_dss",
    "estimated_records": 3200
  }
}
```

### GET /api/v1/audit/compliance-packs/{pack_id}

Poll for pack generation status and download.

**Response** (200 — completed):
```json
{
  "data": {
    "pack_id": "pack-uuid",
    "status": "completed",
    "framework": "pci_dss",
    "record_count": 3200,
    "download_url": "/api/v1/audit/compliance-packs/pack-uuid/download",
    "generated_at": "2026-03-05T15:00:00Z"
  }
}
```
