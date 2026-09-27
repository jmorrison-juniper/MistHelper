# Tasks: The picker note and the history note make the noun agree with the count

**Issue**: #3449 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of a count of 1 must fail on the old code. Each test
of the count 0 or 2 must also fail on the old code, because the old note says
"of them" for each count. Each test task comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3449` from `main`, and run
  `scripts/bootstrap_worktree.py`. Move the branch to `main` at `711fc64d`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3449-count-nouns/`.

## Phase 2: User Stories 1 and 2 (the unit tests)

- [x] T003 Write `tests/unit/upgrade_portal/test_issue_3449_count_nouns.py`.
  Read the three texts of each view for the counts 0, 1, and 2. Render each
  real template, and read the whole note.

## Phase 3: User Stories 1 and 2 (the contract tests)

- [x] T004 In `tests/contract/upgrade_portal/test_select.py`, read the picker
  note for 1 match, and for an offset of 1 with 2 matches.
- [x] T005 In `tests/contract/upgrade_portal/test_history_routes.py`, read the
  history note for 1 capture. Also read it for a page of 1 row that starts
  after 1 of 2 captures.

## Phase 4: User Story 3 (the browser journey)

- [x] T006 Write `tests/e2e/upgrade_portal/test_count_nouns_journey.py`. Search
  for the one organization of the stand-in account by its full name. Open the
  history of the stand-in site that holds one capture. Open it again with a
  page size of 1. Save a screenshot of each note.
- [x] T007 Run T003 through T006 on the old code. Record the red result in
  this file.

### The red result (T007)

| Test set | Result on the old code |
| - | - |
| The unit file | 24 of 25 tests failed. |
| The four contract tests | 4 of 4 tests failed. |
| The browser journey | 3 of 3 tests failed. |

The one unit test that passed is the guard of the view fields. That guard
passes before and after the change, because the change adds no field.

Each unit test of a view text failed with an `AttributeError`, because no
text property existed. Each unit test of a template failed, because the note
had no test identifier. The unit test of the words "of them" failed on the
old text. Each contract test failed, because the page held the old sentence.

The screenshots of the red run show the old notes.

| Screenshot | The old note |
| - | - |
| `picker-one-match.png` | The filter matches 1 organizations. This page starts after 0 of them, and one page holds 25 rows. |
| `history-one-capture.png` | The site holds 1 captures. This page starts after 0 of them, and one page holds 25 rows. |

A probe of `/history` with no site found a second defect. The note named one
site for the captures of two sites. Issue #3482 holds that defect.

## Phase 5: The code change

- [x] T008 In `compare/render.py`, add the mixin `HistoryNoteText`. Let
  `HistoryView` inherit it, and add the name to `__all__`.
- [x] T009 In `app/routes/review.py`, let `HistoryPageView` inherit the mixin.
- [x] T010 In `app/routes/select.py`, add the three properties and the static
  rule to `OrgPickerView`.
- [x] T011 Change `select/orgs.html` and `review/history.html`. Print the three
  texts, add the test identifier of each note, and add a Jinja comment.
- [x] T012 Add the two new identifiers to
  `specs/1823-upgrade-capture-portal/contracts/ui-testids.md`.
- [x] T013 Run T003 through T006 green. Read each screenshot.

### The green result (T013)

| Test set | Result on the new code |
| - | - |
| The unit file | 25 of 25 tests passed. |
| The four contract tests | 4 of 4 tests passed. |
| The browser journey | 3 of 3 tests passed. |

| Screenshot | The new note |
| - | - |
| `picker-one-match.png` | The filter matches 1 organization. This page starts after 0 organizations, and one page holds 25 rows. |
| `history-one-capture.png` | The site holds 1 capture. This page starts after 0 captures, and one page holds 25 rows. |
| `history-one-row.png` | The site holds 1 capture. This page starts after 0 captures, and one page holds 1 row. |

## Phase 6: Polish

- [x] T014 [P] Add `changelog.d/issue-3449-count-nouns.md`.
- [x] T015 Run the gates of the plan, and the STE lint of each new Markdown
  file.
- [x] T016 Run the suites of the plan.

### The gate result (T015)

| Gate | Result |
| - | - |
| Compile, Ruff, and Black | Passed. |
| mypy | Passed. The run read 528 files. |
| Bandit, pydocstyle, and vulture | Passed. |
| Pylint | The rating is 9.91. The floor is 9.5. |
| Radon | No block has grade C or worse. |
| Interrogate | The coverage is 99.6 percent. The floor is 90 percent. |
| The test-quality gate | 0 new findings in 4 files. |
| The STE lint of each new Markdown file | Each file scores 82 or more, with 0 errors. |

The STE linter reports 3 long sentences in `ui-testids.md`. The same 3
sentences exist on `main`. This change adds two table rows to that file and
no new error.

### The suite result (T016)

Each suite ran on the branch after the rebase onto `052d5638`.

| Suite | Result |
| - | - |
| The unit and contract suites of the portal | 5223 passed. |
| Twelve browser files of the picker and the history | 118 passed. |
| The integration and guardrail suites | 434 passed, 13 skipped. |

Issue #2689 records seven of the skips, which come from the SDK compatibility
guard. This change touches no integration file and no guardrail file.
- [ ] T017 Open the pull request. Merge it by hand after each check passes.
- [ ] T018 Do the class B deploy of the five files to port 8056, and close
  #3449.

## Dependencies

- T002 comes before T003.
- T003 through T006 come before T007.
- T007 comes before T008 through T012.
- T008 through T012 come before T013.
- T013, T014, and T015 come before T016.
- T016 comes before T017, and T017 comes before T018.
