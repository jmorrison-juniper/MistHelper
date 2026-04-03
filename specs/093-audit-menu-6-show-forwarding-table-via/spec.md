# Feature Specification: Audit Menu #6 — Show Forwarding Table via WebSocket

**Feature Branch**: `093-audit-menu-6-show-forwarding-table-via`  
**Created**: 2025-07-15  
**Status**: Draft  
**Type**: Audit  
**Input**: User description: "MistHelper Menu #6: Show forwarding table via WebSocket — audit existing implementation, document current state, identify issues, and define acceptance criteria for fixes"

## Audit Context

**Function**: `WebSocketCommands.show_forwarding_table` (delegates to `RoutingUtils.execute_show_forwarding_table`)  
**Category**: WebSocket (interactive, not a data export)  
**SQL Export Relevant**: No  
**Menu Wiring**: Menu option `"6"` maps to `WebSocketCommands.show_forwarding_table` with description "Show forwarding table on gateway device via WebSocket (Layer 3 routing table)"

### Current Implementation Summary

Menu #6 allows a network operator to query the Layer 3 forwarding table (FIB) of a Mist-managed gateway or SSR device. The workflow is:

1. **Site selection** — Operator picks a site from cached CSV inventory
2. **Device selection** — Operator picks a gateway/SSR device from the site's inventory
3. **WebSocket connection** — Authenticated WebSocket opened to `wss://api-ws.{host}/api-ws/v1/stream`
4. **Channel subscription** — Subscribes to `/sites/{site_id}/devices/{device_id}/cmd`
5. **Parameter collection** — Operator provides optional IP prefix, service name, VRF, and HA node
6. **Command execution** — REST POST to `show_forwarding_table` endpoint returns a session ID
7. **Result retrieval** — WebSocket listener matches results by session ID with 60-second timeout
8. **Display** — Parsed JSON forwarding entries rendered as a formatted summary table
9. **Cleanup** — WebSocket disconnected in `finally` block regardless of outcome

### Audit Findings

**Issue AF-01: No automated test coverage**  
The entire forwarding table workflow (`show_forwarding_table`, `execute_show_forwarding_table`, all helper methods in `RoutingUtils` for forwarding table, and `_parse_forwarding_table`) has zero unit or integration tests. Other WebSocket commands (clear policy hit count, clear learned MACs, clear BPDU error, clear session) have dedicated test files, but forwarding table does not.

**Issue AF-02: Silent failure on empty return from device selection**  
`_select_forwarding_table_device` returns `(None, None, None)` when the operator cancels or no device is found. The caller in `execute_show_forwarding_table` checks `if not site_id or not device_id: return` — this exits silently with no return value and no log entry at INFO level, making it difficult to distinguish user cancellation from a failure in automation or log auditing.

**Issue AF-03: Hardcoded 1-second sleep after WebSocket subscription**  
In `_connect_websocket`, after subscribing to the device command channel, there is a `time.sleep(1)` before returning. This arbitrary delay is not tied to any confirmation from the WebSocket server and wastes time in the common case while providing no reliability guarantee.

**Issue AF-04: No input validation on user-provided parameters**  
`_get_forwarding_table_params` accepts IP prefix, service name, VRF, and node inputs from the operator. The IP prefix is not validated as a valid CIDR notation. The node input only checks for `node0` or `node1` but silently discards other values without warning the operator. No length limits or character validation on service name or VRF.

**Issue AF-05: Fragile JSON parsing in `_parse_forwarding_table`**  
The parser assumes each line of raw output is a standalone JSON object (`line.startswith("{") and line.endswith("}")`). Multi-line JSON, JSON arrays, or output containing non-JSON diagnostic text will be silently skipped. Parse failures fall back to returning `[{"raw_data": raw_output}]` which mixes error state into the data model.

**Issue AF-06: No retry mechanism for transient failures**  
The entire execution is single-shot. If the WebSocket connection drops, the REST POST fails transiently, or the device is temporarily busy, the operator must manually re-run menu option 6 from scratch. There is no automatic retry with backoff for any step.

**Issue AF-07: Device type filtering allows non-gateway selection**  
`_select_forwarding_table_device` passes `device_type="gateway"` to `PromptUtils.select_device_id_from_inventory`, but guidance text in `_display_forwarding_table_timeout` accounts for switch and AP device types. If the inventory filter is bypassed or returns mixed types, the command may be sent to an incompatible device with confusing results.

**Issue AF-08: REST POST uses raw `requests` instead of `mistapi` session**  
`_execute_forwarding_table_command` constructs its own `requests.post()` call with manually extracted host and token, bypassing the `mistapi` library's built-in session management, SSL verification settings, and error handling. This creates a maintenance risk if the Mist API authentication or base URL logic changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Successful Forwarding Table Retrieval (Priority: P1)

A network operator selects Menu #6 to inspect the Layer 3 forwarding table on a gateway device. They select a site and gateway, optionally provide filter parameters, and receive a formatted summary of forwarding entries including IP prefixes, services, tenants, protocols, and next-hop interfaces.

**Why this priority**: This is the core happy-path use case. If this doesn't work reliably, the feature has no value.

**Independent Test**: Can be fully tested by mocking WebSocket responses and REST API calls, then verifying the complete flow from device selection through formatted output display.

**Acceptance Scenarios**:

1. **Given** a valid site and online gateway device, **When** the operator selects Menu #6 and accepts default parameters (0.0.0.0/0), **Then** the system displays a formatted summary of all forwarding table entries with entry count, unique prefixes, services, tenants, protocols, and interfaces.
2. **Given** a valid site and online gateway device, **When** the operator provides a specific IP prefix filter (e.g., 192.168.1.0/24), **Then** the system displays only forwarding entries matching that prefix.
3. **Given** a valid site and online SSR gateway, **When** the operator provides a service name and VRF filter, **Then** the system includes both parameters in the query and displays filtered results.
4. **Given** a valid site and an HA SSR pair, **When** the operator specifies node0 or node1, **Then** the query targets the specified node and results reflect that node's forwarding table.

---

### User Story 2 — Graceful Error Handling and Operator Guidance (Priority: P1)

A network operator encounters various failure conditions (device offline, wrong device type, connection timeout, invalid parameters) and receives clear, actionable feedback at every failure point rather than silent exits or cryptic errors.

**Why this priority**: Equal to P1 because poor error handling makes the tool untrustworthy in production network operations where operators need confidence in their diagnostic tools.

**Independent Test**: Can be tested by simulating each failure condition (no site selected, no device selected, WebSocket connection failure, REST API error, timeout) and verifying the error message and logging behavior.

**Acceptance Scenarios**:

1. **Given** the operator cancels site selection, **When** the system returns to the menu, **Then** an INFO-level log entry records the cancellation and the operator sees a clear cancellation message.
2. **Given** no gateway devices exist at the selected site, **When** device selection fails, **Then** the operator is told no gateway devices are available and is guided to check their site selection.
3. **Given** the WebSocket connection cannot be established, **When** the connection times out after 5 seconds, **Then** the operator sees a connection failure message with troubleshooting suggestions (check network, verify API host).
4. **Given** the REST POST to issue the command returns a non-200 status, **When** the error is displayed, **Then** the status code and response body are shown, and the WebSocket connection is properly cleaned up.
5. **Given** the device does not respond within 60 seconds, **When** the timeout occurs, **Then** device-type-specific troubleshooting guidance is displayed and the WebSocket connection is cleaned up.
6. **Given** the operator enters an invalid IP prefix (e.g., "not-an-ip"), **When** the parameter is submitted, **Then** the system validates the input and prompts for correction before sending the request.

---

### User Story 3 — Input Parameter Validation (Priority: P2)

A network operator provides filtering parameters (IP prefix, service name, VRF, HA node) and the system validates all inputs before issuing the command to prevent wasted time on invalid queries.

**Why this priority**: Invalid inputs waste operator time and WebSocket resources. Validation prevents unnecessary API calls.

**Independent Test**: Can be tested in isolation by calling the parameter collection function with various valid and invalid inputs and verifying acceptance/rejection behavior.

**Acceptance Scenarios**:

1. **Given** the operator enters a valid CIDR prefix (e.g., 10.0.0.0/8), **When** the payload is built, **Then** the prefix is included unchanged.
2. **Given** the operator enters an invalid prefix (e.g., "abc", "999.999.999.999/33"), **When** validation runs, **Then** the operator is warned and prompted to re-enter or accept the default.
3. **Given** the operator enters a node value other than node0 or node1 (e.g., "node2", "primary"), **When** validation runs, **Then** the operator is warned that only node0 and node1 are valid options.
4. **Given** the operator leaves all parameters blank, **When** the payload is built, **Then** the default prefix 0.0.0.0/0 is used and confirmed to the operator.

---

### User Story 4 — Automated Test Coverage (Priority: P2)

The forwarding table feature has comprehensive unit and integration tests covering the happy path, each error branch, parameter validation, JSON parsing, and display formatting.

**Why this priority**: Zero test coverage is a critical quality gap. Tests are needed to prevent regressions and enable safe refactoring.

**Independent Test**: Can be verified by running the test suite and confirming all forwarding-table-related tests pass with adequate coverage of the identified code paths.

**Acceptance Scenarios**:

1. **Given** the test suite, **When** all forwarding table tests are run, **Then** unit tests cover: device selection (success/cancel), WebSocket connection (success/failure), parameter collection (all variations), command execution (success/error status/missing session), result processing (success/timeout), JSON parsing (valid/invalid/empty/multi-chunk), display formatting (entries/empty/raw fallback), and resource cleanup.
2. **Given** a mock WebSocket server, **When** integration tests run the full flow, **Then** the end-to-end sequence from site selection through result display completes correctly.
3. **Given** the test suite, **When** coverage is measured for forwarding table code paths, **Then** at least 80% of branches are covered.

---

### User Story 5 — Robust JSON Parsing (Priority: P3)

The forwarding table result parser handles all realistic output formats from Mist devices including multi-line JSON, mixed diagnostic text with JSON, empty responses, and malformed data — without losing valid entries or confusing error state with data.

**Why this priority**: Parsing fragility causes silent data loss, which is unacceptable for a network diagnostic tool.

**Independent Test**: Can be tested by feeding diverse raw output samples into the parser and verifying correct extraction of entries.

**Acceptance Scenarios**:

1. **Given** raw output containing multiple single-line JSON objects with "rows" arrays, **When** the parser runs, **Then** all entries from all chunks are collected into the result.
2. **Given** raw output containing multi-line formatted JSON, **When** the parser runs, **Then** the JSON is correctly reassembled and parsed.
3. **Given** raw output containing a mix of diagnostic text and JSON objects, **When** the parser runs, **Then** only valid JSON entries are extracted and diagnostic text is ignored.
4. **Given** completely empty or whitespace-only output, **When** the parser runs, **Then** an empty list is returned (not a raw_data fallback object).
5. **Given** malformed JSON that cannot be parsed, **When** the parser runs, **Then** the error is logged and the raw output is available for operator inspection, clearly distinguished from valid parsed entries.

---

### Edge Cases

- What happens when the WebSocket connection drops mid-command after the REST POST succeeds but before results arrive?
- How does the system behave when the device returns a very large forwarding table (thousands of entries)?
- What happens if two operators run forwarding table queries against the same device concurrently?
- How does the system handle a device that returns results in an unexpected format (e.g., plain text instead of JSON)?
- What happens if the API token expires between the WebSocket connection and the REST POST?
- How does the system behave when the Mist API host uses a regional endpoint (e.g., api.eu.mist.com)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the operator to query the Layer 3 forwarding table of a gateway/SSR device via WebSocket using Menu #6
- **FR-002**: System MUST validate IP prefix input as valid CIDR notation before issuing the command, or clearly warn the operator and allow correction
- **FR-003**: System MUST validate HA node input (only node0 or node1 accepted) and warn the operator if an invalid value is entered rather than silently discarding it
- **FR-004**: System MUST log an INFO-level entry when the operator cancels site or device selection, distinguishing cancellation from error
- **FR-005**: System MUST display clear, actionable error messages for each distinct failure mode: connection failure, subscription failure, authentication failure, API error, timeout, and parsing failure
- **FR-006**: System MUST clean up the WebSocket connection in all exit paths including exceptions, timeouts, and user cancellation
- **FR-007**: System MUST parse forwarding table JSON results correctly, handling multi-line JSON, multiple chunks, and mixed diagnostic output without silently dropping valid entries
- **FR-008**: System MUST display a formatted summary of forwarding table results including entry count, unique IP prefixes, services, tenants, protocols, and next-hop interfaces
- **FR-009**: System MUST use the default prefix 0.0.0.0/0 when the operator provides no prefix, and confirm this default to the operator
- **FR-010**: System MUST support optional filtering by service name, VRF, and HA node in addition to IP prefix
- **FR-011**: System MUST have unit tests covering all identified code paths: device selection, WebSocket connection, parameter validation, command execution, result processing, JSON parsing, display formatting, and cleanup
- **FR-012**: System MUST provide device-type-specific troubleshooting guidance when commands timeout or fail, helping the operator understand whether their selected device supports forwarding table queries

### Key Entities

- **Forwarding Table Entry**: A single entry in the device's Forwarding Information Base (FIB), containing IP prefix, service, tenant, protocol, next-hop interface, and other routing metadata
- **WebSocket Session**: An authenticated real-time connection to the Mist cloud, identified by a session ID returned from the REST API command, used to receive command results asynchronously
- **Gateway/SSR Device**: A Mist-managed Layer 3 device (router, gateway, or SSR/128T appliance) that maintains a forwarding table for packet routing decisions

## Assumptions

- The existing `WebSocketManager` class correctly handles WebSocket connection lifecycle, threading, and session-based message demultiplexing — this audit focuses on forwarding-table-specific logic, not the shared WebSocket infrastructure
- The `PromptUtils.select_site_id_from_csv()` and `PromptUtils.select_device_id_from_inventory()` methods work correctly for interactive selection — their behavior is outside the scope of this audit
- The Mist API endpoint `POST /api/v1/sites/{site_id}/devices/{device_id}/show_forwarding_table` conforms to the documented contract in `documentation/api/utilities/`
- The 60-second command result timeout is appropriate for most devices — extremely large forwarding tables on busy devices may need longer, but this is an acceptable default
- The `websocket-client` library's `WebSocketApp.run_forever()` in a daemon thread is a stable pattern for the application's concurrency model
- Regional Mist API endpoints (e.g., `api.eu.mist.com`) correctly map to `api-ws.eu.mist.com` for WebSocket connections

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can retrieve a forwarding table from an online gateway device within 90 seconds end-to-end (including site/device selection, parameter entry, command execution, and result display)
- **SC-002**: 100% of identified error paths (AF-01 through AF-08) have corresponding fixes validated by passing tests
- **SC-003**: At least 80% branch coverage for all forwarding-table-related code paths (device selection, connection, parameters, execution, parsing, display, cleanup)
- **SC-004**: Invalid IP prefix input is caught and communicated to the operator before any API call is made, preventing wasted WebSocket and API resources
- **SC-005**: Every exit path from the forwarding table workflow produces at minimum an INFO-level log entry, enabling post-incident audit of operator actions
- **SC-006**: The JSON parser correctly extracts forwarding entries from at least 5 distinct output format variations (single-line JSON, multi-line JSON, multi-chunk, mixed text, empty response) without data loss
- **SC-007**: Operators receive device-type-specific guidance within 2 seconds of a timeout or failure, reducing mean time to resolution for forwarding table diagnostic issues
