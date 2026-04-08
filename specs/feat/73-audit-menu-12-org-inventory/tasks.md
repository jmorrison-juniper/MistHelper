# Tasks: Audit Menu 12 - Organization Inventory Export

**Input**: Design documents from `/specs/feat/73-audit-menu-12-org-inventory/` and `/specs/024-audit-menu-12-org-inventory/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md
**Issue**: [#73](https://github.com/jmorrison-juniper/MistHelper/issues/73)
**Branch**: `feat/73-audit-menu-12-org-inventory`

**Tests**: Explicitly requested in spec. TDD approach — write tests first, verify they fail, then implementation confirms they pass.

**Organization**: Tasks grouped by user story (4 stories from spec.md, prioritized P1→P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project prerequisites and create shared test fixtures

- [ ] T001 Verify conftest.py imports MistHelper module correctly in `tests/conftest.py`
- [ ] T002 Create shared device fixtures module in `tests/fixtures/device_inventory.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared fixture data and test utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create device fixture constants (DEVICE_AP, DEVICE_SWITCH, DEVICE_MISSING_OPTIONAL) in `tests/fixtures/device_inventory.py`
- [ ] T004 Create fixture factory function `make_device_fixtures(count)` that generates N unique device records in `tests/fixtures/device_inventory.py`
- [ ] T005 Create `tests/fixtures/__init__.py` to expose fixture imports

**Checkpoint**: Fixture module importable and produces valid device records

---

## Phase 3: User Story 1 - Export Organization Inventory to CSV (Priority: P1) MVP

**Goal**: Verify OrgInventoryExporter.inventory() passes correct parameters to APIDataFetcher and calls execute()

**Independent Test**: Run `pytest tests/unit/test_menu_12_inventory.py -v` — all tests pass with mocked APIDataFetcher

### Tests for User Story 1

- [ ] T006 [P] [US1] Write test_inventory_creates_api_data_fetcher_with_correct_params in `tests/unit/test_menu_12_inventory.py`
- [ ] T007 [P] [US1] Write test_inventory_calls_execute_exactly_once in `tests/unit/test_menu_12_inventory.py`
- [ ] T008 [US1] Run tests and verify they PASS (no production changes needed — implementation already exists)

**Checkpoint**: Unit tests confirm Menu 12 wiring is correct — APIDataFetcher receives api_call, filename="OrgInventory.csv", sort_key="model", limit=1000

---

## Phase 4: User Story 2 - Idempotent SQLite Upsert on Repeated Runs (Priority: P1)

**Goal**: Verify SQLite upsert produces no duplicates on repeated exports and updates changed fields

**Independent Test**: Run `pytest tests/integration/test_menu_12_sqlite_upsert.py::test_upsert_idempotency -v` — exactly N rows after 2 writes of N records

### Tests for User Story 2

- [ ] T009 [P] [US2] Write test_upsert_idempotency (10 devices written twice, assert 10 rows) in `tests/integration/test_menu_12_sqlite_upsert.py`
- [ ] T010 [P] [US2] Write test_upsert_updates_changed_fields (write 10, change 1 model, rewrite, verify update) in `tests/integration/test_menu_12_sqlite_upsert.py`
- [ ] T011 [US2] Write test_indexes_created (verify sqlite_master has indexes on org_id, site_id, mac, serial, model, type) in `tests/integration/test_menu_12_sqlite_upsert.py`
- [ ] T012 [US2] Run integration tests and verify they PASS against temporary SQLite database

**Checkpoint**: SQLite upsert is idempotent, field updates propagate, indexes exist

---

## Phase 5: User Story 3 - Stable CSV Column Schema (Priority: P2)

**Goal**: Verify CSV output contains expected column headers matching API response fields

**Independent Test**: Run `pytest tests/integration/test_menu_12_sqlite_upsert.py::test_csv_schema_contains_expected_columns -v`

### Tests for User Story 3

- [ ] T013 [US3] Write test_csv_schema_contains_expected_columns (export fixtures to CSV, verify headers) in `tests/integration/test_menu_12_sqlite_upsert.py`
- [ ] T014 [US3] Write test_csv_roundtrip_matches_source_data (export fixtures, read back, verify values match) in `tests/integration/test_menu_12_sqlite_upsert.py`
- [ ] T015 [US3] Run CSV schema tests and verify they PASS

**Checkpoint**: CSV column schema is deterministic and matches expected field set

---

## Phase 6: User Story 4 - Progress Reporting via WebSocket Emitter (Priority: P3)

**Goal**: Verify PROGRESS_EMITTER lifecycle calls with correct menu ID and timing

**Independent Test**: Run `pytest tests/unit/test_menu_12_inventory.py::test_inventory_emits_progress_start_and_complete -v`

### Tests for User Story 4

- [ ] T016 [P] [US4] Write test_inventory_emits_progress_start_and_complete (mock emitter, verify emit_progress_start/complete called) in `tests/unit/test_menu_12_inventory.py`
- [ ] T017 [P] [US4] Write test_inventory_handles_no_emitter_gracefully (PROGRESS_EMITTER=None, no exception) in `tests/unit/test_menu_12_inventory.py`
- [ ] T018 [US4] Run emitter tests and verify they PASS

**Checkpoint**: Progress emitter integration verified — web UI receives correct events

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and CI readiness

- [ ] T019 Run full test suite (`pytest tests/ -v --timeout=30`) and verify no regressions
- [ ] T020 [P] Run quickstart.md validation commands from `specs/feat/73-audit-menu-12-org-inventory/quickstart.md`
- [ ] T021 [P] Verify CI quality gates locally: ruff check, mypy, bandit, pip-audit on new test files
- [ ] T022 Commit all test files and push to `feat/73-audit-menu-12-org-inventory` branch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — unit tests for APIDataFetcher wiring
- **US2 (Phase 4)**: Depends on Foundational — integration tests for SQLite upsert
- **US3 (Phase 5)**: Depends on Foundational — integration tests for CSV schema
- **US4 (Phase 6)**: Depends on Foundational — unit tests for progress emitter
- **Polish (Phase 7)**: Depends on ALL user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent — no dependency on other stories
- **US2 (P1)**: Independent — tests DataExporter/SQLite layer directly, no dependency on US1
- **US3 (P2)**: Independent — tests CSV output directly, no dependency on US1/US2
- **US4 (P3)**: Independent — tests PROGRESS_EMITTER mocking, no dependency on US1-3

### Within Each User Story

- Write tests FIRST
- Run tests to verify behavior (existing implementation should make them PASS)
- No production code changes expected (audit confirms existing code is correct)

### Parallel Opportunities

- **After Phase 2 completes**: US1, US2, US3, US4 can ALL start in parallel (different test files, no shared state)
- Within US1: T006, T007 can run in parallel (different test functions, same file)
- Within US2: T009, T010 can run in parallel (different test functions, same file)
- Within US4: T016, T017 can run in parallel (different test functions, same file)

---

## Parallel Example: User Stories 1-4

```bash
# After Phase 2 (Foundational) completes, launch all in parallel:

# Agent/Thread 1: User Story 1 (unit tests)
Task T006: "Write test_inventory_creates_api_data_fetcher_with_correct_params"
Task T007: "Write test_inventory_calls_execute_exactly_once"
Task T008: "Run and verify"

# Agent/Thread 2: User Story 2 (integration tests - SQLite)
Task T009: "Write test_upsert_idempotency"
Task T010: "Write test_upsert_updates_changed_fields"
Task T011: "Write test_indexes_created"
Task T012: "Run and verify"

# Agent/Thread 3: User Story 3 (integration tests - CSV)
Task T013: "Write test_csv_schema_contains_expected_columns"
Task T014: "Write test_csv_roundtrip_matches_source_data"
Task T015: "Run and verify"

# Agent/Thread 4: User Story 4 (unit tests - emitter)
Task T016: "Write test_inventory_emits_progress_start_and_complete"
Task T017: "Write test_inventory_handles_no_emitter_gracefully"
Task T018: "Run and verify"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (verify conftest)
2. Complete Phase 2: Foundational (create fixtures)
3. Complete Phase 3: US1 — unit tests for APIDataFetcher wiring
4. Complete Phase 4: US2 — integration tests for SQLite upsert
5. **STOP and VALIDATE**: Run `pytest tests/unit/test_menu_12_inventory.py tests/integration/test_menu_12_sqlite_upsert.py -v`
6. These 2 stories cover the critical data correctness requirements

### Incremental Delivery

1. Setup + Foundational → Fixtures ready
2. US1 → APIDataFetcher wiring verified
3. US2 → SQLite upsert idempotency proven → **MVP complete**
4. US3 → CSV schema stability confirmed
5. US4 → Progress emitter lifecycle verified → **Full coverage**
6. Polish → CI gates, full regression, commit+push

### Multi-Agent Safety

- This branch touches ONLY: `tests/unit/test_menu_12_inventory.py`, `tests/integration/test_menu_12_sqlite_upsert.py`, `tests/fixtures/device_inventory.py`, `tests/fixtures/__init__.py`
- **MistHelper.py is NOT modified** — no hot-file conflict
- No overlap with `feat/72-ssid-template-consolidation-rewrite` (different spec dir, different test files)
- Commit scope: specs + test files only

---

## Notes

- [P] tasks = different files or independent test functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after Phase 2
- No production code changes — this is a test-only audit PR
- Existing implementation already works; tests CONFIRM correctness
- Commit after each phase checkpoint for progress visibility
