# Tasks: The options page shows a real note under each type control

**Issue**: #3381 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add `TypedStandInOptionsView` and the two note tests to
  `tests/contract/upgrade_portal/test_upgrade_options.py`.
- [x] T002 Run the two tests on the old template, and record the red result.
  Both tests failed. Each note without a warning read `None`, and the switch
  warning showed correctly.

## Phase 2: The change

- [x] T003 Change line 195 of `options.html` to `default(<text>, true)`.
- [x] T004 Run the two tests green. The contract file gave 51 passed.
- [x] T005 After pull request #3382 merges, rebase, and add the browser check
  of each visible type note to `test_upgrade.py`. The browser test failed on
  the old template, because each of the three notes read `None`. The test then
  passed on the repaired template, and the module gave 15 passed.

## Phase 3: Finish

- [x] T006 Add the release note under `changelog.d/`.
- [x] T007 Run every gate: ruff, black, pydocstyle, interrogate, bandit, radon,
  vulture, the STE lint, and the test quality gate.
- [ ] T008 Run the portal suites and the browser suite of the upgrade portal.
- [ ] T009 After the merge, deploy the template to port 8056 with a class B
  reload, and read the note on the served page.
