# Tasks: Menu 270 mode 4, the closed Marvis Actions report

**Feature**: `3342-marvis-closed-report` | **Issue**: #3342

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

Each task names its files. A task marked `[P]` can run beside another `[P]` task
in the same phase, because the two tasks touch no common file.

## Phase 1: The status rule (User Stories 1 and 2)

- [X] **T001** In `src/marvis/actions/selection.py`, add `MODE_EXPORT_CLOSED`,
  add it to `MODES`, and add the tables `MODE_IS_OPEN_VALUES` and
  `MODE_ACTION_NOUNS`. Satisfies FR-001 and FR-003.

- [X] **T002** In `src/marvis/actions/selection.py`, change
  `MarvisTopicSelector` to take the mode. Change `select` and `_count_topics` to
  use the kept `is_open` values. Satisfies FR-003 and FR-005.

- [X] **T003** In `src/marvis/actions/selection.py`, add the property
  `MarvisTopicCount.closed_count` and the Closed column of `_log_table`.
  Satisfies FR-006.

- [X] **T004** In `src/marvis/actions/selection.py`, add the mode 4 line to
  `ask_mode`, and change the prompt text. Satisfies FR-001, FR-002, and FR-013.

## Phase 2: The run flow (User Stories 1 and 4)

- [X] **T005** In `src/marvis/actions/operation.py`, change the refusal of `run`,
  the stop check of `_load`, the selector call of `_filter`, and the words of
  `_refuse`. Satisfies FR-004, FR-007, FR-008, and FR-012.

- [X] **T006** In `src/marvis/actions/operation.py`, move the status summary of
  `_export` into `_log_status_mix`, and add the caution line for an unknown
  status key. Satisfies FR-009 and FR-010.

## Phase 3: The portal (User Story 3)

- [X] **T007** In `web_portal/services/operation.py`, add the mode 4 choice to the
  menu 270 row. Change the comments that count the modes. Satisfies FR-011.

## Phase 4: Tests

- [X] **T008** `[P]` Update `tests/unit/marvis/actions/test_selection.py`. Cover
  the mode 4 tables, the Closed column, the mode 4 select, the mode table, and the
  prompt text.

- [X] **T009** `[P]` Update `tests/unit/marvis/actions/test_operation.py`. Cover
  the mode 4 export, the kept resolution columns, the stop line, the empty filter,
  the unknown status, and the refusal of `5`.

- [X] **T010** `[P]` Update `tests/unit/marvis/actions/test_portal_contract.py`.
  Cover the four mode values, the mode 4 label, and two portal runs of mode 4.

- [X] **T011** `[P]` Update `tests/unit/marvis/actions/test_properties.py`. Prove
  that modes 2 and 4 split the mode 1 rows for any status mix.

- [X] **T012** `[P]` Update `tests/e2e/test_marvis_actions_portal.py`. Cover the
  four choices, the mode 4 label, and the answers that the browser sends for mode 4.

- [X] **T012a** `[P]` Update `tests/unit/marvis/actions/test_console_visibility.py`.
  Prove that the SSH console shows the mode 4 line, the Closed column, the stop
  line, and the caution line.

## Phase 5: Documentation

- [X] **T013** `[P]` Update the menu 270 paragraph of `README.md`. Satisfies
  FR-014.

- [X] **T014** `[P]` Update `documentation/marvis-actions-api-endpoints.md`: the
  mode list, the summary table, the status table note, the request budget, and the
  results table. After the merge, copy the file to
  `data/Marvis_Actions_API_Endpoints_Report.md` in the main checkout. Satisfies
  FR-014.

- [X] **T015** `[P]` Add the release note `changelog.d/issue-3342-marvis-closed-report.md`.

## Phase 6: Validation

- [X] **T016** Run the local gates: `py_compile`, `ruff`, `black`, `mypy`, the
  menu 270 tests, the guardrail, the browser tests, and the STE linter.

- [X] **T017** Copy the changed files into `misthelper-app` with the class B
  method, and send HUP to the 8055 Gunicorn master. Log START and DONE lines in
  the coordination log.

- [ ] **T018** Run mode 4 and mode 2 on port 8055 with Playwright. Run mode 4
  through SSH on port 2200. Satisfies SC-003 and SC-004.

- [ ] **T018a** The live screenshot of T018 showed the Closed value on a second
  line of the portal log. In `src/marvis/actions/selection.py`, fit each column of
  `_log_table` to its widest cell, and move the Name column to the end. Update the
  table tests in `test_selection.py` and `test_console_visibility.py`. Deploy the
  file again, and repeat the Playwright check. Satisfies FR-015 and SC-006. See
  research R9.

- [ ] **T019** Read the container log and `data/script.log`. Read the CSV file,
  the SQLite table, and the ArangoDB collection. Satisfies SC-001 and SC-002.

- [ ] **T020** Open the pull request with `Closes #3342`. Wait for every required
  check, including CodeQL. Squash-merge, then remove the branch and the worktree.

## Dependencies

- T002 needs T001. T003 and T004 need T001.
- T005 and T006 need T002.
- T007 needs T001.
- T008 to T012a need T001 to T007.
- T016 needs T001 to T015. T017 needs T016. T018 and T019 need T017.
- T018a needs T018.
- T020 needs T018, T018a, and T019.
