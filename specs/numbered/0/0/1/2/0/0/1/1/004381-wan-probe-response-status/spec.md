# Feature Specification: WAN Probe Response Status

**Feature Branch**: `jmorrison-juniper-fix-4381-wan-probe-rejected-config`

**Created**: 2026-10-23

**Status**: Draft

**Input**: Issue #4381: Reject a device configuration response when Mist returns HTTP 403, even if its body contains usable-looking port settings.

## User Scenarios & Testing

### User Story 1 - Reject a refused device configuration (Priority: P1)

An operator applies WAN probe overrides to a gateway. Mist refuses the device configuration request but returns a body that looks usable. The operation must report a failure and must not submit an update.

**Why this priority**: A refused read must not lead to a device change based on an error body.

**Independent Test**: Use a mocked HTTP 403 response with plausible port settings. Confirm that the operation reports the refused status and does not call the device update.

**Acceptance Scenarios**:

1. **Given** a mocked HTTP 403 response with plausible port settings, **When** the operator applies the override, **Then** the operation reports a failure with status 403 and does not submit an update.
2. **Given** a mocked HTTP 200 response with valid port settings, **When** the operator applies the override, **Then** the operation continues and records the successful update.

### Edge Cases

- If the response body is valid but the status is not 200, reject the body before reading its configuration.
- If the SDK call raises an exception, preserve the existing error result.

## Requirements

### Functional Requirements

- **FR-001**: The operation MUST accept device configuration only when Mist returns HTTP 200.
- **FR-002**: The operation MUST reject a non-200 response even when its body contains plausible device configuration.
- **FR-003**: The operation MUST report the rejected HTTP status and MUST NOT submit a device update.
- **FR-004**: The operation MUST continue to accept valid HTTP 200 configuration responses.
- **FR-005**: The operation MUST preserve its existing handling of exceptions from the SDK call.

### Mist Cloud Response Requirements

- The existing `getSiteDevice` SDK method remains the only method used to read device configuration.
- The response status and parsed body are separate values. Tests MUST prove that a rejected status cannot pass through its parsed body.
- Tests MUST use mocked SDK responses and MUST make no Mist Cloud or production-device calls.
- The change MUST preserve SDK authentication, endpoint selection, output behavior, and secret handling.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every mocked non-200 device configuration response produces a failed result and zero update requests.
- **SC-002**: A mocked HTTP 200 device configuration response still completes the existing success path.
- **SC-003**: Existing SDK exception results remain unchanged.

## Assumptions

- The Mist SDK response exposes `status_code` even when it parses a response body for an HTTP error.
- HTTP 200 is the successful status for this existing operation.
- A failed device configuration read uses the operation's existing failed-result format.
