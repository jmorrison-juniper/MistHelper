# Tasks: A later site check names an incomplete site list

**Issue**: #3439 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: SC-001 asks for each new test of a refusal to fail on the old code.
Each test task therefore comes before its code task. Each regression test of
FR-006, FR-007, and FR-010 passes on both code versions.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3439` from `main` at `3d8cce8c`,
  and run `scripts/bootstrap_worktree.py`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, `data-model.md`,
  `quickstart.md`, and `checklists/requirements.md` in
  `specs/3439-later-site-checks/`.
- [x] T003 File issue #3441 for the plan with no site. Name the issue in the
  Out of Scope section of `specs/3439-later-site-checks/spec.md`.

## Phase 2: Foundational (the error and the missing-site rule)

These tasks block User Stories 1, 2, and 3.

- [ ] T004 Write the red unit tests of the missing-site rule in
  `tests/unit/upgrade_portal/test_issue_3439_site_checks.py`.
  - The method `SiteList.missing_sites` returns each missing site in the order
    of the request.
  - The raise rule of `SiteListIncompleteError` does not raise for a count of
    zero or for a whole list.
  - The raise rule raises for a missing site of a partial list, and it writes
    one warning.
  - The function `find_site` raises for a missing site of a partial list. It
    also raises after a failed first page.
  - The function `find_site` returns the record of a listed site of a partial
    list. It returns None for a missing site of a whole list.
- [ ] T005 Write the red unit tests of `selected_rows` in
  `tests/unit/upgrade_portal/test_issue_3439_site_checks.py`.
  - The function raises for a missing site of a partial list.
  - It returns the rows of the listed sites in the order of the request.
  - It returns an empty list for a missing site of a whole list.
- [ ] T006 Run T004 and T005 on the old code. Record the red result in
  `specs/3439-later-site-checks/tasks.md`.
- [ ] T007 Add the three constants, `SiteListIncompleteError`, and
  `SiteList.missing_sites` to `src/upgrade_portal/app/routes/select.py`.
- [ ] T008 Change `find_site` in `src/upgrade_portal/app/routes/select.py`, so
  that it raises the error for a missing site of a partial list.
- [ ] T009 Add the application error handler of `SiteListIncompleteError` to
  `src/upgrade_portal/app/routes/select.py`. A browser page receives the
  shared error page. A script receives the error envelope. A refused form post
  from a browser also receives the link back to the form.
- [ ] T010 Add the later-check organization, its operator, its three sites,
  and the settled operation of the retry in
  `tests/e2e/upgrade_portal/later_check_seeds.py`.
- [ ] T011 Add the later-check cloud session and the header rule of the
  stand-in reader in `tests/e2e/upgrade_portal/conftest.py`. Also add the
  device series of the three sites, the operator record, the retry seed, and
  the page fixture.

## Phase 3: User Story 1 (P1), the single-site steps

**Goal**: The inventory page, the inventory answer, and the capture start name
an incomplete site list.

**Independent test**: Open a site of page two in the single-site mode while
the site read loses page two. Then start a capture of that site.

- [ ] T012 [US1] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  the inventory page, the inventory answer, and the capture start. Check that
  the capture start stores no capture and takes no lock. Also cover a site of
  a kept page and the 404 answers of a whole list.
- [ ] T013 [US1] Run T012 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
- [ ] T014 [US1] Add the single-site journeys to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot of
  each page, and read it.

## Phase 4: User Story 2 (P1), the multi-site site choice

**Goal**: The site choice post names an incomplete site list, and a browser
returns to the site picker with a Caution message.

**Independent test**: Select one site of page one and one site of page two.
Press the forward control while the site read loses page two.

- [ ] T015 [US2] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  the browser post, the script post, a choice of kept sites only, and the
  stored choice after a refusal. Also cover the 404 answer of a whole list.
- [ ] T016 [US2] Run T015 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
- [ ] T017 [US2] Add `site_set_refusal` to
  `src/upgrade_portal/app/routes/select.py`. Change `site_choice_refusal` to
  return its answer.
- [ ] T018 [US2] Add the site choice journey to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot, and
  read it.

## Phase 5: User Story 3 (P1), the multi-site plan steps

**Goal**: The options page, the options save, the confirm page, the pre-check
start, and the retry name an incomplete site list.

**Independent test**: Save a plan that holds a site of page two. Then open
each later step while the site read loses page two.

- [ ] T019 [US3] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  each of the five steps in a browser and in a script. Check that no plan, no
  saved options, no capture, no lock, and no retry reference change. Also
  cover the kept-site pass, the 404 answers of a whole list, and the save
  request with no `selected_types` field.
- [ ] T020 [US3] Run T019 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
- [ ] T021 [US3] Change `selected_rows` in
  `src/upgrade_portal/app/routes/org_upgrade.py`, so that it raises the error
  for a missing site of a partial list.
- [ ] T022 [US3] Add the plan step journeys and the retry journey to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot of
  each page, and read it. If the state cell of the pre-check card keeps the
  text "starting" after a refusal, file an issue.

## Phase 6: Polish

- [ ] T023 [P] Name the 503 answer in
  `specs/1823-upgrade-capture-portal/contracts/http-api.md` and
  `specs/1823-upgrade-capture-portal/contracts/README.md`. Name the status 503
  in the comment of `src/upgrade_portal/app/assets/templates/error.html`.
- [ ] T024 [P] Add `changelog.d/issue-3439-later-site-checks.md`.
- [ ] T025 Count the cloud reads of each step in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py` (SC-005).
  Run the count on both code versions.
- [ ] T026 Run the gates of `specs/3439-later-site-checks/plan.md` on each
  changed file.
- [ ] T027 Run the upgrade-portal unit, contract, integration, and browser
  suites.
- [ ] T028 Open the pull request, wait for each check, and merge it by hand.
- [ ] T029 Do the class B deploy to port 8056, and close #3439.

## Dependencies

- Phase 2 blocks Phases 3, 4, and 5.
- Phase 3 and Phase 5 need the error handler of T009.
- Phase 4 needs the constants of T007 only.
- Phase 6 needs each earlier phase.

## Parallel opportunities

- T010 and T011 do not depend on T004 through T009.
- T023 and T024 change documents only.
- The route tests of T012, T015, and T019 share one file, so they run in
  order.

## Implementation strategy

1. The first increment is Phase 2 and Phase 3. The single-site steps then name
   an incomplete site list.
2. Add Phase 4. The multi-site site choice then returns to the site picker
   with a Caution message.
3. Add Phase 5. Each plan step then names an incomplete site list.
4. Finish with Phase 6.