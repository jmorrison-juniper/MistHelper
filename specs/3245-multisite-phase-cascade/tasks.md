# Tasks: The cascade phases of a multi-site upgrade

**Issue**: #3245
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Phase 1: Tests first

- [x] T001 Write the red unit tests for the record module in `tests/unit/upgrade_portal/test_org_cascade_record.py`.
- [x] T002 Write the red unit tests for the reader module in `tests/unit/upgrade_portal/test_org_cascade_readers.py`.
- [x] T003 Write the red rehearsal tests for the walk in `tests/unit/upgrade_portal/test_org_cascade_walk.py`.
- [x] T004 Write the red unit tests for the view in `tests/unit/upgrade_portal/test_org_cascade_view.py`.
- [x] T005 Write the red contract tests in `tests/contract/upgrade_portal/test_org_phase_watch_contract.py`.

## Phase 2: The core modules

- [x] T006 Add the `device_type` keyword to `read_fleet_statistics` in `src/upgrade_portal/upgrade/gate.py`.
- [x] T007 Create `src/upgrade_portal/upgrade/org_cascade/record.py`.
- [x] T008 Create `src/upgrade_portal/upgrade/org_cascade/readers.py`.
- [x] T009 Create `src/upgrade_portal/upgrade/org_cascade/walk.py`.
- [x] T010 Create `src/upgrade_portal/upgrade/org_cascade/view.py` and `__init__.py`.

## Phase 3: The route and the page

- [x] T011 Store the anchors and start the watch in `_submit_aggregate`.
- [x] T012 Resume the watch in `_refresh_aggregate`.
- [x] T013 Add the phase fields to `_aggregate_record_view` and the current phase to `aggregate_summary`.
- [x] T014 Add the partial `partials/org_phase_list.html` and the parity test `test_org_phase_list_parity.py`. `progress.html` does not change.
- [x] T015 Add the "Cascade phases" card to `org_progress.html`.
- [x] T016 Paint the phases and keep the poll alive in `portal.js`.

## Phase 4: Proof

- [x] T017 Write the browser journey `tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py`, and read each screenshot.
- [x] T018 Run the single-site phase tests, and confirm that they pass with no change.
- [x] T019 Run every quality gate.
- [x] T020 Add the release note `changelog.d/issue-3245-multisite-phase-cascade.md`.
