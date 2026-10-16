# Tasks: MistCircuitStats WAN Dashboard

**Input**: Design documents in `specs/live/20261013-122636-mistcircuitstats-wan/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/wan-dashboard.md`, and `quickstart.md`

**Tests**: Required by the feature specification and repository rules. Write tests first and verify that they fail before implementation.

**Organization**: Tasks are grouped by user story. Mark each task complete only after its acceptance test or validation passes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it has no dependency on an incomplete task and uses different files.
- **[Story]**: The user story served by the task.
- Record delivery evidence only after implementation and verification.

## Phase 1: Setup

**Purpose**: Prepare the feature package and local test locations without adding another application or service.

- [X] T001 Create the feature package skeleton in `src/interfaces/portals/wan_dashboard/__init__.py`, `src/interfaces/portals/wan_dashboard/routes.py`, `src/interfaces/portals/wan_dashboard/services.py`, `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html`, and `src/interfaces/portals/wan_dashboard/static/dashboard.css` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.
- [X] T002 Create feature test modules in `tests/integration/web_portal/wan_dashboard/test_services.py`, `tests/integration/web_portal/wan_dashboard/test_routes.py`, `tests/integration/web_portal/wan_dashboard/test_exports.py`, and `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`.
- [X] T003 Add one dashboard end-to-end test method to the existing `TestDashboardPage` class in `tests/e2e/web_portal/test_portal_smoke.py`.

## Phase 2: Foundational

**Purpose**: Establish the shared portal, access, Mist SDK, error, and cache contracts that block all user stories.

- [X] T004 Add the Mist SDK signature and authentication contract tests in `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` for each method listed in `spec.md`.
- [X] T005 Add failure, pagination, secret-redaction, authorization, one-pass token rotation, 60-second cooldown, and all-token cooldown contract tests in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [X] T006 Add blueprint registration and existing portal security assertions to the T003 test method for `web_portal/app.py` and `web_portal/templates/base.html`.
- [X] T007 Implement the read-only feature blueprint and route validation in `src/interfaces/portals/wan_dashboard/routes.py`.
- [X] T008 Implement the shared Mist data collector, result validation, and explicit error states in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T009 Implement namespaced cache access with the 300-second site TTL and 600-second profile and gateway-template TTL in `src/interfaces/portals/wan_dashboard/services.py`. Reuse the existing Redis service and do not add a new service or database.
- [X] T010 Register the feature blueprint in `web_portal/app.py` and add the navigation link in `web_portal/templates/base.html`.
- [X] T011 Add the licensed source credit and modification notice to `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html`.

**Checkpoint**: Run the contract and portal security tests before starting user-story work.

## Phase 3: User Story 1 - Review organization WAN health (Priority: P1)

**Goal**: Show a searchable, filterable organization gateway overview in the MistHelper portal.

**Independent Test**: Use synthetic records that exceed one API page. Verify complete pagination, readable site names, gateway status, port totals, and site and gateway filters.

### Tests for User Story 1

- [X] T012 [P] [US1] Add collector tests for site and gateway pagination, access scope, and 300-second site cache behavior in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [X] T013 [P] [US1] Add route tests for organization overview, search, filters, empty results, and failure responses in `tests/integration/web_portal/wan_dashboard/test_routes.py`.
- [X] T014 [P] [US1] Extend the T003 end-to-end test method to verify navigation, filtering, search, empty states, and rate-limit notices in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 1

- [X] T015 [US1] Collect authorized organization, site, gateway inventory, and current gateway statistics through the documented `mistapi` methods in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T016 [US1] Resolve gateway profile and gateway-template data with the 600-second cache TTL in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T017 [US1] Render the overview table, site filter, gateway search, status, and port totals in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html`.
- [X] T018 [US1] Add stable overview test identifiers and status handling in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.
- [X] T019 [US1] Verify the overview filters use the full paginated record set in the T003 test method.

**Checkpoint**: The operator can review the complete authorized gateway list without opening the source application.

## Phase 4: User Story 2 - Inspect a gateway port (Priority: P2)

**Goal**: Show port configuration, traffic history, and VPN peer paths while preserving the source dashboard interaction.

**Independent Test**: Load synthetic gateway and port records. Expand a row, inspect details, select each traffic range, and inspect peer paths.

### Tests for User Story 2

- [X] T020 [P] [US2] Add tests for optional port fields, device-profile and gateway-template records, and URL-encoded port identifiers in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [X] T021 [P] [US2] Add tests for VPN peer paths, missing statistics, and all four traffic ranges in `tests/integration/web_portal/wan_dashboard/test_routes.py`.
- [X] T022 [P] [US2] Extend the T003 end-to-end test method to verify port details, peer paths, chart controls, and 10-minute buckets in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 2

- [X] T023 [US2] Collect port configuration and statistics with explicit `mistapi` arguments in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T024 [US2] Collect and validate VPN peer-path responses in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T025 [US2] Validate traffic ranges and group chart samples in UTC in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T026 [US2] Render expandable port details, traffic charts, and peer-path details in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.
- [X] T027 [US2] Verify missing optional values remain visible as unavailable, not as zero, in the T003 test method.

**Checkpoint**: The operator can inspect a gateway's ports, traffic, and VPN paths in the shared portal.

## Phase 5: User Story 3 - Review WAN Insights and export data (Priority: P3)

**Goal**: Show WAN Insights and export gateway and hourly port data safely.

**Independent Test**: Load synthetic bandwidth, WAN link health, and SLE responses. Verify all five insight ranges and both CSV exports.

### Tests for User Story 3

- [X] T028 [P] [US3] Add tests for five insight ranges, bandwidth peaks, link health, and SLE values in `tests/integration/web_portal/wan_dashboard/test_services.py`.
- [X] T029 [P] [US3] Add tests for CSV headers, selected rows, UTC timestamps, and formula neutralization in `tests/integration/web_portal/wan_dashboard/test_exports.py`.
- [X] T030 [P] [US3] Extend the T003 end-to-end test method to verify WAN Insights, failure notices, and both CSV downloads in `tests/e2e/web_portal/test_portal_smoke.py`.

### Implementation for User Story 3

- [X] T031 [US3] Collect bandwidth, WAN link health, Application Health SLE, impacted interfaces, and thresholds through the documented SDK methods in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T032 [US3] Validate insight ranges and preserve UTC timestamps in `src/interfaces/portals/wan_dashboard/services.py`.
- [X] T033 [US3] Implement gateway and 12-column hourly port CSV exports with formula-safe cells in `src/interfaces/portals/wan_dashboard/routes.py`.
- [X] T034 [US3] Render insight metrics and export controls in `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`.
- [X] T035 [US3] Verify rate-limit and Mist error responses retain prior data and show a visible status in the T003 test method.

**Checkpoint**: The operator can review insights and export selected data without exposing credentials or hiding API failures.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Validate compatibility, accessibility, documentation, and shared deployment behavior.

- [X] T036 [P] Update the portal feature description and source attribution in `README.md`.
- [X] T037 Add the release note for issue #4195 in `changelog.d/issue-4195-mistcircuitstats-wan.md` when implementation is ready to ship.
- [X] T038 [P] Update the operator portal guide in `documentation/wiki/Web-Portal.md` with the WAN dashboard route and user workflows.
- [X] T039 Run the changed feature tests in `tests/integration/web_portal/wan_dashboard/` and `tests/e2e/web_portal/test_portal_smoke.py`.
- [X] T040 Run Ruff, Black, mypy, Bandit, and STE checks for the changed feature and documentation files.
- [X] T041 Run the existing Mist API compatibility, portal operation coverage, and compose policy guardrails in `tests/integration/test_mistapi_sdk_compatibility.py`, `tests/guardrails/test_portal_operation_coverage.py`, and `tests/guardrails/test_compose_naming_policy.py`.
- [X] T042 Verify `compose.yml` has no new service, database, or published port for the feature.
- [X] T043 Compare the integrated dashboard against the source screenshots and flows in a browser with synthetic data. Record the comparison in the implementation pull request.
- [X] T044 Measure source and integrated page latency for the same synthetic organization and record both values in the implementation pull request. Set no new latency target before collecting the baseline.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Creates feature package and test locations.
- **Foundational (Phase 2)**: Depends on setup and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on the shared portal, authorization, SDK, and cache boundaries.
- **User Story 2 (Phase 4)**: Depends on the gateway and site data contracts from User Story 1.
- **User Story 3 (Phase 5)**: Depends on the gateway and port selection from User Story 1 and User Story 2.
- **Polish (Phase 6)**: Depends on all three user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Independent after the foundational phase.
- **User Story 2 (P2)**: Uses gateway and site identifiers from User Story 1.
- **User Story 3 (P3)**: Uses selected gateway and port context from User Stories 1 and 2.

### Parallel Opportunities

- T012, T013, and T014 can run in parallel because they use different test files.
- T020, T021, and T022 can run in parallel because they use different test files.
- T028, T029, and T030 can run in parallel because they use different test files.
- T036 and T037 can run in parallel because they update separate documentation files.

## Parallel Example: User Story 1

```text
Task: T012 Add pagination and cache tests in tests/integration/web_portal/wan_dashboard/test_services.py
Task: T013 Add route tests in tests/integration/web_portal/wan_dashboard/test_routes.py
Task: T014 Extend the dashboard end-to-end test in tests/e2e/web_portal/test_portal_smoke.py
```

## Implementation Strategy

### MVP First

1. Complete setup and foundational tasks.
2. Complete User Story 1.
3. Run the independent overview tests and portal regression tests.
4. Review the dashboard in the shared portal with synthetic data.

### Incremental Delivery

1. Deliver organization overview and filters.
2. Add port details, traffic charts, and peer paths.
3. Add WAN Insights and exports.
4. Run the full feature test set and verify the unchanged compose service set.

## Notes

- All 44 tasks are complete. The current feature tests pass at 92.05% coverage, and the browser journey verifies the operator workflows with synthetic responses.
- The offline latency baseline measured 74.54 ms for the source dashboard and 72.17 ms for the integrated dashboard. Both measurements waited for three gateway rows after DOMContentLoaded in Chromium. The harness blocked source CDN requests and mocked the integrated API.
- Do not create a second database, Redis service, web server, or public port.
- Do not copy source assets until the feature retains CC BY-NC-SA 4.0 attribution and modification notices.
- Do not mark a task complete until its tests and file evidence pass.

## Implementation Validation (2026-10-16)

- Feature, portal, SDK, and guardrail tests: 109 passed and 1 skipped in 8.54 seconds.
- Feature integration coverage: 52 passed with 92.05% coverage. The required threshold was 90%.
- The post-commit test-quality gate checked 5 test files and found 0 new issues. It skipped 3 files and found 0 parse errors.
- Ruff passed. Black left 2,464 files unchanged. Mypy found no issues in 853 source files.
- Bandit, Vulture, and pydocstyle exited with code 0. Complexity stayed within the limit. Interrogate reported 99.7% coverage.
- STE scores passed for all 6 changed Markdown files. Their scores ranged from 95 to 99.
- Compileall passed, and `compose.yml` remained unchanged.
- The Markdown link checker found one existing extensionless GitHub Wiki link in `documentation/wiki/Web-Portal.md:19`. The `Container-Setup.md` page and target heading exist.
- The portal browser journey passed with synthetic Mist responses. The recorded offline latency baseline remains 74.54 ms for the source and 72.17 ms for the integrated page.

### CI navigation regression repair (2026-10-16)

- The initial CI run found a template error when an isolated app did not register the WAN dashboard blueprint.
- The portal now enables the dashboard link only when `wan_dashboard.page` exists in the route table.
- `.venv/bin/python -m pytest -p no:cacheprovider -q tests/unit/websocket_streams/web/test_ws_blueprint_routes.py::test_page_and_catalog_routes_answer` passed 1 test.
- `.venv/bin/python -m pytest -p no:cacheprovider -q tests/integration/web_portal/wan_dashboard tests/e2e/web_portal/test_portal_smoke.py` passed 71 tests.
- `.venv/bin/python -m pytest -p no:cacheprovider -q tests/unit/websocket_streams/web/test_ws_blueprint_routes.py::test_page_and_catalog_routes_answer` passed 1 test.
- The new isolated-template regression test passed 1 test.
- `.venv/bin/python -m pytest -p no:cacheprovider -q tests/e2e/websockets_tab` passed 197 tests.
- `.venv/bin/python -m ruff check web_portal/app.py` passed.
- The first updated CI run found 90 pixels of horizontal overflow on a tablet viewport. The portal now collapses navigation below 1200 pixels.
- The tablet navigation and overflow regression tests passed 2 tests locally.
