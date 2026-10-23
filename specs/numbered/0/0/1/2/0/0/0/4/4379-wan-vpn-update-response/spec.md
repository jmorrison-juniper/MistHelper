# Feature Specification: WAN VPN Update Response

**Feature Branch**: `[4379-wan-vpn-update-response]`

**Created**: 2026-10-23

**Status**: Draft

**Input**: Issue #4379, WAN hub VPN updates must not report success after Mist rejects an update.

## User Scenarios & Testing

### User Story 1 - Trust VPN update results (Priority: P1)

An operator changes WAN hub VPN paths and needs the result message to match the result from Mist.

**Why this priority**: A false success message can lead an operator to believe that a production network change took effect.

**Independent Test**: Mock Mist responses for a rejected update and an accepted update, then verify the operator receives the correct outcome.

**Acceptance Scenarios**:

1. **Given** Mist rejects a VPN update with an HTTP error, **When** the operator submits the change, **Then** the tool reports a failure with the returned status and does not report updated paths.
2. **Given** Mist accepts a VPN update, **When** the operator submits the change, **Then** the tool reports the number of updated paths.

## Edge Cases

- If the response has no HTTP status, the tool reports failure and does not report updated paths.
- If the update call raises an exception, the tool keeps its existing failure handling.
- If one VPN update fails, the tool does not report the remaining updates as complete.

## Requirements

### Functional Requirements

- **FR-001**: The tool MUST report a VPN update as successful only when Mist returns a successful HTTP status.
- **FR-002**: The tool MUST report the VPN identifier and returned status when Mist rejects an update.
- **FR-003**: The tool MUST stop the update sequence after a rejected or unconfirmed response.
- **FR-004**: The tool MUST preserve the current success message for an accepted update.
- **FR-005**: The tool MUST preserve its current handling when the update call raises an exception.

### Mist Cloud Transport Requirements

- The existing `mistapi.api.v1.orgs.vpns.updateOrgVpn` method performs the VPN update and returns an `APIResponse`.
- The SDK response exposes `status_code` as an integer or `None`. The tool accepts a 2xx status and rejects every other value.
- The tool uses no direct HTTP transport and owns no WebSocket transport.
- Mocked response tests verify accepted status handling, refusal handling, and failure safety. The tool logs only the VPN identifier and status, not response content or credentials.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every mocked non-2xx or missing-status response produces a failure result and zero VPN update success messages.
- **SC-002**: Every mocked 2xx response preserves the existing updated-path count and success message.
- **SC-003**: The update sequence stops after the first rejected response.

## Assumptions

- Any HTTP status from 200 through 299 confirms an accepted update.
- A missing HTTP status does not confirm that Mist applied the update.
- The operator can use the existing error logs to identify the affected VPN and response status.
