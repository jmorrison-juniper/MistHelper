# Tasks: The capture walk ends each run that it builds

**Input**: The design documents in `specs/3511-walk-live-run/`
**Prerequisites**: plan.md, spec.md, and research.md

**Tests**: The spec asks for tests. Write each test before the code that it proves.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel, because it changes a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Red

- [x] T001 [P] [US4] Write the direct tests in `tests/unit/upgrade_portal/test_e2e_live_runs.py`. Cover the rule parity with `run_is_live`, the paging, the page bound, each refused answer, the leak decision, the record, the summary, and the scan time.
- [x] T002 [P] [US4] Write one direct test in `tests/unit/upgrade_portal/test_e2e_site_lock.py` for a ledger with a live run and a final run.
- [x] T003 Run both direct test files on the old code. Record the failures.

## Phase 2: The check

- [x] T004 [US2] Write `tests/support/upgrade_portal_e2e/live_runs.py` with `LiveRun`, `SiteRunScan`, `SiteRunReader`, and `LiveRunCheck`.
- [x] T005 Run both direct test files, and record the pass.
- [x] T006 [US2] Add the module check to `tests/e2e/upgrade_portal/conftest.py`: the portal state, the stash key, the record, the fixture `module_live_run_check`, and the summary line.
- [x] T007 [US2] Run `test_capture.py` alone in Edge with the old walk teardown. The check must fail the module and name the run of the walk (SC-002).

## Phase 3: The walk teardown

- [x] T008 [US1] Add the fixture `run_ledger` and the helper `_end_the_walk_runs` to `tests/e2e/upgrade_portal/test_capture.py`. Change `walking_page` to end the runs, and then to release the site.
- [x] T009 [US1] Record the run key of the walk after the options page opens.
- [x] T010 [US3] Change the refusal test: require 201 for the first create call, record the key, and check that the refusal names that run.
- [x] T011 Run `test_capture.py` alone in Edge. Each test passes or skips for #3380 only, and the check finds no leak.

## Phase 4: Browser green

- [x] T012 [US1] Run `test_capture.py` and `test_existing.py` together in Edge with a debug log. Each create call of `test_existing.py` answers 201 (SC-001).
- [x] T013 Run all of `tests/e2e/upgrade_portal` in Edge. Record the result, the leaks, and the scan time (SC-003 and SC-004).
- [x] T014 If T013 finds a leak in another module, end that run with the ledger of #3497 (FR-009), or file a new issue.
- [x] T015 Run py_compile, ruff, black, mypy, the test quality gate, `tests/guardrails`, and the STE linter.

## Phase 5: Delivery

- [x] T016 Commit the change, push the branch, and open the pull request with `Closes #3511`.
- [ ] T017 Wait for each check and CodeQL, then merge the pull request.
- [ ] T018 Post the result on issue #3511, and remove the worktree.

## Dependencies

- Phase 1 comes before Phase 2, because each test must fail first.
- T004 comes before T006, because the conftest imports the new module.
- T007 comes before T008, because the red run needs the old walk teardown.
- Phase 4 comes after Phase 3.
- T013 comes after T012, because the full run takes the longest time.

## Notes

The red runs and the green runs go here.

- T003, red. The run stopped at collection with `ModuleNotFoundError: No module named 'tests.support.upgrade_portal_e2e.live_runs'`. The site lock file alone gave 37 passed. The new ledger test of T002 passes on the old code too, because `SiteRelease.end_runs` already holds that decision. The test guards the decision against a later change.
- T005, green. The two direct test files gave 85 passed: 48 for the live-run check and 37 for the site lock. Ruff and black report no finding on the three files.
- T006. The conftest imports the check, and it adds the fixture `module_live_run_check`, the record `live-run-check.jsonl`, and the summary line. Ruff and black report no finding.
- T007, red. The first two runs stopped at setup, because the portal did not answer in 10 seconds. The child needed 12.2 seconds on this loaded workstation. Issue #3516 holds that defect. The third run used a local plugin outside the repository. The plugin set a start budget of 60 seconds.
- T007, red, third run. The result was 11 passed, 1 skipped for #3380, and 1 error. The error came at the teardown of the last test of the module.
- T007, the error text: "The module tests/e2e/upgrade_portal/test_capture.py left 1 live run(s)". The next line named the run `run-5491ad8e…` in state `created` at site `22222222-…`. The check scanned 5 sites, read 3 history rows, and took 368.3 ms. So SC-002 is met.
- T008 to T010. The walk and the refusal test record their runs in the ledger. The teardown cancels each live run, and then it releases the site. The refusal test now requires 201 for its first create call, and it checks that the refusal names its own run. Ruff passes. Black wrapped one signature.
- T011, green. The result was 11 passed and 1 skipped for #3380, with no error. Each of the two teardowns cancelled 1 run. The status read and the cancel each answered 200. The check scanned 5 sites, read 4 history rows, found 0 leaked live runs, and took 515.9 ms.
- T012, green. The two modules ran in this order: `test_capture.py`, then `test_existing.py`. The result was 22 passed and 1 skipped for #3380. Each of the 11 create calls of `test_existing.py` answered 201, so SC-001 is met. The check scanned 5 sites after each of 2 modules, read 21 history rows, found 0 leaked live runs, and took 411.6 ms.
- T013, first run. All 317 tests ran in 2,067.6 seconds. The check found 3 leaked live runs in 3 other modules. This list shows each leaked run.
  - The module `test_short_inventory_read.py` left a run in state `created` at site 8888.
  - The module `test_stop.py` left a run in state `created` at site 2222.
  - The module `test_upgrade.py` left a run in state `awaiting_confirmation` at site 4444.
- T013, first run, the end. The budget of the last test stopped the process during the session teardown, with exit code 1. So the output held no report. Issue #3517 holds that defect.
- T013, first run, the multi-site modules. 5 tests failed there. A failed multi-site test left operation `org-run-858c46d2…` running, and the operation held sites 2222 and 3333. Issue #3518 holds that defect. The live-run check cannot see a multi-site operation.
- T014. Each of the 3 modules now records the run of each test in a ledger. A teardown then cancels each live run through `SiteRelease.end_runs`. Each module holds its own teardown helper, by the convention of the suite.
- T014, green. The 3 modules ran together in Edge. The result was 36 passed in 179.63 seconds. The check took 667.7 milliseconds to scan 5 sites after each of 4 module scans. The check read 63 history rows and found 0 leaked live runs. The hold check found 0 leaked holds in 8 records.
- T014, the multi-site modules alone. The modules `test_org_start_double_click.py`, `test_org_upgrade_flow.py`, `test_org_upgrade_history.py`, and `test_capture.py` ran alone. The result was 18 passed and 1 skipped for #3380, with 0 leaks. So the 5 failures of T013 do not occur without the held site.
- T013, second run. The result was 316 passed, 1 skipped for #3380, and 1 error, in 1,421.24 seconds. The hold check found 0 leaked holds. The check scanned 5 sites after each of 62 modules, read 347 history rows, and took 3,643.7 ms, so SC-004 is met.
- T013, second run, the error. The check failed `test_two_operators.py`. The module left run `run-29a3160283ec46599d5015de7ce9fad2` in state `created` at site 2222. The first run did not show this leak, because `test_stop.py` runs first. In the first run, `test_stop.py` left a live run at site 2222. So the create call of `test_two_operators.py` met 409, and the module used that run and created no new run.
- T014, the fourth module. The module `test_two_operators.py` now creates the run of each control test in the fixture `held_run`. The teardown of that fixture cancels each run of the ledger.
- T014, green. The module `test_two_operators.py` ran alone in Edge. The result was 19 passed in 102.12 seconds. Each of the 6 control tests got 201 for its own run, and each teardown ended 1 run. The check read 8 history rows, found 0 leaked live runs, and took 178.9 ms. The hold check found 0 leaked holds.
- T013, third run, green. The result was 316 passed and 1 skipped for #3380, with 0 errors, in 1,455.80 seconds. The check took 3,021.9 milliseconds to scan 5 sites after each of 62 modules. The check read 357 history rows and found 0 leaked live runs. So SC-003 and SC-004 are met. The hold check read 122 records of 8 sites and found 0 leaked holds.
- T013, third run, the end. A local plugin outside the repository gave the last test a budget of 900 seconds, so the session teardown ended and the report printed. Issue #3517 holds the repair of that budget.
- T015, first gate run. The syntax check, Ruff, Black, and mypy passed. The mypy check found no issue in 528 source files. The folder `tests/guardrails` and the two direct test files gave 423 passed and 2 skipped. The test quality gate failed with 18 new findings.
- T015, the 18 findings. 17 were known `weak_zero_assertions` findings of `test_capture.py` and `test_stop.py`. The edits of #3511 moved those tests, so the baseline keys no longer matched. The eighteenth was `missing_ec_empty_input` in the new unit test file.
- T015, the repair. Each of the 17 tests now ends with a plain assertion after its Playwright `expect` call. The unit test file got an empty-row test. The 17 baseline entries are gone, and the baseline diff holds 187 deletions and 0 additions.
- T015, green. The full gate checked 871 files and 729 findings, with 0 new findings. The two direct test files gave 86 passed. The modules `test_capture.py` and `test_stop.py` ran in Edge and gave 30 passed and 1 skipped for #3380, in 105.89 seconds. The check read 27 history rows and found 0 leaked live runs. The hold check found 0 leaked holds.
- T016. The branch base moved to `main` at `985081ca`. The syntax check, Ruff, and Black passed again. The two direct test files gave 86 passed. The full quality gate checked 871 files and 729 findings, with 0 new findings.
