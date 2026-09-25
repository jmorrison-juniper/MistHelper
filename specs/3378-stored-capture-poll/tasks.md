# Tasks: The poll of a stored capture stops

**Issue**: #3378 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the unit tests in
  `tests/unit/upgrade_portal/test_capture_stored_state.py`. Run them red on the
  old code.
- [x] T002 Move the stored seed of
  `tests/contract/upgrade_portal/test_capture_status.py` to the shipped shape.
  Add the cases for `partial` and for a capture that this release cannot
  compare. Run them red on the old code.
- [x] T003 Add the seed `e2e-capture-stored-poll-0001` to
  `stand_in_capture_index` in `tests/e2e/upgrade_portal/conftest.py`.
- [x] T004 Add the journey
  `tests/e2e/upgrade_portal/test_stored_capture_poll_journey.py`. Run it red on
  the old code, and read the screenshot.

## Phase 2: The change

- [x] T005 Change `stored_progress` in
  `src/upgrade_portal/app/routes/capture.py`. Correct the poll interval in the
  docstring of `capture_status`.
- [x] T006 Correct the docstring of `_result` in
  `src/upgrade_portal/app/routes/org_postcheck.py`, and the stub in
  `tests/unit/upgrade_portal/test_org_postcheck_bridge.py`.
- [x] T007 Correct the status section of
  `specs/1823-upgrade-capture-portal/contracts/http-api.md`.
- [x] T008 Run the unit tests, the contract tests, and the journey green. Read
  each screenshot.

## Phase 3: Finish

- [x] T009 Add the release note
  `changelog.d/issue-3378-stored-capture-poll.md`.
- [x] T010 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T011 Run the portal suites and the browser suite of the upgrade portal.
