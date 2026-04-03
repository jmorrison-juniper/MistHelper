# Feature Specification: Audit Menu #8 — Show SSR/SRX Routing Table

**Feature Branch**: `095-audit-menu-8-show-ssrsrx-routing-table`
**Created**: 2025-07-17
**Status**: Draft
**Input**: User description: "MistHelper Menu #8: Show SSR/SRX routing table — AUDIT spec analyzing WebSocketCommands.show_ssr_routes implementation"

## Current State Analysis

Menu #8 ("Show SSR/SRX routing table via dedicated API") invokes `WebSocketCommands.show_ssr_routes()`, a static method that delegates entirely to `RoutingUtils.execute_show_ssr_routes()`. Unlike menus 5–7 which use generic WebSocket `showDeviceCommandPorts` calls, menu #8 calls the dedicated `mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes` endpoint, which provides structured routing table queries optimized for SSR (128T Session Smart Router) and SRX (Juniper SRX series) gateways.

**Execution pipeline (5 steps):**

1. **Select site and device** — `_select_ssr_device()` prompts for site (from CSV), then filters devices by `device_type="gateway"`, then verifies SSR/SRX compatibility via model string matching.
2. **Collect query parameters** — `_get_ssr_route_params()` prompts for protocol, prefix, VRF, BGP neighbor, HA node, refresh interval, and duration. All parameters are optional.
3. **Establish WebSocket connection** — `_connect_websocket()` creates a `WebSocketManager`, connects, and subscribes to `/sites/{site_id}/devices/{device_id}/cmd`.
4. **Execute API call** — `_execute_ssr_route_command()` calls `showSiteSsrAndSrxRoutes` with the request body, extracts a `session` ID from the response.
5. **Process results** — `_process_ssr_route_results()` waits on WebSocket for the session result (60s timeout), then delegates to `_display_ssr_route_output()` for parsing and display.

**Result display path:** `_display_ssr_route_output()` attempts `_parse_ssr_routing()` on the `"raw"` field first (expects JSON with `status`, `columns`, `rows` structure). If that returns no entries, it falls back to `_parse_routing_table()` (generic text-based parser). It repeats the same logic for the `"Output"` field if present.

**Category**: WebSocket (interactive, not a data export). Not SQL-export relevant.

## Issues Found

### Issue 1: Misleading print message in shared `_connect_websocket()` helper

`_connect_websocket()` (line 18004) hardcodes: `"Executing show forwarding table on device {device_id}..."`. This message is incorrect when called from menu #8 (SSR routing), menu #7 (switch routing), or menu #5 (MAC table). The method is shared across all four WebSocket commands but always displays the menu #6 message.

**Impact**: User sees the wrong operation name, causing confusion about which command is running.

### Issue 2: Fixed 60-second WebSocket timeout conflicts with user-configurable duration

`_process_ssr_route_results()` passes `timeout_seconds=60` to `wait_for_command_result()`, but the user can configure a refresh duration up to 300 seconds via the `duration` parameter in `_get_ssr_route_params()`. A 120-second real-time refresh will always timeout at 60 seconds, losing results and displaying an error.

**Impact**: Real-time refresh with duration > 60 seconds silently fails. Users who configure longer durations see a timeout error rather than results.

### Issue 3: Inconsistent node parameter structure in request body

`_get_ssr_route_params()` wraps the node selection in a nested dictionary `{"node": node_input}`, producing `request_body["node"] = {"node": "node0"}`. All other parameters are flat string values. This nesting may not match the API contract and could cause silent parameter rejection.

**Impact**: HA cluster node selection may be silently ignored by the API, causing the wrong node's routing table to be returned without warning.

### Issue 4: No input validation for prefix format

The prefix parameter accepts any free-text input without validating CIDR notation (e.g., `192.168.1.0/24`). Invalid prefixes like `foo`, `999.999.999.999/99`, or partial input `192.168.` are passed directly to the API.

**Impact**: Users may get unhelpful API errors or empty results with no indication of what went wrong.

### Issue 5: SSR routing parser silently returns empty on non-SUCCESS status

`_parse_ssr_routing()` returns an empty list when `data.get("status") != "SUCCESS"` without logging the actual status or error message from the API response. Error details in the response body are discarded.

**Impact**: When the API returns an error status with diagnostic information, users see only "No routing table entries found" with no troubleshooting guidance.

### Issue 6: Zero test coverage

No unit tests, integration tests, or any test references exist for `show_ssr_routes`, `execute_show_ssr_routes`, `_select_ssr_device`, `_verify_ssr_compatibility`, `_get_ssr_route_params`, `_execute_ssr_route_command`, `_process_ssr_route_results`, `_display_ssr_route_output`, `_parse_ssr_routing`, or `_display_ssr_routing`. The entire menu #8 flow is untested.

**Impact**: Any regression, refactor, or API contract change will go undetected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Query SSR/SRX routing table with default parameters (Priority: P1)

A network operator selects menu #8, chooses a site and SSR gateway, accepts all default parameters (pressing Enter through each prompt), and receives the full routing table displayed in a formatted table.

**Why this priority**: This is the most common usage pattern — operators want a quick view of the routing table without filtering.

**Independent Test**: Can be fully tested by mocking the API session, device selection, and WebSocket results, then verifying the correct API call and formatted output.

**Acceptance Scenarios**:

1. **Given** an authenticated session and at least one SSR gateway in the selected site, **When** the operator selects menu #8 and accepts all defaults, **Then** the system calls the SSR routing API with an empty request body, displays a formatted routing table, and closes the WebSocket connection.
2. **Given** an authenticated session, **When** the operator selects menu #8 but cancels at site selection, **Then** the system prints a cancellation message and returns without establishing any connection.
3. **Given** an authenticated session, **When** the operator selects menu #8 but cancels at device selection, **Then** the system prints a cancellation message and returns without establishing any connection.

---

### User Story 2 — Query with filtered parameters (Priority: P2)

A network operator queries the routing table with specific filters: a BGP protocol filter, a specific prefix, a VRF name, and a BGP neighbor IP with route direction. The results show only matching routes.

**Why this priority**: Filtered queries are the primary troubleshooting use case — operators need to drill into specific routing issues.

**Independent Test**: Can be tested by providing mock user inputs for each parameter and verifying the request body structure passed to the API.

**Acceptance Scenarios**:

1. **Given** an authenticated session and a selected SSR device, **When** the operator specifies protocol=bgp, prefix=10.0.0.0/8, and neighbor=192.168.1.1 with direction=received, **Then** the request body contains all specified parameters and the API is called with the correct body.
2. **Given** an authenticated session and a selected SSR device, **When** the operator enters an invalid protocol value (e.g., "rip"), **Then** the system ignores the invalid input and proceeds with no protocol filter rather than sending an invalid value.
3. **Given** an authenticated session and a selected SSR device, **When** the operator specifies node=node0 for an HA cluster, **Then** the node parameter is correctly formatted in the request body and the correct node's routing table is returned.

---

### User Story 3 — Device compatibility handling for non-SSR/SRX gateways (Priority: P2)

A network operator selects a gateway device that is neither SSR nor SRX (e.g., a different gateway model). The system warns about limited compatibility and asks for confirmation before proceeding.

**Why this priority**: Prevents operators from accidentally running an SSR-specific command against an incompatible device, which could produce misleading results.

**Independent Test**: Can be tested by mocking device info with various model strings and verifying the compatibility check behavior.

**Acceptance Scenarios**:

1. **Given** a device with model containing "SSR" or "128T", **When** compatibility is checked, **Then** the system confirms full compatibility and proceeds without prompting.
2. **Given** a device with model containing "SRX", **When** compatibility is checked, **Then** the system confirms full compatibility and proceeds without prompting.
3. **Given** a gateway device with an unrecognized model, **When** compatibility is checked, **Then** the system warns about limited compatibility and prompts for confirmation. Answering "n" cancels the operation.
4. **Given** a non-gateway device type, **When** compatibility is checked, **Then** the system warns about the device type mismatch and prompts for confirmation.

---

### User Story 4 — Real-time refresh mode (Priority: P3)

A network operator configures a refresh interval (e.g., 5 seconds) and duration (e.g., 120 seconds) to monitor routing table changes in real-time.

**Why this priority**: Real-time monitoring is a less frequent but valuable use case for tracking route convergence during maintenance windows.

**Independent Test**: Can be tested by verifying the interval and duration parameters are included in the request body and that the WebSocket timeout accommodates the configured duration.

**Acceptance Scenarios**:

1. **Given** a selected SSR device, **When** the operator configures interval=5 and duration=120, **Then** the request body includes both parameters and the WebSocket wait timeout is at least as long as the configured duration plus a buffer.
2. **Given** a selected SSR device, **When** the operator configures interval=5 and presses Enter for duration, **Then** the duration defaults to 30 seconds.
3. **Given** a selected SSR device, **When** the operator enters interval=0, **Then** no duration prompt is shown and the query is one-time only.

---

### User Story 5 — Error handling and graceful degradation (Priority: P2)

When the WebSocket connection fails, the API returns an error, or results time out, the system provides clear error messages and suggests fallback options.

**Why this priority**: Robust error handling prevents operators from being stuck with cryptic failures during time-sensitive troubleshooting.

**Independent Test**: Can be tested by simulating each failure mode (connection failure, API error, timeout) and verifying the error messages and cleanup behavior.

**Acceptance Scenarios**:

1. **Given** a WebSocket connection failure, **When** the operator attempts to query, **Then** the system prints a clear error message and does not attempt the API call.
2. **Given** a successful WebSocket connection but an API error response, **When** results are processed, **Then** the system displays the error details from the API response (not just "No routing table entries found").
3. **Given** a successful API call but no WebSocket result within the timeout, **When** the timeout expires, **Then** the system prints a timeout message, suggests menu #7 as fallback, and properly closes the WebSocket connection.
4. **Given** the operator presses Ctrl+C at any point, **When** the KeyboardInterrupt is caught, **Then** the system prints an interruption message and cleanly closes the WebSocket connection.

### Edge Cases

- What happens when the device inventory API call fails during `_get_device_info()`? Currently it logs a warning and proceeds with `None` device info, which means the compatibility check is skipped entirely (returns `True` for `None` device_info).
- What happens when `_parse_ssr_routing()` encounters valid JSON that does not contain `columns` or `rows` keys? It returns an empty list, falling through to the generic parser, which may misinterpret the data.
- What happens when both `"raw"` and `"Output"` fields contain identical data? The system displays it twice, once as primary output and once under "ADDITIONAL OUTPUT", which is redundant and confusing.
- What happens when the user enters a prefix with no subnet mask (e.g., `10.0.0.1` instead of `10.0.0.1/32`)? The input is passed as-is — API behavior is undefined.
- What happens when the SSR routing API response has `status != "SUCCESS"` but contains a meaningful error message? The parser discards it and returns an empty list with no error context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display the correct operation name ("SSR/SRX routing table") in all user-facing messages during the menu #8 flow, including the shared WebSocket connection step.
- **FR-002**: System MUST set the WebSocket wait timeout to at least the configured refresh duration plus a 30-second buffer when real-time refresh is requested.
- **FR-003**: System MUST format the HA cluster node parameter correctly for the SSR routing API contract (flat value, not nested dictionary).
- **FR-004**: System MUST validate prefix input as valid CIDR notation (IPv4 or IPv6 with subnet mask) before including it in the request body, and display a clear validation message for invalid input.
- **FR-005**: System MUST log and display the API error status and any diagnostic message when `_parse_ssr_routing()` encounters a non-SUCCESS status, rather than silently returning an empty result.
- **FR-006**: System MUST suppress duplicate output when the `"raw"` and `"Output"` fields in the WebSocket result contain identical data.
- **FR-007**: System MUST have unit test coverage for `execute_show_ssr_routes()` covering: successful query with default parameters, successful query with all parameters specified, device selection cancellation, WebSocket connection failure, API error response, and WebSocket timeout.
- **FR-008**: System MUST have unit test coverage for `_verify_ssr_compatibility()` covering: SSR device, SRX device, unrecognized gateway, and non-gateway device type.
- **FR-009**: System MUST have unit test coverage for `_get_ssr_route_params()` covering: all defaults, all parameters specified, invalid protocol rejection, and boundary values for interval/duration.
- **FR-010**: System MUST have unit test coverage for `_parse_ssr_routing()` covering: successful parse, non-SUCCESS status, missing columns/rows, malformed JSON, and empty input.

### Key Entities

- **SSR/SRX Device**: A gateway device (type="gateway") with model matching SSR, 128T, or SRX. Key attributes: site_id, device_id, model, name, type, HA cluster node.
- **Routing Query Parameters**: Optional filters for routing table queries. Key attributes: protocol (enum), prefix (CIDR), VRF name, BGP neighbor IP, route direction (received/advertised), HA node (node0/node1), refresh interval (0–10s), duration (0–300s).
- **Routing Table Entry**: A single route from the parsed API response. Key attributes: destination prefix, next hop, protocol, route name, status, selection reason, weight, metric, local preference, AS path, VRF.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All six identified issues (misleading message, timeout mismatch, node parameter nesting, prefix validation, silent error suppression, duplicate output) are resolved and verified by tests.
- **SC-002**: Unit test coverage exists for every helper method in the menu #8 flow: `show_ssr_routes`, `execute_show_ssr_routes`, `_select_ssr_device`, `_verify_ssr_compatibility`, `_get_ssr_route_params`, `_execute_ssr_route_command`, `_process_ssr_route_results`, `_display_ssr_route_output`, and `_parse_ssr_routing`.
- **SC-003**: All unit tests pass in under 10 seconds without requiring network access, live API credentials, or WebSocket connections.
- **SC-004**: Users who configure real-time refresh with duration up to 300 seconds receive complete results without premature timeout.
- **SC-005**: Users who query non-SSR/SRX gateways receive clear compatibility warnings and can make an informed decision to proceed or cancel.
- **SC-006**: Existing menu #8 behavior is preserved for all valid inputs — no regressions in the happy-path flow.

## Assumptions

- The `mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes` API expects the node parameter as a flat string value (e.g., `"node": "node0"`), not a nested dictionary. This assumption should be verified against API documentation during implementation.
- The 60-second fixed timeout was an oversight, not an intentional design decision. Adjusting it to match user-configured duration is safe.
- The `_connect_websocket()` method's hardcoded message is a copy-paste artifact from menu #6, not an intentional choice.
- Prefix validation should follow standard CIDR notation (e.g., `10.0.0.0/8`, `192.168.1.0/24`, `2001:db8::/32`) and reject bare IPs without mask, non-numeric octets, and out-of-range values.
