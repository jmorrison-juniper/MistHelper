# Tasks: Each browser test frees each site lock that it took, and the run fails when a lock stays

**Input**: The design documents in `specs/3508-browser-lock-leaks/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [x] T001 [P] [US1] Write the direct tests of `HeldSiteLocks` in `tests/unit/upgrade_portal/test_e2e_lock_holds.py`.
- [x] T002 [P] [US3] Write the direct tests of `TrailHoldCheck` in `tests/unit/upgrade_portal/test_e2e_trail_hold_check.py`.
- [x] T003 Run the two new test files, and record the collection errors.

## Phase 2: Implementation

- [x] T004 [US1] Add the class `HeldSiteLocks` to `tests/support/upgrade_portal_e2e/lock_holds.py`.
- [x] T005 [US3] Add the class `TrailHoldCheck` to `tests/support/upgrade_portal_e2e/records/audit.py`.
- [x] T006 Run the two new test files, and record the pass (SC-004).
- [x] T007 [US1] Change the fixture `site_lock` in `tests/e2e/upgrade_portal/test_run_controls/conftest.py`, so it yields `HeldSiteLocks`.
- [x] T008 [US1] Change the three calls in `test_run_controls/test_bulk.py` and the one call in `test_run_controls/test_isolation.py` to `site_lock.take`.
- [x] T009 [US3] Add the session fixture `run_trail_hold_guard` to `tests/e2e/upgrade_portal/conftest.py`.
  The fixture `capture_portal_server` requests it, and the terminal summary prints its measure.

## Phase 3: Red proof

- [x] T010 Run `test_run_controls/test_isolation.py` and `test_later_site_checks.py` in Edge with the two old tests.
  Record the teardown error of the isolation test (SC-002) and the failure of the trail check (SC-001).

## Phase 4: Test repairs and green

- [x] T011 [US1] Release the lock in the test of the lost action answer before the cookie change (FR-005).
- [x] T012 [US2] Change `PlanSteps.take_the_site`, so it waits for the state `held` and never types the takeover word (FR-007).
- [x] T013 [US2] Add the step `PlanSteps.release_the_site`, and call it at the end of the capture start test (FR-006).
- [x] T014 Run the pair of T010 again, and record the pass and the measure with 0 leaked holds.
- [x] T015 Run the folder `test_run_controls` and `test_later_site_checks.py` together.
- [x] T016 Run all of `tests/e2e/upgrade_portal` in Edge (SC-003).
- [x] T017 Time the trail check on the trail of the full run (SC-005).
- [x] T018 Run py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter.

## Phase 5: Delivery

- [ ] T019 Commit the change, push the branch, and open the pull request with `Closes #3508`.
- [ ] T020 Wait for each check and CodeQL, then merge the pull request.
- [ ] T021 Post the result on issue #3508, and remove the worktree.

## Dependencies

- Phase 1 comes before Phase 2, because each test must fail first.
- T004 comes before T007, because the fixture uses the class.
- T005 comes before T009, because the fixture uses the class.
- Phase 3 comes before Phase 4, because the red proof needs the two old tests.
- Phase 5 comes after each task of Phase 4.
