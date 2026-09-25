# Tasks: The single-site upgrade journey measures every step

**Issue**: #3377 | **Plan**: [plan.md](plan.md)

## Phase 1: Tests first

- [x] T001 Add `test_options_page_offers_a_version_in_each_type_control` to
  `tests/e2e/upgrade_portal/test_upgrade.py`.
- [x] T002 Turn the save helper, the capture helper, the target table helper,
  and the three skips into failures that name the cause.
- [x] T003 Run `test_upgrade.py` on the old stand-in with `-rs`, and record the
  red result. The result was 1 failed, 6 passed, and 7 errors.

## Phase 2: The change

- [x] T004 Add `stand_in_view_of` to `tests/e2e/upgrade_portal/conftest.py`,
  and call it from `stand_in_options_view` and `stand_in_org_options_view`.
- [x] T005 Add `JOURNEY_SITE_ID` and `JOURNEY_SITE_NAME`, and list the site in
  `stand_in_cloud_read`.
- [x] T006 Point the `run_id` fixture and the capture helper of
  `test_upgrade.py` at the journey site.
- [x] T007 Add the release step to `confirm_page`, as research Decision 5
  records.
- [x] T008 Run `test_upgrade.py` green with 0 skips, and read the screenshots.
  The result was 14 passed in 23 seconds. The screenshots found issue #3381.

## Phase 3: Finish

- [x] T009 Run every gate: ruff, black, mypy, pydocstyle, interrogate, bandit,
  pylint, radon, vulture, the STE lint, and the test quality gate. CI runs
  mypy and pylint on `src/` only, and this change touches no file there. The
  test quality gate found 7 findings on the first run, as research Decision 7
  records. The second run found 0.
- [x] T010 Run the browser suite of the upgrade portal and the portal suites.
  The browser suite gave 261 passed and 1 skipped. The skip is issue #3380.
  The portal suites gave 5743 passed.
