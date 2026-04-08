File: specs\\118-audit-menu-118-site-auto-upgrade-configuration\\spec.md

Title: Site Auto-Upgrade Configuration (menu 118)
Function reference: SiteAutoUpgradeConfigurator.execute
Category: config_mgmt

1. Purpose

This spec defines a Site Auto-Upgrade Configuration feature that allows operators to define, schedule, stage (wave) and execute automated software/firmware upgrades for devices at a site-level. The feature provides a persistent "upgrade plan" object that the system schedules and runs, with controls for maintenance windows, staged rollouts (waves), success thresholds, retry/backout rules, notifications and audit logging.

2. Scope

- Create, update, list, get, schedule, execute and cancel site-level auto-upgrade plans.
- Support scheduled upgrades with timezone-aware windows and blackout periods.
- Support staged (wave) rollouts across site targets with configurable percentages / explicit target groups.
- Enforce policies: concurrency limits, success thresholds, automatic rollback or pause, retry/backoff, and escalation notifications.
- Expose an API for plan CRUD and execution; export plan data for audit and reporting in SQL-friendly format.

3. Inputs

User-provided inputs required to create an upgrade plan:
- plan_name (string): Friendly name.
- site_id (UUID/string): Target site identifier.
- target_selector (object): Device selector for the plan (explicit device list OR filter expression: by role, model, tag, sw_version).
- firmware_image (string/URL/ID): Firmware/software to apply.
- scheduled_start (datetime, timezone-aware, ISO8601) OR immediate flag.
- maintenance_window (object): start_time_local (HH:MM), end_time_local (HH:MM), days_of_week (list), timezone (IANA tz).
- blackout_windows (optional array): periods to avoid.
- staging_policy (object): defines waves:
  - waves (array of wave objects): each wave has wave_id, target_percentage OR explicit_targets list, min_success_percent, max_concurrent_per_wave, min_wait_between_waves.
- concurrency (int): maximum concurrent device upgrades across waves (global limit).
- retry_policy (object): retry_count, retry_backoff_seconds, retry_on_transient_errors (boolean).
- rollback_policy (object): auto_rollback_on_failure (boolean), rollback_window_seconds, rollback_trigger_threshold (e.g., if > X% fail in wave or plan).
- notification_policy (object): email/slack/webhook list + events to notify (start, wave_complete, plan_complete, plan_failed).
- dry_run (boolean): validate-only mode to simulate plan and target counts without executing.
- tags/metadata (map)

System-calculated/optional inputs (not required from user):
- plan_id (UUID) assigned on creation.
- created_by, created_ts, modified_ts.

Validation rules (input constraints):
- scheduled_start must be in future if provided.
- maintenance_window must be at least X minutes long to permit upgrade (configurable default 30m).
- sum of waves' explicit target counts or percentages cannot exceed 100% unless explicit_targets provided and overlap rules defined.
- target_selector must resolve to >= 1 device unless dry_run.
- concurrency must be >= 1 and <= site-wide limit (config param).
- timezone must be valid IANA name.

4. Outputs

Primary outputs/effects produced by execute:
- Persistent Plan record (DB table: site_auto_upgrade_plans) containing all plan config and status.
- Plan lifecycle events (table site_auto_upgrade_events) for audit: scheduled, started, wave_started, device_started, device_success, device_failure, wave_completed, plan_completed, plan_failed, plan_cancelled.
- Scheduler jobs / messages enqueued to the orchestration engine (internal scheduler queue) to start waves and device jobs at the appropriate times.
- API responses for plan CRUD and status endpoints (JSON objects with plan metadata, current status, progress, per-wave breakdown, failures list).
- Notifications sent per configured notification_policy.
- Optional exports: SQL/CSV rows for audit and compliance reporting.

5. Policies (detailed)

A. Scheduling & Timezones
- Plans are scheduled with an ISO8601 scheduled_start and an associated timezone (IANA). Stored normalized to UTC but UI and maintenance windows are validated in local time.
- The plan will only run inside maintenance windows; if a plan start time falls outside the window, it will wait until the next valid window.

B. Staged (Wave) Rollouts
- Waves are defined in order; each wave must have either percentage or explicit target list. If percentage, the system resolves devices from target_selector in stable deterministic order (e.g., device_id ascending) to map targets to waves.
- A wave begins only after previous wave completes and the configured min_wait_between_waves elapsed, or after success_threshold met.
- min_success_percent per wave must be satisfied to proceed; otherwise apply failure/rollback policy.

C. Concurrency
- Global concurrency cap prevents too many devices being upgraded concurrently across all waves and plans on the same site or system-wide (configurable limit). A request to exceed will be queued or fail based on config.

D. Success & Failure Handling
- Success is confirmed when device reports upgrade success event within rollback_window or when orchestration confirms status.
- If failures in a wave exceed the wave's failure threshold (1 - min_success_percent), then: either pause, cancel, or auto-rollback depending on rollback_policy.
- Retries: transient failures can be retried per retry_policy. Permanent failures (e.g., incompatible image) are not retried.

E. Rollback & Recovery
- If auto_rollback_on_failure is true, the system will attempt to revert devices upgraded in the failed wave back to the prior version if a rollback image is available and within rollback_window.
- A separate rollback job is created and tracked in events table; rollbacks are treated as their own waves for concurrency planning.

F. Notifications & Auditing
- Send notifications at events defined in notification_policy.
- All plan state transitions and device events must be recorded as immutable audit events with timestamp, user( API key ), and reason.

G. Safety & Compliance
- Plans must be reviewable and cancellable; cancellations transition plan to CANCELLED state and attempt to halt further waves. Device-level in-flight jobs may still complete.
- For networks with regulatory constraints, the system will not schedule upgrades across blackout_windows.

6. API Endpoints (examples)

Base path: /api/v1/upgrade-plans

- POST /api/v1/upgrade-plans
  Purpose: Create a plan
  Request body: (JSON) {
    "plan_name": "string",
    "site_id": "uuid",
    "target_selector": {"tags": ["edge"], "role": "ap"},
    "firmware_image": "img-1234",
    "scheduled_start": "2026-05-01T01:00:00-07:00",
    "maintenance_window": {"start": "01:00", "end": "04:00", "days": ["mon","tue"], "timezone": "America/Los_Angeles"},
    "staging_policy": {"waves": [{"percentage": 10, "min_success_percent": 95, "min_wait_minutes": 30}, {"percentage": 50}], "concurrency": 20},
    "retry_policy": {"retry_count": 2, "backoff_seconds": 300}
  }
  Response: 201 Created with plan object including generated plan_id.

- GET /api/v1/upgrade-plans?site_id={site_id}
  Purpose: List plans for site (filterable by status, dates)

- GET /api/v1/upgrade-plans/{plan_id}
  Purpose: Get plan details and status, per-wave breakdown.

- POST /api/v1/upgrade-plans/{plan_id}/execute
  Purpose: Force execute (start now) respecting concurrency & maintenance windows unless override flag provided.
  Body: {"override_window": boolean}

- POST /api/v1/upgrade-plans/{plan_id}/cancel
  Purpose: Cancel a scheduled or running plan.

- POST /api/v1/upgrade-plans/{plan_id}/dry-run
  Purpose: Validate resolution of target_selector and wave mapping; returns counts and warnings.

- GET /api/v1/upgrade-plans/{plan_id}/export?format=sql|csv
  Purpose: Export plan + events for auditing.

7. Storage / Event Model (high-level)

Key persistent tables (logical):
- site_auto_upgrade_plans
  - plan_id (UUID PK), site_id, plan_name, target_selector (JSON), firmware_image, scheduled_start_utc, maintenance_window (JSON), staging_policy (JSON), retry_policy (JSON), rollback_policy (JSON), notification_policy (JSON), concurrency, status, created_by, created_ts, modified_ts, metadata (JSON)

- site_auto_upgrade_waves
  - wave_id (UUID PK), plan_id (FK), ordinal (int), percentage (float, nullable), explicit_targets (JSON), min_success_percent, min_wait_seconds, max_concurrent

- site_auto_upgrade_events
  - event_id (UUID PK), plan_id (FK), wave_id (FK nullable), device_id (nullable), event_type (enum), event_ts, details (JSON), actor

- site_auto_upgrade_targets (optional normalized mapping)
  - target_id (PK UUID), plan_id (FK), device_id, assigned_wave_id, status (pending/in_progress/success/failure), last_update_ts

8. SQL Export Strategy

Goals:
- The export must produce an auditable snapshot of plans and all events that is importable into common RDBMS systems (Postgres, MySQL, MSSQL).
- Exports must be deterministic and optionally anonymizable (mask device ids/IPs for compliance).

Export formats supported:
- SQL INSERT statements for tables site_auto_upgrade_plans, site_auto_upgrade_waves, site_auto_upgrade_targets, site_auto_upgrade_events; compatible with standard SQL types.
- CSV for each table with headers.

Design choices and mapping:
- Use canonical tables described above; store complex objects (target_selector, maintenance_window, policies) as JSON columns.
- When exporting to SQL, JSON fields will be exported as JSON literals using the database's supported literal (e.g., in Postgres as '...') — implement safe escaping.
- Provide an export option for normalization (flatten arrays like explicit_targets into site_auto_upgrade_targets rows).

Primary Key strategy (recommended):
- Use UUIDv4 GUIDs for plan_id, wave_id, event_id, target_id to avoid collisions on distributed systems. (See primary_key_suggestions below.)

Anonymization option:
- Exporter supports mapping device_id -> pseudonymized token per export with a reproducible salt or one-time salt depending on audit needs.

Export performance considerations:
- For large event sets, stream exports and paginate; include a consistent snapshot timestamp.
- Add indexes on plan_id, site_id, device_id, event_ts for fast queries post-import.

9. Test Plan (high-level)

Unit tests:
- Input validation tests: invalid start times, invalid timezones, illegal percentages, overlapping waves.
- Policies: concurrency validation, maintenance window enforcement.
- Dry-run behavior: target resolution and deterministic mapping tests.

Integration tests:
- End-to-end plan creation -> scheduler enqueue -> wave creation -> device job submission (mock devices) -> event ingestion -> plan success path.
- Failure scenarios: wave fails beyond threshold triggers cancel, pause or rollback depending on rollback_policy.
- Retry logic: transient failures retried with backoff.

Contract tests:
- API schema conformance for create/list/get/execute/cancel.

Load tests:
- Create plans targeting thousands of devices and ensure wave resolution and export scale.
- Concurrency limit enforcement under heavy load.

Security tests:
- Ensure only authorized roles can create/execute/cancel plans.
- Test anonymization on export and ensure no PII leaks.

Acceptance criteria (example):
- Plans scheduled in a maintenance window start at the correct local time.
- Waves progress only after meeting min_success_percent; failure paths follow rollback_policy.
- All plan lifecycle events are written to events table with timestamps and actors.
- SQL/CSV exports load into a clean schema producing the same counts as the API.

10. Audit & Compliance

- All API changes and user actions must be auditable: who created/modified/cancelled and timestamps.
- Exports must include event audit trails and be reproducible for a time-window snapshot.

11. Security

- Enforce RBAC: only roles with upgrade permission can create/execute/cancel plans.
- Protect firmware_image references: check that the image is valid and user has permission to use it.
- Sign or verify firmware_image before scheduling if platform supports image signing.

12. Backwards Compatibility & Migration Notes

- If introducing new tables, provide DB migrations to create tables and backfill minimal state (none required for new features).
- Existing device-level upgrade services must be integrated via the orchestration queue; define an adapter interface if necessary.

13. Files & Paths

Target folder for spec and artifacts:
- specs\\118-audit-menu-118-site-auto-upgrade-configuration\\

End of spec.md

