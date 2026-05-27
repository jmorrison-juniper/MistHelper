# Mist Ops Platform — Architecture

## Overview

Mist Ops Platform is a three-layer containerized application that provides
configuration management, change orchestration, and compliance auditing for
Juniper Mist Cloud networks.

## System Layers

### 1. API Layer (FastAPI)

- **Framework**: FastAPI 0.115+ on Uvicorn (4 workers)
- **Purpose**: REST API serving all client operations
- **Prefix**: All routes under `/api/v1/`
- **Middleware**: Structured logging, rate limiting, authentication
- **Routers**: health, sync, inventory, config, deploy, audit, drift, policies, webhooks

### 2. Worker Layer (Celery)

- **Broker**: Redis 7
- **Queues**: `default`, `sync`, `deploy`
- **Key Workers**:
  - **Sync pipeline** (5-min interval): inventory, config, status, events, drift scan
  - **Deploy tasks**: job execution, rollout waves, firmware orchestration
  - **Audit tasks**: export, compliance packs, retention cleanup

### 3. Data Layer

- **PostgreSQL 16**: Primary store with hash-partitioned tables (16 partitions)
  for `config_revisions`, `device_status_snapshots`, `audit_records`
- **Redis 7**: Caching, rate limiting, Celery broker
- **MinIO**: S3-compatible object storage for audit artifacts
- **Vault**: Secret management (API tokens, credentials)

## Entity Model (21 Entities)

| ID   | Entity                    | Table                         | PK Strategy     |
|------|---------------------------|-------------------------------|-----------------|
| E-00 | MSP                       | msps                          | Natural (UUID)  |
| E-01 | Organization              | orgs                          | Natural (UUID)  |
| E-02 | Site                      | sites                         | Natural (UUID)  |
| E-03 | Device                    | devices                       | Natural (UUID)  |
| E-04 | ConfigRevision            | config_revisions              | Composite       |
| E-05 | DeviceStatusSnapshot      | device_status_snapshots       | Composite       |
| E-06 | AuditRecord               | audit_records                 | Composite       |
| E-07 | ScheduledJob              | scheduled_jobs                | Natural (UUID)  |
| E-08 | JobCheckpoint             | job_checkpoints               | Natural (UUID)  |
| E-09 | RolloutPlan               | rollout_plans                 | Natural (UUID)  |
| E-10 | RolloutWave               | rollout_waves                 | Composite       |
| E-11 | Baseline                  | baselines                     | Natural (UUID)  |
| E-12 | DriftAlert                | drift_alerts                  | Natural (UUID)  |
| E-13 | ChangeTemplate            | change_templates              | Natural (UUID)  |
| E-14 | GoldenImage               | golden_images                 | Natural (UUID)  |
| E-15 | ComplianceAuditPack       | compliance_audit_packs        | Natural (UUID)  |
| E-16 | NetworkPolicy             | network_policies              | Natural (UUID)  |
| E-17 | IncidentChangeCorrelation | incident_change_correlations  | Natural (UUID)  |
| E-18 | NotificationChannel       | notification_channels         | Natural (UUID)  |
| E-19 | SyncLedgerEntry           | sync_ledger                   | Auto-increment  |
| E-20 | WebhookEnvelope           | webhook_envelopes             | Natural (UUID)  |

## User Stories

1. **Time-Travel** (P1): Point-in-time config and status queries
2. **Config Versioning** (P1): Full revision history with diff and rollback
3. **Scheduled Changes** (P2): Deployment jobs with pre/post checks
4. **Audit Trail** (P2): Chronological change tracking with compliance export
5. **Phased Rollouts** (P3): Multi-wave rollouts with health gates
6. **Drift Detection** (P3): Continuous baseline comparison with remediation

## Key Design Decisions

- **R-01**: All Mist API calls isolated to Celery workers (never in API request path)
- **R-02**: Hash-partitioned tables by org_id for multi-tenant scalability
- **R-04**: Temporal queries use `captured_at <= timestamp ORDER BY desc LIMIT 1`
- **R-05**: deepdiff 8.x for JSON config diffing
- **R-06**: Saga pattern for multi-step rollback
- **R-09**: KEDA-ready auto-scaling via queue depth

## Directory Structure

```
mist-ops-platform/
  src/
    api/                    # FastAPI layer
      main.py               # App factory
      deps.py               # Dependency injection
      middleware/            # Auth, logging, rate-limit
      routes/               # Endpoint handlers
      schemas/              # Pydantic request/response models
    shared/                 # Cross-cutting concerns
      config/               # Settings, enums, constants
      db.py                 # Engine factory
      models/               # SQLAlchemy ORM (4 modules, 21 entities)
      mist/                 # Mist API integration
      services/             # Business logic (diff, auth, notification, etc.)
    worker/                 # Celery layer
      celeryconfig.py       # Broker, queues, Beat schedule
      sync/                 # Inventory/config/status/event sync
      deploy/               # Executor, rollback, rollout, firmware
      checks/               # Pre/post checks, drift, correlation
      tasks/                # Task definitions
  deploy/                   # Container/compose/Helm
  migrations/               # Alembic migrations
  tests/                    # Unit, integration, contract, e2e
  docs/                     # Architecture, operations guides
```

## Security

- Vault for secret storage (dev mode: `dev-root-token`)
- Per-org sliding window rate limiting via Redis
- HMAC-SHA256 webhook signature validation
- Maker-checker for golden image approvals (FR-033)
- Destructive operations require explicit `confirm: true`

## Integration Note (MistHelper Decomposition)

- Documentation aligned with MistHelper decomposition wave `193-main-decomposition-wave-2`
  through Phase 9, including extracted packet capture and service-ping modules.
- No Mist Ops Platform runtime behavior changed by this documentation sync; this is
  traceability alignment only.
