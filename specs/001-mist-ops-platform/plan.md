# Implementation Plan: Mist Ops Platform

**Branch**: `001-mist-ops-platform` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-mist-ops-platform/spec.md`

## Summary

Build a 3-layer containerized microservice platform that provides operator-grade
capabilities missing from the Juniper Mist AI Cloud portal. The platform
continuously syncs device inventory, configuration, and status from the Mist API
(via `mistapi` SDK) and stores immutable configuration revisions in PostgreSQL.
It exposes a FastAPI REST API for time-travel
investigation, config versioning/diff/rollback, scheduled deployments with
pre/post-check safety gates, field-level change audit trails, phased rollouts,
continuous compliance/drift detection, firmware orchestration, risk simulation,
policy lifecycle management, and incident-change correlation. Celery workers
handle all Mist API interactions (sync polling, config push, health checks) with
per-org rate-limit budgeting in Redis. KEDA provides event-driven autoscaling.
All components are free, open-source, and Kubernetes-ready.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution constraint)
**Primary Dependencies**: FastAPI 0.115+, Celery 5.4+, SQLAlchemy 2.0+,
mistapi 0.60+, pydantic 2.x, httpx, tenacity, structlog, redis, alembic,
asyncpg, deepdiff, prometheus_client, opentelemetry-sdk, apscheduler, hvac
**Storage**: PostgreSQL 16 (Zalando Operator for K8s HA), Redis 7 (Spotahome
Operator), MinIO (S3-compatible object storage)
**Testing**: pytest + pytest-asyncio + httpx (async test client) + testcontainers
**Target Platform**: Linux containers / Kubernetes (local dev: Windows 11 + Docker Compose)
**Project Type**: web-service (3-layer microservice platform)
**Performance Goals**: <5s time-travel queries (SC-001), <10min change capture
(SC-002), <3s diff rendering (SC-003), <60s scheduled deployment execution
(SC-004), <90s auto-rollback initiation (SC-005), <5s audit queries (SC-006),
<30s 12-month audit export (SC-012), <10s dry-run validation (SC-013)
**Constraints**: All free/OSS (SC-007), no vendor lock-in (FR-020), ASCII-only
logging (Principle V), max 25 lines per function (Principle I), class-based
architecture — no wrapper functions (Principle II), safe_input for all user
input (Principle III), on-prem or cloud deployable (FR-020)
**Scale/Scope**: 100 orgs x 1K sites x 10 devices = 1M devices baseline;
5x headroom = 5M devices (SC-008). PostgreSQL partitioned by org_id + time.
Per-org Celery queues with KEDA autoscaling.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I — Five-Item Rule: PASS

The source structure uses exactly 5 Level-2 directories (`src/`, `tests/`,
`migrations/`, `deploy/`, `docs/`). Within `src/`, 3 packages (`api/`,
`worker/`, `shared/`). Each sub-package contains <= 5 modules. Function
limits (max 5 params, max 25 lines) enforced via linting rules.

### Principle II — Class-Based Architecture: PASS

All domain logic resides in semantically named classes:
- `MistSyncService`, `ConfigRevisionService`, `DiffService`,
  `DeploymentService`, `AuditService`, `DriftDetectionService`,
  `RolloutService`, `ComplianceService`, `NotificationService`
- No standalone wrapper functions. All FastAPI route handlers delegate to
  service class methods.

### Principle III — Safety-First: PASS

- All API inputs validated via pydantic models (strict mode).
- Destructive operations (install-from-revision, remediation push, firmware
  upgrade, rollback) require explicit confirmation field in request body.
- No secrets in logs — structlog processors strip sensitive fields.
- All Mist API tokens stored in Vault with encryption at rest.

### Principle IV — Full Deployment Pipeline: PASS (with adaptation)

The new platform has its own CI/CD pipeline following the same pattern:
1. `python -m py_compile` on all source files before commit
2. `pytest` must pass before merge
3. GitHub Actions builds container images on push to main
4. Automated image pull and container restart in deployment
5. Health endpoint verification post-deploy

**Note**: The new platform's pipeline is independent from MistHelper's
existing pipeline but follows identical principles. This is not a
violation — it is an extension.

### Principle V — Observability & Logging: PASS

- `structlog` with JSON output for all services.
- `prometheus_client` exposes `/metrics` on every service.
- OpenTelemetry SDK for distributed tracing across API → worker → DB.
- ASCII-only log output enforced via structlog processor.
- Health (`/healthz`) and readiness (`/readyz`) endpoints per FR-016.

### Gate Result: ALL PASS — proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-mist-ops-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api-overview.md
│   ├── config.md
│   ├── audit.md
│   ├── deploy.md
│   └── sync.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mist-ops-platform/                    # Project root (Level 1)
├── src/                              # Source code (Level 2: 3 children)
│   ├── api/                          # FastAPI service (Level 3: 5 children)
│   │   ├── routes/                   # Route handlers (Level 4: ≤5 modules)
│   │   │   ├── config.py             # Config revisions, diff, install-from-revision, baselines (≤5 handlers; split to config/baselines.py if exceeded)
│   │   │   ├── audit.py              # Audit trail queries, export (≤5 handlers)
│   │   │   ├── deploy.py             # Scheduled jobs, rollouts, dry-run (≤5 handlers; split to deploy/rollout.py if exceeded)
│   │   │   ├── sync.py               # Sync status, drift alerts, webhooks, policies (≤5 handlers; split to sync/drift.py if exceeded)
│   │   │   └── health.py             # /healthz, /readyz, /metrics, auth, notifications (≤5 handlers; split to system/{auth,notifications}.py if exceeded)
│   │   ├── middleware/               # Request processing (Level 4: ≤5 modules)
│   │   │   ├── auth.py               # Mist API token/session validation
│   │   │   ├── rate_limit.py         # Per-org request throttling
│   │   │   └── logging.py            # Request/response structured logging
│   │   ├── schemas/                  # Pydantic request/response models (Level 4: ≤5)
│   │   │   ├── config.py             # Revision, diff, rollback schemas
│   │   │   ├── audit.py              # Audit query/export schemas
│   │   │   ├── deploy.py             # Job, rollout, dry-run schemas
│   │   │   ├── sync.py               # Sync, drift, baseline schemas
│   │   │   └── common.py             # Shared pagination, error, envelope
│   │   ├── deps.py                   # Dependency injection (DB session, auth)
│   │   └── main.py                   # FastAPI app factory, router mounting
│   ├── worker/                       # Celery workers (Level 3: 5 children)
│   │   ├── tasks/                    # Task definitions (Level 4: ≤5 modules)
│   │   │   ├── sync_tasks.py         # Periodic Mist API sync
│   │   │   ├── deploy_tasks.py       # Scheduled deployment execution
│   │   │   ├── check_tasks.py        # Pre/post-check health probes
│   │   │   ├── audit_tasks.py        # Audit export, compliance pack gen
│   │   │   └── notify_tasks.py       # Notification dispatch (email/webhook)
│   │   ├── sync/                     # Mist API sync logic (Level 4: ≤5 modules)
│   │   │   ├── inventory.py          # Org/site/device inventory sync
│   │   │   ├── config.py             # Configuration snapshot capture
│   │   │   ├── events.py             # Audit log / event sync from Mist
│   │   │   ├── status.py             # Device status / health metric sync
│   │   │   └── webhook.py            # Inbound Mist webhook processing
│   │   ├── deploy/                   # Deployment logic (Level 4: ≤5 modules)
│   │   │   ├── executor.py           # Config push via mistapi
│   │   │   ├── rollout.py            # Multi-wave rollout orchestration
│   │   │   ├── rollback.py           # Auto-rollback and install-from-revision
│   │   │   ├── firmware.py           # Firmware upgrade orchestration
│   │   │   └── dry_run.py            # Dry-run validation and risk scoring
│   │   ├── checks/                   # Health check implementations (Level 4: ≤5)
│   │   │   ├── pre_checks.py         # Device reachability, version compat
│   │   │   ├── post_checks.py        # Service health, client connectivity
│   │   │   ├── drift.py              # Baseline vs actual comparison
│   │   │   └── correlation.py        # Incident-change correlation
│   │   └── celeryconfig.py           # Celery app, broker, beat schedule
│   └── shared/                       # Shared code (Level 3: 5 children)
│       ├── models/                   # SQLAlchemy models (Level 4: ≤5 modules)
│       │   ├── inventory.py          # MSP, Org, Site, Device, SyncLedgerEntry (5)
│       │   ├── config.py             # ConfigRevision, DeviceStatusSnapshot, Baseline, DriftAlert, WebhookEnvelope (5)
│       │   ├── operations.py         # ScheduledJob, JobCheckpoint, AuditRecord, RolloutPlan, RolloutWave, NotificationChannel (6 — see Complexity Tracking)
│       │   ├── governance.py         # ChangeTemplate, GoldenImage, ComplianceAuditPack, NetworkPolicy, IncidentChangeCorrelation (5)
│       │   └── base.py               # DeclarativeBase, mixins, common columns
│       ├── services/                 # Business logic (Level 4: ≤5 modules)
│       │   ├── diff.py               # deepdiff-based config comparison
│       │   ├── auth.py               # Mist session management, privilege cache
│       │   ├── notification.py       # Email/webhook dispatch
│       │   ├── compliance.py         # Audit pack generation, policy lifecycle
│       │   └── template.py           # Change template instantiation
│       ├── mist/                     # mistapi integration (Level 4: ≤5 modules)
│       │   ├── session.py            # APISession factory, token rotation
│       │   ├── rate_limit.py         # Per-org Redis rate buckets (PID adaptive)
│       │   ├── endpoints.py          # Wrapper class for read/write API calls
│       │   └── types.py              # Mist entity type mappings
│       ├── config/                   # Settings (Level 4: ≤5 modules)
│       │   ├── settings.py           # pydantic-settings (env vars, defaults)
│       │   └── constants.py          # Enums, magic values, retry defaults
│       └── db.py                     # Async engine, session factory, connection
├── tests/                            # Tests (Level 2: 3 children)
│   ├── unit/                         # Unit tests (mirrors src/ structure)
│   ├── integration/                  # Integration tests (DB, Redis, Mist API)
│   └── contract/                     # API contract tests (OpenAPI validation)
├── migrations/                       # Alembic (Level 2: alembic-managed)
│   ├── env.py
│   └── versions/
├── deploy/                           # Deployment (Level 2: ≤5 children)
│   ├── compose.yml                   # Development Docker Compose
│   ├── helm/                         # Kubernetes Helm chart
│   ├── Containerfile.api             # API service container
│   └── Containerfile.worker          # Worker service container
└── docs/                             # Documentation (Level 2: ≤5 children)
    ├── architecture.md               # Architecture overview
    ├── operations.md                 # Operator runbook
    └── api.md                        # API reference (auto-generated)
```

**Structure Decision**: Selected a single-project layout with 3 internal
packages (`api`, `worker`, `shared`) under `src/`. This follows the Five-Item
Rule at every level. The `api` and `worker` packages share models and services
via `shared`, avoiding code duplication. The structure supports independent
container images (one for API, one for worker) from the same codebase. The
`deploy/` directory holds both Compose (dev) and Helm (prod) manifests.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| operations.py has 6 entities (Principle I) | 21 total entities across 4 model files; 5/5/6/5 is the minimum achievable split. RolloutPlan/RolloutWave are operational orchestration entities tightly coupled to ScheduledJob execution lifecycle. | Adding a 5th model file would violate Principle I at the directory level (models/ would have 6 children instead of 5). A module-level violation is less severe than a directory-level violation. |

## Post-Design Constitution Re-evaluation

Re-evaluated after Phase 1 artifacts (data-model.md, 5 contract files,
quickstart.md) were complete.

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Five-Item Rule | PASS (with documented exception) | 5 Level-2 dirs, 3 src/ packages, 5 contract files, 21 entities grouped into 4 model modules (5/5/6/5 — operations.py exception documented in Complexity Tracking) |
| II. Class-Based | PASS | Service classes designed: SyncService, ConfigRevisionService, DeploymentService, DriftDetectionService, AuditService, NotificationDispatcher — no wrappers |
| III. Safety-First | PASS | `confirm: true` required on all destructive endpoints (activate, approve, rollback, firmware, remediate, recertify). Maker-checker requires different approver. Webhook HMAC validation. Pydantic strict mode |
| IV. Deployment Pipeline | PASS | Independent CI/CD for the platform (Containerfile.api + Containerfile.worker). MistHelper's existing pipeline preserved |
| V. Observability | PASS | /healthz, /readyz, /metrics system endpoints. structlog + prometheus-client + opentelemetry in dependency list. ASCII-only logging rule carried forward |

**Gate Result: ALL PASS — no violations introduced during design**
