# Feature Specification: Client CoA Disconnect

**Feature Branch**: `3566-client-coa-disconnect`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 286 client CoA, reauthentication, and disconnect. A helpdesk operator who must force a client to reauthenticate, disconnect a client, deauthorize a guest, or drop the clients of a rogue AP must open the Mist UI. Mist offers one endpoint for each action, and no MistHelper operation calls them. The operation asks for a site, an action, and a client MAC or a rogue BSSID. It shows the target, asks the operator to type the MAC or BSSID again as the confirmation, sends the request, and writes ClientSessionControlLog.csv with the action, the target, and the result."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm and send client session control (Priority: P1)

A helpdesk operator can select a site, choose one client session control action, enter the target MAC or rogue BSSID, review the target, and type the same target again to approve the request.

**Why this priority**: This is the core safety flow. It lets an operator use MistHelper instead of opening the Mist UI, while still preventing accidental client disruption.

**Independent Test**: Run the operation with a site, a supported action, and a target. Verify that no request is sent before exact confirmation, then verify that the selected request is sent after exact confirmation.

**Acceptance Scenarios**:

1. **Given** a site, the wireless reauthenticate action, and a client MAC, **When** the operator types the exact normalized target as confirmation, **Then** the operation sends the reauthenticate request for that client and reports the result.
2. **Given** a site, the wired reauthenticate action, and a client MAC, **When** the operator types a different value at confirmation, **Then** the operation sends no request and reports that confirmation failed.
3. **Given** a site, the disconnect action, and a client MAC, **When** the operator confirms with the exact target, **Then** the operation sends the disconnect request for that client and reports the result.
4. **Given** a site, the guest unauthorize action, and a client MAC, **When** the operator confirms with the exact target, **Then** the operation sends the unauthorize request for that guest and reports the result.
5. **Given** a site, the deauth rogue clients action, and a rogue BSSID, **When** the operator confirms with the exact target, **Then** the operation sends the rogue client deauth request for that BSSID and reports the result.

---

### User Story 2 - Preview a destructive request safely (Priority: P2)

A helpdesk operator can use dry run mode to see the request that would be sent for a selected site, action, and target without changing any client session state.

**Why this priority**: Operators need a safe way to verify the target and action before they run a destructive operation.

**Independent Test**: Run the operation in dry run mode with each action and a target. Verify that the operation prints the request details and sends no request.

**Acceptance Scenarios**:

1. **Given** dry run mode, a valid site, a valid action, and a target, **When** the operator runs the operation, **Then** the operation prints the request it would send and sends nothing.
2. **Given** dry run mode and an exact confirmation value, **When** the operator completes the flow, **Then** the operation still sends nothing and records the dry run result.

---

### User Story 3 - Keep an audit trail for each request (Priority: P3)

A helpdesk lead can review a CSV log that records each requested client session control action with the target and result.

**Why this priority**: Destructive operations need traceability so support teams can review what was attempted and what happened.

**Independent Test**: Run confirmed and dry run requests. Verify that `data/ClientSessionControlLog.csv` contains one row per request with the action, target, and result.

**Acceptance Scenarios**:

1. **Given** a confirmed request, **When** the operation completes, **Then** the CSV log has one new row with the action, target, and result.
2. **Given** a dry run request, **When** the operation completes, **Then** the CSV log has one new row that identifies the result as a dry run.
3. **Given** a failed confirmation, **When** the operation stops before sending, **Then** the CSV log records the attempted action, target, and confirmation failure.

---

### Edge Cases

- If the operator leaves the confirmation blank, the operation sends no request and explains that exact confirmation is required.
- If the operator confirms with a value that differs by any character after normalization, the operation sends no request.
- If the operator enters a MAC with colons, hyphens, or dots, the operation normalizes it to lowercase colon-free form before it builds the request.
- If the operator enters an invalid MAC or BSSID, the operation stops before confirmation and shows a clear validation message.
- If the selected action requires a rogue BSSID but the operator enters a client MAC, the operation rejects the target before any request.
- If the Mist request fails or returns an error, the operation reports the failure and writes the failure result to the CSV log.
- If the CSV log does not exist, the operation creates it under `data/` with headers before writing the row.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide menu 286 as a destructive operation named for client CoA, reauthentication, and disconnect.
- **FR-002**: The operation MUST ask the operator to select a site before it asks for the action and target.
- **FR-003**: The operation MUST support these actions: wireless reauthenticate, wired reauthenticate, disconnect, unauthorize guest, and deauth rogue clients.
- **FR-004**: The operation MUST ask for a client MAC for wireless reauthenticate, wired reauthenticate, disconnect, and unauthorize guest.
- **FR-005**: The operation MUST ask for a rogue BSSID for deauth rogue clients.
- **FR-006**: The operation MUST display the selected action and normalized target before it asks for destructive confirmation.
- **FR-007**: The operation MUST require the operator to type the exact target MAC or BSSID again as confirmation before it sends any request.
- **FR-008**: The operation MUST send no Mist request when the confirmation value does not exactly match the normalized target.
- **FR-009**: The operation MUST support `--dry-run`, print the request it would send, and send no Mist request.
- **FR-010**: The operation MUST normalize MAC and BSSID values to the lowercase colon-free form that Mist expects.
- **FR-011**: Automated tests MUST prove the three common MAC input forms: colon separated, hyphen separated, and dotted.
- **FR-012**: The operation MUST write `data/ClientSessionControlLog.csv` with one row for each request attempt.
- **FR-013**: Each CSV row MUST include at least the action, target, and result.
- **FR-014**: The operation MUST report a clear success, dry run, confirmation failure, validation failure, or Mist failure result to the operator.
- **FR-015**: The operation MUST be registered as destructive and excluded from every automated test pass.
- **FR-016**: The implementation package MUST be `src/device/client_session_control/`.
- **FR-017**: The handler MUST be class `ClientSessionControl` with static `run()`.
- **FR-018**: Registration work MUST be deferred to `specs/3566-client-coa-disconnect/wiring.md` and MUST NOT edit repository wiring files during specification.
- **FR-019**: The wiring manifest `specs/3566-client-coa-disconnect/wiring.md` MUST exist and include every section required by the implementation contract.
- **FR-020**: The release note fragment `changelog.d/issue-3566-client-coa-disconnect.md` MUST exist before completion of implementation.

### Key Entities *(include if feature involves data)*

- **Client Session Control Request**: A requested operation for one site, one action, and one target. Key attributes are site, action, target type, normalized target, dry run flag, confirmation status, and result.
- **Target**: The client MAC or rogue BSSID that identifies the client or rogue AP clients to affect. The stored request form is lowercase and colon-free.
- **Client Session Control Log Row**: One audit entry for a request attempt. Key attributes are action, target, and result, with optional context such as site, dry run state, and timestamp.
- **Wiring Manifest**: The owned planning record that lists the menu number, category, handler, operation contract, deferred registration files, tests, exclusions, and release note requirement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100 percent of tested negative confirmation cases, no Mist request is sent.
- **SC-002**: In 100 percent of dry run cases, the operator sees the exact request preview and no Mist request is sent.
- **SC-003**: In 100 percent of supported MAC input form tests, the target normalizes to lowercase colon-free form.
- **SC-004**: In 100 percent of request attempts, `data/ClientSessionControlLog.csv` receives exactly one row that includes action, target, and result.
- **SC-005**: Helpdesk operators can complete a confirmed session control request in under 2 minutes when site and target are known.
- **SC-006**: Automated test discovery excludes the destructive operation in every automated test pass.
- **SC-007**: The implementation handoff is complete when `wiring.md` exists in the feature directory and the release note fragment requirement is tracked.

## Assumptions

- Helpdesk operators already have valid Mist access through the existing MistHelper configuration.
- The existing site selection pattern is reused so the operator can select the intended site by the normal MistHelper site flow.
- Mist exposes one endpoint for each supported action.
- The confirmation comparison uses the normalized target value shown to the operator.
- `ClientSessionControlLog.csv` is not a secret log. It must not include API tokens, passwords, or unrelated client personal data.
- Automated test passes are safe by default and must not execute destructive operations.
- The release note fragment is outside the owned specification path for this step. It is required for implementation but is not created during specification because the fleet contract limits edits to the feature specification directory.

## Planning Constraints

- Use Simplified Technical English in specification and planning documents.
- Do not use semicolons in the specification and planning documents.
- For this specification step, edit only `specs/3566-client-coa-disconnect/**`.
- Do not edit `.specify/feature.json` or repository wiring files during this step.
- Do not edit `MistHelper.py`, `operation_registry.py`, `endpoint_primary_key_strategies.py`, `README.md`, `copilot-instructions.md`, `menu_reference.md`, `web_portal`, or existing files outside owned paths during this step.
