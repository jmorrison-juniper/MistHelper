# Tasks: Adopt mistapi.device_utils for Device Operations

**Input**: Design documents from `/specs/device-utils-adoption/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/adapter-api.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Version detection, adapter scaffolding, and import wiring

- [X] T001 Add `mistapi>=0.61.0` version constraint to requirements.txt and pyproject.toml
- [X] T002 Create `src/device/device_utils_adapter.py` with `DeviceUtilsAdapter` class skeleton, version detection (`DEVICE_UTILS_AVAILABLE` flag via try/except import), and `_command_map` structure per data-model.md
- [X] T003 [P] Create `tests/unit/test_device_utils_adapter.py` with mock `UtilResponse` fixture and test skeleton for `execute()`, `_normalize_response()`, `is_available()`
- [ ] T004 [P] Add startup log message in `MistHelper.py` reporting device_utils availability status (info-level) -- DEFERRED: requires locating safe spot in 28K-line monolith

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core adapter logic that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `DeviceUtilsAdapter.__init__()` in `src/device/device_utils_adapter.py` — accept `mist_session`, populate `_utils_available`, build `_command_map` dispatch table mapping `(device_type, command)` → `device_utils.*` callable
- [X] T006 Implement `DeviceUtilsAdapter._normalize_response()` in `src/device/device_utils_adapter.py` — extract `.data` from `UtilResponse`, flatten via local helper matching `flatten_dict_recursively()`, return `list[dict]` matching current CSV column format
- [X] T007 Implement `DeviceUtilsAdapter._fallback_raw_api()` in `src/device/device_utils_adapter.py` — delegates to caller-injected `fallback_fn`, logs fallback at info level
- [X] T008 Implement `DeviceUtilsAdapter.execute()` in `src/device/device_utils_adapter.py` — route to device_utils or fallback per contracts/adapter-api.md, with before/after action logging
- [X] T009 Implement `DeviceUtilsAdapter.is_available()` in `src/device/device_utils_adapter.py` — check `_utils_available` and `_command_map` lookup
- [X] T010 [P] Write unit tests for `_normalize_response()` in `tests/unit/test_device_utils_adapter.py` — mock UtilResponse with nested data, verify flattened output matches expected CSV columns
- [X] T011 [P] Write unit tests for `execute()` fallback path in `tests/unit/test_device_utils_adapter.py` — mock `DEVICE_UTILS_AVAILABLE=False`, verify raw API path is called
- [ ] T012 Instantiate `DeviceUtilsAdapter` in `MistHelper.py` alongside existing session setup -- DEFERRED until first caller (T016) needs it

**Checkpoint**: Adapter fully functional with dispatch + fallback. No commands migrated yet.

---

## Phase 3: User Story 1 — EX Show Commands via device_utils (Priority: P1) 🎯 MVP

**Goal**: Migrate 6 EX switch show commands to use `device_utils.ex.*` helpers. Output identical to current implementation.

**Independent Test**: Run each show command against a live EX switch, diff CSV output against pre-migration baseline. Diff must be empty.

### Implementation for User Story 1

- [ ] T013 [US1] Add EX show command entries to `_command_map` in `src/device/device_utils_adapter.py` — map `("switch", "show_arp")` → `device_utils.ex.show_arp`, and 5 other EX show commands per spec.md Phase 1 table
- [ ] T014 [P] [US1] Write unit tests for EX show_arp path in `tests/unit/test_device_utils_adapter.py` — mock `device_utils.ex.show_arp()` return, verify normalized output columns match current CSV
- [ ] T015 [P] [US1] Write unit tests for EX show_mac_table, show_dhcp_leases, show_route_summary, show_dot1x_clients, show_evpn_database paths in `tests/unit/test_device_utils_adapter.py`
- [ ] T016 [US1] Rewire show ARP menu operation in `src/device/utility_commands.py` (or `MistHelper.py` WebSocketCommands) to call `DeviceUtilsAdapter.execute("show_arp", "switch", site_id, device_id)` instead of raw API + WebSocket
- [ ] T017 [US1] Rewire remaining 5 EX show commands (show_mac_table, show_dhcp_leases, show_route_summary, show_dot1x_clients, show_evpn_database) to call adapter
- [ ] T018 [US1] Write unit test for offline device error handling in `tests/unit/test_device_utils_adapter.py` — verify error message matches current implementation
- [ ] T019 [US1] Verify CSV output columns and PK strategies unchanged for all 6 EX show commands — no `ENDPOINT_PRIMARY_KEY_STRATEGIES` modifications needed

**Checkpoint**: All 6 EX show commands use device_utils. Raw API + WebSocket no longer invoked for these commands.

---

## Phase 4: User Story 1 continued — SSR/SRX Show Commands (Priority: P1)

**Goal**: Migrate 8 SSR/SRX gateway show commands to device_utils. Completes all show command migration.

**Independent Test**: Run each SSR/SRX show command against a live gateway, diff CSV output against baseline.

### Implementation

- [ ] T020 [US1] Add SSR show command entries to `_command_map` — map `("gateway", "show_route")` → `device_utils.ssr.show_route`, plus show_sessions, show_service_path, show_ospf_neighbors, show_ospf_interfaces
- [ ] T021 [P] [US1] Add SRX show command entries to `_command_map` — map `("gateway", "show_route_srx")` → `device_utils.srx.show_route`, plus show_ospf_neighbors, show_security_flow_session
- [ ] T022 [US1] Implement device type sub-routing in adapter for gateway commands — detect SSR vs SRX (based on device model/type field) and dispatch to correct submodule
- [ ] T023 [P] [US1] Write unit tests for SSR show commands in `tests/unit/test_device_utils_adapter.py`
- [ ] T024 [P] [US1] Write unit tests for SRX show commands in `tests/unit/test_device_utils_adapter.py`
- [ ] T025 [US1] Rewire all 8 SSR/SRX show command menu operations to call adapter
- [ ] T026 [US1] Verify CSV output and PK strategies unchanged for all 8 gateway show commands

**Checkpoint**: All show commands (EX + SSR + SRX) migrated. Phase 1+2 of spec complete.

---

## Phase 5: User Story 2 — Diagnostic Commands via device_utils (Priority: P2)

**Goal**: Migrate 9 diagnostic commands (ping, traceroute, DNS) across all device types.

**Independent Test**: Run ping/traceroute against known targets on each device type. Verify output format and timing match.

### Implementation for User Story 2

- [ ] T027 [US2] Add diagnostic command entries to `_command_map` — ping/traceroute for AP, EX, SSR, SRX + dns_resolution
- [ ] T028 [P] [US2] Write unit tests for ping/traceroute paths across device types in `tests/unit/test_device_utils_adapter.py`
- [ ] T029 [P] [US2] Write unit test for timeout/unreachable target handling — verify error messages match current implementation
- [ ] T030 [US2] Rewire all ping menu operations (AP, EX, SSR, SRX) to call adapter
- [ ] T031 [US2] Rewire all traceroute menu operations to call adapter
- [ ] T032 [US2] Rewire DNS lookup menu operation to call adapter
- [ ] T033 [US2] Write unit test for Ctrl+C cancellation during long-running diagnostic — verify no orphaned WebSocket connections
- [ ] T034 [US2] Verify CSV output and PK strategies unchanged for all 9 diagnostic commands

**Checkpoint**: All diagnostic commands migrated. WebSocketManager no longer invoked for ping/traceroute/DNS.

---

## Phase 6: User Story 3 — Management Commands via device_utils (Priority: P3)

**Goal**: Migrate 5 destructive management commands (bounce port, cable test, clear ARP/MAC/BGP). Confirmation flows unchanged.

**Independent Test**: Run each management command with confirmation flow. Verify prompt text identical, operation executes, result output matches.

### Implementation for User Story 3

- [ ] T035 [US3] Add management command entries to `_command_map` — bounce_port, cable_test, clear_arp, clear_mac_table, clear_bgp for EX
- [ ] T036 [P] [US3] Write unit tests for bounce_port and cable_test paths in `tests/unit/test_device_utils_adapter.py` — verify confirmation prompts are NOT bypassed by adapter
- [ ] T037 [P] [US3] Write unit tests for clear_arp, clear_mac_table, clear_bgp paths in `tests/unit/test_device_utils_adapter.py`
- [ ] T038 [US3] Rewire bounce_port and cable_test menu operations to call adapter — confirmation logic stays in calling code, adapter only handles API call
- [ ] T039 [US3] Rewire clear_arp, clear_mac_table, clear_bgp menu operations to call adapter
- [ ] T040 [US3] Write unit test for declined confirmation — verify adapter is never called when user cancels
- [ ] T041 [US3] Verify CSV output, PK strategies, and confirmation prompt text unchanged for all 5 management commands

**Checkpoint**: All device utility commands migrated. WebSocketManager retained only for packet captures and continuous monitoring.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, documentation, and deployment

- [ ] T042 [P] Add debug logging to adapter showing which path was used (device_utils vs fallback) for every `execute()` call
- [ ] T043 [P] Update README.md with device_utils requirement note (mistapi >= 0.61.0)
- [ ] T044 [P] Update CHANGELOG.md with migration entry
- [ ] T045 Remove any dead code in `WebSocketCommands` that is no longer reachable after all migrations
- [ ] T046 Run full test suite — `python -m pytest tests/unit/test_device_utils_adapter.py -v --cov=src/device/device_utils_adapter --cov-report=term-missing` — verify >= 70% coverage
- [ ] T047 Run quickstart.md validation — execute fallback verification steps from quickstart.md
- [ ] T048 Run quality gates: `python -m py_compile MistHelper.py && python -m ruff check MistHelper.py && python -m black --check MistHelper.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 EX Show (Phase 3)**: Depends on Phase 2
- **US1 SSR/SRX Show (Phase 4)**: Depends on Phase 2 (can parallel with Phase 3 if adapter is complete)
- **US2 Diagnostics (Phase 5)**: Depends on Phase 2 (independent of Phases 3-4)
- **US3 Management (Phase 6)**: Depends on Phase 2 (independent of Phases 3-5, but recommended after US1/US2 prove adapter works)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: EX show + SSR/SRX show — can start after Foundational
- **US2 (P2)**: Diagnostics — can start after Foundational, independent of US1
- **US3 (P3)**: Management — can start after Foundational, recommended after US1+US2

### Parallel Opportunities

- T003 + T004 can run in parallel (Phase 1)
- T010 + T011 can run in parallel (Phase 2)
- T014 + T015 can run in parallel (Phase 3)
- T021 + T023 + T024 can run in parallel (Phase 4)
- T028 + T029 can run in parallel (Phase 5)
- T036 + T037 can run in parallel (Phase 6)
- T042 + T043 + T044 can run in parallel (Phase 7)
- US1/US2/US3 can proceed in parallel after Phase 2 (if team capacity allows)

---

## Implementation Strategy

### MVP Scope
**Phase 1 + Phase 2 + Phase 3 (US1 EX Show Commands)** = minimum viable migration. Proves the adapter pattern works end-to-end with 6 low-risk read-only commands.

### Incremental Delivery
Each phase is independently deployable. Deploy after each checkpoint to get production feedback before migrating riskier operations.

### Rollback
Set `DEVICE_UTILS_AVAILABLE = False` to instantly revert all commands to raw API + WebSocket path. No code changes needed for rollback.
