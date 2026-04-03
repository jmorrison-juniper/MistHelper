# Feature Specification: Audit Menu #5 — Show MAC Table via WebSocket

**Feature Branch**: `092-audit-menu-5-show-mac-table-via`  
**Created**: 2025-07-01  
**Status**: Draft  
**Type**: Audit (analyze existing implementation, document issues, define acceptance criteria for fixes)  
**Input**: User description: "MistHelper Menu #5: Show MAC table via WebSocket — audit existing `WebSocketCommands.show_mac_table` implementation"

## Current Implementation Summary

Menu #5 allows a network operator to retrieve the MAC address learning table from a Juniper Mist-managed switch via WebSocket streaming. The workflow follows a three-phase pattern:

1. **Interactive selection** — operator picks a site then a switch device (Layer 2 only)
2. **WebSocket lifecycle** — connect, subscribe to the device command channel, issue a REST POST to trigger `show_mac_table`, then stream results back over WebSocket
3. **Result display** — raw output is printed to the console with field enumeration for debugging

Key components: `WebSocketCommands.show_mac_table` (static method, ~225 lines), `WebSocketManager` class (connection, subscription, message handling, result waiting), `PromptUtils` (site and device selection helpers).

## Audit Findings

### AF-01: No dedicated unit tests

`show_mac_table` has **zero** test coverage. The only MAC-related test (`test_clear_learned_macs.py`) covers Menu #152, not Menu #5. All WebSocket connection, subscription, command triggering, streaming, timeout, and result-parsing paths are untested.

### AF-02: `finally` block uses fragile local-variable lookup

The cleanup block uses `locals().get("websocket_manager")` to find the manager instance. If the variable is renamed or a future refactor moves the try/except boundary, cleanup silently fails and the WebSocket connection leaks.

### AF-03: Subscription success is not confirmed

`subscribe_to_channel` sends the subscribe message and immediately returns `True` without waiting for a server-side acknowledgment. A race condition exists: the REST POST to trigger the command may fire before the subscription is actually active on the server, causing results to be silently lost.

### AF-04: Hardcoded 1-second sleep after subscribe

`time.sleep(1)` is used as a workaround for AF-03. This is brittle — too short under load, wasteful under normal conditions.

### AF-05: Direct `requests.post` bypasses the API session

The REST call to `/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table` is made with raw `requests.post` and manually assembled headers instead of using the shared `apisession` object. This bypasses any session-level retry logic, connection pooling, proxy configuration, and certificate pinning that the API session may provide.

### AF-06: Completion detection heuristics are fragile

MAC table completion relies on: (a) detecting the text "ethernet switching table", (b) counting repeated identical messages, or (c) an idle-time heuristic (3 seconds with no new data). None of these are protocol-guaranteed — a large table could arrive with pauses exceeding 3 seconds between chunks, causing premature "completion."

### AF-07: Empty MAC table is indistinguishable from an error

When `mac_table_result` is returned but both `raw` and `Output` are empty, the code prints "No output data received" — the same message shown for a genuine parsing failure. An operator cannot tell whether the device has an empty MAC table or whether something went wrong.

### AF-08: Debug-mode code uses inline `import traceback`

The `except` block contains `import traceback` at runtime. While harmless, it deviates from the project's top-of-file import convention and is flagged by linters.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Retrieve MAC Table from a Healthy Switch (Priority: P1)

A network operator selects Menu #5, chooses a site and a switch, and views the complete MAC address learning table printed to the console.

**Why this priority**: This is the core value of the feature — everything else is error handling around this primary flow.

**Independent Test**: Can be fully tested by mocking WebSocket connection, subscription, REST POST, and streaming response, then asserting that the MAC table output is printed correctly.

**Acceptance Scenarios**:

1. **Given** a valid site and switch device are available, **When** the operator selects Menu #5 and picks a site and switch, **Then** the system establishes a WebSocket connection, subscribes to the device command channel, issues the show MAC table command, and displays the MAC table output.
2. **Given** the switch returns a MAC table with multiple entries across multiple VLANs, **When** results stream in via WebSocket, **Then** all entries are printed without truncation or corruption.
3. **Given** the switch returns an empty MAC table (zero learned entries), **When** results arrive, **Then** the system displays a clear message indicating "MAC table is empty" rather than a generic "No output data received."

---

### User Story 2 — Graceful Handling of Connection and Command Failures (Priority: P1)

When the WebSocket connection fails, the subscription fails, the REST POST returns an error, or no session ID is returned, the operator sees a clear, actionable error message and the system cleans up all resources.

**Why this priority**: Failure paths are exercised frequently in real networks (device offline, token expired, connectivity issues). Reliable error handling is essential for operator trust.

**Independent Test**: Can be tested by injecting failures at each stage (connection, subscription, POST, session ID extraction) and asserting the correct error message appears and the WebSocket is always disconnected.

**Acceptance Scenarios**:

1. **Given** the WebSocket connection cannot be established (network unreachable, invalid host), **When** the operator runs Menu #5, **Then** the system prints "Failed to establish WebSocket connection" and returns without leaking resources.
2. **Given** the REST POST to trigger show_mac_table returns a non-200 status, **When** the response is received, **Then** the system prints the HTTP status code and response body, disconnects the WebSocket, and returns.
3. **Given** the REST POST returns 200 but the response body does not contain a session ID, **When** the response is parsed, **Then** the system prints "No session ID returned" and cleans up.
4. **Given** the WebSocket subscription message is sent but the server never acknowledges it, **When** the REST command fires, **Then** results must still be captured (or the system must detect the unconfirmed subscription and warn the operator).

---

### User Story 3 — Timeout and Large-Table Resilience (Priority: P2)

When a device is slow to respond or has a very large MAC table (thousands of entries), the system waits long enough to collect all data and clearly communicates timeout situations.

**Why this priority**: Large campus switches can have 10,000+ MAC entries, and streaming may take longer than average. False timeouts frustrate operators.

**Independent Test**: Can be tested by simulating slow-arriving WebSocket messages and verifying that the system does not prematurely declare timeout or completion.

**Acceptance Scenarios**:

1. **Given** a switch with a large MAC table (5,000+ entries), **When** results stream in with occasional pauses of up to 5 seconds between chunks, **Then** the system continues collecting results and does not falsely trigger the idle-time completion heuristic.
2. **Given** no results arrive within the 60-second timeout, **When** the timeout expires, **Then** the system prints a timeout message with actionable troubleshooting hints (device type, connectivity, busy state).
3. **Given** the circuit breaker triggers after 10,000 checks, **When** this occurs, **Then** any partial results collected so far are displayed rather than discarded.

---

### User Story 4 — Resource Cleanup on Any Exit Path (Priority: P2)

Regardless of how the operation ends (success, error, timeout, user interrupt), the WebSocket connection is always closed and no threads are left running.

**Why this priority**: Connection leaks degrade system stability over repeated operations.

**Independent Test**: Can be tested by triggering each exit path (success, each error branch, timeout, KeyboardInterrupt) and asserting the WebSocket disconnect is called exactly once.

**Acceptance Scenarios**:

1. **Given** the operation completes successfully, **When** results are displayed, **Then** the WebSocket connection is closed and the background thread terminates.
2. **Given** an exception is raised during result processing, **When** the exception handler runs, **Then** the `finally` block reliably finds and disconnects the WebSocket manager without relying on `locals()` introspection.
3. **Given** the operator presses Ctrl+C during the wait, **When** `KeyboardInterrupt` is raised, **Then** the WebSocket is disconnected and the system returns cleanly.

---

### User Story 5 — Unit Test Coverage (Priority: P1)

Automated tests exist for all critical paths of the `show_mac_table` method and the `WebSocketManager` infrastructure it depends on.

**Why this priority**: Zero test coverage is the highest-risk finding. Every other audit finding becomes harder to fix safely without tests.

**Independent Test**: Can be verified by running the test suite and confirming tests exist that cover: happy path, each error branch, timeout, empty result, large table, cleanup, and completion detection heuristics.

**Acceptance Scenarios**:

1. **Given** the test suite is run, **When** all Menu #5-related tests execute, **Then** the following paths have at least one test each: successful MAC table retrieval, WebSocket connection failure, subscription failure, REST POST failure, missing session ID, timeout, empty MAC table, and resource cleanup.
2. **Given** the `WebSocketManager.wait_for_command_result` method is tested, **When** simulated messages arrive, **Then** the completion detection logic (table header pattern, repeated messages, idle timeout) is exercised with both correct and edge-case inputs.

---

### Edge Cases

- What happens when the operator selects a device type other than "switch" (e.g., router or AP)? The current filter restricts to `device_type="switch"`, but what if the inventory CSV contains miscategorized devices?
- What happens when the WebSocket connection drops mid-stream (after some results received but before completion)?
- What happens when the API token expires between the WebSocket connection and the REST POST?
- What happens when multiple operators issue MAC table commands to the same device concurrently — does session-based demultiplexing work correctly?
- What happens when the device returns MAC table output in an unexpected format (e.g., different Junos version, different vendor output)?
- What happens when `mist_host` uses a regional endpoint that doesn't follow the `api.` → `api-ws.` naming convention?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display the complete MAC address learning table output from a switch device selected by the operator
- **FR-002**: System MUST restrict device selection to switch-type devices (Layer 2), since routers and APs do not maintain MAC learning tables
- **FR-003**: System MUST establish a WebSocket connection with proper authentication before issuing commands
- **FR-004**: System MUST subscribe to the device command channel and confirm subscription readiness before triggering the REST command
- **FR-005**: System MUST use the shared API session for the REST POST rather than constructing raw HTTP requests with manually assembled credentials
- **FR-006**: System MUST extract the session ID from the REST response and use it to correlate streaming WebSocket results
- **FR-007**: System MUST distinguish between an empty MAC table (valid result with zero entries) and a command failure (no output received due to error)
- **FR-008**: System MUST wait up to 60 seconds for MAC table results, with the idle-timeout completion heuristic tolerating pauses of at least 5 seconds between data chunks
- **FR-009**: System MUST clean up the WebSocket connection on every exit path (success, error, timeout, user interrupt) using a reliable reference to the manager instance — not `locals()` introspection
- **FR-010**: System MUST display actionable error messages for each failure mode: connection failure, subscription failure, REST error, missing session ID, and timeout
- **FR-011**: System MUST have automated unit tests covering: happy path, each error branch, timeout, empty MAC table, large table streaming, completion detection heuristics, and resource cleanup
- **FR-012**: System MUST follow project import conventions (no inline imports in exception handlers)

### Key Entities

- **Site**: A Mist-managed location; identified by `site_id`, selected interactively from the inventory CSV
- **Switch Device**: A Layer 2 switching device within a site; identified by `device_id`, filtered by `device_type="switch"`
- **WebSocket Session**: A command execution session; identified by a `session_id` returned from the REST POST, used to correlate streaming results
- **MAC Table Entry**: A single learned MAC address record; contains MAC address, VLAN, interface, and learning type

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operator can retrieve and view a complete MAC table from a healthy switch in under 90 seconds end-to-end (including site/device selection)
- **SC-002**: All eight identified failure modes (connection failure, subscription failure, REST error, missing session ID, timeout, empty table, mid-stream disconnect, expired token) produce distinct, human-readable error messages
- **SC-003**: The WebSocket connection is confirmed closed after every operation — verified by zero leaked connections after 10 consecutive Menu #5 invocations
- **SC-004**: Unit test suite covers at least 80% of the lines in the `show_mac_table` method and the `WebSocketManager` methods it calls
- **SC-005**: MAC tables with 5,000+ entries stream to completion without false-positive timeout or premature completion detection
- **SC-006**: Empty MAC tables display a clear "MAC table is empty (0 entries)" message distinguishable from error conditions
- **SC-007**: All eight audit findings (AF-01 through AF-08) are resolved and verified by corresponding tests

## Assumptions

- The Mist API endpoint pattern `/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table` remains stable and is the correct endpoint for triggering MAC table retrieval
- The WebSocket host derivation (`api.` → `api-ws.`) is correct for all supported Mist cloud regions
- The `websocket-client` library (`WebSocketApp`) is the established dependency and will continue to be used
- MAC table output format follows Junos "ethernet switching table" conventions; other vendor formats are out of scope for this audit
- The `apisession` global object provides `host` and `apitoken` attributes suitable for both REST and WebSocket authentication
- The 60-second timeout is sufficient for tables with up to 10,000 entries under normal network conditions
