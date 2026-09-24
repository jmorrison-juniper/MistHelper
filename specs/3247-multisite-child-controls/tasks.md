# Tasks: Retry, reschedule, and reconciliation for multi-site upgrades

**Issue**: #3247

## Phase 1: Red tests

- [x] T001 Write the unit tests of `OrgRetrySelection`, `OrgRetryPlan`, `OrgReconcileCheck`, `OrgScheduleView`, and `OrgControlsView` in `tests/unit/upgrade_portal/test_org_child_controls.py`.
- [x] T002 Write the unit tests of `reschedule` and `reconcile` in `tests/unit/firmware/test_aggregate_child_controls.py`.
- [x] T003 Write the contract tests of the four routes in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`.
- [x] T004 Run the tests, and save the red proof.

## Phase 2: US1, the retry

- [x] T005 Add `ORG_UPGRADE_RETRY_KEY` to `select.py`, and drop it in `clear_org_upgrade_options`.
- [x] T006 Add `OrgRetrySelection` and `OrgRetryPlan` to `org_retry.py`.
- [x] T007 Add the retry route and the clear route.
- [x] T008 Narrow the options page and the save. Store `plan_options` and `retry_of_operation_id`.
- [x] T009 Add the retry card and the options banner.

## Phase 3: US2, the reconciliation

- [x] T010 Add `OrgReconcileCheck` to `org_reconcile.py`, and make `OrgVersionRefresh.read_site` public.
- [x] T011 Add `AggregateUpgradeService.reconcile`.
- [x] T012 Add the reconciliation route and card.

## Phase 4: US3, the reschedule

- [x] T013 Add `OrgScheduleView` to `org_child_controls.py`, and add `AggregateUpgradeService.reschedule`.
- [x] T014 Add the reschedule route and the confirmation page form.

## Phase 5: The poll and the browser tests

- [x] T015 Add the signature reload to `paintOrgUpgradeStatus`.
- [x] T016 Add the browser journeys and the fixture operations.
- [x] T017 Run the green tests, the browser suite, and every gate.
- [x] T018 Add the release note fragment.
