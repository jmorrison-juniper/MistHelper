# Feature Specification: Stale Portal Response Ownership

**Feature Branch**: `jmorrison-juniper-fix-stale-portal-warning-race`

**Created**: 2026-10-13

**Status**: Implemented

**Input**: Issue #4040: Menu 241 SSH-only warning remains visible after another operation is selected.

## User Scenarios & Testing

### User Story 1 - Keep guidance with the selected operation (Priority: P1)

An operator selects an operation and sees only guidance for that operation, even when an earlier request finishes later.

**Why this priority**: Stale guidance can mislead an operator about the selected operation.

**Independent Test**: Delay the response for menu 241, select menu 242, then allow the earlier response to finish.

**Acceptance Scenarios**:

1. **Given** menu 241 is selected and its response is pending, **When** the operator selects menu 242 and the menu 241 response succeeds, **Then** the title remains Menu 242 and the menu 241 warning stays hidden.
2. **Given** menu 241 is selected and its response is pending, **When** the operator selects menu 242 and the menu 241 response fails, **Then** the menu 242 state shows no error from menu 241.
3. **Given** menu 241 remains selected, **When** its response identifies an SSH-only operation, **Then** the SSH-only warning appears for menu 241.

### Edge Cases

- A delayed response must not hide or replace the loading state of the selected operation.
- A delayed failure must not show an error after the operator selects another operation.
- A current SSH-only response must retain its warning.

## Requirements

### Functional Requirements

- **FR-001**: The page MUST apply parameter results only while the requested operation remains selected.
- **FR-002**: The page MUST ignore a successful result when another operation is selected.
- **FR-003**: The page MUST ignore a failure when another operation is selected.
- **FR-004**: The page MUST show the SSH-only warning when the selected operation requires SSH access.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In every delayed-success test, the selected title remains Menu 242 and the menu 241 warning is hidden.
- **SC-002**: In every delayed-failure test, the selected operation shows no error from menu 241.
- **SC-003**: In every current-selection test, menu 241 still shows its SSH-only warning.

## Assumptions

- The most recently selected operation owns the visible operation panels.
- An operation response can arrive after the operator selects another operation.
- The repair does not change Mist cloud data or operation execution behavior.
