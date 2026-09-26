# Tasks: The multi-site options page states the correct site noun

**Issue**: #3447 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test must fail on the old template. Each test task
therefore comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3447` from `main` at `d54eb6a7`,
  and run `scripts/bootstrap_worktree.py`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, and
  `checklists/requirements.md` in `specs/3447-selected-site-count/`.
- [x] T003 File issue #3449 for the same defect on the organization page and
  on the capture history page.

## Phase 2: User Stories 1 and 2 (the contract tests)

- [x] T004 Write the contract tests of one selected site and of two selected
  sites. Put them in
  `tests/contract/upgrade_portal/test_issue_3447_selected_site_count.py`.
- [x] T005 Write the retry tests in the same file. Cover a retry of one site,
  the end of that retry, and a retry of two sites.

## Phase 3: User Story 3 (the browser journey)

- [x] T006 Write the browser journey in
  `tests/e2e/upgrade_portal/test_selected_site_count.py`. Select one site,
  and then two sites, through the real site picker. Save one screenshot of
  each note.
- [x] T007 Run T004 through T006 on the old template. Record the red result
  in this file.
  Red result on `d54eb6a7`: 7 of 7 tests failed. The 5 contract tests found
  no note with the test identifier. The 2 browser journeys found no such
  note. A probe of the old page read the text "One operation targets 1
  selected sites." for one site. The screenshot
  `red-one-selected-sites.png` shows the same text.

## Phase 4: The template change

- [x] T008 Change the note in
  `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`. Add
  the two `set` statements, the Jinja comment, and the test identifier.
- [x] T009 Run T004 through T006 green. Read each screenshot.
  Result: 7 tests passed in 12.5 seconds. The screenshot of one site shows
  "1 selected site". The screenshot of two sites shows "2 selected sites".
  The confirm page shows "Sites: 1".

## Phase 5: Polish

- [x] T010 [P] Add `changelog.d/issue-3447-selected-site-count.md`.
- [x] T011 Run the gates of the plan, and the STE lint of each new Markdown
  file.
  Result: each gate passed. The test-quality gate asked for an empty body and
  a malformed JSON body. Two contract tests now send each body to the retry
  API. The retry reads no body, so both tests expect the same retry of one site.
- [x] T012 Run the upgrade-portal unit suite, contract suite, integration
  suite, and the browser files that read the options page.
  Result: the contract and unit suites passed 5,085 tests. The integration and
  guardrail suites passed 359 tests and skipped 2 tests. The 6 browser files
  passed 18 tests.
- [ ] T013 Open the pull request. Merge it by hand after each check passes.
- [ ] T014 Do the class B deploy of the template to port 8056, and close
  #3447.

## Dependencies

- T004 through T006 come before T007.
- T007 comes before T008.
- T008 comes before T009.
- T009, T010, and T011 come before T012.
- T012 comes before T013, and T013 comes before T014.
