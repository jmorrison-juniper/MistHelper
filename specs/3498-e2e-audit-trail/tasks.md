# Tasks: The browser test portal keeps its lock audit trail inside its own run

**Issue**: #3498 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each direct test must fail before the class exists. The guard
must fail on a browser run with no placement. Each test task comes before
its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3498` from `main`, and run
  `scripts/bootstrap_worktree.py`. Move the branch to `main` at `61357ba9`,
  which holds the repair of #3492.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3498-e2e-audit-trail/`.
- [x] T003 File issue #3501 for the dead test keys and the trap counters. The
  research of this issue found them.

## Phase 2: User Story 3 (the direct tests)

- [x] T004 Write `tests/unit/upgrade_portal/test_e2e_audit_trail_isolation.py`.
  Prove the placement inside `tmp_path`. Prove the refusal of a run trail
  that is the checkout trail. Prove that an absent trail counts 0 and that
  an unreadable trail raises. Prove that equal counts pass and report the
  path, and that a written line fails the guard.
- [x] T005 Run T004 before the class exists. Record the red result in this
  file.
  - Result: the collection stopped with an `ImportError`, because the class
    `AuditTrailIsolation` did not exist. The run gave 1 error in 11.62 s.

## Phase 3: User Stories 1 and 2 (the browser journey)

- [x] T006 Write `tests/e2e/upgrade_portal/test_audit_log_journey.py`. Open
  the capture start page of the journey site. Press the take control and the
  release control. Read the Audit log card of the site and of the page with
  no site. Read the run trail from the parent process. Save a screenshot of
  each state.

## Phase 4: The guard

- [x] T007 Write the class `AuditTrailIsolation` in
  `tests/support/upgrade_portal_e2e/records/audit.py`. Add the action logs.
  - Result: the 10 direct tests of T004 passed in 1.36 s.
- [x] T008 In `tests/e2e/upgrade_portal/conftest.py`, add the session fixture
  `checkout_audit_trail_guard`, the dependency of `capture_portal_server`,
  and the hook `pytest_terminal_summary`.
- [x] T009 Run T006 and one existing lock test with the guard and with no
  placement. Record the red result of the guard in this file.
  - Result: 1 failed, 1 passed, and 1 error in 34.97 s. The guard failed at
    the teardown of the lock test. Its message named the checkout trail of
    the worktree. It stated 0 lines before the run, 4 lines after the run,
    and 0 lines in the trail of the run. The journey failed too. It read 2
    lines of the journey site in the checkout trail and no record in the run
    trail.
  - The first attempt did not reach the tests. The portal did not answer in
    the 10 s wait, and the log of the child stopped during an import. The
    second attempt started the portal. This result does not depend on the
    change, because the guard adds 2 file reads to the parent alone.

## Phase 5: The placement

- [x] T010 In `build_stand_in_app`, call the placement before `create_app`.
- [x] T011 Run T004, T006, and the lock test green. Read each screenshot.
  Record the result in this file.
  - Result: 12 passed in 33.06 s. The guard stated 0 lines before the run,
    0 lines after the run, and 4 lines in the trail of the run.
  - The 5 screenshots show the free banner, the held banner with the release
    control, and the released banner with the take control. The Audit log
    card of the site and of the page with no site show 2 rows each. The rows
    are the release and the take of the journey site, and the operator digest
    is `ef9f811c166805f7`.
- [x] T012 Delete the trail that the red run wrote in this worktree.
  - Result: the trail held the 4 test lines of the red run. The green run
    left no trail in the worktree.

## Phase 6: Proof

- [x] T013 Run every test under `tests/e2e/upgrade_portal/`. Explain or fix
  each changed result. Record the result in this file.
  - Result: 316 passed and 1 skipped in 851.20 s. The skip is the known skip
    at `test_capture.py:745` (#3380). The guard stated 0 lines before the run,
    0 lines after the run, and 98 lines in the trail of the run.
  - The earlier folder run gave 297 passed and 19 skipped in 1102.72 s. The
    change of result comes from the time of the run, not from this change.
    Issue #3497 records the cause. The 18 two-operator tests skip only when
    more than 300 s pass between a retry test and the two-operator tests.
    This run was 251 s shorter, so the lock cooldown did not start. The
    guard and the move do not touch the lock records, so #3497 stays open.
- [x] T014 Run `tests/unit/upgrade_portal`, `tests/contract/upgrade_portal`,
  and `tests/guardrails`. Run the gates. Record the result in this file.
  - Result: 5615 passed and 2 skipped in 532.66 s.
  - The commands `py_compile`, `ruff check`, and `black --check` gave no
    finding on the 4 changed Python files. The `mypy` run on the MYPY_PATHS
    scope found no issue in 528 source files.
  - The quality gate checked the 2 new test files and found 0 new findings.
- [ ] T015 Open the pull request. Merge it by hand after each check passes.
- [ ] T016 Comment on #3498 with the result. No deploy is necessary.

## Dependencies

- T002 comes before T004 and T006.
- T004 comes before T005, and T005 comes before T007.
- T006, T007, and T008 come before T009.
- T009 comes before T010, and T010 comes before T011 and T012.
- T011 comes before T013 and T014.
- T013 and T014 come before T015, and T015 comes before T016.