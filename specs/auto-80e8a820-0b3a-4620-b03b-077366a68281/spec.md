# Spec: Configure WAN Probe Device Overrides (Menu 114)

Target path: specs\\114-audit-menu-114-configure-wan-probe-device-overrides\\

Menu metadata
- menu_id: 114
- title: Configure WAN Probe Device Overrides
- function_ref: WANProbeDeviceOverrideManager.configure
- category: destructive

Summary

Provide an interactive / programmatic operation that allows an operator to create, update, or delete WAN probe configuration overrides on a per-device basis. This operation is destructive (changes device config) and must produce audit records and safe-guards (confirmation, validation, scope checks). It must integrate with the operations audit trail, be idempotent where possible, and allow export of changes for compliance.

User stories / high-level requirements
- As a network operator I want to set a WAN probe override for a gateway device so that synthetic tests target the desired interface/IP.
- As a compliance reviewer I want an audit record for every change (who, what, old/new values, when).
- As an automation engineer I want a well-defined API so I can script batch updates across devices.
- As a safety-conscious operator I want confirmation, site-exclusion rules, and validation to avoid accidental destructive changes.

Acceptance criteria (explicit, testable)
1. Functionality
   - Given a valid org_id and device_id, a POST (create) or PATCH (update) request applies a WAN probe override on the device and returns HTTP 200 with the resulting override object.
   - A DELETE request removes the device-specific override and returns HTTP 204 (no content).
   - The configure flow validates the override payload (required fields present, IPs valid, referenced interface name is in allowed MIST_WAN_TARGET_PORTS) and rejects invalid payloads with HTTP 400 and helpful error messages.
   - If the device is not found or not in the organisation, return HTTP 404.

2. Safety & constraints
   - Operations fail if the target site name starts with MIST_SITE_EXCLUDE_PREFIX (configurable), returning HTTP 403.
   - Before performing the destructive change, interactive CLI must display a clear confirmation (device name/serial, site, override details) and require explicit approval. Non-interactive API calls must provide a reason and actor field; high-risk operations must require an explicit header/API flag (e.g., X-Force-Destructive: true) for scripted runs.

3. Audit & observability
   - Each create/update/delete emits an AuditRecord entry with actor (user/email), entity_type="wan_probe_override", entity_id=device_id, change_type="create/update/delete", old_values and new_values JSON populated.
   - Audit records are persisted to the audit_records table (or equivalent) and are retrievable via the existing audit endpoints.
   - The system returns a correlation id in the response headers for tracing in logs.

4. Concurrency & idempotence
   - Multiple identical create/update requests are idempotent (re-applying same payload results in no-op and returns 200 with a message indicating no change).
   - Update requests include optimistic concurrency via an optional revision token or last_updated timestamp; if the revision is stale, return HTTP 409 with current resource snapshot.

5. API ergonomics
   - Provide REST endpoints with predictable URL patterns and JSON request/response schemas that match other ops endpoints in mist-ops-platform.

API endpoints (proposal)

Note: These endpoints are proposed to be added to the mist-ops-platform API (prefix /api/v1 or /wan-probes as appropriate). Use FastAPI patterns consistent with existing routes (/api/v1/*).

1) Create or update device override (idempotent upsert)
- Method: PUT
- Path: /api/v1/orgs/{org_id}/devices/{device_id}/wan_probe_overrides
- Request JSON body (application/json):
  - probe_type: string (e.g., "icmp", "http", "tcp")  -- required
  - target_ip: string (IPv4 or IPv6) -- required
  - target_port: int | null (for tcp/http probes) -- optional
  - interface: string (e.g., "ge-0/0/0") -- required when interface-specific override
  - interval_seconds: int (probe frequency) -- optional, default 60
  - enabled: boolean -- optional, default true
  - actor: string -- required for API (email/service-account)
  - reason: string -- required for destructive operations
  - revision: string|int -- optional optimistic concurrency token
- Response: 200 OK
  - body: { override_id: uuid, org_id, device_id, probe_type, target_ip, target_port, interface, interval_seconds, enabled, created_at, updated_at, revision }
- Headers:
  - X-Correlation-ID: uuid
- Errors:
  - 400 Bad Request — validation failure
  - 403 Forbidden — site excluded or insufficient permissions
  - 404 Not Found — device/org not found
  - 409 Conflict — revision mismatch

2) Partial update (PATCH)
- Method: PATCH
- Path: /api/v1/orgs/{org_id}/devices/{device_id}/wan_probe_overrides/{override_id}
- Request: partial fields to change + actor + reason + revision optional
- Response: 200 OK with updated object
- Errors: same as above

3) Delete override
- Method: DELETE
- Path: /api/v1/orgs/{org_id}/devices/{device_id}/wan_probe_overrides/{override_id}
- Query / header: actor and reason required
- Response: 204 No Content
- Side effects: emits audit record with old_values and new_values = null

4) List device overrides (read-only)
- Method: GET
- Path: /api/v1/orgs/{org_id}/devices/{device_id}/wan_probe_overrides
- Response: 200 OK: [ {override}, ... ]

5) (Optional) Bulk apply for multiple devices
- Method: POST
- Path: /api/v1/orgs/{org_id}/wan_probe_overrides/bulk_apply
- Body: { devices: [device_id,...], override_payload: {...}, actor, reason }
- Response: 202 Accepted — starts async job (ScheduledJob) and returns job_id
- This follows existing ScheduledJob model for long-running destructive operations.

Schema examples (concise)
- Override object fields (canonical):
  - override_id: UUID (server assigned)
  - org_id: UUID
  - device_id: UUID
  - probe_type: str
  - target_ip: str
  - target_port: int | null
  - interface_name: str | null
  - interval_seconds: int
  - enabled: bool
  - created_by: str
  - created_at: timestamp
  - updated_at: timestamp
  - revision: int

Security considerations

1) Authentication & Authorization
- All endpoints require authenticated users via existing auth middleware (CurrentUser) used in mist-ops-platform.
- Only users with organization-level "admin" or appropriate "gateway:modify" capability may perform creates/updates/deletes.
- Support MSP-level role scoping — ensure MSP tokens or session-based login check whether user has the right org scope.

2) Audit & Non-repudiation
- Every change must produce an AuditRecord entry with actor, timestamp, entity_type="wan_probe_override", entity_id=device_id, change_type and old/new payloads.
- Require actor and reason in API requests and record both in the audit record and in ScheduledJob metadata for bulk/async operations.

3) Safety checks
- Validate interface names against MIST_WAN_TARGET_PORTS env list. If interface not in whitelist, reject request unless an explicit override allow list environment variable or feature flag is set and the actor has elevated privilege.
- Enforce site exclusion by MIST_SITE_EXCLUDE_PREFIX. If site name begins with the prefix, return 403 and require out-of-band approval.
- CLI interactive flows must show a two-step confirmation for destructive actions; non-interactive flows require explicit X-Force-Destructive header and appropriate logging.

4) Rate limiting & throttling
- Implement per-org rate limiting for destructive operations (e.g., max 10 WAN override changes per minute) to protect the API and downstream Mist API quotas.

5) Input sanitization
- Strict schema validation of IP addresses and integers. Reject malformed JSON and extra fields.
- Escape or refuse potentially dangerous characters in "reason" or "actor" inputs used in logs.

6) Concurrency
- Use optimistic concurrency via revision field to avoid blind overwrites. On conflict, return 409 with current resource snapshot.

Data model & persistence

Primary storage options (prefer using the existing mist-ops-platform DB):
- New table: wan_probe_device_overrides
  - override_id UUID PK
  - org_id UUID (indexed)
  - device_id UUID (indexed)
  - probe_type TEXT
  - target_ip TEXT
  - target_port INT
  - interface_name TEXT
  - interval_seconds INT
  - enabled BOOLEAN
  - metadata JSONB (freeform: original_mist_payload, validation_warnings, source)
  - created_by TEXT
  - created_at TIMESTAMP with timezone
  - updated_at TIMESTAMP with timezone
  - revision INT (for optimistic concurrency)

Alternatively: store overrides as AuditRecord old/new JSON and operational data in ScheduledJob records, but an explicit table is recommended for read/lookup performance and exports.

Audit linkage
- AuditRecord.entity_type value: "wan_probe_override"
- AuditRecord.entity_id: device_id (the device that changed)
- AuditRecord.old_values / new_values: full override JSON

SQL export strategy

Goal: All changes must be exportable to CSV/SQL for compliance.

Preferred approach (if DataExporter exists)
- Use the existing DataExporter abstraction to export the wan_probe_device_overrides table and related audit_records rows for the org within a time range.
- Ensure DataExporter applies canonical primary keys and natural keys (org_id + device_id + override_id) so incremental exports are simple.

Remediation / fallback (if DataExporter is not available)
- Add an export helper function in mist-ops-platform that:
  1. Executes a SELECT on wan_probe_device_overrides where org_id = :org_id and updated_at >= :since
  2. Joins audit_records to include the most recent change record for each override
  3. Writes results to CSV using a standardized header (include JSONB fields as JSON string columns)
- Provide a migration/DDL script sample to create the wan_probe_device_overrides table and the necessary indexes.

DDL example (Postgres):

CREATE TABLE wan_probe_device_overrides (
  override_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES orgs(org_id),
  device_id UUID NOT NULL,
  probe_type TEXT NOT NULL,
  target_ip TEXT NOT NULL,
  target_port INTEGER,
  interface_name TEXT,
  interval_seconds INTEGER DEFAULT 60,
  enabled BOOLEAN DEFAULT true,
  metadata JSONB,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX ON wan_probe_device_overrides (org_id);
CREATE INDEX ON wan_probe_device_overrides (device_id);

If DataExporter is not used: ensure the export helper function uses server-side pagination and streaming to avoid memory pressure and write CSV to data/ directory (same pattern as other exports in the codebase).

Operational concerns
- When applying overrides via Mist API call, handle Mist API failure patterns (retry, exponential backoff, idempotency tokens). If the provider call fails after local DB update, roll back the DB update and emit a failed audit record.
- For bulk operations, use ScheduledJob table pattern. Each bulk job should create ScheduledJob with pre_check_defs/post_check_defs and a job_id returned to caller.
- Support a dry-run mode that validates and simulates changes and returns planned changes without applying them.

Testing & verification
- Unit tests for validation logic (IP parsing, interface whitelist check).
- Integration tests that run in --test mode against a mocked mistapi that returns predictable responses.
- End-to-end tests for audit emission and export CSV format.

Notes
- This spec assumes the existence of the mist-ops-platform authentication & audit infrastructure (CurrentUser, AuditRecord). It integrates with those models and patterns.
- Because this is labelled "destructive", UI/CLI behavior must be more conservative than read-only operations and require explicit operator confirmations.

