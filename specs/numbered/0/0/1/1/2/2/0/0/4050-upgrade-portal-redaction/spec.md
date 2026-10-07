# Feature Specification: Upgrade Portal Log Redaction

**Feature Branch**: `fix-4050-upgrade-portal-redaction`

**Created**: 2026-10-06

**Status**: Approved

**Input**: Issue #4050 requires the upgrade portal logging boundary to redact credential-shaped text.

## User Scenarios and Testing

### User Story 1 - Protect upgrade portal logs (Priority: P1)

As an operator, I need portal logs to redact credential-shaped text so a failure cannot write sensitive data.

**Why this priority**: The package logger owns a handler that bypasses every ancestor redaction filter.

**Independent Test**: Emit an exception message through the package logger. The handler must redact the marker.

**Acceptance Scenarios**:

1. **Given** credential-shaped exception text, **When** the package logger emits it, **Then** the output contains the redaction placeholder.
2. **Given** an ordinary portal message, **When** the same logger emits it, **Then** the output keeps the message and context fields.
3. **Given** repeated application builds, **When** logging configuration runs, **Then** the package has one portal handler.

### User Story 2 - Repair false logging coverage (Priority: P1)

As a maintainer, I need a test of the installed logging path so a missing filter cannot report success.

**Why this priority**: Eighty-six existing logging tests passed while the portal handler emitted synthetic credential-shaped text unchanged.

**Independent Test**: Remove the handler filter. The focused test must fail because the synthetic marker reaches output.

**Acceptance Scenarios**:

1. **Given** the current unprotected handler, **When** the focused test runs, **Then** the test fails.
2. **Given** the repaired handler, **When** the focused test runs, **Then** it reports two examined lines and passes.
3. **Given** unreadable or missing output, **When** the focused test runs, **Then** the test fails.

### Edge Cases

- The filter must not remove an ordinary diagnostic message.
- The filter must retain the run and site fields.
- The test must use an obvious synthetic marker.
- The test must not include captured output in an assertion message.
- The package logger must keep propagation disabled.

## Requirements

### Functional Requirements

- **FR-001**: The portal handler MUST install `SensitiveFilter`.
- **FR-002**: The package logger MUST keep `propagate = False`.
- **FR-003**: The focused test MUST emit through `src.interfaces.portals.upgrade_portal`.
- **FR-004**: The focused test MUST use exception text with a synthetic credential-shaped marker.
- **FR-005**: The focused test MUST prove that the marker is absent and the redaction placeholder is present.
- **FR-006**: The focused test MUST prove that an ordinary message and both context fields remain.
- **FR-007**: The focused test MUST report a nonzero examined line count.
- **FR-008**: The change MUST NOT edit the root logger configuration or contested upgrade files.
- **FR-009**: The change MUST add one release-note fragment for issue #4050.
- **FR-010**: The change MUST use only the three routed specification files.

## Key Entities

- **Package logger**: The `src.interfaces.portals.upgrade_portal` logger.
- **Portal handler**: The named stream handler that owns the portal format and context filter.
- **SensitiveFilter**: The existing shared filter that replaces credential-shaped values.
- **Synthetic marker**: An obvious test-only value that cannot be mistaken for a real credential.

## Success Criteria

- **SC-001**: The red proof fails before the product repair.
- **SC-002**: The focused test passes after `SensitiveFilter` is installed.
- **SC-003**: The focused test examines exactly two output lines.
- **SC-004**: The ordinary output retains its message, run field, and site field.
- **SC-005**: All required local gates pass.

## Assumptions

- The portal keeps its package handler because the root format lacks portal context fields.
- Propagation would create duplicate output and would not apply a root logger filter to descendant records.
- The existing `SensitiveFilter` is the approved redaction implementation for this issue.
