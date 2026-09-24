# Feature Specification: Clear Stale Operation Results

**Feature Branch**: `fix/3154-stale-result-panel`

**Created**: 2026-09-23

**Status**: Draft

**Input**: User description: "Fix issue #3154. Selecting a new operation must clear the previous execution panel without revealing an empty panel."

## User Scenarios & Testing

### User Story 1 - Select Another Operation (Priority: P1)

An operator runs one operation, sees a result table, and then selects another operation. The page must clear the old result before the operator starts a new run.

**Why this priority**: A stale result can make the operator trust data from the wrong operation.

**Independent Test**: Show a finished result, select another operation, and verify that the old table and file list disappear.

**Acceptance Scenarios**:

1. **Given** a completed run shows output files and result rows, **When** the operator selects another operation, **Then** the page clears the old files, rows, logs, progress, and status.
2. **Given** no run started for the new operation, **When** the operator selects a command-line operation, **Then** the page does not reveal an empty execution panel.

---

### Edge Cases

- If a result preview request finishes after the selection changes, the stale table must not become visible again.
- If the execution panel is already hidden, selection must keep it hidden.
- If no `OperationResults` object exists, selection must still clear the standard execution fields.

## Requirements

### Functional Requirements

- **FR-001**: The page MUST clear the execution fields when the operator selects a different operation.
- **FR-002**: The page MUST clear result rows, result summary text, output files, logs, debug logs, progress, and status together.
- **FR-003**: The page MUST NOT reveal `#executionPanel` only because the operator selected an operation.
- **FR-004**: The page MUST continue to reveal `#executionPanel` when a run starts, when an error appears, or when the operator reconnects to a run.
- **FR-005**: A regression test MUST fail if `selectOperation()` leaves a visible result table or output file from the prior run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: After selection, the previous result table is hidden within one browser event loop.
- **SC-002**: After selection, the output file list contains zero items.
- **SC-003**: Existing run-start paths still show the execution panel before status updates occur.
- **SC-004**: The regression test reports at least one checked stale-result scenario.

## Assumptions

- The prior no-output states in issue #3154 are covered by the existing silent-completion guard.
- This issue scope covers stale browser state, not missing server output for a completed run.
- The selection repair can stay in static JavaScript and Playwright tests.
