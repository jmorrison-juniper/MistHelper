# Tasks: Upgrade Lock Retention

**Input**: `specs/numbered/0/0/1/0/4/4/0/1/3726-upgrade-lock-retention/`

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`

## Phase 1: Setup

**Purpose**: Reuse the current Python environment, source modules, and focused test modules. No dependency or package setup is required.

## Phase 2: Foundational

**Purpose**: No new blocking infrastructure is required. The shared refusal rule belongs to User Story 1.

## Phase 3: User Story 1 - Protect a site after an uncertain submission (Priority: P1)

**Goal**: Keep site locks and block retry when a response does not prove refusal or completion.

**Independent Test**: Use mocked HTTP 503 and malformed HTTP 200 results. Confirm the child is uncertain, the site lock is not released, and the retry plan is absent.

### Tests for User Story 1

- [x] T001 [P] [US1] Add service classification tests for HTTP 4xx, HTTP 5xx, invalid status, and HTTP 200 without an upgrade identity in `tests/unit/firmware/test_aggregate_upgrade_service.py`.
- [x] T002 [P] [US1] Add lock-release and retry tests for ambiguous legacy rejection records in `tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`.
- [x] T003 [P] [US1] Extend refusal and uncertainty cases in `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`.

### Implementation for User Story 1

- [x] T004 [US1] Add a shared confirmed-refusal predicate and submission-state classifier in `src/operations/execution/firmware/aggregate_upgrade_service.py`.
- [x] T005 [US1] Apply the shared classifier to device and organization submission results in `src/operations/execution/firmware/aggregate_upgrade_service.py`.
- [x] T006 [US1] Require refusal evidence before releasing a rejected child in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.
- [x] T007 [US1] Reuse the shared refusal predicate when building cancellation outcomes in `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py`.

## Phase 4: User Story 2 - Release a site after a proven refusal (Priority: P2)

**Goal**: Preserve lock release and retry behavior for confirmed HTTP 4xx refusals and known non-submissions.

**Independent Test**: Use mocked HTTP 4xx and known not-submitted records. Confirm existing settled-state behavior remains unchanged.

### Tests for User Story 2

- [x] T008 [US2] Verify HTTP 4xx refusals, known non-submissions, and reported final cloud jobs retain existing release behavior in `tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`.
- [x] T009 [US2] Verify HTTP 4xx refusals remain known non-submissions in `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`.

## Phase 5: Polish and Cross-Cutting Concerns

**Purpose**: Record the user-visible safety change and validate the issue scope.

- [x] T010 [P] Add the issue-specific release note in `changelog.d/issue-3726-upgrade-lock-retention.md`.
- [x] T011 Run the focused tests, Ruff, Black, and applicable type and security checks. Record exact results for `src/operations/execution/firmware/aggregate_upgrade_service.py`, `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`, and `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py`.
- [x] T012 Run the read-only cross-artifact analysis on `spec.md`, `plan.md`, and `tasks.md`. Resolve any actionable findings in those files.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: Uses the existing environment and files.
- **Foundational**: No new blocking infrastructure exists.
- **User Story 1**: T001-T003 add failing tests. T004-T007 implement the shared certainty rule and its release and cancellation uses.
- **User Story 2**: T008-T009 verify that proven refusals and known non-submissions keep their current behavior.
- **Polish**: T010-T012 follow implementation and focused validation.

### User Story Dependencies

- **US1 (P1)**: Can start with the existing service and portal modules. It is the MVP because it prevents duplicate firmware work after an uncertain response.
- **US2 (P2)**: Uses the shared rule from US1. Its tests protect the existing behavior for proven refusals and known non-submissions.

## Parallel Opportunities

```text
T001 + T002 + T003
T010
```

## Implementation Strategy

1. Add the offline tests and confirm that the ambiguous cases fail.
2. Implement the shared certainty rule and the lock-release guard.
3. Verify both user stories with mocked results and intercepted callbacks.
4. Run the focused local gates and record their exact results.
5. Hold pull request publication until PR #4679 releases the serial merge slot.
