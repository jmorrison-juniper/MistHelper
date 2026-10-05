# Tasks: WebSocket Audit Compatibility

**Input**: Design documents from `specs/3923-websocket-audit-compatibility/`

**Scope**: Keep this change in the isolated audit support and test files. Do not change portal behavior, shared instructions, or deployment files.

**Tests**: Regression tests are required. Add both story test sets before any repair, then confirm each set fails for the expected reason.

## Phase 1: Setup

**Purpose**: Reuse the existing Python project and audit test structure.

No setup tasks are needed. The plan identifies the existing support modules and isolated pytest modules.

## Phase 2: Foundational

**Purpose**: Identify shared work that blocks both stories.

No foundational tasks are needed. Each story uses the existing audit fixtures and can be repaired independently.

## Phase 3: Add isolated regression tests

**Purpose**: Add both story test sets before running any test or repairing code.

### User Story 1 - Audit scoped client discovery (Priority: P1)

**Goal**: Permit only the exact client GET after approved site and same-site device responses establish both IDs.

**Independent test criteria**: Use synthetic responses and local browser routes. Confirm the exact approved GET passes, all scope violations fail before transmission, and no SDK method runs.

- [X] T001 [P] [US1] Add regressions in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`. Cover missing, malformed, empty, unrelated, and cross-site evidence. Allow only the exact `/api/websockets/sites/{site_id}/devices/{device_id}/clients` GET. Deny other methods, origins, queries, redirects, encoded paths, and mutations before transmission. Verify GET source for `listSiteDevices`, `searchSiteWiredClients`, and `getSiteSdkStatsByMap` without invoking methods. Compare records with loaded inventory.

### User Story 2 - Report visible cancellation accurately (Priority: P2)

**Goal**: Report the actual count of visible exact-name Cancel controls in each operation form.

**Independent test criteria**: Use the isolated browser to verify zero, one, hidden, and duplicate controls. Confirm the result retains one record per inventory entry after an inspection failure.

- [X] T002 [P] [US2] Add regressions in `tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`. Measure visible controls in the actual operation form named exactly `Cancel` with test ID `ws-cancel-selection-button`. Cover zero, one, hidden, and duplicate controls, `operation-cancel`, and record retention after inspection errors.

## Phase 4: Confirm red regressions

**Purpose**: Confirm the new regressions fail for the known gaps before either repair.

### User Story 1

- [X] T003 [P] [US1] Run `python -m pytest tests/e2e/websockets_tab/dialog_audit/test_inventory.py` and confirm new scope and SDK-source regressions fail for the expected reasons.

### User Story 2

- [X] T004 [P] [US2] Run `python -m pytest tests/e2e/websockets_tab/dialog_audit/test_dialogs.py` and confirm the fixed cancellation result fails the new cases.

**Red run evidence before repair**:

- `test_inventory.py`: `========================= 5 failed, 79 passed in 0.59s =========================`
- `test_dialogs.py`: `======================== 5 failed, 17 passed in 24.55s ========================`

## Phase 5: Implement the independently testable story repairs

**Purpose**: Repair each story only after both red-test runs confirm the expected failures.

### User Story 1 repair

- [X] T005 [P] [US1] Update `ReadScope` in `tests/e2e/websockets_tab/dialog_audit/support/policy.py`. Store `Approved device IDs by site` as `Map from site ID to a set of UUID strings`. Allow the exact client GET after valid same-site responses. Preserve denial for non-GET methods, other origins, queries, redirects, encoded paths, and mutations.

### User Story 2 repair

- [X] T006 [P] [US2] Update `DialogInspector` in `tests/e2e/websockets_tab/dialog_audit/support/journeys.py`. Count visible controls with test ID `ws-cancel-selection-button` and exact name `Cancel`. Emit `operation-cancel` at zero controls. Report no missing finding at one. Keep one result record per inventory entry after inspection errors.

## Phase 6: Relevant validation gates

**Purpose**: Run isolated tests and Python quality gates after both repairs.

- [X] T007 Run `python -m pytest tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py` and confirm all isolated regressions pass.
- [X] T008 [P] Run `python -m py_compile tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`.
- [X] T009 [P] Run `python -m ruff check tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`.
- [X] T010 [P] Run `python -m black --check tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/test_inventory.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py`.
- [x] T011 Update `quickstart.md` with scoped client reads and shared Cancel measurements. Record the internal-only release-fragment exemption in the plan.

Do not run `test_live.py`, use credentials, probe a live portal, or submit an operation.

Before publication, run the guide preflight and both configured test-quality gates.
Use the committed comparison against `origin/main` for the changed-test gate.
Do not change the test-quality baseline.

## Dependencies and execution order

### Phase dependencies

- Setup has no tasks because the project and test structure already exist.
- Foundational work has no tasks because neither story needs a shared blocker.
- Both regression test additions come before all red-test runs.
- Both red-test runs must confirm the expected failures before either repair starts.
- The two repairs can run in parallel because they change separate support modules.
- Run the combined isolated tests after both repairs. Run the three quality gates after the combined tests pass.

### User story dependencies

- **User Story 1 (P1)**: Add and confirm its regression tests before repairing `policy.py`. It does not depend on User Story 2.
- **User Story 2 (P2)**: Add and confirm its regression tests before repairing `journeys.py`. It does not depend on User Story 1.
- Complete User Story 1 first for the P1 MVP. User Story 2 can proceed independently after the shared red-test checkpoint.

### Task dependency graph

```text
T001 and T002 -> T003 and T004 -> T005 and T006 -> T007 -> T008, T009, and T010
```

### Parallel opportunities

- T001 and T002 can run in parallel because they add tests to separate files.
- T003 and T004 can run in parallel after their matching test additions.
- T005 and T006 can run in parallel after both red-test runs.
- T008, T009, and T010 can run in parallel after T007 passes.

## Parallel execution examples

```text
After adding both regression sets:
Run T003 for test_inventory.py and T004 for test_dialogs.py.

After both red runs:
Repair policy.py with T005 and journeys.py with T006.

After T007 passes:
Run T008, T009, and T010.
```

## Implementation strategy

### MVP first

1. Add and run the User Story 1 isolated regressions.
2. Add and run the User Story 2 isolated regressions.
3. Confirm both sets fail for the expected reasons before repair.
4. Repair and validate User Story 1 as the P1 MVP.
5. Repair and validate User Story 2 without changing the portal or live audit path.

### Independent delivery

Complete each story against its own synthetic regression tests. Keep both repairs separate, then run the combined isolated suite and the relevant quality gates.
