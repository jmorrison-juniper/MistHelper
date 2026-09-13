# Tasks: Mist Ops Platform

**Input**: Design documents from `/specs/001-mist-ops-platform/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks included per constitution Principle IV (Full Deployment Pipeline).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Exact file paths from plan.md project structure included

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffold, dependencies, tooling, container definitions

- [ ] T001 Create project directory structure per plan.md (src/api/, src/worker/, src/shared/, tests/, migrations/, deploy/, docs/)
- [ ] T002 Create pyproject.toml with all 21 runtime and 7 dev dependencies from research.md R-11
- [ ] T003 [P] Configure ruff linter and mypy type checker in pyproject.toml (enforce max 25 lines per function, max 5 params)
- [ ] T004 [P] Create deploy/Containerfile.api for the FastAPI service container
- [ ] T005 [P] Create deploy/Containerfile.worker for the Celery worker container
- [ ] T006 [P] Create deploy/compose.yml for local dev (PostgreSQL 16, Redis 7, MinIO, Vault)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

### Database & Configuration

- [ ] T007 Create SQLAlchemy DeclarativeBase, TimestampMixin, and UUIDPKMixin in src/shared/models/base.py
- [ ] T008 [P] Create pydantic-settings AppSettings class in src/shared/config/settings.py (env vars from quickstart.md)
- [ ] T009 [P] Create constants and enums in src/shared/config/constants.py (EntityType, DeviceType, JobStatus, AlertType per data-model.md)
- [ ] T010 Create async engine factory and session dependency in src/shared/db.py (asyncpg, partition-aware)
- [ ] T011 Create Organization, Site, Device models (E-00, E-01, E-02, E-03) in src/shared/models/inventory.py (includes MSP entity)
- [ ] T012 Create SyncLedgerEntry model (E-19) in src/shared/models/inventory.py and WebhookEnvelope model (E-20) in src/shared/models/config.py
- [ ] T013 Create Alembic env.py with async migration support in migrations/env.py
- [ ] T014 Create initial migration for inventory tables with hash partitioning (16 partitions for org_id) in migrations/versions/

### Mist API Integration Layer

- [ ] T015 [P] Create Mist entity type mappings and ENTITY_ENDPOINT_MAP in src/shared/mist/types.py (R-05 table)
- [ ] T016 [P] Create per-org Redis rate limiter (sliding window) in src/shared/mist/rate_limit.py (R-06)
- [ ] T017 Create APISession factory with Vault token retrieval and caching in src/shared/mist/session.py (R-07)
- [ ] T018 Create MistEndpointService class with read/write methods in src/shared/mist/endpoints.py (R-05 mapping)

### FastAPI Scaffold

- [ ] T019 Create FastAPI app factory with router mounting and lifespan in src/api/main.py
- [ ] T020 [P] Create auth middleware (Bearer token + session cookie, Mist privilege cache, scope enforcement per FR-025: filter query results to user's MSP/org/site privileges) in src/api/middleware/auth.py (R-07)
- [ ] T021 [P] Create request/response structured logging middleware in src/api/middleware/logging.py
- [ ] T022 [P] Create per-org rate-limit middleware in src/api/middleware/rate_limit.py
- [ ] T023 Create common Pydantic schemas (ResponseEnvelope, ErrorDetail, PaginationMeta, ConfirmBody) in src/api/schemas/common.py
- [ ] T024 Create dependency injection providers (get_db_session, get_current_user, get_mist_session) in src/api/deps.py
- [ ] T025 Create health and readiness endpoints (/healthz, /readyz, /metrics) in src/api/routes/health.py

### Celery Scaffold

- [ ] T026 Create Celery app, broker config, and Beat schedule in src/worker/celeryconfig.py (R-09)
- [ ] T027 [P] Create notification dispatch service (EmailAdapter, WebhookAdapter) in src/shared/services/notification.py (R-12)
- [ ] T028 [P] Create notify_tasks (send_notification Celery task) in src/worker/tasks/notify_tasks.py

### Inventory Sync (Foundation for All Stories)

- [ ] T029 Create inventory sync logic (orgs, sites, devices from Mist API) in src/worker/sync/inventory.py
- [ ] T030 Create sync_tasks (periodic inventory sync Celery task, Beat every 5 min) in src/worker/tasks/sync_tasks.py
- [ ] T031 Create auth service (Mist session mgmt, privilege cache in Redis) in src/shared/services/auth.py
- [ ] T032 Create inventory and sync-status Pydantic schemas in src/api/schemas/sync.py (inventory + sync status only)
- [ ] T033 Create sync route with GET /sync/status, POST /sync/trigger, GET /inventory/* in src/api/routes/sync.py
- [ ] T034 Create NotificationChannel model (E-18) in src/shared/models/operations.py
- [ ] T035 Create notification channel CRUD endpoints in src/api/routes/health.py (notification channels are a system-level concern, co-located with health endpoints per api-overview.md)

**Checkpoint**: Foundation ready — inventory syncing from Mist, API serving health + inventory, Celery processing tasks

---

## Phase 3: User Story 1 — Historical State Investigation ("Time-Travel") (Priority: P1) MVP

**Goal**: Operators rewind to any past timestamp to see device config, port states, client counts, and health metrics as they were at that moment.

**Independent Test**: Ingest historical snapshots from Mist API, query a past timestamp, verify returned state matches captured data. Delivers immediate value as a standalone network forensics tool.

### Implementation for User Story 1

- [X] T036 [P] [US1] Create ConfigRevision model (E-04) with hash partitioning and time-travel index in src/shared/models/config.py
- [X] T037 [P] [US1] Create DeviceStatusSnapshot model (E-05) with hash partitioning in src/shared/models/config.py
- [X] T038 [US1] Create migration for config_revisions and device_status_snapshots (16 hash partitions each, dedup unique constraint) in migrations/versions/
- [X] T039 [US1] Create config snapshot sync logic (fetch device/site config, compute content_hash, store if changed) in src/worker/sync/config.py
- [X] T040 [US1] Create device status sync logic (port states, client count, health metrics per device) in src/worker/sync/status.py
- [X] T041 [US1] Create event sync logic (audit logs from Mist for actor attribution) in src/worker/sync/events.py
- [X] T042 [US1] Add config and status sync tasks to sync_tasks.py (extend periodic sync to capture config + status) in src/worker/tasks/sync_tasks.py
- [X] T043 [US1] Create Mist webhook receiver and processing logic in src/worker/sync/webhook.py (R-02 dual strategy)
- [X] T044 [US1] Create webhook receiver endpoint POST /webhooks/mist with HMAC validation in src/api/routes/sync.py
- [X] T045 [US1] Create config Pydantic schemas (RevisionResponse, TimeTravel request/response) in src/api/schemas/config.py
- [X] T046 [US1] Create time-travel query endpoint GET /config/time-travel in src/api/routes/config.py (R-04 temporal query)

**Checkpoint**: Operators can sync inventory + config + status from Mist and query any historical timestamp. US1 is fully functional.

---

## Phase 4: User Story 2 — Configuration Versioning, Diff & Rollback (Priority: P1)

**Goal**: Operators view revision history, compare any two revisions with field-level diffs, and restore a prior known-good configuration via "Install from Revision."

**Independent Test**: Make a config change via Mist API, verify platform captures before/after, display correct diff, restore prior state via API push. Instant "undo button."

### Implementation for User Story 2

- [X] T047 [US2] Create DiffService class using deepdiff 8.x (compute_diff, normalize output to old/new values) in src/shared/services/diff.py (R-03)
- [X] T048 [US2] Create config push executor (install-from-revision via mistapi write endpoints) in src/worker/deploy/executor.py (R-05)
- [X] T049 [US2] Create rollback logic (pre-snapshot + compensating transactions for atomic multi-device) in src/worker/deploy/rollback.py (R-08)
- [X] T050 [US2] Create deploy_tasks for install-from-revision Celery task in src/worker/tasks/deploy_tasks.py (partial — job creation)
- [X] T051 [US2] Extend config Pydantic schemas with DiffRequest, DiffResponse, InstallFromRevisionRequest in src/api/schemas/config.py
- [X] T052 [US2] Create config revision list and detail endpoints (GET /config/revisions, GET /config/revisions/{id}) in src/api/routes/config.py
- [X] T053 [US2] Create config diff endpoint POST /config/diff in src/api/routes/config.py
- [X] T054 [US2] Create install-from-revision endpoint POST /config/install-from-revision (202 Accepted, async job) in src/api/routes/config.py

**Checkpoint**: Operators can browse revision history, diff any two revisions, and restore prior configs. US1 + US2 fully functional.

---

## Phase 5: User Story 3 — Scheduled Changes & Maintenance Windows (Priority: P2)

**Goal**: Change managers author and schedule future deployments with pre/post-check safety gates and auto-rollback on failure.

**Independent Test**: Schedule a future config change, verify execution at correct time, verify pre/post checks run, simulate failure and confirm rollback. Eliminates after-hours toil.

### Implementation for User Story 3

- [ ] T055 [P] [US3] Create ScheduledJob model (E-07) with state machine in src/shared/models/operations.py
- [ ] T056 [P] [US3] Create JobCheckpoint model (E-08) for safe resumption in src/shared/models/operations.py
- [ ] T057 [US3] Create migration for scheduled_jobs and job_checkpoints tables in migrations/versions/
- [ ] T058 [US3] Create pre-check implementations (reachability, version compat) in src/worker/checks/pre_checks.py
- [X] T059 [US3] Create post-check implementations (service health, client connectivity) in src/worker/checks/post_checks.py
- [X] T060 [US3] Create check_tasks Celery tasks (run_pre_checks, run_post_checks) in src/worker/tasks/check_tasks.py
- [X] T061 [US3] Extend deploy_tasks with scheduled job execution (poll for due jobs, execute with pre/post checks, auto-rollback) in src/worker/tasks/deploy_tasks.py
- [X] T062 [US3] Create deploy Pydantic schemas (JobCreate, JobResponse, DryRunRequest, DryRunResponse) in src/api/schemas/deploy.py
- [X] T063 [US3] Create deploy job CRUD endpoints (GET/POST/PUT/DELETE /deploy/jobs, POST /deploy/jobs/{id}/approve) in src/api/routes/deploy.py
- [X] T064 [US3] Create dry-run validation endpoint POST /deploy/dry-run (risk score, blast radius, policy violations) in src/api/routes/deploy.py
- [X] T065 [US3] Create dry-run validation logic (schema check, policy check, blast radius estimation) in src/worker/deploy/dry_run.py

**Checkpoint**: Change managers can schedule, approve, and auto-execute deployments with safety gates. US1 + US2 + US3 functional.

---

## Phase 6: User Story 4 — Change Audit Trail with Field-Level Diffs (Priority: P2)

**Goal**: Auditors query chronological change records with old/new field values, export compliance-ready reports.

**Independent Test**: Make config changes, query audit view with filters, verify every change captured with correct old/new values and timestamps. Standalone compliance evidence tool.

### Implementation for User Story 4

- [X] T066 [P] [US4] Create AuditRecord model (E-06) with hash partitioning and retention policy in src/shared/models/operations.py
- [X] T067 [P] [US4] Create ComplianceAuditPack model (E-15) in src/shared/models/governance.py
- [X] T068 [P] [US4] Create IncidentChangeCorrelation model (E-17) in src/shared/models/governance.py
- [X] T069 [US4] Create migration for audit_records (16 hash partitions), compliance_audit_packs, incident_change_correlations in migrations/versions/
- [X] T070 [US4] Create compliance service (audit pack generation, bundling change records + diffs + approvals) in src/shared/services/compliance.py
- [X] T071 [US4] Create incident-change correlation logic (temporal + scope matching) in src/worker/checks/correlation.py (SC-016 <2min)
- [X] T072 [US4] Create audit_tasks Celery tasks (audit export, compliance pack generation) in src/worker/tasks/audit_tasks.py
- [X] T073 [US4] Create audit Pydantic schemas (AuditRecordResponse, ExportRequest, CorrelationResponse, CompliancePackResponse) in src/api/schemas/audit.py
- [X] T074 [US4] Create audit trail endpoints (GET /audit/records, GET /audit/records/{id}, POST /audit/export) in src/api/routes/audit.py
- [X] T075 [US4] Create correlation and compliance-pack endpoints (GET /audit/correlations, POST /audit/compliance-packs) in src/api/routes/audit.py

**Checkpoint**: Auditors can query, filter, and export change records with full old/new diffs. US1-US4 functional.

---

## Phase 7: User Story 5 — Phased / Ring-Based Rollouts (Priority: P3)

**Goal**: Operators create multi-wave rollout plans with health-gate promotion, pause, and per-wave rollback for safe fleet-wide upgrades.

**Independent Test**: Create multi-wave plan, execute first wave, verify promotion logic (manual/auto), simulate failure and confirm rollback + pause. Safe controlled upgrades.

### Implementation for User Story 5

- [X] T076 [P] [US5] Create RolloutPlan model (E-09) with state machine in src/shared/models/operations.py
- [X] T077 [P] [US5] Create RolloutWave model (E-10) with state machine in src/shared/models/operations.py
- [X] T078 [P] [US5] Create GoldenImage model (E-14) with lifecycle states in src/shared/models/governance.py
- [X] T079 [US5] Create migration for rollout_plans, rollout_waves, golden_images in migrations/versions/
- [X] T080 [US5] Create multi-wave rollout orchestration logic (wave execution, health gate evaluation, promotion) in src/worker/deploy/rollout.py
- [X] T081 [US5] Create firmware upgrade orchestration logic (golden image validation, staged deployment) in src/worker/deploy/firmware.py
- [X] T082 [US5] Extend deploy_tasks with rollout execution and wave promotion Celery tasks in src/worker/tasks/deploy_tasks.py
- [X] T083 [US5] Extend deploy Pydantic schemas with RolloutCreate, WaveResponse, GoldenImageResponse in src/api/schemas/deploy.py
- [X] T084 [US5] Create rollout endpoints (GET/POST /deploy/rollouts, POST activate/pause/resume, POST wave promote/rollback) in src/api/routes/deploy.py
- [X] T085 [US5] Create golden image endpoints (GET/POST /deploy/golden-images, POST approve/retire) in src/api/routes/deploy.py

**Checkpoint**: Operators can plan, execute, and control multi-wave rollouts with automatic health gating. US1-US5 functional.

---

## Phase 8: User Story 6 — Continuous Compliance & Drift Detection (Priority: P3)

**Goal**: Platform continuously compares intended ("golden") config against actual Mist state, flags drift with field-level diffs, offers one-click remediation or baseline acceptance.

**Independent Test**: Define intended state, introduce drift via Mist API, verify platform detects and flags with correct diff. Prevents silent configuration rot.

### Implementation for User Story 6

- [X] T086 [P] [US6] Create Baseline model (E-11) with unique constraint per entity scope in src/shared/models/config.py
- [X] T087 [P] [US6] Create DriftAlert model (E-12) with state transitions in src/shared/models/config.py
- [X] T088 [P] [US6] Create NetworkPolicy model (E-16) with lifecycle states in src/shared/models/governance.py
- [X] T089 [US6] Create migration for baselines, drift_alerts, network_policies in migrations/versions/
- [X] T090 [US6] Create drift detection logic (baseline vs actual comparison using DiffService) in src/worker/checks/drift.py (SC-010 <10min)
- [X] T091 [US6] Add drift check to sync_tasks (after each config sync, compare against baselines) in src/worker/tasks/sync_tasks.py
- [X] T092 [US6] Extend sync Pydantic schemas with BaselineCreate, DriftAlertResponse, PolicyCreate in src/api/schemas/sync.py
- [X] T093 [US6] Create baseline endpoints (GET/POST /config/baselines, POST accept-drift, POST remediate) in src/api/routes/config.py
- [X] T094 [US6] Create drift alert endpoints (GET /drift/alerts, GET /drift/alerts/{id}, POST acknowledge) in src/api/routes/sync.py
- [X] T095 [US6] Create network policy endpoints (GET/POST /policies, POST recertify) in src/api/routes/sync.py

**Checkpoint**: Platform continuously monitors for drift and offers remediation. All 6 user stories fully functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Extended features, documentation, security hardening, performance

- [X] T096 [P] Create ChangeTemplate model (E-13) and template instantiation service in src/shared/models/governance.py and src/shared/services/template.py (FR-031)
- [X] T097 [P] Create change template endpoints (GET/POST /deploy/templates, POST instantiate) in src/api/routes/deploy.py
- [X] T098 Create retention policy Celery Beat task (nightly cleanup per data-model.md retention table) in src/worker/tasks/audit_tasks.py
- [X] T099 [P] Create architecture.md documentation in docs/architecture.md
- [X] T100 [P] Create operator runbook in docs/operations.md
- [X] T101 Create KEDA ScaledObject manifest for Celery workers in deploy/helm/templates/scaled-object.yaml (R-09)
- [X] T102 [P] Create Helm chart values.yaml and Chart.yaml in deploy/helm/
- [X] T103 Validate quickstart.md workflow end-to-end (start compose, migrate, run API + worker, first sync, verify)
- [X] T104 Security hardening: verify no secrets in logs (structlog processor), Vault references in auth_config, HMAC webhook validation

### Test Tasks (Principle IV Compliance)

- [X] T105 [P] Create unit tests for inventory models (E-00 through E-03) and db.py in tests/unit/shared/test_models_inventory.py
- [X] T106 [P] Create unit tests for DiffService in tests/unit/shared/test_diff.py
- [X] T107 [P] Create unit tests for auth middleware scope enforcement in tests/unit/api/test_auth.py
- [X] T108 Create integration tests for inventory sync (Mist API mock → DB) in tests/integration/test_sync_inventory.py
- [X] T109 Create integration tests for config revision capture and time-travel query in tests/integration/test_time_travel.py
- [X] T110 Create integration tests for scheduled job lifecycle (create → execute → rollback) in tests/integration/test_deploy_jobs.py
- [X] T111 Create integration tests for drift detection (baseline → drift → alert) in tests/integration/test_drift.py
- [X] T112 Create contract tests validating all API endpoints match contracts/*.md schemas in tests/contract/test_api_contracts.py
- [X] T113 [P] Create end-to-end smoke test (compose up → migrate → first sync → time-travel query) in tests/integration/test_e2e_smoke.py

### Additional Coverage Tasks

- [X] T114 [P] Create auth token and session endpoints (POST /auth/token, POST /auth/login, DELETE /auth/session) in src/api/routes/health.py (FR-018)
- [X] T115 [P] Create daily automated backup Celery Beat task in src/worker/tasks/sync_tasks.py (FR-034, SC-018 — pre-change + daily schedule)
- [X] T116 Document SC-011 UX acceptance criteria ("90% of operators complete time-travel investigation in <5 min") with test script and validation methodology in docs/operations.md
- [X] T117 Research feasibility of deferred requirements FR-026 (Path Analysis), FR-027 (App-Centric Modeling), FR-030 (App Discovery) — document findings in specs/001-mist-ops-platform/research.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **US1 (Phase 3, P1)**: Depends on Foundational — first story to implement
- **US2 (Phase 4, P1)**: Depends on Foundational + US1 (uses ConfigRevision model and sync from US1)
- **US3 (Phase 5, P2)**: Depends on Foundational + US2 (uses config push executor from US2)
- **US4 (Phase 6, P2)**: Depends on Foundational — can run in parallel with US3 (independent models)
- **US5 (Phase 7, P3)**: Depends on Foundational + US3 (uses deploy tasks and job infrastructure from US3)
- **US6 (Phase 8, P3)**: Depends on Foundational + US2 (uses ConfigRevision from US1 and DiffService from US2)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

```text
Foundational ──┬──> US1 (Time-Travel) ──> US2 (Versioning/Diff) ──> US3 (Scheduling) ──> US5 (Rollouts)
               │                          │
               │                          └──> US6 (Drift Detection) [uses DiffService from US2]
               │
               └──> US4 (Audit Trail) [independent models, can parallel with US2/US3]
```

### Within Each User Story

- Models before migrations
- Migrations before sync/worker logic
- Worker logic before API routes
- Pydantic schemas before route implementations
- Core implementation before integration with other stories

### Parallel Opportunities

Within **Phase 1 (Setup)**: T003, T004, T005, T006 can all run in parallel after T001+T002
Within **Phase 2 (Foundational)**: T008+T009 parallel, T015+T016 parallel, T020+T021+T022 parallel, T027+T028 parallel
Within **Phase 3 (US1)**: T036+T037 parallel (models), then T039+T040+T041 parallel (sync workers)
Within **Phase 5 (US3)**: T055+T056 parallel (models)
Within **Phase 6 (US4)**: T066+T067+T068 parallel (models)
Within **Phase 7 (US5)**: T076+T077+T078 parallel (models)
Within **Phase 8 (US6)**: T086+T087+T088 parallel (models)
**Cross-story**: US4 can proceed in parallel with US2 or US3 (independent data models)

---

## Parallel Example: User Story 1

```text
# Step 1 - Launch models in parallel:
T036: Create ConfigRevision model in src/shared/models/config.py
T037: Create DeviceStatusSnapshot model in src/shared/models/config.py

# Step 2 - Migration (depends on T036+T037):
T038: Create migration for config_revisions and device_status_snapshots

# Step 3 - Launch sync workers in parallel:
T039: Config snapshot sync in src/worker/sync/config.py
T040: Device status sync in src/worker/sync/status.py
T041: Event sync in src/worker/sync/events.py

# Step 4 - Integrate:
T042: Add sync tasks to sync_tasks.py
T043: Webhook receiver logic
T044: Webhook endpoint

# Step 5 - API:
T045: Config Pydantic schemas
T046: Time-travel query endpoint
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Time-Travel)
4. **STOP and VALIDATE**: Sync from Mist, query historical state, verify correctness
5. Deploy/demo — immediate value as "network forensics" tool

### Incremental Delivery

1. Setup + Foundational → Foundation ready (inventory syncing, health endpoints)
2. Add US1 → Test time-travel independently → Deploy/Demo (**MVP!**)
3. Add US2 → Test revisions + diff + rollback → Deploy/Demo (undo button)
4. Add US3 → Test scheduling + safety gates → Deploy/Demo (maintenance windows)
5. Add US4 → Test audit queries + export → Deploy/Demo (compliance evidence)
6. Add US5 → Test multi-wave rollouts → Deploy/Demo (fleet upgrades)
7. Add US6 → Test drift detection + remediation → Deploy/Demo (config governance)
8. Polish → Templates, docs, Helm, security hardening

### Parallel Team Strategy

With multiple developers after Foundational is complete:

- **Developer A**: US1 → US2 → US3 → US5 (core deployment path)
- **Developer B**: US4 (audit trail, independent) → US6 (drift detection)
- Stories integrate via shared models in `src/shared/` without conflicts

---

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after its dependencies
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- All file paths are relative to the `mist-ops-platform/` project root (a **new, separate repository** — not inside MistHelper)
- Constitution compliance: all functions max 25 lines (Principle I), all logic in classes (Principle II), confirm fields on destructive ops (Principle III)
