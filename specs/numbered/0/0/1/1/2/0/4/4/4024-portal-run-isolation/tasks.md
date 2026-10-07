---

description: "Dependency-ordered tasks for issue #4024 portal run evidence isolation"
---

# Tasks: Portal Run Evidence Isolation

**Input**: Design documents from `specs/numbered/0/0/1/1/2/0/4/4/4024-portal-run-isolation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/run-evidence-isolation.md`, and `quickstart.md`

**Tests**: This feature requires test-first unit, executor integration, and result-selection coverage.

**Managed file carve-out**: Do not edit, reformat, or reorder `PARAMETER_REGISTRY` in `web_portal/services/operation.py`.

**Product scope**: Change only the `_RunLogHandler` run-evidence region in `web_portal/services/operation.py` and `web_portal/services/output_scan.py`.

**Compatibility guard**: Preserve `HANDLED_ERROR_MARKERS`, `_handled_error_reason()`, `_finish_successful_operation()`, and upstream error versus genuine no-data classification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it changes a different file and has no incomplete dependency.
- **[Story]**: The task maps to one user story from `spec.md`.
- Write each test before its product change, and confirm that the test fails for the expected reason.

## Phase 1: Setup and Baseline

**Purpose**: Confirm the current behavior and protect the managed file carve-out.

- [x] T001 Run the existing focused baseline in `tests/unit/test_operation_output_file_discovery.py`, `tests/unit/web_portal/test_output_scan_runtime_files.py`, `tests/unit/web_portal/test_output_scan_clock_race.py`, `tests/unit/web_portal/test_portal_log_routing.py`, `tests/unit/web_portal/test_operation_run_registry_caps.py`, `tests/unit/web_portal/test_operation_output_files_cap.py`, `tests/unit/web_portal/test_event_bus.py`, `tests/unit/web_portal/test_event_bus_deadlock.py`, and `tests/unit/web_portal/test_portal_silent_completion.py`
- [x] T002 Record the pre-change `PARAMETER_REGISTRY` region and protected completion symbols with `symbol-diff` and a focused diff check for `web_portal/services/operation.py`

---

## Phase 2: Foundational Ownership Test Harness

**Purpose**: Add shared synchronization and evidence helpers before any product change.

**Critical**: Complete this phase before the user story phases.

- [x] T003 Create synchronized executor fixtures with `threading.Barrier`, `threading.Event`, distinct safe menu handlers, per-run event subscribers, and deterministic file roots in `tests/unit/web_portal/test_portal_run_isolation.py`
- [x] T004 Add shared assertions for foreign logs, debug logs, output files, discard counts, completion state, and event payload `run_id` values in `tests/unit/web_portal/test_portal_run_isolation.py`

**Checkpoint**: The shared test harness can prove overlap without sleeps.

---

## Phase 3: User Story 1 - Trust Each Concurrent Run Record (Priority: P1) - MVP

**Goal**: Store and publish only the log evidence from the worker that owns one run.

**Independent Test**: Start two synchronized operations and confirm that each run and subscriber receives only its owner logs, debug logs, and discard count.

### Tests for User Story 1

- [x] T005 [P] [US1] Add `_RunLogHandler` owner-thread acceptance and foreign-thread rejection unit tests in `tests/unit/web_portal/test_portal_log_routing.py`
- [x] T006 [P] [US1] Add a two-subscriber run filter test for distinct `run_id` values in `tests/unit/web_portal/test_event_bus.py`
- [x] T007 [P] [US1] Add concurrent bounded-log tests that overflow one run by seven entries and keep the other run at zero discards in `tests/unit/web_portal/test_operation_run_registry_caps.py`
- [x] T008 [US1] Add a 100-repetition synchronized executor test for isolated main logs, debug logs, discard counts, and SSE events in `tests/unit/web_portal/test_portal_run_isolation.py`

### Implementation for User Story 1

- [x] T009 [US1] Capture one stable worker thread identifier and pass it to the run log handler in the `_capture_and_run` region of `web_portal/services/operation.py`
- [x] T010 [US1] Reject foreign `LogRecord.thread` values before formatting, storage, file extraction, discard counting, or SSE publication in the `_RunLogHandler` region of `web_portal/services/operation.py`
- [x] T011 [US1] Run the User Story 1 tests in `tests/unit/web_portal/test_portal_log_routing.py`, `tests/unit/web_portal/test_operation_run_registry_caps.py`, `tests/unit/web_portal/test_event_bus.py`, and `tests/unit/web_portal/test_portal_run_isolation.py`

**Checkpoint**: Concurrent run records and live event streams contain no foreign log evidence.

---

## Phase 4: User Story 2 - Preview the Correct Operation Result (Priority: P1)

**Goal**: Attribute tracked files to one owner and select only that run's previewable result.

**Independent Test**: Run two overlapping operations with distinct result and cache files, then confirm that each run lists and previews only its own result.

### Tests for User Story 2

- [x] T012 [P] [US2] Add scanner unit tests for distinct owners, ownerless child-thread writes, shared-path ambiguity, and overlap-disabled timestamp fallback in `tests/unit/web_portal/test_output_scan_runtime_files.py`
- [x] T013 [P] [US2] Add single-scanner regression tests for new-file fallback, in-place rewrite fallback, runtime-file exclusions, and clock boundaries in `tests/unit/web_portal/test_output_scan_runtime_files.py` and `tests/unit/web_portal/test_output_scan_clock_race.py`
- [x] T014 [P] [US2] Add result-selection tests for owned result ordering, prompt-cache ordering, ambiguous file exclusion, and first previewable output in `tests/unit/test_operation_output_file_discovery.py`
- [x] T015 [P] [US2] Add completion tests that distinguish upstream handled errors, genuine no-data results, and foreign-only evidence in `tests/unit/web_portal/test_portal_silent_completion.py`
- [x] T016 [US2] Add synchronized executor tests for distinct tracked files, ambiguous shared paths, ownerless files, and first previewable results in `tests/unit/web_portal/test_portal_run_isolation.py`

### Implementation for User Story 2

- [x] T017 [US2] Change the active scanner collection to one owner-keyed registry with duplicate-owner rejection in `web_portal/services/output_scan.py`
- [x] T018 [US2] Attribute writable `builtins.open` and `Path.open` calls only to the scanner for the calling thread in `web_portal/services/output_scan.py`
- [x] T019 [US2] Mark paths tracked by multiple active owners as ambiguous and exclude them from `_changed_tracked_files` in `web_portal/services/output_scan.py`
- [x] T020 [US2] Make any scanner that overlaps another scanner permanently ineligible for directory-mark and full-walk fallback in `web_portal/services/output_scan.py`
- [x] T021 [US2] Pass the stable worker owner to `OutputFileScanner` and merge only scanner-approved names in the `_capture_and_run` run-evidence region of `web_portal/services/operation.py`
- [x] T022 [US2] Verify that `HANDLED_ERROR_MARKERS`, `_handled_error_reason()`, `_finish_successful_operation()`, and no-data classification remain unchanged in `web_portal/services/operation.py`
- [x] T023 [US2] Run the User Story 2 tests in `tests/unit/web_portal/test_output_scan_runtime_files.py`, `tests/unit/web_portal/test_output_scan_clock_race.py`, `tests/unit/test_operation_output_file_discovery.py`, `tests/unit/web_portal/test_portal_silent_completion.py`, and `tests/unit/web_portal/test_portal_run_isolation.py`

**Checkpoint**: Foreign, ownerless, and ambiguous files cannot become output or completion evidence.

---

## Phase 5: User Story 3 - Preserve Concurrency and Scanner Lifecycle (Priority: P2)

**Goal**: Keep independent operations concurrent and restore process hooks after the final scanner stops.

**Independent Test**: Hold two workers in one overlap, release them in both orders, and repeat with each worker failing first.

### Tests for User Story 3

- [x] T024 [P] [US3] Add scanner lifecycle tests for both stop orders, exact hook identity restoration, and tracking continuity after the first stop in `tests/unit/web_portal/test_output_scan_runtime_files.py`
- [x] T025 [US3] Add executor integration tests for simultaneous worker activity, both completion orders, each failure order, and remaining-worker evidence in `tests/unit/web_portal/test_portal_run_isolation.py`

### Implementation for User Story 3

- [x] T026 [US3] Keep file hooks installed until the owner registry is empty and restore the exact saved hook objects in `web_portal/services/output_scan.py`
- [x] T027 [US3] Remove handler and scanner ownership on normal return and exceptions without adding a global operation lock in the `_capture_and_run` run-evidence region of `web_portal/services/operation.py`
- [x] T028 [US3] Run the User Story 3 tests in `tests/unit/web_portal/test_output_scan_runtime_files.py` and `tests/unit/web_portal/test_portal_run_isolation.py`

**Checkpoint**: Both workers overlap, either worker can finish first, and no process hook remains after the final cleanup.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Publish the change record and run every applicable validation gate.

- [x] T029 [P] Add the issue #4024 fixed-entry release note in `changelog.d/issue-4024-portal-run-isolation.md`
- [x] T030 Confirm that the final diff changes no product file outside `web_portal/services/operation.py` and `web_portal/services/output_scan.py`, and confirm that `PARAMETER_REGISTRY` is byte-for-byte unchanged in `web_portal/services/operation.py`
- [ ] T031 Run `python -m py_compile MistHelper.py`, `python -m ruff check .`, and `python -m black --check .` for the repository
- [x] T032 Run the focused unit and executor integration command from `specs/numbered/0/0/1/1/2/0/4/4/4024-portal-run-isolation/quickstart.md`
- [x] T033 Run the result-selection browser workflow with `python -m pytest tests/e2e/web_portal/test_operations_panel_workflow.py -q`
- [ ] T034 Run `radon cc web_portal/services/operation.py web_portal/services/output_scan.py -j | complexity-gate --max 10` and `symbol-diff --base origin/main` for both product files
- [ ] T035 Run `bandit-exclude-check`, `python -m bandit -c pyproject.toml -r .`, `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`, `pydocstyle src/ wsgi.py web_portal`, and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v`
- [ ] T036 Run the live test-quality preflight and changed-test gate from `specs/numbered/0/0/1/1/2/0/4/4/4024-portal-run-isolation/quickstart.md` after the implementation commit
- [ ] T037 Run both `pytest-chunks` commands from `.github/copilot-instructions.md`, then run the full test-quality gate before the push

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on Phase 1 and blocks all user story implementation.
- **User Story 1** depends on Phase 2.
- **User Story 2** depends on Phase 2 and must retain the worker owner contract from User Story 1.
- **User Story 3** depends on the scanner ownership work in User Story 2.
- **Phase 6** depends on each selected user story.

### Task Dependencies

- T003 depends on T001.
- T004 depends on T003.
- T009 and T010 depend on T005 through T008.
- T011 depends on T009 and T010.
- T017 through T021 depend on T012 through T016.
- T022 depends on T021.
- T023 depends on T017 through T022.
- T026 and T027 depend on T024 and T025.
- T028 depends on T026 and T027.
- T030 depends on T009, T010, T017 through T022, T026, and T027.
- T031 through T037 depend on T028 through T030.

### User Story Dependencies

- **User Story 1 (P1)**: Delivers log and event isolation after the shared harness is ready.
- **User Story 2 (P1)**: Delivers file ownership and result selection. It reuses the stable worker owner from User Story 1.
- **User Story 3 (P2)**: Delivers lifecycle safety after scanner ownership exists.

### Parallel Opportunities

- T005, T006, and T007 can run in parallel.
- T012, T013, T014, and T015 can run in parallel.
- T024 can run while T025 extends the separate executor integration module.
- T029 can run after the behavior is final while the focused validation starts.

---

## Parallel Example: User Story 1

```text
Task T005: Add owner-thread handler tests in tests/unit/web_portal/test_portal_log_routing.py.
Task T006: Add two-run subscriber filtering in tests/unit/web_portal/test_event_bus.py.
Task T007: Add per-run discard tests in tests/unit/web_portal/test_operation_run_registry_caps.py.
```

## Parallel Example: User Story 2

```text
Task T012: Add overlap ownership tests in tests/unit/web_portal/test_output_scan_runtime_files.py.
Task T014: Add result ordering tests in tests/unit/test_operation_output_file_discovery.py.
Task T015: Add completion classification tests in tests/unit/web_portal/test_portal_silent_completion.py.
```

## Parallel Example: User Story 3

```text
Task T024: Add hook lifecycle tests in tests/unit/web_portal/test_output_scan_runtime_files.py.
Task T025: Add executor completion-order tests in tests/unit/web_portal/test_portal_run_isolation.py.
```

---

## Implementation Strategy

### MVP First

1. Complete Phases 1 and 2.
2. Complete User Story 1.
3. Run T011 and confirm zero foreign log evidence.
4. Continue to User Story 2 before release, because file evidence remains unsafe without it.

### Incremental Delivery

1. Add deterministic overlap tests before each product change.
2. Isolate log evidence.
3. Isolate tracked file evidence and preserve single-run fallback.
4. Prove hook lifecycle and both completion orders.
5. Add the changelog fragment and run all gates.

### Scope Controls

- Do not edit `PARAMETER_REGISTRY`.
- Do not change public response or SSE shapes.
- Do not change the shared `data/` directory.
- Do not add a global operation lock.
- Do not change `HANDLED_ERROR_MARKERS`, `_handled_error_reason()`, or `_finish_successful_operation()`.
- Do not use mypy or repository coverage as proof for `web_portal`, because current CI does not measure that scope.

## Notes

- Each story test must fail before its product task starts.
- Keep all log and output stores bounded.
- Use `pathlib.Path` for path validation.
- Preserve exact hook objects after the final scanner stops.
- Keep upstream errors distinct from genuine no-data completion.
