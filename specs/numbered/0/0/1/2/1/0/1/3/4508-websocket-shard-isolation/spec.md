# Feature Specification: Terminal Session Replay Isolation

**Feature Branch**: `jmorrison-juniper-fix-4508-websocket-shard-isolation`

**Created**: 2026-11-08

**Status**: Specified

**Input**: Investigate #4508 with offline evidence. Repair the session lifecycle only when evidence supports the cause. Preserve the serial review process.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Return to a shell (Priority: P1)

An operator returns to a shell after selecting another session. The terminal shows the stored output of the selected shell.

**Why this priority**: The operator must identify the selected shell before sending a command.

**Independent Test**: Start two fake shells. Select the first shell again and inspect its stored output.

**Acceptance Scenarios**:

1. **Given** two shell sessions, **When** the operator selects the first shell again, **Then** its stored banner appears.
2. **Given** a pending paste confirmation, **When** the operator selects another shell, **Then** the confirmation closes without sending the paste.

### Edge Cases

- A session changes before the previous output reaches the terminal.
- A terminal mount waits for the browser to complete a display update.
- An earlier test leaves a session, a server, or a browser callback active.
- A stored response arrives but the browser does not display its banner.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The selected shell MUST display its own stored output after a session change.
- **FR-002**: A pending paste MUST NOT reach a different session.
- **FR-003**: The investigation MUST distinguish stored output from visible output.
- **FR-004**: Each test MUST isolate its fake sessions and browser state.
- **FR-005**: A repair MUST have a failing control that demonstrates the cause.
- **FR-006**: Tests MUST use offline data and MUST NOT contact a production device.
- **FR-007**: The existing wait boundary MUST remain unchanged unless measured evidence requires a change.

### Key Entities

- **Shell session**: One selected device connection and its stored terminal output.
- **Pending paste**: Text that requires confirmation before delivery to its original shell.
- **Test lifecycle**: The setup, test, and cleanup of fake sessions and browser state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The focused session-change journey passes within the existing 15-second display boundary.
- **SC-002**: All 201 original tests and the added controlled case pass in the offline shard without a retry.
- **SC-003**: A controlled failure demonstrates the cause before a repair is accepted.
- **SC-004**: No pending paste byte reaches the other shell.

## Assumptions

- The reported defect is intermittent. One passing run does not establish a cause.
- The existing terminal behavior remains the contract.
- A missing reproduction or unavailable evidence blocks a speculative implementation.
- This change does not change production device commands or repository protection.
