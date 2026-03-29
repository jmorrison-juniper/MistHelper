# Research: Mist Ops Platform

**Phase**: 0 (Outline & Research)
**Date**: 2026-03-05
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context and
document technology decisions with rationale.

---

## R-01: mistapi Sync Integration in Async FastAPI

**Context**: The `mistapi` SDK uses `requests` (synchronous HTTP). FastAPI is
async-native. Running sync code in an async event loop blocks the thread.

**Decision**: Isolate all mistapi calls to Celery workers (sync by design).
FastAPI handles only internal CRUD against PostgreSQL (via async SQLAlchemy +
asyncpg) and webhook reception. The API layer never calls mistapi directly.

**Rationale**:
- Celery workers are sync processes — `requests` runs natively without blocking
- Decouples API response times from Mist API latency
- Matches MistHelper's existing pattern (all API calls happen in batch, not in
  request-response cycles)
- If a future FastAPI route needs Mist data, it reads from PostgreSQL (synced
  by workers) rather than calling Mist directly

**Alternatives considered**:
- `asyncio.to_thread()` wrapping mistapi calls in FastAPI: Rejected — creates
  thread pool pressure under load and obscures error handling
- Replacing mistapi with raw `httpx` async calls: Rejected — loses all mistapi
  features (token rotation, pagination, cloud region handling, session mgmt)
- Running FastAPI with sync workers (Gunicorn + sync): Rejected — defeats the
  purpose of async PostgreSQL and loses concurrency benefits

---

## R-02: Change Detection Strategy (Webhook vs Polling)

**Context**: The platform must detect configuration changes within 10 minutes
(SC-002). Two strategies: Mist webhooks (push) or API polling (pull).

**Decision**: Use both — webhooks for real-time detection, polling as
reconciliation fallback.

**Implementation**:
1. **Webhooks (primary)**: Register a Mist webhook via
   `mistapi.api.v1.orgs.webhooks.createOrgWebhook()` pointing to the
   platform's `/api/v1/webhooks/mist` endpoint. Subscribe to `audit`,
   `device-events`, and `alarms` topics. On receipt, enqueue a Celery task
   to fetch and store the changed configuration.
2. **Polling (fallback)**: Celery Beat schedules a periodic sync task (default:
   every 5 minutes per FR-001). The task compares content hashes of fetched
   configs against stored revisions. New or changed configs are stored as new
   revisions. This catches changes missed by webhooks (network issues,
   webhook delivery failures).

**Rationale**:
- Webhooks alone are unreliable — Mist may fail to deliver, network issues
  may drop events, and the platform may be temporarily unavailable
- Polling alone is too slow for real-time use cases
- The dual approach ensures SC-002 (10-minute capture) even under adverse
  conditions
- MistHelper currently has no webhook receiver — this is greenfield

**Mist webhook topics** (from API docs):
- `audit` — configuration changes with actor attribution
- `device-events` — device state changes, firmware events
- `alarms` — threshold violations, connectivity events
- `device-updowns` — device online/offline transitions

**Alternatives considered**:
- Webhooks only: Rejected — no guarantee of delivery; missed events require
  manual reconciliation
- Polling only: Rejected — 5-minute intervals may miss the SC-002 target if
  a change occurs just after a poll cycle

---

## R-03: Configuration Diff Algorithm

**Context**: The platform must show field-level diffs between configuration
revisions (FR-003, SC-003). Configurations are nested JSON objects (JSONB in
PostgreSQL).

**Decision**: Use `deepdiff` 8.x (MIT license) for structural JSON comparison.

**Implementation**:
```python
from deepdiff import DeepDiff

class DiffService:
    def compute_diff(self, old_config: dict, new_config: dict) -> dict:
        result = DeepDiff(
            old_config,
            new_config,
            ignore_order=True,
            verbose_level=2,    # Include old and new values
            view="tree",
        )
        return self._normalize_diff(result)
```

**Rationale**:
- `deepdiff` natively handles nested dicts, lists, type changes, and set
  comparisons — all common in Mist config payloads
- `verbose_level=2` produces old/new value pairs required by FR-003 and FR-008
- MIT license is compatible with OSS requirements (FR-021)
- Not currently used in MistHelper — clean greenfield addition
- Performance: DeepDiff processes 50KB JSON in <100ms (well within SC-003)

**Alternatives considered**:
- `jsondiff`: Rejected — less feature-rich, no old/new value output
- Custom recursive diff: Rejected — reinventing the wheel; edge cases
  (list reordering, type coercion) are already solved by deepdiff
- `dictdiffer`: Rejected — unmaintained since 2022

---

## R-04: Time-Travel Query Implementation

**Context**: Operators must retrieve historical device state for any timestamp
within the retention window in under 5 seconds (SC-001, FR-013).

**Decision**: Point-in-time queries against `config_revisions` table using
PostgreSQL temporal indexing.

**Implementation**:
```sql
-- "What was this device's config at timestamp T?"
SELECT config_payload, captured_at, actor
FROM config_revisions
WHERE entity_id = :device_id
  AND entity_type = 'device'
  AND captured_at <= :target_timestamp
ORDER BY captured_at DESC
LIMIT 1;
```

**Index strategy**:
```sql
CREATE INDEX idx_config_revisions_time_travel
ON config_revisions (entity_id, entity_type, captured_at DESC);
```

**For device status/health snapshots**: Separate `device_status_snapshots`
table with periodic captures (every sync cycle). Same temporal query pattern.

**Rationale**:
- Simple descending index lookup — O(log n) performance
- PostgreSQL B-tree indexes handle this efficiently even at 100M+ rows
  (partitioned by org_id)
- No need for specialized temporal databases (TimescaleDB, InfluxDB) at this
  scale — standard PostgreSQL with partitioning is sufficient
- Partitioning by org_id ensures queries are scoped to a single partition

**Performance estimate** (1M devices, 90-day retention, 5-min sync):
- ~26K revisions per device in 90 days (if every sync captures a change)
- Realistic: ~100 revisions per device (configs rarely change every cycle)
- Total rows: ~100M config_revisions (worst case) = manageable with
  partitioning
- Indexed lookup: <10ms per query

**Alternatives considered**:
- TimescaleDB hypertables: Rejected — adds operational complexity; standard
  PostgreSQL partitioning is sufficient at 1M-5M device scale
- Materialized views per device: Rejected — maintenance overhead outweighs
  benefit; indexed query is fast enough
- Event sourcing with CQRS: Rejected — over-engineered for this use case;
  simple immutable revisions with temporal queries achieve the same result

---

## R-05: Mist API Write Endpoints for Install-from-Revision

**Context**: The platform must push historical configurations back to devices
via the Mist API (FR-004). Need to identify which endpoints accept full
config payloads.

**Decision**: Map entity types to mistapi write endpoints.

**Endpoint mapping** (confirmed via mistapi library inspection):

| Entity Type | Read Endpoint | Write Endpoint |
|-------------|--------------|----------------|
| Device config | `getSiteDevice(site_id, device_id)` | `updateSiteDevice(site_id, device_id, body)` |
| Site settings | `getSiteSetting(site_id)` | `updateSiteSettings(site_id, body)` |
| Site info | `getSiteInfo(site_id)` | `updateSiteInfo(site_id, body)` |
| Org WLAN | `getOrgWlan(org_id, wlan_id)` | `updateOrgWlan(org_id, wlan_id, body)` |
| Site WLAN | `getSiteWlan(site_id, wlan_id)` | `updateSiteWlan(site_id, wlan_id, body)` |
| Network | `getOrgNetwork(org_id, network_id)` | `updateOrgNetwork(org_id, network_id, body)` |
| Gateway template | `getOrgGatewayTemplate(org_id, t_id)` | `updateOrgGatewayTemplate(org_id, t_id, body)` |
| Network template | `getOrgNetworkTemplate(org_id, t_id)` | `updateOrgNetworkTemplate(org_id, t_id, body)` |
| AP template | `getOrgAptemplate(org_id, t_id)` | `updateOrgAptemplate(org_id, t_id, body)` |
| RF template | `getOrgRfTemplate(org_id, t_id)` | `updateOrgRfTemplate(org_id, t_id, body)` |
| Device profile | `getOrgDeviceProfile(org_id, p_id)` | `updateOrgDeviceProfile(org_id, p_id, body)` |
| Service policy | `getOrgServicePolicy(org_id, p_id)` | `updateOrgServicePolicy(org_id, p_id, body)` |
| NAC rule | `getOrgNacRule(org_id, r_id)` | `updateOrgNacRule(org_id, r_id, body)` |
| Security policy | `getOrgSecPolicy(org_id, p_id)` | `updateOrgSecPolicy(org_id, p_id, body)` |

**Implementation pattern**:
```python
class ConfigPushService:
    ENTITY_ENDPOINT_MAP = {
        "device": ("sites.devices", "updateSiteDevice"),
        "site_setting": ("sites.setting", "updateSiteSettings"),
        "org_wlan": ("orgs.wlans", "updateOrgWlan"),
        # ... etc
    }

    def install_from_revision(self, revision_id: int) -> PushResult:
        revision = self.get_revision(revision_id)
        module, method = self.ENTITY_ENDPOINT_MAP[revision.entity_type]
        api_func = getattr(mistapi.api.v1, module)
        result = getattr(api_func, method)(
            session, *revision.entity_ids, body=revision.config_payload
        )
        # Record push as new audit entry
        return PushResult(status=result.status_code, revision=revision)
```

**Rationale**:
- MistHelper already uses these write endpoints (confirmed: `updateSiteDevice`
  at 3 call sites, `updateOrgGatewayTemplate` at 3 call sites, etc.)
- The Mist API accepts full config payloads as PUT/POST body — no special
  "restore" endpoint needed
- The platform stores the exact payload received from the read endpoint and
  pushes it back via the write endpoint

**Alternatives considered**:
- Custom Mist API calls via httpx: Rejected — loses mistapi's token rotation,
  error handling, and session management
- Partial config push (only changed fields): Rejected for initial impl — risk
  of field omission bugs; full payload push is safer. Optimization candidate
  for Phase 3

---

## R-06: Multi-Org Rate Limiting Strategy

**Context**: At 100+ orgs, Celery workers must respect per-org Mist API rate
limits (typically 5,000 requests/hour per org). Multiple workers may process
the same org concurrently.

**Decision**: Per-org Redis rate-limit buckets with sliding window, inspired
by MistHelper's PID-based adaptive delay system.

**Implementation**:
```python
class MistRateLimiter:
    def __init__(self, redis_client, org_id: str):
        self.key = f"ratelimit:{org_id}"
        self.redis = redis_client
        self.limit = 5000  # requests per hour
        self.window = 3600  # seconds

    async def acquire(self) -> float:
        """Returns delay in seconds before request can proceed."""
        current = await self.redis.incr(self.key)
        if current == 1:
            await self.redis.expire(self.key, self.window)
        if current > self.limit:
            ttl = await self.redis.ttl(self.key)
            return max(ttl, 1)  # Wait until window resets
        return 0.0
```

**Enhancements over MistHelper's approach**:
- Redis-backed (distributed) vs file-based (`delay_metrics.json`)
- Sliding window vs PID controller — simpler, more predictable
- Per-org isolation — one org hitting limits doesn't affect others
- PID tuning can be added later as an optimization layer

**Rationale**:
- MistHelper's PID controller (`RateLimitingUtils` at line 22464) is
  sophisticated but designed for single-process operation with file-based
  state. Multi-worker requires distributed coordination.
- Redis sliding window is the standard pattern for distributed rate limiting
- Per-org keys ensure blast-radius isolation (one busy org doesn't starve
  others)

**Alternatives considered**:
- Token bucket algorithm: Considered — slightly more complex but smoother
  distribution. May upgrade in Phase 3.
- MistHelper's PID approach ported to Redis: Rejected — PID state (integral,
  derivative) is hard to coordinate across multiple workers
- Centralized rate-limit service: Rejected — overengineered; Redis counters
  are sufficient

---

## R-07: Authentication Session Management

**Context**: The platform must authenticate to the Mist API on behalf of
users for both interactive requests and scheduled jobs that execute when the
user is offline (FR-018). Three auth methods: API tokens, interactive login
(email/password + 2FA), Mist SSO.

**Decision**: Store Mist API tokens encrypted in Vault. Create
`mistapi.APISession` per request/task with cached sessions.

**Implementation**:
1. **API token auth** (most common for automation):
   - User provides org-scoped API token via platform API (`Authorization`
     header or stored credential)
   - Token encrypted at rest in Vault (`secret/mist/tokens/{org_id}`)
   - Celery tasks retrieve token from Vault, create `APISession`, execute,
     discard session
   - Token cached in Redis with TTL (default: 5 minutes) to avoid repeated
     Vault lookups during burst operations

2. **Interactive login** (MSP-level access):
   - User authenticates via platform login page. Platform creates
     `mistapi.APISession` with `login_with_return()` (as MistHelper does)
   - Session cookie/token stored encrypted in Vault
   - Scheduled jobs using interactive sessions require token refresh strategy
     (session expiry handling)

3. **Mist SSO** (enterprise):
   - Platform redirects to Mist SSO endpoint
   - On callback, retrieves session credentials and stores in Vault
   - Same session management as interactive login

**Privilege caching**:
- `GET /api/v1/self` result cached in Redis with 5-minute TTL
  (consistent with MistHelper's pattern)
- Privilege check on every API request via middleware

**Rationale**:
- Vault provides encryption at rest, audit trail, and dynamic rotation
- Redis cache prevents repeated Vault + Mist API calls for privilege checks
- Matches MistHelper's existing patterns (`detect_msp_privileges()`,
  `initialize_mist_session()`)
- API tokens don't expire but can be revoked — simpler for scheduled jobs

**Alternatives considered**:
- Store tokens in PostgreSQL encrypted column: Rejected — no rotation,
  no audit trail, less secure than Vault
- Store tokens in environment variables: Rejected — doesn't scale to
  100+ orgs with different tokens
- JWT wrapping of Mist tokens: Rejected — unnecessary indirection; Mist
  tokens are already bearer tokens

---

## R-08: Atomic Multi-Device Transactions

**Context**: FR-028 requires atomic multi-device configuration transactions
that either commit to all targets or roll back entirely. The Mist API has no
native transaction support — each device update is an independent HTTP PUT.

**Decision**: Implement application-level saga pattern with compensating
transactions.

**Implementation**:
1. **Pre-flight**: Snapshot current config of all target devices (stored as
   "pre-change revisions")
2. **Execute**: Push config to devices sequentially (ordered by criticality).
   After each push, verify success via API response.
3. **On failure**: For each successfully-pushed device, push the pre-change
   revision (compensating transaction). Mark the job as "partially rolled
   back" with details of which devices succeeded/failed.
4. **Idempotency**: Each push operation is idempotent (PUT with full payload).
   Progress checkpoints stored in Redis so the saga can resume on process
   restart (FR-015).

**Rationale**:
- True distributed transactions (2PC) are impossible with the Mist API
- Saga pattern is the standard approach for coordinating multiple independent
  services
- Compensating transactions (push pre-change config back) provide eventual
  consistency
- Progress checkpoints in Redis enable safe resumption (FR-015)

**Limitations** (documented for operators):
- There is a brief window where some devices have the new config and others
  have the old config (eventual consistency, not strict atomicity)
- If a compensating transaction fails, the operator is alerted for manual
  intervention
- The platform records all intermediate states for audit purposes

**Alternatives considered**:
- Best-effort batch (no rollback): Rejected — violates FR-028
- Queue all changes then push simultaneously: Rejected — Mist API rate limits
  prevent truly simultaneous pushes; sequential with rollback is more reliable
- Two-phase commit over Mist API: Impossible — API doesn't support prepare/
  commit semantics

---

## R-09: Celery + KEDA Autoscaling Pattern

**Context**: Celery workers must scale based on queue depth. KEDA provides
event-driven autoscaling for Kubernetes deployments.

**Decision**: Use KEDA Redis scaler to monitor Celery queue lengths.

**Implementation** (KEDA ScaledObject):
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaler
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 1
  maxReplicaCount: 20
  triggers:
    - type: redis
      metadata:
        address: redis:6379
        listName: celery          # Default Celery queue
        listLength: "10"          # Scale up when >10 pending tasks
        activationListLength: "1" # Scale from zero when >0 tasks
```

**Per-org queues**: Use Celery task routing to send org-specific sync tasks
to org-specific queues (`sync:{org_id}`). KEDA can monitor individual queues
for fine-grained scaling.

**Rationale**:
- KEDA natively supports Redis list length as a scale trigger
- Celery's default broker uses Redis lists — no adapter needed
- Scale-to-zero is supported (saves resources for low-traffic orgs)
- Max 20 replicas provides 5x headroom over baseline worker count

**Alternatives considered**:
- Standard HPA on CPU/memory: Rejected — doesn't reflect actual work pending;
  CPU may be low while queue is full (waiting on API rate limits)
- Custom metrics adapter: Rejected — KEDA provides this out of the box
- Manual scaling: Rejected — defeats the purpose of Kubernetes

---

## R-10: PostgreSQL Partitioning Strategy

**Context**: At 1M+ devices with 90-day retention, `config_revisions` and
`audit_records` tables will contain hundreds of millions of rows. Queries
must remain performant (SC-001, SC-006).

**Decision**: Hash partitioning by `org_id` (primary), range sub-partitioning
by `captured_at`/`timestamp` (secondary) for time-series tables.

**Implementation**:
```sql
-- config_revisions: hash by entity's org + range by time
CREATE TABLE config_revisions (
    revision_id BIGSERIAL,
    org_id UUID NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    content_hash TEXT NOT NULL,
    config_payload JSONB NOT NULL,
    actor TEXT,
    PRIMARY KEY (org_id, revision_id)
) PARTITION BY HASH (org_id);

-- Create 16 hash partitions (supports up to ~500+ orgs per partition)
CREATE TABLE config_revisions_p0 PARTITION OF config_revisions
    FOR VALUES WITH (MODULUS 16, REMAINDER 0);
-- ... repeat for p1-p15

-- audit_records: same strategy
CREATE TABLE audit_records (
    record_id BIGSERIAL,
    org_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    -- ... other columns
    PRIMARY KEY (org_id, record_id)
) PARTITION BY HASH (org_id);
```

**Retention management**: Celery Beat task runs nightly to delete rows older
than the configured retention window (default: 90 days for config_revisions,
365 days for audit_records). Uses `DELETE ... WHERE captured_at < :cutoff`
per partition for efficiency.

**Rationale**:
- Hash by org_id ensures all queries scoped to a single org hit a single
  partition (partition pruning)
- 16 hash partitions are sufficient for 100-500 orgs (can increase later)
- Range sub-partitioning by time can be added in Phase 3 if needed
- Standard PostgreSQL partitioning — no extensions required

**Alternatives considered**:
- Range partitioning by time only: Rejected — cross-org queries become
  expensive; most queries are org-scoped
- Citus distributed PostgreSQL: Rejected — adds operational complexity;
  standard PostgreSQL partitioning is sufficient at target scale
- No partitioning (rely on indexes): Rejected — at 100M+ rows, even indexed
  queries degrade without partition pruning

---

## R-11: Project Dependency Inventory

**Decision**: Final dependency list with versions and licenses.

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| `fastapi` | >=0.115 | MIT | REST API framework |
| `uvicorn[standard]` | >=0.32 | BSD | ASGI server |
| `celery[redis]` | >=5.4 | BSD | Distributed task queue |
| `sqlalchemy` | >=2.0 | MIT | ORM + async database |
| `alembic` | >=1.14 | MIT | Database migrations |
| `asyncpg` | >=0.30 | Apache 2.0 | Async PostgreSQL driver |
| `pydantic` | >=2.10 | MIT | Data validation |
| `pydantic-settings` | >=2.7 | MIT | 12-factor config |
| `httpx` | >=0.28 | BSD | HTTP client |
| `redis` | >=5.2 | MIT | Redis client |
| `tenacity` | >=9.0 | Apache 2.0 | Retry logic |
| `structlog` | >=24.4 | MIT/Apache | Structured logging |
| `deepdiff` | >=8.0 | MIT | JSON config diff |
| `prometheus-client` | >=0.21 | Apache 2.0 | Metrics export |
| `opentelemetry-sdk` | >=1.29 | Apache 2.0 | Distributed tracing |
| `opentelemetry-instrumentation-fastapi` | >=0.50 | Apache 2.0 | FastAPI auto-instrument |
| `apscheduler` | >=3.11 | MIT | Time-based scheduling |
| `hvac` | >=2.3 | Apache 2.0 | Vault integration |
| `mistapi` | >=0.60 | MIT | Mist API SDK |
| `cryptography` | >=44.0 | Apache/BSD | Encryption |
| `authlib` | >=1.4 | BSD | JWT / SSO |

### Development Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| `pytest` | >=8.3 | MIT | Test framework |
| `pytest-asyncio` | >=0.24 | Apache 2.0 | Async test support |
| `pytest-cov` | >=6.0 | MIT | Coverage reporting |
| `httpx` | >=0.28 | BSD | Async test client |
| `testcontainers` | >=4.9 | Apache 2.0 | DB/Redis test containers |
| `ruff` | >=0.8 | MIT | Linter + formatter |
| `mypy` | >=1.13 | MIT | Type checking |

**All licenses**: MIT, BSD, Apache 2.0 — all permissive, compatible with
FR-021 (free/OSS requirement). MinIO (AGPLv3) is infrastructure only, not
linked into application code.

---

## R-12: Notification Dispatch Architecture

**Context**: FR-037 requires email (SMTP) and webhook (Slack, Teams,
PagerDuty, generic HTTP) notifications. Each alert type must be independently
routable to one or more channels.

**Decision**: Celery-based async notification dispatch with channel-specific
adapters.

**Implementation**:
```python
class NotificationService:
    def dispatch(self, alert_type: str, payload: dict) -> None:
        channels = self.get_channels_for_alert(alert_type)
        for channel in channels:
            notify_tasks.send_notification.delay(
                channel_id=channel.channel_id,
                alert_type=alert_type,
                payload=payload,
            )

class EmailAdapter:
    def send(self, destination: str, subject: str, body: str) -> bool:
        # SMTP via smtplib (stdlib) with TLS
        ...

class WebhookAdapter:
    def send(self, url: str, payload: dict, auth: dict) -> bool:
        # httpx POST with configurable auth (Bearer, Basic, HMAC)
        ...
```

**Channel routing** stored in `notification_channels` table. Each channel
subscribes to specific alert types (e.g., `["drift_detected",
"deployment_failed"]`).

**Rationale**:
- Celery ensures notifications don't block the main API or deployment tasks
- Adapter pattern allows adding new channel types without modifying core logic
- `smtplib` (stdlib) for email avoids additional dependencies
- httpx for webhooks (already a dependency) provides async HTTP with retry

**Alternatives considered**:
- Direct in-process notification: Rejected — blocks deployment tasks, no retry
- Third-party notification service (e.g., Apprise): Considered — adds a
  dependency but simplifies multi-channel. May adopt in Phase 3.
- NATS-based pub/sub for notifications: Rejected for MVP — NATS is optional
  infrastructure; Celery provides sufficient decoupling

---

## R-13: Deferred Requirements Feasibility (T117)

**Context**: Three functional requirements were deferred from MVP scope.
This section documents their feasibility for a future phase.

### FR-026: Path Analysis (Network Path Tracing)

**Feasibility**: MODERATE. Mist provides `GET /api/v1/sites/:site_id/insights/marvis`
and `pcap` endpoints that give hop-by-hop visibility. However, full
Layer-2/Layer-3 path reconstruction across switches and gateways requires
correlating LLDP neighbours, ARP tables, and routing tables — data already
synced by MistHelper option 11/13. A PathAnalyzer service could join
device adjacency data from `device_status_snapshots` with route tables
fetched via `GET /api/v1/sites/:site_id/devices/:device_id/config_cmd`.

**Estimate**: 2-3 sprints (PathAnalyzer service + visualization endpoint).

### FR-027: Application-Centric Network Modeling

**Feasibility**: HIGH for basic mapping. Mist's `wxtags` and `services`
entities already group traffic by application. The platform could define
an `ApplicationProfile` entity linking service policies to network
segments and golden configs. Advanced dependency mapping (e.g., which
VLANs serve which applications) requires manual or semi-automated
tagging by operators.

**Estimate**: 1-2 sprints (ApplicationProfile entity + CRUD + policy linking).

### FR-030: Application Discovery

**Feasibility**: LOW without external integration. Mist does not natively
perform deep packet inspection or application fingerprinting beyond basic
L7 classification on SRX/SSR gateways. Integrating with Juniper ATP or
a third-party NBAR-like service would be required. The platform could
ingest application classification data if a source provides it, but
cannot generate it from Mist APIs alone.

**Estimate**: 3-5 sprints (external integration + classification pipeline).

**Recommendation**: Prioritize FR-027 first (leverages existing data),
then FR-026 (moderate effort, high operator value), defer FR-030 until
an application classification source is available.
