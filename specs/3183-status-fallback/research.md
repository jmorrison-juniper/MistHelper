# Research: Status Fallback for Quiet Operation Streams

## Decision: Use the existing status route

Rationale: The status route already returns completed and failed states. The browser can recover without a new API.

Alternatives considered: Adding a new stream endpoint was rejected because the defect is the browser recovery path.

## Decision: Add a silence timer

Rationale: A stream can stay open without terminal events. A timer detects that state and asks the server.

Alternatives considered: Only using `EventSource.onerror` was rejected because a quiet stream can leave the browser waiting.

## Decision: Use one timer for the active run

Rationale: One active timer limits status calls and prevents old runs from updating the new run.

Alternatives considered: A fixed polling loop was rejected because it adds avoidable server load.
