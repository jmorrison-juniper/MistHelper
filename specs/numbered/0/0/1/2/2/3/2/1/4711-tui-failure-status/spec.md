# Feature Specification: TUI completion reporting

**Feature Branch**: `jmorrison-juniper-tui-completion-reporting`

**Created**: 2026-11-09

**Status**: Approved for implementation

**Input**: Issue #4711 requires accurate completion reporting after a TUI failure.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report the actual result (Priority: P1)

An operator receives an error report after a TUI failure, without a success report.
The operator can then continue at the main menu.

**Why this priority**: A success report after a failure gives the operator incorrect information.

**Independent Test**: Simulate a failure without external connections and examine the result messages.

**Acceptance Scenarios**:

1. **Given** a ready session, **When** the TUI fails, **Then** the launcher reports the error and returns to the menu without success.
2. **Given** a ready session, **When** the TUI returns normally, **Then** the launcher reports success once and returns to the menu.
3. **Given** a ready session, **When** the operator interrupts the TUI, **Then** the launcher reports the interruption and returns without success.

### Edge Cases

- Console logging returns after normal completion, failure, and interruption.
- Debug mode preserves the timestamp and menu return message.
- A failed session initialization does not start the TUI or report success.
- Repeated launches do not retain the result of a previous launch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The launcher MUST report success only after a normal TUI return.
- **FR-002**: The launcher MUST preserve the error report and exception details after a failure.
- **FR-003**: The launcher MUST restore console logging before the menu return message.
- **FR-004**: The launcher MUST preserve the interruption report without treating an interruption as a failure.
- **FR-005**: The launcher MUST preserve session initialization behavior and the return value.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each simulated failure produces one fatal error report and zero success reports.
- **SC-002**: Each normal completion produces one success report.
- **SC-003**: Each simulated interruption produces one interruption report and zero fatal error or success reports.
- **SC-004**: All three completion paths restore console logging and produce one menu return message.
- **SC-005**: Verification makes zero external connections and starts zero real TUI sessions.

## Assumptions

- An interruption is a user stop, not a successful TUI completion.
- The launch method continues to return no value.
- Only the reserved source, new test, release note, and issue-specific records can change.
- Existing tests owned by draft #4358 remain unchanged.
- The user requires a local commit only, without deployment or remote writes.
