# Feature Specification: Block child submission after a multi-site cancel

**Issue**: #3327
**Feature Branch**: `fix/3327-cancel-race`
**Status**: Implemented

## Problem

A cancel request can run while another request holds the parent submission
claim. The cancel marks each planned child job as `unavailable`, because no
cloud job identifier exists yet.

The live submission then claims a planned child job and sends the cloud write.
A second cancel skips that child, because it already holds the `unavailable`
result from the first cancel.

## User Story 1: A cancel blocks each later child claim

**Acceptance scenarios**:

1. **Given** a live parent submission claim, **When** a cancel request stores
   the cancellation marker before a planned child claim, **Then** the
   submission sends no cloud write for that child or any later child.
2. **Given** an operation that already holds a cancellation marker, **When** a
   new submission request starts, **Then** the service refuses the parent
   submission claim.
3. **Given** a child submission claim that wins before the cancel marker,
   **When** its result later supplies a cloud job identifier, **Then** a second
   cancel can reach that cloud job.

## Functional requirements

- **FR-001**: The parent submission claim must read the durable cancellation
  marker in the same compare-and-set decision.
- **FR-002**: Each child submission claim must read the durable cancellation
  marker in the same compare-and-set decision.
- **FR-003**: A cancellation marker that wins the child claim race must stop
  that child and all later child writes.
- **FR-004**: A second cancel may replace an `unavailable` child result only
  after the child holds a cloud job identifier.
- **FR-005**: A second cancel must not repeat a claimed, completed, or unknown
  cancellation request.

## Success criteria

- **SC-001**: A deterministic concurrency test proves the order: parent claim,
  cancel marker, child claim, and no cloud write.
- **SC-002**: A regression test proves that a second cancel reaches a cloud
  job that became known after the first cancel.
- **SC-003**: The aggregate service unit tests pass.
