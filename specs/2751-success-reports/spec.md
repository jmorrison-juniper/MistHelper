# Feature Specification: Success Report Audit Slice

**Feature Branch**: `chore/2751-success-reports`

**Created**: 2026-09-17

**Status**: Draft

**Input**: GitHub issue #2751 asks for a bounded audit of success reports that can outrun the work.

## User Scenarios and Testing

### User Story 1 - Trust destructive write logs (Priority: P1)

A network operator reads the log for a destructive write of a WAN probe. The log must not say that the code updated a probe configuration before the Mist API returns.

**Why this priority**: A false success line can hide a failed configuration change.

**Independent Test**: Run the unit tests for WAN probe paths with a failed API response and assert with `caplog`.

**Acceptance Scenarios**:

1. **Given** a WAN probe for a template returns HTTP 500, **When** the preparation log appears, **Then** no `Updated` success line appears before the failed write.
2. **Given** a WAN probe for a device returns HTTP 500, **When** the preparation log appears, **Then** no `Updated` success line appears before the failed write.

### User Story 2 - Preserve required before-action logs (Priority: P2)

A maintainer reviews the audit change. The change must keep the required before-action log and only reword messages that claimed a result too early.

**Why this priority**: The repository requires an `info` log before each meaningful action.

**Independent Test**: Review `specs\2751-success-reports\triage.md` and run the focused tests.

**Acceptance Scenarios**:

1. **Given** a candidate contains a start message, **When** the message only announces an operation, **Then** the code keeps it unchanged.

## Edge Cases

- If an API write returns a non-200 status, the result object and the log keep the failure status visible.
- If the code only prepares a local payload, the log uses `Prepared` instead of `Updated`.
- If a candidate is a correct completion report after proof, the audit records it and does not change it.

## Requirements

### Functional Requirements

- **FR-001**: The audit MUST triage a bounded slice of the #1924 inventory before any repair.
- **FR-002**: The repair MUST keep the before-action announcement for each changed path.
- **FR-003**: The repair MUST remove success wording from logs that run before the Mist API proves the write.
- **FR-004**: Each changed message MUST use wording that matches the evidence available at that point.
- **FR-005**: Each repair MUST have a test that asserts the old success line is absent when the underlying write fails.
- **FR-006**: The work MUST defer the remaining #1924 candidates into follow-up issues with counts.

### Key Entities

- **Candidate success report**: A log or printed message from the #1924 inventory that contains a success or completion word.
- **Correct announcement**: A before-action log that states intent without claiming the result.
- **Premature success claim**: A message that says the work succeeded before the code proves it.
- **Correct completion report**: A message that appears after the code proves the result it reports.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The triage artifact classifies every candidate read into one of the three required shapes.
- **SC-002**: The two changed failure tests pass and prove that the old success lines are absent.
- **SC-003**: The body of the pull request states the triage counts, the repair wording, the deferred counts, and the test evidence.
- **SC-004**: Follow-up issues exist for all deferred areas.

## Assumptions

- This slice audits about 20 files by operator impact instead of all 582 candidates.
- The two messages about WAN probe preparation are destructive-path messages because they support menu 166 and menu 167.
- No live call to the Mist API is necessary. Unit tests use local doubles.
