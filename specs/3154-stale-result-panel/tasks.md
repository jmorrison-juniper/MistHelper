# Tasks: Clear Stale Operation Results

**Input**: Design documents from `specs/3154-stale-result-panel/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui.md, quickstart.md

**Tests**: A browser regression test is required by FR-005.

**Organization**: Tasks are grouped by the single user story.

## Phase 1: Setup

**Purpose**: Prepare a small browser-state repair.

- [X] T001 Review `web_portal/static/js/operations.js` selection and reset functions.
- [X] T002 Review `tests/e2e/test_operation_results_table.py` for an existing result table fixture.

---

## Phase 2: User Story 1 - Select Another Operation (Priority: P1)

**Goal**: Selecting another operation clears stale output without revealing an empty panel.

**Independent Test**: Render a result table, select another operation, and verify that the stale table and file list disappear.

### Tests for User Story 1

- [X] T003 [US1] Add a stale-selection browser test in `tests/e2e/test_operation_results_table.py`.
- [X] T004 [US1] Run the new test against the unmodified code and record the failing result.

### Implementation for User Story 1

- [X] T005 [US1] Add a clear-only helper in `web_portal/static/js/operations.js`.
- [X] T006 [US1] Call the clear-only helper from `selectOperation()` in `web_portal/static/js/operations.js`.
- [X] T007 [US1] Keep `resetExecutionPanel()` as the reveal-and-clear helper in `web_portal/static/js/operations.js`.
- [X] T008 [US1] Run the browser test again and record the passing result.

---

## Phase 3: Polish

**Purpose**: Prepare the pull request.

- [X] T009 Add `changelog.d/issue-3154-stale-result-panel.md`.
- [X] T010 Run the targeted quality gates from `quickstart.md`.
- [X] T011 Verify the local portal on port 9602 and capture before-and-after screenshots when live credentials permit the run.

## Dependencies & Execution Order

T001 and T002 precede all other work. T003 must run before T005 so the guard can fail first. T005 through T007 precede T008. T009 through T011 close the work.

## Parallel Opportunities

T001 and T002 can run in parallel. No implementation tasks should run in parallel because they touch the same JavaScript behavior.

## Implementation Strategy

Deliver the test first, confirm that it fails, implement the small JavaScript split, and rerun the same test.


