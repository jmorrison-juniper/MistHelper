# Feature Specification: Capture cleanup completion

**Feature Branch**: `jmorrison-juniper-fix-3769-capture-cleanup-order`

**Created**: 2026-10-26

**Status**: Specified

**Input**: Issue #3769 requires a deterministic proof and repair of premature terminal notification during capture cleanup.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report completion after cleanup (Priority: P1)

An operator stops a capture. The session reports completion only after the matching capture cleanup ends.

**Why this priority**: A premature completion report can leave a capture active when the operator expects it to stop.

**Independent Test**: Block capture cleanup with an event. Confirm that no terminal notification occurs before the event permits cleanup.

**Acceptance Scenarios**:

1. **Given** a matching site capture, **When** cleanup blocks, **Then** the session has no terminal notification.
2. **Given** a matching organization capture, **When** cleanup succeeds, **Then** the session reports stopped after the matching deletion.
3. **Given** a different capture identifier, **When** the operator stops the session, **Then** the system does not delete that capture.

### User Story 2 - Report cleanup failure (Priority: P1)

An operator sees an explicit failure when capture cleanup raises an exception, rather than a successful stop report.

**Why this priority**: An operator must know when the capture can remain active.

**Independent Test**: Make the controlled cleanup request raise an exception. Confirm one failed terminal notification and a safe error message.

**Acceptance Scenarios**:

1. **Given** a stopped capture, **When** its cleanup request raises an exception, **Then** the session reports failure exactly once.
2. **Given** a utility execution error, **When** cleanup succeeds, **Then** the session preserves the existing execution error outcome.

### Edge Cases

- Stop occurs before the trigger returns its capture identifier.
- Cleanup finds no matching capture or no capture identifier.
- A command utility finishes, times out, or fails without capture cleanup.
- Stream close raises an exception.
- The cleanup request raises an exception after an execution error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Publish a terminal outcome only after stream close and required matching capture cleanup complete.
- **FR-002**: Preserve capture scope and identifier checks. Never delete an unrelated capture.
- **FR-003**: Publish one explicit failed outcome when cleanup raises an exception. Do not report a successful stop.
- **FR-004**: Preserve existing normal, timeout, execution error, and operator-stop outcomes when cleanup succeeds.
- **FR-005**: Prove the ordering defect with a deterministic barrier that fails against unchanged production source.
- **FR-006**: Preserve existing assertions, timeouts, test memberships, and the separate #3575 long-capture behavior.
- **FR-007**: Use controlled test services only. Make no production cloud request.

### Mist Cloud Transport Requirements

This repair changes lifecycle ordering only. It adds no REST endpoint, SDK method, authentication rule, or owned transport.
Existing capture cleanup uses the SDK session methods `mist_get` and `mist_delete`.
Existing transport contract tests remain unchanged.

### Key Entities

- **Utility session**: One execution, its output, its stop request, and its terminal outcome.
- **Capture identity**: The capture identifier and site or organization scope returned for that execution.
- **Cleanup completion**: The boundary after stream close and the required capture cleanup attempt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both site and organization barrier cases show zero terminal notifications while cleanup remains blocked.
- **SC-002**: Each successful matching cleanup produces exactly one stopped notification after its deletion.
- **SC-003**: Each cleanup exception produces exactly one failed notification and no stopped notification.
- **SC-004**: Existing utility runner assertions remain unchanged and pass with the repaired lifecycle.

## Assumptions

- A terminal notification means lifecycle cleanup has completed or has explicitly failed.
- Existing cleanup exception behavior must remain visible, not become a success report.
- This repair does not reinterpret unsuccessful HTTP response bodies that the existing cleanup code does not validate.
- Existing run-duration limits and long-capture behavior remain outside this issue.
- PowerShell is unavailable on this host. The numeric route reproduces the eight-digit base-5 algorithm in `spec-route.ps1`.
- The existing app-managed branch replaces the branch-creation hook. The shared feature pointer remains unchanged.
