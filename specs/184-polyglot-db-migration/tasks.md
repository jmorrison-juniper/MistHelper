# Tasks: Polyglot Database Migration

**Input**: Design documents from `/specs/184-polyglot-db-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/database-router.md, quickstart.md

**Tests**: Included — plan.md defines test files (tests/unit/test_router.py, test_arango_writer.py, test_redis_writer.py, tests/integration/test_compose_deploy.py) and CI requires >=70% coverage.

**Organization**: Tasks are grouped by user story. Implementation order differs from priority labels due to dependencies: US2 and US3 (backend writers) must exist before US4 (routing), and US4 must exist before US1 (end-to-end integration) can be validated.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Exact file paths included in every task description

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create package structure and declare new dependencies

- [ ] T001 Create `src/db/` package directory with empty `src/db/__init__.py`
- [ ] T002 [P] Add `python-arango>=8.3.2`, `redis[hiredis]>=7.4.0`, `structlog` to `requirements.txt` and `pyproject.toml` dependencies
- [ ] T003 [P] Add database environment variables (`ARANGO_ROOT_PASSWORD`, `REDIS_PASSWORD`, `ARANGO_HOST`, `REDIS_HOST`, `REDIS_PORT`, retention vars, `MISTHELPER_STANDALONE`) to `deploy/.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types, container services, and router skeleton that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `DatabaseConfig` dataclass (from_env class method, 8 fields per contract) and `WriteResult` dataclass (5 fields) in `src/db/__init__.py`
- [ ] T005 [P] Configure `structlog` logging for `src/db/` modules: JSON output, ASCII-only, stdlib integration, bound loggers per class in `src/db/__init__.py`
- [ ] T006 [P] Add `arangodb` service to `compose.yml` — image `arangodb:3.12`, port `8529`, volume `arangodb-data:/var/lib/arangodb3`, health check `curl -f http://localhost:8529/_api/version`, env `ARANGO_ROOT_PASSWORD`
- [ ] T007 [P] Add `redis-stack` service to `compose.yml` — image `redis/redis-stack-server:latest`, port `6379`, volume `redis-data:/data`, health check `redis-cli -a ${REDIS_PASSWORD} ping`, env `REDIS_ARGS="--requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru"`
- [ ] T008 Implement `DatabaseRouter` skeleton in `src/db/router.py` — `__init__(config)` with connection attempts and availability flags, `health_check()` returning backend status dict, `close()` for graceful shutdown (leave `write()` as stub for US4)

**Checkpoint**: Package exists, types defined, compose services configured, router skeleton ready — user story implementation can begin

---

## Phase 3: User Story 2 — Natural Key Entities in ArangoDB (Priority: P1)

**Goal**: All configuration and inventory data (sites, devices, templates, WLANs, PSKs) stored as ArangoDB documents with graph edges representing relationships

**Independent Test**: Run Menu 12 (org inventory), then query ArangoDB to verify device documents exist with correct fields and Mist API UUID as `_key`

### Tests for User Story 2

- [ ] T009 [P] [US2] Write unit tests for `ArangoDBWriter` in `tests/unit/test_arango_writer.py` — mock `python-arango` client; test upsert with overwrite, collection auto-creation, `_key` from natural PK, `_misthelper_updated_at` timestamp, graph edge creation, soft-delete marking

### Implementation for User Story 2

- [ ] T010 [US2] Implement `ArangoDBWriter.__init__()` in `src/db/arango_writer.py` — connect using `ArangoClient`, authenticate, ensure `misthelper` database exists, bind structured logger
- [ ] T011 [US2] Implement `ArangoDBWriter.write()` in `src/db/arango_writer.py` — auto-create collection on first write, upsert via `collection.insert(doc, overwrite=True, overwrite_mode="replace")`, set `_key` from strategy `primary_key[0]`, add `_misthelper_updated_at` epoch, handle `auto_increment_with_unique` with auto-generated keys
- [ ] T012 [US2] Implement graph creation and edge management in `ArangoDBWriter` in `src/db/arango_writer.py` — create `mist_network_topology` graph with vertex collections (orgs, sites, devices, templates, ports) and 4 edge definitions (`OrgContainsSite`, `SiteContainsDevice`, `TemplateAssignedToSite`, `DeviceHasPort`); insert edges during write when relationship fields detected
- [ ] T013 [US2] Implement soft-delete logic in `ArangoDBWriter` in `src/db/arango_writer.py` — set `_misthelper_deleted_at` epoch when entity absent from API pull, clear on re-appearance, lifecycle: Active → Soft-Deleted → Purged (by retention)

**Checkpoint**: ArangoDB writer can upsert documents with natural keys, create graph edges, and handle soft-deletes — testable independently via direct `ArangoDBWriter` calls

---

## Phase 4: User Story 3 — Time-Series Metrics in Redis TimeSeries (Priority: P1)

**Goal**: All statistical and performance data (device stats, port stats, SLE metrics, client counts) stored as Redis TimeSeries keys with labels and automatic downsampling

**Independent Test**: Run Menu 13 (org device stats), then query Redis to verify time-series keys exist with correct labels and data points

**Note**: Phase 4 can proceed in parallel with Phase 3 (different files, no shared dependencies)

### Tests for User Story 3

- [ ] T014 [P] [US3] Write unit tests for `RedisTimeSeriesWriter` in `tests/unit/test_redis_writer.py` — mock `redis` client; test TS.CREATE with labels and retention, TS.ADD with pipeline batching, compaction rule creation, key naming convention, numeric value extraction from flattened records

### Implementation for User Story 3

- [ ] T015 [US3] Implement `RedisTimeSeriesWriter.__init__()` in `src/db/redis_writer.py` — connect using `redis.Redis`, verify TimeSeries module available via `module_list()`, bind structured logger
- [ ] T016 [US3] Implement `RedisTimeSeriesWriter.write()` in `src/db/redis_writer.py` — extract numeric values from flattened records, create TS key per metric (`{api_function_name}:{entity_id}:{field_name}`), apply labels (org_id, site_id, device_id, metric_name, metric_category), use `TS.ADD` with auto-timestamp, batch via pipeline
- [ ] T017 [US3] Implement automatic compaction rules in `RedisTimeSeriesWriter` in `src/db/redis_writer.py` — on first key creation, add `TS.CREATERULE` for hourly avg (`:avg_1h`, 90d retention) and daily avg (`:avg_1d`, 365d retention); raw key retention from `REDIS_RAW_RETENTION_DAYS` (default 7d); track created keys to avoid duplicate rules

**Checkpoint**: Redis TimeSeries writer can store metrics with labels, append data points, and auto-create downsampling compaction rules — testable independently

---

## Phase 5: User Story 4 — Automatic Data Routing by Endpoint Type (Priority: P2)

**Goal**: `DatabaseRouter.write()` automatically routes data to ArangoDB or Redis based on `ENDPOINT_PRIMARY_KEY_STRATEGIES` type field — no per-endpoint code changes needed for new operations

**Independent Test**: Add a test endpoint to `ENDPOINT_PRIMARY_KEY_STRATEGIES` with type `natural_pk` and verify it routes to ArangoDB without additional code

### Tests for User Story 4

- [ ] T018 [P] [US4] Write unit tests for `DatabaseRouter.write()` routing logic in `tests/unit/test_router.py` — test `natural_pk` → ArangoDB, `composite_pk` → Redis, `auto_increment_with_unique` → ArangoDB, unknown `api_function_name` → skip with Debug log, both backends down → CSV-only with Error log, single backend down → degraded mode

### Implementation for User Story 4

- [ ] T019 [US4] Implement `DatabaseRouter.write()` routing logic in `src/db/router.py` — look up `api_function_name` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, route `natural_pk`/`auto_increment_with_unique` to `ArangoDBWriter.write()`, route `composite_pk` to `RedisTimeSeriesWriter.write()`, return `WriteResult` with success/failure status
- [ ] T020 [US4] Implement degraded mode handling in `DatabaseRouter.write()` in `src/db/router.py` — if target backend unavailable, log warning and return `WriteResult(success=False, backend="csv_only")`; if both backends down, log error; auto-detect recovery when backend becomes available again (reconnect on next write attempt)

**Checkpoint**: Router correctly dispatches data to backends by strategy type; degraded mode gracefully falls back — testable with mock writers

---

## Phase 6: User Story 1 — Container Deployment with Multi-DB Backend (Priority: P1) — MVP

**Goal**: `podman-compose up` starts MistHelper, ArangoDB, and Redis; any data extraction menu operation persists data to the correct backend AND produces CSV output identically to current behavior

**Independent Test**: Deploy using `podman-compose up` and run Menu 11 (org sites export). Verify data is stored in ArangoDB (not SQLite) and CSV output still works identically.

### Tests for User Story 1

- [ ] T021 [P] [US1] Write integration test for container deployment in `tests/integration/test_compose_deploy.py` — verify all 3 services start healthy within 60s, verify MistHelper can reach ArangoDB and Redis, verify health_check endpoint returns all green, verify CSV output unchanged

### Implementation for User Story 1

- [ ] T022 [US1] Add `DatabaseRouter` initialization in `DataExporter.__init__()` in `MistHelper.py` (line ~9401) — create `DatabaseConfig.from_env()`, instantiate `DatabaseRouter`, handle init failure gracefully (log warning, set router to None)
- [ ] T023 [US1] Modify `DataExporter.write_with_format_selection()` in `MistHelper.py` (line ~9410) — after existing CSV write, if `api_function_name` provided and router available: call `self.router.write(data, api_function_name)`, log `WriteResult` at Info level, never raise to caller
- [ ] T024 [US1] Add `depends_on` with `condition: service_healthy` for both `arangodb` and `redis-stack` on the `misthelper` service in `compose.yml`
- [ ] T025 [US1] Import `src.db` package in `MistHelper.py` — add conditional import with `ImportError` fallback for standalone mode (no python-arango/redis installed)

**Checkpoint**: MVP complete — full end-to-end data flow from menu operation through router to backends with CSV always produced. Deploy and validate with `podman-compose up`

---

## Phase 7: User Story 5 — Config Snapshot on Change with Periodic Fallback (Priority: P2)

**Goal**: Configuration snapshots captured whenever a change is detected and periodically during idle periods, stored as versioned documents in ArangoDB with hash-based deduplication

**Independent Test**: Modify a WLAN configuration, then verify a new snapshot document appears in ArangoDB `config_snapshots` collection with timestamp, config hash, and diff from previous version

### Implementation for User Story 5

- [ ] T026 [US5] Implement `ArangoDBWriter.snapshot()` in `src/db/arango_writer.py` — compute SHA-256 hash of sorted JSON config body, query latest snapshot for entity, skip if hash matches, store in `config_snapshots` collection with entity_type, entity_id, timestamp, config_hash, config_body, trigger field
- [ ] T027 [US5] Implement on-change snapshot detection in `DatabaseRouter.write()` in `src/db/router.py` — for config entity types (sites, wlans, templates, networks, services), call `ArangoDBWriter.snapshot()` after successful document upsert, set trigger="api_pull"
- [ ] T028 [US5] Add periodic snapshot check to `DataExporter` in `MistHelper.py` — track last snapshot time per entity type, poll current config when idle period exceeds configurable threshold, snapshot if changed, set trigger="periodic"

**Checkpoint**: Config snapshots are captured on API data pulls and periodically — dedup prevents duplicate snapshots

---

## Phase 8: User Story 6 — Storage-Aware Retention with Oldest-First Rollover (Priority: P3)

**Goal**: Automatic data retention management that uses all available storage and rolls over oldest data first, no manual cleanup needed

**Independent Test**: Configure small storage limit, ingest enough data to exceed it, verify oldest records removed while newest preserved

### Implementation for User Story 6

- [ ] T029 [US6] Implement `RetentionManager.__init__()` in `src/db/retention.py` — accept ArangoDBWriter and RedisTimeSeriesWriter references, load retention config from env (thresholds, intervals), bind structured logger
- [ ] T030 [US6] Implement ArangoDB retention in `RetentionManager` in `src/db/retention.py` — check `ARANGO_MAX_STORAGE_GB` threshold, purge oldest soft-deleted entities first, then oldest snapshot versions, always preserve at least one snapshot per entity (SC-006)
- [ ] T031 [US6] Implement Redis retention validation in `RetentionManager` in `src/db/retention.py` — verify compaction rules exist on all TS keys, validate per-tier retention (raw 7d, hourly 90d, daily 365d), trim keys exceeding retention via `TS.DEL`
- [ ] T032 [US6] Add periodic retention sweep timer in `RetentionManager` in `src/db/retention.py` — configurable interval from `RETENTION_CHECK_INTERVAL_HOURS` (default 6h), run in background thread, log sweep results at Info level

**Checkpoint**: Storage is self-managing — oldest data purged automatically when thresholds reached

---

## Phase 9: User Story 7 — Standalone Mode Backward Compatibility (Priority: P3)

**Goal**: MistHelper running directly on a host (not in a container) continues working with CSV-only output — no errors, no DB connection attempts

**Independent Test**: Run `python MistHelper.py --menu 11` on a host without ArangoDB or Redis installed. Verify CSV output produced and no errors thrown.

### Implementation for User Story 7

- [ ] T033 [US7] Implement standalone mode detection in `DatabaseRouter.__init__()` in `src/db/router.py` — check `MISTHELPER_STANDALONE` env var and `is_running_in_container()` function; if standalone, set `config.standalone_mode = True`, skip all connection attempts, log at Info "Running in standalone mode — CSV-only output"
- [ ] T034 [US7] Verify conditional import path in `MistHelper.py` — when `python-arango` or `redis` not installed (standalone host), `ImportError` fallback sets `DatabaseRouter` to `None`, DataExporter skips routing silently
- [ ] T035 [US7] Validate optional backend connectivity in `DatabaseRouter` in `src/db/router.py` — when running standalone but `ARANGO_HOST`/`REDIS_HOST` explicitly configured, attempt connection (user has opted in); log result at Info level

**Checkpoint**: Standalone users experience zero regressions — CSV output identical, no new error messages, no new dependencies required

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, migration utility, and final quality validation

- [ ] T036 [P] Update `README.md` with polyglot database architecture section — new environment variables table, compose service diagram, storage backend descriptions
- [ ] T037 [P] Update `CHANGELOG.md` with version entry for polyglot DB migration feature (Keep a Changelog format, `version YY.MM.DD.HH.MM`)
- [ ] T038 Implement SQLite-to-polyglot one-time migration utility in `scripts/migrate_sqlite_to_polyglot.py` (FR-011) — read existing `data/mist_data.db`, classify tables by PK strategy, export documents to ArangoDB and time-series to Redis, preserve all historical data (SC-008)
- [ ] T039 Run full quality gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `pytest tests/ -v --cov`
- [ ] T040 [P] Run `quickstart.md` validation steps end-to-end — verify developer setup, service connections, test execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US2 (Phase 3)**: Depends on Foundational — ArangoDB writer (can parallel with Phase 4)
- **US3 (Phase 4)**: Depends on Foundational — Redis writer (can parallel with Phase 3)
- **US4 (Phase 5)**: Depends on US2 + US3 — routing connects the writers
- **US1 (Phase 6)**: Depends on US4 — end-to-end integration (MVP checkpoint)
- **US5 (Phase 7)**: Depends on US2 — uses ArangoDBWriter.snapshot()
- **US6 (Phase 8)**: Depends on US2 + US3 — manages retention across both backends
- **US7 (Phase 9)**: Depends on US4 — validates graceful fallback in router
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### Priority vs Implementation Order

US1 is P1 (highest priority) but depends on US2 + US3 + US4. The implementation order resolves this: build the backends first (US2, US3), wire the routing (US4), then validate end-to-end (US1). All P1 stories complete together at the Phase 6 checkpoint.

### User Story Dependencies

```text
US2 (ArangoDB Writer) ──┐
                        ├──→ US4 (Routing) ──→ US1 (Integration) ──→ MVP
US3 (Redis Writer) ─────┘         │
                                  ├──→ US5 (Snapshots)
                                  ├──→ US7 (Standalone)
US2 + US3 ────────────────────────┴──→ US6 (Retention)
```

### Within Each User Story

1. Tests written first (should fail before implementation)
2. Core class and connection before business logic
3. Primary operations before edge cases (soft-delete, compaction rules)
4. Story complete before moving to next phase

---

## Parallel Opportunities

### Phase 3 + Phase 4 (Full Parallel)

```text
Agent A: T009 → T010 → T011 → T012 → T013   (ArangoDB writer)
Agent B: T014 → T015 → T016 → T017           (Redis writer)
```

### Within Foundational Phase

```text
Parallel: T005 (structlog), T006 (ArangoDB compose), T007 (Redis compose)
After T004: T008 (router skeleton imports DatabaseConfig)
```

### Within US1 Phase

```text
Parallel: T021 (integration test), T025 (import setup)
Sequential: T022 → T023 → T024 (DataExporter changes + compose depends_on)
```

### Polish Phase

```text
Parallel: T036 (README), T037 (CHANGELOG), T040 (quickstart validation)
Sequential: T038 (migration utility) → T039 (quality gates)
```

---

## Implementation Strategy

### MVP First (Through Phase 6)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (5 tasks, blocks everything)
3. Complete Phase 3 + 4 in parallel: US2 + US3 backend writers (9 tasks)
4. Complete Phase 5: US4 routing logic (3 tasks)
5. Complete Phase 6: US1 integration (5 tasks)
6. **STOP AND VALIDATE**: `podman-compose up`, run Menu 11, verify ArangoDB + Redis + CSV output
7. This is the **MVP** — all P1 stories complete, system is functional end-to-end

### Incremental Delivery After MVP

1. Add US5 (P2): Config snapshots → Deploy/validate
2. Add US6 (P3): Retention management → Deploy/validate
3. Add US7 (P3): Standalone verification → Deploy/validate
4. Polish: Docs, migration tool, quality gates → Final release

### Total Task Summary

| Phase | Story | Tasks | Parallel |
| - | - | - | - |
| 1 Setup | — | 3 | 2 |
| 2 Foundational | — | 5 | 3 |
| 3 US2 | ArangoDB Writer | 5 | 1 |
| 4 US3 | Redis Writer | 4 | 1 |
| 5 US4 | Auto-Routing | 3 | 1 |
| 6 US1 | Container Integration | 5 | 2 |
| 7 US5 | Config Snapshots | 3 | 0 |
| 8 US6 | Retention | 4 | 0 |
| 9 US7 | Standalone Mode | 3 | 0 |
| 10 Polish | Cross-Cutting | 5 | 3 |
| **Total** | | **40** | **13** |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps tasks to user stories for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- Stop at Phase 6 checkpoint to validate MVP before proceeding
- All new code in `src/db/` uses `structlog` (research decision #8)
- Migration utility (T038) in `scripts/` to keep `src/db/` at 5 files (Five-Item Rule)
- `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is read-only for this feature — no entries changed
