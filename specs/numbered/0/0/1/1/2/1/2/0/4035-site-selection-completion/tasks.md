# Tasks: Site selection completion

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Inspect current main, issue evidence, and ownership in web_portal/services/operation.py (delivered: design/research.md).

## Phase 2: Foundation

- [x] T002 Define the terminal contract and preserve selector callers in design/contracts/terminal-result.md (delivered: design/contracts/terminal-result.md).

## Phase 3: User Story 1 - Confirm a selected site

**Goal**: Successful menu-92 selection completes without an export.

**Independent test**: Run the actual selector against controlled CSV input and inspect the terminal result.

- [x] T003 [US1] Add failing selection and invalid-result tests (delivered: tests/unit/web_portal/test_portal_silent_completion.py).
- [x] T004 [US1] Interpret only menu 92's nonblank string identifier (delivered: web_portal/services/operation.py).
- [x] T005 [P] [US1] Verify the visible empty-output completion (delivered: tests/e2e/web_portal/test_operation_terminal_reconciliation.py).

## Phase 4: User Story 2 - Preserve other terminal results

**Goal**: Other menus, empty exports, and exceptions retain their behavior.

**Independent test**: Assess silent string returns, explicit empty results, and raised exceptions.

- [x] T006 [US2] Add negative and terminal-state controls (delivered: tests/unit/web_portal/test_portal_silent_completion.py).

## Phase 5: Validation and Documentation

- [x] T007 Record the repair (delivered: changelog.d/issue-4035-site-selection-completion.md).
- [x] T008 Run focused tests and applicable local gates (delivered: design/quickstart.md).
- [x] T009 Analyze spec, plan, tasks, and delivered changes for consistency (delivered: design/checklists/requirements.md).

## Dependencies and Execution Order

T002 requires T001. T003 and T006 require T002. T004 requires the failing T003 regression.
T005 can proceed independently of the unit-test edits after T002.
T007 requires the final behavior. T008 requires T003 through T007. T009 requires T008.

## Parallel Examples

For US1, the browser regression and unit-test edits affect different files.
For US2, existing selector tests can run with the browser regression.
Use one owner for the shared unit-test module.

## Implementation Strategy

Confirm the original failure first. Implement US1 at the existing outcome boundary.
Verify US2 controls before committing the change.
Optional git commit hooks remain deferred until the coherent change passes local gates.
