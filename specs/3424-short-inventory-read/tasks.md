# Tasks: A short inventory read never looks complete

**Issue**: #3424 | **Plan**: [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3424` from `main`, and run the
  bootstrap.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, this file, and the
  quality checklist.

## Phase 2: Tests first (User Stories 1, 2, and 3)

- [x] T003 [US1] [US2] Add the unit tests in
  `tests/unit/upgrade_portal/test_upgrade_options.py`: `is_short`, the view
  reasons, the record refusal, no version read after a short read, and the
  empty-read rule.
- [x] T004 [US3] Add the unit tests in
  `tests/unit/upgrade_portal/test_org_site_records.py`: a short site, the
  refusal order, and a retry.
- [x] T005 [US1] [US2] Add the contract tests in
  `tests/contract/upgrade_portal/test_upgrade_options.py`: the banner, no
  banner, and the refusal that keeps the run record.
- [x] T006 [US3] Add the contract tests in
  `tests/contract/upgrade_portal/test_org_site_records_routes.py`: the banner,
  a short view, a short save read, a retry, and the refusal order.
- [x] T007 Run T003 through T006 on the old code, and record the red result.

## Phase 3: Implementation

- [x] T008 [US1] [US2] Change `src/upgrade_portal/upgrade/options.py`.
- [x] T009 [US3] Change `src/upgrade_portal/upgrade/org_site_records.py`.
- [x] T010 [US1] Change `src/upgrade_portal/app/routes/upgrade.py`.
- [x] T011 [US3] Change `src/upgrade_portal/app/routes/org_upgrade.py`.
- [x] T012 [US1] [US3] Add the banners to `upgrade/options.html` and
  `upgrade/org_options.html`.
- [x] T013 Run T003 through T006 green.

## Phase 4: Browser journeys (User Story 4)

- [x] T014 [US4] Add `tests/e2e/upgrade_portal/short_read_seeds.py`, and add
  the short site to `tests/e2e/upgrade_portal/conftest.py`.
- [x] T015 [US4] Add `tests/e2e/upgrade_portal/test_short_inventory_read.py`
  with one single-site journey and one multi-site journey. Save a screenshot
  of each page, and read each screenshot.

## Phase 5: Polish

- [x] T016 Add `changelog.d/issue-3424-short-inventory-read.md`.
- [x] T017 Run the gates of `plan.md` and the upgrade-portal suites.

## Phase 6: Code review finding (FR-013 and FR-014)

- [x] T018 Add `tests/support/sdk_pages.py`. It builds a real SDK answer with
  the page headers.
- [x] T019 Write the red tests `TestLostLaterPage` and `TestReadEveryPage`.
  Record the red run: 14 failed and 1 passed.
- [x] T020 Add `read_every_page` to `capture/devices.py`. Use it in
  `_read_paged`, and copy the rows inside the guarded block. Run T019 green.
- [x] T021 File #3436 for the capture reads and the gate read.
- [ ] T022 Run the gates of `plan.md`, the upgrade-portal suites, and the new
  browser file again.

## Phase 7: Delivery

- [ ] T023 Open the pull request, wait for each check, and merge it by hand.
- [ ] T024 Do the class B deploy to port 8056, and close #3424.
