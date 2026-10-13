# Tasks: Mist WAN Performance

**Input**: Design documents in `specs/live/20261013-182629-mist-wan-performance/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/wan-performance.md`, and `quickstart.md`

**Tests**: Required by the feature specification and project constitution. Write tests before implementation.

**Organization**: The first two phases hold cross-cutting evidence and foundation work. Later phases follow the five prioritized user stories.

## Planning Boundary

Every task below is future work. No task is authorized by this planning PR.
Do not start any implementation task until the required investigation is complete, the design is approved, and the user authorizes implementation.
In particular, do not copy source code, fixtures, or visual assets without written rights confirmation.

## Phase 1: Setup and Evidence Gates

**Purpose**: Resolve source, rights, storage, and request contracts before product changes.

- [ ] T001 Record the HPE Network Operations notice, identify the authorized rights approver, confirm written rights separately for source code, fixtures, and screenshots, and document approval or denial evidence and the independent implementation boundary in `specs/live/20261013-182629-mist-wan-performance/research.md`.
- [ ] T002 [P] Verify every candidate endpoint against the pinned Mist SDK and OpenAPI records, then record explicit method arguments, output fields, units, pagination, and mocked response evidence in `specs/live/20261013-182629-mist-wan-performance/research.md`.
- [ ] T003 Inventory all four completed source pages, their visual hierarchy, metric definitions, selectors, direct links, and excluded CLI TODO stubs in `specs/live/20261013-182629-mist-wan-performance/research.md`.
- [ ] T004 Count tracked Python children in every proposed parent, confirm a compliant nested package path, and record existing hierarchy debt and incremental remediation in `specs/live/20261013-182629-mist-wan-performance/plan.md`.
- [ ] T005 Identify the configured durable application store and existing DataExporter selection, its read/write APIs, transactions, unique-key support, failure behavior, and retention owner in `specs/live/20261013-182629-mist-wan-performance/research.md`.
- [ ] T006 Verify completed source history behavior, source fields, UTC hour identity, aggregation boundaries, missing-data rules, historical coverage, and retention; map it to one selected current application database in `specs/live/20261013-182629-mist-wan-performance/data-model.md`.
- [ ] T007 Verify source Redis key format, serialization, 31-day history TTL, refresh triggers, worker lifecycle, and duplicate-work behavior in `specs/live/20261013-182629-mist-wan-performance/research.md`.
- [ ] T008 [P] Verify whether the source has a completed stable export route and format; document the verified contract or exclude export from `specs/live/20261013-182629-mist-wan-performance/contracts/wan-performance.md`.
- [ ] T009 Prove one shared organization request ledger can account for portal refresh, existing operations, pagination, retries, and fast mode across workers in `specs/live/20261013-182629-mist-wan-performance/contracts/wan-performance.md`.
- [ ] T010 [P] Inspect current Flask, database, Redis, and browser test fixtures, verify screenshot and trace paths are ignored and excluded from the PR manifest, and record exact mocked tests in `specs/live/20261013-182629-mist-wan-performance/quickstart.md`.

**Gate**: T001 through T010 must pass before product implementation. Stop if rights are denied, SDK contracts remain unverified, one authoritative existing database cannot be selected through current configuration, history semantics remain unknown, or shared request admission cannot be proven.

## Phase 2: Foundational Work

**Purpose**: After approval, establish storage, identity, refresh, and test foundations that block every user story.

- [ ] T011 [P] Add failing identity, serialization, natural-key, finite-value, and invalid-measurement tests in `tests/unit/wan_performance/test_domain.py`.
- [ ] T012 [P] Add failing selected-store transaction, uniqueness, configured-export-selection, and outage tests in `tests/integration/wan_performance/test_history_repository.py`.
- [ ] T013 [P] Add failing Redis namespace, organization isolation, evidence-approved TTL, serialization, corrupt-payload, and outage tests in `tests/integration/wan_performance/test_cache.py`.
- [ ] T014 [P] Add failing lease expiry, competing-worker, shared quota, retry admission, and fast-mode coordination tests in `tests/contract/wan_performance/test_refresh_coordination.py`.
- [ ] T015 [P] Add failing fixture-isolation and no-client-start tests in `tests/unit/wan_performance/test_offline_fixtures.py`.
- [ ] T016 [P] Add offline synthetic fixtures that start no Mist, Redis, database, or refresh clients in `tests/fixtures/wan_performance/offline_dashboard.py`.
- [ ] T017 [P] Add typed site, gateway, circuit, and peer-path identities in `src/interfaces/portals/wan_performance/domain/identity.py`, preserving verified source identifiers and membership checks.
- [ ] T018 [P] Add UTC hourly circuit and peer measurement records with units, coverage, provenance, finite-value validation, and natural keys in `src/interfaces/portals/wan_performance/domain/measurement.py`.
- [ ] T019 [P] Add approved calendar period and missing-data rules in `src/interfaces/portals/wan_performance/domain/aggregation.py`, using evidence from T006.
- [ ] T020 Add one selected-store repository that follows existing configured DataExporter selection, transactional upserts, unique identities, and explicit unavailable-history errors in `src/interfaces/portals/wan_performance/integration/history_repository.py`; do not add another database.
- [ ] T021 Add isolated, versioned Redis JSON keys with T007-approved namespace and TTLs in `src/interfaces/portals/wan_performance/integration/cache.py`.
- [ ] T022 Add durable refresh ownership and shared request admission in `src/interfaces/portals/wan_performance/integration/refresh_coordinator.py`; block all Mist SDK calls unless a shared lease and quota permit them.

**Checkpoint**: Do not begin a user story until T001 through T010 pass and T011 through T022 are implemented with their test-first checks.

## Phase 3: User Story 1 - Identify Affected Circuits (Priority: P1)

**Goal**: Give operators an overview of site and circuit utilization, congestion, availability, and path quality.

**Independent Test**: Load a controlled dataset through the Flask test client and verify overview metrics, units, coverage, detail links, and no false healthy values for missing records.

### Tests for User Story 1

- [ ] T023 [P] [US1] Test overview aggregation, thresholds, units, coverage, and missing values in `tests/unit/wan_performance/test_overview.py`.
- [ ] T024 [P] [US1] Test overview store reads, stale-history behavior, and authorization middleware in `tests/integration/wan_performance/test_overview.py`.
- [ ] T025 [P] [US1] Test overview navigation, period context, and stable selectors in `tests/e2e/wan_performance/test_overview.py`.

### Implementation for User Story 1

- [ ] T026 [US1] Add overview query and approved summaries in `src/interfaces/portals/wan_performance/domain/overview.py`.
- [ ] T027 [US1] Add the overview page and period controls in `src/interfaces/portals/wan_performance/presentation/templates/overview.html` with the contract `data-testid` values.

## Phase 4: User Story 2 - Investigate A Gateway And WAN Port (Priority: P1)

**Goal**: Let operators inspect gateway health, WAN ports, bandwidth, and circuit history.

**Independent Test**: Open gateway and port links with controlled identities; verify site membership, exact encoded port names, units, and parent navigation.

### Tests for User Story 2

- [ ] T028 [P] [US2] Test gateway identity, membership, health, and port links in `tests/unit/wan_performance/test_gateway.py`.
- [ ] T029 [P] [US2] Test port slash encoding, conflicting identifiers, bandwidth units, and not-found states in `tests/unit/wan_performance/test_port.py`.
- [ ] T030 [P] [US2] Test direct gateway and WAN-port journeys with stable selectors in `tests/e2e/wan_performance/test_gateway_and_port.py`.

### Implementation for User Story 2

- [ ] T031 [P] [US2] Add gateway detail queries in `src/interfaces/portals/wan_performance/domain/gateway.py`.
- [ ] T032 [P] [US2] Add port detail queries and strict one-step identifier decoding in `src/interfaces/portals/wan_performance/domain/circuit.py`.
- [ ] T033 [US2] Add gateway and port views in `src/interfaces/portals/wan_performance/presentation/templates/gateway.html` and `src/interfaces/portals/wan_performance/presentation/templates/port.html`.

## Phase 5: User Story 3 - Investigate A VPN Peer (Priority: P2)

**Goal**: Let operators inspect peer packet loss, latency, jitter, tunnel identity, and return navigation.

**Independent Test**: Open a peer link with controlled paths; verify canonical identity and separate records for each stable tunnel.

### Tests for User Story 3

- [ ] T034 [P] [US3] Test peer MAC validation, tunnel identity, and quality units in `tests/unit/wan_performance/test_vpn_peer.py`.
- [ ] T035 [P] [US3] Test a direct VPN-peer journey and its return link in `tests/e2e/wan_performance/test_vpn_peer.py`.

### Implementation for User Story 3

- [ ] T036 [US3] Add peer detail queries and path separation in `src/interfaces/portals/wan_performance/domain/peer_path.py`.
- [ ] T037 [US3] Add the peer page in `src/interfaces/portals/wan_performance/presentation/templates/vpn_peer.html` with explicit units and tunnel selectors.

## Phase 6: User Story 4 - Compare Historical Periods (Priority: P2)

**Goal**: Let operators compare hourly UTC data and approved daily, weekly, and monthly summaries.

**Independent Test**: Use controlled boundary and duplicate records; verify calendar windows, coverage, repeat upserts, and no invented measurements.

### Tests for User Story 4

- [ ] T038 [P] [US4] Test UTC hour, day, week, month, leap-day, and partial-period boundaries in `tests/unit/wan_performance/test_aggregation.py`.
- [ ] T039 [P] [US4] Test repeat collection upserts, coverage, stale history, and selected-store failures in `tests/integration/wan_performance/test_history.py`.

### Implementation for User Story 4

- [ ] T040 [US4] Add verified period queries and versioned summaries in `src/interfaces/portals/wan_performance/domain/history.py`.
- [ ] T041 [US4] Add historical comparison and gap labels in `src/interfaces/portals/wan_performance/presentation/templates/history.html`.

## Phase 7: User Story 5 - Distinguish Live, Stale, And Synthetic Data (Priority: P1)

**Goal**: Make data provenance and refresh status explicit without exceeding shared Mist API limits.

**Independent Test**: Simulate synthetic mode, stale records, quota exhaustion, SDK failures, cache outage, and competing workers; verify visible states and bounded requests.

### Tests for User Story 5

- [ ] T042 [P] [US5] Test live, stale, unavailable, and synthetic state transitions in `tests/unit/wan_performance/test_data_state.py`.
- [ ] T043 [P] [US5] Test 401, 403, 404, 429, 5xx, timeout, malformed response, and redacted errors in `tests/contract/wan_performance/test_mist_api.py`.
- [ ] T044 [P] [US5] Test cache outage, quota delay, worker duplication, and preserved last-success time in `tests/integration/wan_performance/test_refresh.py`.
- [ ] T045 [P] [US5] Test all four journeys, access denial, missing data, and synthetic labels in `tests/e2e/wan_performance/test_data_states.py`.

### Implementation for User Story 5

- [ ] T046 [US5] Add an SDK-only Mist reader with explicit verified method arguments in `src/interfaces/portals/wan_performance/integration/mist_reader.py`.
- [ ] T047 [US5] Add bounded refresh lifecycle integration to the existing application lifecycle in `src/interfaces/portals/wan_performance/integration/refresh_service.py`.
- [ ] T048 [US5] Add visible state, collection time, and coverage indicators in `src/interfaces/portals/wan_performance/presentation/templates/_data_state.html`.

## Final Phase: Polish And Cross-Cutting Concerns

**Purpose**: Register the pages, verify layout, update operator documentation, and prove the release boundary.

- [ ] T049 Register one WAN Performance blueprint in `web_portal/app.py` and add navigation in `web_portal/templates/base.html` without changing existing routes or access controls.
- [ ] T050 [P] Compare all four source journeys at 1440 by 1100 and 390 pixels in `tests/e2e/wan_performance/test_layout.py`; use source captures only with written screenshot rights from T001, or create an independent baseline, and verify failed traces remain ignored and outside the PR manifest.
- [ ] T051 [P] Document the verified operator routes, metrics, data-state meanings, selected-store behavior, and limitations in `documentation/wan-performance.md` and add the user-facing feature entry to `README.md`.
- [ ] T052 [P] Add the issue-specific release fragment `changelog.d/issue-4200-wan-performance.md` after approved user-visible implementation.
- [ ] T053 Run all applicable unit, contract, integration, E2E, type, lint, formatting, security, SDK-compatibility, committed-test quality, function-size, class-based architecture, ASCII logging, action logging, docstring, and inline-comment gates recorded in `specs/live/20261013-182629-mist-wan-performance/quickstart.md`.
- [ ] T054 Verify the diff adds no database, Snowflake dependency, web service, public port, Compose group, token store, or unauthorized source assets in `specs/live/20261013-182629-mist-wan-performance/quickstart.md`.
- [ ] T055 Record hierarchy-gate results and track an independent maintenance issue for gradual reduction of inherited package excess in `specs/live/20261013-182629-mist-wan-performance/plan.md`.
- [ ] T056 Measure response time and record count on the approved representative data set, then set a measurable page-performance target or document a non-goal in `specs/live/20261013-182629-mist-wan-performance/plan.md`.
- [ ] T057 After code changes, follow the required local gates, explicit feature manifest, commit, rebase, push, PR, CI, squash merge, main build, image revision, deployment, and health verification in `.github/copilot-instructions.md`.

## Dependencies And Execution Order

### Phase Dependencies

- **Phase 1**: T001 through T010 are blocking evidence gates. Rights, SDK contracts, selected storage, or shared quota failure stops implementation.
- **Phase 2**: T011 through T022 establish shared data, ownership, cache, and testing foundations. User stories depend on their completion.
- **Phase 3**: US1 depends on the shared foundations and proves the smallest operator-visible overview.
- **Phase 4**: US2 depends on shared foundations. It may use the overview links from US1, but direct gateway and port routes remain independently testable.
- **Phase 5**: US3 depends on shared foundations. Add a gateway link when US2 exists without making peer queries depend on port rendering.
- **Phase 6**: US4 depends on T006 and shared foundations. It uses the same selected application store.
- **Phase 7**: US5 depends on shared foundations and T009. Enable live refresh only after shared admission passes.
- **Final phase**: Depends on the stories chosen for release. Run T053 and T054 before approval to release.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2. Its overview works with controlled records independently.
- **US2 (P1)**: Starts after Phase 2. Direct gateway and port routes have no required dependency on US1.
- **US3 (P2)**: Starts after Phase 2. Direct peer navigation remains independently testable.
- **US4 (P2)**: Starts after Phase 2 and verified historical contracts in T006.
- **US5 (P1)**: Starts after Phase 2 and verified quota coordination in T009. Live refresh cannot be enabled before this gate.

### Parallel Opportunities

- Phase 1 research tasks T001, T002, T003, T005, T006, T007, and T008 can proceed independently when evidence owners do not conflict.
- Phase 2 domain tasks T011, T012, T013, and T017 can proceed in separate files after T001 through T010 pass.
- Within each user story, independent unit and E2E test files marked `[P]` can be prepared separately.
- US2, US3, and US4 can proceed independently after the common foundation, subject to their evidence gates.
- T049 integrates the routes and navigation after the page modules exist. Keep `web_portal/app.py` owned by one implementer.

### Parallel Example: User Story 1

```text
T023 overview unit tests
T024 overview integration tests
T025 overview browser journey tests
```

Start the three test tasks in separate test files.
Complete the overview query and page tasks after their tests define the independently verifiable contract.

### Parallel Example: User Story 2

```text
T028 gateway unit tests
T029 WAN-port unit tests
T030 gateway and port browser journeys
T031 gateway queries
T032 port queries and decoding
```

Keep gateway and port code in separate modules.
Run T033 after both modules and their view contracts are ready.

## Implementation Strategy

### MVP First

1. Obtain user authorization and complete T001 through T010.
2. Complete and test Phase 2.
3. Implement US1 only and verify its independent test criteria.
4. Do not release live refresh until US5 proves shared request admission.

### Incremental Delivery

1. Add US1 overview with explicit missing and stale states.
2. Add independent gateway and port investigation in US2.
3. Add historical comparisons after T006 approval.
4. Add peer quality details in US3.
5. Enable live refresh only with US5 shared admission and failure tests.
6. Run final layout, documentation, and quality gates before release.

## Planning Boundary

This file is a future implementation plan, not authorization.
The current change stops before every product implementation task.
Issue #4200 remains the migration record for any later implementation request.
