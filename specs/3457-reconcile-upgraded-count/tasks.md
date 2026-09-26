# Tasks: A child job that the check proves counts its devices as upgraded

**Issue**: #3457 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of a proven child job must fail on the old code. Each
test of a child job with no proof must pass on the old code, because it guards
the counts that were already correct. Each test task comes before its code
task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3457` from `main`, and run
  `scripts/bootstrap_worktree.py`. Rebase onto `main` at `34472aef`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3457-reconcile-upgraded-count/`.

## Phase 2: User Stories 1 and 4 (the unit tests)

- [x] T003 Write `tests/unit/upgrade_portal/test_issue_3457_reconcile_upgraded_count.py`.
  Read the proof rule for each pair of a state and a stored verdict. Read the
  counts of a proven child job with no failed device and with one failed
  device. Read the counts of a damaged record. Read the summary of a proven
  child job beside a child job that completed through the cloud.

## Phase 3: User Stories 1, 2, and 3 (the contract tests)

- [x] T004 In `tests/contract/upgrade_portal/test_org_child_controls_routes.py`,
  add a test of a check that proves both child jobs. Read the counts of the
  page and of the status answer.
- [x] T005 In the same file, add a test of a check that proves one child job.
  Read the counts of both child rows, of the operation block, and of the
  device table.
- [x] T006 In the same file, add a test of a check that proves nothing. The
  counts stay 0.

## Phase 4: User Story 5 (the browser journey)

- [x] T007 In `tests/e2e/upgrade_portal/test_org_recovery_controls.py`, read
  the counts of both child rows and of the operation block after the check.
- [x] T008 Run T003 through T007 on the old code. Record the red result in
  this file.

## Phase 5: The code change

- [x] T009 Change `upgrade/org_devices.py`. Add the class method `is_proven`
  and the method `proven_counts` to `OrgChildDevices`.
- [x] T010 Change `app/routes/org_upgrade.py`. Import `OrgChildDevices`, and
  return the proven counts from `_aggregate_child_counts` for a proven child
  job.
- [x] T011 Run T003 through T007 green. Read the screenshot
  `reconcile-after.png`.

## Phase 6: Polish

- [x] T012 [P] Add `changelog.d/issue-3457-reconcile-upgraded-count.md`.
- [x] T013 Run the gates of the plan, and the STE lint of each new Markdown
  file.
- [x] T014 Run the suites of the plan.
- [ ] T015 Open the pull request. Merge it by hand after each check passes.
- [ ] T016 Do the class B deploy of the two files to port 8056, and close
  #3457.

## Evidence

### The red run (T008)

- Outside the browser, the old code gave 14 failed tests and 42 passed tests.
- The 8 cases of `is_proven` and the 3 tests of `proven_counts` failed with
  `AttributeError`, because the old code has no such method.
- One summary test and 2 contract tests failed on the counts. The Upgraded
  count of a proven child job stayed 0.
- In the browser, the journey failed at line 209 of
  `test_org_recovery_controls.py`. The Upgraded cell of the first child row
  showed "0".
- The screenshots of the red run are in the session folder `i3457-red`.

### The green run (T011)

- Outside the browser, the new code gave 155 passed tests. That run holds the
  #3457 tests and the tests of the neighbor files.
- In the browser, `test_org_recovery_controls.py` gave 4 passed tests.
- The screenshot `reconcile-after.png` shows these counts after the check:
  - The operation block shows Total targets 2, Upgraded 1, and Failed 0.
  - The row of "E2E Stand-In Site" shows completed, 1, 1, and 0.
  - The second row shows submission_unknown, 1, 0, and 0.
  - The device table agrees with the rows.
- The test quality gate found one missing empty input and one missing `None`
  input. The unit file now holds a test of an operation with no child job. The
  access point child job now names no site, as the real organization route
  does. After that change, the unit file gave 14 passed tests, and the gate
  found 0 new findings.

### The suites (T014)

- The unit suite and the contract suite of the upgrade portal gave 5194
  passed tests in 425 seconds.
- The 14 browser files of the multi-site pages gave 32 passed tests in 160
  seconds.
- The integration suite and the guardrails gave 424 passed tests and 13
  skipped tests in 178 seconds.
- Each skip names its reason. The reasons are no Mist API credentials, no
  running compose services, no pull request event, and no registry option of
  the class unregistered. No skip comes from this change.

## Dependencies

- T002 comes before T003.
- T003 through T007 come before T008.
- T008 comes before T009 and T010.
- T009 and T010 come before T011.
- T011, T012, and T013 come before T014.
- T014 comes before T015, and T015 comes before T016.
