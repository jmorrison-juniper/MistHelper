# Tasks: Each isolation check of the browser test portal can fail

**Issue**: #3501 | **Plan**: [plan.md](plan.md)

## Phase 1: Red

- [x] T001 Write `tests/unit/upgrade_portal/test_e2e_run_owner_header.py`
  with the six direct cases of the owner check. (US2)
- [x] T002 Add the kept-key test to
  `tests/unit/upgrade_portal/test_runs/test_isolation.py`. (US1)
- [x] T003 Add the one-header test to
  `tests/contract/upgrade_portal/test_upgrade_routes/test_isolation.py`. (US1)
- [x] T004 Run T001 to T003 on the code of today. Record the red result.

## Phase 2: Implementation

- [x] T005 Write the class `RunOwnerHeaderCheck` in
  `tests/support/upgrade_portal_e2e/owner.py`. (US2)
- [x] T006 Remove the seven fields, the eight keys, and `trap_call_counts` from
  `src/upgrade_portal/api/run_controls/models.py`. (US1)
- [x] T007 Make the test branch of `src/upgrade_portal/app/factory.py` write
  the run owner header only. (US1)
- [x] T008 Update `tests/support/upgrade_portal_e2e/__init__.py`. Delete the
  `traps` package. Remove `AuditRecordStore` and its export. (US1)
- [x] T009 Use the owner check in `tests/e2e/upgrade_portal/conftest.py`.
  Remove the header constants and the fixed session guard. Update the
  docstring of the trail guard. (US1, US2)
- [x] T010 Update the three isolation test modules. Name the real isolation
  in each docstring. Repair the five accepted ratchet findings. (US1, US3)

## Phase 3: Green and proof

- [x] T011 Run T001 to T003 and the three isolation modules green.
- [x] T012 Search `src/`, `tests/`, and `wsgi_capture.py` for each removed
  name. Record 0 matches.
- [x] T013 Run every test under `tests/e2e/upgrade_portal/`.
- [x] T014 Run `tests/unit/upgrade_portal`, `tests/contract/upgrade_portal`,
  and `tests/guardrails`. If the catalog guard names a deleted file, remove
  its row from the performance catalog of #2448 and lower the counts.
- [x] T015 Run py_compile, ruff, black, mypy, the quality gate, and the STE
  lint.

## Phase 4: Delivery

- [ ] T016 Commit, push, and open the pull request.
- [ ] T017 Wait for each check and CodeQL. Merge the pull request by hand.
- [ ] T018 Copy the two files under `src/` into the container of port 8056.
  Verify the SHA-256 values and `/healthz`.
- [ ] T019 Comment on #3501, and log the result.

## Dependencies

- T004 needs T001, T002, and T003.
- T006 to T010 need T004.
- T011 needs T005 to T010.
- T013 and T014 need T011.
- T016 needs T012 to T015.