# Tasks: Show a final multi-site operation as final

**Issue**: #3225 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the service unit tests in
  `tests/unit/firmware/test_aggregate_final_cancel.py`. Run them red.
- [x] T002 Add the text unit tests in
  `tests/unit/upgrade_portal/test_org_cancel_text.py`. Run them red.
- [x] T003 Add the route contract tests in
  `tests/contract/upgrade_portal/test_org_final_cancel_routes.py`. Run them red.
- [x] T004 Add the contract tests of the earlier job marker to
  `tests/contract/upgrade_portal/test_org_upgrade_routes.py`. Run them red.
- [x] T005 Add the unit test of the finished state list. Run it red.
- [x] T006 Add the browser journey in
  `tests/e2e/upgrade_portal/test_org_final_operation_page.py`. Run it red, and
  read each screenshot.

## Phase 2: The change

- [x] T007 Add the constant, the message, the error class, and the guard to the
  aggregate service.
- [x] T008 Add the class `OrgCancelText`.
- [x] T009 Change the cancel route, the earlier job path, and both summaries.
- [x] T010 Change the template, the page script, and the style sheet.
- [x] T011 Update `tests/e2e/upgrade_portal/test_org_upgrade_flow.py`.
- [x] T012 Run the unit, contract, and browser tests green.

## Phase 3: Finish

- [x] T013 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T014 Add the note to `documentation/upgrade_capture_portal.md` and the
  fragment `changelog.d/issue-3225-final-operation-page.md`.
- [x] T015 Run the browser suite of the multi-site progress page.
