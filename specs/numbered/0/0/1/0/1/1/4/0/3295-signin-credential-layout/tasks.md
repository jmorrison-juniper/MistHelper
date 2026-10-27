# Tasks: Sign-in Credential Layout

**Input**: [spec.md](spec.md), [plan.md](plan.md), and supporting documents under `design/`.

**Prerequisites**: `.venv` from `scripts/bootstrap_worktree.py` and the existing browser fixture.

## Phase 1: Setup

- [x] T001 Verify the sign-in fixture and credential-mode identifiers in `tests/e2e/upgrade_portal/test_signin.py` (delivered: `tests/e2e/upgrade_portal/test_signin.py`).

## Phase 2: Foundational

No shared foundation changes are required.

## Phase 3: User Story 1 - Choose a sign-in method (Priority: P1)

**Goal**: Show the correct credential controls for each mode and present warning prefixes with equal weight.

**Independent Test**: Run `python -m pytest tests/e2e/upgrade_portal/test_signin.py`.

### Tests

- [x] T002 [US1] Add browser assertions for label position, inactive mode state, keyboard access, and warning-prefix weight in `tests/e2e/upgrade_portal/test_signin.py` (delivered: `tests/e2e/upgrade_portal/test_signin.py`).

### Implementation

- [x] T003 [P] [US1] Move the token label, field, and note into a separate group in `src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html` (delivered: `src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html`).
- [x] T004 [P] [US1] Toggle token-group visibility and field disabled state in `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js` (delivered: `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js`).
- [x] T005 [P] [US1] Match sign-in warning-prefix weight with the error-page prefix in `src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css` (delivered: `src/interfaces/portals/upgrade_portal/app/assets/static/css/portal.css`).
- [x] T006 [P] [US1] Add the issue release note in `changelog.d/issue-3295-signin-credential-layout.md` (delivered: `changelog.d/issue-3295-signin-credential-layout.md`).
- [x] T007 [US1] Run focused browser, JavaScript syntax, lint, and format checks for `tests/e2e/upgrade_portal/` and `src/interfaces/portals/upgrade_portal/app/assets/static/js/portal.js` (39 tests passed; syntax, Ruff, and Black passed).
- [x] T008 [US1] Run STE and Markdown link checks for `changelog.d/issue-3295-signin-credential-layout.md` and `specs/numbered/0/0/1/0/1/1/4/0/3295-signin-credential-layout/` (9 files scanned; 0 broken links; STE scores 87-98).
- [x] T009 [US1] Run the configured test-quality gate after adding regressions in `tests/e2e/upgrade_portal/test_signin.py` (1198 files and 632 findings checked; 0 new findings; 0 parse errors).

## Dependencies & Execution Order

- T001 verifies the existing fixture before test work.
- T002 must fail before T003 through T005 begin.
- T003 through T006 use separate files and may run in parallel after T002.
- T007 depends on T002 through T005.
- T008 depends on T006 and the feature documents.
- T009 depends on T002.

## Parallel Execution

After the regression tests fail, implementation tasks T003, T004, T005, and T006 have no shared file dependencies.

## Implementation Strategy

Deliver the single P1 story. Keep server authentication behavior unchanged. Verify the layout and mode transitions in the browser before completing the issue.
