# Mist Ops Platform — Operations Runbook

## Prerequisites

- Docker/Podman with Compose support
- PostgreSQL 16, Redis 7, MinIO, Vault (provided via compose)
- Python 3.13+ for local development

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env with actual Mist API tokens

# 2. Start all services
docker compose --profile full up -d

# 3. Run database migrations
docker compose exec api alembic upgrade head

# The API does not create a table on startup. Alembic owns the schema.
# Run step 3 before the first request, or every route fails. See issue #1883.
# Warning: revision 0003_align_schema_with_orm drops every platform table and
# builds it again. Take a database backup before you run this step.

# 4. Verify health
curl http://localhost:8000/api/v1/healthz

# 5. Trigger first inventory sync
curl -X POST http://localhost:8000/api/v1/sync/trigger \
  -H "Content-Type: application/json" \
  -d '{"org_id": "YOUR_ORG_UUID"}'
```

## Common Operations

### Trigger On-Demand Sync

```bash
curl -X POST http://localhost:8000/api/v1/sync/trigger \
  -H "Content-Type: application/json" \
  -d '{"org_id": "abc-123"}'
```

### Time-Travel Query

```bash
curl "http://localhost:8000/api/v1/config/time-travel?\
org_id=abc-123&entity_id=device-uuid&entity_type=device&\
timestamp=2026-03-01T10:00:00Z&include_status=true"
```

### Create a Deployment Job

```bash
curl -X POST http://localhost:8000/api/v1/deploy/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "abc-123",
    "change_payload": {"radio_config": {"band_24": {"power": 10}}},
    "target_entities": [{"entity_type": "device", "entity_id": "dev-uuid"}],
    "scheduled_at": "2026-03-10T02:00:00Z"
  }'
```

### Export Audit Records

```bash
curl -X POST http://localhost:8000/api/v1/audit/export \
  -H "Content-Type: application/json" \
  -d '{"org_id": "abc-123", "format": "csv"}'
```

## Monitoring

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/healthz` | Liveness probe |
| `GET /api/v1/readyz` | Readiness (DB + Redis) |
| `GET /api/v1/metrics` | Prometheus metrics |

### Key Metrics

- `sync_duration_seconds` — Time per sync cycle
- `deploy_job_total` — Jobs created/completed/failed
- `drift_alerts_open` — Current open drift alerts
- `celery_queue_depth` — Queue backlog (KEDA trigger)

## Troubleshooting

### Sync Not Running

1. Check Beat scheduler: `docker compose logs beat`
2. Verify Redis connectivity: `docker compose exec redis redis-cli PING`
3. Check sync queue: `celery -A src.worker.celeryconfig inspect active`

### Drift Alerts Not Generating

1. Verify baselines exist: `GET /api/v1/config/baselines?org_id=...`
2. Check config sync ran: `GET /api/v1/sync/status?org_id=...`
3. Review worker logs: `docker compose logs worker`

### Database Migrations Failed

```bash
# Check current revision
docker compose exec api alembic current

# Rollback one revision
docker compose exec api alembic downgrade -1

# Inspect migration history
docker compose exec api alembic history
```

## Retention Policy

Automated nightly at 02:00 UTC:

| Table | Retention |
|-------|-----------|
| config_revisions | 365 days |
| device_status_snapshots | 90 days |
| audit_records | 730 days |
| drift_alerts | 180 days |
| webhook_envelopes | 30 days |

## SC-011 UX Acceptance (T116)

**Criterion**: 90% of operators complete a time-travel investigation in under 5 minutes.

**Test Script**:
1. Give operator a device ID and a timestamp
2. Operator queries time-travel endpoint
3. Operator identifies the config state at that time
4. Operator diffs with current config
5. Measure total elapsed time

**Validation**: Run with 10 NOC operators, 9/10 must complete in <5 min.
