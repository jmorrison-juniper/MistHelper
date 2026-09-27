# Tasks: Each run-control browser test frees its site, and the two-operator fixture fails on a refusal

**Issue**: #3497
**Input**: [spec.md](spec.md), [plan.md](plan.md), and [research.md](research.md)

The marker `[P]` shows a task that can run in parallel with the other `[P]` tasks of the same phase.
The marker `[USn]` names the user story of the task.

## Phase 1: Setup

- [x] T001 Create the branch `fix/3497-retry-lock-leak` from `main` in the worktree `MistHelper-i3497`.
- [x] T002 Record the red baseline of the repro sequence in `research.md`, section R1.
- [x] T003 Record the baseline time of `test_existing.py` in `research.md`, section R6.

## Phase 2: Direct tests first (US3)

- [x] T004 [P] [US3] Write the direct tests of `RunLedger` in `tests/unit/upgrade_portal/test_e2e_site_lock.py`.
- [x] T005 [P] [US3] Write the direct tests of `SiteRelease` in the same file.
- [x] T006 [P] [US3] Write the direct tests of `LockTakeAnswer` in the same file.
- [x] T007 [US3] Run the direct tests before the implementation, and record the red result in `research.md`.

## Phase 3: Each run-control test frees the site (US1)

- [x] T008 [US1] Write `RunLedger` and `SiteRelease` in `tests/support/upgrade_portal_e2e/site_lock.py`.
- [x] T009 [US1] Add the fixture `run_ledger` and the teardown of the fixture `portal_page` in `test_existing.py`.
- [x] T010 [US1] Record each run that the create call answered with 201 in the helper `_create_run`.
- [x] T011 [US1] Record the retry run of each retry test from the address of the capture page.

## Phase 4: The two-operator fixture fails on a refusal (US2)

- [x] T012 [US2] Write `LockTakeAnswer` in `tests/support/upgrade_portal_e2e/site_lock.py`.
- [x] T013 [US2] Use `LockTakeAnswer` in the fixture `held_site` of `test_two_operators.py`, and update its docstring.

## Phase 5: Validation

- [x] T014 Run the direct tests after the implementation. Each test must pass.
- [x] T015 Run the repro sequence of SC-001, and read the trail of the run for SC-004.
- [x] T016 Run the full folder `tests/e2e/upgrade_portal` in Edge for SC-002.
- [x] T017 Compare the time of `test_existing.py` with the baseline for SC-005.
- [x] T018 Delete the temporary wait test `tests/e2e/upgrade_portal/test_zz_tmp3497_wait.py`.
- [x] T019 Run ruff, black, py_compile, mypy, and the test quality gate.
  The first gate run reported 8 new findings. The class `AnswerBody` and two address checks repair them. See research R7.
- [ ] T020 Commit the change, push the branch, and open the pull request.

## Dependencies

1. Phase 2 comes before Phases 3 and 4, because the direct tests must fail first.
2. T008 comes before T009, T010, and T011.
3. T012 comes before T013.
4. Phase 5 comes after Phases 3 and 4.
