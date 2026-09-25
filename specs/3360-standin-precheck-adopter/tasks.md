# Tasks: The browser test store adopts only a standalone pre-check

**Issue**: #3360 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the unit tests in
  `tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py`. Run them
  red on the old stand-in.
- [x] T002 Add the standalone seed `e2e-capture-standalone-0001` to
  `stand_in_capture_index` in `tests/e2e/upgrade_portal/conftest.py`.
- [x] T003 Add the assertion to
  `tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py`. Run the
  journey red on the old stand-in, and read the screenshot.

## Phase 2: The change

- [x] T004 Add the run filter to `_is_precheck`, add `_start_moment`, and pick
  the newest match in `newest_precheck`.
- [x] T005 Run the unit tests and the journey green.

## Phase 3: Finish

- [x] T006 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T007 Run the browser suite of the upgrade portal and the unit and
  contract tests that build the stand-in store.
