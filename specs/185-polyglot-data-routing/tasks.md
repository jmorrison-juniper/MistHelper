# Tasks: Polyglot Data Routing Refactor

**Input**: Design documents from `/specs/185-polyglot-data-routing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/internal-interfaces.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and prepare the working environment

- [x] T001 Verify infrastructure is running: `podman compose up -d arangodb redis-stack` and confirm both services are healthy
- [x] T002 Verify environment variables are set per quickstart.md (`ARANGO_HOST`, `ARANGO_ROOT_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)
- [x] T003 Create feature branch `feat/185-polyglot-data-routing` from `main`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model updates and new classes that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `DualWriteResult` dataclass to `src/db/__init__.py` with `arango_result: WriteResult`, `redis_result: WriteResult`, and `combined` property
- [x] T005 Update `WriteResult.backend` field documentation in `src/db/__init__.py` to include new values: `"redis_json"`, `"dual"`
- [x] T006 [P] Add `RedisJSONWriter` class to `src/db/redis_writer.py` with `__init__(config: DatabaseConfig)`, `write(data, api_function_name, strategy) -> WriteResult`, and `_build_key(endpoint, record, pk_fields) -> str` methods
- [x] T007 [P] Update routing constants in `src/db/router.py`: replace `ARANGO_PK_TYPES` and `REDIS_PK_TYPES` with `ARANGO_ONLY_TYPES`, `DUAL_WRITE_TYPES`, and `TIMESERIES_TYPES` sets
- [x] T008 Export `RedisJSONWriter` and `DualWriteResult` in `src/db/__init__.py` `__all__` list
- [x] T009 Run quality gates on all modified files: `py_compile`, `ruff check`, `black --check` for `src/db/__init__.py`, `src/db/redis_writer.py`, `src/db/router.py`

**Checkpoint**: Foundation ready -- new writer class exists, routing constants updated, data models in place

---

## Phase 3: User Story 1 - Raw Document Persistence in ArangoDB (Priority: P1) MVP

**Goal**: Route unflattened API data to polyglot backends while preserving CSV output byte-for-byte

**Independent Test**: Run menu 11 (Org Sites), query ArangoDB for nested fields (e.g., `doc.latlng.lat`), verify CSV output is unchanged

### Implementation for User Story 1

- [x] T010 [US1] Add `raw_data: list[dict[str, Any]] | None = None` parameter to `DataExporter.write_with_format_selection()` in `MistHelper.py` per contract in `contracts/internal-interfaces.md`
- [x] T011 [US1] Update `DataExporter._route_to_polyglot()` in `MistHelper.py` to accept `raw_data` parameter and pass `raw_data or data` to `DatabaseRouter.write()`
- [x] T012 [US1] Update menu 11 (`listOrgSites`) caller in `MistHelper.py` to pass `raw_data=raw_results` alongside flattened data to `write_with_format_selection()`
- [x] T013 [P] [US1] Update menu 1 (`getOrgInventory`) caller in `MistHelper.py` to pass `raw_data=raw_results` alongside flattened data
- [x] T014 [P] [US1] Update menu 3 (`listSiteDevices`) caller in `MistHelper.py` to pass `raw_data=raw_results` alongside flattened data
- [x] T015 [US1] Run quality gates: `py_compile`, `ruff check`, `black --check` for `MistHelper.py`
- [x] T016 [US1] Verify: run `python MistHelper.py --menu 11`, query ArangoDB for nested `latlng` field, confirm CSV output is identical to pre-refactor

**Checkpoint**: ArangoDB receives raw nested documents for `natural_pk` endpoints. CSV output unchanged. SC-001, SC-003 verified.

---

## Phase 4: User Story 2 - Event Documents in Redis JSON (Priority: P2)

**Goal**: Store `composite_pk` event documents as Redis JSON with dual-write to ArangoDB

**Independent Test**: Run menu 13 (Device Events), verify Redis contains full JSON documents with all fields, and ArangoDB also has the archive copy

### Implementation for User Story 2

- [x] T017 [US2] Implement `RedisJSONWriter._verify_json_module()` method in `src/db/redis_writer.py` to check for `ReJSON` module availability (mirrors existing `_verify_timeseries_module()` pattern)
- [x] T018 [US2] Implement `RedisJSONWriter.write()` body in `src/db/redis_writer.py`: pipeline `JSON.SET` + `EXPIRE` for each record using key pattern `{endpoint}:{pk_values}` and TTL from `REDIS_JSON_TTL_DAYS` env var (default 7)
- [x] T019 [US2] Initialize `RedisJSONWriter` in `DatabaseRouter.__init__()` in `src/db/router.py` alongside existing `RedisTimeSeriesWriter`
- [x] T020 [US2] Add `_write_dual()` method to `DatabaseRouter` in `src/db/router.py` that calls both `_write_redis_json()` and `_write_arango()` independently, returning `DualWriteResult`
- [x] T021 [US2] Update `DatabaseRouter.write()` dispatch in `src/db/router.py` to route `composite_pk` (from `DUAL_WRITE_TYPES`) through `_write_dual()`
- [x] T022 [US2] Add `_write_redis_json()` helper method to `DatabaseRouter` in `src/db/router.py` that delegates to `RedisJSONWriter.write()`
- [x] T023 [US2] Run quality gates: `py_compile`, `ruff check`, `black --check` for `src/db/router.py`, `src/db/redis_writer.py`
- [x] T024 [US2] Verify: run a `composite_pk` endpoint (e.g., menu 13 Device Events), confirm Redis JSON documents exist with `redis-cli JSON.GET`, confirm ArangoDB archive has same documents

**Checkpoint**: `composite_pk` endpoints dual-write to Redis JSON + ArangoDB. SC-002, SC-005 verified.

---

## Phase 5: User Story 3 - Numeric Metrics via Redis TimeSeries (Priority: P3)

**Goal**: Route pure-numeric endpoints to Redis TimeSeries with explicit field configuration via `timeseries_pk` strategy

**Independent Test**: Run a device stats endpoint, verify Redis TimeSeries has numeric data points with text metadata stored as labels

### Implementation for User Story 3

- [x] T025 [US3] Add `timeseries_pk` to routing dispatch in `DatabaseRouter.write()` in `src/db/router.py` -- route to existing `_write_redis()` method
- [x] T026 [US3] Update `RedisTimeSeriesWriter._extract_chunk()` in `src/db/redis_writer.py` to respect `ts_value_fields` (extract only listed fields) when present in the strategy dict
- [x] T027 [US3] Update `RedisTimeSeriesWriter._extract_chunk()` in `src/db/redis_writer.py` to use `ts_label_fields` as TimeSeries labels when present in the strategy dict
- [x] T028 [US3] Ensure fallback: if `ts_value_fields` is not in the strategy, `_extract_chunk()` falls back to current auto-detect behavior in `src/db/redis_writer.py`
- [x] T029 [US3] Run quality gates: `py_compile`, `ruff check`, `black --check` for `src/db/router.py`, `src/db/redis_writer.py`
- [x] T030 [US3] Verify: confirm `timeseries_pk` dispatching works by temporarily reclassifying one endpoint and running it

**Checkpoint**: `timeseries_pk` strategy routes numeric data to Redis TimeSeries with labels. SC-004 verified.

---

## Phase 6: User Story 4 - Endpoint Strategy Reclassification (Priority: P2)

**Goal**: Reclassify 6 pure-numeric endpoints from `composite_pk` to `timeseries_pk` with explicit field configuration

**Independent Test**: Inspect `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict, verify reclassified endpoints have `timeseries_pk` type with `ts_value_fields` and `ts_label_fields`

### Implementation for User Story 4

- [x] T031 [US4] Reclassify `listOrgDevicesStats` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` from `composite_pk` to `timeseries_pk` with `ts_value_fields` and `ts_label_fields` per data-model.md
- [x] T032 [P] [US4] Reclassify `listSiteDevicesStats` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` with same pattern as `listOrgDevicesStats`
- [x] T033 [P] [US4] Reclassify `listSiteWirelessClientsStats` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` with `ts_value_fields: [rssi, snr, rx_rate, tx_rate]` and `ts_label_fields: [ssid, hostname, device_id]`
- [x] T034 [P] [US4] Reclassify `searchOrgSwOrGwPorts` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` with `ts_value_fields: [rx_bytes, tx_bytes, rx_errors, tx_errors]` and `ts_label_fields: [port_id, device_id, org_id]`
- [x] T035 [P] [US4] Reclassify `searchSiteSwOrGwPorts` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` with same port pattern
- [x] T036 [P] [US4] Reclassify `searchOrgPeerPathStats` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py` with `ts_value_fields: [latency, jitter, loss]` and `ts_label_fields: [from_device, to_device, org_id]`
- [x] T037 [US4] Verify all other endpoints (`natural_pk`, `auto_increment_with_unique`, remaining `composite_pk`) are unchanged in `MistHelper.py`
- [x] T038 [US4] Run quality gates: `py_compile`, `ruff check`, `black --check` for `MistHelper.py`
- [x] T039 [US4] Verify: run a reclassified stats endpoint, confirm Redis TimeSeries receives labeled numeric data points

**Checkpoint**: All 6 endpoints reclassified. Remaining endpoints verified unchanged. SC-004 verified end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and quality sweep

- [x] T040 [P] Verify graceful degradation: stop Redis, run menu 11, confirm CSV output succeeds and warning is logged (SC-005)
- [x] T041 [P] Verify graceful degradation: stop ArangoDB, run a `composite_pk` endpoint, confirm CSV output succeeds and warning is logged (SC-005)
- [x] T042 Verify dual-write performance: time a `composite_pk` endpoint write and confirm overhead is < 2x single-backend (SC-007)
- [x] T043 Run full quality gates on all modified files: `py_compile`, `ruff check`, `black --check` for `MistHelper.py`, `src/db/__init__.py`, `src/db/router.py`, `src/db/redis_writer.py`
- [x] T044 Update `src/db/__init__.py` module docstring to reflect new routing: "Routes API data to ArangoDB (documents), Redis JSON (events), or Redis TimeSeries (metrics)"
- [x] T045 Run quickstart.md verification commands end-to-end to confirm all acceptance criteria pass

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup)
    |
    v
Phase 2 (Foundational) -- BLOCKS all user stories
    |
    v
Phase 3 (US1: Raw Data Pipeline - P1) -- MVP
    |
    v
Phase 4 (US2: Redis JSON + Dual-Write - P2) ----+
    |                                             |
Phase 5 (US3: TimeSeries Strategy - P3) ---------+
    |                                             |
    v                                             v
Phase 6 (US4: Endpoint Reclassification - P2) -- requires Phase 4 AND Phase 5
    |
    v
Phase 7 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. No dependency on other stories. **This is the MVP.**
- **US2 (P2)**: Depends on Phase 2 and US1 (needs `raw_data` pipeline from US1 to feed dual-write)
- **US3 (P3)**: Depends on Phase 2 only. Independent of US1 and US2 (routing update only, no data pipeline change needed)
- **US4 (P2)**: Depends on US2 (dual-write routing must exist) AND US3 (`timeseries_pk` routing must exist). Both must be complete before reclassification.

### Within Each User Story

- Core implementation before integration/verification
- Quality gates before verification testing
- Verification confirms acceptance criteria from spec.md

### Parallel Opportunities

**Phase 2**: T006 and T007 can run in parallel (different files: `redis_writer.py` vs `router.py`)

**Phase 3 (US1)**: T013 and T014 can run in parallel (different menu operations in same file, but independent callers)

**Phase 5 (US3) and Phase 4 (US2)**: These two phases can run in parallel after US1 completes, since they modify different files:
- US2 modifies `src/db/router.py` (dual-write dispatch) and `src/db/redis_writer.py` (JSON writer body)
- US3 modifies `src/db/router.py` (TS dispatch) and `src/db/redis_writer.py` (extract_chunk)
- **Caution**: Both touch the same two files, so true parallelism requires careful coordination. Sequential execution (US2 → US3) is safer for a single agent.

**Phase 6 (US4)**: T032-T036 can all run in parallel (independent endpoint entries in the same dictionary)

---

## Implementation Strategy

### MVP Scope

**User Story 1 (Phase 3)** is the MVP. After completing Phases 1-3:
- ArangoDB receives raw nested documents instead of flattened data
- CSV output is byte-identical to current behavior
- The system is strictly better than before with zero regression risk

### Incremental Delivery

1. **Increment 1 (MVP)**: Phases 1-3 → Raw data pipeline working for `natural_pk` endpoints
2. **Increment 2**: Phase 4 → `composite_pk` events stored in Redis JSON + ArangoDB
3. **Increment 3**: Phase 5 → `timeseries_pk` routing with explicit field config
4. **Increment 4**: Phase 6 → Endpoint reclassification (all routing correct)
5. **Increment 5**: Phase 7 → Polish, degradation testing, performance verification

Each increment is independently deployable and testable.
