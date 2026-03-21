# Tasks: Device Utility Commands — Complete Mist API Coverage

**Input**: Design documents from `/specs/014-device-utility-commands/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (diagnostics, show-commands, management, clear-reset, hardware), quickstart.md

**Tests**: Not explicitly requested in spec. Manual testing via `python MistHelper.py --test` and quickstart.md checklist.

**Organization**: Tasks grouped by user story. All implementation in `MistHelper.py` (monolith) and `README.md`. Each user story phase is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- All code changes target `MistHelper.py` unless stated otherwise

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create class skeleton, device type validation, and primary key strategy registration

- [X] T001 Create `DeviceUtilityCommands` class skeleton with docstring and `DEVICE_TYPE_COMPATIBILITY_MAP` constant (static dict mapping each of the 35 command names to their valid device type lists per data-model.md) in MistHelper.py
- [X] T002 Implement `_validate_device_type(device_type, command_name)` static method in `DeviceUtilityCommands` that checks device type against `DEVICE_TYPE_COMPATIBILITY_MAP` and prints clear rejection message for incompatible types (FR-034) in MistHelper.py
- [X] T003 Implement `_select_site_and_device(api_session, allowed_types)` static helper in `DeviceUtilityCommands` that wraps `PromptUtils.select_site_id_from_csv()` and `PromptUtils.select_device_id_from_inventory()`, then validates device type via `_validate_device_type()`, checks device `status` field from inventory and warns user if device is offline before proceeding (FR-035), returning `(site_id, device_id, device_type)` or None on failure, in MistHelper.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers that ALL user stories depend on — WebSocket command execution, port selection, streaming, menu wiring

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `_select_port_from_device(api_session, site_id, device_id)` static helper in `DeviceUtilityCommands` that fetches device stats to get port list, displays numbered port list with status, allows selection by number or manual port name entry (FR-041), in MistHelper.py
- [X] T005 Implement `_run_websocket_command(api_session, site_id, device_id, sdk_method, params, timeout_seconds)` static helper in `DeviceUtilityCommands` that executes the WebSocket command pattern: POST via SDK method -> get session ID -> subscribe to `/sites/{site_id}/devices/{device_id}/cmd` -> await result -> return parsed output (FR-038, 120s max timeout), in MistHelper.py
- [X] T006 Implement `_run_streaming_command(api_session, site_id, device_id, sdk_method, params, auto_timeout_seconds)` static helper in `DeviceUtilityCommands` for `monitor_traffic` and `run_top`: incremental display of WebSocket fragments, Ctrl+C (KeyboardInterrupt) handler for early exit, auto-timeout (FR-040), in MistHelper.py
- [X] T007 Add all 14 primary key strategies for show/diagnostic commands to `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (composite_pk with `['device_id', 'timestamp']` per data-model.md: traceroute, 4 OSPF, sessions, service_path, bgp_summary, arp, dhcp_leases, dot1x, evpn_database, resolve_dns, cable_test) in MistHelper.py
- [X] T008 Add all 35 menu entries (123-157) to the menu dictionary in MistHelper.py, mapping each menu number to its `DeviceUtilityCommands` static method with display name and category label per quickstart.md menu map
- [X] T009 Add interactive/destructive menu numbers to OperationRegistry: 133, 134 (streaming), 137, 139 (y/N destructive), 144-152 (CLEAR destructive) in MistHelper.py

**Checkpoint**: Foundation ready — DeviceUtilityCommands class has all helpers, menu wiring, PK strategies. User story implementation can begin.

---

## Phase 3: User Story 1 — Run Traceroute from a Device (Priority: P1) MVP

**Goal**: NOC engineer runs traceroute from any device (AP/switch/gateway) to see hop-by-hop path to a destination.

**Independent Test**: Select any device, enter destination `8.8.8.8`, confirm hop-by-hop output with RTT values. Also test with invalid input (empty destination) to verify rejection.

### Implementation for User Story 1

- [X] T010 [US1] Implement `traceroute(api_session)` static method (menu 120) in `DeviceUtilityCommands`: select site/device (any type), prompt for destination host (required, validated non-empty and hostname/IP format), optional protocol (udp/icmp), call `tracerouteSiteDevice()` via `_run_websocket_command()`, display hop-by-hop output, write to dual output via `DataExporter.write_with_format_selection()`, in MistHelper.py

**Checkpoint**: Menu 120 functional. Verify: `python MistHelper.py --menu 120` with a connected device and destination `8.8.8.8`.

---

## Phase 4: User Story 2 — OSPF Troubleshooting on SSR/SRX Gateways (Priority: P1)

**Goal**: Network engineer inspects OSPF state (neighbors, interfaces, database, summary) on SSR/SRX gateways through dedicated menu options.

**Independent Test**: Select any SSR/SRX gateway running OSPF, run each of the four OSPF commands, confirm structured output. Test with non-gateway device to verify rejection message.

### Implementation for User Story 2

- [X] T011 [US2] Implement `show_ospf_neighbors(api_session)` and `show_ospf_interfaces(api_session)` static methods (menus 121-122) in `DeviceUtilityCommands`: select site/gateway (SSR/SRX only), prompt for optional VRF, node, and command-specific filters (neighbor IP for neighbors, port_id for interfaces), call SDK via `_run_websocket_command()`, display structured table, write to dual output, in MistHelper.py
- [X] T012 [US2] Implement `show_ospf_database(api_session)` and `show_ospf_summary(api_session)` static methods (menus 123-124) in `DeviceUtilityCommands`: select site/gateway (SSR/SRX only), prompt for optional VRF, node, self_originate (database only), call SDK via `_run_websocket_command()`, display structured table, write to dual output, in MistHelper.py

**Checkpoint**: Menus 121-124 functional. Verify: `python MistHelper.py --menu 121` on an SSR/SRX with OSPF configured.

---

## Phase 5: User Story 3 — SSR Session and Service Path Inspection (Priority: P1)

**Goal**: Network engineer inspects active sessions and service paths on SSR gateways for traffic flow troubleshooting.

**Independent Test**: Select SSR gateway with active traffic, run show sessions (with and without filters), confirm session data. Run show service path, confirm path information.

### Implementation for User Story 3

- [X] T013 [US3] Implement `show_session(api_session)` static method (menu 125) in `DeviceUtilityCommands`: select site/gateway (SSR/SRX only), prompt for optional filters per FR-042 (service name, session ID, node — Enter to skip each), call `showSiteDeviceSessions()` via `_run_websocket_command()`, display session table, write to dual output, in MistHelper.py
- [X] T014 [US3] Implement `show_service_path(api_session)` static method (menu 126) in `DeviceUtilityCommands`: select site/gateway (SSR only), prompt for optional service name and node, call `showSiteDeviceServicePath()` via `_run_websocket_command()`, display path table (service, route, type, destination, next-hop, interface, vector, cost, rate, capacity, state), write to dual output, in MistHelper.py

**Checkpoint**: Menus 125-126 functional. Verify: `python MistHelper.py --menu 125` on an SSR with active sessions.

---

## Phase 6: User Story 4 — Structured Show Commands (Priority: P2)

**Goal**: NOC engineer accesses common device state tables (BGP summary, ARP, DHCP, 802.1X, EVPN) via dedicated menu options without opening a shell session.

**Independent Test**: Each command tested independently on appropriate device type. BGP on SSR/SRX/switch, ARP on switch/gateway, DHCP on switch/gateway, 802.1X on switch, EVPN on switch/gateway.

### Implementation for User Story 4

- [X] T015 [US4] Implement `show_bgp_summary(api_session)` (menu 130), `show_arp_table(api_session)` (menu 131), and `show_dhcp_leases(api_session)` (menu 132) static methods in `DeviceUtilityCommands`: each selects site/device with appropriate type validation, prompts for optional node (HA), calls respective SDK method via `_run_websocket_command()`, displays structured table, writes to dual output, in MistHelper.py
- [X] T016 [US4] Implement `show_dot1x(api_session)` (menu 133) and `show_evpn_database(api_session)` (menu 134) static methods in `DeviceUtilityCommands`: select site/device with type validation (dot1x=switch only, evpn=switch/gateway), prompt for optional node, call SDK via `_run_websocket_command()`, display structured table, write to dual output, in MistHelper.py

**Checkpoint**: Menus 127-131 functional. Verify: `python MistHelper.py --menu 128` on a switch to see ARP table.

---

## Phase 7: User Story 5 — DNS Resolution Test and Device Monitoring (Priority: P2)

**Goal**: Network engineer tests DNS resolution from SSR, monitors live traffic on switch/SRX ports, and checks resource utilization via top command.

**Independent Test**: DNS tested by resolving known hostname from SSR. Monitor traffic tested on switch with active port. Top tested on any switch/SRX.

### Implementation for User Story 5

- [X] T017 [US5] Implement `resolve_dns(api_session)` static method (menu 135) in `DeviceUtilityCommands`: select site/gateway (SSR only), prompt for hostname (required, validated non-empty), call `resolveSiteDeviceDns()` via `_run_websocket_command()`, display resolution results, write to dual output, in MistHelper.py
- [X] T018 [US5] Implement `monitor_traffic(api_session)` (menu 136) and `run_top(api_session)` (menu 137) streaming static methods in `DeviceUtilityCommands`: select site/device (switch/SRX), for monitor_traffic use `_select_port_from_device()` (FR-041), call respective SDK method via `_run_streaming_command()` with Ctrl+C and auto-timeout support (FR-040), console-only output (no CSV/SQLite), in MistHelper.py

**Checkpoint**: Menus 132-134 functional. Verify: `python MistHelper.py --menu 132` on an SSR to resolve `google.com`.

---

## Phase 8: User Story 6 — Locate and Unlocate Devices (Priority: P2)

**Goal**: Field technician physically identifies a device by blinking its LED and stops the blinking when found.

**Independent Test**: Select any AP or switch, run locate to start LED blink, run unlocate to stop. Verify gateway rejection message.

### Implementation for User Story 6

- [X] T019 [US6] Implement `locate_device(api_session)` (menu 138) and `unlocate_device(api_session)` (menu 139) static methods in `DeviceUtilityCommands`: select site/device (AP/switch only, reject gateways), for locate prompt for duration (1-120 minutes, default 5), call `startSiteLocateDevice()` / `stopSiteLocateDevice()` (synchronous, no WebSocket), display confirmation message, no CSV/SQLite output, in MistHelper.py

**Checkpoint**: Menus 135-136 functional. Verify: `python MistHelper.py --menu 135` on an AP.

---

## Phase 9: User Story 7 — Port Bounce and Cable Test (Priority: P2)

**Goal**: NOC engineer bounces a switch port to clear connectivity issues or runs cable test for physical-layer diagnostics.

**Independent Test**: Port bounce on any switch port (with y/N confirmation). Cable test on any switch port with cable connected.

### Implementation for User Story 7

- [X] T020 [US7] Implement `bounce_port(api_session)` (menu 140) static method in `DeviceUtilityCommands`: select site/device (switch/gateway), use `_select_port_from_device()` for port selection (FR-041), validate port name (reject vme/ae/irb prefixes), y/N confirmation via `safe_input()` (FR-036), call `bounceDevicePort()` via `_run_websocket_command()`, display result, in MistHelper.py
- [X] T021 [US7] Implement `cable_test(api_session)` (menu 141) static method in `DeviceUtilityCommands`: select site/switch, use `_select_port_from_device()` for port selection, call `cableTestFromSwitch()` via `_run_websocket_command()`, display cable test results (pair status, length, fault distance), write to dual output, in MistHelper.py

**Checkpoint**: Menus 137-138 functional. Verify: `python MistHelper.py --menu 138` on a switch port.

---

## Phase 10: User Story 8 — Clear/Reset Operations (Priority: P3)

**Goal**: Network engineer clears stale state from devices (ARP cache, BGP routes, sessions, MAC tables, BPDU errors, policy hit counts) to recover from incorrect cached state.

**Independent Test**: Each clear operation tested independently with 'CLEAR' confirmation. Verify cancellation when user does not type 'CLEAR'.

### Implementation for User Story 8

- [X] T022 [US8] Implement `clear_arp_cache(api_session)` (menu 147), `clear_bgp_routes(api_session)` (menu 148), `clear_session(api_session)` (menu 149), and `clear_mac_table(api_session)` (menu 150) static methods in `DeviceUtilityCommands`: each selects site/device with type validation, prompts for command-specific optional params (IP/port_id/vlan for ARP, neighbor/type/vrf for BGP, session_id for session, node for all), typed 'CLEAR' confirmation via `safe_input()`, calls respective SDK method, displays confirmation, no CSV/SQLite output, in MistHelper.py
- [X] T023 [US8] Implement `clear_bpdu_error(api_session)` (menu 151), `clear_learned_macs(api_session)` (menu 152), and `clear_policy_hit_count(api_session)` (menu 153) static methods in `DeviceUtilityCommands`: bpdu_error selects switch with optional port_id, clear_macs uses `_select_port_from_device()` (FR-041) with required port_id, policy_hit_count selects gateway (SSR) with optional node, all require typed 'CLEAR' confirmation, call SDK, display confirmation, no CSV/SQLite, in MistHelper.py

**Checkpoint**: Menus 144-150 functional. Verify: attempt `python MistHelper.py --menu 144`, type something other than 'CLEAR' to confirm cancellation works.

---

## Phase 11: User Story 9 — DHCP Lease Release (Priority: P3)

**Goal**: Network engineer releases active DHCP leases to force renewal, resolving IP addressing conflicts.

**Independent Test**: Release a lease on a switch/gateway and confirm release. Test SSR-specific variant on SSR/SRX.

### Implementation for User Story 9

- [X] T024 [US9] Implement `release_dhcp_lease(api_session)` (menu 154) and `release_dhcp_ssr(api_session)` (menu 155) static methods in `DeviceUtilityCommands`: general release selects switch/gateway with required port_id and optional node, SSR release selects SSR/SRX with required port_id and optional node, both use y/N confirmation via `safe_input()`, call `releaseSiteDeviceDhcpLease()` / `releaseSiteSsrDhcpLease()`, display confirmation, no CSV/SQLite, in MistHelper.py

**Checkpoint**: Menus 151-152 functional.

---

## Phase 12: User Story 10 — Device Management Operations (Priority: P3)

**Goal**: Network engineer performs device management tasks: reprovision, re-adopt, ZTP password, config CLI commands, support file upload.

**Independent Test**: Each operation tested independently on appropriate device type. Reprovision requires y/N confirmation.

### Implementation for User Story 10

- [X] T025 [US10] Implement `reprovision_device(api_session)` (menu 142) with y/N confirmation, `readopt_device(api_session)` (menu 140) no confirmation, and `get_ztp_password(api_session)` (menu 141) with console-only display (no logging of password, FR security) static methods in `DeviceUtilityCommands` in MistHelper.py
- [X] T026 [US10] Implement `get_config_commands(api_session)` (menu 145) for switch brown-field adoption CLI commands and `upload_support_file(api_session)` (menu 143) with support file type selection (full/process/outbound-ssh/messages/core-dumps/var-logs/jma-logs) static methods in `DeviceUtilityCommands` in MistHelper.py

**Checkpoint**: Menus 139-143 functional. Verify: `python MistHelper.py --menu 141` on a switch to get ZTP password.

---

## Phase 13: User Story 11 — Switch Hardware Operations (Priority: P3)

**Goal**: Network engineer polls fresh switch statistics and creates device snapshots.

**Independent Test**: Poll stats on any switch. Create snapshot on any switch.

### Implementation for User Story 11

- [X] T027 [US11] Implement `poll_switch_stats(api_session)` (menu 156) and `create_device_snapshot(api_session)` (menu 157) static methods in `DeviceUtilityCommands`: each selects site/switch, calls `pollSiteSwitchStats()` / `createSiteDeviceSnapshot()` (synchronous, no WebSocket), displays confirmation message, no CSV/SQLite, in MistHelper.py

**Checkpoint**: Menus 153-154 functional. Verify: `python MistHelper.py --menu 153` on a switch.

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, syntax validation, and deployment readiness

- [X] T028 [P] Update README.md: increment total operation count by 35, add menu table entries for 123-157 with command names, categories, and device type info per quickstart.md menu map
- [X] T029 [P] Add version changelog entry to README.md (version 26.03.20.22.31) in format `version YY.MM.DD.HH.MM - Add 35 device utility commands (menus 120-154): traceroute, OSPF, sessions, show commands, locate, port bounce, cable test, clear/reset, DHCP release, device management, hardware ops`
- [X] T030 Run `python -m py_compile MistHelper.py` -- PASSED (no errors) to validate syntax — fix any errors before proceeding
- [X] T031 Run `python MistHelper.py --test` -- PASSED (48/48 safe ops, 0 failures, 110 skipped) to validate all non-interactive operations pass with new menu entries

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) — BLOCKS all user stories
- **User Stories (Phase 3-13)**: All depend on Foundational phase (T004-T009) completion
  - User stories can proceed sequentially in priority order (P1 -> P2 -> P3)
  - Within same priority level, stories are independent
- **Polish (Phase 14)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 Traceroute (P1)**: Can start after Foundational — no dependencies on other stories
- **US2 OSPF (P1)**: Can start after Foundational — no dependencies on other stories
- **US3 SSR Sessions (P1)**: Can start after Foundational — no dependencies on other stories
- **US4 Show Commands (P2)**: Can start after Foundational — no dependencies on other stories
- **US5 DNS/Monitor/Top (P2)**: Can start after Foundational — `monitor_traffic` depends on `_select_port_from_device()` (T004) and `_run_streaming_command()` (T006)
- **US6 Locate/Unlocate (P2)**: Can start after Foundational — simplest implementation (synchronous HTTP, no WebSocket)
- **US7 Port Bounce/Cable Test (P2)**: Can start after Foundational — depends on `_select_port_from_device()` (T004)
- **US8 Clear/Reset (P3)**: Can start after Foundational — clear_macs depends on `_select_port_from_device()` (T004)
- **US9 DHCP Release (P3)**: Can start after Foundational — no dependencies on other stories
- **US10 Device Management (P3)**: Can start after Foundational — no dependencies on other stories
- **US11 Hardware (P3)**: Can start after Foundational — simplest P3 story (synchronous HTTP)

### Within Each User Story

- Commands within a story that share the same device type validation and helper pattern can be implemented together
- All commands must use `safe_input()` for any user input (FR cross-cutting)
- All show/diagnostic commands must write to dual output (FR-039)
- All destructive commands must have appropriate confirmation gates (FR-036)

### Parallel Opportunities

Since all implementation is in `MistHelper.py` (monolith), true parallel execution is limited to:
- **T003 (PK strategies)** can run parallel with T001-T002 (different code location in file)
- **T028-T029 (README)** can run parallel with any MistHelper.py task (different file)
- Within the same priority level, user stories are independent and could be serialized in any order

---

## Parallel Example: P1 User Stories (After Foundational Complete)

```text
# Sequential execution (recommended for monolith):
T010 [US1] Traceroute implementation
T011-T012 [US2] OSPF implementation (4 commands)
T013-T014 [US3] SSR session/service path implementation

# README can be done in parallel with any code task:
T028-T029 [P] README updates
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009)
3. Complete Phase 3: User Story 1 — Traceroute (T010)
4. **STOP and VALIDATE**: `python MistHelper.py --menu 120` with a connected device
5. If working: commit and continue to US2-US3

### Incremental Delivery

1. Setup + Foundational -> Class skeleton and menu wiring ready
2. Add US1 (Traceroute) -> Test independently -> First working command (MVP)
3. Add US2 (OSPF) + US3 (Sessions) -> Test -> Complete P1 coverage
4. Add US4-US7 -> Test -> Complete P2 coverage (show commands + management)
5. Add US8-US11 -> Test -> Complete P3 coverage (clear/reset + hardware)
6. Polish -> README + syntax check + full test run -> Ready for deployment

### Deployment (After All Stories Complete)

```powershell
python -m py_compile MistHelper.py        # T030: Syntax validation
python MistHelper.py --test               # T031: Automated test run
git add MistHelper.py README.md
git commit -m "version YY.MM.DD.HH.MM - Add 35 device utility commands (menus 120-154)"
git push origin main
```

---

## Notes

- All 35 commands are in the `DeviceUtilityCommands` class as static methods
- WebSocket commands (22 of 35) use `_run_websocket_command()` helper
- Streaming commands (2 of 35) use `_run_streaming_command()` helper
- Synchronous commands (13 of 35) call SDK directly with no WebSocket
- Confirmation tiers: none (read-only), y/N (port bounce, reprovision, DHCP release), typed 'CLEAR' (all clear/reset ops)
- Port selection helper used by: bounce_port, cable_test, clear_macs, monitor_traffic
- Test skip list additions: 133, 134 (streaming), 137, 139 (y/N destructive), 144-152 (CLEAR destructive)
- Each user story checkpoint includes a specific `--menu N` command to run for validation
