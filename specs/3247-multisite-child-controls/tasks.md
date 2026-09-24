# Tasks: Retry, reschedule, and reconciliation for multi-site upgrades

**Issue**: #3247

## Phase 1: Red tests

- [ ] T001 Write the unit tests of `OrgRetrySelection`, `OrgRetryPlan`, `OrgReconcileCheck`, `OrgScheduleView`, and `OrgControlsView` in `tests/unit/upgrade_portal/test_org_child_controls.py`.
- [ ] T002 Write the unit tests of `reschedule` and `reconcile` in `tests/unit/firmware/test_aggregate_child_controls.py`.
- [ ] T003 Write the contract tests of the four routes in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`.
- [ ] T004 Run the tests, and save the red proof.

## Phase 2: US1, the retry

- [ ] T005 Add `ORG_UPGRADE_RETRY_KEY` to `select.py`, and drop it in `clear_org_upgrade_options`.
- [ ] T006 Add `OrgRetrySelection` and `OrgRetryPlan` to `org_retry.py`.
- [ ] T007 Add the retry route and the clear route.
- [ ] T008 Narrow the options page and the save. Store `plan_options` and `retry_of_operation_id`.
- [ ] T009 Add the retry card and the options banner.

## Phase 3: US2, the reconciliation

- [ ] T010 Add `OrgReconcileCheck` to `org_reconcile.py`, and make `OrgVersionRefresh.read_site` public.
- [ ] T011 Add `AggregateUpgradeService.reconcile`.
- [ ] T012 Add the reconciliation route and card.

## Phase 4: US3, the reschedule

- [ ] T013 Add `OrgScheduleView` to `org_child_controls.py`, and add `AggregateUpgradeService.reschedule`.
- [ ] T014 Add the reschedule route and the confirmation page form.

## Phase 5: The poll and the browser tests

- [ ] T015 Add the signature reload to `paintOrgUpgradeStatus`.
- [ ] T016 Add the browser journeys and the fixture operations.
- [ ] T017 Run the green tests, the browser suite, and every gate.
- [ ] T018 Add the release note fragment.
