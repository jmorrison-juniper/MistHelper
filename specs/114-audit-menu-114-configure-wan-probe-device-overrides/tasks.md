# Tasks for Menu 114 (Configure WAN Probe Device Overrides)

Grouped by component — each task should be added to the tracker with owner, estimate, acceptance criteria.

API & Schema
- [ ] Create Pydantic schemas: WanProbeOverrideCreate, WanProbeOverrideUpdate, WanProbeOverrideResponse.
  - Validate IP addresses, port ranges, probe_type enumeration.
  - Ensure actor and reason fields are required for mutating endpoints.
- [ ] Add FastAPI route module: src/api/routes/wan_probes.py with CRUD endpoints and bulk apply endpoint.
  - Integrate with get_authenticated_user and get_db_session.
  - Implement permission checks, site exclusion check (MIST_SITE_EXCLUDE_PREFIX), and interface whitelist validation (MIST_WAN_TARGET_PORTS).
- [ ] Emit AuditRecord for every change. Use existing AuditRecord model; populate old_values/new_values.

DB & Persistence
- [ ] Create new SQLAlchemy model wan_probe_device_overrides in src/shared/models (or new file). Fields per Spec.
- [ ] Add Alembic migration script to create table and indexes. Include a migration for existing installations.
- [ ] Add repository/DAO functions for create/update/delete/get/list.

CLI / MistHelper
- [ ] Implement WANProbeDeviceOverrideManager.configure() function in the CLI (pattern from other destructive menus):
  - Fetch device info (name, serial, site), show summary to user.
  - Validate interface against env whitelist.
  - Prompt for confirmation; in non-interactive mode require X-Force-Destructive or flag.
  - Call the server API or local DB layer depending on context (mist-ops-platform server vs local script usage).
- [ ] Register menu 114 in the CLI menu mapping (if not already) with title and description.

Worker / Bulk operations
- [ ] Implement ScheduledJob creation for bulk_apply endpoint.
- [ ] Implement worker task (src/worker/tasks/wan_probe_tasks.py) that iterates devices and applies overrides with retries, checkpointing, and emits JobCheckpoint records.

Export & SQL export compatibility
- [ ] Integrate wan_probe_device_overrides into DataExporter config (if present) so exports include the table.
- [ ] Implement fallback export helper (streaming) to write CSV of overrides and join audit records when DataExporter absent.
- [ ] Include sample SQL export query in documentation.

Testing
- [ ] Unit tests for validation logic (IP, interface, probe_type, interval, enabled flag).
- [ ] Unit tests for API endpoints using FastAPI TestClient and DB fixtures.
- [ ] Integration tests for audit emission (assert AuditRecord rows created) and export outputs.
- [ ] CLI tests for interactive confirmation flow using test harness / monkeypatch input.

Docs & Ops
- [ ] Add API docs (OpenAPI) auto-generated via FastAPI; add docstrings and example request/response.
- [ ] Update web_portal/menu_registry.py descriptions.
- [ ] Add runbook for rollback (how to delete overrides) and how to recover from Mist API partial failure.

Security & Review
- [ ] Security review for actor/reason recording, logs, and site-exclusion enforcement.
- [ ] Add monitoring/alerting on bulk destructive jobs (ex: high failure rate or many reverts).

Deployment / Migrations
- [ ] Release migration scripts and DB backup guidance.
- [ ] Release notes detailing the new table, new API endpoints, and required environment variables (MIST_WAN_TARGET_PORTS, MIST_SITE_EXCLUDE_PREFIX).

