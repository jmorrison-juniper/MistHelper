# Feature Specification: Long packet streams

**Feature Branch**: `jmorrison-juniper-long-packet-streams`

**Created**: 2026-10-01

**Status**: Specified

**Input**: [Issue #3575](https://github.com/jmorrison-juniper/MistHelper/issues/3575)
requires packet captures longer than 60 seconds on the WebSockets tab.

## User Scenarios & Testing

### User Story 1 - Choose the capture duration (Priority: P1)

An operator chooses a duration from 60 through 3600 seconds.
The selected card continues to show packet records after 60 seconds.

**Why this priority**: The existing 60-second limit prevents an operator from
observing a fault that occurs later.

**Independent Test**: Start a 120-second capture through the existing tab.
Verify records at 59, 61, and 119 seconds with a controlled clock.

**Acceptance Scenarios**:

1. **Given** a valid target, **When** the operator selects 60 or 3600 seconds,
   **Then** the tab accepts the duration.
2. **Given** a 3600-second capture, **When** a record arrives at 3599 seconds,
   **Then** the card shows that record.
3. **Given** an invalid duration, **When** the operator starts the capture,
   **Then** the tab refuses the request before any capture action.

### User Story 2 - Receive the first packet records (Priority: P1)

The tab confirms the stream subscription before it starts the capture.
It retains matching records that arrive before the start response.

**Why this priority**: A missing first record can hide the cause of a fault.

**Independent Test**: Delay the subscription confirmation and the start response
independently. Verify the action order and the first matching record.

**Acceptance Scenarios**:

1. **Given** an open connection without confirmation, **When** the tab waits,
   **Then** it sends no capture request.
2. **Given** confirmation for the selected scope, **When** the tab starts,
   **Then** it starts exactly one capture.
3. **Given** another scope or capture identifier, **When** records arrive,
   **Then** the selected card excludes those records.

### User Story 3 - Stop and release the capture (Priority: P1)

An operator can stop the capture before the selected duration ends.
The tab checks the active capture identifier before it sends the cloud stop.
The tab releases the connection and all owned helper threads.

**Why this priority**: A stream disconnect alone does not stop the cloud capture.

**Independent Test**: Stop through the existing controller.
Verify one matching cloud stop, the response state, and zero owned resources.

**Acceptance Scenarios**:

1. **Given** a matching active capture, **When** the operator presses Stop,
   **Then** the tab sends one cloud stop and reports its result.
2. **Given** a different active capture, **When** the operator presses Stop,
   **Then** the tab sends no cloud stop and reports the identity conflict.
3. **Given** a stop failure, **When** the cloud refuses the action,
   **Then** the card reports failure instead of a successful stop.
4. **Given** a stop before capture start, **When** the subscription completes,
   **Then** the tab does not start a capture.

### Edge Cases

- Reject fractional, negative, Boolean, Unicode-digit, and oversized durations.
- Keep the default duration at 60 seconds when the request omits it.
- Refuse subscription failures and subscription timeouts without a capture start.
- Keep one capture start across repeated subscription confirmations.
- Retain immediate matching records in a bounded buffer until the identifier arrives.
- Treat a matching capture-end record as completion, not a transport failure.
- Report an unexpected disconnect or an uncertain start explicitly.
- Preserve the idle stop, session limit, message caps, and ended-session retention.
- Preserve the regional host, authentication, target checks, and safety flags.
- Preserve the packet length ceiling of 1536 bytes.

## Requirements

### Functional Requirements

- **FR-001**: The tab MUST accept whole durations from 60 through 3600 seconds.
- **FR-002**: The server and the form MUST refuse invalid durations before capture start.
- **FR-003**: The tab MUST confirm the correct subscription before capture start.
- **FR-004**: The card MUST receive matching records throughout the selected duration.
- **FR-005**: The tab MUST correlate records with both the scope and the capture identifier.
- **FR-006**: The tab MUST preserve immediate records within explicit message and byte caps.
- **FR-007**: An early stop MUST check the active identifier and send the matching cloud stop once.
- **FR-008**: A failed or uncertain start or stop MUST produce an explicit failure state.
- **FR-009**: Completion, stop, disconnect, timeout, and error MUST release owned stream resources.
- **FR-010**: The change MUST preserve other streams, safety checks, authentication, and regional routing.
- **FR-011**: Captures MUST preserve the existing session, memory, packet, and rate limits.
- **FR-012**: Tests MUST use local fixtures only and MUST prove the failure paths.

### Key Entities

- **Capture request**: The checked target, filter, packet limits, and duration.
- **Capture session**: The existing card state, bounded records, and counters.
- **Capture identity**: The private scope and identifier that permit record delivery and cloud stop.
- **Capture connection**: One authenticated regional stream owned by one capture session.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both duration boundaries pass, and every required invalid-duration case fails.
- **SC-002**: Records at 59, 61, 119, and 3599 seconds reach the actual card.
- **SC-003**: Every start follows confirmation for its own subscription.
- **SC-004**: Repeated confirmations and reconnects produce exactly one capture start.
- **SC-005**: An early stop produces one matching cloud stop and no unrelated stop.
- **SC-006**: Each tested terminal path leaves zero owned connections or running helper threads.
- **SC-007**: The new capture package reaches at least 80 percent test coverage.

## Assumptions

- A capture can end earlier when it reaches the selected packet limit.
- Existing capture permissions and safety classifications remain authoritative.
- Site captures and organization Mist Edge captures retain their existing scopes.
- No menu operation, database schema, dependency, or environment variable changes.
- Publication requires an explicit parent grant after the preceding issue's verified main result.
- Live Mist actions, production data, stores, containers, and firmware actions remain unauthorized.
