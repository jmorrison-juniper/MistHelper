# Feature Specification: Audit Menu #7 — Show Routing Table via WebSocket

**Feature Branch**: `094-audit-menu-7-show-routing-table-via`
**Created**: 2025-07-24
**Status**: Audit
**Category**: WebSocket (interactive, not a data export)
**SQL Export Relevant**: No

## Current State Analysis

Menu #7 ("Show routing table on switches via WebSocket") is implemented as a two-class pipeline:

- **Entry point**: `WebSocketCommands.show_routing_table()` — a static method that delegates to `RoutingUtils.execute_show_routing_table()`.
- **Orchestrator**: `RoutingUtils.execute_show_routing_table()` runs a 5-step pipeline:
  1. **Site & device selection** (`_select_routing_table_device`) — prompts the user to choose a site via `PromptUtils.select_site_id_from_csv()` and a switch device via `PromptUtils.select_device_id_from_inventory(site_id, device_type="switch")`. Retrieves device info for compatibility guidance.
  2. **WebSocket connection** (`_connect_websocket`) — creates a `WebSocketManager`, calls `connect()`, subscribes to `/sites/{site_id}/devices/{device_id}/cmd`, and waits 1 second for subscription confirmation.
  3. **Parameter collection** (`_get_routing_table_params`) — prompts for optional query filters: prefix, protocol (bgp/ospf/static/direct/evpn/any), VRF, BGP neighbor, route direction (received/advertised), and HA node (node0/node1).
  4. **Command execution** (`_execute_routing_table_command`) — HTTP POST to `https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_route` with the filter payload. Extracts a `session` ID from the response.
  5. **Result processing** (`_process_routing_table_results`) — calls `websocket_manager.wait_for_command_result(session_id, timeout_seconds=60)`, then parses and displays results via `_display_routing_table_output`.

- **Output pipeline**: `_display_routing_table_output` reads the `raw` and `Output` fields from the WebSocket result, parses them through `_parse_routing_table` (which handles Juniper, standard Linux-style, protocol-keyword, JSON, and tabular formats), then displays a summary via `_display_routing_summary` (protocol counts, unique destinations/next-hops/interfaces, active route count) and a detailed table via `_display_routing_details`.

- **Error handling**: The orchestrator wraps the full pipeline in try/except/finally. `KeyboardInterrupt` prints an interruption notice. General exceptions call `_handle_routing_error` (prints message, logs error, prints traceback in debug mode). The finally block always calls `_cleanup_websocket` to close the connection.

- **WebSocket infrastructure**: Uses `websocket-client` library via `WebSocketManager`. Connection runs on a background daemon thread. Result polling uses 0.1s check intervals with activity-timeout (2s inactivity), global timeout (60s), and an emergency circuit breaker (10,000 checks). Session-based demultiplexing stores results in `command_results[session_id]` behind a thread lock.

- **Menu registration**: Defined in `web_portal/menu_registry.py` as key `"7": "Show routing table on switches via WebSocket"`.

## Issues Found

1. **No test coverage**: No unit tests, integration tests, or mock-based tests exist for `WebSocketCommands.show_routing_table`, `RoutingUtils.execute_show_routing_table`, or any of its helper methods (`_select_routing_table_device`, `_connect_websocket`, `_get_routing_table_params`, `_execute_routing_table_command`, `_process_routing_table_results`, `_parse_routing_table`, `_display_routing_summary`). This is the most critical gap.

2. **No input validation on user-entered prefix**: `_get_routing_table_params` accepts any string for the prefix field and passes it directly to the API. No validation confirms the input is a valid IP prefix (e.g., CIDR notation). Invalid values may produce confusing API errors.

3. **Protocol filter silently defaults**: If the user enters an unrecognized protocol string (e.g., "isis", "rip"), the code silently falls through to `payload["protocol"] = "any"` without notifying the user that their input was ignored.

4. **Device type hardcoded to "switch"**: `_select_routing_table_device` calls `select_device_id_from_inventory(site_id, device_type="switch")` and `_get_device_info(site_id, device_id, "switch", debug_mode)`. The docstring claims support for SRX routers and SSR gateways, but the device selection filter excludes non-switch devices from the inventory list. Users see guidance text ("For SSR/SRX devices, use Menu Option 8") but may not understand why their gateway device is missing.

5. **Hardcoded 1-second subscription wait**: After subscribing to the WebSocket channel, the code uses `time.sleep(1)` as a fixed wait. On slow networks or under load, the subscription may not be confirmed in time, leading to missed messages.

6. **No subscription confirmation validation**: The code subscribes and waits 1 second but does not verify the subscription was actually confirmed (via the `confirmed_subscriptions` set) before proceeding to send the command. A race condition could cause commands to be sent before the subscription is active.

7. **Silent failure on missing session ID**: If the API POST response does not contain a `session` field, the code returns `None` and the orchestrator disconnects without explaining why. The user only sees the WebSocket cleanup message.

8. **Result fields inconsistency**: `_display_routing_table_output` checks both `result.get("raw")` and `result.get("Output")` but the relationship between these fields is undocumented. If both are empty, the user sees "No routing table data received" with no troubleshooting guidance beyond listing result keys.

9. **Parse fallback chain lacks coverage**: `_parse_routing_table` has four fallback parsing patterns (standard route lines, protocol keywords, JSON, tabular). The tabular pattern (`len(line.split()) >= 3`) is very permissive and could match non-route lines, potentially producing garbage entries in the output.

10. **WebSocket connection leak on subscription failure**: In `_connect_websocket`, if `subscribe_to_channel` fails after the connection succeeds, the method returns `None`. The orchestrator checks `if not websocket_manager: return` and never calls cleanup, leaving the connection open.

## SQL Export Compliance

Not applicable. This is an interactive WebSocket command that displays output in the terminal. No data is exported to CSV or SQLite files. No `DataExporter` or `write_with_format_selection` flow is involved.

## Test Coverage

- **Existing tests**: None. No test file targets `show_routing_table`, `RoutingUtils`, `WebSocketManager`, or Menu #7.
- **Related test patterns**: Other menu items have unit tests (e.g., `tests/test_clear_session.py`, `tests/test_clear_bpdu_error.py`) that use monkeypatching of API calls and user input. The same pattern should apply here.
- **Critical test gaps**:
  - Routing table parsing logic (`_parse_routing_table`) for each format variant (Juniper, standard, protocol, JSON, tabular)
  - Parameter collection with various input combinations
  - WebSocket result processing with timeout, empty, and multi-segment results
  - Error paths (connection failure, subscription failure, API error, missing session ID)
  - Summary display formatting with edge cases (zero routes, single route, mixed protocols)

## User Scenarios & Testing

### User Story 1 — Query Routing Table on a Switch (Priority: P1)

A network operator selects Menu #7 to view the routing table of a specific switch. They choose a site and device, optionally filter by protocol or prefix, and receive a formatted display of routes grouped by protocol with summary statistics.

**Why this priority**: This is the core function of the menu item. If this does not work reliably, the entire feature is broken.

**Independent Test**: Can be tested by mocking the API session, site/device selection, API POST, and WebSocket result, then verifying the output pipeline produces correct formatted output.

**Acceptance Scenarios**:

1. **Given** a valid site and switch device, **When** the user runs Menu #7 with no filters, **Then** the system displays all routing table entries grouped by protocol with summary statistics (total entries, unique destinations, unique next-hops, unique interfaces).
2. **Given** a valid site and switch device, **When** the user filters by protocol "bgp", **Then** only BGP routes appear in the output.
3. **Given** a valid site and switch device, **When** the user enters a specific prefix "10.0.0.0/8", **Then** only routes matching that prefix appear.

---

### User Story 2 — Graceful Handling of Errors and Timeouts (Priority: P1)

When the WebSocket connection fails, the device is unreachable, or the command times out, the operator receives clear, actionable feedback rather than cryptic errors or silent failures.

**Why this priority**: Error visibility is equally critical as the happy path — operators depend on clear diagnostics to troubleshoot network issues.

**Independent Test**: Can be tested by mocking connection failures, API errors, and timeout conditions, then verifying appropriate user-facing messages appear.

**Acceptance Scenarios**:

1. **Given** a device that does not respond within 60 seconds, **When** the timeout expires, **Then** the system displays a timeout message with possible causes and the WebSocket connection is cleaned up.
2. **Given** an API POST that returns an error status code, **When** the command execution step fails, **Then** the system displays the error status and response body to the user.
3. **Given** a WebSocket connection that fails to establish, **When** the connection step fails, **Then** the system informs the user and does not attempt to send commands.
4. **Given** the user presses Ctrl+C at any point, **When** the interrupt is received, **Then** the system prints an interruption notice and cleanly disconnects.

---

### User Story 3 — Automated Test Coverage (Priority: P2)

A developer adding or modifying routing table functionality can run automated tests that validate parsing logic, parameter handling, error paths, and output formatting without requiring a live Mist environment.

**Why this priority**: Test coverage prevents regressions and enables safe refactoring. Without tests, every change to the routing pipeline is high-risk.

**Independent Test**: Can be tested by running the test suite and verifying all routing-table-related tests pass with full branch coverage of parsing and error paths.

**Acceptance Scenarios**:

1. **Given** sample Juniper-format routing table output, **When** the parsing test runs, **Then** the parser produces correctly structured route entries with destination, next-hop, protocol, interface, and active flag.
2. **Given** sample generic-format routing table output, **When** the parsing test runs, **Then** the parser correctly handles standard, protocol-keyword, JSON, and tabular formats.
3. **Given** empty or malformed routing output, **When** the parsing test runs, **Then** the parser returns an empty list without raising exceptions.

---

### User Story 4 — Input Validation and User Feedback (Priority: P3)

When the operator enters invalid filter parameters (malformed prefix, unrecognized protocol), the system provides immediate feedback and allows correction rather than silently ignoring input or sending invalid requests to the API.

**Why this priority**: Improves user experience and prevents confusion, but the feature is functional without it.

**Independent Test**: Can be tested by providing invalid inputs to the parameter collection function and verifying appropriate validation messages.

**Acceptance Scenarios**:

1. **Given** the user enters an invalid prefix (e.g., "not-an-ip"), **When** the parameter collection step processes the input, **Then** the system warns the user and prompts for correction or confirmation.
2. **Given** the user enters an unrecognized protocol (e.g., "isis"), **When** the parameter collection step processes the input, **Then** the system notifies the user it will default to "any" rather than silently ignoring the input.

---

### Edge Cases

- What happens when the device returns an empty routing table (no routes configured)?
- What happens when the WebSocket receives multiple message segments for a large routing table?
- What happens when the API returns a 200 response but no `session` field in the body?
- What happens when the device returns routing output in an unexpected format not covered by any parser pattern?
- What happens when the WebSocket subscription is not confirmed before the command is sent?
- What happens when `_get_device_info` fails (API error) — does the flow continue or abort?
- What happens when the user selects a non-Layer-3-capable switch that has no routing protocols?

## Requirements

### Functional Requirements

- **FR-001**: System MUST have at least one unit test for each helper method in the routing table pipeline (`_select_routing_table_device`, `_connect_websocket`, `_get_routing_table_params`, `_execute_routing_table_command`, `_process_routing_table_results`)
- **FR-002**: System MUST have parsing tests for `_parse_routing_table` covering Juniper format, standard route lines, protocol-keyword lines, JSON format, tabular format, and empty/malformed input
- **FR-003**: System MUST have tests for `_display_routing_summary` verifying correct statistics (protocol counts, unique destinations, next-hops, interfaces, active routes) for known inputs
- **FR-004**: System MUST notify the user when an unrecognized protocol is entered and the default "any" is used
- **FR-005**: System MUST clean up the WebSocket connection in all failure paths, including when subscription fails after connection succeeds
- **FR-006**: System MUST log and display a meaningful message when the API response does not contain a session ID
- **FR-007**: System MUST verify WebSocket subscription confirmation before sending commands, with a configurable wait timeout instead of a hardcoded 1-second sleep
- **FR-008**: System MUST have error-path tests for connection failure, subscription failure, API error responses, timeout, and KeyboardInterrupt
- **FR-009**: Menu #7 MUST remain reachable and functional with existing behavior preserved after all fixes

### Key Entities

- **WebSocketManager**: Manages authenticated WebSocket connections, channel subscriptions, threaded message handling, and result storage with session-based demultiplexing
- **RoutingUtils**: Static utility class containing the 5-step orchestrator pipeline and all routing-specific parsing, display, and error-handling methods
- **Route Entry**: Parsed routing table record with destination, next-hop, protocol, interface, table name, and active flag
- **Session ID**: Correlation identifier returned by the API POST, used to match WebSocket result messages to the originating command

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 8 new test cases exist covering the routing table pipeline (parsing, parameter handling, result processing, error paths)
- **SC-002**: All parsing format variants (Juniper, standard, protocol, JSON, tabular, empty) have at least one dedicated test each
- **SC-003**: Connection leak on subscription failure is eliminated — every code path that opens a WebSocket connection also closes it
- **SC-004**: Users see an explicit notification when protocol input is unrecognized and defaulted to "any"
- **SC-005**: Users see an explicit error message when the API response lacks a session ID
- **SC-006**: All existing Menu #7 behavior is preserved — no regressions in the happy-path flow
- **SC-007**: Test suite runs without requiring live Mist API access (all external dependencies mocked)

## Assumptions

- The audit scope is limited to Menu #7 and the `RoutingUtils` methods it invokes. Shared infrastructure (`WebSocketManager`, `PromptUtils`) will be tested only as they relate to routing table functionality.
- The `_parse_juniper_routing` sub-parser (called when Juniper format is detected) is in scope for testing but detailed refactoring of its internals is deferred unless bugs are found.
- The hardcoded `device_type="switch"` filter is documented as an issue but not changed in this audit — the docstring's claim of SRX/SSR support via this menu item is considered misleading documentation rather than a missing feature (Menu #8 handles SSR/SRX).
- Input validation improvements (FR-004, User Story 4) are lower priority and may be deferred to a follow-up if the test coverage work (User Stories 1-3) is substantial.
