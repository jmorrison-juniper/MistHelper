# Tasks: The Captures table of the history with no site names the site of each row

**Issue**: #3486 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of the page with no site must fail on the old code.
Each new test of the page of one site must pass on the old code, because that
page does not change. Each test task comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3486` from `main`, and run
  `scripts/bootstrap_worktree.py`. Move the branch to `main` at `751077a6`,
  which holds the repair of #3482.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3486-history-site-column/`.

## Phase 2: User Stories 1 and 2 (the unit tests)

- [x] T003 Write `tests/unit/upgrade_portal/test_issue_3486_history_site_column.py`.
  Read the three properties of `HistoryCaptureColumns` for no site and for one
  site. Read `record_site_label` for a name, for an identifier alone, and for
  no value. Read the two site fields that `page_rows` adds. Render the real
  template for every site, for one site, and with no column value. Read the
  ten width rules and the clip rule of the stylesheet.

## Phase 3: User Stories 1 and 2 (the contract tests)

- [x] T004 In `tests/contract/upgrade_portal/test_history_routes.py`, read the
  headers, the site cells, and the caption of the page with no site over the
  captures of two sites. Also read the headers and the caption of the page of
  one site.

## Phase 4: User Story 3 (the browser journey)

- [x] T005 Write `tests/e2e/upgrade_portal/test_history_site_column_journey.py`.
  Open `/history` with no site. Read the headers and the site cell of each of
  the five seed captures. Measure the Open control and the row at three window
  widths. Push the Site header, and read the order of the site cells. Open the
  history of the site that holds one capture, and read the headers. Save a
  screenshot of each page.
- [x] T006 Run T003 through T005 on the old code. Record the red result in
  this file.

### The red result (2026-09-27, on `751077a6`)

- The unit file gave 23 failures and 1 pass. Each failure named a missing
  value: `HistoryCaptureColumns`, `record_site_label`, the row field
  `site_text`, or the width rule of 18 percent. The render with no column
  value passed, because that render does not change.
- The four contract tests gave 3 failures and 1 pass. The empty page with no
  site printed `colspan="9"`. The page of one site passed.
- The journey gave 2 failures and 4 passes. The header check read nine
  headers. The sort check pressed the Started header, so the row of the stored
  poll site sat between the rows of the stand-in site. The three width checks
  and the check of one site passed, because they guard the layout of today.

## Phase 5: The code change

- [x] T007 In `app/routes/review.py`, rename `run_site_label` to
  `record_site_label`, and change its docstring. Add the constant
  `SITE_TEST_ID_PREFIX` and the two field names.
- [x] T008 In `page_rows`, add the site text and the site test identifier to
  each row. Add the action logs.
- [x] T009 Add the class `HistoryCaptureColumns` after `HistoryScope`. In
  `history_page`, give the template one instance as `history_columns`.
- [x] T010 In `review/history.html`, read the three column values with a
  default. Print the table class, the Site header, the site cell, the caption,
  and the span of the empty row. Name `history_columns` in the variable list,
  and add a Jinja comment.
- [x] T011 In `static/css/portal.css`, add the width set of ten columns and
  the clip rule of the site cell. In
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md`, add the row of
  `history-site-{capture_id}`.

## Phase 6: Proof

- [x] T012 Run T003 through T005 on the new code. Read each screenshot.
  Record the green result in this file.

### The green result (2026-09-27)

- The first browser run failed at 1024 pixels. Research R4 records the two
  faults and the probe that measured each column. The final shares are 12,
  13, 14, 7, 9, 7, 12, 7, 9, and 10 percent, and the floor is 60rem.
- The journey now holds 7 tests. The new test
  `test_the_site_column_hides_no_sort_arrow` compares the headers of the two
  tables at 1280 pixels.
- The red proof of the new test: a Devices share of 6 percent made the test
  fail with `The Site column hides the sort arrow of ['Devices']`. The share
  then went back to 7 percent.
- The journey gave 7 passes in Microsoft Edge. The unit file gave 24 passes.
  The unit and contract files of the history gave 192 passes in 8 files.
- The first load of the history with no site took 671 milliseconds. Each
  later load took 71 to 155 milliseconds.
- The screenshot at 1024 pixels shows each capture row on one line. The word
  `post` does not break, and each Open control is in the window. The site
  names clip with an ellipsis.
- The screenshot at 1280 pixels shows each header whole, and the name
  `E2E Stored Poll Site` fits its cell.
- The screenshots show two defects outside this fix. Issue #3491 records the
  Runs table and the Multi-site upgrades table, which break the site text in
  a narrow window. Issue #3492 records the seed captures, which hold no device
  type counts.
- [x] T013 Write `changelog.d/issue-3486-history-site-column.md`.
- [x] T014 Run the gates. Record the result in this file.
- [x] T015 Run the suites. Record the result in this file.

### The gates and the suites (2026-09-27)

- Ruff, Black, mypy, Bandit, pydocstyle, and vulture passed. mypy read 528
  files. Pylint rated the code 9.93. Radon found no block of grade C or
  worse. Interrogate gave a coverage of 99.6 percent.
- The test-quality gate first found one bare assert in the unit file. The
  assert now holds a message, and the gate reports 0 new findings.
- The unit and contract suites of the portal gave 5267 passes on `751077a6`.
  The branch then moved to `df6027b8`. That commit changed no file of the
  portal.
- On `df6027b8`, the integration and guardrail suites gave 430 passes and 13
  skips. The old base gave 434 passes. The commit `df6027b8` rewrote four
  guardrail files and removed six test functions.
- On `df6027b8`, the twelve browser files of the history and the new journey
  gave 125 passes and 1 skip. Issue #3380 records the skip.
- On `df6027b8`, the four repository tests that read the Markdown files and
  the package layout gave 92 passes.
- [ ] T016 Open the pull request. Merge it by hand after each check passes.
- [ ] T017 Do the class B deploy of the three files to port 8056, and close
  #3486.

## Dependencies

- T002 comes before T003.
- T003 through T005 come before T006.
- T006 comes before T007 through T011.
- T007 through T011 come before T012.
- T012, T013, and T014 come before T015.
- T015 comes before T016, and T016 comes before T017.
