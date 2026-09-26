# Tasks: The site picker and the reconciliation read name a lost page

**Issue**: #3438 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Tests**: SC-001 asks for each new test to fail on the old code. Each test
task therefore comes before its code task.

## Phase 1: Setup

- [x] T001 Create the worktree `MistHelper-i3438` from `main` at `d2f2b64d`,
  and run `scripts/bootstrap_worktree.py`.
- [x] T002 Write `spec.md`, `research.md`, `plan.md`, `data-model.md`,
  `quickstart.md`, and `checklists/requirements.md` in
  `specs/3438-picker-reconcile-pages/`.
- [x] T003 File issue #3439 for the later site checks. Name the issue in
  `specs/3438-picker-reconcile-pages/spec.md`.

## Phase 2: Foundational (the picker read)

These tasks block User Stories 1, 2, and 3.

- [ ] T004 Write the red tests of the page walk in
  `tests/unit/upgrade_portal/test_issue_3438_picker_pages.py`. Cover a whole
  read of two pages, a lost second page in HTML and in JSON, and a second page
  with no status. Also cover a failed first page and the log record.
- [ ] T005 Write the red tests of the cache rule in
  `tests/unit/upgrade_portal/test_issue_3438_picker_pages.py`. The cache never
  keeps a read that lost a page. The cache keeps a whole read, so a second view
  makes no cloud call. A read that cannot run gives the reason `read_not_run`.
- [ ] T006 [P] Change the `collect_pages` stand-in in
  `tests/unit/upgrade_portal/test_cloud_cache.py`, so that it returns a
  `DeviceRead`. Compare the `records` field in each assert.
- [ ] T007 [P] Remove the two floor tests and the `_page` helper from
  `tests/unit/upgrade_portal/test_org_picker.py`.
- [ ] T008 Run T004 through T007 on the old code. Record the red result in
  `specs/3438-picker-reconcile-pages/tasks.md`.
- [ ] T009 Change `collect_pages` and `default_cloud_read` in
  `src/upgrade_portal/app/routes/select.py`. Walk each page, and name a fault
  of the first page. Return a `DeviceRead`, and keep a whole read only.
- [ ] T010 Add `SiteList` to `src/upgrade_portal/app/routes/select.py`. Change
  `build_site_rows` to return it. Move `site_choice_refusal` to
  `SiteList.rows`.
- [ ] T011 Move `selected_rows` and `_site_labels` to `SiteList.rows` in
  `src/upgrade_portal/app/routes/org_upgrade.py`.
- [ ] T012 Add the lost-page organization and its operator in
  `tests/e2e/upgrade_portal/lost_page_seeds.py`.
- [ ] T013 Add the lost-page cloud session and the real read for that
  organization in `tests/e2e/upgrade_portal/conftest.py`. Also add the operator
  record and the `lost_page_operator_page` fixture.

## Phase 3: User Story 1 (P1), the single-site note

**Goal**: The single-site picker shows a Caution note for each read that lost
a page.

**Independent test**: Open the picker as the lost-page operator in the
single-site mode. Read the two notes above the table.

- [ ] T014 [US1] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3438_site_list_notes.py`. Cover
  each note, and no note after two whole reads. Also cover the site list note
  above an empty table after a failed first page.
- [ ] T015 [US1] Pass `site_list_partial` and `site_count_partial` from
  `sites_page` in `src/upgrade_portal/app/routes/select.py`.
- [ ] T016 [US1] Add the two Caution notes to
  `src/upgrade_portal/app/assets/templates/select/sites.html`.
- [ ] T017 [US1] Add the single-site journey to
  `tests/e2e/upgrade_portal/test_lost_site_page.py`. Save a screenshot, and
  read it.

## Phase 4: User Story 2 (P1), the multi-site note

**Goal**: The multi-site picker shows the same notes, and the forward post
still works.

**Independent test**: Open the picker as the lost-page operator in the
multi-site mode. Read the notes above the check boxes. Select a site of the
first page, and push the forward control.

- [ ] T018 [US2] Write the multi-site route tests in
  `tests/contract/upgrade_portal/test_issue_3438_site_list_notes.py`. Cover
  both notes above the form, and a forward post of a site of the first page.
- [ ] T019 [US2] Add the multi-site journey to
  `tests/e2e/upgrade_portal/test_lost_site_page.py`. Save a screenshot, and
  read it.

## Phase 5: User Story 3 (P1), the fields of the site list answer

**Goal**: A script reads the completeness of each read.

**Independent test**: Read `GET /api/sites` as the lost-page operator.

- [ ] T020 [US3] Write the red route tests in
  `tests/contract/upgrade_portal/test_issue_3438_site_list_notes.py`. Cover
  `site_list_complete` and `device_counts_complete` on both paths. Also cover
  the rows, which must not change.
- [ ] T021 [US3] Add the two fields in `list_sites` in
  `src/upgrade_portal/app/routes/select.py`.
- [ ] T022 [P] [US3] Name the two fields in
  `specs/1823-upgrade-capture-portal/contracts/http-api.md`.
- [ ] T023 [US3] Read the site list answer in the browser in
  `tests/e2e/upgrade_portal/test_lost_site_page.py`.

## Phase 6: User Story 4 (P1), the reconciliation read

**Goal**: Each target of a lost page holds unavailable evidence.

**Independent test**: Reconcile a stale stopping run with two targets. The
statistics read loses its second page.

- [ ] T024 [US4] Write the red tests in
  `tests/unit/upgrade_portal/test_issue_3438_reconcile_pages.py`. Cover a whole
  walk, a lost second page, and a fresh target that keeps its evidence. Also
  cover a failed first page and one full-path service test.
- [ ] T025 [P] [US4] Replace the `get_all` stand-in with a real SDK answer in
  `tests/unit/upgrade_portal/test_site_stats_evidence_reader.py`.
- [ ] T026 [US4] Run T024 and T025 on the old code. Record the red result in
  `specs/3438-picker-reconcile-pages/tasks.md`.
- [ ] T027 [US4] Change `SiteStatsFirmwareEvidenceReader.read` in
  `src/upgrade_portal/api/run_controls/routes.py`. Add `_read_pages`,
  `_unread_evidence`, and `_target_id`.

## Phase 7: Polish

- [ ] T028 Add `changelog.d/issue-3438-picker-reconcile-pages.md`.
- [ ] T029 Run the gates of `specs/3438-picker-reconcile-pages/plan.md` on each
  changed file.
- [ ] T030 Run the upgrade-portal unit, contract, integration, and browser
  suites.
- [ ] T031 Open the pull request, wait for each check, and merge it by hand.
- [ ] T032 Do the class B deploy to port 8056, and close #3438.

## Dependencies

- Phase 2 blocks Phases 3, 4, and 5.
- Phase 6 does not depend on Phases 2 through 5.
- Phase 4 uses the template change of T016.
- Phase 7 needs each earlier phase.

## Parallel opportunities

- T006 and T007 change different files.
- T022 changes a document only.
- T025 changes one test file only.
- Phase 6 can run beside Phases 3 through 5.

## Implementation strategy

1. The first increment is Phase 2 and Phase 3. The single-site picker then
   names a lost page.
2. Add Phase 4 and Phase 5. The multi-site mode and each script then read the
   same facts.
3. Add Phase 6. Reconciliation then never shows a stored version as a running
   version.
4. Finish with Phase 7.
