# Data Model: Ops Frontend Portal

**Branch**: `007-ops-frontend-portal` | **Date**: 2026-03-06
**Input**: [spec.md](spec.md) entities + [research.md](research.md) technology decisions

---

## Overview

The frontend has no persistent storage — all data comes from the backend API. This document defines the TypeScript types that model API responses, client-side state, and UI view models. Types are organized into 5 domains matching the API route groups, plus a shared domain for cross-cutting concerns.

---

## Domain 1: Navigation & Session

### NavigationContext

Persisted in Zustand store with localStorage middleware. Represents the operator's current drill-down position.

| Field | Type | Description |
|-------|------|-------------|
| `mspId` | `string \| null` | Selected MSP (null if org-scoped token) |
| `orgId` | `string \| null` | Selected organization ID |
| `orgName` | `string \| null` | Selected organization name (display) |
| `siteId` | `string \| null` | Selected site ID |
| `siteName` | `string \| null` | Selected site name (display) |
| `deviceId` | `string \| null` | Selected device ID |

**Validation**: Setting `siteId` requires `orgId` to be set. Setting `deviceId` requires `siteId` to be set. Clearing `orgId` clears `siteId` and `deviceId`.

### SessionState

| Field | Type | Description |
|-------|------|-------------|
| `isAuthenticated` | `boolean` | Whether operator has a valid session |
| `sessionId` | `string \| null` | Backend session identifier |
| `operator` | `OperatorIdentity \| null` | Authenticated operator details |
| `expiresAt` | `string \| null` | ISO 8601 session expiry timestamp |
| `returnUrl` | `string \| null` | URL to redirect to after re-authentication |

### OperatorIdentity

| Field | Type | Description |
|-------|------|-------------|
| `email` | `string` | Operator email |
| `name` | `string` | Display name |
| `role` | `'msp' \| 'org_admin' \| 'org_viewer'` | Permission scope |
| `orgs` | `OrgRef[]` | Accessible organizations |

### OrgRef

| Field | Type | Description |
|-------|------|-------------|
| `orgId` | `string` | Organization ID |
| `name` | `string` | Organization display name |

---

## Domain 2: Config (Revisions, Diffs, Baselines)

### ConfigRevision

Maps to `GET /api/v1/config/revisions` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Revision UUID |
| `entityType` | `string` | Entity type (device, site, wlan, policy) |
| `entityId` | `string` | Entity UUID |
| `capturedAt` | `string` | ISO 8601 capture timestamp |
| `actor` | `string` | Who/what triggered the capture |
| `source` | `'sync' \| 'manual' \| 'restore'` | How the revision was created |
| `contentHash` | `string` | SHA-256 of config content |
| `summary` | `string \| null` | Human-readable change summary |

### ConfigDiff

Maps to `POST /api/v1/config/diff` response.

| Field | Type | Description |
|-------|------|-------------|
| `leftRevisionId` | `string` | Old revision ID |
| `rightRevisionId` | `string` | New revision ID |
| `changes` | `DiffChange[]` | Array of field-level changes |
| `summary` | `DiffSummary` | Aggregate change counts |

### DiffChange

| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Dot-notation path to changed field |
| `changeType` | `'added' \| 'removed' \| 'modified'` | Type of change |
| `oldValue` | `unknown \| null` | Previous value (null for added) |
| `newValue` | `unknown \| null` | New value (null for removed) |

### DiffSummary

| Field | Type | Description |
|-------|------|-------------|
| `added` | `number` | Fields added |
| `removed` | `number` | Fields removed |
| `modified` | `number` | Fields changed |
| `total` | `number` | Total changes |

### TimeTravelSnapshot

Maps to `GET /api/v1/config/time-travel` response.

| Field | Type | Description |
|-------|------|-------------|
| `queriedAt` | `string` | Requested timestamp |
| `actualAt` | `string` | Closest available data timestamp |
| `config` | `Record<string, unknown>` | Device config at that moment |
| `portStates` | `PortState[]` | Port up/down states |
| `clientCount` | `number` | Connected client count |
| `healthMetrics` | `Record<string, number>` | Key health indicators |

### PortState

| Field | Type | Description |
|-------|------|-------------|
| `portId` | `string` | Port identifier |
| `name` | `string` | Port display name |
| `status` | `'up' \| 'down' \| 'disabled'` | Port state |
| `speed` | `string \| null` | Negotiated speed |

### ConfigBaseline

Maps to `GET /api/v1/config/baselines` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Baseline UUID |
| `name` | `string` | Baseline display name |
| `scopeType` | `'site' \| 'device_group'` | What scope the baseline covers |
| `scopeId` | `string` | Scope entity ID |
| `content` | `Record<string, unknown>` | Baseline config content |
| `createdAt` | `string` | ISO 8601 creation timestamp |
| `updatedAt` | `string` | ISO 8601 last update timestamp |
| `createdBy` | `string` | Creator identity |

---

## Domain 3: Deploy (Jobs, Rollouts, Templates, Golden Images)

### DeployJob

Maps to `GET /api/v1/deploy/jobs` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Job UUID |
| `name` | `string` | Job display name |
| `status` | `JobStatus` | Current job status |
| `scheduledAt` | `string \| null` | ISO 8601 scheduled execution time |
| `scheduledTz` | `string` | IANA timezone for scheduled time |
| `targetDevices` | `string[]` | Target device IDs |
| `changePayload` | `Record<string, unknown>` | Config change to apply |
| `preChecks` | `CheckConfig[]` | Pre-deployment checks |
| `postChecks` | `CheckConfig[]` | Post-deployment checks |
| `autoRollback` | `boolean` | Whether to rollback on post-check failure |
| `requiresApproval` | `boolean` | Maker-checker required |
| `approvedBy` | `string \| null` | Approver identity |
| `createdBy` | `string` | Creator identity |
| `createdAt` | `string` | ISO 8601 creation timestamp |

### JobStatus

```typescript
type JobStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'scheduled'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'rolled_back';
```

### CheckConfig

| Field | Type | Description |
|-------|------|-------------|
| `type` | `string` | Check type (e.g., 'reachability', 'client_count') |
| `threshold` | `number \| null` | Threshold value |
| `operator` | `'gte' \| 'lte' \| 'eq'` | Comparison operator |

### DryRunResult

Maps to `POST /api/v1/deploy/dry-run` response.

| Field | Type | Description |
|-------|------|-------------|
| `riskScore` | `number` | Numeric risk score (0-100) |
| `riskLevel` | `'low' \| 'medium' \| 'high'` | Risk classification |
| `blastRadius` | `BlastRadius` | Impact scope |
| `warnings` | `string[]` | Potential issues |
| `policyViolations` | `string[]` | Policy violations found |

### BlastRadius

| Field | Type | Description |
|-------|------|-------------|
| `deviceCount` | `number` | Devices affected |
| `siteCount` | `number` | Sites affected |
| `estimatedClients` | `number` | Estimated client impact |

### Rollout

Maps to `GET /api/v1/deploy/rollouts` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Rollout UUID |
| `name` | `string` | Rollout plan name |
| `status` | `RolloutStatus` | Current rollout status |
| `goldenImageId` | `string \| null` | Associated golden image |
| `promotionMode` | `'automatic' \| 'manual'` | Wave promotion mode |
| `waves` | `RolloutWave[]` | Ordered wave definitions |
| `healthGates` | `HealthGate` | Gate criteria |
| `createdBy` | `string` | Creator identity |
| `createdAt` | `string` | ISO 8601 creation timestamp |

### RolloutStatus

```typescript
type RolloutStatus =
  | 'draft'
  | 'active'
  | 'paused'
  | 'completed'
  | 'cancelled';
```

### RolloutWave

| Field | Type | Description |
|-------|------|-------------|
| `waveNumber` | `number` | Wave sequence number (1-based) |
| `status` | `'pending' \| 'in_progress' \| 'completed' \| 'failed' \| 'rolled_back'` | Wave status |
| `targets` | `string[]` | Device/site IDs in this wave |
| `completedCount` | `number` | Devices completed |
| `failedCount` | `number` | Devices failed |
| `healthGatePassed` | `boolean \| null` | Health gate result (null if not evaluated) |

### HealthGate

| Field | Type | Description |
|-------|------|-------------|
| `minClientPercent` | `number` | Minimum client count as % of pre-upgrade |
| `maxAlarmCount` | `number` | Maximum allowed alarms |
| `waitMinutes` | `number` | Minutes to wait after wave before evaluating |

### ChangeTemplate

Maps to `GET /api/v1/deploy/templates` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Template UUID |
| `name` | `string` | Template display name |
| `description` | `string` | Template description |
| `parameters` | `TemplateParam[]` | User-fillable parameters |
| `payload` | `Record<string, unknown>` | Template payload with `{{param}}` placeholders |

### TemplateParam

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Parameter name |
| `label` | `string` | Human-readable label |
| `type` | `'string' \| 'number' \| 'boolean' \| 'select'` | Input type |
| `required` | `boolean` | Whether parameter is required |
| `options` | `string[] \| null` | Options for select type |
| `defaultValue` | `unknown \| null` | Default value |

### GoldenImage

Maps to `GET /api/v1/deploy/golden-images` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Image UUID |
| `version` | `string` | Firmware version string |
| `deviceType` | `'ap' \| 'switch' \| 'gateway'` | Target device type |
| `models` | `string[]` | Compatible model names |
| `status` | `'pending' \| 'approved' \| 'retired'` | Approval lifecycle |
| `approvedBy` | `string \| null` | Approver identity |
| `registeredAt` | `string` | ISO 8601 registration timestamp |

---

## Domain 4: Audit (Records, Export, Compliance)

### AuditRecord

Maps to `GET /api/v1/audit/records` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Record UUID |
| `timestamp` | `string` | ISO 8601 event timestamp |
| `actor` | `string` | Who performed the action |
| `entityType` | `string` | Affected entity type |
| `entityId` | `string` | Affected entity ID |
| `entityName` | `string` | Affected entity display name |
| `changeType` | `string` | Type of change (create, update, delete, restore) |
| `changeSummary` | `string` | Human-readable summary |
| `revisionId` | `string \| null` | Linked config revision ID |
| `deployJobId` | `string \| null` | Linked deployment job ID |
| `oldValues` | `Record<string, unknown> \| null` | Previous field values |
| `newValues` | `Record<string, unknown> \| null` | New field values |

### AuditExport

Maps to `POST /api/v1/audit/export` and `GET /api/v1/audit/export/{id}` responses.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Export job UUID |
| `status` | `'pending' \| 'generating' \| 'completed' \| 'failed'` | Export status |
| `format` | `'csv' \| 'json'` | Export format |
| `filters` | `AuditFilters` | Filters applied |
| `downloadUrl` | `string \| null` | Download URL when completed |
| `progress` | `number` | Progress percentage (0-100) |

### AuditFilters

| Field | Type | Description |
|-------|------|-------------|
| `entityType` | `string \| null` | Filter by entity type |
| `actor` | `string \| null` | Filter by actor |
| `startDate` | `string \| null` | ISO 8601 start of date range |
| `endDate` | `string \| null` | ISO 8601 end of date range |
| `changeType` | `string \| null` | Filter by change type |

### IncidentCorrelation

Maps to `GET /api/v1/audit/correlations` response items.

| Field | Type | Description |
|-------|------|-------------|
| `changeId` | `string` | Correlated audit record ID |
| `incidentType` | `'alarm' \| 'sle_degradation'` | Type of incident |
| `incidentId` | `string` | Incident identifier |
| `confidenceScore` | `number` | Correlation confidence (0.0-1.0) |
| `detectionMethod` | `string` | How the correlation was detected |
| `timestamp` | `string` | ISO 8601 correlation timestamp |

### CompliancePack

Maps to compliance pack endpoints.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Pack UUID |
| `framework` | `'sox' \| 'pci_dss' \| 'soc2'` | Compliance framework |
| `status` | `'pending' \| 'generating' \| 'completed' \| 'failed'` | Generation status |
| `startDate` | `string` | ISO 8601 period start |
| `endDate` | `string` | ISO 8601 period end |
| `downloadUrl` | `string \| null` | Download URL when completed |
| `progress` | `number` | Progress percentage (0-100) |

---

## Domain 5: Sync & Inventory (Sync Status, Drift, Devices)

### SyncStatus

Maps to `GET /api/v1/sync/status` response.

| Field | Type | Description |
|-------|------|-------------|
| `orgId` | `string` | Organization ID |
| `lastSyncAt` | `string` | ISO 8601 last sync timestamp |
| `nextPollAt` | `string` | ISO 8601 next scheduled poll |
| `state` | `'synced' \| 'stale' \| 'error'` | Overall sync state |
| `entityCounts` | `EntitySyncCount[]` | Per-entity-type counts |

### EntitySyncCount

| Field | Type | Description |
|-------|------|-------------|
| `entityType` | `string` | Entity type |
| `total` | `number` | Total entities |
| `synced` | `number` | Successfully synced |
| `stale` | `number` | Out of date |
| `error` | `number` | Sync errors |

### InventoryDevice

Maps to `GET /api/v1/sync/inventory/devices` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Device UUID |
| `orgId` | `string` | Organization ID |
| `siteId` | `string` | Site ID |
| `name` | `string` | Device name |
| `type` | `'ap' \| 'switch' \| 'gateway'` | Device type |
| `model` | `string` | Hardware model |
| `serial` | `string` | Serial number |
| `mac` | `string` | MAC address |
| `firmwareVersion` | `string` | Current firmware |
| `connectionStatus` | `'connected' \| 'disconnected'` | Live connection state |
| `uptime` | `number \| null` | Uptime in seconds |
| `lastSeenAt` | `string \| null` | ISO 8601 last seen timestamp |

### InventorySite

Maps to `GET /api/v1/sync/inventory/sites` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Site UUID |
| `orgId` | `string` | Organization ID |
| `name` | `string` | Site name |
| `location` | `string \| null` | Geographic location |
| `deviceCount` | `number` | Total devices at site |

### InventoryOrg

Maps to `GET /api/v1/sync/inventory/orgs` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Organization UUID |
| `name` | `string` | Organization name |
| `siteCount` | `number` | Total sites |
| `deviceCount` | `number` | Total devices |

### DriftAlert

Maps to `GET /api/v1/sync/drift/alerts` response items.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Alert UUID |
| `entityType` | `string` | Drifted entity type |
| `entityId` | `string` | Drifted entity ID |
| `entityName` | `string` | Drifted entity display name |
| `severity` | `'low' \| 'medium' \| 'high' \| 'critical'` | Alert severity |
| `fieldCount` | `number` | Number of drifted fields |
| `detectedAt` | `string` | ISO 8601 detection timestamp |
| `acknowledged` | `boolean` | Whether operator acknowledged |
| `baselineId` | `string` | Associated baseline ID |
| `diff` | `DiffChange[]` | Field-level diff (reuses Domain 2 type) |

---

## Shared Types

### ApiResponse\<T\>

Standard response envelope wrapping all API calls.

| Field | Type | Description |
|-------|------|-------------|
| `data` | `T` | Response payload |
| `meta` | `PaginationMeta \| null` | Pagination info (list endpoints) |
| `errors` | `ApiError[]` | Error array (empty on success) |

### PaginationMeta

| Field | Type | Description |
|-------|------|-------------|
| `page` | `number` | Current page (1-based) |
| `perPage` | `number` | Items per page |
| `total` | `number` | Total items |
| `totalPages` | `number` | Total pages |

### ApiError

| Field | Type | Description |
|-------|------|-------------|
| `code` | `string` | Machine-readable error code |
| `message` | `string` | Human-readable message |
| `field` | `string \| null` | Affected field (for validation errors) |
| `detail` | `string \| null` | Additional context |

### NotificationItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Notification UUID |
| `type` | `'approval_request' \| 'drift_alert' \| 'deploy_status' \| 'export_ready'` | Notification category |
| `severity` | `'info' \| 'warning' \| 'error'` | Notification severity |
| `title` | `string` | Short notification title |
| `message` | `string` | Notification body |
| `timestamp` | `string` | ISO 8601 timestamp |
| `read` | `boolean` | Whether operator has read |
| `linkTo` | `string` | Route path to relevant view |

### TimezonePreference

| Field | Type | Description |
|-------|------|-------------|
| `mode` | `'local' \| 'utc' \| 'site'` | Active timezone display mode |
| `siteTimezone` | `string \| null` | IANA timezone from site config |

---

## State Transitions

### DeployJob Lifecycle

```
draft → pending_approval → approved → scheduled → running → completed
                                                          → failed → rolled_back
                        → cancelled (from any pre-running state)
```

### Rollout Lifecycle

```
draft → active → paused → active (resume)
              → completed
              → cancelled
```

### DriftAlert Lifecycle

```
detected → acknowledged → remediated (cleared)
                        → accepted (baseline updated, cleared)
```

### AuditExport / CompliancePack Lifecycle

```
pending → generating → completed (download available)
                     → failed
```
