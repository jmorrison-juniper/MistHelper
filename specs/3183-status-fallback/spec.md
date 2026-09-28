# Feature Specification: Status Fallback for Quiet Operation Streams

**Feature Branch**: `fix/3183-status-fallback`

**Created**: 2026-09-23

**Status**: Draft

**Input**: User description: "Fix issue #3183. A running row must ask the status route when the stream closes or stays silent."

## User Scenarios & Testing

### User Story 1 - Recover a Quiet Run (Priority: P1)

An operator starts an operation. If the event stream stops or goes silent before a terminal event arrives, the page asks the server for the run status.

**Why this priority**: The operator must not wait 210 seconds when the server already knows that the run finished.

**Independent Test**: Simulate a running stream with no terminal event. Verify that the page calls `/api/operations/status/<run_id>` and marks the run complete.

**Acceptance Scenarios**:

1. **Given** a run is active, **When** the event stream reports an error or closes, **Then** the page asks the status route for the same run.
2. **Given** a run is active, **When** no stream event arrives during the silence window, **Then** the page asks the status route for the same run.
3. **Given** the status route reports `completed`, **When** the fallback reads it, **Then** the badge changes to `Complete` and the run controls reset.

### Edge Cases

- If the status route reports `running`, the page must arm another fallback check.
- If the operator starts another run, an old fallback timer must not update the new run.
- If the status route fails, the page must show a clear connection error.

## Requirements

### Functional Requirements

- **FR-001**: The page MUST call `/api/operations/status/<run_id>` when a stream closes or errors before a terminal event.
- **FR-002**: The page MUST call the status route when a stream stays silent during the fallback window.
- **FR-003**: The page MUST cancel old fallback timers when a run finishes or a new stream starts.
- **FR-004**: The page MUST apply completed and failed status route answers to the same UI paths as stream terminal events.
- **FR-005**: A regression test MUST fail if no silence fallback exists.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A quiet running stream causes a status route check within 20 seconds.
- **SC-002**: A completed status route answer changes the badge to `Complete` in one fallback cycle.
- **SC-003**: The fallback does not poll more than once per silence window for one active run.

## Assumptions

- The server status route already reports accurate terminal states.
- The browser can use the existing status route without a new API.
- A 15 second silence window is fast enough for operators and light enough for the server.
