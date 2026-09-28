# Tasks: Each test keeps its site lock actions out of the checkout trail

**Input**: The design documents in `specs/3503-test-site-lock-trail/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [x] T001 [US1] Record the baseline leak of the portal suites in research.md.
- [x] T002 [P] [US1] Write the direct tests of the move in `tests/unit/upgrade_portal/test_checkout_trail_guard.py`.
- [x] T003 [P] [US2] Write the direct tests of the count, the measure, the decision, and the skip text in the same file.
- [x] T004 [US3] Write the direct test that the session guard reads the checkout trail and not a moved trail.
- [x] T005 Run the new test file, and record the failures.

## Phase 2: Implementation

- [x] T006 [US2] Add the class `CheckoutTrailGuard` to `tests/support/site_lock_trail.py`.
- [x] T007 [US1] Add the autouse move `isolate_site_lock_trail` to `tests/conftest.py`.
- [x] T008 [US2] Add the session guard `checkout_site_lock_trail_guard` to `tests/conftest.py`.
- [x] T009 [US2] Add the hook `pytest_terminal_summary` to `tests/conftest.py`, so the run prints the measure.
- [x] T010 Update the module text of `tests/conftest.py` for issue #3503.

## Phase 3: Green and proof

- [x] T011 Run the new test file, and record the pass.
- [x] T012 [US1] Run the portal suites and `tests/test_upgrade_portal_audit.py` in the worktree.
  The worktree trail must stay absent (SC-001).
- [x] T013 [US2] Add a temporary test that writes to the checkout trail.
  Record the failed run, and then delete the temporary test.
- [x] T014 Run `tests/unit`, `tests/contract`, and `tests/guardrails` in full (SC-003).
- [x] T015 [US3] Run the audit log journey and a broad set of journeys in Edge.
  Record the two guard lines (SC-004).
- [x] T016 Read the setup time of the two fixtures with `--durations` (SC-005).
- [x] T017 Run py_compile, ruff, black, mypy, the test quality gate, and the STE linter.

## Phase 4: Delivery

- [ ] T018 Commit the change, push the branch, and open the pull request with `Closes #3503`.
- [ ] T019 Wait for each check and CodeQL, then merge the pull request.
- [ ] T020 Post the result on issue #3503, and remove the worktree.

## Dependencies

- Phase 1 comes before Phase 2, because each test must fail first.
- T006 comes before T007 and T008, because the fixtures use the class.
- T013 comes after T011, because the proof needs a green base.
- Phase 4 comes after each task of Phase 3.