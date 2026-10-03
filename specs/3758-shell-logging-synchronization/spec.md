# Feature Specification: Shell Logging Synchronization

**Feature Branch**: `jmorrison-juniper-shell-logging-synchronization`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "Specify the test-only repair for issue #3758. The shell runner test can observe STOPPED before the terminal_outcome_completed log event reaches caplog. Wait for that exact event before taking the snapshot. Preserve the existing assertions and prove the wait helper with deterministic tests."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture the complete shell log (Priority: P1)

As a test maintainer, I need the shell-runner test to wait for its terminal log event before it reads captured logs.

**Why this priority**: The test currently reads an incomplete log snapshot and fails even when the shell operation completes.

**Independent Test**: Run the affected test while controlling when the real terminal log event is delivered.

**Acceptance Scenarios**:

1. **Given** the test observes STOPPED before `terminal_outcome_completed` reaches its `caplog` binding, **When** the test waits for the exact event, **Then** it takes the snapshot only after that event appears.
2. **Given** the complete log snapshot, **When** the existing checks run, **Then** they retain the expected 21 events, all field and length checks, and all secret checks.

### User Story 2 - Reject incomplete or unrelated logs (Priority: P2)

As a test maintainer, I need the wait helper to reject a missing event or an event from the wrong logger.

**Why this priority**: A bounded refusal proves that the helper does not accept unrelated or incomplete log output.

**Independent Test**: Exercise the actual helper with controlled real log delivery for the expected event, a wrong event, a wrong logger, and no event.

**Acceptance Scenarios**:

1. **Given** the expected event is delivered to the real `caplog` binding, **When** the helper checks that binding, **Then** it accepts only the exact event.
2. **Given** the event is missing or comes from the wrong event name or logger, **When** the existing two-second bound expires, **Then** the helper refuses completion within that bound.

### Edge Cases

- The expected event is present before the helper starts. The helper accepts it without waiting for the full bound.
- A wrong event or a matching event from another logger must not satisfy the wait.
- The expected event does not arrive. The helper refuses within the existing two-second bound.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The affected test MUST wait for the exact `terminal_outcome_completed` event on the real `caplog` binding before it takes the log snapshot.
- **FR-002**: The wait MUST use the existing bounded polling convention and the existing two-second bound. It MUST NOT use a fixed sleep as synchronization or increase the timeout.
- **FR-003**: The test MUST retain its original AST assertions, input assertions, call identities, event count, field checks, length checks, and secret checks.
- **FR-004**: A unique new deterministic test module MUST exercise the actual wait helper with controlled delivery before and after the real log event.
- **FR-005**: The helper test MUST prove bounded refusal for an unavailable event and reject wrong-event and wrong-logger controls.
- **FR-006**: The repair MUST remain test-only. It MUST NOT change runtime ordering, fixtures, policies, dependencies, baselines, stores, browser behavior, or containers.
- **FR-007**: The failure MUST be treated as a test synchronization defect, not as a secret leak or a runtime ordering defect.
- **FR-008**: Preserve one local commit and a private receipt for parent review. Do not push or publish a pull request without a separate grant.

### Key Entities

- **Terminal log event**: The `terminal_outcome_completed` event that the test must observe before it snapshots captured logs.
- **Captured log snapshot**: The records and events checked by the existing assertions, including the expected 21-event result.
- **Wait helper**: The existing or newly introduced test helper that accepts the expected event or refuses within the existing bound.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The affected shell-runner test takes its snapshot only after the exact terminal event appears on the real `caplog` binding.
- **SC-002**: The existing snapshot checks still validate 21 events, every original field and length, and every secret assertion.
- **SC-003**: Deterministic tests show that the helper accepts the expected event and rejects a missing event, a wrong event, and a wrong logger.
- **SC-004**: An unavailable event causes refusal within the existing two-second bound, without a longer timeout or fixed-sleep synchronization.
- **SC-005**: The repair changes no production runtime files or unrelated test inputs.
- **SC-006**: The private receipt records exact test memberships, unchanged assertions, gate failures, source identities, and the local delivery boundary.

## Assumptions

- The test observes STOPPED before the synchronous `terminal_outcome_completed` logger emission. This ordering creates the incomplete snapshot.
- The original main-run result is diagnostic evidence: 369 unique tests, 368 passed, one failed, zero skipped, zero errors, and 27.57 seconds. The failure produced a 20-event snapshot. The final report had 27 records and 21 events, with `terminal_outcome_completed` as the last new event.
- The implementation scope contains two runner test modules and this unique SpecKit directory. Shared files remain read-only.
- The change is test-only and does not need a release-note fragment.
- The parent permits a preservation commit with unchanged, out-of-scope gate failures. Record each failure without suppression or a passing claim.
