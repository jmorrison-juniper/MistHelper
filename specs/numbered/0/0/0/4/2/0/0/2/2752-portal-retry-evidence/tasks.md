# Tasks: Portal retry evidence

## Phase 1: Setup

- [x] T001 Read the current assessment and recovery records for #2752 and claim the exact file set.
- [x] T002 Bootstrap this worktree and run the baseline tests named in plan.md.

## Phase 2: Foundation

- [x] T003 Define unchanged contracts and safety limits in spec.md and plan.md.

## Phase 3: Capture evidence

**Independent test**: A first timeout remains visible after no data, recovery, a distinct error, and exhaustion.

- [x] T004 [US1] Add controlled capture retry tests in tests/unit/upgrade_portal/test_phase2_service_wiring.py.
- [x] T005 [US1] Preserve timeout details in src/interfaces/portals/upgrade_portal/capture/service.py.

## Phase 4: Tracker evidence

**Independent test**: First file failures remain visible after recovery or exhaustion without exposing tracker rows.

- [x] T006 [US2] Add file retry and cleanup tests in tests/unit/upgrade_portal/test_upgrade_driver.py.
- [x] T007 [US2] Preserve retry and cleanup evidence in src/interfaces/portals/upgrade_portal/upgrade/driver.py.

## Phase 5: Settle evidence

**Independent test**: Ping warnings preserve the first cause and the final result or exception contract.

- [x] T008 [US3] Add controlled ping sequences in tests/unit/upgrade_portal/test_settle_gate_service.py.
- [x] T009 [US3] Preserve warning-level ping evidence in src/interfaces/portals/upgrade_portal/settle/service.py.

## Phase 6: Verification and Delivery

- [ ] T010 Run applicable local gates and cross-artifact analysis for spec.md, plan.md, and tasks.md.
- [x] T011 Add changelog.d/issue-2752-portal-retry-evidence.md and prepare the repository PR template.
- [x] T012 Define human-review publication controls in plan.md.

## Dependencies and Execution

T001 through T003 precede implementation.
Each story adds tests before its production edit.
The three stories are independent after T003, but this session executes them in order without delegation.
T010 through T012 precede publication.
The capture story is the smallest useful increment.
This bounded PR completes all three stories together.
Optional commit hooks remain deferred until the coherent change is ready.
Disabled companion hooks do not run.
Delivery requires a ready PR with current-head checks and CodeQL passed.
The PR remains open for human review without automatic merge.
