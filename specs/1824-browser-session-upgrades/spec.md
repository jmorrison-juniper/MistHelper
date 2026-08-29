# Feature Specification: Browser Token and Safe Device Selection

**Feature Branch**: `2133-browser-session-token-upgrades`  
**Created**: 2026-08-29  
**Status**: Draft  
**Input**: Add browser-session Mist token sign-in, device-type selection, and target-version mismatch warnings.

## User Scenarios & Testing

### User Story 1 - Sign in with a browser token (Priority: P1)

An operator starts a portal with no environment API token. The operator enters a
Mist API token for one browser session. The portal uses that credential only for
that session. The portal identifies the credential by its safe token name.

**Why this priority**: An operator must use the portal when a container did not
receive an environment token at startup.

**Independent Test**: Start the portal without an environment token. Sign in
with a test token. Confirm that later portal calls use the session credential,
and that the page, logs, storage, and source do not contain the token value.

**Acceptance Scenarios**:

1. **Given** the portal started without an environment token, **When** an
   operator opens the sign-in page, **Then** the page offers a browser-token
   sign-in field.
2. **Given** the portal started with an environment token, **When** an operator
   opens the sign-in page, **Then** the page does not offer the browser-token
   sign-in field.
3. **Given** an operator submits a valid browser token, **When** the portal
   accepts the sign-in, **Then** the portal reads the safe token name and uses
   that name for the audit identity and the site-lock holder.
4. **Given** a browser-token session is active, **When** the operator selects,
   captures, reviews, or prepares an upgrade, **Then** each Mist request uses
   the session credential.
5. **Given** a browser token is invalid, **When** the portal refuses the
   sign-in, **Then** the portal shows a safe refusal and retains no token value.

### User Story 2 - Select the device types for an upgrade (Priority: P1)

An operator captures the complete site state before an upgrade. The operator
chooses all supported device types, selected types, or one type. The portal
prepares a safe plan for the chosen types only.

**Why this priority**: Operators need one capture of the whole site, but they
must limit an upgrade to the hardware that the change window covers.

**Independent Test**: Create a complete capture with access points, switches,
and gateways. Select one type, then a selected group, then all types. Confirm
that the target rows and prepared plans contain only the selected types.

**Acceptance Scenarios**:

1. **Given** a verified site capture exists, **When** an operator opens upgrade
   options, **Then** the portal lists supported types with checkboxes and offers
   all, selected, and single-type choices.
2. **Given** an operator chooses selected types, **When** the portal shows
   targets or accepts a plan, **Then** it includes only the chosen types.
3. **Given** an operator chooses one type, **When** the portal shows targets or
   accepts a plan, **Then** it includes only that type.
4. **Given** an operator chooses all types, **When** the portal shows targets or
   accepts a plan, **Then** it includes all supported types in the capture.
5. **Given** a selected target fails existing safety validation, **When** the
   operator submits the plan, **Then** the portal refuses the plan.

### User Story 3 - See devices that differ from the safe target (Priority: P1)

An operator reviews the site inventory before an upgrade. The portal marks each
known running firmware version that differs from its safe target. The portal
keeps its current behavior when the running version is unknown.

**Why this priority**: A clear mismatch warning helps the operator find devices
that need attention before a change window.

**Independent Test**: Use capture data with known matching, known different,
and unknown running versions. Confirm that only the known different version
shows a warning. Confirm that a valid compatible override takes priority.

**Acceptance Scenarios**:

1. **Given** a device has a known running version and a safe target, **When**
   the two values differ, **Then** the inventory shows a clear mismatch marker.
2. **Given** a valid compatible override exists for a device type, **When** the
   portal finds a target, **Then** the override supplies the target.
3. **Given** no valid compatible override exists, **When** the portal finds a
   target, **Then** it selects the highest compatible model version.
4. **Given** a device has an unknown running version, **When** the portal shows
   inventory, **Then** it preserves the existing unknown-version behavior.

## Edge Cases

- The portal rejects an empty browser token and a token that fails identity
  lookup without writing its value to a response, log, session, file, or store.
- The portal clears the browser credential when the browser session ends or the
  operator signs out.
- The portal excludes unsupported device types and empty selections from a
  submitted plan.
- The portal retains complete captured rows even when an operator filters the
  displayed target rows.
- The portal rejects a version override when it is not compatible with the
  device model.
- The portal marks no mismatch when it cannot safely determine a running
  version.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST offer browser-token sign-in only when no
  environment token existed at portal startup.
- **FR-002**: The portal MUST keep a browser token only in server-side
  session memory and MUST not render, log, persist, export, or commit it.
- **FR-003**: The portal MUST use the active browser credential for every Mist
  API request in that browser session.
- **FR-004**: The portal MUST call `GetSelf` after browser-token sign-in and
  MUST use its safe token name for audit identity and site-lock holder data.
- **FR-005**: The portal MUST retain complete site capture data regardless of
  the device types selected for a later upgrade.
- **FR-006**: The upgrade options view MUST let an operator choose all,
  selected, or one supported device type with checkboxes.
- **FR-007**: The portal MUST filter target rows and submitted upgrade plans to
  the selected supported device types.
- **FR-008**: The portal MUST preserve target-version safety validation for
  every selected device.
- **FR-009**: The inventory MUST mark a known running version that differs
  from the safe target version.
- **FR-010**: The portal MUST use a valid compatible type override as the safe
  target, or the highest compatible model version when no such override exists.
- **FR-011**: The portal MUST preserve current behavior for unknown running
  firmware versions.
- **FR-012**: The implementation, tests, validation, and deployment MUST NOT
  start a real firmware upgrade.

### Key Entities

- **Browser credential**: A session-only authorization value and a derived safe
  token name. The value never appears outside the active session boundary.
- **Credential identity**: The safe name used for audit records and site locks.
- **Device-type selection**: The supported types that limit target rows and
  the submitted plan after the full site capture.
- **Safe target**: A compatible override when valid, otherwise the highest
  compatible version for a device model.
- **Firmware mismatch**: A visible condition where a known running version
  differs from the safe target.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A test proves that no response, log record, session export,
  database record, or committed source contains a submitted token value.
- **SC-002**: A test proves that each portal Mist call in a browser-token
  session receives that session credential.
- **SC-003**: A test proves that a complete capture keeps all supported types
  while each selected plan includes only chosen types.
- **SC-004**: A test proves that a mismatched known version has a marker, and
  that an unknown version has no new mismatch marker.
- **SC-005**: Focused unit, contract, and browser tests pass without starting
  a firmware upgrade.
- **SC-006**: The built container and local portal readiness checks pass after
  the merged change deploys.

## Assumptions

- The current server-side session store protects session content from browser
  scripts and does not serialize the browser credential to durable storage.
- The Mist identity response exposes a safe token name that does not equal the
  token value.
- Access point, switch, and gateway remain the supported upgrade device types.
- Existing typed confirmation remains the only path that can start an upgrade.

## Verbatim Constraints

- `GetSelf`
- `MIST_APITOKEN`
- `MIST_API_TOKEN`
- `CONFIRM`
