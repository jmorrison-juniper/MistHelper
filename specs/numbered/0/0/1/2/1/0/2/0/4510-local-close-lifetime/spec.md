# Feature Specification: Local close lifetime

**Feature Branch**: `jmorrison-juniper-shell-local-close-investigation`

**Created**: 2026-10-30

**Status**: Specified

**Input**: Repair the proven local-close lifetime defect for issue #4510. Keep all work local.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop an active terminal (Priority: P1)

An operator stops a shell or screen session while its reader waits for device output.
The session ends without waiting for an unrelated connection.

**Why this priority**: A session that remains live prevents the operator from knowing whether the stop completed.

**Independent Test**: Stop an active reader while unrelated connections reuse released resources.

**Acceptance Scenarios**:

1. **Given** a live shell with an active read, **When** the operator stops it, **Then** it becomes stopped within two seconds.
2. **Given** a live screen with an active read, **When** the operator stops it, **Then** it becomes stopped within 2.5 seconds.
3. **Given** a failed shell write, **When** local closure interrupts a read, **Then** the session becomes failed with the existing write-failure reason.

### Edge Cases

- Close before open and repeated close remain safe.
- A read that starts after closure receives a local-close result.
- A partial frame does not prevent local closure.
- Normal remote close, keepalive, and subscription behavior remain unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Local closure MUST interrupt active reads before releasing resources that those reads still use.
- **FR-002**: New reads MUST NOT use resources after local closure starts.
- **FR-003**: Shell, screen, and event-stream connections MUST follow the same lifetime rule.
- **FR-004**: The repair MUST preserve existing final states, reasons, timeouts, authentication, and output.
- **FR-005**: Regression tests MUST fail before the repair without an external service or production credential.

### Mist Cloud Transport Requirements

This repair changes no Mist request, endpoint, credential, or SDK contract.
It preserves the existing owned WebSocket transport and its exact terminal-byte output.
The existing transport and SDK contract tests remain authoritative.

### Key Entities

- **Active read**: An operation that still uses connection resources.
- **Local closure**: A request that interrupts reads and prevents later resource access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every controlled shell and screen stop reaches its expected state within its existing test bound.
- **SC-002**: A failed shell write retains the existing failure reason.
- **SC-003**: Existing live-transport tests pass without assertion or timeout changes.

## Assumptions

- The native descriptor-reuse reproduction proves a reachable lifetime defect, not the exact schedule of every prior failure.
- The repair remains local. PR #4503 and umbrella issue #1794 remain held.
- No reader join or public stop contract change is required.
