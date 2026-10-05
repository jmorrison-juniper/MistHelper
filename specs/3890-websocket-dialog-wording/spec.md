# Feature Specification: WebSocket Dialog Target Wording

**Feature Branch**: `jmorrison-juniper-fix-3890-websocket-dialog-wording`

**Created**: 2026-10-04

**Status**: Approved for bounded local repair

**Input**: Issue #3890 reports missing purpose text in four WebSocket utility dialogs. Parent audit: #3862.

## User Scenarios & Testing

### User Story 1 - Choose a valid DHCP release target (Priority: P1)

An operator opens the DHCP lease release form for an EX, an SRX, or an SSR device.
The purpose text tells the operator which target fields to supply together.
The purpose text also tells the operator that the release changes client state.

**Why this priority**: A wrong target set can fail, or it can release more leases than the operator intends.

**Independent Test**: Read the catalog purpose text for each key, and read the text that the browser shows.

**Acceptance Scenarios**:

1. **Given** the operator selects `ex.releaseDhcpLeases`, **When** the form opens, **Then** the text names the three EX target sets from the installed SDK.
2. **Given** the operator selects `srx.releaseDhcpLeases` or `ssr.releaseDhcpLeases`, **When** the form opens, **Then** the text names the five SRX and SSR target sets from the installed SDK.
3. **Given** any DHCP release form, **When** the form opens, **Then** the text states that the release changes client state.

### User Story 2 - Filter the MAC table (Priority: P2)

An operator opens the MAC table form for an EX switch.
The purpose text tells the operator that the filters are optional and that empty filters return the full table.

**Why this priority**: The operator otherwise cannot tell whether an empty MAC address field is valid.

**Independent Test**: Read the catalog purpose text, and read the text that the browser shows.

**Acceptance Scenarios**:

1. **Given** the operator selects `ex.retrieveMacTable`, **When** the form opens, **Then** the text explains the full table and the optional MAC address filter.

## Edge Cases

- A future SDK family that adds `releaseDhcpLeases` keeps the existing generic DHCP sentence.
- The DHCP release utilities keep the `change` safety class, the lock flag, and the warning box.
- The browser test must not click Start, and it must not call any Mist API.

## Requirements

### Functional Requirements

- **FR-001**: The EX DHCP purpose text MUST list these target sets: Network and MAC addresses, Network and Port, Port only.
- **FR-002**: The SRX and SSR DHCP purpose text MUST list these target sets: Network only, Network and MAC addresses, Network and Port, Port only, Port and MAC addresses.
- **FR-003**: Each DHCP purpose text MUST state that the release changes client state.
- **FR-004**: The MAC table purpose text MUST state that empty filters return the full table and that a MAC address filter is optional.
- **FR-005**: The repair MUST NOT change SDK arguments, fields, safety classes, locks, confirmations, triggers, or execution logic.
- **FR-006**: The repair MUST NOT edit `websockets.js` or `tests/e2e/websockets_tab/test_websockets_page.py`, because PR #3814 owns them.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Unit tests prove the four purpose texts and the unchanged generic fallback.
- **SC-002**: A unit test proves that the stated target sets match the installed SDK docstring.
- **SC-003**: A Playwright test proves that the browser shows each corrected text for all four forms, without a start request.
- **SC-004**: Unit tests prove that the safety class and the fields of the four utilities stay unchanged.

## Assumptions

- The installed `mistapi` 0.64.0 docstring of `release_dhcp_leases` is the authoritative target contract.
- The form field labels are "Network", "MAC addresses", and "Port", so the text uses those labels.
