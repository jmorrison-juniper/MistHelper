# Tasks: Licensing comparison layout

## Phase 1: Setup

- [X] T001 Inspect issue #4258, source screenshot, hooks, ownership, and current prerequisites in `.specify/extensions.yml`.
- [X] T002 Create the focused specification and design in `specs/numbered/0/0/1/1/4/0/1/3/4258-licensing-comparison-layout/`.

## Phase 2: Foundation

- [X] T003 Analyze requirement, plan, and task coverage in `design/analysis.md`.
- [X] T004 Configure shared-shell rendering in `tests/e2e/web_portal/licensing_comparison/conftest.py` and `test_session_state.py`.

## Phase 3: User Story 1

**Goal**: Restore readable comparisons in the shared shell.
**Independent test**: Compare synthetic organizations and verify numeric columns, descriptions, totals, shell, and narrow layout.

- [X] T005 [US1] Add failing layout, numeric, missing-data, and escaped-value browser cases in `tests/e2e/web_portal/licensing_comparison/test_layout.py`.
- [X] T006 [US1] Extend the shared shell and restore panel order in `src/interfaces/portals/licensing_comparison/templates/licensing_comparison.html`.
- [X] T007 [P] [US1] Scope charcoal and magenta responsive styles in `src/interfaces/portals/licensing_comparison/static/licensing_comparison.css`.
- [X] T008 [US1] Add checkbox discovery, refresh, numeric columns, descriptions, totals, and summary cards in `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`. An absent count remains `Unavailable`, not zero.

## Phase 4: User Story 2

**Goal**: Preserve adjustment and export workflows without JSON entry.
**Independent test**: Enter numeric manual values and purchases, reload, compare, remove, and export.

- [X] T009 [US2] Update persistence tests and add purchase, bundle, invalid-input, refresh, and export cases in `tests/e2e/web_portal/licensing_comparison/test_session_state.py` and `test_layout.py`.
- [X] T010 [US2] Connect numeric manual and purchase controls, balance labels, validation, and stale-purchase filtering in `src/interfaces/portals/licensing_comparison/static/licensing_comparison.js`.

## Phase 5: Validation and Delivery

- [X] T011 Run focused integration, browser, and applicable quality gates for `tests/e2e/web_portal/licensing_comparison/`. Preserve screenshots in `test-artifacts/`.
- [X] T012 Add `changelog.d/issue-4258-licensing-comparison-layout.md` and complete the final coverage analysis in `design/analysis.md`.

## Required Delivery Actions

These lifecycle actions remain mandatory and are recorded in the pull request, outside the implementation checkbox count.

Commit explicit feature paths, run the committed test-quality ratchet, push, and create the template-based pull request for issue #4258.
Watch required checks and CodeQL, then merge only after all checks pass.
Record the merge result or precise blocker in the pull request and final report.

## Dependencies and Parallel Work

T001 precedes T002. T002 precedes T003 and T004.
T004 and T005 precede the UI implementation.
T006 precedes T008. T007 can run independently after T005.
T009 precedes T010. T008 and T010 precede T011.
T011 and T012 precede the required delivery actions.
US2 shares rendering and input code with US1 and follows it.

## Implementation Strategy

First restore the shell and numeric comparison for US1.
Then restore numeric adjustments and export for US2.
Keep the existing backend contracts and use offline evidence before delivery.
