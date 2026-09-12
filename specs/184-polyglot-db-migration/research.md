# Research: Polyglot Database Migration

**Feature**: 184-polyglot-db-migration | **Date**: 2026-04-20

## 1. ArangoDB Python Driver

**Decision**: Use `python-arango` 8.3.2 (official driver by ArangoDB Inc)
**Rationale**: Only official, actively maintained Python driver. Supports Python 3.9+ (compatible with 3.13). Provides both low-level collection operations and high-level graph APIs.
**Alternatives considered**:
- Direct HTTP via `requests`: Rejected — reinvents driver functionality, no connection pooling, no type safety
- `aioarango`: Rejected — async-only, MistHelper is synchronous
- `python-arango-async`: Considered for future — separate package, not needed now

### Key patterns

- **Upsert**: `collection.insert(doc, overwrite=True, overwrite_mode="replace")` — equivalent to SQLite's `INSERT OR REPLACE`
- **Graph creation**: `db.create_graph("network_topology")` with vertex/edge definitions
- **Edge insertion**: Edge collection with `_from`/`_to` referencing `collection/key`
- **Connection**: `ArangoClient(hosts="http://arangodb:8529").db("misthelper", username="root", password=<from_env>)`

## 2. Redis TimeSeries Client

**Decision**: Use `redis` (redis-py) 7.4.0 with `hiredis` C extension for performance
**Rationale**: Official Redis client with built-in TimeSeries namespace (`r.ts()`). No separate package needed. `hiredis` gives 10x parsing speedup.
**Alternatives considered**:
- `redistimeseries`: Rejected — deprecated in favor of built-in `redis.ts()` namespace
- `aioredis`: Rejected — merged into `redis` package, synchronous API sufficient

### Key patterns

- **Create**: `ts.create("metric:device_id", retention_msecs=N, labels={"device_id": "...", "metric": "cpu"})`
- **Add**: `ts.add("metric:device_id", "*", value)` — auto-timestamp from server
- **Query**: `ts.range(key, from_ts, to_ts)` returns `[(timestamp, value), ...]`
- **Compaction**: `ts.createrule(src_key, dest_key, aggregation_type="avg", bucket_size_msec=3600000)`
- **Cross-series**: `ts.mrange(from, to, filters=["metric=cpu"])` with label matching

## 3. ArangoDB Container

**Decision**: Use `arangodb:3.12` (Docker Hub official image)
**Rationale**: Latest stable LTS. Official image supports amd64 + arm64. Community Edition sufficient (Apache 2.0 license).
**Alternatives considered**:
- ArangoDB 3.11: Rejected — older, fewer features, 3.12 is current stable

### Configuration

| Setting | Value |
| - | - |
| Image | `arangodb:3.12` |
| Port | `8529` |
| Auth env | `ARANGO_ROOT_PASSWORD` |
| Data volume | `/var/lib/arangodb3` |
| Health check | `curl -f http://localhost:8529/_api/version` |
| Dataset limit | 100 GB (Community Edition 3.12+) |
| Max document key | 254 bytes |

## 4. Redis Stack Container

**Decision**: Use `redis/redis-stack-server:latest` (includes TimeSeries module)
**Rationale**: Official Redis image with all modules pre-loaded (TimeSeries, Search, JSON, Graph, Bloom). Server-only variant (no RedisInsight UI) is lighter.
**Alternatives considered**:
- `redis/redis-stack`: Rejected — includes RedisInsight web UI (unnecessary overhead)
- `redis:latest` + manual module loading: Rejected — complex, fragile
- `valkey`: Considered for future — Redis fork, but TimeSeries module availability uncertain

### Configuration

| Setting | Value |
| - | - |
| Image | `redis/redis-stack-server:latest` |
| Port | `6379` |
| Auth | `REDIS_ARGS="--requirepass ${REDIS_PASSWORD}"` |
| Memory limit | `REDIS_ARGS="--maxmemory 2gb --maxmemory-policy allkeys-lru"` |
| Data volume | `/data` |
| Health check | `redis-cli -a ${REDIS_PASSWORD} ping` |

## 5. Data Routing Strategy

**Decision**: Route by `ENDPOINT_PRIMARY_KEY_STRATEGIES` type field
**Rationale**: The existing dictionary already classifies all 53 endpoints by data pattern. No new metadata needed — the `type` field directly maps to backend.
**Alternatives considered**:
- Explicit backend field per endpoint: Rejected — redundant with type field, increases maintenance
- Configuration file mapping: Rejected — adds external dependency when routing is deterministic from type

### Routing rules

| PK Strategy Type | Count | Backend | Collection/Key Pattern |
| - | - | - | - |
| `natural_pk` | ~17 | ArangoDB document | Collection per API function, `_key` = entity UUID |
| `composite_pk` | ~34 | Redis TimeSeries | Key = `metric:entity_id`, labels from PK fields |
| `auto_increment_with_unique` | ~2 | ArangoDB document | Collection per API function, auto-generated `_key` |

## 6. Compose Integration

**Decision**: Add `arangodb` and `redis-stack` services to existing `compose.yml`
**Rationale**: compose.yml already exists with `misthelper` and `ollama` services on `misthelper-network`. Adding services to the same network enables container DNS resolution.
**Alternatives considered**:
- Separate compose file: Rejected — adds operational complexity, requires network linking
- Kubernetes/Podman pods: Rejected — out of scope, single-node deployment

### Health check + depends_on pattern

```yaml
arangodb:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8529/_api/version"]
    interval: 10s
    timeout: 5s
    retries: 5

redis-stack:
  healthcheck:
    test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

misthelper:
  depends_on:
    arangodb:
      condition: service_healthy
    redis-stack:
      condition: service_healthy
```

## 7. Soft-Delete Pattern

**Decision**: Mark entities inactive with `_misthelper_deleted_at` timestamp field
**Rationale**: Preserves history for snapshots and graph edge integrity. Hard-delete would orphan edges and lose config snapshot history.
**Alternatives considered**:
- Hard delete with cascade: Rejected — loses history, complex edge cleanup
- TTL-based expiry: Rejected — unpredictable timing, no human control

## 8. Structured Logging

**Decision**: Use `structlog` for all new `src/db/` modules
**Rationale**: Constitution Principle V requires structured, machine-parseable logging for new modules. `structlog` integrates with stdlib `logging` and produces JSON-formatted entries compatible with monitoring tools.
**Alternatives considered**:
- stdlib `logging` only: Rejected — not structured, harder to parse programmatically
- `loguru`: Rejected — not in existing deps, `structlog` is more widely adopted for structured output
