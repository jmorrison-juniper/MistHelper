# Tasks: The cancellation result of a multi-site upgrade

**Issue**: #3246
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Phase 1. The red tests

- [x] T001 Write `tests/unit/firmware/test_org_cancel_sort.py`. Cover the nested `upgrades` entry, the `site_upgrades` entry, a reference entry, a damaged list, the root cover, a refused cancel, and the MAC spelling.
- [x] T002 Write `tests/unit/upgrade_portal/test_upgrade_service_cancel_sort.py`. Cover a refused cancel, an unknown state, and a split.
- [x] T003 Write `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`. Cover the stored rule, the rule for a child job that never started, the rule for an unsorted result, the order, and the signature.
- [x] T004 Write `tests/contract/upgrade_portal/test_org_cancel_outcomes_routes.py`. Cover the page, the poll, and the HTML post.
- [x] T005 Run the new tests. Record the red result in the session folder.

## Phase 2. The firmware layer

- [x] T006 Rename `_reboot_macs` to `reboot_macs` in `src/firmware/upgrade_service.py`.
- [x] T007 Replace `_sort_cancel` with `sort_cancel(macs, writing, status)`. Update `cancel_upgrade`.
- [x] T008 Update the comments that name `_sort_cancel` in `tests/support/rehearsal/cloud.py`.
- [x] T009 Add `src/firmware/org_cancel_sort.py` with the classes `OrgRebootLists` and `OrgCancelSort`.
- [x] T010 Change `AggregateUpgradeService._cancel_org_child` to return `OrgCancelSort.result`.
- [x] T011 Add the AP list assertion to `tests/unit/firmware/test_aggregate_upgrade_service.py`.
- [x] T011a Add the sections for `reboot_macs` and `sort_cancel` to `specs/1823-upgrade-capture-portal/contracts/upgrade-service.md`.

## Phase 3. The view layer

- [x] T012 Add `src/upgrade_portal/upgrade/org_cancel_outcomes.py` with the classes `OrgCancelLists` and `OrgCancelOutcomes`. Apply the rule of issue #3327 to a planned child job and to a rejected child job.
- [x] T013 Add `cancel_outcomes` to `_aggregate_record_view` in `org_upgrade.py`.
- [x] T014 Add the `cancel=` part to `OrgControlsView.build`. Update the three signature assertions in `test_org_child_controls_routes.py`.
- [x] T015 Replace the note with the Caution text in `org_progress.html`. Add the panel.
- [x] T016 Update the comment of `orgControlsChanged` in `portal.js`.

## Phase 4. The browser journey

- [x] T017 Add `tests/e2e/upgrade_portal/org_cancel_seeds.py`. Seed one operation with an AP child job, a switch child job, and a rejected child job.
- [x] T018 Extend `E2EOrgUpgradeService.status` so that the seeded AP job names one AP in `reboot_in_progress`.
- [x] T019 Write `tests/e2e/upgrade_portal/test_org_cancel_outcomes_journey.py`. Type CANCEL, press the button, read the lists, and load the page again.
- [x] T020 Take a screenshot after the cancel and after the reload. Read each screenshot.

## Phase 5. The gates and the merge

- [x] T021 Run Ruff, Black, mypy, Radon, Vulture, pydocstyle, interrogate, Pylint, the test ratchet, and the STE linter.
- [x] T022 Run the unit tests, the contract tests, and the E2E tests of the upgrade portal.
- [x] T023 Add `changelog.d/issue-3246-multisite-cancel-outcomes.md`.
- [x] T024 Open the pull request with `Closes #3246`. Wait for CodeQL, then merge.
