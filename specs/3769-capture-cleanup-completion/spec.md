# Feature Specification: Capture Cleanup Completion

**Feature Branch**: `jmorrison-juniper-capture-cleanup-completion` (existing branch, unchanged)

**Created**: 2026-10-03

**Status**: Implemented locally. Publication remains held.

**Input**: Issue #3769. Base commit: `d4d1110352eeab3d9f9d483242232c12f6de4d2d`.

## User Scenarios & Testing

### User Story 1 - Accurate utility completion (Priority: P1)

An operator needs the utility run to report a final result only after stream and capture cleanup finish.

**Why this priority**: An early success result can hide a cleanup failure and leave an active capture.

**Independent Test**: Hold cleanup at a controlled local barrier. Confirm that no terminal result appears until cleanup resolves.

**Acceptance Scenarios**:

1. **Given** a utility run finishes normally, **When** stream close resolves, **Then** the run reports its existing normal result without cloud stop.
2. **Given** cleanup is still blocked, **When** the run reaches its normal finish point, **Then** no terminal result appears before cleanup resolves.
3. **Given** the operator stops the run and cleanup succeeds, **When** cleanup resolves, **Then** the run retains its existing stopped result.

### User Story 2 - Visible cleanup failure (Priority: P1)

An operator needs a cleanup error to appear as a failed run, including when the operator requested the stop.

**Why this priority**: A stopped result must not hide a failed stream close or capture cleanup.

**Independent Test**: Cause each cleanup operation to fail, both during normal completion and operator stop, then inspect the final run result.

**Acceptance Scenarios**:

1. **Given** stream-client close fails, **When** matching capture cleanup succeeds, **Then** capture cleanup is still attempted and the final result is `FAILED`.
2. **Given** capture lookup or deletion fails, **When** the run reaches its terminal point, **Then** the final result is `FAILED`.
3. **Given** the operator stops the run and either cleanup operation fails, **When** cleanup resolves, **Then** the final result is `FAILED`, not a successful stopped result.

### User Story 3 - Safe capture selection (Priority: P1)

An operator needs a stopped utility to affect only the capture started by that utility.

**Why this priority**: Cleanup must not stop another site's or organization's capture.

**Independent Test**: Return a different capture identifier, or no matching capture, and verify that cleanup does not delete it.

**Acceptance Scenarios**:

1. **Given** the capture lookup returns the utility's capture identifier in its original scope, **When** cleanup runs, **Then** only that matching capture is stopped.
2. **Given** the lookup returns no matching capture, **When** cleanup runs, **Then** no delete occurs and cleanup does not create a failure.
3. **Given** the operator stops the run while its trigger is in progress, **When** the trigger returns a capture identity, **Then** cleanup uses that identity and its original scope before reporting the terminal result.

### Edge Cases

- Stream-client close fails while a matching capture needs a cloud stop.
- Capture lookup fails, so the system cannot confirm a matching capture.
- Capture deletion fails after lookup confirms a match.
- The trigger response contains no usable capture identifier.
- The trigger produces no matching capture, so no delete is required.
- The operator stops the run during trigger execution or stream monitoring.
- Cooperative cancellation sets `RunnerState.stopping`. A repeated cancellation during cleanup does not interrupt cleanup or create another terminal result.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST report a terminal result only after stream-client close and required capture cleanup have both resolved.
- **FR-002**: The system MUST attempt required capture cleanup even if stream-client close fails.
- **FR-003**: The system MUST report `FAILED` if stream-client close, capture lookup, or required capture deletion fails.
- **FR-004**: A cleanup failure MUST report `FAILED` even when the operator requested the stop. It MUST NOT report a successful `STOPPED` result.
- **FR-005**: The system MUST use the capture identifier returned by the utility trigger and preserve its site or organization scope.
- **FR-006**: The system MUST NOT delete a capture when lookup finds no matching identifier. A no-match result MUST remain a successful cleanup outcome.
- **FR-007**: The system MUST preserve subscribe-first behavior, cancellation handling, and existing terminal outcomes when cleanup succeeds.
- **FR-008**: Tests MUST cover successful cleanup, no match, GET failure, DELETE failure, client-close failure, stop during trigger, normal finish, and cancellation.
- **FR-009**: A controlled local barrier test MUST demonstrate the premature terminal result against the unmodified source once. The test MUST pass after the repair.
- **FR-010**: The new tests MUST provide at least 80 percent branch coverage for changed branches.
- **FR-011**: Source changes MUST stay in the three reserved utility runner modules. The new test MUST use `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`.
- **FR-012**: The existing utility test file MUST remain read-only. The change MUST NOT modify `captures/**`, fixtures, or dependency manifests.
- **FR-013**: Documentation MUST stay in this specification directory and `changelog.d/issue-3769-capture-cleanup-completion.md`.
- **FR-014**: HTTP status validation MUST reject unavailable or malformed status. Existing endpoint paths and capture data selection MUST remain unchanged.

### Mist Cloud Transport Requirements

This change adds no Mist Cloud transport or endpoint. Cleanup MUST retain the existing `mist_get` lookup and `mist_delete` operation for the utility's site or organization scope. Tests MUST verify matching-identifier selection, no-match behavior, and failure handling for both operations.

### Key Entities

- **Utility run**: One triggered operation with a stream, output, and final result.
- **Capture identity**: The identifier and site or organization scope returned for the utility's capture.
- **Cleanup result**: The resolved outcome of stream-client close and any required capture stop.
- **Terminal result**: The existing normal, stopped, or failed result reported for the utility run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In every tested run, no terminal result appears before stream-client close and required capture cleanup resolve.
- **SC-002**: Every tested client-close, GET, or DELETE failure produces exactly one `FAILED` result, including during operator stop.
- **SC-003**: The cleanup tests cover at least 80 percent of changed branches and pass for all required success, no-match, failure, stop, finish, and cancellation cases.
- **SC-004**: Tests confirm that cleanup never deletes a capture with a different identifier or scope.

## Assumptions

- A cleanup operation that is not required because no matching capture exists counts as resolved successfully.
- Existing terminal states and messages remain unchanged when cleanup succeeds.
- The feature directory and specification are the only files this request permits the specification task to create or modify.

## Authorized boundary decisions

The coordinator replaced the provisional utility test path with the existing `transport/clients/` directory. Its child count changes from three to four.
No existing test moves or changes. The private original barrier remains preserved at its original location.
The coordinator approved HTTP status validation only. Capture data selection and endpoint migration remain outside this repair.
`monitoring.py` receives the monitor completion timestamp. This preserves normal completion reasons when stream close takes additional time.
Cancellation means the existing operator stop event. This repair does not add asynchronous thread cancellation or intercept `BaseException`.
This bounded local task does not complete the release process. The user's explicit publication hold overrides the normal delivery steps.
