---

description: "Implementation tasks for issue #4026 executor initialization synchronization"

---

# Tasks: Operations Portal Concurrent Load

**Input**: Design documents in `specs/numbered/0/0/1/1/2/1/0/1/4026-operations-portal-concurrent-load/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/executor-initialization.md`, and `quickstart.md`

**Tests**: The specification requires one deterministic forced-race unit test. The test must fail before the product repair and pass after it.

**Scope**: Change only `web_portal/routes/operations.py`, `tests/unit/web_portal/test_operation_executor_concurrency.py`, and `changelog.d/issue-4026-operation-executor-race.md`. Do not modify `web_portal/services/operation.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel after its stated prerequisites complete.
- **[Story]**: The task maps to a user story from `spec.md`.
- Tick a task only after its command or file result is verified.

## Phase 1: Setup and Scope Control

**Purpose**: Confirm the narrow file boundary before implementation.

- [x] T001 Review `specs/numbered/0/0/1/1/2/1/0/1/4026-operations-portal-concurrent-load/plan.md`, `spec.md`, `contracts/executor-initialization.md`, and `quickstart.md` before editing.
- [x] T002 Capture the pre-change diff for `web_portal/routes/operations.py` and confirm that `web_portal/services/operation.py` has no issue #4026 change.

**Checkpoint**: The implementation file set contains one route module, one existing unit-test module, and one new changelog fragment.

---

## Phase 2: Foundational Test Design

**Purpose**: Define the deterministic race boundary that blocks product implementation.

**Critical rule**: Complete the red test run before any edit to `web_portal/routes/operations.py`.

- [x] T003 Define the controlled configuration mapping, first-read barrier, fake executor constructor, concurrent caller count, and fixed completion timeout in `tests/unit/web_portal/test_operation_executor_concurrency.py`.

**Checkpoint**: The test design forces every caller to observe the initial empty executor slot before any constructor can complete.

---

## Phase 3: User Story 1 - Start Concurrent Portal Requests Safely (Priority: P1) MVP

**Goal**: Concurrent first callers construct one executor and receive the same stored object.

**Independent Test**: Run the forced race with at least two callers. Verify one constructor call, one stored marker, identity equality for every result, and zero extra construction on a later accessor call.

### Tests for User Story 1

- [x] T004 [US1] Add `test_get_executor_constructs_once_under_forced_race` to `tests/unit/web_portal/test_operation_executor_concurrency.py` with controlled `current_app.config` reads, one barrier, a fake constructor, concurrent callers, and fixed timeouts.
- [x] T005 [US1] Run `python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py::test_get_executor_constructs_once_under_forced_race -q` before the product edit and record the expected failure caused by multiple constructor calls.

### Implementation for User Story 1

- [x] T006 [US1] Add one private module-level `threading.Lock` and double-checked lazy executor initialization in `web_portal/routes/operations.py`, with the existing constructor arguments unchanged.
- [x] T007 [US1] Run `python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py::test_get_executor_constructs_once_under_forced_race -q` after T006 and verify that the same test passes.
- [x] T008 [US1] Run `python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py -q` and verify that the full concurrency module passes without leaked worker pools or threads.

**Checkpoint**: The unsynchronized implementation has a recorded red result, and the synchronized implementation has a green result.

---

## Phase 4: User Story 2 - Preserve Existing Operations Routes (Priority: P2)

**Goal**: Preserve all unrelated routes, including the account-aware MSP selector from PR #4065.

**Independent Test**: Verify that `list_msps` is unchanged, the selector tests pass, and no file under `web_portal/services/` changes.

- [x] T009 [P] [US2] Run `python -m pytest tests/unit/web_portal/test_operations_msp_selector.py -q` and verify the existing `list_msps` response contract in `web_portal/routes/operations.py`.
- [x] T010 [P] [US2] Inspect `git diff -- web_portal/routes/operations.py web_portal/services/operation.py` and verify that only the import, lock declaration, and `_get_executor()` changed in the route module.

**Checkpoint**: PR #4065 route lines remain unchanged, and `web_portal/services/operation.py` has no diff.

---

## Phase 5: Release Note and Required Validation

**Purpose**: Add the issue record and run every required local check.

- [x] T011 Add `changelog.d/issue-4026-operation-executor-race.md` with one `###` heading and one `Fixed` bullet that names issue #4026.
- [x] T012 [P] Run `python -m py_compile web_portal/routes/operations.py` and verify that the command produces no error.
- [x] T013 [P] Run `python -m ruff check .` and verify the full repository reports `All checks passed`.
- [x] T014 [P] Run `python -m black --check .` and verify that no repository file needs formatting.
- [x] T015 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` and verify the required test-quality inputs.
- [x] T016 After the implementation commit, run `git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"` and `git rev-parse --verify "origin/main^{commit}"` for the test-quality base.
- [x] T017 Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` and verify `gate: 0 new findings vs baseline`.
- [x] T018 Run `git diff --name-only origin/main...HEAD` and `git status --short`, then verify that issue #4026 adds no implementation change outside `web_portal/routes/operations.py`, `tests/unit/web_portal/test_operation_executor_concurrency.py`, and `changelog.d/issue-4026-operation-executor-race.md`.

**Checkpoint**: The focused tests, preservation test, syntax check, full Ruff check, full Black check, test-quality checks, and scope check pass.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately and fixes the scope boundary.
- **Phase 2**: Depends on Phase 1 and defines the forced-race test design.
- **Phase 3**: Depends on Phase 2. T005 must fail before T006 starts. T007 and T008 depend on T006.
- **Phase 4**: Depends on T006 and can run after the synchronized accessor exists.
- **Phase 5**: T011 depends on the completed repair. T012 through T015 depend on the final working-tree content. T016 and T017 require the implementation commit. T018 is the final scope check.

### User Story Dependencies

- **User Story 1 (P1)**: Has no dependency on another user story and is the MVP.
- **User Story 2 (P2)**: Depends on the narrow User Story 1 route edit and verifies preservation only.

### Required Red-Before-Green Order

1. Complete T004.
2. Run T005 and record the expected failure.
3. Complete T006.
4. Run T007 and record the passing result.
5. Run T008 to verify the full test module.

### Parallel Opportunities

- T009 and T010 can run in parallel after T006 because they are read-only preservation checks.
- T012, T013, and T014 can run in parallel after T011 because they are independent read-only validation commands.
- No implementation task can run in parallel with T004 through T007 because the red-before-green evidence requires strict order.

---

## Parallel Example: User Story 2

```text
Task: "Run the MSP selector tests in tests/unit/web_portal/test_operations_msp_selector.py."
Task: "Inspect the route and service diffs for web_portal/routes/operations.py and web_portal/services/operation.py."
```

---

## Implementation Strategy

### MVP First

1. Complete Phases 1 and 2.
2. Add the forced-race test in T004.
3. Record the required red result in T005.
4. Implement only the module lock and double-check sequence in T006.
5. Record the green results in T007 and T008.

### Incremental Delivery

1. Deliver User Story 1 as the concurrency repair.
2. Verify User Story 2 without changing its route behavior.
3. Add the issue-specific changelog fragment.
4. Run all required validation commands.
5. Stop if any changed file falls outside the declared scope.

## Notes

- Do not modify `web_portal/services/operation.py`.
- Do not add another executor accessor, wrapper, alias, lock, or synchronization primitive.
- Do not use sleeps to force the race.
- Do not create a real `OperationExecutor` worker pool in the regression test.
- Preserve constructor exceptions and leave the configuration slot empty when construction fails.
