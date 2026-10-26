# Feature Specification: Sign-in Credential Layout

**Feature Branch**: `jmorrison-juniper-3295-upgrade-portal-sign-in-credential-l`

**Created**: 2026-10-26

**Status**: Draft

**Input**: Issue #3295, “Upgrade portal: the sign-in credential group puts the token label next to the mode buttons”

## User Scenarios & Testing

### User Story 1 - Choose a sign-in method (Priority: P1)

An operator selects a credential mode and sees only the fields that apply to that mode.

**Why this priority**: The current layout can make the token label look like a mode choice and leaves an unused token field visible.

**Independent Test**: Open the sign-in page, inspect the token label and field, then change credential modes with a keyboard.

**Acceptance Scenarios**:

1. **Given** browser-token sign-in is available, **When** the sign-in page opens, **Then** the token label appears above its field.
2. **Given** a mode that does not use a browser token is selected, **When** the page is displayed, **Then** the token field and its note are hidden or disabled.
3. **Given** browser-token sign-in is available, **When** an operator selects that mode with a keyboard, **Then** the token field becomes visible and reachable by keyboard.
4. **Given** a sign-in warning and an error-page warning are displayed, **When** an operator reads each prefix, **Then** both prefixes use the same weight.

### Edge Cases

- When browser-token sign-in is not available, the page does not show its token field.
- When the operator changes from browser-token mode to another mode, the token field and note stop appearing as active controls.

## Requirements

### Functional Requirements

- **FR-001**: The sign-in page MUST place the “Mist API token” label directly above its field.
- **FR-002**: The page MUST hide or disable the browser-token field and its note when the selected mode does not use a browser token.
- **FR-003**: The page MUST let a keyboard operator reach the browser-token field after selecting browser-token mode.
- **FR-004**: The “Warning:” prefix on a sign-in warning MUST use the same weight as the prefix on an error-page warning.
- **FR-005**: The page MUST preserve existing credential validation and sign-in behavior.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In every supported browser-token sign-in view, the token label appears above and aligns with the token field.
- **SC-002**: In every non-browser-token mode, the token field and its note are hidden or disabled.
- **SC-003**: A keyboard-only operator can select browser-token mode and focus the token field.
- **SC-004**: The sign-in and error-page warning prefixes have the same visual weight.
- **SC-005**: Existing credential validation and sign-in tests continue to pass.

## Assumptions

- The existing sign-in modes and server-side credential decisions remain unchanged.
- Browser-token sign-in remains available only when the portal allows it at startup.
