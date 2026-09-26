# Tasks: The multi-site texts name one site with a singular noun

**Issue**: #3462 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: Each new test of one site must fail on the old code. Each test of
two or more sites must pass on the old code, because it guards the plural text
that was already correct. Each test task comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3462` from `main` at `abcf000b`,
  and run `scripts/bootstrap_worktree.py`.
- [x] T002 Add the start refusal to the body of #3462. Write `spec.md`,
  `research.md`, `plan.md`, and `checklists/requirements.md` in
  `specs/3462-site-list-noun/`.

## Phase 2: User Story 2 (the unit tests)

- [x] T003 Write `tests/unit/upgrade_portal/test_issue_3462_site_list_noun.py`.
  Read the place words for zero, one, two, and twelve sites. Read the whole
  text of each save refusal for one site, two sites, and twelve sites.
- [x] T004 Change `tests/unit/upgrade_portal/test_org_site_records.py` to the
  texts of one site.

## Phase 3: User Stories 1, 2, and 3 (the contract tests)

- [x] T005 In `tests/contract/upgrade_portal/test_org_site_records_routes.py`,
  change each text of one site. Add a test of the whole banner for one short
  site and for two short sites. Add a test of the whole save refusal for one
  site.
- [x] T006 In `tests/contract/upgrade_portal/test_org_precheck_routes.py`,
  change the start refusal of one site. Add a test of the start refusal for
  two sites.
- [x] T007 In `tests/contract/upgrade_portal/test_org_child_controls_routes.py`,
  change the two texts of one site.

## Phase 4: User Story 4 (the browser journeys)

- [x] T008 Change `tests/e2e/upgrade_portal/test_short_inventory_read.py` and
  `tests/e2e/upgrade_portal/test_org_empty_site.py` to the texts of one site.
  The short-read journey also reads the whole banner.
- [x] T009 Run T003 through T008 on the old code. Record the red result in
  this file.
  - The red run of the tests outside the browser gave 13 failed and 102
    passed. Each failed test reads a text of one site.
  - The red run of the browser journeys gave 2 failed and 1 passed. The
    short-read journey failed at line 223, because the banner read "at these
    sites: E2E Short Read Site". The empty-site journey failed at line 101,
    because the refusal read "at these sites: E2E Empty Site". The single-site
    journey passed, because the single-site page does not change.

## Phase 5: The code change

- [x] T010 Change `upgrade/org_site_records.py`. Add the place words, the
  method `place_text`, and the new templates of the three save refusals.
- [x] T011 Change `app/routes/org_upgrade.py`. Import `OrgSiteRefusal`, and
  format the place words into the start refusal.
- [x] T012 Change `upgrade/org_options.html`. Add the Boolean value, the two
  nouns of the banner, and a Jinja comment.
- [x] T013 Run T003 through T008 green. Read each screenshot.
  - The green run of the tests outside the browser gave 115 passed.
  - The green run of the browser journeys gave 3 passed. The screenshots
    `multi-site-banner.png`, `multi-site-refusal.png`, and
    `empty-site-refusal.png` show "at this site" and "devices of that site".

## Phase 6: Polish

- [x] T014 [P] Add `changelog.d/issue-3462-site-list-noun.md`. The STE score is 98.
- [x] T015 Run the gates of the plan, and the STE lint of each new Markdown
  file. Ruff, Black, mypy, Bandit, pydocstyle, vulture, and the test-quality
  gate passed. Pylint rated the code 9.95, and Radon found no block of grade C
  or worse. Each Markdown file scored 95 or more, with 0 errors.
- [x] T016 Run the suites of the plan.
  - The unit and contract suites of the portal gave 5,160 passed.
  - The 14 browser files that open the multi-site options page gave 44 passed.
  - After the rebase onto `0a72a555`, the integration and guardrail suites
    gave 424 passed and 13 skipped. Each skip names a missing capability: the
    compose services, the Mist API credentials, a pull request event, or an
    option of the class `unregistered`.
- [ ] T017 Open the pull request. Merge it by hand after each check passes.
- [ ] T018 Do the class B deploy of the three files to port 8056, and close
  #3462.

## Dependencies

- T002 comes before T003.
- T003 through T008 come before T009.
- T009 comes before T010, T011, and T012.
- T010, T011, and T012 come before T013.
- T013, T014, and T015 come before T016.
- T016 comes before T017, and T017 comes before T018.
