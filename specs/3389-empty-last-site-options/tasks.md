# Tasks: An empty site never replaces the choices of the operator

**Issue**: #3389 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the unit tests of `OrgSiteRecords` and `OrgSiteRefusal`.
  The file holds 13 tests.
- [x] T002 Add the contract tests of the save route. The file holds 10 tests.
- [x] T003 Run the contract tests on the old code, and record the red result.
  The run gave 7 failed and 16 passed. Six failures show status 200 where the
  test expects 400. The name test fails with a transport fault, because the old
  save accepts the plan.

## Phase 2: The change

- [x] T004 Add `src/upgrade_portal/upgrade/org_site_records.py`.
- [x] T005 Change `_aggregate_option_record`, and add `_site_labels`.
- [x] T006 Run the unit tests and the contract tests green. The two contract
  files gave 44 passed. One test of issue #3383 emptied the first site of its
  gateways, so the new refusal stopped it. That test now narrows the selection
  on the Sites page.

## Phase 3: The browser journey

- [x] T007 Add the empty site and its operator to the browser stand-in.
- [x] T008 Add the journey of the refusal and the recovery. Read each
  screenshot. The journey passes. On the old route code, the journey fails,
  because the flash region stays empty.

## Phase 4: Finish

- [x] T009 Add the release note under `changelog.d/`. The file is
  `changelog.d/issue-3389-empty-last-site-options.md`.
- [x] T010 Run every gate. Ruff, black, py_compile, mypy (597 files),
  pylint (9.94), pydocstyle, interrogate (100 percent), bandit, radon, and
  vulture pass. The test quality ratchet reports 0 new findings. The STE
  linter scores each changed file from 95 to 99.
- [x] T011 Run the portal suites and the browser suite of the upgrade portal.
  The unit, contract, and integration suites give 5025 passed. The browser
  suite gives 267 passed and 1 skipped. Issue #3380 tracks that skip.

## Phase 5: The review finding

A code review found that the FR-003 refusal stops a valid retry save. The
Sites page ends the retry, so the message sent the operator to a page that
adds the healthy devices to the plan again.

- [x] T013 Add the flag `every_site_planned` to `OrgSiteRecords`. The route
  passes `current_retry_plan() is None`. The request cache holds the retry
  plan, so the flag adds no store read.
- [x] T014 Add two unit tests of the flag, and run the FR-004 unit test for
  both flag values. Add two retry contract tests to
  `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. With the
  flag forced to True, both contract tests fail with status 400 and the FR-003
  message.
- [x] T015 Add the browser journey of a retry with one cleared type to
  `tests/e2e/upgrade_portal/test_org_recovery_controls.py`. Read each
  screenshot. The confirm page shows "Sites: 2" and "Devices: 1". Issue #3396
  covers that site count.
- [x] T016 Run the gates, the portal suites, and the browser journeys of the
  multi-site mode again. Each gate passes, and pylint rates the source 9.95.
  The unit, contract, and integration suites give 5032 passed. The 14 browser
  files of the multi-site mode give 32 passed in Edge.

## Phase 6: The second review finding

A second code review found that a failed view read drops the retry devices of
a site with no message. The narrow step of the retry hid the loss, because
FR-008 skips a site with no target.

- [x] T017 In `_site_option_record`, return the empty record when the device
  view holds no device. The route then makes no second read of that site.
- [x] T018 Add a retry contract test to
  `tests/contract/upgrade_portal/test_org_child_controls_routes.py`, and add a
  plain-save contract test to
  `tests/contract/upgrade_portal/test_org_site_records_routes.py`. With the
  early return removed, the retry save answers 200, and the plain save shows
  the FR-003 message.
- [x] T019 Run the gates, the portal suites, and the browser journeys of the
  multi-site mode again. Each gate passes, and pylint rates the source 9.95.
  The unit, contract, and integration suites give 5034 passed. The 14 browser
  files of the multi-site mode give 32 passed in Edge.

## Phase 7: Deploy

- [ ] T012 After the merge, deploy to port 8056 with a class B reload, and
  check the served files.
