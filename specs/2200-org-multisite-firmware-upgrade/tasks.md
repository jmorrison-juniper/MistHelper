# Tasks: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Source**: The specification files in this directory

## Phase 1: Verify the Contracts

- [ ] T001 Record the OpenAPI AP-only description for
  `POST /api/v1/orgs/{org_id}/devices/upgrade`.
- [ ] T002 Add a contract test for the conflicting `device_type` values.
- [ ] T003 Add a contract test for the conflicting `firmware_type` values.
- [ ] T004 Record the conflicting saved organization guide example.
- [ ] T005 Verify the existing site and SSR routes in
  `src/firmware/upgrade_service.py`.

## Phase 2: Model the Aggregate

- [ ] T006 Add a durable aggregate operation record.
- [ ] T007 Add durable child operation records.
- [ ] T008 Store child identity, route, scope, organization, site, and family.
- [ ] T009 Store target identifiers, request body, status, and errors.
- [ ] T010 Store submit claims and cancel claims.
- [ ] T011 Add atomic conditional updates for every claim.
- [ ] T012 Recover an incomplete claimed child as `unknown`.

## Phase 3: Build the Mixed Plan

- [ ] T013 Build an immutable target snapshot.
- [ ] T014 Verify organization ownership for every selected site.
- [ ] T015 Verify site ownership for every selected target.
- [ ] T016 Create at most one organization AP child.
- [ ] T017 Set `all_sites` to false for the AP child.
- [ ] T018 Set `device_type` and `firmware_type` to `ap`.
- [ ] T019 Route switch groups by site through `upgrade_service.py`.
- [ ] T020 Route Junos gateway groups by site through `upgrade_service.py`.
- [ ] T021 Keep the organization SSR route for classified SSR targets.
- [ ] T022 Reject every Mist Edge target.
- [ ] T023 Store stable child identifiers before confirmation.

## Phase 4: Build the Seamless UI

- [ ] T024 Keep the sequence organization, mode, sites, options, confirmation,
  and progress.
- [ ] T025 Use AP, switch, and gateway terms in all operator text.
- [ ] T026 Add family and target controls to the options page.
- [ ] T027 Show each child route and target count on the confirmation page.
- [ ] T028 Show family-specific warnings on the confirmation page.
- [ ] T029 Show one progress row for every child.
- [ ] T030 Show partial, failed, unknown, and unsubmitted states.
- [ ] T031 Show cancel status and cancel errors for every child.
- [ ] T032 Keep every driven control under a stable `data-testid`.

## Phase 5: Protect Submission

- [ ] T033 Verify the authenticated owner before each action.
- [ ] T034 Verify the active organization before each action.
- [ ] T035 Verify every site and target before submission.
- [ ] T036 Verify every required site lock before each child claim.
- [ ] T037 Store and verify the canonical confirmation plan hash.
- [ ] T038 Require the exact confirmation text.
- [ ] T039 Require a valid CSRF token for every browser write.
- [ ] T040 Reject a stale confirmation after any plan change.
- [ ] T041 Reject a repeated submit after a child claim.

## Phase 6: Enforce One Write Attempt

- [ ] T042 Use a session with zero SDK retries.
- [ ] T043 Use transport adapters with zero retries.
- [ ] T044 Refuse a write session that permits retries.
- [ ] T045 Claim each child before its cloud request.
- [ ] T046 Increment `write_attempts` only during the first claim.
- [ ] T047 Send one cloud request for each claimed child.
- [ ] T048 Store `unknown` after an uncertain write result.
- [ ] T049 Never replay an `unknown` or claimed child.
- [ ] T050 Reconcile unknown children with read operations only.

## Phase 7: Aggregate Status and Cancellation

- [ ] T051 Derive the aggregate display state from child states.
- [ ] T052 Preserve child detail when the aggregate is partial.
- [ ] T053 Preserve every accepted child after a later failure.
- [ ] T054 Mark untouched children as `not_submitted`.
- [ ] T055 Require owner, organization, confirmation, and CSRF checks for cancel.
- [ ] T056 Select each cancel route from the stored child route.
- [ ] T057 Claim each child cancel before the cloud request.
- [ ] T058 Send no automatic cancel retry.
- [ ] T059 Store `cancel_unknown` after an uncertain cancel result.
- [ ] T060 State that cancellation does not restore firmware.

## Phase 8: Unit Tests

- [ ] T061 Test AP aggregation across many sites.
- [ ] T062 Test switch grouping by site and version.
- [ ] T063 Test Junos gateway grouping by site and version.
- [ ] T064 Test SSR classification and organization routing.
- [ ] T065 Test Mist Edge rejection.
- [ ] T066 Test aggregate state calculation.
- [ ] T067 Test submit and cancel claim transitions.
- [ ] T068 Test stale plan hash rejection.

## Phase 9: Contract Tests

- [ ] T069 Test the AP-only organization request body.
- [ ] T070 Test each site request body from `upgrade_service.py`.
- [ ] T071 Test the organization SSR request body.
- [ ] T072 Test cloud identifier storage for each route.
- [ ] T073 Test malformed and empty cloud answers.
- [ ] T074 Test status and cancel answer normalization.
- [ ] T075 Keep every contract test offline.

## Phase 10: Integration Tests

- [ ] T076 Test one aggregate with AP, switch, Junos, and SSR children.
- [ ] T077 Test partial submission after a child failure.
- [ ] T078 Test process loss after a durable claim.
- [ ] T079 Test an uncertain cloud answer.
- [ ] T080 Test duplicate form posts and replay prevention.
- [ ] T081 Test cross-user operation access.
- [ ] T082 Test a site from another organization.
- [ ] T083 Test lock loss before a later child claim.
- [ ] T084 Test mixed cancellation results.

## Phase 11: Playwright Tests

- [ ] T085 Test the complete six-page sequence.
- [ ] T086 Test an AP-only selection.
- [ ] T087 Test a switch-only selection.
- [ ] T088 Test a gateway-only selection.
- [ ] T089 Test a mixed selection.
- [ ] T090 Test the confirmation gate and stale confirmation refusal.
- [ ] T091 Test progress after a browser reload.
- [ ] T092 Test cancellation with partial and unknown results.

## Phase 12: Validation

- [ ] T093 Run the focused unit, contract, and integration tests.
- [ ] T094 Run the Playwright suite with network stand-ins.
- [ ] T095 Run the full offline portal suite.
- [ ] T096 Verify that the socket guard blocks outbound traffic.
- [ ] T097 Grade every changed Markdown file with the STE linter.
- [ ] T098 Confirm that no live Mist write ran.

## Dependency Order

Complete T001 through T005 before route implementation.

Complete T006 through T012 before submission work.

Complete T013 through T023 before the confirmation UI.

Complete T033 through T050 before cancellation work.

Complete all implementation tasks before T093 through T098.
