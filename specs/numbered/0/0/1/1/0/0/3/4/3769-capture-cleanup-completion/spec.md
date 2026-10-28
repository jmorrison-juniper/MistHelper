# Feature Specification: Capture cleanup completion

**Feature Branch**: `jmorrison-juniper-fix-3769-capture-cleanup-completion`

**Created**: 2026-10-26

**Status**: Accepted

**Input**: Issue #3769 requires a deterministic cleanup-order proof and terminal notification after cleanup.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report stop after cleanup (Priority: P1)

An operator stops a packet capture. The session reports completion only after the matching capture cleanup ends.

**Why this priority**: A terminal session must not imply that cloud cleanup finished while that cleanup still runs.

**Independent Test**: Hold matching cleanup at a barrier. Check that no terminal notification occurs before release.

**Acceptance Scenarios**:

1. **Given** a matching site or organization capture, **When** cleanup waits at a barrier, **Then** the session has no terminal result.
2. **Given** successful matching cleanup, **When** cleanup returns, **Then** the session reports one stopped result.
3. **Given** a different active capture, **When** the operator stops this session, **Then** cleanup does not delete the different capture.

### User Story 2 - Report cleanup failure (Priority: P1)

An operator receives an explicit failure when cleanup raises an exception.

**Why this priority**: A stopped result must not hide cleanup failure.

**Independent Test**: Make cleanup raise an exception and check the final result and error log.

**Acceptance Scenarios**:

1. **Given** a stop request, **When** cleanup raises an exception, **Then** the session reports one failed result and logs the failure.
2. **Given** an execution failure, **When** cleanup succeeds, **Then** the session preserves the existing execution-failure classification.

### Edge Cases

- Stop occurs before the trigger returns.
- Execution fails after a capture identifier becomes available.
- Stream close raises an exception.
- The active capture identifier does not match.
- A command completes normally or without output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Terminal notification MUST follow the cleanup attempt for every utility execution path.
- **FR-002**: Successful cleanup MUST preserve existing terminal states and reasons.
- **FR-003**: Cleanup exceptions MUST produce an explicit failed result, including during operator stop.
- **FR-004**: Cleanup MUST retain the current capture scope and identifier checks.
- **FR-005**: Existing assertions, timeouts, test memberships, and the separate #3575 behavior MUST remain unchanged.
- **FR-006**: A deterministic barrier test MUST fail on unchanged production source before the repair.

### Key Entities

- **Utility session**: One execution, its stop request, and its terminal notification.
- **Capture identity**: The scope and identifier returned by the capture trigger.
- **Cleanup attempt**: Stream closure and the existing conditional capture stop.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No terminal notification occurs while the deterministic cleanup barrier remains closed.
- **SC-002**: Each tested execution produces exactly one terminal result after cleanup.
- **SC-003**: Each tested cleanup exception produces a failed result and an error record.
- **SC-004**: A different capture receives zero deletion requests.

## Assumptions

- The existing transport and Mist SDK request paths remain unchanged.
- Tests use only controlled local collaborators and loopback fixtures.
- Cleanup failure takes precedence over an execution result because cleanup completion remains unknown.
- The existing live utility test remains read-only.
- This change adds no interface controls, credentials, storage, or capture-duration policy.
