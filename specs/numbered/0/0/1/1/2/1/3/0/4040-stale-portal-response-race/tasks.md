# Tasks: Stale Portal Response Ownership

**Input**: Design documents in `specs/numbered/0/0/1/1/2/1/3/0/4040-stale-portal-response-race/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `quickstart.md`

**Organization**: Tasks follow the independent user story in `spec.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Tasks can run in parallel because they use different files.
- **[Story]**: The task belongs to the named user story.
- Use the exact file path in each task.

## Phase 1: Setup

**Purpose**: Prepare the local browser-test environment.

- [x] T001 Build the local browser-test environment with `scripts/bootstrap_worktree.py`.

## Phase 2: Foundational

**Purpose**: Reuse the existing portal and browser-test infrastructure.

No shared infrastructure changes are required.

## Phase 3: User Story 1 - Keep guidance with the selected operation (Priority: P1)

**Goal**: Keep every parameter result with the operation that still owns the page.

**Independent Test**: Delay the menu 241 response, select menu 242, then verify that the title remains Menu 242 and the SSH-only warning stays hidden.

### Tests for User Story 1

- [x] T002 [US1] Add browser checks for delayed success, delayed failure, and the current menu 241 warning in `tests/e2e/web_portal/test_web_interactivity_quickstart.py`. Confirm that the delayed-success case fails before the repair.

### Implementation for User Story 1

- [x] T003 [US1] Ignore a stale parameter success and failure before either path changes page state in `web_portal/static/js/operations.js`.
- [x] T004 [P] [US1] Add the issue 4040 release note in `changelog.d/issue-4040-stale-portal-response-race.md`.
- [x] T005 [US1] Run the browser regression in `tests/e2e/web_portal/test_web_interactivity_quickstart.py`.

**Checkpoint**: The delayed menu 241 response cannot change menu 242, and menu 241 still shows its warning while selected.

## Phase 4: Polish and Cross-Cutting Checks

**Purpose**: Check the feature files and record the verified result.

- [x] T006 Run Ruff and Black checks for `tests/e2e/web_portal/test_web_interactivity_quickstart.py`.
- [x] T007 Run `tests/guardrails/test_spec_route_contract.py` and verify the issue 4040 route.

## Dependencies and Execution Order

### Phase Dependencies

- Setup must finish before browser testing.
- The foundational phase needs no code changes.
- The user story depends on the test environment.
- Polish checks depend on the user story implementation.

### User Story Dependencies

- User Story 1 is the only story. It delivers the complete fix and has no dependency on another story.

### Within User Story 1

- Add and fail the browser regression before changing the controller.
- Add the release note in parallel with the regression and controller change.
- Run the browser regression after the controller change.

## Parallel Opportunities

- T004 can run in parallel with T002 and T003 because it edits a separate file.
- T006 and T007 can run in parallel after the feature files are complete.

## Parallel Example: User Story 1

```text
Task: Add regression checks in tests/e2e/web_portal/test_web_interactivity_quickstart.py
Task: Add the issue 4040 fragment in changelog.d/issue-4040-stale-portal-response-race.md
```

## Implementation Strategy

### MVP First

1. Prepare the browser-test environment.
2. Add the delayed-response regression and confirm that it fails.
3. Guard both completion paths.
4. Run the browser test and the focused file checks.

### Incremental Delivery

User Story 1 is the complete feature. Do not add another operation, API request, or deployment step.

## Notes

- Every task names its target file or setup script.
- No live Mist operation is part of this feature.
