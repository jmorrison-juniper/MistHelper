# Tasks: Site health dashboard

**Input**: [Plan](plan.md), [specification](spec.md), and the supporting files under `design/`.

**Tests**: Required. Keep live, protected-reuse, and deployment tasks unchecked until their gates close.

**Path rule**: Documentation paths below are relative to this feature directory.
Product and test paths are relative to the repository root.
Future portal paths are proposed destinations, not permission to create a sixth child.

## Phase 1: Setup

- [x] T001 Inspect pinned source workflows and record license, dependencies, layout, and deployment in `design/research.md`. (delivered: design/research.md)
- [x] T002 Define user stories and acceptance outcomes in `spec.md`. (delivered: spec.md)
- [x] T003 Define target architecture and safe delivery boundaries in `plan.md`. (delivered: plan.md)
- [x] T004 Define normalized values, entities, keys, and states in `design/data-model.md`. (delivered: design/data-model.md)
- [x] T005 Define API and portal contracts in `design/contracts/api.md` and `design/contracts/portal.md`. (delivered: design/contracts/api.md)
- [x] T006 Analyze consistency and record validation evidence in `analysis.md`. (delivered: analysis.md)

## Phase 2: Foundational gates

- [ ] T007 Obtain portal file ownership and a compliant package route in `plan.md`. B06 blocks portal code, not T010 through T012.
- [ ] T008 Record license compatibility and explicit protected-reuse approval in `design/research.md`. B01 blocks reuse only.
- [ ] T009 Record approved site access, data retention, and permission matrix in `design/contracts/portal.md`. B05 blocks live portal data.

## Phase 3: User Story 2 - Independent offline score model

**Goal**: Provide correct normalized score arithmetic without a transport or browser.
**Independent test**: Supply synthetic sample counts and verify exact results and explicit invalid-input errors.

- [x] T010 [US2] Add synthetic boundary, invalid-input, immutability, and serialization tests in `tests/unit/dataclasses/test_service_measurement.py`. (delivered: tests/unit/dataclasses/test_service_measurement.py)
- [x] T011 [US2] Implement immutable `ServiceMeasurement` in `src/foundation/models/data/service_measurement.py`. (delivered: src/foundation/models/data/service_measurement.py)
- [x] T012 [US2] Verify `src/foundation/models/data/service_measurement.py` and document results in `analysis.md`. (delivered: analysis.md)

T010 must also prove zero totals return `None`, not a healthy percentage.
T011 rejects boolean, fractional, infinite, string, and negative counts.
T011 enforces "Both absent counts mean unavailable data." "One absent count is invalid."
T012 verifies "Degraded counts must not exceed total counts."
T011 returns the exact percentage without display rounding.
T010 through T012 have no dependency on T007 through T009.
They implement FR-014 and the arithmetic portion of FR-005, not the full dashboard.

## Phase 4: User Story 1 - Organization and site health

**Goal**: Find affected sites and examine device health.
**Independent test**: Use scoped synthetic fixtures for organization ranking, search, selection, and all device states.

- [ ] T013 [US1] Add SDK pagination, scope, payload, HTTP failure, and redaction tests in `tests/contract/site_health/test_collection.py`. B04 and T007 block this phase.
- [ ] T014 [US1] Add site-search and device-state browser tests in `tests/e2e/web_portal/test_site_health_site.py`, including denied access and stale responses.
- [ ] T015 [US1] Prove organization ranking parity in `tests/contract/site_health/test_organization.py`. B02 blocks unsupported worst-sites transport.
- [ ] T016 [US1] Resolve period contracts in `design/contracts/api.md`. B03 blocks unverified periods.
- [ ] T017 [US1] Implement scoped site and device collection in `src/interfaces/portals/site_health/collection/` after T007, T009, T013, and T016.
- [ ] T018 [US1] Register the Site health tab in `web_portal/app.py` and `web_portal/templates/base.html` only after file handover.
- [ ] T019 [US1] Add organization category, metric-ordering, search, refresh, and worst-100 browser assertions in `tests/e2e/web_portal/test_site_health_organization.py`.

T017 must preserve unknown device state and absent running firmware.
T018 also needs T014, T015, T017, and T019 to pass.
No source template reuse is implied.

## Phase 5: User Story 2 - Service detail integration

**Goal**: Examine classifiers and affected items without losing scope or period.
**Independent test**: Select each category, open affected items, retry a failed section, and export authorized synthetic rows.

- [ ] T020 [US2] Add summary, classifier, impacted-item, units, and missing-sample contracts in `tests/contract/site_health/test_service_quality.py`.
- [ ] T021 [US2] Implement verified service collection in `src/interfaces/portals/site_health/collection/` after T007, T009, T016, and T020.
- [ ] T022 [US2] Add responsive SLE dialogs, safe columns, and formula-safe export tests in `tests/e2e/web_portal/test_site_health_sle.py`.
- [ ] T023 [US2] Implement service views under `src/interfaces/portals/site_health/presentation/` after T018, T021, and T022.

T020 requires B04 fixtures and verifies that unsupported units fail.
T022 covers text and color thresholds, unavailable data, keyboard closing, and 390-pixel and 1440-pixel viewports.
T023 retains category collapse, classifier bars, selected periods, and section retry.

## Phase 6: User Story 3 - Client and gateway investigation

**Goal**: Connect service failures to clients, interfaces, and peers.
**Independent test**: Follow synthetic device links and compare details with the original selected site.

- [ ] T024 [P] [US3] Add wireless and wired history tests in `tests/e2e/web_portal/test_site_health_clients.py` after T007 and T009.
- [ ] T025 [P] [US3] Add WAN, VPN, and BGP assertions in `tests/e2e/web_portal/test_site_health_gateway.py` after T007 and T009.
- [ ] T026 [US3] Implement client views under `src/interfaces/portals/site_health/presentation/` after T018, T024, and verified client SDK contracts.
- [ ] T027 [US3] Integrate gateway details with the existing WAN feature after owner approval, T025, and verified peer SDK contracts.

T027 must record its approved source paths in `plan.md` before changing WAN files.
Do not duplicate the other feature's collector or route registration.

## Phase 7: Cross-cutting delivery

- [x] T028 Add the unique release fragment `changelog.d/issue-4232-site-health-measurement.md` for the offline slice and its limits. (delivered: changelog.d/issue-4232-site-health-measurement.md)
- [x] T029 Run applicable local gates and the committed test-quality ratchet, then record exact commands and results in `analysis.md`. (delivered: analysis.md)
- [x] T030 Publish a dedicated pull request with `.github/PULL_REQUEST_TEMPLATE.md`. Keep cloud access, merging, auto-merge, and deployment blocked. (delivered: analysis.md)
- [ ] T031 Verify future persistence through `DataExporter.write_with_format_selection()` and declared natural keys before live release. B04 and B07 remain open.

## Dependencies and execution order

T001 through T005 precede T006.
T006 precedes T010. T010 precedes T011. T011 precedes T012.
T028 and T029 precede T030. T012 precedes final offline validation.
The gated tasks T007 through T009 are independent decisions, not implicit approvals.
US1 requires verified collection and approved portal access.
The remaining US2 and US3 work depends on that portal foundation, not on each other's views.
T031 requires all collection contracts, scope approval, and persistence failure tests.

## Parallel examples

During offline work, documentation checks and model lint can run independently.
After T007 and T009, T024 and T025 can run independently on separate test files.
For US1, site and organization browser scenarios can run independently after shared fixture contracts pass.
For US2, classifier unit fixtures and dialog browser assertions can run independently after their response contract is fixed.
Do not parallelize edits to the portal entry points.

## Implementation strategy

Deliver the offline score model first because its normalized contract needs no protected code or live connection.
This is a useful domain increment, not a complete user-facing dashboard.
Keep all blocked tasks visible and unchecked.
After approval, deliver US1, service details, and client investigation in separate verified increments.
Do not call a blocked live task complete merely because its planning artifact exists.
