# Tasks: Cache generator error reporting

**Input**: [Specification](spec.md) and [plan](plan.md).
**Prerequisites**: `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.
**Tests**: Required. Use mocked callbacks only.

## Phase 1: Setup

- [x] T001 Verify source ownership and prepare the environment with scripts/bootstrap_worktree.py. (delivered: scripts/bootstrap_worktree.py)

## Phase 2: Foundational

- [x] T002 Record the existing boundary and bounded scope in plan.md. (delivered: plan.md)

## Phase 3: User Story 1 - Diagnose a generation failure (Priority: P1)

**Goal**: Preserve failure context and traceback.
**Independent Test**: Inspect the error record and boolean result.

- [x] T003 [US1] Add mocked failure and success assertions and demonstrate four missing-traceback failures. (delivered: tests/unit/cache/test_cache_utils.py)
- [x] T004 [US1] Preserve the active traceback without changing the boundary or message. (delivered: src/foundation/persistence/cache/cache_utils.py)
- [x] T005 [US1] Test failure reporting through the public cache dispatcher. (delivered: tests/unit/cache/test_cache_utils.py)

## Phase 4: User Story 2 - Stop generation safely (Priority: P2)

**Goal**: Preserve interrupt and exit propagation.
**Independent Test**: Assert the original exception instance reaches the caller without completion messages.

- [x] T006 [US2] Add keyboard interrupt and process exit cases for both entry points. (delivered: tests/unit/cache/test_cache_utils.py)

## Phase 5: Polish and Cross-Cutting Concerns

- [x] T007 Add the release fragment. (delivered: changelog.d/issue-1794-cache-generator-errors.md)
- [x] T008 Run the focused gates and record consistency findings. (delivered: analysis.md)

## Dependencies and Execution Order

T002 depends on T001. T003 depends on T002. T004 depends on T003.
T005 and T006 depend on T004. T007 depends on T004.
T008 depends on T005, T006, and T007.
US2 has no behavioral dependency on US1 but uses the same test file.

## Parallel Examples

For US1, source inspection and test planning can occur independently before edits.
For US2, interrupt validation can run with US1 success validation after test edits.
Do not edit the shared test file concurrently.
Documentation checks and source checks can run independently.

## Implementation Strategy

Complete US1 first and prove the traceback regression.
Complete US2 next, then run all focused checks and create one local commit.
Optional commit hooks remain deferred. Disabled companion hooks do not execute.
