# Quickstart: Polyglot Database Migration Development

**Feature**: 184-polyglot-db-migration | **Date**: 2026-04-20

## Prerequisites

- Python 3.13+
- Podman or Docker (for container mode)
- Git + `gh` CLI

## 1. Clone and Setup

```powershell
git checkout 184-polyglot-db-migration
cd "C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper"
.venv\Scripts\Activate.ps1
pip install python-arango redis[hiredis] structlog
```

## 2. Start Services (Container Mode)

```powershell
# Create .env with required variables (copy from deploy/.env.example)
# Ensure these are set:
#   ARANGO_ROOT_PASSWORD=<secure-password>
#   REDIS_PASSWORD=<secure-password>

# Start all services
podman compose up -d

# Verify health
podman compose ps
# All 4 services (misthelper, ollama, arangodb, redis-stack) should show "healthy"
```

## 3. Verify Connections

```python
# Quick ArangoDB check
from arango import ArangoClient
client = ArangoClient(hosts="http://localhost:8529")
db = client.db("misthelper", username="root", password="<password>")
print(db.version())  # Should print ArangoDB version

# Quick Redis check
import redis
r = redis.Redis(host="localhost", port=6379, password="<password>")
print(r.ping())  # Should print True
print(r.module_list())  # Should include "timeseries"
```

## 4. Run Tests

```powershell
# Unit tests (mocked, no services needed)
pytest tests/unit/test_router.py -v
pytest tests/unit/test_arango_writer.py -v
pytest tests/unit/test_redis_writer.py -v

# Integration tests (requires running services)
pytest tests/integration/test_compose_deploy.py -v

# Full quality gates
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
```

## 5. Key Files to Edit

| File | What to Change |
| - | - |
| `src/db/router.py` | DatabaseRouter class (new) |
| `src/db/arango_writer.py` | ArangoDBWriter class (new) |
| `src/db/redis_writer.py` | RedisTimeSeriesWriter class (new) |
| `src/db/retention.py` | RetentionManager class (new) |
| `MistHelper.py` line ~9401 | DataExporter: add DatabaseRouter delegation |
| `compose.yml` | Add arangodb + redis-stack services |
| `requirements.txt` | Add python-arango, redis[hiredis], structlog |
| `deploy/.env.example` | Add ARANGO_ROOT_PASSWORD, REDIS_PASSWORD, retention vars |

## 6. Environment Variables

| Variable | Default | Purpose |
| - | - | - |
| `ARANGO_ROOT_PASSWORD` | (required) | ArangoDB root password |
| `REDIS_PASSWORD` | (required) | Redis requirepass |
| `ARANGO_HOST` | `http://arangodb:8529` | ArangoDB connection URL |
| `REDIS_HOST` | `redis-stack` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_RAW_RETENTION_DAYS` | `7` | Raw metric retention |
| `REDIS_HOURLY_RETENTION_DAYS` | `90` | Hourly aggregate retention |
| `REDIS_DAILY_RETENTION_DAYS` | `365` | Daily aggregate retention |
| `ARANGO_MAX_STORAGE_GB` | `50` | Max ArangoDB storage |
| `RETENTION_CHECK_INTERVAL_HOURS` | `6` | Retention sweep interval |
| `MISTHELPER_STANDALONE` | `false` | Set `true` to disable DB backends |

## 7. Architecture Overview

```text
MistHelper.py
  └── DataExporter.write_with_format_selection()
        ├── _write_csv()           # Always (unchanged)
        └── DatabaseRouter.write() # New: routes by PK strategy type
              ├── ArangoDBWriter   # natural_pk, auto_increment_with_unique
              └── RedisTimeSeriesWriter  # composite_pk
```
