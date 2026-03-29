# Quickstart Guide

Get the Mist Ops Platform running locally for development in under
10 minutes.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Runtime |
| Podman or Docker | Latest | Container runtime |
| Podman Compose or Docker Compose | Latest | Service orchestration |
| Git | 2.40+ | Source control |
| UV | Latest | Python package manager |

---

## 1. Clone and Branch

```bash
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
git checkout 001-mist-ops-platform
```

---

## 2. Environment Variables

Copy the example environment file and fill in secrets:

```bash
cp .env.example .env
```

Required variables:

```dotenv
# Mist API token (org-scoped, read/write)
MIST_API_TOKEN=your-mist-api-token-here

# PostgreSQL
POSTGRES_USER=mistops
POSTGRES_PASSWORD=changeme
POSTGRES_DB=mistops

# Redis
REDIS_URL=redis://redis:6379/0

# Webhook secret (generate: python -c "import secrets; print(secrets.token_hex(32))")
MIST_WEBHOOK_SECRET=generate-a-hex-secret
```

---

## 3. Start Infrastructure

```bash
podman compose -f compose.dev.yml up -d
```

This starts PostgreSQL, Redis, and MinIO containers. Health checks
ensure readiness before dependent services start.

Verify:

```bash
podman compose -f compose.dev.yml ps
```

All services should show `healthy`.

---

## 4. Install Python Dependencies

```bash
uv venv .venv --python 3.13
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\Activate.ps1   # Windows PowerShell

uv pip install -e ".[dev]"
```

---

## 5. Run Database Migrations

```bash
alembic upgrade head
```

This creates all tables, partitions, and indexes defined in
data-model.md.

---

## 6. Start the API Server

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for the interactive OpenAPI UI.

---

## 7. Start the Celery Worker

In a separate terminal:

```bash
celery -A src.worker.app worker --loglevel=info -Q default,sync,deploy
```

---

## 8. Start the Celery Beat Scheduler

In another terminal:

```bash
celery -A src.worker.app beat --loglevel=info
```

This triggers periodic sync polling (every 5 minutes).

---

## 9. Verify Everything Works

### Health Check

```bash
curl http://localhost:8000/healthz
# {"status": "ok"}
```

### Readiness Check

```bash
curl http://localhost:8000/readyz
# {"status": "ready", "checks": {"db": "ok", "redis": "ok"}}
```

### First API Call — Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"api_token": "your-mist-api-token-here"}'
# Returns session with org/site permissions
```

### Trigger Initial Sync

```bash
curl -X POST http://localhost:8000/api/v1/sync/trigger \
  -H "Authorization: Bearer <session-token>" \
  -H "Content-Type: application/json" \
  -d '{"org_id": "your-org-id"}'
# Returns {"data": {"task_id": "...", "status": "queued"}}
```

### Check Inventory

After sync completes (~15s):

```bash
curl "http://localhost:8000/api/v1/inventory/orgs" \
  -H "Authorization: Bearer <session-token>"
# Lists all cached organizations
```

---

## 10. Run Tests

```bash
# Unit tests (fast, no external dependencies)
pytest tests/unit/ -v

# Integration tests (requires running containers)
pytest tests/integration/ -v

# Contract tests (validates API responses against schemas)
pytest tests/contract/ -v

# All tests with coverage
pytest --cov=src --cov-report=term-missing
```

---

## Project Layout

```text
src/
  api/          FastAPI routes, middleware, auth
  worker/       Celery tasks, sync, deploy logic
  shared/       Models, schemas, utilities
tests/
  unit/         Pure logic tests
  integration/  DB and Redis tests
  contract/     API schema validation
migrations/     Alembic migration scripts
deploy/         Kubernetes manifests, Helm charts
docs/           Architecture and API docs
```

---

## Common Tasks

| Task | Command |
|------|---------|
| Add migration | `alembic revision --autogenerate -m "description"` |
| Lint | `ruff check src/ tests/` |
| Type check | `mypy src/` |
| Format | `ruff format src/ tests/` |
| Reset DB | `alembic downgrade base && alembic upgrade head` |
| View logs | `podman compose -f compose.dev.yml logs -f` |
