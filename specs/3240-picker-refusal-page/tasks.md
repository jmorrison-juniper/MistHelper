# Tasks: Show a picker refusal inside the picker page

**Issue**: #3240 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add contract tests for the browser refusals of `choose_sites` in
  `tests/contract/upgrade_portal/test_select.py`. Run them red.
- [x] T002 Add contract tests for the browser refusals of `choose_mode` and
  `choose_org`. Run them red.
- [x] T003 Add contract tests that a script keeps each envelope and that a
  refusal keeps each stored choice.
- [x] T004 Add the browser journeys in
  `tests/e2e/upgrade_portal/test_picker_refusal_pages.py`. Run them red, and
  read each screenshot.

## Phase 2: The change

- [x] T005 Add the class `PickerRefusal` to `routes/select.py`.
- [x] T006 Change `choose_org`, `choose_mode`, and `choose_sites`, and add the
  helper `site_choice_refusal`.
- [x] T007 Run the contract tests and the browser journeys green.

## Phase 3: Finish

- [x] T008 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T009 Add the note to `documentation/upgrade_capture_portal.md` and the
  fragment `changelog.d/issue-3240-picker-refusal-page.md`.
- [x] T010 Run the full browser suite of the upgrade portal.
