# Tasks: Multi-site upgrades in the history

**Issue**: #3248
**Plan**: [plan.md](./plan.md)

## Phase 1: Red tests

- [x] T001 Write the store tests in `tests/unit/upgrade_portal/test_store_history.py`. Prove that `list_runs` excludes the operation records, and prove the query of `list_operations`.
- [x] T002 Write the shaper tests in `tests/unit/upgrade_portal/test_org_history.py`.
- [x] T003 Write the route tests in `tests/contract/upgrade_portal/test_history_operations.py`.
- [x] T004 Write the browser journey in `tests/e2e/upgrade_portal/test_org_upgrade_history.py`.
- [x] T005 Run the four files and record the red result.

## Phase 2: The store and the shaper

- [x] T006 Add the exclusion filter to `_RUN_LIST_HEAD`, and update the test that expected no filter.
- [x] T007 Add `OPERATION_LIST_FIELDS`, `OperationQuery`, `OperationListPage`, and `list_operations`.
- [x] T008 Add `src/upgrade_portal/upgrade/org_history.py`.

## Phase 3: The route and the page

- [x] T009 Add the seam, the fallback, and the section helper to `review.py`.
- [x] T010 Record the seam call in `seam_shapes.py`.
- [x] T011 Add the section to `review/history.html`.
- [x] T012 Write `created_at` in `_build_record`.

## Phase 4: The browser test support

- [x] T013 Add `operation_lister` to `E2ERecordOverrides`, and pass it from the browser test support.
- [x] T014 Add `list_operations` to `PortalRecordStore`, and skip the operation records in `list_runs`.
- [x] T015 Update the two isolation tests that build the record overrides by position.
- [x] T016 Inject an operation stand-in in `test_lock_free_reads.py`, because that test selects an organization.

## Phase 5: Proof

- [x] T017 Run the four new test files and the existing history tests. All tests pass.
- [x] T018 Run the gates: compile, ruff, black, mypy, pylint, interrogate, vulture, pydocstyle, the test quality ratchet, and the STE linter.
- [x] T019 Take the screenshots of the history page, and read each screenshot.
- [x] T020 Add the release note `changelog.d/issue-3248-multisite-history.md`.
