# Tasks: Sign-In Narrow Viewport Layout

**Input**: Numeric record at `/specs/numbered/0/0/1/2/1/1/2/4/4539-fix-signin-overflow/`.

**Prerequisites**: `plan.md`, `spec.md`, and supporting documents under `design/`.

**Tests**: The specification and issue require a browser regression test.

## Phase 1: Setup

**Purpose**: Confirm the local browser test environment.

- [X] T001 Confirm Chromium and the isolated portal fixtures in `tests/e2e/upgrade_portal/conftest.py`. (delivered: `tests/e2e/upgrade_portal/conftest.py`)

## Phase 2: Foundational

**Purpose**: Shared infrastructure is already present.

No foundational changes are required.

## Phase 3: User Story 1 - Sign in on a narrow screen (Priority: P1)

**Goal**: Keep the sign-in page usable at 390 pixels without horizontal document scrolling.

**Independent Test**: At 390 by 844 pixels, verify that the document width does not exceed the viewport width and that all sign-in controls remain usable.

### Tests for User Story 1

- [X] T002 [US1] Remove the strict expected-failure marker from the 390-pixel test in `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`. (delivered: `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`)

### Implementation for User Story 1

- [X] T003 [US1] Put the service table in the existing scroll box in `src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html`. (delivered: `src/interfaces/portals/upgrade_portal/app/assets/templates/auth/signin.html`)
- [X] T004 [P] [US1] Add the issue-specific release note in `changelog.d/issue-4539-signin-overflow.md`. (delivered: `changelog.d/issue-4539-signin-overflow.md`)
- [X] T005 [US1] Run the sign-in and viewport Chromium tests in `tests/e2e/upgrade_portal/test_signin.py` and `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`. (delivered: `tests/e2e/upgrade_portal/journeys/test_crosscut_journeys.py`)

## Phase 4: Polish and Cross-Cutting Concerns

**Purpose**: Validate the delivered files and layout.

- [X] T006 Run the applicable format, lint, test-quality, and documentation checks for the changed files. (delivered: `specs/numbered/0/0/1/2/1/1/2/4/4539-fix-signin-overflow/tasks.md`)

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 must pass before the browser test runs.
- **Foundational**: No changes are required.
- **User Story 1**: T002 precedes T003. T004 is independent of the layout fix.
- **Polish**: T006 depends on all User Story 1 tasks.

### Parallel Opportunities

- T004 can run in parallel with T002 and T003 because it changes a separate file.
- T003 must follow T002 so the regression test proves the fix.

## Implementation Strategy

1. Confirm the local Chromium environment.
2. Make the narrow viewport test fail without an expected-failure marker.
3. Correct the overflowing page element and add the issue release note.
4. Run the focused regression test and applicable quality checks.

## Notes

- **MVP**: User Story 1.
- **Parallel tasks**: One task, T004.
- **Test evidence**: The local portal test must pass at 390 by 844 pixels without a Mist cloud request.
