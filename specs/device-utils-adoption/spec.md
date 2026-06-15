# Feature Specification: Adopt mistapi.device_utils for Device Operations

**Feature Branch**: `device-utils-adoption`
**Created**: 2026-06-11
**Status**: Draft
**Input**: User description: "Replace raw mistapi.api.v1.sites.devices.utilities.* calls with mistapi.device_utils helpers, leveraging UtilResponse for automatic WebSocket result collection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Show Commands Return Same Output via device_utils (Priority: P1)

A NOC engineer runs a show command (e.g., show ARP, show routes, show BGP summary) from MistHelper's menu. The engineer sees identical prompts, identical output formatting, and identical CSV/SQLite data — they should not notice any change. Under the hood, the call now uses `mistapi.device_utils.ex.show_arp()` (or equivalent) instead of raw `mistapi.api.v1.sites.devices.utilities.*` with custom WebSocket polling.

**Why this priority**: Show commands are the most frequently used device utility operations (menu ops 102-123). They are read-only and safe to migrate first. Proving behavioral equivalence here builds confidence for all subsequent migrations.

**Independent Test**: Run each migrated show command against a live device. Compare CSV output columns, row count, and key values against the current implementation. Diff must be empty.

**Acceptance Scenarios**:

1. **Given** a connected EX switch, **When** user selects "show ARP table" (or any migrated show command), **Then** output displays the same columns, formatting, and data as the current raw-API implementation
2. **Given** a connected SSR/SRX gateway, **When** user runs "show routes" or "show OSPF neighbors", **Then** output is identical to current implementation
3. **Given** a device that is offline or unreachable, **When** user runs any show command, **Then** error handling produces the same user-facing messages as today
4. **Given** any migrated operation, **When** output is saved to CSV or SQLite, **Then** column names, data types, and row structure match the current format exactly

---

### User Story 2 — Diagnostic Commands Use device_utils (Priority: P2)

A NOC engineer runs a diagnostic command (ping, traceroute, DNS lookup) from MistHelper. The device_utils helper handles WebSocket polling automatically via `UtilResponse`, eliminating the need for MistHelper's custom `WebSocketManager` polling loops for these operations.

**Why this priority**: Diagnostic commands (ping, traceroute) are the second most common device utility operations. They involve more complex result streaming than show commands, making them a good test of UtilResponse's automatic polling.

**Independent Test**: Run ping/traceroute against known targets. Verify hop-by-hop output appears with same timing and format as current implementation.

**Acceptance Scenarios**:

1. **Given** any connected device, **When** user runs ping via the migrated code path, **Then** results appear with the same per-packet output format as the current implementation
2. **Given** any connected device, **When** user runs traceroute via the migrated code path, **Then** hop-by-hop results appear identically to today
3. **Given** a timeout or unreachable target, **When** user runs a diagnostic command, **Then** the timeout behavior and error messages are identical to today
4. **Given** user presses Ctrl+C during a long-running diagnostic, **Then** cancellation works cleanly without orphaned WebSocket connections

---

### User Story 3 — Device Management Commands Use device_utils (Priority: P3)

A NOC engineer runs a device management command (bounce port, clear MAC table, clear ARP, cable test) from MistHelper. These are write/action operations that modify device state, so they require the same destructive-operation confirmation flow as today.

**Why this priority**: Management commands are less frequent than show/diagnostic commands and have destructive potential. They should be migrated last, after show and diagnostic commands prove the device_utils integration is solid.

**Independent Test**: Run each management command with confirmation flow. Verify the confirmation prompt text is identical, the operation executes, and the result output matches.

**Acceptance Scenarios**:

1. **Given** an EX switch, **When** user selects "bounce port" and confirms, **Then** the confirmation prompt, execution, and result output are identical to today
2. **Given** an EX switch, **When** user selects "cable test" and confirms, **Then** cable test results display with the same format as today
3. **Given** any management command, **When** user declines the confirmation prompt, **Then** the operation is cancelled with the same cancellation message as today

---

### Edge Cases

- What happens when device_utils returns a different response structure than the raw API? Migration code must normalize to the current output schema.
- How does UtilResponse handle API rate limiting (429)? Must behave identically to MistHelper's existing adaptive delay system.
- What happens when mistapi < 0.61.0 is installed? The migration must fail gracefully with a clear version requirement message.
- What happens when a device_utils function doesn't exist for a specific device type + command combination? Fall back to the raw API call.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace raw `mistapi.api.v1.sites.devices.utilities.*` calls with equivalent `mistapi.device_utils.*` functions for all migrated menu operations
- **FR-002**: System MUST produce identical user-facing prompts (same wording, same order) for all migrated operations
- **FR-003**: System MUST produce identical CSV/SQLite output (same column names, same data types, same row structure) for all migrated operations
- **FR-004**: System MUST use `UtilResponse` automatic WebSocket handling instead of custom `WebSocketManager` polling for migrated operations
- **FR-005**: System MUST validate that mistapi >= 0.61.0 is installed at startup and display a clear error if device_utils is unavailable
- **FR-006**: System MUST preserve all existing error handling behavior (timeouts, offline devices, permission errors) for migrated operations
- **FR-007**: System MUST migrate operations in phases (Phase 1: EX show commands, Phase 2: SSR/SRX show commands, Phase 3: diagnostics, Phase 4: management commands)
- **FR-008**: System MUST preserve existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for all migrated operations — no PK strategy changes unless the endpoint name changes
- **FR-009**: System MUST fall back to raw API calls for any device type + command combination not covered by device_utils
- **FR-010**: System MUST not change the custom `WebSocketManager` for non-migrated operations (packet captures, continuous monitoring)

### Migration Mapping

Operations to migrate, grouped by phase:

**Phase 1 — EX Switch Show Commands (lowest risk)**:

| Menu Op | Current Call | device_utils Replacement |
| - | - | - |
| Show ARP | raw utilities POST | `device_utils.ex.show_arp()` |
| Show MAC table | raw utilities POST | `device_utils.ex.show_mac_table()` |
| Show DHCP leases | raw utilities POST | `device_utils.ex.show_dhcp_leases()` |
| Show BGP summary | raw utilities POST | `device_utils.ex.show_route_summary()` |
| Show 802.1X | raw utilities POST | `device_utils.ex.show_dot1x_clients()` |
| Show EVPN DB | raw utilities POST | `device_utils.ex.show_evpn_database()` |

**Phase 2 — SSR/SRX Show Commands**:

| Menu Op | Current Call | device_utils Replacement |
| - | - | - |
| Show routes (SSR) | raw utilities POST | `device_utils.ssr.show_route()` |
| Show sessions (SSR) | raw utilities POST | `device_utils.ssr.show_sessions()` |
| Show service path (SSR) | raw utilities POST | `device_utils.ssr.show_service_path()` |
| Show OSPF neighbors (SSR) | raw utilities POST | `device_utils.ssr.show_ospf_neighbors()` |
| Show OSPF interfaces (SSR) | raw utilities POST | `device_utils.ssr.show_ospf_interfaces()` |
| Show routes (SRX) | raw utilities POST | `device_utils.srx.show_route()` |
| Show OSPF neighbors (SRX) | raw utilities POST | `device_utils.srx.show_ospf_neighbors()` |
| Show sessions (SRX) | raw utilities POST | `device_utils.srx.show_security_flow_session()` |

**Phase 3 — Diagnostic Commands (all device types)**:

| Menu Op | Current Call | device_utils Replacement |
| - | - | - |
| Ping (AP) | raw utilities POST | `device_utils.ap.ping()` |
| Traceroute (AP) | raw utilities POST | `device_utils.ap.traceroute()` |
| Ping (EX) | raw utilities POST | `device_utils.ex.ping()` |
| Traceroute (EX) | raw utilities POST | `device_utils.ex.traceroute()` |
| Ping (SSR) | raw utilities POST | `device_utils.ssr.ping()` |
| Traceroute (SSR) | raw utilities POST | `device_utils.ssr.traceroute()` |
| Ping (SRX) | raw utilities POST | `device_utils.srx.ping()` |
| Traceroute (SRX) | raw utilities POST | `device_utils.srx.traceroute()` |
| DNS lookup | raw utilities POST | `device_utils.*.dns_resolution()` |

**Phase 4 — Management Commands (destructive, requires confirmation)**:

| Menu Op | Current Call | device_utils Replacement |
| - | - | - |
| Bounce port (EX) | raw utilities POST | `device_utils.ex.bounce_port()` |
| Cable test (EX) | raw utilities POST | `device_utils.ex.cable_test()` |
| Clear ARP (EX) | raw utilities POST | `device_utils.ex.clear_arp()` |
| Clear MAC table (EX) | raw utilities POST | `device_utils.ex.clear_mac_table()` |
| Clear BGP (EX) | raw utilities POST | `device_utils.ex.clear_bgp()` |

### Key Entities

- **UtilResponse**: SDK-provided response object that encapsulates the API call result and automatic WebSocket polling. Replaces MistHelper's manual `WebSocketManager.subscribe_to_channel()` + polling loop for device utility commands.
- **WebSocketManager**: Existing MistHelper class (~200 lines at line 2335) that manages WebSocket connections. After full migration, this class would only be needed for packet captures and continuous monitoring — not for device utility commands.
- **Device Type Router**: Logic that maps device type (AP/EX/SSR/SRX) to the correct `device_utils` submodule. Must match the existing device type detection used by the current raw API calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All migrated operations produce byte-identical CSV output when run against the same device and compared to pre-migration output
- **SC-002**: User-facing prompts and messages are unchanged — a NOC engineer cannot distinguish pre- and post-migration behavior
- **SC-003**: Custom WebSocket polling code is no longer invoked for any migrated operation (verified via debug logging)
- **SC-004**: Each migration phase can be deployed independently without breaking unmigrated operations
- **SC-005**: Test suite includes mock `UtilResponse` objects for each migrated operation with >= 70% coverage of migration code
- **SC-006**: No new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries required unless the API endpoint name changes in device_utils

## Assumptions

- mistapi SDK v0.61.0+ is available and stable (device_utils module exists with documented API)
- `UtilResponse` objects provide the same data fields as the current raw API responses, potentially in a different structure that needs normalization
- The device_utils functions are truly non-blocking and handle WebSocket internally — no additional polling code is needed in MistHelper
- Packet captures (menu ops 134-135) and continuous monitoring (menu ops 151-152) are out of scope — they will continue using the custom WebSocketManager
- The existing `src/websocket/` module will not be deleted in this spec — it will be reduced in scope but retained for non-device-utility operations
- Phase boundaries are firm: each phase must be completed, tested, and deployed before the next phase begins
- device_utils function signatures and return types are stable across minor SDK versions (0.61.x)
