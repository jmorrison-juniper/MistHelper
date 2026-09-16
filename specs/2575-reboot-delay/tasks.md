# Tasks: Multi-Site Reboot Delay

**Issue**: #2575
**Source**: `spec.md` and `plan.md` in this directory

## Phase 1: Verify the Existing Contract

- [x] T001 Read issue #2575 and issue #2644.
- [x] T002 Read the repository constitution and workflow rules.
- [x] T003 Inspect the single-site reboot delay control and option mapper.
- [x] T004 Inspect the multi-site route, aggregate service, and templates.

## Phase 2: Route and Template Implementation

- [x] T005 Add the multi-site `reboot_at` control to `src/upgrade_portal/app/assets/templates/upgrade/org_options.html`.
- [x] T006 Add the confirmation display to `src/upgrade_portal/app/assets/templates/upgrade/org_confirm.html`.
- [x] T007 Add `OrgUpgradeScheduleReader` to `src/upgrade_portal/app/routes/org_upgrade.py`.
- [x] T008 Read, validate, and store `reboot_at` in `src/upgrade_portal/app/routes/org_upgrade.py`.
- [x] T009 Pass `reboot_at` into the existing single-site option mapper from `src/upgrade_portal/app/routes/org_upgrade.py`.

## Phase 3: Service Implementation

- [x] T010 Store converted `reboot_at` epoch seconds on each aggregate site child in `src/firmware/aggregate_upgrade_service.py`.
- [x] T011 Keep the AP organization child free of `reboot_at`.

## Phase 4: Safety Tests

- [x] T012 Add a contract test that the options page shows the new control and `data-testid`.
- [x] T013 Add a contract test that a valid delay reaches confirmed options and the confirmation page.
- [x] T014 Add a contract test that an empty delay keeps `reboot_at` unset.
- [x] T015 Add a contract test that a past delay returns 400 and names the control.
- [x] T016 Add a unit-level aggregate planner test that two selected sites receive the same delay.

## Phase 5: Release and Validation

- [x] T017 Add `changelog.d/issue-2575-reboot-delay.md`.
- [ ] T018 Run the local gates listed in `plan.md`.
- [ ] T019 Commit the change.
- [ ] T020 Open the pull request.
- [ ] T021 Watch required checks.
- [ ] T022 Report whether the pull request merged and whether issue #2575 closed.

## Dependency Order

Complete T001 through T004 before implementation.

Complete T005 through T009 before service tests.

Complete T010 and T011 before final validation.

Complete T012 through T017 before T018.
