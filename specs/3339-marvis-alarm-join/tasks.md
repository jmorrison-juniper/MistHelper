# Tasks: Menu 270 joins each Marvis Action to its Marvis alarm

**Feature**: `3339-marvis-alarm-join` | **Issue**: #3339, phase 1

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

Each task names its files. A task marked `[P]` can run beside another `[P]` task
in the same phase, because the two tasks touch no common file.

## Phase 1: The search and the record (User Stories 1 and 3)

- [x] **T001** In `src/marvis/actions/client.py`, add `ALARM_GROUP`,
  `ALARM_PAGE_LIMIT`, and `MAX_ALARM_PAGES`. Add `search_marvis_alarms` and its
  five private helpers. Change the docstrings of the module and of
  `MarvisListResult`. Satisfies FR-001, FR-003, FR-004, and FR-014.

- [x] **T002** `[P]` In `src/marvis/actions/model.py`, add
  `MarvisFieldReader.iso_seconds`. Append the eight alarm fields to
  `MarvisActionRecord`, and change the comment of `build`. Satisfies FR-006,
  FR-007, and FR-008.

## Phase 2: The join (User Stories 1, 2, and 3)

- [x] **T003** Create `src/marvis/actions/alarms.py` with `MarvisAlarmIndex` and
  `MarvisAlarmJoin`. Satisfies FR-002, FR-005, FR-010, FR-012, and FR-015.

- [x] **T004** In `src/marvis/actions/operation.py`, call the join in `_export`,
  and change the module docstring. In `src/marvis/actions/__init__.py`, name five
  modules. Satisfies FR-009, FR-011, and FR-013.

## Phase 3: Tests

- [x] **T005** Change the `site_api` fixture of
  `tests/unit/marvis/actions/conftest.py`. The fixture returns an empty alarm
  page by default. The factory name `make_alarm_page` starts with `make_`, so the
  test-quality ratchet reads it as a factory.

- [x] **T006** `[P]` Add the class `TestAlarmSearch` to
  `tests/unit/marvis/actions/test_client.py`. Cover the call values, the next
  links, a refused page, a `None` page, and a repeated link. Also cover the guard,
  another group, a row that is not an object, and an empty page with a link.

- [x] **T007** `[P]` Create `tests/unit/marvis/actions/test_alarms.py`. Cover the
  two keys, the key order, the `last_seen` rule, the eight values, the unmatched
  count, the window, the refused search, and the portal words.

- [x] **T008** `[P]` Update `tests/unit/marvis/actions/test_model.py`. Cover the
  51 columns, the last eight columns, the defaults, and `iso_seconds`.

- [x] **T009** `[P]` Update `tests/unit/marvis/actions/test_properties.py`. Prove
  that `iso_seconds` never raises, and that the join changes no action column.
  Also prove that a failed search leaves every alarm column empty.

- [x] **T010** `[P]` Update `tests/unit/marvis/actions/test_operation.py`. Cover
  the alarm columns of modes 1, 2, and 4, the absent search of mode 3, a refused
  search, and the window start.

- [x] **T011** `[P]` Update `tests/unit/marvis/actions/test_console_visibility.py`.
  Prove that the SSH console shows the two count lines. Also update
  `tests/unit/marvis/actions/test_portal_contract.py`. Prove that the portal marks
  a joined run and a run with a refused search as completed.

## Phase 4: Documentation

- [x] **T012** `[P]` Update the menu 270 paragraph of `README.md`. Satisfies
  FR-016.

- [x] **T013** `[P]` Update `documentation/marvis-actions-api-endpoints.md`.
  Change the summary, the summary table, and the request budget. Add a section for
  the alarm search. Change the list of endpoints that menu 270 does not call, the
  results table, and the code table. After the merge, copy the file to
  `data/Marvis_Actions_API_Endpoints_Report.md` in the main checkout. Satisfies
  FR-016.

- [x] **T014** `[P]` Add the release note
  `changelog.d/issue-3339-marvis-alarm-join.md`.

## Phase 5: Validation

- [x] **T015** Run the local gates: `py_compile`, `ruff`, `black`, `mypy`, the
  menu 270 tests, the guardrail, the ratchet, `bandit`, `radon`, `pydocstyle`,
  `vulture`, and the STE linter.

- [x] **T016** Copy the changed files into `misthelper-app` with `podman cp`, and
  send HUP to the 8055 Gunicorn master. Log START and DONE lines in the
  coordination log. Result on 2026-09-24: the git blob hash of each of the six
  files matches the commit. The 8055 master stayed, and one new worker started.
  The 8056 master received no signal. Issue #3356 records a torn log line from
  this HUP.

- [x] **T017** Run mode 1 and mode 4 on port 8055 with Playwright. Run mode 4
  through SSH on port 2200. Satisfies SC-003 and SC-004. Result: mode 4 for the
  switch topic joined 21 of 33 actions, and mode 1 for all topics joined 33 of
  114 actions. Mode 2 sent no alarm search, and the browser console showed no
  error.

- [x] **T018** Read the container log, `data/script.log`, the CSV file, the
  SQLite table, and the ArangoDB collection. Satisfies SC-001, SC-002, and
  SC-006. Result: each store holds 114 rows and 33 rows with an alarm. The CSV
  file holds 51 columns, and the SQLite table grew from 45 to 53 columns. No cell
  differs between the stores, and the 33 alarm rows match a live
  `searchOrgAlarms` call. The only error line in the logs is the SSH database
  fault of issue #3313.

- [ ] **T019** Open the pull request with `Closes #3339`. Wait for every required
  check, including CodeQL. Squash-merge, then remove the branch and the worktree.

- [x] **T020** Open a new issue for phase 2, the acknowledge step. Label it for a
  human review. Result: issue #3357.

## Dependencies

- T003 needs T001 and T002.
- T004 needs T003.
- T005 needs T001.
- T006 to T011 need T001 to T005.

The validation tasks run in this order.

- T015 needs T001 to T014. T016 needs T015.
- T017 and T018 need T016.
- T019 needs T017 and T018. T020 needs T018, so the pull request can name the
  new issue.
