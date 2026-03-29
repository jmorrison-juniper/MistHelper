# Tasks: Automated Testing Infrastructure

**Input**: Design documents from `/specs/012-automated-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests ARE included — this feature is specifically about building test infrastructure (FR-003, FR-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project directories and shared configuration for all test infrastructure

- [X] T001 Create `tests/` directory structure with `tests/__init__.py`, `tests/unit/__init__.py`
- [X] T002 Create pytest configuration in `tests/conftest.py` with test isolation setup (temp dirs, no network)
- [X] T003 [P] Add `pytest` to `requirements.txt` as a dev dependency

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core classes that MUST be complete before ANY user story can be implemented — `TelemetryEmitter` and `OperationRegistry` are used by all stories

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `TelemetryEmitter` class in `MistHelper.py` with `__init__(file_path)`, `emit(event_dict)`, `close()`, and context manager support per data-model.md schemas
- [X] T005 Implement `TelemetryEmitter.enforce_retention()` method to delete oldest timestamped JSONL files when count exceeds configurable limit (default 10) in `MistHelper.py`
- [X] T006 Implement `OperationRegistry` class in `MistHelper.py` centralizing all operation classifications from existing `unsafe_options` and `interactive_read_only_options` dicts per research.md R2. Unregistered operations MUST default to category `safe` with a logged warning so new menu items are automatically included in test runs
- [X] T007 Add `TelemetryEmitter` helper methods `emit_progress_start()`, `emit_progress_tick()`, `emit_progress_complete()` with parameter construction per contracts/telemetry.md schemas in `MistHelper.py`
- [X] T008 Add `TelemetryEmitter` helper methods `emit_test_start()`, `emit_test_pass()`, `emit_test_fail()`, `emit_test_skip()`, `emit_test_summary()` per contracts/telemetry.md schemas in `MistHelper.py`

**Checkpoint**: Foundation ready — `TelemetryEmitter` can emit all 8 event types, `OperationRegistry` classifies all ~120 menu operations

---

## Phase 3: User Story 1 — Structured Test Event Output for AI Consumption (Priority: P1) MVP

**Goal**: `--test` and `--testinteractive` runs emit structured NDJSON events to `data/test_events_YYYYMMDD_HHMMSS.jsonl` so AI agents can read pass/fail/skip results without regex parsing

**Independent Test**: Run `python MistHelper.py --test --skip-deps` (with valid credentials), then verify every line in `data/test_events_*.jsonl` is valid JSON with fields per contracts/telemetry.md

### Implementation for User Story 1

- [X] T009 [US1] Refactor `run_systematic_test()` in `MistHelper.py` to use `OperationRegistry` instead of inline `unsafe_options` dict, replacing the duplicated classification logic
- [X] T010 [US1] Integrate `TelemetryEmitter` into `run_systematic_test()` in `MistHelper.py` — emit `test_start`/`test_pass`/`test_fail` events around each operation execution
- [X] T011 [US1] Add skip event emission in `run_systematic_test()` in `MistHelper.py` — emit `test_skip` for every operation in `OperationRegistry` that is not category `safe` or `interactive_safe`
- [X] T012 [US1] Add `test_summary` event emission at end of `run_systematic_test()` in `MistHelper.py` with total/pass/fail/skip counts and elapsed time
- [X] T013 [US1] Refactor `run_interactive_test()` in `MistHelper.py` to use `OperationRegistry` instead of inline `interactive_read_only_options` dict
- [X] T014 [US1] Integrate `TelemetryEmitter` into `run_interactive_test()` in `MistHelper.py` — emit test events with `test_mode: "interactive"` and summary at completion
- [X] T015 [US1] Add timestamped filename generation for test event files (`test_events_YYYYMMDD_HHMMSS.jsonl`) in `TelemetryEmitter` initialization within `run_systematic_test()` and `run_interactive_test()` in `MistHelper.py`
- [X] T016 [US1] Call `TelemetryEmitter.enforce_retention()` at end of test runs in `MistHelper.py` to clean up old JSONL files

**Checkpoint**: Running `--test` produces a machine-readable JSONL file alongside existing console/log output. Every operation emits exactly one event (pass, fail, or skip).

---

## Phase 4: User Story 2 — Offline Unit Test Suite for Core Utilities (Priority: P1)

**Goal**: `python -m pytest tests/unit/` runs isolated tests for pure utility functions with zero API credentials, zero network, under 30 seconds

**Independent Test**: Run `python -m pytest tests/unit/ -v` from project root with no `.env` file. All tests pass. No network calls made.

### Implementation for User Story 2

- [X] T017 [P] [US2] Create `tests/unit/test_config_utils.py`
- [X] T018 [P] [US2] Create `tests/unit/test_data_processing.py`
- [X] T019 [P] [US2] Create `tests/unit/test_pk_strategies.py`
- [X] T020 [P] [US2] Create `tests/unit/test_telemetry.py`

**Checkpoint**: `python -m pytest tests/unit/ -v` passes all tests in <30 seconds with zero network calls. Exit code 0.

---

## Phase 5: User Story 3 — CI Pipeline Integration with GitHub Actions (Priority: P2)

**Goal**: GitHub Actions runs unit tests before container build on every push/PR, gating deployment on test success

**Independent Test**: Push a commit with a broken test. CI `test` job fails, `build-and-push` job is skipped.

### Implementation for User Story 3

- [X] T021 [US3] Add `test` job to `.github/workflows/container-build.yml` between `validate` and `build-and-push` — uses `actions/setup-python@v5` with Python 3.13, installs pytest, runs `python -m pytest tests/unit/ -v`
- [X] T022 [US3] Update `build-and-push` job dependency in `.github/workflows/container-build.yml` from `needs: validate` to `needs: test` so container build is gated on test success
- [X] T023 [US3] Add `tests/**` to workflow trigger paths in `.github/workflows/container-build.yml` so test file changes trigger CI

**Checkpoint**: CI pipeline has 3 sequential jobs: validate → test → build-and-push. Test failures block container deployment.

---

## Phase 6: User Story 4 — AI-Readable Progress Hooks During Live Operations (Priority: P2)

**Goal**: Long-running site/device iteration operations always emit structured `progress_start`/`progress_tick`/`progress_complete` events to `data/test_events.jsonl` for AI consumption

**Independent Test**: Run Menu 11 (device inventory), then read `data/test_events.jsonl` and confirm progress events show start/tick/complete lifecycle with site counts

### Implementation for User Story 4

- [X] T024 [US4] Initialize a global `TelemetryEmitter` instance for progress events (file: `data/test_events.jsonl`) in `MistHelper.py` startup, gated behind best-effort try/except per FR-008
- [X] T025 [US4] Add progress hooks to Menu 11 (List Site Devices) site iteration loop in `MistHelper.py` — emit `progress_start` before loop, `progress_tick` per site, `progress_complete` after loop
- [X] T026 [P] [US4] Add progress hooks to Menu 12 (List Site Device Stats) site iteration loop in `MistHelper.py`
- [X] T027 [P] [US4] Add progress hooks to Menu 13 (List Org Devices) operation in `MistHelper.py`
- [X] T028 [P] [US4] Add progress hooks to Menu 66 (Wireless Client Data) site iteration loop in `MistHelper.py`
- [X] T029 [P] [US4] Add progress hooks to Menu 67 (Wired Client Data) site iteration loop in `MistHelper.py`
- [X] T030 [US4] Add progress hooks to 5 additional high-use site iteration operations (Menus 15, 16, 17, 29, 42) in `MistHelper.py` — start with most-used operations per research.md R6
- [X] T031 [US4] Add telemetry hooks to 2-3 representative destructive operations (Menu 90 AP Firmware, Menu 97 SSH Runner) in `MistHelper.py` — hooks emit progress/test events only when a human runs them manually per FR-013

**Checkpoint**: Running any instrumented operation produces progress events in `data/test_events.jsonl` with full lifecycle (start/tick/complete). AI agents can determine percentage completion at any point. Destructive operations have telemetry hooks for manual execution.

---

## Phase 7: User Story 5 — Test Result Comparison Across Runs (Priority: P3)

**Goal**: A comparison utility reads two JSONL files and reports regressions (new failures, resolved failures, timing changes >2x)

**Independent Test**: Create two sample JSONL files with known differences, run comparison utility, verify it flags expected regressions

### Implementation for User Story 5

- [X] T032 [US5] Create `TestComparator` class in `scripts/compare_test_runs.py` with `load_events(file_path)` method that reads JSONL and indexes TestEvents by `menu_option`
- [X] T033 [US5] Implement `TestComparator.compare(run_a_path, run_b_path)` method in `scripts/compare_test_runs.py` that produces `TestComparison` result per data-model.md — detecting new failures, resolved failures, timing regressions (>2x), and status changes
- [X] T034 [US5] Implement `TestComparator.format_report(comparison)` method in `scripts/compare_test_runs.py` to produce human-readable summary output
- [X] T035 [US5] Add CLI entry point to `scripts/compare_test_runs.py` with `argparse` accepting two JSONL file paths and printing comparison report

**Checkpoint**: `python scripts/compare_test_runs.py data/run_a.jsonl data/run_b.jsonl` outputs a clear regression report with new failures, resolved failures, and timing changes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and deployment

- [X] T036 [P] Add FR-011/FR-014 compliance check — verify `run_systematic_test()` executes ALL non-destructive operations (no operations accidentally excluded) and all execution is non-interactive in `MistHelper.py`
- [X] T037 [P] Update `README.md` with testing section documenting: unit test commands, live test commands, JSONL output format, comparison utility usage
- [X] T038 Validate syntax with `python -m py_compile MistHelper.py` and run full unit test suite `python -m pytest tests/unit/ -v`
- [X] T039 Run `specs/012-automated-testing/quickstart.md` validation — execute each quickstart command and confirm expected output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (`TelemetryEmitter`, `OperationRegistry`)
- **US2 (Phase 4)**: Depends on Phase 1 (test directory) and Phase 2 (`TelemetryEmitter` for test_telemetry.py). Can run in PARALLEL with US1.
- **US3 (Phase 5)**: Depends on Phase 4 (unit tests must exist before CI can run them)
- **US4 (Phase 6)**: Depends on Phase 2 (`TelemetryEmitter`). Can run in PARALLEL with US1, US2, US3.
- **US5 (Phase 7)**: Depends on Phase 3 (needs JSONL files to compare). Can start once US1 is done.
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no other story dependencies
- **US2 (P1)**: Depends on Foundational only — no other story dependencies. **Can run in parallel with US1.**
- **US3 (P2)**: Depends on US2 (unit tests must exist for CI to run them)
- **US4 (P2)**: Depends on Foundational only — no other story dependencies. **Can run in parallel with US1, US2.**
- **US5 (P3)**: Depends on US1 (needs test event JSONL format established)

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks T001-T003 are all independent
- Foundational tasks T004-T005 (TelemetryEmitter) and T006 (OperationRegistry) can run in parallel
- T007-T008 (helper methods) depend on T004 but can run in parallel with each other
- US1 and US2 can start simultaneously after Foundational is done
- US4 can start anytime after Foundational, independent of US1/US2/US3
- Within US2: all 4 test files (T017-T020) can be written in parallel
- Within US4: progress hooks for different menus (T026-T029) can be added in parallel

---

## Parallel Example: User Stories 1 + 2 (Simultaneous)

```text
# After Phase 2 completes, launch US1 and US2 together:

# US1 track (test harness refactor):
Task T009: Refactor run_systematic_test() to use OperationRegistry
Task T010: Integrate TelemetryEmitter into run_systematic_test()
...

# US2 track (unit tests — independent files, all parallel):
Task T017: test_config_utils.py
Task T018: test_data_processing.py
Task T019: test_pk_strategies.py
Task T020: test_telemetry.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: User Story 1 — structured NDJSON output from `--test`
4. Complete Phase 4: User Story 2 — offline unit tests
5. **STOP and VALIDATE**: Run `--test` and verify JSONL output. Run `pytest tests/unit/`. Both must pass.
6. This is the MVP — machine-readable test results + fast offline tests.

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. US1 + US2 (parallel) → MVP: NDJSON output + unit tests
3. US3 → CI gates deployment on tests
4. US4 → Progress monitoring for AI agents
5. US5 → Regression detection across runs
6. Polish → Documentation, validation, deployment

### Single-Developer Path (Sequential)

1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7 (US5) → Phase 8

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Unit tests duplicate pure utility functions from MistHelper.py to avoid import side effects (research.md R1)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
