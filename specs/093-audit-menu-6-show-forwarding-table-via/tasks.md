---

description: "Tasks for Audit Menu #6 — Show Forwarding Table via WebSocket"
---

# Tasks: Audit Menu #6 — Show Forwarding Table via WebSocket

**Input**: plan.md, spec.md (required). Optional: research.md, data-model.md, contracts/, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Update dependency manifest to ensure required packages (mistapi>=0.59, websocket-client, tenacity, pytest) in pyproject.toml
- [ ] T002 Create tests/integration/run_mock_ws_server.py to launch a configurable mocked WebSocket server for integration tests
- [ ] T003 [P] Add development/test dependencies to requirements-dev.txt (websocket-client, pytest-mock, tenacity) and document install steps in specs/093-audit-menu-6-show-forwarding-table-via/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

- [ ] T004 Implement mistapi_wrapper in misthelper/utils/mistapi_wrapper.py exposing show_forwarding_table(site_id, device_id, payload) that centralizes host resolution, authentication and timeouts
- [ ] T005 [P] Extend misthelper/utils/websocket_manager.py to provide a subscribe_and_wait_for_ack(channel, timeout=5) helper and expose session demultiplexing hooks for command results
- [ ] T006 Implement robust parser helper _parse_forwarding_table in misthelper/utils/routing_utils.py (buffer assembly + json.JSONDecoder.raw_decode loop) and document behavior in specs/093-audit-menu-6-show-forwarding-table-via/data-model.md
- [ ] T007 [P] Add retry/backoff helpers using tenacity in misthelper/utils/retry_utils.py and integrate into mistapi_wrapper POST calls
- [ ] T008 Configure logging improvements: ensure global logging configuration records INFO-level operator cancellations and redact secrets; update logging config in misthelper/__init__.py or equivalent
- [ ] T009 Create tests/unit/test_routing_utils.py skeleton with placeholders for parser, retry, and websocket ack tests

**Checkpoint**: Foundational helpers (mistapi_wrapper, websocket ack, parser, retry, logging) are implemented and unit-test skeletons exist

---

## Phase 3: User Story 1 - Successful Forwarding Table Retrieval (Priority: P1) 🎯 MVP

**Goal**: Restore and harden end-to-end forwarding-table workflow (site/device selection → REST POST via mistapi_wrapper → WebSocket subscription ACK → receive results → parse → formatted display)

**Independent Test**: Integration test using mocked WS server and pytest-mock to stub mistapi responses. The test should drive the full command and assert the formatted summary output and resource cleanup.

### Tests (required per spec)

- [ ] T010 [P] [US1] Add unit test for happy-path parsing and display in tests/unit/test_websocket_commands.py (test_show_forwarding_table_happy_path)
- [ ] T011 [P] [US1] Add end-to-end integration test tests/integration/test_show_forwarding_table_end_to_end.py that uses tests/integration/run_mock_ws_server.py and mistapi_wrapper mock

### Implementation

- [ ] T012 [P] [US1] Implement default prefix handling and confirmation (use 0.0.0.0/0 when empty) in misthelper/commands/websocket_commands.py
- [ ] T013 [US1] Replace raw requests.post usage with mistapi_wrapper.show_forwarding_table(site_id, device_id, payload) in misthelper/utils/routing_utils.py (or commands layer where current raw POST is located)
- [ ] T014 [US1] Implement WebSocket subscribe-and-wait-for-ack usage and session-result demultiplexing in misthelper/utils/routing_utils.py using websocket_manager.subscribe_and_wait_for_ack
- [ ] T015 [US1] Implement formatted summary rendering of forwarding table results (entry count, unique prefixes, services, tenants, protocols, interfaces) in misthelper/commands/websocket_commands.py (exact output helper function)
- [ ] T016 [US1] Add integration test hooks (fixtures) in tests/conftest.py to start/stop mocked WS server for the end-to-end test

**Checkpoint**: US1 should be independently runnable and testable with mocked WS server

---

## Phase 4: User Story 2 - Graceful Error Handling and Operator Guidance (Priority: P1)

**Goal**: Provide clear actionable feedback for failure modes and ensure deterministic cleanup of WebSocket and resources

**Independent Test**: Unit tests that simulate cancellation, device offline, subscription failure, REST error, and timeout

### Tests

- [ ] T017 [P] [US2] Add unit tests for each failure mode in tests/unit/test_websocket_commands.py (cancellation, connection failure, REST 4xx/5xx, timeout)

### Implementation

- [ ] T018 [US2] Ensure execute_show_forwarding_table returns clear exit codes/messages and logs INFO on operator cancellation in misthelper/commands/websocket_commands.py
- [ ] T019 [US2] Implement device-type-specific troubleshooting messages and explicit error mapping in misthelper/utils/routing_utils.py (map timeout vs unsupported-device vs auth error)
- [ ] T020 [US2] Ensure WebSocket cleanup lives in finally and add unit tests that verify socket close is called on all exit paths in tests/unit/test_websocket_commands.py

**Checkpoint**: US2 behavior validated by unit tests and logs

---

## Phase 5: User Story 3 - Input Parameter Validation (Priority: P2)

**Goal**: Validate IP prefix, HA node, service name and VRF before issuing the command and prompt operator to correct invalid input

**Independent Test**: Unit tests for validation helpers covering valid/invalid CIDR, node values, and length/character limits

### Tests

- [ ] T021 [P] [US3] Add unit tests for validation helpers in tests/unit/test_validation.py (CIDR, node, string limits)

### Implementation

- [ ] T022 [US3] Implement validation helpers in misthelper/utils/validation.py using ipaddress.ip_network for CIDR validation and length/character checks for service/VRF
- [ ] T023 [US3] Integrate validation and re-prompt logic into misthelper/commands/websocket_commands.py so invalid input is rejected with a clear prompt before API calls

**Checkpoint**: US3 is testable via validation unit tests and interactive prompt behavior

---

## Phase 6: User Story 4 - Automated Test Coverage (Priority: P2)

**Goal**: Bring forwarding-table-related code to required test coverage levels and add CI integration

**Independent Test**: Run pytest to verify unit and integration tests pass and coverage thresholds are met

### Tests & CI

- [ ] T024 [P] [US4] Implement comprehensive unit tests for parser edge cases in tests/unit/test_routing_utils.py (single-line JSON, multi-line JSON, mixed diagnostic + JSON, empty response, malformed JSON)
- [ ] T025 [US4] Add integration test that simulates large payloads and measures end-to-end completion time in tests/integration/test_show_forwarding_table_large_payload.py
- [ ] T026 [US4] Update .github/workflows/ci.yml to run forwarding-table unit and integration tests and fail the build on regressions

### Implementation

- [ ] T027 [US4] Ensure tests are isolated and use pytest-mock fixtures in tests/unit/ and tests/integration/

**Checkpoint**: Tests pass locally and in CI

---

## Phase 7: User Story 5 - Robust JSON Parsing (Priority: P3)

**Goal**: Harden parser to handle all realistic device output formats without silent data loss and provide operator-accessible raw output on parse failures

**Independent Test**: Unit tests that feed parser many realistic raw outputs and assert extracted entries + raw fallback behavior

- [ ] T028 [US5] Add parser unit tests for multi-chunk and mixed-content inputs in tests/unit/test_routing_utils.py
- [ ] T029 [US5] Improve parser error handling to return [] (empty) on empty/whitespace outputs and to log parse errors while making raw output available via a "Show raw output" option in misthelper/commands/websocket_commands.py
- [ ] T030 [US5] Add integration test that injects malformed JSON and asserts operator-facing raw-output option is available and descriptive error logged

**Checkpoint**: Parser covers at least the five formats listed in acceptance criteria

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final cleanup, and non-functional improvements

- [ ] T031 Create specs/093-audit-menu-6-show-forwarding-table-via/quickstart.md with developer instructions to run unit and integration tests locally (including mocked WS server steps)
- [ ] T032 [P] Update specs/093-audit-menu-6-show-forwarding-table-via/contracts/ with example request/response payloads for show_forwarding_table (if not present)
- [ ] T033 Code cleanup: address linter warnings and run formatting across modified files (apply via pre-commit hooks); touch files: misthelper/utils/routing_utils.py, misthelper/commands/websocket_commands.py, misthelper/utils/mistapi_wrapper.py
- [ ] T034 [P] Add release note entry in docs/CHANGELOG.md describing AF-01..AF-08 remediations

---

## Dependencies & Execution Order

- Phase 1 (Setup) -> Phase 2 (Foundational) -> Phase 3/4 (US1 & US2, both P1) -> Phase 5/6 (US3 & US4, P2) -> Phase 7 (US5, P3) -> Phase 8 (Polish)

**User story order (by priority)**:
1. US1 (P1) — Successful retrieval (MVP)
2. US2 (P1) — Graceful error handling
3. US3 (P2) — Input validation
4. US4 (P2) — Automated test coverage
5. US5 (P3) — Robust JSON parsing

## Parallel execution examples

- Parallel: T003, T005, T007, T024, T025, T032, T034 can run concurrently as they touch different files or CI
- Example: While T004 (mistapi_wrapper) is being implemented, another developer can implement T006 (parser) and T007 (retry helpers) in parallel

## Implementation strategy

- MVP First: Complete Phases 1+2 and deliver US1 (T010..T016) as the first deployable increment
- Incremental: After US1 validated, deliver US2, then US3/US4, then US5
- Tests: Write tests first for each story (tasks marked [P] under Tests) and ensure they fail before implementing the code


---

## Reporting Summary

- Generated file: specs/093-audit-menu-6-show-forwarding-table-via/tasks.md
- Total tasks: 34
- Task count per user story:
  - US1: 7 tasks (T010-T016)
  - US2: 4 tasks (T017-T020)
  - US3: 3 tasks (T021-T023)
  - US4: 4 tasks (T024-T027)
  - US5: 3 tasks (T028-T030)
  - Setup/Foundational/Polish (non-story): 13 tasks (T001-T009, T031-T034)
- Parallel opportunities identified: T003, T005, T007, T011, T024, T025, T032, T034, plus model/test tasks within each US marked [P]

## Independent test criteria (one-line per story)
- US1: Full end-to-end integration test using mocked WS server validates site/device selection, REST POST, WS subscribe ACK, result parsing, and formatted output
- US2: Unit tests simulate cancellation, connection failure, REST errors, and timeouts and verify INFO-level cancellation logs and deterministic cleanup
- US3: Validation unit tests cover valid/invalid CIDR, HA node values, and string length/character constraints
- US4: Unit and integration tests run in CI; coverage measurement ensures >=80% branches for forwarding-table code paths
- US5: Parser unit tests validate extraction from single-line, multi-line, multi-chunk, mixed-text, empty, and malformed inputs with raw-output fallback

## Suggested MVP scope
- Deliverable for MVP: User Story 1 (T010..T016) after completing Foundational tasks (T004..T009) — this enables a working, testable forwarding-table retrieval flow

## Format validation
- ALL tasks follow the required checklist format: each line begins with "- [ ]", includes a sequential TaskID (T001..T034), includes [P] only where parallelizable, includes [USx] labels for user-story-specific tasks, and provides an exact file path where the change or test should be implemented


