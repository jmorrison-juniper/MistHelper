# Feature Specification: WebSocket Migration to mistapi.websockets

**Feature Branch**: `websocket-migration`  
**Created**: 2026-06-11  
**Status**: Draft  
**Input**: Migrate MistHelper's ~3,008 lines of custom WebSocket code in `src/websocket/` to the official `mistapi.websockets` SDK module (v0.61.0+), maintaining identical user-facing behavior across all 22 menu operations (102-123).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Show Commands Work Identically (Priority: P1)

A NOC engineer selects a show command (Menu 102-115, e.g., "Show ARP Table") for a device. The command executes via `mistapi.websockets` instead of custom WebSocket code. Output format, column headers, data content, and error messages are identical to current behavior.

**Why this priority**: Show commands are the most frequently used WebSocket operations. Any regression here affects daily NOC workflows.

**Independent Test**: Run each show command (102-115) against a test device, capture output, and diff against baseline output from current custom implementation.

**Acceptance Scenarios**:

1. **Given** a connected Mist device, **When** the user selects Menu 102 (Show ARP), **Then** the ARP table output matches the current format exactly (same columns, same data, same sorting).
2. **Given** a device that is offline, **When** the user selects any show command, **Then** the error message displayed is the same as current behavior.
3. **Given** a show command that returns large output, **When** the user runs it, **Then** all results are collected completely without truncation or timeout.

---

### User Story 2 — Diagnostic Commands Work Identically (Priority: P1)

A NOC engineer selects a diagnostic command (Menu 116-123, e.g., "Ping", "Traceroute", "Cable Test"). The command executes via `mistapi.websockets`. Prompts for target host/interface, progress indicators, and result formatting are identical.

**Why this priority**: Diagnostic commands are critical troubleshooting tools. Regression breaks incident response workflows.

**Independent Test**: Run each diagnostic (116-123) against a test device, compare prompts and output to baseline.

**Acceptance Scenarios**:

1. **Given** a device and target host, **When** the user selects Menu 116 (Ping), **Then** the ping prompts, progress, and result output match current behavior.
2. **Given** a diagnostic that times out, **When** the timeout expires, **Then** the timeout message matches current behavior.
3. **Given** a cable test command, **When** the user selects an interface, **Then** the cable test results display identically.

---

### User Story 3 — Adapter Layer Provides Seamless Transition (Priority: P2)

During migration, an adapter wraps `mistapi.websockets` with the same interface as `WebSocketManager`. Menu operations call the adapter without code changes. Both old and new implementations can coexist during phased rollout.

**Why this priority**: Enables incremental migration — one operation at a time — reducing risk of breaking all 22 operations simultaneously.

**Independent Test**: Swap one show command to use the adapter, run it, confirm identical output. Then swap back to verify rollback works.

**Acceptance Scenarios**:

1. **Given** the adapter layer is implemented, **When** a show command calls it, **Then** the adapter delegates to `mistapi.websockets.sites.DeviceCmdEvents` and returns results in the same format as `WebSocketManager`.
2. **Given** a migration flag or configuration, **When** an operation is toggled to use the adapter, **Then** it works without any changes to the menu operation code.
3. **Given** the adapter encounters a `mistapi.websockets` error, **Then** it translates it to the same error format the menu operation expects.

---

### User Story 4 — Custom WebSocket Code Removed (Priority: P3)

After all 22 operations are migrated and verified, the entire `src/websocket/` directory (13 files, ~3,008 lines) is removed. No references remain in `MistHelper.py` or elsewhere. The `websocket-client` dependency is removed from `requirements.txt`.

**Why this priority**: Reduces maintenance burden and attack surface, but only safe after all operations are verified.

**Independent Test**: Remove `src/websocket/`, run full test suite, confirm no import errors or runtime failures.

**Acceptance Scenarios**:

1. **Given** all operations migrated, **When** `src/websocket/` is deleted, **Then** no import errors occur anywhere in the codebase.
2. **Given** cleanup is complete, **When** `websocket-client` is removed from dependencies, **Then** all operations still function via `mistapi.websockets`.
3. **Given** the cleanup PR is merged, **Then** the codebase has ~3,000 fewer lines of custom WebSocket code.

---

### Edge Cases

- What happens when `mistapi.websockets` disconnects mid-stream during a show command? (Must match current reconnection behavior or improve it.)
- What happens when the Mist API returns binary frames? (`mistapi.websockets` v0.61.1 handles these — verify identical parsing.)
- What happens when multiple show commands are queued rapidly? (Thread safety with `mistapi.websockets` locks vs current custom locking.)
- What happens when an operation is in the `device-utils-adoption` spec scope? (Skip WS migration for those ops — they'll use `device_utils` instead.)
- What happens when `mistapi` version is below 0.61.0? (Fail gracefully with clear version requirement message.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an adapter class that wraps `mistapi.websockets.sites.DeviceCmdEvents` with the same interface as the current `WebSocketManager`.
- **FR-002**: System MUST migrate show commands (Menu 102-115) to use `mistapi.websockets` via the adapter, one operation at a time.
- **FR-003**: System MUST migrate diagnostic commands (Menu 116-123) to use `mistapi.websockets` via the adapter, one operation at a time.
- **FR-004**: System MUST produce identical user-facing output (prompts, tables, error messages) after migration.
- **FR-005**: System MUST handle connection failures, timeouts, and reconnection at least as robustly as current custom code.
- **FR-006**: System MUST support coexistence of old and new WebSocket implementations during phased migration.
- **FR-007**: System MUST remove all custom WebSocket code (`src/websocket/`) after all operations are verified migrated.
- **FR-008**: System MUST remove `websocket-client` from dependencies after cleanup.
- **FR-009**: System MUST require `mistapi >= 0.61.0` and fail with a clear message if an older version is detected.
- **FR-010**: System MUST skip migration for operations that are in scope for `device-utils-adoption` (those ops will use `device_utils` instead of direct WS).

### Key Entities

- **Adapter**: Wraps `mistapi.websockets.sites.DeviceCmdEvents`, translates between SDK event model and current `WebSocketManager` result format.
- **WebSocketManager** (current): Custom class in `src/websocket/manager.py` managing raw `websocket-client` connections, message routing, result collection.
- **DeviceCmdEvents** (target): Official SDK class providing auto-reconnect, bounded queues, binary frame handling, thread-safe operation.
- **Menu Operation**: A numbered menu entry (102-123) that sends a command to a device via WebSocket and displays results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 22 menu operations (102-123) produce output identical to pre-migration baseline when run against the same device.
- **SC-002**: Custom WebSocket code reduced from ~3,008 lines to 0 lines (adapter layer excluded from count).
- **SC-003**: `websocket-client` dependency removed from `requirements.txt`.
- **SC-004**: No user-reported regressions in WebSocket operations within 2 weeks of deployment.
- **SC-005**: Connection recovery time (after disconnect) is equal to or faster than current custom implementation.
- **SC-006**: Each migration phase (adapter, show commands, diagnostics, cleanup) can be deployed independently without breaking other phases.

## Assumptions

- `mistapi >= 0.61.0` is available and stable (currently at 0.61.4+).
- `mistapi.websockets.sites.DeviceCmdEvents` provides sufficient control for all current show/diagnostic command patterns.
- The `device-utils-adoption` spec will identify which operations migrate there instead of using direct WS — those are excluded from this spec.
- Binary frame handling in `mistapi.websockets` (v0.61.1) covers all binary payloads currently handled by custom code.
- Thread safety guarantees in `mistapi.websockets` (v0.61.3 locks + `_finished` event) are sufficient to replace custom threading logic.
- The adapter layer will be thin (~200-400 lines) — not a rewrite of the custom code.
- Baseline output captures will be taken before migration begins for diff-based regression testing.
- SSH/container EOF handling in menu operations is unaffected (it's above the WebSocket layer).
