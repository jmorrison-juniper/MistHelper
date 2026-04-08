# Plan: Implement Configure WAN Probe Device Overrides (Menu 114)

Objective

Provide an implementation that enables single-device and bulk device WAN probe override configuration with safe-guards, audit trail, exportability, and API endpoints consistent with mist-ops-platform architecture.

Phases

1) Design & spec finalization (this phase)
   - Lock request/response schemas, DB schema, audit behavior, and CLI/interactive flows.
   - Review with security/compliance stakeholders for site-exclusion policy and actor/reason requirements.

2) Server API implementation
   - Add new route module (e.g., src/api/routes/wan_probes.py) with endpoints:
     - PUT /orgs/{org_id}/devices/{device_id}/wan_probe_overrides
     - PATCH /orgs/{org_id}/devices/{device_id}/wan_probe_overrides/{override_id}
     - DELETE /orgs/{org_id}/devices/{device_id}/wan_probe_overrides/{override_id}
     - GET /orgs/{org_id}/devices/{device_id}/wan_probe_overrides
     - POST /orgs/{org_id}/wan_probe_overrides/bulk_apply (async)
   - Wire in authentication (get_authenticated_user) and dependency injection (get_db_session).
   - Validate payloads using Pydantic models (src/api/schemas).
   - Emit AuditRecord entries on every mutating call.
   - Implement optimistic concurrency via revision field.

3) DB schema & persistence
   - Create new SQLAlchemy model in src/shared/models (e.g., wan_probe.py or add to inventory/operations module). Use JSONB for metadata and store revision/time fields.
   - Create Alembic migration scripts to create the new table and indexes.

4) CLI / MistHelper integration
   - Implement WANProbeDeviceOverrideManager.configure() in the CLI code (pattern similar to other destructive menu functions).
   - Add interactive confirmation flow for destructive ops and non-interactive headers/flags for automation.
   - Validate MIST_WAN_TARGET_PORTS / MIST_SITE_EXCLUDE_PREFIX environment settings.

5) Bulk jobs & scheduling
   - Use existing ScheduledJob and JobCheckpoint models for long-running, bulk override application.
   - Implement worker task (src/worker/tasks) to perform bulk ops and record progress in job_checkpoints.

6) Export & tooling
   - Add DataExporter integration to include the wan_probe_device_overrides table and related audit records.
   - If DataExporter unavailable, add a streaming CSV export helper in maps_manager or a new export module consistent with existing exports.

7) Tests
   - Unit tests for validation & business logic.
   - Integration tests for endpoints using test DB and mocked Mist API.
   - E2E smoke test for CLI interactive flow with --test flag.

8) Documentation & rollout
   - Document CLI usage and API docs (OpenAPI schema additions).
   - Add menu entry description to web_portal/menu_registry.py.
   - Prepare release notes and migration instructions for DB.

Estimated timeline (rough, can be adjusted based on team size)
- Design/spec review: 1 day
- API + DB model + migration: 2-3 days
- CLI integration + interactive confirmation: 1 day
- Bulk jobs + worker tasks: 2 days
- Export & DataExporter integration / fallback: 1 day
- Tests + docs: 2 days
- Buffer / review / bugfixes: 2 days

Total: ~11–14 engineering days (single engineer). If parallelized (API + DB + CLI split), ~6–8 calendar days.

