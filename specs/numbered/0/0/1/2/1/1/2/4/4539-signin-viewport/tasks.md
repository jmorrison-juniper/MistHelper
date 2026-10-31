# Tasks: Sign-in viewport fit

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Prepare the local browser environment through `scripts/bootstrap_worktree.py`. (delivered: design/quickstart.md)

## Phase 2: Foundational

- [x] T002 Confirm CSS ownership and reproduce the reported journey in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`. (delivered: design/research.md)

## Phase 3: User Story 1 - Read the complete sign-in page

**Goal**: Fit the sign-in page without hiding service details.
**Independent Test**: Run the reported journey at both existing viewport sizes.

- [x] T003 [US1] Strengthen width diagnostics and signed-out checks in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`. (delivered: tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py)
- [x] T004 [US1] Permit dependency address wrapping in `src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css`. (delivered: src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css)

## Phase 4: Polish

- [x] T005 Add `changelog.d/issue-4539-upgrade-portal-sign-in-overflow.md`. (delivered: changelog.d/issue-4539-upgrade-portal-sign-in-overflow.md)
- [x] T006 Run the focused browser journey and relevant gates from `design/quickstart.md`. (delivered: design/quickstart.md)
- [x] T007 Analyze requirement coverage across `spec.md`, `plan.md`, and `tasks.md`. (delivered: tasks.md)

## Dependencies & Execution Order

T001 precedes T002. T002 precedes T003. T003 precedes T004.
T004 and T005 precede T006. T006 precedes T007.

## Parallel Example: User Story 1

The independent release note T005 can run during browser validation.
The regression and CSS changes remain sequential to prove the test fails before the repair.

## Implementation Strategy

Complete the single story without changing other portal behavior.
Retain the complete viewport page loop and validate the test before and after the CSS repair.

## Verification record

The strengthened regression failed before the CSS repair with a 400-pixel document at a 390-pixel viewport.
After the repair, the document and viewport widths match at 390 and 1024 pixels.
The focused journey passes. The related sign-in, theme, and structure selection reports 64 passing tests.
Ruff, Black, compilation, symbol preservation, and STE checks pass.
The test-quality input preflight passes. The precommit journey-tree analyzer checks five files and reports zero new findings.
The committed-difference gate runs after the local commit.

An additional mypy check reports one existing `no-any-return` error.
The same error exists on `origin/main`, and this test is outside the configured CI type-check paths.
No unrelated repair is included.

## Specification analysis

All four functional requirements map to tasks. FR-001 and FR-002 map to T003, T004, and T006.
FR-003 maps to T003 and T006. FR-004 maps to T002 and the scoped changed-file review.
No requirement gap, unresolved ambiguity, or duplicate requirement remains.
The existing long journey remains unchanged except for the scoped assertions described in the plan.

All optional commit hooks ran with their repository configuration disabled.
Disabled companion hooks did not run.
The user prohibited publication, merging, and live deployment, so those pipeline steps remain outside this task.
The design hook reported existing card accents outside the changed selector.
These existing status accents are not part of the address-wrap defect, so the repair leaves them unchanged.
