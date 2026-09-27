# Tasks: The capture history with no site names every site

**Issue**: #3482 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of the page with no site must fail on the old code.
Each new test of the page of one site must pass on the old code, because that
page does not change. Each test task comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3482` from `main`, and run
  `scripts/bootstrap_worktree.py`. Move the branch to `main` at `42e53630`,
  which holds the repair of #3449.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3482-org-history-scope/`.

## Phase 2: User Stories 1 and 2 (the unit tests)

- [x] T003 Write `tests/unit/upgrade_portal/test_issue_3482_history_scope.py`.
  Read the three texts for no site, for a named site, and for a site with no
  name. Prove that the scope with no site reads no row name.
  Render the real template, and read the whole note and the caption.

## Phase 3: User Stories 1 and 2 (the contract tests)

- [x] T004 In `tests/contract/upgrade_portal/test_history_routes.py`, read the
  note and the caption of the page with no site over the captures of two
  sites. Also read the note of the page of one site.

## Phase 4: User Story 3 (the browser journey)

- [x] T005 Write `tests/e2e/upgrade_portal/test_history_scope_journey.py`. Open
  `/history` with no site, and read the note and the caption. Open the history
  of the stand-in site that holds one capture, and read the note and the
  caption. Save a screenshot of each page.
- [x] T006 Run T003 through T005 on the old code. Record the red result in
  this file.

### The red result (T006)

| Test set | Result on the old code |
| - | - |
| The unit file | 12 of 13 tests failed. |
| The three contract tests | 2 of 3 tests failed. |
| The browser journey | 1 of 2 tests failed. |

Each unit test of a scope text failed with an `AttributeError`, because the
class `HistoryScope` did not exist. The one unit test that passed renders the
template with no scope. That test passes before and after the change, because
the template keeps the old texts as its default.

The contract test and the browser test of the page of one site passed. That
result is correct, because the page of one site does not change.

The screenshot `history-every-site.png` of the red run shows the old note of
the page with no site.

| Test | The old note |
| - | - |
| The contract test of two sites | The list shows the stored captures of Test Site. The site holds 2 captures. |
| The browser journey with no site | The list shows the stored captures of E2E Stand-In Site. The site holds 5 captures. This page starts after 0 captures, and one page holds 25 rows. |

The browser fixtures put the 5 captures on two sites. The old note named only
the site of the first row.

## Phase 5: The code change

- [x] T007 In `app/routes/review.py`, add the class `HistoryScope` after
  `read_site_name`. Change the docstring of `read_site_name`.
- [x] T008 In `history_page`, pass `history_scope` in place of `site_name`.
- [x] T009 In `review/history.html`, print the three scope texts in the note
  and in the caption. Name `history_scope` in the variable list, and add a
  Jinja comment.
- [x] T010 In `test_issue_3449_count_nouns.py`, `test_history_view.py`, and
  `test_history_layout.py`, pass a scope in place of `site_name`.

## Phase 6: Proof

- [x] T011 Run T003 through T005 on the new code. Read each screenshot.

### The green result (T011)

| Test set | Result on the new code |
| - | - |
| The unit file | 13 of 13 tests passed. |
| The three contract tests | 3 of 3 tests passed. |
| The browser journey | 2 of 2 tests passed. |

| Screenshot | The new note |
| - | - |
| `history-every-site.png` | The list shows the stored captures of every site. The portal holds 5 captures. This page starts after 0 captures, and one page holds 25 rows. |
| `history-one-site.png` | The list shows the stored captures of E2E Stored Poll Site. The site holds 1 capture. This page starts after 0 captures, and one page holds 25 rows. |

The Runs table of the screenshot with no site shows a site identifier in
place of a site name. The seed runs of the browser fixtures hold no site name.
A real run record stores the site name, so this result is not a defect.
- [x] T012 Write `changelog.d/issue-3482-org-history-scope.md`.
- [x] T013 Run the gates. Record the result in this file.
- [x] T014 Run the suites. Record the result in this file.

### The gate result (T013)

| Gate | Result |
| - | - |
| Compile, Ruff, and Black | Passed. |
| mypy | Passed. The run read 528 files. |
| Bandit, pydocstyle, and vulture | Passed. |
| Pylint | The rating is 9.93. The floor is 9.5. |
| Radon | No block has grade C or worse. |
| Interrogate | The coverage is 99.6 percent. The floor is 90 percent. |
| The test-quality gate | 0 new findings in 6 files. |
| The STE lint of each new Markdown file | Each file scores 96 or more, with 0 errors. |

### The suite result (T014)

Each suite ran on the branch at `42e53630`, which is the tip of `main`.

| Suite | Result |
| - | - |
| The unit and contract suites of the portal | 5239 passed. |
| Twelve browser files of the history | 118 passed, 1 skipped. |
| The integration and guardrail suites | 434 passed, 13 skipped. |

The skipped browser test is the click walk of `test_capture.py`. Issue #3380
records that skip. Issue #2689 records seven of the integration skips. This
change touches no integration file and no guardrail file.

An earlier run of the browser files reported one setup error in
`test_run_controls/test_isolation.py`. The error said that pytest found no
fixture `site_lock`. That run put `test_two_operators.py` between two files
of the folder `test_run_controls`. The folder passes as one argument, with 45
passed. The run above keeps the files of that folder together, and it reports
no error.

- [ ] T015 Open the pull request. Merge it by hand after each check passes.
- [ ] T016 Do the class B deploy of the two source files to port 8056, and
  close #3482.

## Dependencies

- T002 comes before T003.
- T003 through T005 come before T006.
- T006 comes before T007 through T010.
- T007 through T010 come before T011.
- T011, T012, and T013 come before T014.
- T014 comes before T015, and T015 comes before T016.
