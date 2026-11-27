# Tasks: Preserve CSV Carriage Returns

**Input**: Numeric record `specs/numbered/0/0/1/2/3/1/0/1/4776-csv-carriage-returns/`. Design files are `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/csv-cell-presentation.md`, and `design/quickstart.md`.

**Order**: Write the test tasks T003 to T009 first. Run them on `main`. Each new carriage return assertion must fail before T010 to T013 start.

**Environment**: Run Python from the worktree root with the project `.venv`. Use `python -m` commands as listed in the local gates table at RC-38.

## Format

- **[P]**: The task edits a different file from the other tasks in its phase.
- **[FR]**: Requirement IDs from `spec.md`.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. Status `absent` means the change is not on `main` yet.

## Phase 1: Verify the Baseline

- [ ] T001 [P] [FR-001] Verify the carriage return removal on `main`. Path: `src/foundation/models/data/data_processing_utils.py` line 167. Acceptance: line 167 removes carriage returns on `main`. Verify: `python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`. Status: verified-present (RC-01).
- [ ] T002 [P] [FR-010] Verify that the EX report writer has no shared escape call. Path: `src/operations/exporting/ex_hardware_inventory/report/csv_file.py` line 50. Acceptance: the file has a `csv.DictWriter` and no `escape_multiline` call. Verify: `python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_csv.py`. Status: verified-present (RC-16, RC-27).

## Phase 2: Tests First

- [ ] T003 [P] [FR-007, FR-001] Replace the removal assertion with the preservation assertion. Path: `tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py` lines 262 to 267. Acceptance: input `a`, carriage return, line feed, `b` returns `a`, carriage return, backslash, `n`, `b`. Verify: `python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`. Status: absent (RC-21).
- [ ] T004 [P] [FR-002, FR-004] Add presenter tests in a new file. Path: `tests/unit/config/foundation/models/dataproc/test_csv_cell_presenter.py`. Acceptance: four tests cover each carriage return, literal backslash-r text, non-text values, and unchanged raw rows. Verify: `python -m pytest tests/unit/config/foundation/models/dataproc/test_csv_cell_presenter.py`. Status: absent (RC-67, RC-68).
- [ ] T005 [FR-002, FR-003, FR-004] Add `write_to_csv` tests for CSV cells, raw rows, and list values. Path: `tests/unit/export/test_data_exporter.py`. Acceptance: three tests read the cell back, keep the raw row, and present a carriage return in a list item. Verify: `python -m pytest tests/unit/export/test_data_exporter.py`. Status: absent (RC-22).
- [ ] T006 [P] [FR-003, FR-005] Add 52-week CSV and SQLite tests. Path: `tests/unit/test_device_events_52w_exporter_extended.py`. Acceptance: two tests show the CSV presentation and keep raw carriage returns in SQLite. Verify: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`. Status: absent (RC-23).
- [ ] T007 [P] [FR-005] Add the SQLite raw carriage return test. Path: `tests/unit/db/sle_window_summary/test_backend_preservation.py`. Acceptance: the stored value keeps the carriage return character. Verify: `python -m pytest tests/unit/db/sle_window_summary/test_backend_preservation.py`. Status: absent (RC-26).
- [ ] T008 [FR-005] Add the non-CSV dispatch test and the double-presentation test. Path: `tests/unit/export/test_data_exporter.py`. Acceptance: the router receives raw carriage returns, and pre-escaped text is not escaped twice. Verify: `python -m pytest tests/unit/export/test_data_exporter.py`. Status: absent (RC-22).
- [ ] T009 [P] [FR-001] Update the endpoint family expectations. Path: `tests/unit/export/test_endpoint_family_exporter.py` lines 687 and 692. Acceptance: expected notes keep the carriage returns from the input. Verify: `python -m pytest tests/unit/export/test_endpoint_family_exporter.py`. Status: absent (RC-24, RC-25).

## Phase 3: Implementation

- [ ] T010 [P] [FR-001, FR-006] Keep carriage returns in the shared normalizer. Path: `src/foundation/models/data/data_processing_utils.py` lines 157 to 161 and line 167. Acceptance: the function keeps carriage returns, keeps line feed escaping, and keeps list joining. Verify: `python -m pytest tests/unit/config/foundation/models/dataproc/test_data_processing_utils.py`. Status: absent (RC-01, RC-70).
- [ ] T011 [P] [FR-002, FR-004, FR-008] Create the presenter package. Paths: `src/foundation/models/csv_presentation/__init__.py` and `src/foundation/models/csv_presentation/cell_presenter.py`. Acceptance: `prepare_rows` copies rows, escapes line feeds, and presents carriage returns. `present_carriage_returns` replaces each carriage return with two characters. Verify: `python -m pytest tests/unit/config/foundation/models/dataproc/test_csv_cell_presenter.py`. Status: absent (RC-68).
- [ ] T012 [FR-002, FR-003, FR-004, FR-008] Use the presenter in `write_to_csv`. Path: `src/operations/exporting/export/data_exporter.py` line 408 and the import block. Acceptance: `write_to_csv` calls `CsvCellPresenter.prepare_rows`, keeps the function at 25 lines, and leaves the caller rows unchanged. Verify: `python -m pytest tests/unit/export/test_data_exporter.py`. Status: absent (RC-04, RC-05).
- [ ] T013 [FR-003, FR-005] Present carriage returns in the 52-week CSV branches. Path: `src/operations/exporting/export/device_events_52w_exporter.py` lines 312 to 314 and 327 to 328, plus the import block. Acceptance: the CSV branches present carriage returns. The SQLite branch does not change. Verify: `python -m pytest tests/unit/test_device_events_52w_exporter_extended.py`. Status: absent (RC-11 to RC-13).

## Phase 4: Documentation and Review

- [ ] T014 [P] [FR-009] Add the changelog fragment. Path: `changelog.d/issue-4776-csv-carriage-returns.md`. Acceptance: the fragment has one `###` heading and one `Fixed` bullet that names issue 4776. Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: absent (RC-31).
- [ ] T015 [FR-008] Review the changed blocks. Paths: `src/foundation/models/data/data_processing_utils.py`, `src/foundation/models/csv_presentation/cell_presenter.py`, `src/operations/exporting/export/data_exporter.py`, and `src/operations/exporting/export/device_events_52w_exporter.py`. Acceptance: each new line has a same-line comment, each new action has logs, and each changed function stays at 25 lines or fewer. Verify: `pylint src/ --fail-under=9.5`. Status: open. The pylint gate checks structure only. The reviewer records the comment and log check in the pull request body.

## Phase 5: Delivery

- [ ] T-LOCAL-GATES [FR-001 to FR-010] Run each applicable gate from the local gates table. Paths: the twelve files in `plan.md` Change Map. Acceptance: each applicable gate passes. Each gate that does not apply has a reason in the pull request body. Not applicable: pip-audit (no dependency change), menu reference (no menu change), Playwright (no UI change), ops portal, and ops platform. Verify: the two `pytest-chunks` commands in the Full tests row of RC-38. Status: open.
- [ ] T-PR [FR-009] Commit, push, and open the pull request. Paths: the twelve files in `plan.md` Change Map and this record folder. Acceptance: the commit uses Conventional Commits. The branch is `fix/4776-csv-carriage-returns`. The body contains `Closes #4776`. PR #4813 closes after the push, with a preservation proof. Verify: `python -m py_compile MistHelper.py`. Status: open (RC-59).
- [ ] T-REMOTE-CI [FR-001 to FR-010] Watch the remote checks. Path: the new pull request. Acceptance: every required check passes. CodeQL passes before the `auto-merge` label is added. Verify: the Full tests row of RC-38, which the CI shards repeat. Status: open.
- [ ] T-MERGE [SC-006] Enable auto-merge after the orchestrator authorizes the merge. Path: the new pull request. Acceptance: the squash merge lands once. The branch and the worktree are removed. Verify: `python -m py_compile MistHelper.py` on the merged `main`. Status: open.

## Dependencies

- T010 depends on T003.
- T011 depends on T004.
- T012 depends on T005, T008, T010, and T011.
- T013 depends on T006 and T011.
- T014 and T015 depend on T010 to T013.
- T-LOCAL-GATES depends on T007, T009, T012, T013, T014, and T015.
- T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI and the orchestrator authorization.

## Guard Rules

- Warning: never push to `main` directly. A direct push skips the required checks.
- Caution: a closed pull request needs a preservation proof. Record the surviving branch and commit first.
