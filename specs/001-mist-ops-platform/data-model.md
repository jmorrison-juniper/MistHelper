# Data Model: Mist Ops Platform

**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-05
**Source**: spec.md (16 key entities), reference-architecture.md (13 PostgreSQL tables)

---

## Entity Relationship Overview

```text
MSP 1──* Organization 1──* Site 1──* Device
                 │                       │
                 │                       ├──* ConfigRevision
                 │                       ├──* DeviceStatusSnapshot
                 │                       └──* DriftAlert
                 │
                 ├──* AuditRecord
                 ├──* ScheduledJob ──* JobCheckpoint
                 ├──* RolloutPlan ──* RolloutWave
                 ├──* Baseline
                 ├──* ChangeTemplate
                 ├──* GoldenImage
                 ├──* ComplianceAuditPack
                 ├──* NetworkPolicy
                 ├──* NotificationChannel
                 └──* SyncLedgerEntry
```

---

## Entity Definitions

### E-00: MSP (Managed Service Provider)

**Table**: `msps`
**PK Type**: Natural (Mist UUID)
**Maps to**: Spec entity "MSP (Managed Service Provider)", FR-001, FR-025

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `msp_id` | UUID | PK | Mist MSP UUID |
| `name` | TEXT | NOT NULL | MSP display name |
| `api_host` | TEXT | NOT NULL | Mist cloud API base URL |
| `auth_method` | TEXT | NOT NULL | "session" (email/password+2FA required for MSP-level access) |
| `last_sync_at` | TIMESTAMPTZ | nullable | Last successful org enumeration |
| `sync_enabled` | BOOLEAN | DEFAULT TRUE | Whether MSP-level sync is active |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Indexes**: `(name)`

**Validation rules**:
- `msp_id` must be a valid UUID from Mist API (`GET /api/v1/self` privileges)
- `api_host` must be a valid Mist cloud hostname
- `auth_method` must be "session" (API tokens cannot access MSP-level APIs)
- MSP enumeration via `mistapi.api.v1.msps.orgs.listMspOrgs(msp_id)`

**Notes**:
- MSP is the top-level tenant. Organizations reference MSP via `msp_id` FK.
- Discovered automatically from `GET /api/v1/self` when user authenticates with session credentials.
- API token users will have `msp_id = NULL` on their organizations (org-scoped access only).

---

### E-01: Organization

**Table**: `orgs`
**PK Type**: Natural (Mist UUID)
**Maps to**: Spec entity "Organization", FR-001

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `org_id` | UUID | PK | Mist organization UUID |
| `msp_id` | UUID | FK → msps, nullable | Parent MSP (null if standalone) |
| `name` | TEXT | NOT NULL | Organization display name |
| `api_host` | TEXT | NOT NULL | Mist cloud API base URL |
| `last_sync_at` | TIMESTAMPTZ | nullable | Last successful inventory sync |
| `sync_enabled` | BOOLEAN | DEFAULT TRUE | Whether sync is active |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Indexes**: `(msp_id)`, `(name)`

**Validation rules**:
- `org_id` must be a valid UUID from Mist API
- `api_host` must be a valid Mist cloud hostname (11 known clouds)
- `name` must be non-empty

---

### E-02: Site

**Table**: `sites`
**PK Type**: Natural (Mist UUID)
**Maps to**: Spec entity "Site", FR-001

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `site_id` | UUID | PK | Mist site UUID |
| `org_id` | UUID | FK → orgs, NOT NULL | Parent organization |
| `name` | TEXT | NOT NULL | Site display name |
| `address` | TEXT | nullable | Physical address |
| `location` | JSONB | nullable | Lat/lng/country/timezone |
| `last_sync_at` | TIMESTAMPTZ | nullable | Last successful sync |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Indexes**: `(org_id)`, `(org_id, name)`

**Validation rules**:
- `site_id` must be a valid UUID from Mist API
- `org_id` must reference an existing organization

---

### E-03: Device

**Table**: `devices`
**PK Type**: Natural (Mist UUID)
**Maps to**: Spec entity "Device", FR-001

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `device_id` | UUID | PK | Mist device UUID |
| `org_id` | UUID | FK → orgs, NOT NULL | Parent organization |
| `site_id` | UUID | FK → sites, nullable | Assigned site (null if unassigned) |
| `serial` | TEXT | UNIQUE, NOT NULL | Hardware serial number |
| `model` | TEXT | NOT NULL | Device model (e.g., AP45, EX4100) |
| `device_type` | TEXT | NOT NULL | "ap", "switch", or "gateway" |
| `firmware_version` | TEXT | nullable | Currently running firmware |
| `status` | TEXT | DEFAULT 'unknown' | Operational status |
| `mac_address` | TEXT | nullable | Device MAC address |
| `ip_address` | TEXT | nullable | Management IP |
| `last_sync_at` | TIMESTAMPTZ | nullable | Last successful sync |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Indexes**: `(org_id)`, `(site_id)`, `(serial)`, `(org_id, device_type)`

**Validation rules**:
- `device_type` must be one of: `ap`, `switch`, `gateway`
- `status` must be one of: `connected`, `disconnected`, `unknown`
- `serial` must be non-empty and unique

---

### E-04: ConfigRevision

**Table**: `config_revisions`
**PK Type**: Composite (org_id + revision_id for partitioning)
**Maps to**: Spec entity "Configuration Revision", FR-002, FR-003, FR-004, FR-013
**Partitioned by**: HASH(org_id)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `revision_id` | BIGSERIAL | PK component | Auto-increment revision ID |
| `org_id` | UUID | PK component, FK → orgs | Owning organization (partition key) |
| `entity_type` | TEXT | NOT NULL | "device", "site", "org", "wlan", "policy" |
| `entity_id` | UUID | NOT NULL | Mist UUID of the configured entity |
| `captured_at` | TIMESTAMPTZ | NOT NULL | When this revision was captured |
| `content_hash` | TEXT | NOT NULL | SHA-256 of config_payload for dedup |
| `config_payload` | JSONB | NOT NULL | Full configuration snapshot |
| `actor` | TEXT | nullable | User email or API token ID |
| `source` | TEXT | DEFAULT 'sync' | "sync", "webhook", "manual" |

**Indexes**: `(entity_id, entity_type, captured_at DESC)` — time-travel query
**Unique constraint**: `(entity_id, content_hash)` — dedup

**Validation rules**:
- `entity_type` must be a recognized type from `ENTITY_TYPE_ENUM`
- `content_hash` is computed server-side, never from client input
- `config_payload` must be valid JSON and non-empty
- Immutable: once inserted, revisions are never updated or deleted (except
  by retention policy)

**State**: This entity is append-only. No state transitions.

---

### E-05: DeviceStatusSnapshot

**Table**: `device_status_snapshots`
**PK Type**: Composite (org_id + snapshot_id)
**Maps to**: FR-013 (time-travel for status/health, not just config)
**Partitioned by**: HASH(org_id)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `snapshot_id` | BIGSERIAL | PK component | Auto-increment ID |
| `org_id` | UUID | PK component, FK → orgs | Partition key |
| `device_id` | UUID | FK → devices, NOT NULL | Target device |
| `captured_at` | TIMESTAMPTZ | NOT NULL | Snapshot timestamp |
| `status` | TEXT | NOT NULL | Device status at capture time |
| `port_states` | JSONB | nullable | Port up/down states (switches) |
| `client_count` | INTEGER | nullable | Connected client count |
| `health_metrics` | JSONB | nullable | SLE scores, signal strength, etc. |

**Indexes**: `(device_id, captured_at DESC)` — time-travel query

**Validation rules**:
- `device_id` must reference an existing device
- Append-only. Retention policy applies.

---

### E-06: AuditRecord

**Table**: `audit_records`
**PK Type**: Composite (org_id + record_id)
**Maps to**: Spec entity "Audit Record", FR-008, FR-009
**Partitioned by**: HASH(org_id)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `record_id` | BIGSERIAL | PK component | Auto-increment ID |
| `org_id` | UUID | PK component, FK → orgs | Partition key |
| `timestamp` | TIMESTAMPTZ | NOT NULL | When the change occurred |
| `actor` | TEXT | NOT NULL | User email or API token ID |
| `entity_type` | TEXT | NOT NULL | Type of entity changed |
| `entity_id` | UUID | NOT NULL | UUID of changed entity |
| `change_type` | TEXT | NOT NULL | "create", "update", "delete", "restore" |
| `old_values` | JSONB | nullable | Previous field values (null for create) |
| `new_values` | JSONB | nullable | New field values (null for delete) |
| `revision_id` | BIGINT | nullable | Link to config_revision if applicable |
| `job_id` | UUID | nullable | Link to scheduled_job if applicable |

**Indexes**: `(org_id, timestamp)`, `(org_id, entity_type, timestamp)`,
`(org_id, actor, timestamp)`

**Validation rules**:
- `actor` defaults to API token identifier if user attribution unavailable
- `change_type` must be one of: `create`, `update`, `delete`, `restore`
- Append-only. 365-day default retention.

---

### E-07: ScheduledJob

**Table**: `scheduled_jobs`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Scheduled Job", FR-005, FR-006, FR-007

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `job_id` | UUID | PK, DEFAULT gen_random_uuid() | Job identifier |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `target_entities` | JSONB | NOT NULL | Array of {entity_type, entity_id} |
| `change_payload` | JSONB | NOT NULL | Configuration to apply |
| `scheduled_at` | TIMESTAMPTZ | NOT NULL | Planned execution time |
| `status` | TEXT | DEFAULT 'pending' | Current job state |
| `pre_check_defs` | JSONB | nullable | Pre-check probe definitions |
| `post_check_defs` | JSONB | nullable | Post-check probe definitions |
| `pre_check_result` | JSONB | nullable | Pre-check execution result |
| `post_check_result` | JSONB | nullable | Post-check execution result |
| `created_by` | TEXT | NOT NULL | Author (user email/token) |
| `approved_by` | TEXT | nullable | Approver (for maker-checker) |
| `rollout_plan_id` | UUID | FK → rollout_plans, nullable | Parent rollout |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Job creation time |
| `started_at` | TIMESTAMPTZ | nullable | Actual execution start |
| `completed_at` | TIMESTAMPTZ | nullable | Execution completion time |
| `error_message` | TEXT | nullable | Error details if failed |

**Indexes**: `(org_id, status)`, `(org_id, scheduled_at)`, `(rollout_plan_id)`

**State transitions**:
```text
pending → pre_check_running → pre_check_failed (terminal)
                            → ready → running → post_check_running
                                                    → completed (terminal)
                                                    → rolling_back → rolled_back (terminal)
                                                    → post_check_failed (terminal)
                                       → failed (terminal)
pending → cancelled (terminal)
```

**Validation rules**:
- `scheduled_at` must be in the future at creation time
- `target_entities` must contain at least one valid entity reference
- `change_payload` must be valid JSON
- Conflict detection: no two pending jobs for the same entity at the same time

---

### E-08: JobCheckpoint

**Table**: `job_checkpoints`
**PK Type**: Composite (job_id + checkpoint_id)
**Maps to**: FR-015 (idempotent operations with progress checkpoints)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `checkpoint_id` | BIGSERIAL | PK component | Auto-increment ID |
| `job_id` | UUID | PK component, FK → scheduled_jobs | Parent job |
| `entity_id` | UUID | NOT NULL | Device/entity being processed |
| `step` | TEXT | NOT NULL | "pre_snapshot", "push", "verify", "post_check" |
| `status` | TEXT | NOT NULL | "completed", "failed", "skipped" |
| `payload` | JSONB | nullable | Step result data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Checkpoint creation time |

**Purpose**: Enables safe resumption of interrupted jobs. On restart, the
system reads checkpoints to determine which entities have been processed
and which are pending.

---

### E-09: RolloutPlan

**Table**: `rollout_plans`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Rollout Plan", FR-010

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `plan_id` | UUID | PK, DEFAULT gen_random_uuid() | Plan identifier |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `name` | TEXT | NOT NULL | Rollout plan display name |
| `promotion_mode` | TEXT | DEFAULT 'manual' | "manual" or "automatic" |
| `health_gate_criteria` | JSONB | NOT NULL | Health check thresholds |
| `status` | TEXT | DEFAULT 'draft' | Current plan state |
| `created_by` | TEXT | NOT NULL | Author |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**State transitions**:
```text
draft → active → paused → active (resume)
                        → cancelled (terminal)
              → completed (terminal)
              → partially_rolled_back (terminal)
```

---

### E-10: RolloutWave

**Table**: `rollout_waves`
**PK Type**: Composite (plan_id + wave_number)
**Maps to**: FR-010 wave definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `plan_id` | UUID | FK → rollout_plans, NOT NULL | Parent plan |
| `wave_number` | INTEGER | NOT NULL | Execution order (1-based) |
| `target_entities` | JSONB | NOT NULL | Devices/sites in this wave |
| `status` | TEXT | DEFAULT 'pending' | Wave state |
| `started_at` | TIMESTAMPTZ | nullable | Wave execution start |
| `completed_at` | TIMESTAMPTZ | nullable | Wave completion |
| `health_check_result` | JSONB | nullable | Post-wave health check |

**PK**: `(plan_id, wave_number)`

**State transitions**:
```text
pending → running → health_checking → promoted (terminal)
                                    → paused
                                    → rolled_back (terminal)
```

---

### E-11: Baseline

**Table**: `baselines`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Baseline (Intended State)", FR-011, FR-012

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `baseline_id` | UUID | PK, DEFAULT gen_random_uuid() | Baseline ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `entity_type` | TEXT | NOT NULL | Scope type (site, device_group) |
| `entity_scope` | UUID | NOT NULL | Site ID or device group ID |
| `config_payload` | JSONB | NOT NULL | Intended configuration |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update |
| `updated_by` | TEXT | NOT NULL | Who set this baseline |

**Indexes**: `(org_id, entity_type, entity_scope)` UNIQUE

**Validation rules**:
- One baseline per (entity_type, entity_scope) combination
- `config_payload` must be valid JSON
- Mutable: updated when operator accepts drift as new baseline (FR-012)

---

### E-12: DriftAlert

**Table**: `drift_alerts`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Drift Alert", FR-011

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `alert_id` | UUID | PK, DEFAULT gen_random_uuid() | Alert ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `baseline_id` | UUID | FK → baselines, NOT NULL | Reference baseline |
| `device_id` | UUID | FK → devices, NOT NULL | Drifted device |
| `detected_at` | TIMESTAMPTZ | NOT NULL | When drift was detected |
| `diff_payload` | JSONB | NOT NULL | deepdiff output (old/new values) |
| `status` | TEXT | DEFAULT 'open' | Alert state |
| `resolved_at` | TIMESTAMPTZ | nullable | Resolution timestamp |
| `resolved_by` | TEXT | nullable | Who resolved the alert |

**State transitions**:
```text
open → remediated (pushed intended state back)
     → accepted (drift accepted as new baseline)
     → expired (auto-closed by retention policy)
```

---

### E-13: ChangeTemplate

**Table**: `change_templates`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Change Template", FR-031

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `template_id` | UUID | PK, DEFAULT gen_random_uuid() | Template ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `name` | TEXT | NOT NULL | Template display name |
| `category` | TEXT | NOT NULL | "vlan", "acl", "wlan", "firmware", etc. |
| `parameter_schema` | JSONB | NOT NULL | JSON Schema for template params |
| `config_template` | JSONB | NOT NULL | Jinja2-like config template body |
| `target_entity_type` | TEXT | NOT NULL | What entity type this applies to |
| `approval_required` | BOOLEAN | DEFAULT FALSE | Requires maker-checker |
| `author` | TEXT | NOT NULL | Template creator |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**Validation rules**:
- `parameter_schema` must be valid JSON Schema
- `category` must be from a defined set of categories

---

### E-14: GoldenImage

**Table**: `golden_images`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Golden Image", FR-029

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `image_id` | UUID | PK, DEFAULT gen_random_uuid() | Image ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `image_type` | TEXT | NOT NULL | "firmware" or "config_template" |
| `device_model` | TEXT | NOT NULL | Target device model family |
| `version` | TEXT | NOT NULL | Firmware version string |
| `lifecycle_state` | TEXT | DEFAULT 'draft' | Approval state |
| `content_hash` | TEXT | NOT NULL | SHA-256 of the image/artifact |
| `artifact_url` | TEXT | nullable | MinIO path to stored artifact |
| `approved_by` | TEXT | nullable | Approver identity |
| `approved_at` | TIMESTAMPTZ | nullable | Approval timestamp |
| `created_by` | TEXT | NOT NULL | Uploader identity |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Upload time |

**State transitions** (FR-029, SC-017):
```text
draft → approved → retired
draft → rejected (terminal)
```

**Unique constraint**: `(org_id, image_type, device_model, version)`

---

### E-15: ComplianceAuditPack

**Table**: `compliance_audit_packs`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Compliance Audit Pack", FR-032

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `pack_id` | UUID | PK, DEFAULT gen_random_uuid() | Pack ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `framework` | TEXT | NOT NULL | "sox", "pci_dss", "soc2" |
| `date_range_start` | TIMESTAMPTZ | NOT NULL | Evidence start date |
| `date_range_end` | TIMESTAMPTZ | NOT NULL | Evidence end date |
| `included_records` | JSONB | NOT NULL | Record IDs and types included |
| `artifact_url` | TEXT | nullable | MinIO path to exported pack |
| `export_format` | TEXT | DEFAULT 'json' | "json", "csv", "pdf" |
| `generated_by` | TEXT | NOT NULL | Who generated the pack |
| `generated_at` | TIMESTAMPTZ | DEFAULT NOW() | Generation timestamp |

---

### E-16: NetworkPolicy

**Table**: `network_policies`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Network Policy", FR-024

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `policy_id` | UUID | PK, DEFAULT gen_random_uuid() | Policy ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `mist_entity_id` | UUID | NOT NULL | Mist UUID of the policy object |
| `policy_type` | TEXT | NOT NULL | "wlan", "firewall", "nac_rule" |
| `name` | TEXT | NOT NULL | Policy display name |
| `lifecycle_state` | TEXT | DEFAULT 'active' | Current lifecycle state |
| `version` | INTEGER | DEFAULT 1 | Version counter |
| `effective_from` | TIMESTAMPTZ | nullable | When policy became active |
| `expires_at` | TIMESTAMPTZ | nullable | Auto-expiry date (if set) |
| `dependencies` | JSONB | nullable | Dependent policy references |
| `last_reviewed_at` | TIMESTAMPTZ | nullable | Last recertification |
| `reviewed_by` | TEXT | nullable | Reviewer identity |

**State transitions**:
```text
active → expired (auto or manual)
       → retired (permanent decommission)
active ↔ under_review (recertification cycle)
```

---

### E-17: IncidentChangeCorrelation

**Table**: `incident_change_correlations`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Incident-Change Correlation", FR-035

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `correlation_id` | UUID | PK, DEFAULT gen_random_uuid() | Correlation ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `incident_type` | TEXT | NOT NULL | "alarm", "sle_degradation", "client_drop" |
| `incident_id` | TEXT | NOT NULL | Mist alarm/event ID |
| `incident_at` | TIMESTAMPTZ | NOT NULL | When the incident occurred |
| `change_revision_id` | BIGINT | nullable | Linked config revision |
| `change_job_id` | UUID | nullable | Linked scheduled job |
| `confidence_score` | FLOAT | NOT NULL | 0.0 to 1.0 confidence |
| `detection_method` | TEXT | NOT NULL | "temporal", "scope_match", "manual" |
| `detected_at` | TIMESTAMPTZ | DEFAULT NOW() | When correlation found |

**Validation rules**:
- At least one of `change_revision_id` or `change_job_id` must be non-null
- `confidence_score` must be between 0.0 and 1.0

---

### E-18: NotificationChannel

**Table**: `notification_channels`
**PK Type**: Natural (UUID)
**Maps to**: Spec entity "Notification Channel", FR-037

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `channel_id` | UUID | PK, DEFAULT gen_random_uuid() | Channel ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Owning organization |
| `channel_type` | TEXT | NOT NULL | "email" or "webhook" |
| `name` | TEXT | NOT NULL | Display name for the channel |
| `destination` | TEXT | NOT NULL | SMTP address or webhook URL |
| `alert_subscriptions` | TEXT[] | NOT NULL | Alert types subscribed to |
| `enabled` | BOOLEAN | DEFAULT TRUE | Active flag |
| `auth_config` | JSONB | nullable | Webhook auth (encrypted ref) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**Validation rules**:
- `channel_type` must be one of: `email`, `webhook`
- `destination` must be valid email (for email) or valid URL (for webhook)
- `alert_subscriptions` must contain valid alert type identifiers
- `auth_config` must never contain plaintext secrets (Vault reference only)

---

### E-19: SyncLedgerEntry

**Table**: `sync_ledger`
**PK Type**: Auto-increment
**Maps to**: Internal bookkeeping for FR-001 sync operations

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PK | Auto-increment ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Organization synced |
| `job_type` | TEXT | NOT NULL | "inventory", "config", "status", "events" |
| `started_at` | TIMESTAMPTZ | NOT NULL | Sync start time |
| `ended_at` | TIMESTAMPTZ | nullable | Sync completion time |
| `status` | TEXT | NOT NULL | "running", "completed", "failed" |
| `rows_affected` | INTEGER | nullable | Number of records processed |
| `error_text` | TEXT | nullable | Error details if failed |

---

### E-20: WebhookEnvelope

**Table**: `webhook_envelopes`
**PK Type**: Natural (event_id for dedup)
**Maps to**: Internal webhook deduplication (R-02 in research.md)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PK | Auto-increment ID |
| `org_id` | UUID | FK → orgs, NOT NULL | Source organization |
| `event_id` | TEXT | UNIQUE, NOT NULL | Mist event ID for dedup |
| `received_at` | TIMESTAMPTZ | NOT NULL | When webhook was received |
| `event_type` | TEXT | NOT NULL | Mist event type |
| `payload` | JSONB | NOT NULL | Raw webhook payload |
| `processed_at` | TIMESTAMPTZ | nullable | When processing completed |
| `status` | TEXT | DEFAULT 'pending' | "pending", "processed", "failed" |

---

## Alert Type Enumeration

Used by `NotificationChannel.alert_subscriptions` and `NotificationService`:

| Alert Type | Trigger | Maps to |
|------------|---------|---------|
| `deployment_started` | Scheduled job begins execution | FR-005 |
| `deployment_completed` | Scheduled job completes successfully | FR-005 |
| `deployment_failed` | Scheduled job fails | FR-005 |
| `pre_check_failed` | Pre-deployment check fails | FR-006 |
| `post_check_failed` | Post-deployment check fails | FR-007 |
| `auto_rollback` | Auto-revert triggered | FR-007 |
| `drift_detected` | Baseline drift found | FR-011 |
| `drift_remediated` | Drift auto-remediated | FR-012 |
| `approval_requested` | Maker-checker approval needed | FR-033 |
| `wave_promoted` | Rollout wave promoted | FR-010 |
| `wave_paused` | Rollout wave paused | FR-010 |
| `compliance_pack_ready` | Audit pack generated | FR-032 |
| `sync_failed` | Mist API sync failure | FR-001 |

---

## Partitioning Summary

| Table | Strategy | Partition Key | Partitions |
|-------|----------|---------------|------------|
| `config_revisions` | HASH | `org_id` | 16 |
| `device_status_snapshots` | HASH | `org_id` | 16 |
| `audit_records` | HASH | `org_id` | 16 |
| All other tables | None | — | — |

**Rationale**: Only high-volume, time-series tables are partitioned. All
queries are org-scoped, so hash partitioning by org_id provides partition
pruning. 16 partitions support up to 500+ orgs with even distribution.

---

## Retention Policies

| Table | Default Retention | Configurable |
|-------|-------------------|--------------|
| `config_revisions` | 90 days | Yes (per org) |
| `device_status_snapshots` | 30 days | Yes (per org) |
| `audit_records` | 365 days | Yes (per org) |
| `webhook_envelopes` | 7 days | Yes (global) |
| `sync_ledger` | 30 days | Yes (global) |
| `job_checkpoints` | 30 days after job completion | No |

**Enforcement**: Celery Beat nightly task runs `DELETE ... WHERE captured_at
< :cutoff` per partition. Large deletes are batched (1000 rows per
transaction) to avoid lock contention.
