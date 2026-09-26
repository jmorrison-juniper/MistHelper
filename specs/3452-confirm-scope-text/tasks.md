# Tasks: The multi-site confirm page names one site for a plan of one site

**Issue**: #3452 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test and each changed test must fail on the old template.
Each test task therefore comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3452` from `main` at `f915ac38`,
  and run `scripts/bootstrap_worktree.py`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3452-confirm-scope-text/`.

## Phase 2: User Stories 1 and 2 (the contract tests)

- [x] T003 Write the contract tests of a plan of one site in
  `tests/contract/upgrade_portal/test_issue_3452_confirm_scope_text.py`.
  Read the whole Warning and the text of each button.
- [x] T004 Write the contract tests of a plan of two sites in the same file.
- [x] T005 Write the contract test of a retry that keeps one site. The file
  also holds two tests of a save with an empty body and a save with a body
  that is not valid JSON. The confirm page then refuses with the code
  `org_upgrade_options_invalid` and shows no scope text.

## Phase 3: User Story 3 (the browser journeys)

- [x] T006 Change `tests/e2e/upgrade_portal/test_selected_site_count.py`. The
  one-site journey reads the three texts on the confirm page. The two-site
  journey continues to the confirm page and reads the three texts.
- [x] T007 Run T003 through T006 on the old template. Record the red result in
  this file.
  - Result: 5 failed and 2 passed.
  - The three contract scope tests failed. The old Warning has no test
    identifier, and the old texts state a plural scope.
  - The two browser journeys failed. Each waited for the element
    `org-upgrade-scope-warning`, and the old page holds no such element.
  - The two tests of a refused save passed, as expected. They guard a path
    that the change does not touch.

## Phase 4: The template change

- [x] T008 Change `upgrade/org_confirm.html`. Add the Boolean value, the three
  texts, the test identifier of the Warning, and a Jinja comment.
- [x] T009 Run T003 through T006 green. Read each screenshot.
  - Result: 7 passed.
  - The screenshot `one-selected-site-confirm.png` shows "Sites: 1", the
    Warning "at the selected site", and the buttons "Take the missing
    pre-check" and "Take a new pre-check for the site".
  - The screenshot `two-selected-sites-confirm.png` shows "Sites: 2", the
    Warning "at each selected site", and the buttons "Take the missing
    pre-checks" and "Take a new pre-check for each site".

## Phase 5: Polish

- [x] T010 [P] Add `changelog.d/issue-3452-confirm-scope-text.md`. The STE
  score is 98.
- [x] T011 Run the gates of the plan, and the STE lint of each new Markdown
  file.
  - Result: each gate passed. The mypy check read 528 files. The
    interrogate coverage is 99.6 percent. The test quality gate found 0 new
    findings in the 2 changed test files.
  - Each new Markdown file scores 96 or more, with no error.
- [x] T012 Run the suites of the plan.
  - The upgrade-portal contract suite and unit suite: 5148 passed.
  - The 13 browser files that open the multi-site confirm page: 39 passed.
  - The upgrade-portal integration suite and the guardrails, after the
    rebase onto `abcf000b`: 374 passed and 2 skipped. The changelog guard
    runs only during a pull request event. The registry holds no option of
    the class `unregistered`.
- [ ] T013 Open the pull request. Merge it by hand after each check passes.
- [ ] T014 Do the class B deploy of `org_confirm.html` to port 8056, and close
  #3452.

## Dependencies

- T002 comes before T003.
- T003 through T006 come before T007.
- T007 comes before T008.
- T008 comes before T009.
- T009, T010, and T011 come before T012.
- T012 comes before T013, and T013 comes before T014.