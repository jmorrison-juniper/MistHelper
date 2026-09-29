# Tasks: Organization WAN Edge Scorecard

**Input**: Design documents from `specs/3560-wan-edge-scorecard/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/scorecard-outputs.md`, `quickstart.md`, and `wiring.md`

**Tests**: Tests are required because `spec.md` defines independent tests and measurable outcomes.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel because it uses different files and has no dependency on incomplete work.
- **[Story]**: The task maps to a user story, such as `[US1]`, `[US2]`, or `[US3]`.
- Each task names the exact file path that the implementer must create, read, or change.
- A deferred task is intentionally scheduled for the integration pull request, not this feature package pull request.

## Phase 1: Setup and Research Verification

**Purpose**: Verify the API source, existing gateway statistics path, and feature wiring before implementation starts.

- [ ] T001 Read the reusable gateway statistics export path in `src/export/org_device_stats_exporter.py`
- [ ] T002 Verify the menu 18 path `_dispatch_gateway_stats_device_stats_with_freshness` in `MistHelper.py`
- [ ] T003 [P] Verify the OpenAPI schemas `stats_gateway`, `dhcpd_stat_lan`, `vpn_peers`, and `bgp_peers` in `documentation/mist-api-openapi3json.json`
- [ ] T004 [P] Verify `requirements.txt` and the installed `mistapi` package expose `listOrgDevicesStats` with a gateway type parameter
- [ ] T005 [P] Confirm `specs/3560-wan-edge-scorecard/wiring.md` contains all implementation contract sections and records the research verification results

---

## Phase 2: Foundational Package and Shared Models

**Purpose**: Create the report package and shared scorecard types that all user stories use.

**Critical**: No user story implementation can start until this phase is complete.

- [ ] T006 Create package initializer in `src/reports/wan_edge_scorecard/__init__.py`
- [ ] T007 [P] Create gateway, DHCP pool, site scorecard, and organization scorecard models in `src/reports/wan_edge_scorecard/models.py`
- [ ] T008 [P] Create shared scoring helpers for percent math, predominant version, threshold parsing, and missing values in `src/reports/wan_edge_scorecard/scoring.py`
- [ ] T009 Create the `WanEdgeScorecard` class skeleton with static `run()` and dependency seams in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T010 [P] Create unit test fixture builders for gateway statistics samples in `tests/unit/reports/wan_edge_scorecard/conftest.py`
- [ ] T011 [P] Create package test initializer in `tests/unit/reports/wan_edge_scorecard/__init__.py`

**Checkpoint**: The package exists, shared models exist, and tests can import the package.

---

## Phase 3: User Story 1 - Export an Organization WAN Edge Scorecard (Priority: P1)

**Goal**: Export one gateway row for each WAN gateway with identity, version, configuration, service, peer, DHCP, uptime, and trouble values.

**Independent Test**: Run the targeted unit tests with fixture gateway statistics and confirm the main gateway scorecard output has one row per gateway.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add a failing unit test for one row per gateway in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T013 [P] [US1] Add a failing unit test for missing optional gateway fields in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T014 [P] [US1] Add a failing unit test for predominant version and version compliance in `tests/unit/reports/wan_edge_scorecard/test_scoring.py`
- [ ] T015 [P] [US1] Add a failing unit test for reuse of the shared gateway statistics fetch seam in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement gateway statistics fetch reuse in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T017 [US1] Implement gateway row creation in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T018 [US1] Implement version compliance and missing value handling in `src/reports/wan_edge_scorecard/scoring.py`
- [ ] T019 [US1] Implement export of `WanEdgeScorecard.csv` through configured export behavior in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T020 [US1] Add action logging before and after fetch, transform, and export actions in `src/reports/wan_edge_scorecard/scorecard.py`

**Checkpoint**: User Story 1 creates the main gateway scorecard and passes its targeted tests.

---

## Phase 4: User Story 2 - Review DHCP Pool Pressure Across Gateways (Priority: P2)

**Goal**: Export DHCP pool rows and gateway DHCP risk values with safe threshold and missing-data behavior.

**Independent Test**: Run the targeted unit tests with normal pools, high-use pools, invalid thresholds, and absent DHCP statistics.

### Tests for User Story 2

- [ ] T021 [P] [US2] Add a failing unit test for the default 80 percent DHCP warning threshold in `tests/unit/reports/wan_edge_scorecard/test_scoring.py`
- [ ] T022 [P] [US2] Add a failing unit test for valid and invalid `DHCP_POOL_WARN_PERCENT` values in `tests/unit/reports/wan_edge_scorecard/test_scoring.py`
- [ ] T023 [P] [US2] Add a failing unit test for absent `dhcpd_stat` with gateway pool count `0` in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T024 [P] [US2] Add a failing unit test for DHCP pool row leased, total, percent, and over-threshold values in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement DHCP threshold parsing in `src/reports/wan_edge_scorecard/scoring.py`
- [ ] T026 [US2] Implement DHCP pool extraction and safe percent calculation in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T027 [US2] Implement gateway worst pool utilization and pool count values in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T028 [US2] Implement export of `WanEdgeDhcpPools.csv` through configured export behavior in `src/reports/wan_edge_scorecard/scorecard.py`

**Checkpoint**: User Story 2 creates the DHCP pool report and passes its targeted tests.

---

## Phase 5: User Story 3 - Summarize Site and Organization Health (Priority: P3)

**Goal**: Export site scorecard rows and print an organization console summary that matches the gateway rows.

**Independent Test**: Run the targeted unit tests with multiple sites, down VPN peers, non-established BGP peers, and summary expectations.

### Tests for User Story 3

- [ ] T029 [P] [US3] Add a failing unit test for VPN peers up and down in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T030 [P] [US3] Add a failing unit test for BGP peers established and not established in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T031 [P] [US3] Add a failing unit test for site scorecard percentages in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`
- [ ] T032 [P] [US3] Add a failing unit test for organization console summary percentages in `tests/unit/reports/wan_edge_scorecard/test_scorecard.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement VPN and BGP peer counts in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T034 [US3] Implement site scorecard percentage calculation in `src/reports/wan_edge_scorecard/scoring.py`
- [ ] T035 [US3] Implement organization scorecard percentage calculation in `src/reports/wan_edge_scorecard/scoring.py`
- [ ] T036 [US3] Implement export of `WanEdgeScorecardBySite.csv` through configured export behavior in `src/reports/wan_edge_scorecard/scorecard.py`
- [ ] T037 [US3] Implement the organization console summary in `src/reports/wan_edge_scorecard/scorecard.py`

**Checkpoint**: User Story 3 creates the site scorecard, prints the organization summary, and passes its targeted tests.

---

## Phase 6: Deferred Integration Pull Request Tasks

**Purpose**: Mark repository integration work that must occur outside the feature package pull request.

- [ ] T038 Deferred to the integration pull request: register menu 279 in `MistHelper.py`
- [ ] T039 Deferred to the integration pull request: register menu 279 as safe in `src/utils/operation_registry.py`
- [ ] T040 Deferred to the integration pull request: confirm no persistent endpoint primary key entry is required in `src/refactors/endpoint_primary_key_strategies.py`
- [ ] T041 Deferred to the integration pull request: update operation count and menu entry in `README.md`
- [ ] T042 Deferred to the integration pull request: update generated menu documentation in `documentation/menu_reference.md`
- [ ] T043 Deferred to the integration pull request: run generated wiki updates with `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`

---

## Phase 7: Polish and Validation Gates

**Purpose**: Add release evidence and run the fleet validation gates before the pull request is ready.

- [ ] T044 [P] Create release note fragment in `changelog.d/issue-3560-wan-edge-scorecard.md`
- [ ] T045 Run `python -m pytest tests\unit\reports\wan_edge_scorecard` and record the result in the pull request
- [ ] T046 Run `python -m py_compile MistHelper.py` and record the result in the pull request
- [ ] T047 Run `python -m ruff check MistHelper.py src\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard` and record the result in the pull request
- [ ] T048 Run `python -m black --check MistHelper.py src\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard` and record the result in the pull request
- [ ] T049 Run `python MistHelper.py --test` and confirm menu 279 completes without an operator prompt
- [ ] T050 Confirm the implementation changes do not edit `.specify/feature.json`
- [ ] T051 Confirm the implementation pull request includes `src/reports/wan_edge_scorecard/`, `tests/unit/reports/wan_edge_scorecard/`, and `changelog.d/issue-3560-wan-edge-scorecard.md`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1** has no dependency.
- **Phase 2** depends on Phase 1.
- **Phase 3** depends on Phase 2.
- **Phase 4** depends on Phase 2 and can run after Phase 3 starts if shared files are coordinated.
- **Phase 5** depends on Phase 2 and can run after Phase 3 starts if shared files are coordinated.
- **Phase 6** is deferred to the integration pull request.
- **Phase 7** depends on the selected implementation stories.

### User Story Dependencies

- **User Story 1 (P1)** can start after Phase 2 and is the MVP.
- **User Story 2 (P2)** can start after Phase 2, but it shares `scorecard.py` and `scoring.py` with User Story 1.
- **User Story 3 (P3)** can start after Phase 2, but it shares `scorecard.py` and `scoring.py` with User Story 1.

### Within Each User Story

- Write tests first and confirm they fail.
- Implement models and scoring before report orchestration.
- Implement export after row creation.
- Validate the story before the next priority story is merged.

## Parallel Opportunities

- T003, T004, and T005 can run in parallel after T001 and T002 start.
- T007, T008, T010, and T011 can run in parallel after T006 starts.
- T012 through T015 can run in parallel because they add separate test cases.
- T021 through T024 can run in parallel because they add separate DHCP test cases.
- T029 through T032 can run in parallel because they add separate summary test cases.
- Phase 6 tasks can be prepared in the integration pull request after the package implementation stabilizes.

## Parallel Example: User Story 1

```text
Task: "T012 [P] [US1] Add a failing unit test for one row per gateway in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T013 [P] [US1] Add a failing unit test for missing optional gateway fields in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T014 [P] [US1] Add a failing unit test for predominant version and version compliance in tests/unit/reports/wan_edge_scorecard/test_scoring.py"
Task: "T015 [P] [US1] Add a failing unit test for reuse of the shared gateway statistics fetch seam in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
```

## Parallel Example: User Story 2

```text
Task: "T021 [P] [US2] Add a failing unit test for the default 80 percent DHCP warning threshold in tests/unit/reports/wan_edge_scorecard/test_scoring.py"
Task: "T022 [P] [US2] Add a failing unit test for valid and invalid DHCP_POOL_WARN_PERCENT values in tests/unit/reports/wan_edge_scorecard/test_scoring.py"
Task: "T023 [P] [US2] Add a failing unit test for absent dhcpd_stat with gateway pool count 0 in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T024 [P] [US2] Add a failing unit test for DHCP pool row leased, total, percent, and over-threshold values in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
```

## Parallel Example: User Story 3

```text
Task: "T029 [P] [US3] Add a failing unit test for VPN peers up and down in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T030 [P] [US3] Add a failing unit test for BGP peers established and not established in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T031 [P] [US3] Add a failing unit test for site scorecard percentages in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
Task: "T032 [P] [US3] Add a failing unit test for organization console summary percentages in tests/unit/reports/wan_edge_scorecard/test_scorecard.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete User Story 1.
4. Run `python -m pytest tests\unit\reports\wan_edge_scorecard`.
5. Stop and review the gateway scorecard output before User Story 2.

### Incremental Delivery

1. Add User Story 1 for the gateway scorecard.
2. Add User Story 2 for DHCP pool risk.
3. Add User Story 3 for site and organization summaries.
4. Complete the deferred integration pull request tasks after the report package passes tests.
5. Run all validation gates before the pull request is ready.
