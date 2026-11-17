# Feature Specification: Fail Closed on VPN Inventory Errors

**Feature Branch**: `jmorrison-juniper-wan-vpn-list-failure`

**Created**: 2026-11-17

**Status**: Draft

**Input**: Issue #4792: Prevent WAN VPN creation when the VPN inventory request fails or returns incomplete data.

## User Scenarios & Testing

### User Story 1 - Protect VPN creation when inventory is incomplete (Priority: P1)

An operator uses the WAN VPN builder to create an organization VPN. The builder must know the complete current VPN inventory before it checks the requested name or offers creation.

**Why this priority**: An incomplete inventory can hide an existing VPN and allow a duplicate organization change.

**Independent Test**: Provide synthetic successful, failed, and incomplete VPN list responses. Verify that only a complete response reaches the name prompt.

**Acceptance Scenarios**:

1. **Given** a complete successful VPN inventory with no VPNs, **When** the operator starts the builder, **Then** the empty inventory remains valid and the normal name flow can continue.
2. **Given** a failed VPN list request, **When** the operator starts the builder, **Then** the builder stops before it asks for a name or creates a VPN.
3. **Given** one successful page followed by a failed or missing page, **When** the builder reads the inventory, **Then** it rejects the incomplete inventory and stops before creation.
4. **Given** a complete successful inventory with an existing VPN name, **When** the operator enters that name, **Then** the builder rejects the duplicate before it offers creation.

### Edge Cases

- A successful response contains an empty list.
- A response has no successful status or has an invalid results shape.
- A later page fails, cannot be fetched, or is missing.
- The list request raises an exception before it returns a response.

## Requirements

### Functional Requirements

- **FR-001**: The builder MUST distinguish a complete empty VPN inventory from a failed or incomplete inventory.
- **FR-002**: The builder MUST stop before the name prompt when it cannot verify the complete VPN inventory.
- **FR-003**: The builder MUST use every nonblank VPN name from a complete inventory to reject duplicate names.
- **FR-004**: The builder MUST keep the existing typed confirmation before it creates an organization VPN.
- **FR-005**: Verification MUST use synthetic responses and MUST NOT call a live Mist organization.
- **FR-006**: Each VPN record MUST be an object with a nonblank string name. A repeated pagination link MUST make the inventory unavailable.

### Mist Cloud Transport Requirements

- The existing `mistapi.api.v1.orgs.vpns.listOrgVpns` method remains the VPN inventory path. The existing `createOrgVpn` method remains behind the typed confirmation. No direct HTTP transport is added.
- Mocked contract tests must prove that failed status, malformed records, unusable names, pagination failure, repeated links, and missing pages cannot reach VPN creation. Tests must not use a production credential or expose a secret.
- SDK insufficiency is not in scope because the existing SDK methods remain in use. Authentication and endpoint parity remain unchanged because this fix does not alter the SDK session or endpoint.

### Key Entities

- **VPN inventory**: The complete set of organization VPN definitions, including the names used to prevent duplicates.
- **Inventory result**: Either a complete VPN inventory, which may be empty, or an unavailable inventory that cannot support creation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested failed or incomplete inventory case, including an unnamed record or repeated link, stops before the builder asks for a VPN name.
- **SC-002**: Every tested failed or incomplete inventory case makes zero VPN creation calls.
- **SC-003**: A complete successful empty inventory remains distinct from an unavailable inventory.
- **SC-004**: A complete multi-page inventory rejects a duplicate name found on a later page before creation.

## Assumptions

- A complete successful empty inventory means the organization has no VPN definitions.
- The builder must stop safely when it cannot prove that the inventory is complete.
- The existing typed confirmation remains the required operator approval for VPN creation.
- Tests use mocks only. No live Mist request or organization change is permitted.
