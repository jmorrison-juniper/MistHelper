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

- [x] T004 Write the red unit tests of the missing-site rule in
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
- [x] T005 Write the red unit tests of `selected_rows` in
  `tests/unit/upgrade_portal/test_issue_3439_site_checks.py`.
  - The function raises for a missing site of a partial list.
  - It returns the rows of the listed sites in the order of the request.
  - It returns an empty list for a missing site of a whole list.
  - The same file holds the unit tests of `site_set_refusal`. The function
    returns no answer when the list holds each chosen site. It returns a 503
    answer for a partial list and a 404 answer for a whole list.
- [x] T006 Run T004 and T005 on the old code. Record the red result in
  `specs/3439-later-site-checks/tasks.md`.
  - Result: 13 of 20 tests failed on the old code. Each failure was an
    `AttributeError` for a new name, such as `SiteListIncompleteError` or
    `SiteList.missing_sites`.
  - The other 7 tests passed on both code versions by design. They are the
    regression tests of a listed site, of a whole list, and of the read count.
  - Result on the new code: 20 of 20 passed. The unit suite of the upgrade
    portal passed with 3894 tests.
- [x] T007 Add the three constants, `SiteListIncompleteError`, and
  `SiteList.missing_sites` to `src/upgrade_portal/app/routes/select.py`.
- [x] T008 Change `find_site` in `src/upgrade_portal/app/routes/select.py`, so
  that it raises the error for a missing site of a partial list.
- [x] T009 Add the application error handler of `SiteListIncompleteError` to
  `src/upgrade_portal/app/routes/select.py`. A browser page receives the
  shared error page. A script receives the error envelope. A refused form post
  from a browser also receives the link back to the form.
- [x] T010 Add the later-check organization, its operator, its three sites,
  and the settled operation of the retry in
  `tests/e2e/upgrade_portal/later_check_seeds.py`.
- [x] T011 Add the later-check cloud session and the header rule of the
  stand-in reader in `tests/e2e/upgrade_portal/conftest.py`. Also add the
  device series of the three sites, the operator record, the retry seed, and
  the page fixture.

## Phase 3: User Story 1 (P1), the single-site steps

**Goal**: The inventory page, the inventory answer, and the capture start name
an incomplete site list.

**Independent test**: Open a site of page two in the single-site mode while
the site read loses page two. Then start a capture of that site.

- [x] T012 [US1] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  the inventory page, the inventory answer, and the capture start. Check that
  the capture start stores no capture and takes no lock. Also cover a site of
  a kept page and the 404 answers of a whole list.
- [x] T013 [US1] Run T012 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
  - Red result at `3d8cce8c`: the inventory page answered 404, and the
    inventory answer and the capture start answered 404 `site_not_found`. A
    failed first page also answered `site_not_found`. The reload test failed,
    because the first attempt answered 404 and not 503. The kept-page test and
    the whole-list test passed, as the plan expects.
- [x] T014 [US1] Add the single-site journeys to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot of
  each page, and read it.
  - Result: the three journeys pass. The inventory page shows the 503 page, and
    a reload with a whole read opens it. The inventory answer of West is 503,
    and the answer of North stays 200. The capture start names the cause.
  - The capture panel keeps the state "starting" after the refusal. The
    refusal sits below the visible part of the page. Issue #3445 tracks both.

## Phase 4: User Story 2 (P1), the multi-site site choice

**Goal**: The site choice post names an incomplete site list, and a browser
returns to the site picker with a Caution message.

**Independent test**: Select one site of page one and one site of page two.
Press the forward control while the site read loses page two.

- [x] T015 [US2] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  the browser post, the script post, a choice of kept sites only, and the
  stored choice after a refusal. Also cover the 404 answer of a whole list.
- [x] T016 [US2] Run T015 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
  - Red result at `3d8cce8c`: the script post answered 404 `site_not_found`.
    The picker showed the old Caution sentence, which states that the
    organization holds no such site. The kept-site test and the whole-list
    test passed, as the plan expects.
- [x] T017 [US2] Add `site_set_refusal` to
  `src/upgrade_portal/app/routes/select.py`. Change `site_choice_refusal` to
  return its answer.
- [x] T018 [US2] Add the site choice journey to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot, and
  read it.
  - Result: the picker opens again with the Caution message and the partial
    note of #3438. A reload with a whole read accepts the same choice.

## Phase 5: User Story 3 (P1), the multi-site plan steps

**Goal**: The options page, the options save, the confirm page, the pre-check
start, and the retry name an incomplete site list.

**Independent test**: Save a plan that holds a site of page two. Then open
each later step while the site read loses page two.

- [x] T019 [US3] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py`. Cover
  each of the five steps in a browser and in a script. Check that no plan, no
  saved options, no capture, no lock, and no retry reference change. Also
  cover the kept-site pass, the 404 answers of a whole list, and the save
  request with no `selected_types` field.
- [x] T020 [US3] Run T019 on the old code, and record the red result in
  `specs/3439-later-site-checks/tasks.md`.
  - Red result at `3d8cce8c`: the options page, the confirm page, and the
    retry answered 404 `sites_not_chosen`. The pre-check start answered 404
    `site_not_found`.
  - Warning: the old save answered 200 and opened the confirm page. It stored
    a plan that held no site. Issue #3441 names the same fault for a whole
    list. After this change, a lost page stops the save with 503 instead.
  - The kept-site test, the whole-list test, and the test of the older save
    request passed, as the plan expects.
  - Result: 20 of 36 contract tests failed at `3d8cce8c`. All 36 pass after
    the change.
- [x] T021 [US3] Change `selected_rows` in
  `src/upgrade_portal/app/routes/org_upgrade.py`, so that it raises the error
  for a missing site of a partial list.
- [x] T022 [US3] Add the plan step journeys and the retry journey to
  `tests/e2e/upgrade_portal/test_later_site_checks.py`. Save a screenshot of
  each page, and read it. If the state cell of the pre-check card keeps the
  text "starting" after a refusal, file an issue.
  - Result: the four journeys pass. The options page and the confirm page show
    the 503 page. The save and the retry are script forms, so the page names
    the cause with the prefix "Warning:", and the form keeps each typed value.
  - The pre-check card names the cause. The state cell keeps the text
    "starting". Issue #3446 tracks that defect.
  - The options page says "1 selected sites". Issue #3447 tracks that text.
  - Each refusal answered in less than 200 ms. The file
    `data/test-artifacts/upgrade-portal-journeys/later-site-checks/timings.json`
    holds the times.

## Phase 6: Polish

- [x] T023 [P] Name the 503 answer in
  `specs/1823-upgrade-capture-portal/contracts/http-api.md` and
  `specs/1823-upgrade-capture-portal/contracts/README.md`. Name the status 503
  in the comment of `src/upgrade_portal/app/assets/templates/error.html`.
- [x] T024 [P] Add `changelog.d/issue-3439-later-site-checks.md`.
- [x] T025 Count the cloud reads of each step in
  `tests/contract/upgrade_portal/test_issue_3439_later_site_checks.py` (SC-005).
  Run the count on both code versions.
  - Result: the nine count tests pass at `3d8cce8c` and after the change. Five
    steps read the site list and the site statistics one time each. These
    steps are the site choice, the options page, the options save, the confirm
    page, and the retry. The other four steps read the site list one time.
- [x] T026 Run the gates of `specs/3439-later-site-checks/plan.md` on each
  changed file.
  - Result: py_compile, ruff, Black, mypy, Bandit, Pylint, Radon, Vulture,
    pydocstyle, and interrogate pass. The first test-quality run found 7 new
    findings. The tests now compare whole values, and two new contract tests
    send an empty body and a malformed JSON body to the save. The second run
    found 0 new findings.
- [x] T027 Run the upgrade-portal unit, contract, integration, and browser
  suites.
  - Result: the unit and contract suites pass with 5136 tests in 449 seconds.
    The integration suite passes with 42 tests. Ten browser files pass with 93
    journeys. One journey skips at `test_capture.py:738`. That skip also occurs
    at `3d8cce8c`, and issue #3380 holds it.
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