# Tasks: The multi-site check result uses correct grammar for each count

**Issue**: #3453 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test and each changed test must fail on the old code. Each
test task therefore comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3453` from `main`, and run
  `scripts/bootstrap_worktree.py`. Rebase onto `64455cdb`, and install the
  devtools pin of that commit.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3453-reconcile-summary-grammar/`.

## Phase 2: User Stories 1 and 2 (the unit tests)

- [x] T003 Write the unit tests of a child job of one device. Cover a proven
  device, a device with no reading, and a reinstall. Put them in
  `tests/unit/upgrade_portal/test_issue_3453_reconcile_summary.py`.
- [x] T004 Write the unit tests of a child job of three devices in the same
  file. Cover one match, and two matches with one device that gives no
  reading.
- [x] T005 Write the unit test of a child job with no device. The text must
  not change.

## Phase 3: The tests that read the old text

- [x] T006 Change the expected text in
  `tests/contract/upgrade_portal/test_org_child_controls_routes.py`.
- [x] T007 Change the expected text in
  `tests/e2e/upgrade_portal/test_org_recovery_controls.py`.
- [x] T008 Change the stand-in text in
  `tests/unit/firmware/test_aggregate_child_controls.py` and in
  `tests/unit/upgrade_portal/test_org_child_controls.py`.
- [x] T009 Run T003 through T007 on the old code. Record the red result in
  this file. Result on `64455cdb`: 12 tests failed and 39 passed. In the new
  unit file, 11 of 12 tests failed. The test of a child job with no device
  passed, because that text does not change. The contract test failed. The
  browser journey failed and read the old text "0 of 1 devices run the target
  version". The stand-in tests passed, because they do not read the text of
  the check class.

## Phase 4: The code change

- [x] T010 Change `_summary` in `src/upgrade_portal/upgrade/org_reconcile.py`,
  and add the static noun method.
- [x] T011 Run T003 through T008 green. Read each screenshot of the browser
  journey. Result: 90 tests passed in the unit, contract, and stand-in files.
  The 4 browser journeys of the recovery file passed. The screenshot
  `reconcile-after.png` shows "The target version runs on 0 of 1 device".

## Phase 5: Polish

- [x] T012 [P] Add `changelog.d/issue-3453-reconcile-summary-grammar.md`.
- [x] T013 Run the gates of the plan, and the STE lint of each new Markdown
  file. Result: each gate passed. The pylint score is 10.00. mypy read 528
  files. The test quality gate found 0 new findings in 5 files. Each STE score
  is 93 or more.
- [x] T014 Run the suites of the plan. Result: the upgrade-portal unit suite,
  the upgrade-portal contract suite, and the firmware unit tests gave 6,007
  passed. The upgrade-portal integration suite and the guardrails gave 358
  passed and 2 skipped. The changelog guard skips outside a pull request
  event. The coverage guard skips because no option has the class
  `unregistered`.
- [ ] T015 Open the pull request. Merge it by hand after each check passes.
- [ ] T016 Do the class B deploy of `org_reconcile.py` to port 8056, and
  close #3453.

## Dependencies

- T002 comes before T003.
- T003 through T008 come before T009.
- T009 comes before T010.
- T010 comes before T011.
- T011, T012, and T013 come before T014.
- T014 comes before T015, and T015 comes before T016.