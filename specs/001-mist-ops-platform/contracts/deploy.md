# API Contract: Deploy

**Prefix**: `/api/v1/deploy`
**Maps to**: US-3 (scheduled changes), US-5 (phased rollouts), FR-005-007,
FR-010, FR-023, FR-028, FR-029, FR-031, FR-033, FR-036

---

## Endpoints

### GET /api/v1/deploy/jobs

List scheduled deployment jobs.

**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Organization scope |
| `status` | string | No | Filter: pending, running, completed, failed, cancelled |
| `from` | ISO 8601 | No | Scheduled time range start |
| `to` | ISO 8601 | No | Scheduled time range end |
| `created_by` | string | No | Filter by author |
| `page`, `per_page` | int | No | Pagination |

**Response** (200 OK):
```json
{
  "data": [
    {
      "job_id": "job-uuid",
      "status": "pending",
      "scheduled_at": "2026-03-06T02:00:00Z",
      "target_count": 5,
      "created_by": "change-mgr@example.com",
      "approved_by": null,
      "rollout_plan_id": null,
      "created_at": "2026-03-05T10:00:00Z"
    }
  ]
}
```

---

### POST /api/v1/deploy/jobs

Create a scheduled deployment job.

**Request**:
```json
{
  "org_id": "abc-123",
  "target_entities": [
    {"entity_type": "device", "entity_id": "device-uuid-1"},
    {"entity_type": "device", "entity_id": "device-uuid-2"}
  ],
  "change_payload": {
    "radio_config": {"band_24": {"power": 15}}
  },
  "scheduled_at": "2026-03-06T02:00:00Z",
  "pre_check_defs": [
    {"type": "reachability", "timeout_seconds": 30},
    {"type": "version_compat", "min_version": "0.14.0"}
  ],
  "post_check_defs": [
    {"type": "client_count", "min_threshold": 5, "wait_seconds": 120},
    {"type": "reachability", "timeout_seconds": 30}
  ],
  "auto_rollback_on_failure": true
}
```

**Response** (201 Created):
```json
{
  "data": {
    "job_id": "job-uuid",
    "status": "pending",
    "scheduled_at": "2026-03-06T02:00:00Z",
    "target_count": 2,
    "created_by": "change-mgr@example.com",
    "approval_required": false
  }
}
```

**Response** (409 Conflict — scheduling conflict):
```json
{
  "errors": [{
    "code": "SCHEDULE_CONFLICT",
    "message": "Device device-uuid-1 has a pending job at 2026-03-06T02:00:00Z",
    "detail": "Conflicting job: job-uuid-existing. Reschedule or cancel."
  }]
}
```

---

### GET /api/v1/deploy/jobs/{job_id}

Get detailed job status with checkpoint progress.

**Response** (200 OK):
```json
{
  "data": {
    "job_id": "job-uuid",
    "status": "running",
    "scheduled_at": "2026-03-06T02:00:00Z",
    "started_at": "2026-03-06T02:00:05Z",
    "target_entities": [...],
    "change_payload": {...},
    "pre_check_result": {"status": "passed", "details": [...]},
    "post_check_result": null,
    "checkpoints": [
      {"entity_id": "device-uuid-1", "step": "push", "status": "completed"},
      {"entity_id": "device-uuid-2", "step": "push", "status": "pending"}
    ],
    "created_by": "change-mgr@example.com"
  }
}
```

---

### PUT /api/v1/deploy/jobs/{job_id}

Update a pending job (reschedule or modify).

**Request**:
```json
{
  "scheduled_at": "2026-03-07T02:00:00Z"
}
```

**Constraints**: Only `pending` jobs can be modified.

---

### DELETE /api/v1/deploy/jobs/{job_id}

Cancel a pending job.

**Response** (200 OK):
```json
{
  "data": {
    "job_id": "job-uuid",
    "status": "cancelled",
    "cancelled_at": "2026-03-05T15:00:00Z"
  }
}
```

---

### POST /api/v1/deploy/jobs/{job_id}/approve

Approve a job that requires maker-checker approval (FR-033).

**Request**:
```json
{
  "confirm": true,
  "comment": "Reviewed change payload and risk assessment. Approved."
}
```

**Constraints**: Approver must be a different user than the job creator.

---

### POST /api/v1/deploy/dry-run

Validate a configuration change without applying it (FR-036).

**Request**:
```json
{
  "org_id": "abc-123",
  "target_entities": [
    {"entity_type": "device", "entity_id": "device-uuid-1"}
  ],
  "change_payload": {
    "radio_config": {"band_24": {"power": 25}}
  }
}
```

**Response** (200 OK):
```json
{
  "data": {
    "valid": true,
    "risk_score": 0.3,
    "risk_level": "low",
    "blast_radius": {
      "devices_affected": 1,
      "sites_affected": 1,
      "estimated_clients_affected": 23
    },
    "warnings": [
      "Power level 25 exceeds recommended maximum (20) for indoor APs"
    ],
    "policy_violations": [],
    "schema_errors": []
  }
}
```

**Performance**: SC-013 requires <10s.

---

### GET /api/v1/deploy/rollouts

List rollout plans.

**Query Parameters**:
- `org_id` (UUID, required)
- `status` (string, optional)
- `page`, `per_page`

---

### POST /api/v1/deploy/rollouts

Create a multi-wave rollout plan (FR-010).

**Request**:
```json
{
  "org_id": "abc-123",
  "name": "Firmware 0.15.0 Fleet Upgrade",
  "promotion_mode": "automatic",
  "health_gate_criteria": {
    "min_client_count_pct": 90,
    "max_alarm_count": 0,
    "wait_minutes": 30
  },
  "waves": [
    {
      "wave_number": 1,
      "name": "Pilot Sites",
      "target_entities": [
        {"entity_type": "site", "entity_id": "site-uuid-1"},
        {"entity_type": "site", "entity_id": "site-uuid-2"}
      ]
    },
    {
      "wave_number": 2,
      "name": "Regional Sites",
      "target_entities": [
        {"entity_type": "site", "entity_id": "site-uuid-3"},
        {"entity_type": "site", "entity_id": "site-uuid-4"},
        {"entity_type": "site", "entity_id": "site-uuid-5"}
      ]
    }
  ],
  "change_payload": {
    "firmware_version": "0.15.0"
  }
}
```

**Response** (201 Created):
```json
{
  "data": {
    "plan_id": "plan-uuid",
    "status": "draft",
    "wave_count": 2,
    "total_targets": 5,
    "promotion_mode": "automatic"
  }
}
```

---

### POST /api/v1/deploy/rollouts/{plan_id}/activate

Start executing a rollout plan (transitions from draft to active).

**Request**:
```json
{"confirm": true}
```

---

### POST /api/v1/deploy/rollouts/{plan_id}/pause

Pause an active rollout.

---

### POST /api/v1/deploy/rollouts/{plan_id}/resume

Resume a paused rollout.

---

### POST /api/v1/deploy/rollouts/{plan_id}/waves/{wave_number}/promote

Manually promote to the next wave (when promotion_mode is "manual").

**Request**:
```json
{
  "confirm": true,
  "comment": "Wave 1 health checks passed. Promoting to Wave 2."
}
```

---

### POST /api/v1/deploy/rollouts/{plan_id}/waves/{wave_number}/rollback

Roll back a specific wave.

**Request**:
```json
{
  "confirm": true,
  "reason": "Client connectivity degraded after Wave 2 deployment"
}
```

---

### GET /api/v1/deploy/templates

List change templates (FR-031).

**Query Parameters**:
- `org_id` (UUID, required)
- `category` (string, optional): "vlan", "wlan", "acl", "firmware"
- `page`, `per_page`

---

### POST /api/v1/deploy/templates

Create a reusable change template.

**Request**:
```json
{
  "org_id": "abc-123",
  "name": "Add VLAN to Site",
  "category": "vlan",
  "target_entity_type": "site",
  "parameter_schema": {
    "type": "object",
    "properties": {
      "vlan_id": {"type": "integer", "minimum": 1, "maximum": 4094},
      "vlan_name": {"type": "string", "minLength": 1},
      "subnet": {"type": "string", "format": "ipv4-network"}
    },
    "required": ["vlan_id", "vlan_name", "subnet"]
  },
  "config_template": {
    "networks": {
      "{{vlan_name}}": {
        "vlan_id": "{{vlan_id}}",
        "subnet": "{{subnet}}"
      }
    }
  },
  "approval_required": true
}
```

---

### POST /api/v1/deploy/templates/{template_id}/instantiate

Instantiate a template with parameters to create a deployment job.

**Request**:
```json
{
  "org_id": "abc-123",
  "target_entity_id": "site-uuid-1",
  "parameters": {
    "vlan_id": 200,
    "vlan_name": "IoT-Sensors",
    "subnet": "10.200.0.0/24"
  },
  "scheduled_at": "2026-03-06T02:00:00Z"
}
```

**Performance**: SC-014 requires <3 user actions to apply.

---

### GET /api/v1/deploy/golden-images

List golden images (FR-029).

**Query Parameters**:
- `org_id` (UUID, required)
- `image_type` (string, optional): "firmware", "config_template"
- `device_model` (string, optional)
- `lifecycle_state` (string, optional): "draft", "approved", "retired"

---

### POST /api/v1/deploy/golden-images

Register a new golden image.

---

### POST /api/v1/deploy/golden-images/{image_id}/approve

Approve a golden image (transitions draft to approved).

**Request**:
```json
{
  "confirm": true,
  "comment": "Validated in lab. Approved for production."
}
```

**Constraints**: Approver must be different from uploader (FR-033).

---

### POST /api/v1/deploy/golden-images/{image_id}/retire

Retire a golden image (transitions approved to retired).
