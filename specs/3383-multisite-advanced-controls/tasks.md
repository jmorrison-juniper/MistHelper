# Tasks: The multi-site options page offers each advanced control

**Issue**: #3383 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the contract file
  `tests/contract/upgrade_portal/test_org_advanced_options.py`. It holds the
  parity map, the route tests, the refusal tests, the prefill tests, and the
  confirm summary test.

- [x] T002 Add the unit file
  `tests/unit/firmware/test_org_advanced_bodies.py`. It holds the organization
  body rules and the access point child fields.

- [x] T003 Run the new tests on the old code, and record the red result.
  The unit file stopped at the import, because `FAILURE_COUNT_HIGHEST` did
  not exist. The contract file gave 25 failed tests and 2 passed tests. The
  two tests that passed guard the old behavior: the default body and the
  legacy request.

## Phase 2: The change

- [x] T004 Add `src/upgrade_portal/upgrade/org_advanced_options.py`.

- [x] T005 Change the routes, the labels, and the two firmware modules.

- [x] T006 Add the controls to `org_options.html` and the summary to
  `org_confirm.html`.

- [x] T007 Extend the multi-site visibility rule in `portal.js`.

- [x] T008 Run the new tests green. The two new files gave 64 passed tests.
  The unit file `tests/unit/upgrade_portal/test_org_advanced_summary.py`
  adds 27 tests for the reader and the confirm summary.

## Phase 3: The browser journey

- [x] T009 Add `tests/e2e/upgrade_portal/test_org_advanced_options.py`. The
  journey sets each visible control, reads the posted body and the confirm
  page, goes Back, and takes a screenshot of each page. The file holds four
  journeys, and all four passed in 20 seconds with the Edge channel. The
  screenshots are in
  `data/test-artifacts/upgrade-portal-journeys/org-advanced-options/`.

## Phase 4: Finish

- [x] T010 Add the release note
  `changelog.d/issue-3383-multisite-advanced-controls.md`.

- [x] T011 Run every gate: ruff, black, mypy, pylint, pydocstyle, interrogate,
  bandit, radon, vulture, the STE lint, and the test quality gate. Each gate
  passes. The test quality gate first reported two findings in the contract
  file: no malformed body and no empty body. Three new tests cover both cases.
  Pylint reported three copies of the peer and radio field names. The names
  now come from one list in `src/firmware/org_upgrade_body.py`.

- [x] T012 Run the portal suites and the browser suite of the upgrade portal.
  The portal suites gave 5864 passed and 2 failed. The two failures pinned
  the old rule that `enable_p2p` and `max_failures` are unsupported fields.
  A new test proves that a null value of each field still stops the build.
  The browser suite gave 266 passed and 1 skipped. Issue #3380 tracks the
  skip, and main has the same skip.

- [x] T013 Get an independent code review. The review gave four findings.
  1. One changed test file was not staged. The commit now holds it.
  2. The confirm summary listed the failure counts for a router child and for
     the per-device call, and neither body carries them. The summary now reads
     the stored child bodies. Two contract tests and three unit tests cover
     the fix. A plugin that put the old rule back made four of them fail.
  3. The new number fields show the text of the Python number reader. Issue
     #3388 covers each number reader of both modes.
  4. An empty last site replaces the choices of the operator with the
     defaults. The defect exists on main, and issue #3389 tracks it. A probe
     also found that the confirm page names a strategy that the per-device
     call does not send. Issue #3390 tracks that gap.

- [ ] T014 After the merge, deploy the changed files to port 8056 with a class
  B reload, and read the new controls on the served page.
