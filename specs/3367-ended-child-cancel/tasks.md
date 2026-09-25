# Tasks: Send no cancel request to a child job that already ended

**Issue**: #3367 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the service unit tests in
  `tests/unit/firmware/test_aggregate_ended_child_cancel.py`. Run them red.
- [x] T002 Change the mixed test in
  `tests/unit/firmware/test_aggregate_upgrade_service.py`. Run it red.
- [x] T003 Add the ended row tests to
  `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`. Run them red.
- [x] T004 Add the panel contract tests to
  `tests/contract/upgrade_portal/test_org_cancel_outcomes_routes.py`. Run them
  red.
- [x] T005 Add the seed and the browser journey. Run the journey red, and read
  each screenshot. The red run used the main versions of the three source
  files. The access point job read `requested`, not `already_ended`.

## Phase 2: The change

- [x] T006 Add the constants and the ended result to the aggregate service.
- [x] T007 Add the note and the `ended` flag to the outcome rows.
- [x] T008 Hide the three lists of an ended child job in the template.
- [x] T009 Run the unit, contract, and browser tests green.

## Phase 3: Finish

- [x] T010 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T011 Add the note to `documentation/upgrade_capture_portal.md` and the
  fragment `changelog.d/issue-3367-ended-child-cancel.md`.
- [x] T012 Run the browser suite of the multi-site progress page. 25 tests in 11 files pass in Edge.

