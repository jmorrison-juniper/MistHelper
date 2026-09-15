# Tasks: Performance monitoring modules

**Input**: Design documents from `specs/2533-perf-monitoring/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Required by issue #2533.

**Organization**: Tasks are ordered by dependency.

## Phase 1: Setup

**Purpose**: Read the issue, the hook catalog, the constitution, and the repository rules.

- [x] T001 Read issue #2533 and issue #2482. (delivered: issue review evidence in the session log)
- [x] T002 Read the 2448 performance monitoring plan and hook catalog summary. (delivered: specs/2448-misthelper-performance-monitoring/plan.md)
- [x] T003 Create `specs/2533-perf-monitoring/` artifacts. (delivered: specs/2533-perf-monitoring/spec.md)

---

## Phase 2: Foundation

**Purpose**: Keep the package small and align it with the 5-Item Rule.

- [x] T004 Move clock records into `src/utils/performance/recorder.py`. (delivered: src/utils/performance/recorder.py)
- [x] T005 Remove `src/utils/performance/clock.py` so the package has five modules. (delivered: src/utils/performance/clock.py removed)
- [x] T006 Update public imports in `src/utils/performance/__init__.py`. (delivered: src/utils/performance/__init__.py)

---

## Phase 3: User Story 1 - Keep monitoring off by default

**Goal**: A default recorder emits no event.

**Independent Test**: Run the default recorder test in `tests/test_performance_monitoring.py`.

- [x] T007 Verify `RecorderSettings(level="off")` remains the default. (delivered: src/utils/performance/recorder.py)
- [x] T008 Verify the null span reads no clock and emits no event. (delivered: tests/test_performance_monitoring.py)

---

## Phase 4: User Story 2 - Measure one selected boundary

**Goal**: An enabled span records wall time and process CPU time.

**Independent Test**: Run the enabled span test in `tests/test_performance_monitoring.py`.

- [x] T009 Keep wall timing on `time.perf_counter_ns()`. (delivered: src/utils/performance/recorder.py)
- [x] T010 Keep CPU timing on `time.process_time_ns()`. (delivered: src/utils/performance/recorder.py)
- [x] T011 Keep the level gate for event families. (delivered: src/utils/performance/recorder.py)

---

## Phase 5: User Story 3 - Store only safe records

**Goal**: Stored JSON Lines records contain no private values.

**Independent Test**: Run `tests/unit/utils/performance/test_privacy_filter_storage.py`.

- [x] T012 Add deny patterns for secrets, personal data, raw paths, URLs, SQL text, IP addresses, MAC addresses, UUIDs, and tokens. (delivered: src/utils/performance/privacy.py)
- [x] T013 Add fixed allowlists for dimension keys and values. (delivered: src/utils/performance/privacy.py)
- [x] T014 Scrub raw source paths before JSON storage. (delivered: src/utils/performance/event.py)
- [x] T015 Add one storage test for each forbidden data category. (delivered: tests/unit/utils/performance/test_privacy_filter_storage.py)

---

## Phase 6: Validation and delivery

**Purpose**: Prove the change locally and create the pull request.

- [x] T016 Run the local quality gates from the plan.
- [x] T017 Measure the disabled-path cost with `tools/bench_performance_overhead.py`.
- [x] T018 Add the release-note fragment `changelog.d/issue-2533-perf-monitoring.md`.
- [ ] T019 Commit, push, open the pull request, and wait for required checks.

