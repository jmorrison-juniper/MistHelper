# Mist Ops Platform — Architecture Reference

**Purpose**: Documents the 3-layer containerized microservice architecture, component shopping list per layer, and rationale for all technology choices. All components are free, open-source, Kubernetes-ready, and horizontally scalable.

**Source**: Architecture design discussion (session 2026-03-05).

---

## Architecture Overview

```
+-------------------------------------------------------------+
|                    LAYER 1: FRONTEND                         |
|                    (API & Edge)                              |
|                                                              |
|  Traefik Proxy (Ingress/Gateway) + cert-manager (TLS)       |
|  FastAPI (REST endpoints, webhooks, health, /metrics)        |
|  httpx + tenacity (resilient outbound calls)                 |
|  prometheus_client + OTel SDK (observability)                |
+-------------------------------------------------------------+
          |                    |                    |
          v                    v                    v
+-------------------------------------------------------------+
|                    LAYER 2: APPLICATION                      |
|                    (Service / Business Logic)                |
|                                                              |
|  FastAPI "app" service (internal APIs, dry-run, validation)  |
|  Celery workers (Redis broker) — orchestration, sync, export |
|  KEDA (event-driven autoscaling on queue depth/HTTP rate)    |
|  Argo Workflows (batch/cron/DAG pipelines)                   |
|  pydantic (data validation), structlog (structured logging)  |
+-------------------------------------------------------------+
          |                    |                    |
          v                    v                    v
+-------------------------------------------------------------+
|                    LAYER 3: BACKEND                          |
|                    (Data, Coordination, Streaming)            |
|                                                              |
|  PostgreSQL (Zalando Operator or Bitnami chart) — SoR        |
|  Redis (Spotahome Operator) — cache, broker, locks           |
|  MinIO — S3-compatible artifact/blob storage                 |
|  NATS or Apache Kafka (optional event streaming)             |
|  Vault / OpenBao — secrets management                        |
|  Harbor — private OCI container registry                     |
|  Prometheus + Grafana + OTel Collector — observability       |
+-------------------------------------------------------------+
```

---

## Layer 1: Frontend (API & Edge)

### Purpose
Terminate TLS, authenticate requests, expose a clean API to operators/automation, fan-out requests to the Application layer, and export SRE metrics.

### Components

| Component | Role | License | K8s Deployment |
|-----------|------|---------|----------------|
| **Traefik Proxy** | Ingress controller / API gateway with Let's Encrypt support. Implements K8s Ingress and Gateway APIs. | Apache 2.0 | Helm chart |
| **cert-manager** | Automates certificate issuance/renewal (Let's Encrypt, Vault PKI, private CA). | Apache 2.0 | Helm chart |
| **FastAPI** | Async REST framework for webhook receiver, operator APIs, health/readiness, /metrics. | MIT | In app container |
| **Uvicorn** | ASGI server for FastAPI. | BSD | In app container |
| **httpx** | Async/sync HTTP client with HTTP/2 for Mist API calls and internal service calls. | BSD | Python package |
| **tenacity** | Retry library with exponential backoff, jitter, stop policies. | Apache 2.0 | Python package |
| **prometheus_client** | Exposes /metrics endpoint for Prometheus scraping. | Apache 2.0 | Python package |
| **OpenTelemetry SDK** | Distributed tracing and metrics (vendor-neutral). | Apache 2.0 | Python package |

### Scaling
- HPA on RPS/latency for API pods
- Traefik handles load balancing and TLS termination
- Certificates auto-renew via cert-manager

### Note on ingress-nginx
The community ingress-nginx controller is in retirement (best-effort maintenance until March 2026). New greenfield installs should use Traefik or a Gateway API implementation.

---

## Layer 2: Application / Service Layer

### Purpose
The "brains" of the platform. Implements all operator workflow features: time-travel queries, scheduled changes, diff/audit, install-from-revision, pre/post checks, evidence packs, drift detection, phased rollouts, etc. All logic is stateless — state is persisted to the Backend layer.

### Components

| Component | Role | License | K8s Deployment |
|-----------|------|---------|----------------|
| **FastAPI** (app service) | Internal APIs for idempotent action endpoints, dry-run verification, validation. | MIT | Deployment |
| **Celery** | Distributed task queue for background jobs (API polling, report generation, bulk exports, scheduled deployments). Redis as broker/backend. | BSD | Deployment |
| **KEDA** | Event-driven autoscaler. Scales Celery workers on Redis queue depth, Kafka lag, or HTTP rate. Supports scale-to-zero. | Apache 2.0 | Helm chart |
| **Argo Workflows** | Orchestrates batch/ETL/cron pipelines on K8s (pre/post-change validation, audit pack generation, report builds). Declarative DAGs with artifact support (uploads to MinIO). | Apache 2.0 | Helm chart |
| **pydantic** | Data validation and settings management (Mist API payloads, config objects). | MIT | Python package |
| **pydantic-settings** | 12-factor config via environment variables and secrets. | MIT | Python package |
| **SQLAlchemy 2.x** | ORM for database access (async or sync). | MIT | Python package |
| **Alembic** | Database migration tool for schema evolution. | MIT | Python package |
| **asyncpg** | High-performance async PostgreSQL driver. | Apache 2.0 | Python package |
| **structlog** | Structured JSON logging for machine-parseable log entries. | MIT/Apache 2.0 | Python package |

### Scaling
- KEDA ScaledObjects for Celery workers (Redis list length, custom metrics)
- Argo Workflows parallelizes long-running jobs
- Stateless design — any worker can process any task

---

## Layer 3: Backend (Data, Coordination, Streaming)

### Purpose
Durable system of record, artifact storage, coordination, and optional event streaming. Enables time-travel queries, audit diffs, install-from-revision, and cheap replays of webhook events.

### Components

| Component | Role | License | K8s Deployment |
|-----------|------|---------|----------------|
| **PostgreSQL** | Relational system of record: normalized inventory, config snapshots, webhook envelopes, audit trails, sync ledgers, job history. | PostgreSQL License (permissive) | Zalando Postgres Operator (HA, Patroni-based) or Bitnami Helm chart |
| **Redis** | Hot cache, idempotency keys, rate-limit counters, Celery broker/backend, distributed locks. | BSD | Spotahome Redis Operator (Redis + Sentinel failover) |
| **MinIO** | S3-compatible object storage for large artifacts: reports, PCAPs, evidence packs, config exports, workflow logs. | AGPLv3 | Helm chart or Operator |
| **NATS** (optional) | Lightweight pub/sub + JetStream persistence for event fan-in, decoupled retries, webhook distribution. Ideal for most Mist sidecars. | Apache 2.0 | Helm chart |
| **Apache Kafka** (optional) | Heavyweight durable event log for enterprise-wide event pipelines, BI integrations, and high-throughput streaming. | Apache 2.0 | Strimzi Operator or Bitnami chart |
| **HashiCorp Vault** | Secrets management: API keys, DB credentials, dynamic user creation, PKI. Integrates with cert-manager. | MPL 2.0 (OSS edition) | Helm chart |
| **OpenBao** (alternative) | Community-governed Vault fork under Linux Foundation. Similar APIs. | MPL 2.0 | Helm chart |
| **Harbor** | Private OCI container registry with RBAC, vulnerability scanning, replication, content trust. | Apache 2.0 | Helm chart |
| **Prometheus** | Metrics collection and alerting. Scrapes /metrics from services and infra exporters. K8s autodiscovery. | Apache 2.0 | kube-prometheus-stack Helm chart |
| **Grafana** | Dashboards, alerting, and visualization. Prometheus data source + OTel traces/logs. | AGPLv3 | Included in kube-prometheus-stack |
| **OpenTelemetry Collector** | Vendor-agnostic pipeline: receives traces/metrics/logs, retries/batches/filters, exports to backends. | Apache 2.0 | Helm chart or Operator |

### Scaling
- PostgreSQL: read replicas via Patroni (Zalando Operator), partitioning by org_id/time
- Redis: Sentinel failover (Spotahome Operator)
- MinIO: add nodes for more throughput; supports erasure coding
- NATS/Kafka: partition-based horizontal scaling

---

## Data Model (PostgreSQL Schema Sketch)

```sql
-- Inventory (synced from Mist API)
CREATE TABLE orgs (
    org_id UUID PRIMARY KEY,
    msp_id UUID,
    name TEXT NOT NULL,
    api_base TEXT,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sites (
    site_id UUID PRIMARY KEY,
    org_id UUID REFERENCES orgs(org_id),
    name TEXT NOT NULL,
    location_json JSONB,
    last_sync_at TIMESTAMPTZ
);

CREATE TABLE devices (
    device_id UUID PRIMARY KEY,
    org_id UUID REFERENCES orgs(org_id),
    site_id UUID REFERENCES sites(site_id),
    serial TEXT UNIQUE,
    model TEXT,
    role TEXT,  -- ap, switch, gateway
    firmware_version TEXT,
    status TEXT,
    last_sync_at TIMESTAMPTZ
);

-- Configuration History (immutable revisions)
CREATE TABLE config_revisions (
    revision_id BIGSERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,  -- org, site, device, wlan, policy
    entity_id UUID NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    content_hash TEXT NOT NULL,
    config_payload JSONB NOT NULL,
    actor TEXT,  -- user or API token ID
    UNIQUE (entity_id, content_hash)
);

-- Audit Trail
CREATE TABLE audit_records (
    record_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    actor TEXT,
    entity_type TEXT,
    entity_id UUID,
    change_type TEXT,
    old_values JSONB,
    new_values JSONB,
    org_id UUID REFERENCES orgs(org_id)
);

-- Scheduled Jobs
CREATE TABLE scheduled_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES orgs(org_id),
    target_entities UUID[],
    change_payload JSONB NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    pre_check_defs JSONB,
    post_check_defs JSONB,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rollout Plans
CREATE TABLE rollout_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES orgs(org_id),
    waves JSONB NOT NULL,  -- ordered list of wave definitions
    health_gate_criteria JSONB,
    promotion_mode TEXT DEFAULT 'manual',  -- manual or automatic
    status TEXT DEFAULT 'pending',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Baselines (Intended State)
CREATE TABLE baselines (
    baseline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_scope UUID NOT NULL,  -- site_id or device_group_id
    config_payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT
);

-- Drift Alerts
CREATE TABLE drift_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_id UUID REFERENCES baselines(baseline_id),
    device_id UUID REFERENCES devices(device_id),
    detected_at TIMESTAMPTZ NOT NULL,
    diff_payload JSONB NOT NULL,
    status TEXT DEFAULT 'open'  -- open, remediated, accepted
);

-- Sync Ledger (bookkeeping)
CREATE TABLE sync_ledger (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID REFERENCES orgs(org_id),
    job_type TEXT,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    status TEXT,
    rows_affected INT,
    error_text TEXT
);

-- Webhook Envelopes (dedup)
CREATE TABLE webhook_envelopes (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID REFERENCES orgs(org_id),
    event_id TEXT UNIQUE,
    received_at TIMESTAMPTZ,
    event_type TEXT,
    payload_json JSONB,
    processed_at TIMESTAMPTZ,
    status TEXT
);

-- Notification Channels
CREATE TABLE notification_channels (
    channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_type TEXT NOT NULL,  -- email, webhook
    destination TEXT NOT NULL,   -- SMTP address or webhook URL
    alert_subscriptions TEXT[],  -- list of alert types
    enabled BOOLEAN DEFAULT TRUE,
    auth_config JSONB,           -- webhook auth (optional)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Redis Usage Patterns

| Pattern | Key Format | Purpose |
|---------|-----------|---------|
| Idempotency | `event:{event_id}` (SET NX EX 86400) | Drop duplicate webhook events |
| Rate limiting | `ratelimit:{org_id}` (INCR with TTL) | Token bucket per org before Mist API calls |
| Locks | `sync:{org_id}` (SETNX) | Ensure one poller per org at a time |
| Cache | `device_site_map:{org_id}` (TTL) | Frequently read device-to-site mappings |
| Job queue | Celery default broker | Background task distribution |

---

## Python Package List (Complete)

### Core I/O & Runtime
| Package | Purpose | License |
|---------|---------|---------|
| `fastapi` | REST API framework (webhooks, health, admin) | MIT |
| `uvicorn[standard]` | ASGI server | BSD |
| `httpx` | Async/sync HTTP client for Mist API calls | BSD |
| `tenacity` | Retry with exponential backoff, jitter, circuit-breaker patterns | Apache 2.0 |
| `pydantic` | Data validation and strict models for Mist payloads | MIT |
| `pydantic-settings` | 12-factor config via env vars and Secrets | MIT |
| `sqlalchemy` (2.x) | ORM for PostgreSQL | MIT |
| `alembic` | Database migrations | MIT |
| `asyncpg` | Async PostgreSQL driver | Apache 2.0 |

### Caching, Jobs, Scheduling
| Package | Purpose | License |
|---------|---------|---------|
| `redis` | Redis client for K-V, locks, rate limiting | MIT |
| `celery[redis]` | Distributed task queue with Redis broker | BSD |
| `apscheduler` | Time-based scheduling (hourly polls, nightly rollups) | MIT |

### Observability & Operations
| Package | Purpose | License |
|---------|---------|---------|
| `prometheus_client` | /metrics endpoint for Prometheus | Apache 2.0 |
| `opentelemetry-sdk` | Distributed tracing and metrics | Apache 2.0 |
| `opentelemetry-instrumentation-fastapi` | Auto-instrument FastAPI | Apache 2.0 |
| `opentelemetry-instrumentation-httpx` | Auto-instrument httpx calls | Apache 2.0 |
| `structlog` | Structured JSON logging | MIT/Apache 2.0 |

### Security & Secrets
| Package | Purpose | License |
|---------|---------|---------|
| `cryptography` | TLS, encryption, certificate operations | Apache 2.0/BSD |
| `authlib` or `pyjwt` | JWT validation/signing for SSO/webhook receipts | BSD/MIT |
| `hvac` | HashiCorp Vault integration for secrets and rotation | Apache 2.0 |

### Data Wrangling (Optional)
| Package | Purpose | License |
|---------|---------|---------|
| `pandas` or `polars` | Report generation, data transforms | BSD/MIT |
| `pyarrow` | Columnar exports (Parquet format) | Apache 2.0 |
| `duckdb` | Ad-hoc analytics on Parquet/CSV (no server needed) | MIT |

---

## Kubernetes Operator / Helm Chart Shopping List

| Component | Chart / Operator | Purpose |
|-----------|-----------------|---------|
| PostgreSQL | Zalando Postgres Operator or Bitnami PostgreSQL chart | HA relational database |
| Redis | Spotahome Redis Operator (or Bitnami Redis chart) | Cache, broker, locks |
| MinIO | MinIO Helm chart or MinIO Operator | S3-compatible object storage |
| Traefik | Traefik Helm chart | Ingress controller |
| cert-manager | cert-manager Helm chart | TLS certificate automation |
| KEDA | KEDA Helm chart | Event-driven autoscaling |
| Prometheus + Grafana | kube-prometheus-stack chart | Metrics, alerting, dashboards |
| OpenTelemetry Collector | OTel Collector Helm chart or Operator | Traces/logs/metrics pipeline |
| Argo CD | Argo CD Helm chart | GitOps deployments |
| Argo Workflows | Argo Workflows Helm chart | Batch/cron/DAG pipelines |
| Vault | HashiCorp Vault Helm chart (or OpenBao) | Secrets management |
| Harbor | Harbor Helm chart | Private container registry |
| NATS (optional) | NATS Helm chart | Lightweight event streaming |
| Kafka (optional) | Strimzi Operator or Bitnami Kafka chart | Heavyweight event streaming |

---

## Scale Design Principles

Target baseline: **100 orgs x 1,000 sites x 10 devices = 1,000,000 devices** (5x headroom = 5,000,000).

1. **Database partitioning**: Partition config_revisions, audit_records, and sync_ledger by org_id and/or time range
2. **Async worker concurrency**: KEDA scales Celery workers per org queue depth; per-org API rate-limit budgeting
3. **Incremental diff storage**: After initial full snapshot, store only diffs with periodic full snapshots for integrity
4. **Configurable retention**: Time-based retention policies for config history (default 90 days full, 1 year audit)
5. **Read replicas**: PostgreSQL Patroni read replicas for query-heavy time-travel and audit views
6. **Artifact offload**: Large blobs (PCAPs, reports, evidence packs) stored in MinIO, not PostgreSQL

---

## Compose Example (Development / Single-Node)

```yaml
version: "3.9"
services:
  api:
    image: ghcr.io/yourorg/mist-ops-api:latest
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8080:8080"]
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

  worker:
    image: ghcr.io/yourorg/mist-ops-worker:latest
    env_file: .env
    depends_on: [postgres, redis]
    command: ["celery", "-A", "app.worker", "worker", "-Q", "default", "-l", "INFO"]

  beat:
    image: ghcr.io/yourorg/mist-ops-worker:latest
    env_file: .env
    depends_on: [redis]
    command: ["celery", "-A", "app.worker", "beat", "-l", "INFO"]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: mist_ops
      POSTGRES_USER: mist_ops
      POSTGRES_PASSWORD: change_me
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7
    command: ["redis-server", "--appendonly", "yes"]
    volumes: ["redisdata:/data"]

  minio:
    image: quay.io/minio/minio:latest
    command: ["server", "/data", "--console-address", ":9001"]
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: change_me
    ports: ["9000:9000", "9001:9001"]
    volumes: ["miniodata:/data"]

volumes:
  pgdata:
  redisdata:
  miniodata:
```

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| System of record | PostgreSQL (not SQLite) | Multi-writer, HA, partitioning, transactions required at 1M+ device scale |
| Cache/broker | Redis (not Memcached) | Persistence, pub/sub, Celery support, distributed locks, KEDA integration |
| Object storage | MinIO (not filesystem) | S3-compatible, scalable, K8s-native, separates blobs from relational data |
| API framework | FastAPI (not Flask/Django) | Async native, auto OpenAPI docs, Pydantic integration, performance |
| Task queue | Celery (not RQ/Dramatiq) | Mature, Redis broker, scheduling, retries, broad ecosystem |
| Ingress | Traefik (not nginx-ingress) | Actively maintained, Let's Encrypt native, Gateway API support |
| Autoscaling | KEDA (not custom HPA) | Event-driven, scale-to-zero, Redis/Kafka/HTTP scalers built-in |
| Secrets | Vault/OpenBao (not K8s Secrets alone) | Dynamic credentials, rotation, audit trail, cert-manager integration |
| GitOps | Argo CD (not Flux) | Rich UI, multi-cluster, drift detection, large community |
| Registry | Harbor (not Docker Hub) | On-prem, RBAC, vuln scanning, replication, content trust |
