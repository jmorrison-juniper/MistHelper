# Tasks: A cancel that stops part of the work makes the operation read cancelled

**Issue**: #3371 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add the service unit tests in
  `tests/unit/firmware/test_aggregate_mixed_cancel_state.py`. Run them red.
  The red run failed the 6 mixed cases and passed the 11 unchanged cases.
- [x] T002 Add the second seeded operation to
  `tests/e2e/upgrade_portal/org_ended_seeds.py`.
- [x] T003 Add the browser journey
  `tests/e2e/upgrade_portal/test_org_mixed_cancel_state_journey.py`. Run it
  red, and read each screenshot. The red run read `completed` in the status
  card after the cancel.

## Phase 2: The change

- [x] T004 Add the helper `_final_word`, and call it from `_settled_state` and
  from `_combined_site_status`.
- [x] T005 Run the unit tests and the browser journey green.

## Phase 3: Finish

- [x] T006 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate.
- [x] T007 Add the note to `documentation/upgrade_capture_portal.md` and the
  fragment `changelog.d/issue-3371-mixed-cancel-state.md`.
- [x] T008 Run the unit, contract, and integration suites, and the browser
  suite of the multi-site pages.
