# Storage and Locking Reference — Feature 1823 Upgrade Capture Portal

Research reference. No source code changed.

Every finding carries a `file_path:line_number` citation. Sections marked
**INFERENCE** are design proposals, not readings of the current code.

Configuration appears by variable name only. This document never reproduces a
secret value.

---

## 1. The router

### 1.1 Class and location

`DatabaseRouter` is the single dispatch point for every polyglot write
(`src/db/router.py:99-100`). The constructor stores the config, stores the
strategy map, and sets three availability flags to `False`
(`src/db/router.py:102-115`). The constructor returns early when
`config.standalone_mode` is true, and it connects no backend
(`src/db/router.py:116-118`). Otherwise it calls three connect helpers
(`src/db/router.py:119-121`).

Each connect helper wraps its writer constructor in `try`/`except`. A failure
sets the flag to `False` and logs one warning. A failure never raises
(`src/db/router.py:123-148`).

### 1.2 The write method signature

```python
def write(self, data: list[dict], api_function_name: str) -> WriteResult:
```

Source: `src/db/router.py:150`.

### 1.3 The result type

`WriteResult` is a dataclass with five fields (`src/db/__init__.py:111-119`).

| Field | Type | Meaning |
| --- | --- | --- |
| `success` | `bool` | Reported outcome |
| `backend` | `str` | One of `arangodb`, `redis`, `redis_json`, `dual`, `csv_only` |
| `records_written` | `int` | Rows the backend accepted |
| `records_failed` | `int` | Rows the backend rejected |
| `error_message` | `str` | Empty on the happy path |

`DualWriteResult` holds one `WriteResult` per leg
(`src/db/__init__.py:122-127`). Its `combined` property merges both legs
(`src/db/__init__.py:129-146`). `success` is true only when both legs succeed
(`src/db/__init__.py:134`).

### 1.4 The routing type sets

```python
ARANGO_ONLY_TYPES = {"natural_pk", "auto_increment_with_unique"}
DUAL_WRITE_TYPES  = {"composite_pk"}
TIMESERIES_TYPES  = {"timeseries_pk"}
DEFAULT_STRATEGY_TYPE = "auto_increment_with_unique"
```

Source: `src/db/router.py:22-25`.

Backend markers live at `src/db/router.py:27-30`. The module default strategy
lives at `src/db/router.py:50-53`.

### 1.5 How a write is routed, step by step

1. The caller invokes `write(data, api_function_name)` (`src/db/router.py:150`).
2. The router checks `config.standalone_mode`. If true, the router returns
   `WriteResult(success=True, backend="csv_only", records_written=0,
   records_failed=0)` and touches no backend (`src/db/router.py:152-158`).
   **This is a silent-success path. See section 2.**
3. The router resolves the strategy for the API function name
   (`src/db/router.py:159`). `_resolve_strategy` prefers a per-endpoint entry,
   then the caller `"default"` entry, then the module default
   (`src/db/router.py:281-285`).
4. The router reads `strategy["type"]` and defaults to
   `auto_increment_with_unique` (`src/db/router.py:160`).
5. `timeseries_pk` routes to `_write_redis` (`src/db/router.py:161-162`).
6. `composite_pk` routes to `_write_dual` (`src/db/router.py:163-164`).
7. Every other type routes to `_write_arango` (`src/db/router.py:165`).

`_write_arango` degrades to `_csv_fallback` when ArangoDB is unavailable
(`src/db/router.py:174-175`). On success it triggers a config snapshot
(`src/db/router.py:178-179`). An exception becomes an honest failure envelope
through `_error_write_result` (`src/db/router.py:181-183`,
`src/db/router.py:88-96`).

`_write_dual` writes Redis JSON first, then ArangoDB, then merges both results
(`src/db/router.py:266-279`).

### 1.6 The health check

```python
def health_check(self) -> dict[str, bool]:
    return {
        "arangodb": self._arango_available,
        "redis": self._redis_available,
        "redis_json": self._redis_json_available,
        "standalone": self.config.standalone_mode,
    }
```

Source: `src/db/router.py:287-294`.

The health check reads cached boolean flags. It issues no live probe. A backend
that died after startup still reports `True`.

---

## 2. The standalone defect — issue #1824

### 2.1 The method that decides standalone mode

```python
131    _standalone_logged = False  # One-shot standalone log guard.
132
133    @staticmethod
134    def _is_standalone_mode() -> bool:  # Detect non-container standalone.
135        """Auto-detect standalone mode: skip polyglot when not in a container."""
136        standalone_env = os.getenv("MISTHELPER_STANDALONE", "").lower()  # Read the override env.
137        if standalone_env == "true":  # Explicit standalone request.
138            return True  # Forced standalone.
139        if standalone_env == "false":  # Forced non-standalone.
140            return False  # Not standalone.
141        if not EnvironmentUtils.is_running_in_container():  # Auto-detect when not in container.
142            if not DataExporter._standalone_logged:  # Log once.
143                logging.info("Standalone mode auto-detected (not in container), skipping polyglot database")
144                DataExporter._standalone_logged = True  # Latch the one-shot log.
145            return True  # Standalone outside a container.
146        return False  # Containerized: not standalone.
```

Source: `src/export/data_exporter.py:131-146`.

### 2.2 Confirmed: the decision depends on a container check

Line 141 is the whole test. The method returns `True` when
`EnvironmentUtils.is_running_in_container()` returns `False`.

`is_running_in_container` runs an override check, then five heuristics in order
(`src/utils/environment_utils.py:142-154`, detector list at
`src/utils/environment_utils.py:127-140`). The heuristics look for
`/.dockerenv`, container environment variables, cgroup markers, the
`misthelper` runtime user, and the `/app` plus `sshd` layout. None of the five
probes contacts ArangoDB or Redis.

A developer who runs the portal on a laptop with a reachable ArangoDB on
`localhost:8529` therefore gets standalone mode. The polyglot layer is skipped
before any connection attempt (`src/export/data_exporter.py:148-156`, the call
at line 153).

A second, independent container check exists at
`src/maps/_container_detection.py:134-151`.

### 2.3 Confirmed: the CSV fallback reports success

Two code paths report success while nothing reaches a database.

**Path A — the router standalone branch.**

```python
152        if self.config.standalone_mode:  # WHY: standalone mode never touches a backend
153            return WriteResult(
154                success=True,
155                backend=BACKEND_CSV_ONLY,
156                records_written=0,
157                records_failed=0,
158            )  # WHY: csv-only success envelope for standalone runs
```

Source: `src/db/router.py:152-158`.

**Path B — the degraded-backend fallback.**

```python
372    @staticmethod
373    def _csv_fallback(api_function_name: str, backend: str) -> WriteResult:  # WHY: shared csv fallback envelope
374        """Return a csv_only result when the target backend is down."""
375        logger.warning(EVT_DEGRADED_MODE, api=api_function_name, backend=backend)  # WHY: single breadcrumb
376        return WriteResult(
377            success=True,
378            backend=BACKEND_CSV_ONLY,
379            records_written=0,
380            records_failed=0,
381            error_message=f"{backend} unavailable, CSV only",
382        )  # WHY: success=True keeps callers from treating csv fallback as a hard error
```

Source: `src/db/router.py:372-382`.

`success=True` with `records_written=0`. The inline comment at line 382 states
the intent plainly. A caller that checks only `result.success` cannot tell a
real write from a no-op.

A third layer hides the failure. `_perform_polyglot_write` catches every
exception and logs a warning (`src/export/data_exporter.py:158-171`, the catch
at lines 170-171). `write_with_format_selection` returns the CSV result and
discards the polyglot outcome entirely (`src/export/data_exporter.py:125-129`).

**Impact on feature 1823.** A capture that must be readable months later can
land in CSV only, while the portal reports success. The user learns nothing.
Fix issue #1824 before the feature depends on the router.

### 2.4 Proposed fix — INFERENCE

Replace the container heuristic with a reachability probe. Cache the result.
Emit one visible warning.

Proposed function signature and result type:

```python
@dataclass(frozen=True, slots=True)
class PolyglotReachability:
    """Cached outcome of a live TCP probe against the polyglot backends."""

    arango_reachable: bool
    redis_reachable: bool
    checked_at: float
    reason: str


PROBE_TIMEOUT_SECONDS = 1.5   # Bound the probe so a cold start never stalls.
PROBE_CACHE_SECONDS = 60.0    # Re-probe at most once a minute.


def probe_polyglot_reachable(
    config: DatabaseConfig,
    *,
    force: bool = False,
) -> PolyglotReachability:
    """Return a cached TCP reachability verdict for ArangoDB and Redis.

    Why:
        The current standalone test reads container markers only
        (src/export/data_exporter.py:141). A host process with a reachable
        database is misclassified as standalone, so writes silently skip the
        polyglot layer. A live TCP probe answers the real question.

    Args:
        config: Connection settings that name the hosts and ports.
        force: Ignore the cache and probe now.

    Returns:
        A PolyglotReachability with one flag per backend.
    """
```

Behavior rules for the fix:

1. Open a TCP socket to the ArangoDB host and port, then to the Redis host and
   port. Do not resolve DNS only. The current DNS-only helper at
   `src/db/__init__.py:81-108` returns standalone only when **both** names fail
   to resolve (`src/db/__init__.py:90`). A resolvable but dead host passes.
2. Cache the verdict for `PROBE_CACHE_SECONDS`. Store the cache in a
   module-level variable next to the existing one-shot latch pattern at
   `src/export/data_exporter.py:131`.
3. Emit exactly one `logging.warning` per process when either backend is
   unreachable. Latch it the same way `_standalone_logged` latches
   (`src/export/data_exporter.py:142-144`). The warning must name the host and
   the port and must state that the rows reached CSV only.
4. Keep the `MISTHELPER_STANDALONE` override. An explicit value still wins
   (`src/export/data_exporter.py:136-140`).

Second half of the fix — make the result honest:

5. Add `persisted: bool = False` to `WriteResult` (`src/db/__init__.py:111-119`).
   Set it `True` only when a backend accepted rows. Both CSV envelopes leave it
   `False` (`src/db/router.py:152-158`, `src/db/router.py:372-382`). The default
   keeps every existing caller compiling.
6. The capture write path must check `persisted`, not `success`. A capture that
   did not persist must fail the run and tell the user.

---

## 3. The ArangoDB writer

### 3.1 The writer class

`ArangoDBWriter` is the primary document writer
(`src/db/arango_writer.py:3893-3894`).

The constructor runs a DNS pre-flight, builds the client, ensures the database,
reopens the client bound to that database, and ensures the named graph
(`src/db/arango_writer.py:3896-3909`). The database handle is stored as
`self._db` (`src/db/arango_writer.py:3903`).

`_preflight_dns` raises `ConnectionError` when the host name does not resolve
(`src/db/arango_writer.py:3911-3917`). It is a name lookup only. It proves
nothing about reachability. This is the same weakness described in section 2.

### 3.2 The write method

```python
def write(self, data: list[dict], collection_name: str, strategy: dict) -> WriteResult:
```

Source: `src/db/arango_writer.py:3965`.

The method ensures the collection, returns early on empty input, prepares every
document, batch-imports, and repopulates the graph when at least one row landed
(`src/db/arango_writer.py:3965-3984`).

### 3.3 How collections are named

The collection name is the API function name. The router passes
`api_function_name` straight through as `collection_name`
(`src/db/router.py:177`). `_ensure_collection` creates a missing collection and
sets the edge flag when the name appears in `_EDGE_COLLECTION_NAMES`
(`src/db/arango_writer.py:3957-3963`, name set at
`src/db/arango_writer.py:1053`).

Vertex collections use short plural nouns such as `orgs`, `sites`, and
`templates`. The mapping from API function name to vertex collection lives in
`ENTITY_TYPE_TO_VERTEX` (`src/db/arango_writer.py:1058`). The mapping that
drives vertex and edge population lives in `COLLECTION_VERTEX_MAP`
(`src/db/arango_writer.py:1247`).

### 3.4 The batch size

```python
IMPORT_BATCH_SIZE = 5000
```

Source: `src/db/arango_writer.py:26`.

`_sum_batch_results` windows the document list in chunks of that size
(`src/db/arango_writer.py:3997-4006`). `_import_single_batch` calls
`collection.import_bulk(batch, on_duplicate="replace")`
(`src/db/arango_writer.py:4012`). A driver exception marks the whole batch
failed (`src/db/arango_writer.py:4013-4020`).

Redis batch sizes differ. See section 4.

### 3.5 The graph name

```python
GRAPH_NAME = "mist_network_topology"
```

Source: `src/db/arango_writer.py:25`.

`_ensure_graph` creates the graph or refreshes it when the live edge definitions
drift (`src/db/arango_writer.py:3931-3943`). `_refresh_graph_if_stale` deletes
and recreates the graph with `drop_collections=False`, so the underlying data
survives (`src/db/arango_writer.py:3945-3955`).

### 3.6 Edge collection conventions

Edge collection names use PascalCase verb phrases. Examples read directly from
the source include `ConfigSnapshotForEntity`
(`src/db/arango_writer.py:291`) and `TemplateAssignedToSite`
(`src/db/arango_writer.py:4225`).

Two edge definition tables exist. `GRAPH_EDGE_DEFINITIONS` is the subset the
named graph shows (`src/db/arango_writer.py:37`). `EDGE_DEFINITIONS` is the
full list (`src/db/arango_writer.py:239`). All edge collections are created and
populated. Only the graph subset is visible in the graph viewer
(`src/db/arango_writer.py:3932-3937`).

Edge documents carry a deterministic key so re-runs upsert cleanly. The key is
the first 16 characters of the sha256 of `"{from_id}:{to_id}"`
(`src/db/arango_writer.py:4248-4253`). The edge body carries `_key`, `_from`,
`_to`, and `_misthelper_updated_at` (`src/db/arango_writer.py:4134-4143`).

Vertex identifiers are `"{collection}/{sanitized_key}"`
(`src/db/arango_writer.py:4136-4137`). `_sanitize_key` replaces `/` and `:`
with `_` (`src/db/arango_writer.py:4266-4269`). A capture key must therefore
avoid both characters.

### 3.7 Document preparation and key computation

`_prepare_document` copies the record, assigns `_key`, and stamps two internal
fields (`src/db/arango_writer.py:4025-4034`):

- `_key`
- `_misthelper_updated_at` — epoch seconds
- `_misthelper_deleted_at` — set to `None` on every fresh write

`_compute_key` decides the key (`src/db/arango_writer.py:4036-4042`):

- `auto_increment_with_unique` always returns a fresh `uuid4`
  (`src/db/arango_writer.py:4039-4040`). **A second write of the same record
  creates a duplicate document.**
- Every other type reads the first primary-key field, and falls back to a
  `uuid4` when the field is missing (`src/db/arango_writer.py:4041`).

This behavior drives the strategy recommendation in section 6.

### 3.8 Change detection and versioning helpers

Change detection exists today and uses sha256 over canonical JSON.

- `_hash_body` returns `sha256(json.dumps(config_body, sort_keys=True))`
  (`src/db/arango_writer.py:4319-4322`).
- `_latest_snapshot_hash` runs an AQL query with `SORT ... DESC LIMIT 1` and
  returns the newest stored hash (`src/db/arango_writer.py:4324-4332`).
- `snapshot` skips the write when the hash is unchanged
  (`src/db/arango_writer.py:4306-4307`).

The router has a parallel helper. `_hash_payload` adds `default=str` so
non-JSON types survive (`src/db/router.py:82-85`). Prefer the router variant
for Mist payloads.

Soft delete replaces hard delete. `mark_absent_as_deleted` scans a collection
and stamps `_misthelper_deleted_at` on rows missing from the current key set
(`src/db/arango_writer.py:4271-4293`).

### 3.9 Warning — the word "snapshot" is already taken

Feature 1823 uses the term **capture**. The repository already uses the term
**snapshot** for a different concept. Do not reuse "snapshot" in any new
identifier. Do not treat the two as synonyms.

Existing "snapshot" identifiers, recorded exactly:

| Identifier | Location |
| --- | --- |
| `snapshot` | `src/db/arango_writer.py:4295` |
| `_hash_body` | `src/db/arango_writer.py:4319` |
| `_latest_snapshot_hash` | `src/db/arango_writer.py:4324` |
| `_build_snapshot_doc` | `src/db/arango_writer.py:4334` |
| `_create_snapshot_edge` | `src/db/arango_writer.py:4355` |
| `_snapshot_edge_doc` | `src/db/arango_writer.py:4374` |
| `_backfill_snapshot_edges` | `src/db/arango_writer.py:4385` |
| `_backfill_already_done` | `src/db/arango_writer.py:4398` |
| `_collect_backfill_edges` | `src/db/arango_writer.py:4405` |
| `_backfill_edge_for` | `src/db/arango_writer.py:4417` |
| `config_snapshots` collection | `src/db/arango_writer.py:4305` |
| `ConfigSnapshotForEntity` edge collection | `src/db/arango_writer.py:291`, `src/db/arango_writer.py:4367` |
| `SnapshotRequest` | `src/db/router.py:71-80` |
| `_snapshot_if_config` | `src/db/router.py:185` |
| `SNAPSHOT_SOURCE_API` | `src/db/router.py:32` |
| `SNAPSHOT_SOURCE_WEBHOOK` | `src/db/router.py:33` |
| `EVT_SNAPSHOT_FAILED` | `src/db/router.py:61` |
| `EVT_WEBHOOK_SNAPSHOT_FAILED` | `src/db/router.py:62` |
| `CONFIG_SNAPSHOT_APIS` | `src/db/router.py:38-48` |
| `_check_periodic_snapshot` | `src/export/data_exporter.py:187` |
| `_last_snapshot_times` | `src/export/data_exporter.py:198` |

The stored snapshot document shape is at `src/db/arango_writer.py:4342-4353`.
It holds `entity_type`, `entity_id`, `timestamp`, `config_hash`, `config_body`,
and `trigger`. A capture document must not reuse this shape.

---

## 4. The Redis writer

### 4.1 The two writer classes

| Class | Location | Purpose |
| --- | --- | --- |
| `RedisTimeSeriesWriter` | `src/db/redis_writer.py:90` | Numeric metrics into Redis TimeSeries |
| `RedisJSONWriter` | `src/db/redis_writer.py:530` | Full API responses into Redis JSON |

Both connect with `decode_responses=True`, so keys and values are `str`
(`src/db/redis_writer.py:108`, `src/db/redis_writer.py:546`).

`RedisTimeSeriesWriter` requires the `timeseries` module
(`src/db/redis_writer.py:122`). `RedisJSONWriter` accepts the module name
`rejson` or `redisjson` (`src/db/redis_writer.py:551-555`). Both fail fast when
the module is missing.

Both share a DNS pre-flight that raises `ConnectionError` on an unresolvable
host (`src/db/redis_writer.py:114-120`, reused at
`src/db/redis_writer.py:541`).

### 4.2 The key naming convention

**Redis JSON keys.**

```python
617    @staticmethod
618    def _build_key(  # WHY: deterministic composite key so re-writes overwrite the same record.
619        endpoint: str,
620        record: dict[str, Any],
621        pk_fields: list[str],
622    ) -> str:
623        """Build Redis key from endpoint name and PK field values."""
624        parts = [endpoint]  # WHY: endpoint anchors the namespace so different APIs never collide.
625        for field in pk_fields:  # WHY: append each PK component in strategy-defined order.
626            parts.append(str(record.get(field, "unknown")))  # WHY: unknown sentinel keeps key length stable.
627        return ":".join(parts)  # WHY: colon-delimited keys align with Redis convention.
```

Source: `src/db/redis_writer.py:617-627`.

The shape is `{endpoint}:{pk_1}:{pk_2}:...`. A missing field becomes the literal
`unknown`.

**Redis TimeSeries keys.**

```python
ts_key = f"{ctx.api_function_name}:{entity_id}:{field_name}"
```

Source: `src/db/redis_writer.py:208`.

Compaction keys append `:avg_1h` and `:avg_1d`
(`src/db/redis_writer.py:305-306`). The retention manager matches
`"*.avg_1h"` (`src/db/retention.py:25`).

### 4.3 Expiry

**Redis JSON sets an expiry on every key.**

```python
597            pipe.json().set(key, "$", record)  # WHY: overwrite entire document at root path.
598            pipe.expire(key, REDIS_JSON_TTL_SECONDS)  # WHY: apply TTL so old docs are pruned by Redis.
```

Source: `src/db/redis_writer.py:597-598`.

```python
REDIS_JSON_TTL_SECONDS = int(os.environ.get("REDIS_JSON_TTL_DAYS", "7")) * 86_400
```

Source: `src/db/redis_writer.py:33`. The default is 7 days. The class docstring
confirms the intent and names ArangoDB as the long-term archive
(`src/db/redis_writer.py:531-536`).

**Warning.** A capture stored through `RedisJSONWriter` disappears after 7 days.
Feature 1823 must let a user read a capture months later. Store captures in
ArangoDB. Never route a capture through a `composite_pk` strategy.

**Redis TimeSeries uses retention, not expiry.**

| Constant | Value | Source |
| --- | --- | --- |
| `RAW_RETENTION_MS` | `REDIS_RAW_RETENTION_DAYS` days, default 7 | `src/db/redis_writer.py:28-30` |
| `HOURLY_RETENTION_MS` | 90 days | `src/db/redis_writer.py:31` |
| `DAILY_RETENTION_MS` | 365 days | `src/db/redis_writer.py:32` |

Batch sizes: `JSON_PIPELINE_BATCH = 500` (`src/db/redis_writer.py:34`),
`KEY_CREATION_BATCH = 500` (`src/db/redis_writer.py:37`),
`ADD_PIPELINE_BATCH = 10_000` (`src/db/redis_writer.py:38`).

### 4.4 Key namespaces for users and sites

**No user namespace exists. No site namespace exists.**

Every key begins with the API function name
(`src/db/redis_writer.py:624`, `src/db/redis_writer.py:208`). A site
identifier appears only when `site_id` happens to be a primary-key field for
that endpoint. An actor identity never appears.

A new prefix such as `misthelper:lock:` therefore cannot collide with any key
the writers produce today.

### 4.5 Other Redis use in the source tree

A repository search for `import redis`, `from redis`, `redis.Redis`, and
`Redis(` inside `src/` returns exactly two files: `src/db/router.py` and
`src/db/redis_writer.py`.

Broader mentions resolve as follows.

| Location | Use |
| --- | --- |
| `src/db/retention.py:118-132` | Counts compacted TimeSeries keys. Read-only validation |
| `web_portal/routes/webhooks.py:87-89` | Reaches the router's private `_redis_writer` to ingest webhook stats |
| `src/db/__init__.py:46-48`, `src/db/__init__.py:62-63`, `src/db/__init__.py:74` | Connection settings by variable name |

**Confirmed.** Redis holds no cache, no session store, and no queue today. The
distributed lock introduces the first non-data use of Redis.

---

## 5. The lock design — INFERENCE

No lock primitive exists in the repository today. This section proposes one.

### 5.1 Requirements restated

1. Hold a work email and a browser identity together.
2. Expire after a 5 minute cooldown when a session is abandoned.
3. Allow the same email in several browser tabs on several sites at once.
4. Let any user read state without holding the lock.

### 5.2 The key format

```
misthelper:lock:site:{org_id}:{site_id}
```

One key per site. Requirement 3 falls out of the key shape. The same email
holds `...:site:orgA:site1` and `...:site:orgA:site2` at the same time, because
the two keys differ.

The `misthelper:lock:` prefix is new. Section 4.4 confirms it cannot collide.

Use a plain Redis string key. Do **not** use `RedisJSONWriter`. That writer
would apply the 7 day JSON expiry (`src/db/redis_writer.py:598`) instead of the
5 minute cooldown. Open a direct `redis.Redis` client with the same constructor
arguments the writers use (`src/db/redis_writer.py:542-547`).

### 5.3 The stored value shape

The value is one JSON string.

```jsonc
{
  "lock_version": 1,          // Bump on any shape change.
  "lock_token": "6f1c...",    // uuid4 hex. Stable while one session holds the lock.
  "actor_email": "jane.doe@example.com",
  "browser_id": "b7f3c9a1...", // Stable per browser. Shared by every tab.
  "run_id": "run_2026-08-19T14-02-11Z_a1b2c3",
  "org_id": "...",
  "site_id": "...",
  "stage": "capture_1",       // Where the run stands. Shown to a waiting user.
  "acquired_at": 1755612131,  // Epoch seconds.
  "renewed_at": 1755612311    // Epoch seconds. Updated by each heartbeat.
}
```

The owner identity is the pair `actor_email` plus `browser_id`. Requirement 1
is met. `browser_id` is a random value the portal writes once into a
first-party cookie. Every tab of that browser reads the same value, so tabs of
one browser share one owner identity.

`lock_token` is the fence. Refresh and release compare on `lock_token` only,
because `renewed_at` and `stage` change while the lock is held.

### 5.4 Expiry handling

| Constant | Value | Purpose |
| --- | --- | --- |
| `LOCK_TTL_SECONDS` | `300` | The 5 minute cooldown |
| `LOCK_HEARTBEAT_SECONDS` | `60` | Refresh cadence from an open tab |

An open tab sends a heartbeat every 60 seconds. Each heartbeat resets the TTL
to 300 seconds. If the browser closes or the user walks away, five heartbeats
are missed and Redis removes the key. The site frees itself. No sweeper thread
is needed.

### 5.5 The atomic operation used to take the lock

```
SET misthelper:lock:site:{org_id}:{site_id} <json> NX EX 300
```

`NX` makes the write conditional on the key being absent. `EX 300` sets the
cooldown in the same command. Redis executes `SET` atomically, so two
administrators who click at the same moment cannot both win. The redis-py call
returns a truthy value to the winner and `None` to the loser.

Refresh must not use a bare `EXPIRE`. A bare `EXPIRE` would let a stale tab
extend a lock another user now holds. Use a compare-and-refresh Lua script.
Redis runs a script atomically.

```lua
-- KEYS[1] = lock key, ARGV[1] = lock_token, ARGV[2] = new json, ARGV[3] = ttl
local raw = redis.call('GET', KEYS[1])
if not raw then return 0 end
if cjson.decode(raw).lock_token ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'XX', 'EX', ARGV[3])
return 1
```

Release uses the same guard with `DEL` in place of `SET`.

### 5.6 Reading state without the lock

```
GET misthelper:lock:site:{org_id}:{site_id}
TTL misthelper:lock:site:{org_id}:{site_id}
```

Both commands are read-only. Any user may call the read endpoint. `TTL`
returns the seconds left. `TTL` returns `-2` when the key is gone. Requirement 4
is met.

Run state and capture documents live in ArangoDB, not in the lock. Any user
reads the full history with no lock at all. The lock guards only the act of
driving a site.

### 5.7 Takeover after the cooldown, with CONFIRM

1. User B opens the site. The portal runs `SET ... NX EX 300`. Redis refuses.
2. The portal runs `GET` and `TTL`.
3. The portal shows: `Site locked by jane.doe@example.com at stage capture_1.
   The lock frees in 214 seconds.` The portal offers no takeover yet.
4. The portal polls `TTL`. When `TTL` returns `-2`, the cooldown is over.
5. The portal shows the takeover prompt and states the consequence:
   `Warning: takeover ends the run for jane.doe@example.com. Unsaved progress
   for that run is lost. Type CONFIRM to take over.`
6. User B types `CONFIRM`. Any other text cancels.
7. The portal runs `SET ... NX EX 300` with User B's identity. User B wins.
8. The portal appends a takeover row to the run audit record in ArangoDB. The
   row names both emails and the time.

The portal never lets a user break a live lock. Takeover happens only after the
cooldown runs out.

### 5.8 Resume with continue

1. User A returns.
2. The portal reads the run document from ArangoDB by `run_id`. The run is still
   open.
3. The portal runs `GET` on the lock key.
4. If the key is absent, the portal shows: `Run run_2026-... is open at stage
   capture_1. Type continue to resume.`
5. User A types `continue`. The portal runs `SET ... NX EX 300` with a new
   `lock_token`, then reloads the run state from ArangoDB.
6. If the key exists and holds User B's identity, the portal refuses. It shows
   the new owner and offers a read-only view.
7. If the key exists and holds User A's own `actor_email` and `browser_id`, the
   portal reattaches to the same lock and starts the heartbeat again. This is
   the second-tab case.

### 5.9 Failure mode to plan for

Redis is not durable by default. If Redis restarts, every lock disappears. Two
administrators can then drive one site. Mitigate by writing the current owner
into the ArangoDB run document on every lock take. On resume, compare the lock
holder against the run document owner and warn on a mismatch.

---

## 6. Primary key strategies

### 6.1 The catalog

`ENDPOINT_PRIMARY_KEY_STRATEGIES` is a bare module-level dict
(`src/refactors/endpoint_primary_key_strategies.py:32`). It ends at the last
line of the file. Each value carries `type`, `primary_key`, `indexes`,
`unique_constraints`, and `description`
(`src/refactors/endpoint_primary_key_strategies.py:21-27`).

The dict holds **363 entries**. That count is 362 API endpoints plus one
`"default"` entry.

### 6.2 The strategy names and their counts

| Strategy type | Entries | Routes to |
| --- | --- | --- |
| `auto_increment_with_unique` | 126 (includes `"default"`) | ArangoDB only (`src/db/router.py:22`) |
| `composite_pk` | 120 | Redis JSON plus ArangoDB (`src/db/router.py:23`) |
| `natural_pk` | 111 | ArangoDB only (`src/db/router.py:22`) |
| `timeseries_pk` | 6 | Redis TimeSeries (`src/db/router.py:24`) |

Counts come from a match on `"type": "<name>"` across the file. The docstring
example at `src/refactors/endpoint_primary_key_strategies.py:22` is excluded.

The six `timeseries_pk` endpoints are `listOrgDevicesStats`,
`listSiteDevicesStats`, `listSiteWirelessClientsStats`, `searchOrgSwOrGwPorts`,
`searchSiteSwOrGwPorts`, and `searchOrgPeerPathStats`.

**Note.** The module docstring at
`src/refactors/endpoint_primary_key_strategies.py:22` lists `"auto_pk"` and
`"time_series"`. Neither name appears in any entry. The docstring is stale.

### 6.3 A default exists for an unknown endpoint

```python
2454    "default": {
2455        "type": "auto_increment_with_unique",
2456        "primary_key": ["misthelper_internal_id"],
2457        "indexes": [],
2458        "unique_constraints": [],
2459        "description": "Fallback strategy with auto-increment primary key and unique constraint on API id",
2460    },
```

Source: `src/refactors/endpoint_primary_key_strategies.py:2452-2460`.

`_resolve_strategy` prefers the per-endpoint entry, then this `"default"` entry,
then the module fallback in the router (`src/db/router.py:281-285`,
`src/db/router.py:50-53`). Both defaults use `auto_increment_with_unique`.

### 6.4 What a new capture collection must declare — INFERENCE

Declare `natural_pk` with `primary_key: ["capture_id"]`.

```python
"upgradeCaptureWrite": {
    "type": "natural_pk",
    "primary_key": ["capture_id"],
    "indexes": ["run_id", "site_id", "org_id", "captured_at", "actor_email"],
    "unique_constraints": [],
    "description": "Upgrade capture document for a single site and capture ordinal",
},
```

Three reasons.

1. **`natural_pk` routes to ArangoDB only** (`src/db/router.py:22`,
   `src/db/router.py:165`). ArangoDB is the durable store. The user must read a
   capture months later.
2. **`natural_pk` makes `_compute_key` reuse the record's own field**
   (`src/db/arango_writer.py:4041`). A re-write of one capture upserts in place.
   `auto_increment_with_unique` mints a fresh `uuid4` on every write
   (`src/db/arango_writer.py:4039-4040`), so a retry would leave two documents
   for one capture.
3. **`composite_pk` is unsafe here.** It routes through `_write_dual`
   (`src/db/router.py:163-164`), which writes Redis JSON with the 7 day expiry
   (`src/db/redis_writer.py:598`). A capture must outlive 7 days.

Do not leave a capture endpoint unregistered. An unregistered name falls back to
`auto_increment_with_unique` and hits problem 2 above.

---

## 7. The exporter

### 7.1 The class

`DataExporter` is the export entry point (`src/export/data_exporter.py:36`).
It holds three class attributes: a shared router, an initialization flag, and a
snapshot throttle map (`src/export/data_exporter.py:43-45`).

### 7.2 The mandated write method

```python
104    @staticmethod
105    def write_with_format_selection(  # Public export entry point.
106        data: list[dict[str, Any]],
107        filename_or_table: str,
108        api_function_name: str | None = None,
109        fieldnames: list[str] | None = None,
110        backend_options: ExportBackendOptions | None = None,
111    ) -> bool:
```

Source: `src/export/data_exporter.py:104-111`.

Every output path must call this method. It runs five steps
(`src/export/data_exporter.py:112-129`):

1. Resolve `ExportBackendOptions`, defaulting when the caller passes none
   (line 113).
2. Read `MistHelper.OUTPUT_FORMAT`, unless `format_override` is set
   (lines 114-115).
3. Validate the inputs (line 123). `_validate_write_inputs` rejects empty data
   and any format other than `csv` or `sqlite`
   (`src/export/data_exporter.py:204-215`).
4. Dispatch to the CSV or SQLite writer (lines 125-127).
5. Mirror to the polyglot layer (line 128), then return the CSV result
   (line 129).

**Warning.** Step 5 discards the polyglot outcome. The return value reflects CSV
only. See section 2.3.

### 7.3 How a bare file name maps to a path under the data directory

```python
266    @staticmethod
267    def _resolve_csv_path(csv_file: str) -> str:
268        """Return the on-disk path for csv_file, placing bare filenames under data/."""
269        data_dir = "data"  # Confine bare filenames to data/ for container persistence
270        os.makedirs(data_dir, exist_ok=True)  # Ensure data/ exists before any write
271        if not os.path.dirname(csv_file):  # Caller passed a bare filename (no directory component)
272            resolved = os.path.join(data_dir, csv_file)  # Place under data/
273        else:
274            resolved = csv_file  # Caller-provided full path is honored verbatim
275        logging.debug("Resolved CSV destination path: %s", resolved)  # Trace path resolution
276        return resolved  # Final destination
```

Source: `src/export/data_exporter.py:266-276`.

The rule is `os.path.dirname`. A name with no directory part lands under
`data/`. A name with any directory part is honored as given. The method creates
`data/` when it is missing (line 270). The path is relative to the process
working directory, not to the repository root.

`write_to_csv` calls the resolver (`src/export/data_exporter.py:257`). Its
signature is:

```python
def write_to_csv(
    data: list[dict[str, Any]],
    csv_file: str,
    fieldnames: list[str] | None = None,
) -> None:
```

Source: `src/export/data_exporter.py:239-244`.

`_write_csv_format` appends `.csv` when the name lacks it
(`src/export/data_exporter.py:224`). `_write_sqlite_format` strips a trailing
`.csv` to build the table name (`src/export/data_exporter.py:232`).

The container mounts the host `./data` directory at `/app/data`
(`compose.yml:17`). A capture written to `data/` survives a container restart.

---

## 8. The capture document schema — INFERENCE

### 8.1 Design goals

1. Carry a schema version from the first write.
2. Identify the organization, the site, the run, the capture ordinal, the tier,
   the actor email, and the time.
3. Hold device state and client lists for tier 2.
4. Hold the extra tier 3 blocks.
5. Make a comparison between two captures cheap.

### 8.2 The proposed document

```jsonc
{
  // ---- Identity -----------------------------------------------------
  "schema_version": 1,          // Readers branch on this first. Bump on any shape change.
  "capture_id": "cap_9f2a4c1e", // Natural key. Declared as primary_key. No "/" and no ":".
  "run_id": "run_2026-08-19T14-02-11Z_a1b2c3",
  "capture_ordinal": 1,         // 1 = capture before the upgrade. 2 = capture after it.
  "tier": 2,                    // 1, 2 or 3. Controls which blocks below are present.

  // ---- Scope --------------------------------------------------------
  "org_id": "8f1c...",
  "site_id": "3b7d...",
  "site_name": "Denver Campus", // Denormalized on purpose. A months-later read needs no join.

  // ---- Actor and time -----------------------------------------------
  "actor_email": "jane.doe@example.com",
  "captured_at": 1755612131,    // Epoch seconds. The sort key for history queries.
  "captured_at_iso": "2026-08-19T14:02:11Z",
  "settle_seconds": 20,         // Settle gate the portal honored before it read the API.

  // ---- Comparison accelerators --------------------------------------
  "digests": {
    "body": "sha256:1f0a...",   // Digest of every block below. Compare this first.
    "devices": "sha256:44be...",
    "clients": "sha256:9c02...",
    "gateway": "sha256:0000...",      // Present only when tier is 3.
    "switch_ports": "sha256:0000...", // Present only when tier is 3.
    "wan": "sha256:0000..."           // Present only when tier is 3.
  },
  "device_index": {             // MAC -> per-device digest. A two-capture diff is a map diff.
    "5c5b350e0001": "sha256:aa11...",
    "5c5b35000301": "sha256:bb22..."
  },
  "counts": {                   // Cheap scalars. A summary screen reads these alone.
    "devices_total": 42,
    "devices_connected": 41,
    "clients_wireless": 380,
    "clients_wired": 96
  },

  // ---- Tier 2 payload -----------------------------------------------
  "devices": [
    {
      "mac": "5c5b350e0001",
      "device_digest": "sha256:aa11...", // Matches device_index. Lets a diff skip the walk.
      "name": "denver-ap-01",
      "model": "AP45",
      "serial": "A123456789",
      "type": "ap",
      "status": "connected",
      "version": "0.14.29511",
      "uptime": 864321,
      "ip": "10.20.30.41",
      "last_seen": 1755612120
    }
  ],
  "clients": {
    "wireless": [
      { "mac": "aabbccddeeff", "ap_mac": "5c5b350e0001", "ssid": "Corp",
        "band": "5", "rssi": -58, "vlan_id": 30 }
    ],
    "wired": [
      { "mac": "112233445566", "switch_mac": "5c5b35000301",
        "port_id": "ge-0/0/12", "vlan_id": 30 }
    ]
  },

  // ---- Tier 3 payload. Absent when tier is 1 or 2. -------------------
  "gateway": {
    "mac": "5c5b35009901",
    "ha_state": "primary",
    "cluster_peer_mac": "5c5b35009902",
    "tunnels_up": 4,
    "bgp_peers_established": 2
  },
  "switch_ports": [
    { "switch_mac": "5c5b35000301", "port_id": "ge-0/0/12",
      "up": true, "speed": 1000, "poe_draw_w": 14.2, "neighbor_mac": "5c5b350e0001" }
  ],
  "wan": {
    "uplinks": [ { "name": "wan0", "up": true, "latency_ms": 12, "loss_pct": 0.0 } ]
  },

  // ---- Provenance and completeness ----------------------------------
  "source_apis": ["listSiteDevices", "listSiteDevicesStats", "listSiteWirelessClientsStats"],
  "capture_status": "complete", // complete | partial | failed.
  "partial_reasons": []         // Filled when capture_status is "partial".

  // The ArangoDB writer stamps _key, _misthelper_updated_at, and
  // _misthelper_deleted_at. See src/db/arango_writer.py:4025-4034.
  // The feature must not set those three fields.
}
```

### 8.3 Why the comparison is cheap

The digests turn a deep comparison into a shallow one.

1. Compare `digests.body` on both captures. If the two match, nothing changed.
   The comparison costs one string equality test.
2. If they differ, compare each entry in `digests`. Walk only the blocks whose
   digests differ.
3. For the devices block, diff the two `device_index` maps. Three sets fall out
   at once: keys only in capture 1 (devices lost), keys only in capture 2
   (devices gained), and keys in both with different digests (devices changed).
   The cost is linear in the device count with no nested walk.
4. Walk the full device record only for the changed set.

Compute the digests with the router helper style at `src/db/router.py:82-85`,
which uses `json.dumps(payload, sort_keys=True, default=str)` then sha256. The
`default=str` argument matters. Mist payloads carry values that plain
`json.dumps` rejects. The ArangoDB variant at
`src/db/arango_writer.py:4319-4322` omits `default=str`, so it can raise.

### 8.4 Companion collections

| Collection | Strategy | Primary key |
| --- | --- | --- |
| `upgrade_captures` | `natural_pk` | `capture_id` |
| `upgrade_runs` | `natural_pk` | `run_id` |

One edge collection links them. Follow the existing PascalCase verb-phrase
convention seen at `src/db/arango_writer.py:291` and
`src/db/arango_writer.py:4225`:

```
CaptureForRun   from upgrade_captures  to upgrade_runs
```

Build the edge key with the existing deterministic helper pattern at
`src/db/arango_writer.py:4248-4253`.

### 8.5 Schema version rules

- Write `schema_version: 1` from the first capture. Never omit it.
- Bump the version on any field rename, any field removal, or any change to a
  digest input.
- A reader must branch on `schema_version` before it touches any other field.
- Index `schema_version` so a migration sweep can find old documents. See
  section 9.

---

## 9. Retention and history

### 9.1 How a user finds a run from months ago — INFERENCE

Offer three lookup paths.

1. **By site and date range.** The most common request. Filter `site_id`, filter
   `captured_at` between two epoch seconds, sort `captured_at` descending.
2. **By run identifier.** Show the `run_id` on screen after every run and place
   it in the notification email. A direct `run_id` lookup is one index hit.
3. **By actor email.** Answers "which sites did I upgrade last quarter".

Denormalize `site_name` into the capture document (section 8.2). A months-later
reader then needs no join, even if the site was renamed since.

### 9.2 The indexes ArangoDB needs — INFERENCE

On `upgrade_captures`:

| Index name | Type | Fields | Serves |
| --- | --- | --- | --- |
| `idx_capture_run_ordinal` | persistent, unique | `run_id`, `capture_ordinal` | The compare screen. Also enforces at most two captures per run |
| `idx_capture_site_time` | persistent | `site_id`, `captured_at` | Site history, newest first |
| `idx_capture_org_time` | persistent | `org_id`, `captured_at` | Organization history |
| `idx_capture_actor_time` | persistent | `actor_email`, `captured_at` | Per-user history |
| `idx_capture_schema_version` | persistent | `schema_version` | Migration sweeps |

On `upgrade_runs`:

| Index name | Type | Fields | Serves |
| --- | --- | --- | --- |
| `idx_run_site_time` | persistent | `site_id`, `started_at` | Site run list |
| `idx_run_org_time` | persistent | `org_id`, `started_at` | Organization run list |
| `idx_run_status_time` | persistent | `status`, `started_at` | Finds open and abandoned runs |

**Do not add a TTL index to either collection.** A TTL index deletes the exact
document the user must read months later.

`_ensure_collection` creates a collection but creates no index
(`src/db/arango_writer.py:3957-3963`). The feature must create these indexes
itself, once, at startup. Make the call idempotent. ArangoDB accepts a repeat
index creation with the same definition.

### 9.3 What the retention manager does today

`RetentionManager` sweeps every 6 hours by default
(`src/db/retention.py:19`, `src/db/retention.py:158-167`). It purges when the
database exceeds 90 percent of a 100 GB ceiling
(`src/db/retention.py:18`, `src/db/retention.py:21`,
`src/db/retention.py:87-96`). Both numbers are overridable by the variables
`ARANGO_MAX_STORAGE_GB` and `RETENTION_CHECK_INTERVAL_HOURS`
(`src/db/retention.py:27-28`).

The purge query names one collection only.

```
FOR snapshot IN config_snapshots ... REMOVE doc IN config_snapshots
```

Source: `src/db/retention.py:40-54`.

**A new `upgrade_captures` collection is safe from this purge.** The query never
names it.

Two cautions.

1. The purge trigger reads the whole-database size
   (`src/db/retention.py:87-96`). Growing captures raise that number and can
   trigger a purge of unrelated `config_snapshots` rows.
2. **Latent defect, unrelated to feature 1823.** `_get_storage_usage_gb` reads
   `getattr(self._arango, "_database", None)` (`src/db/retention.py:100`).
   `ArangoDBWriter` names its handle `self._db`
   (`src/db/arango_writer.py:3903`). No `_database` attribute exists. The
   `getattr` returns `None`, so usage is always `0.0`
   (`src/db/retention.py:101-102`) and the purge never runs. The same mismatch
   makes `_purge_oldest_snapshots` return 0
   (`src/db/retention.py:111-116`). Record this. Do not fix it in this feature.

### 9.4 Capture size control — INFERENCE

A tier 3 capture of a large site can grow past a comfortable document size.
Recommend two guards.

1. Store the tier 3 blocks only when tier 3 runs. Omit the keys otherwise.
2. Set a document size ceiling. If a capture exceeds it, store the heavy blocks
   in a companion `upgrade_capture_bodies` collection and keep a `body_ref` in
   the main document. The digests and `device_index` stay in the main document,
   so a comparison never has to load a body.

---

## 10. Compose services

Source file: `compose.yml` at the repository root. A second, unrelated compose
file exists at `mist-ops-platform/deploy/compose.yml`.

### 10.1 The ArangoDB service

```yaml
66  arangodb:
67    image: docker.io/arangodb/arangodb:3.12
68    container_name: arangodb
69    ports:
70      - "8529:8529"
71    volumes:
72      - arangodb-data:/var/lib/arangodb3
```

Source: `compose.yml:66-72`.

The image is ArangoDB 3.12 (`compose.yml:67`). The container name is `arangodb`
(`compose.yml:68`). Data persists in the named volume `arangodb-data`
(`compose.yml:72`, `compose.yml:153-154`).

The root password comes from the variable `ARANGO_ROOT_PASSWORD`
(`compose.yml:80`). A comment at `compose.yml:74-79` warns that ArangoDB reads
that variable on first boot only. To change it, the operator must remove the
container and the volume.

**Health check** (`compose.yml:84-89`):

| Setting | Value |
| --- | --- |
| Test | `arangosh` with the password variable, running `print(1)` |
| Interval | 10s |
| Timeout | 10s |
| Retries | 5 |
| Start period | 20s |

### 10.2 The Redis service

```yaml
91  redis-stack:
92    image: docker.io/redis/redis-stack:latest
93    container_name: redis-stack
94    ports:
95      - "6379:6379"
96      # RedisInsight web UI for browsing data
97      - "8001:8001"
98    volumes:
99      - redis-data:/data
```

Source: `compose.yml:91-99`.

The image is `redis/redis-stack:latest` (`compose.yml:92`). Redis Stack ships
both the TimeSeries module and the JSON module, which the writers require
(`src/db/redis_writer.py:122`, `src/db/redis_writer.py:551-555`).

The password comes from the variable `REDIS_PASSWORD`, passed through
`REDIS_ARGS` (`compose.yml:101`). Data persists in the named volume
`redis-data` (`compose.yml:99`, `compose.yml:155-156`).

**Health check** (`compose.yml:105-110`):

| Setting | Value |
| --- | --- |
| Test | `redis-cli` with the password variable, running `ping` |
| Interval | 10s |
| Timeout | 5s |
| Retries | 5 |
| Start period | 10s |

### 10.3 Ports the new feature can rely on

| Service | In-container host name | Port | Host port | Source |
| --- | --- | --- | --- | --- |
| ArangoDB | `arangodb` | 8529 | 8529 | `compose.yml:28`, `compose.yml:68-70` |
| Redis Stack | `redis-stack` | 6379 | 6379 | `compose.yml:29-30`, `compose.yml:93-95` |
| RedisInsight | `redis-stack` | 8001 | 8001 | `compose.yml:97` |
| Web portal | `misthelper` | 8055 | 8055 | `compose.yml:13`, `compose.yml:26` |
| SSH | `misthelper` | 2200 | 2200 | `compose.yml:11` |
| Ollama | `ollama-misthelper` | 11434 | 11434 | `compose.yml:116` |

All services share the bridge network `misthelper-network`
(`compose.yml:146-148`). Compose DNS resolves the service names inside that
network.

The application container defaults match. `ARANGO_HOST` is set to
`http://arangodb:8529`, `REDIS_HOST` to `redis-stack`, and `REDIS_PORT` to
`6379` (`compose.yml:28-30`). The same three defaults appear in code at
`src/db/__init__.py:42`, `src/db/__init__.py:46`, and `src/db/__init__.py:47`.

**Confirmed.** The feature can rely on `arangodb:8529` and `redis-stack:6379`
inside the compose network, and on `localhost:8529` and `localhost:6379` from
the host.

### 10.4 Startup ordering

The application container waits for both databases to report healthy.

```yaml
34    depends_on:
35      arangodb:
36        condition: service_healthy
37      redis-stack:
38        condition: service_healthy
```

Source: `compose.yml:34-38`.

This ordering guarantee holds only under compose. It does not hold when a
developer runs the portal on a host. That is the case section 2 describes.

### 10.5 Two smaller notes

1. The `misthelper` service declares no health check. A comment at
   `compose.yml:59-64` refers to a Docker variant that adds one.
2. The file opens with `version: '3.8'` (`compose.yml:1`). Modern Compose
   ignores that key.

---

## 11. Action list for feature 1823

| # | Action | Reason |
| --- | --- | --- |
| 1 | Fix issue #1824 before trusting the router | Two silent-success paths (`src/db/router.py:152-158`, `src/db/router.py:372-382`) plus a container-only standalone test (`src/export/data_exporter.py:141`) |
| 2 | Declare `natural_pk` with `primary_key: ["capture_id"]` | Routes to ArangoDB only. Upserts in place. See section 6.4 |
| 3 | Never route a capture through `composite_pk` | Redis JSON expires keys after 7 days (`src/db/redis_writer.py:598`) |
| 4 | Use the term "capture", never "snapshot" | The repository already owns "snapshot". See the table in section 3.9 |
| 5 | Use a direct `redis.Redis` client for the lock | `RedisJSONWriter` would apply the 7 day expiry, not the 5 minute cooldown |
| 6 | Take the lock with `SET ... NX EX 300` | One atomic command. See section 5.5 |
| 7 | Refresh and release with a Lua `lock_token` guard | A bare `EXPIRE` lets a stale tab extend another user's lock |
| 8 | Create the eight indexes yourself at startup | `_ensure_collection` creates no index (`src/db/arango_writer.py:3957-3963`) |
| 9 | Add no TTL index to the capture collections | The user must read a capture months later |
| 10 | Do not set `_key`, `_misthelper_updated_at`, or `_misthelper_deleted_at` | `_prepare_document` stamps all three (`src/db/arango_writer.py:4025-4034`) |
