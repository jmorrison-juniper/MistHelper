# Feature Specification: Inventory search status

**Feature Branch**: `jmorrison-juniper-inventory-search-status`

**Created**: 2026-11-09

**Status**: Approved for local repair

**Input**: Repair the false empty-result and export-success messages described in issue #4716.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report request failure (Priority: P1)

The operator must distinguish a failed inventory search from a successful search with no matching devices.

**Why this priority**: A false empty result can hide an access or service failure.

**Independent Test**: Supply synthetic failed responses and inspect the error messages and output calls.

**Acceptance Scenarios**:

1. **Given** a failed initial request, **When** the search runs, **Then** it reports failure without an empty-result or export-success message.
2. **Given** an absent or malformed status, **When** the search runs, **Then** it reports failure without writing output.

### User Story 2 - Report write failure (Priority: P1)

The operator must not receive an export-success message when the output writer reports failure.

**Why this priority**: An incorrect success message can hide lost output.

**Independent Test**: Supply one synthetic row and a failed writer result.

**Acceptance Scenarios**:

1. **Given** matching inventory and a failed writer, **When** the export runs, **Then** it reports failure without a persistence or success message.
2. **Given** matching inventory and a successful writer, **When** the export runs, **Then** it retains the existing output name and operation identifier.

### Edge Cases

- Valid empty searches retain their normal empty-result message.
- Both boundaries of the integer success-status range remain valid.
- Boolean, missing, null, text, fractional, and container statuses fail.
- Filter values and organization cancellation retain their current behavior.
- Existing raised exceptions retain their public handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Accept only an integer initial status from 200 through 299, excluding booleans.
- **FR-002**: Reject all other initial statuses before pagination, transformation, or output.
- **FR-003**: Report request failures without normal empty-result or export-success messages.
- **FR-004**: Report a false writer result without persistence or export-success messages.
- **FR-005**: Preserve valid rows, empty results, filters, cancellation, operation identifiers, and public return and exception behavior.
- **FR-006**: Use synthetic tests with sockets and DNS blocked and no production credentials or databases.

### Mist Cloud Transport Requirements

The existing method is `mistapi.api.v1.orgs.inventory.searchOrgInventory`.
The repair retains the SDK and its pagination helper.
No new transport, authentication, or WebSocket path is required.
Tests use the installed SDK response shape and pagination helper without network access.

### Key Entities

- **Initial response**: The inventory request status and its synthetic device rows.
- **Writer result**: The output writer success or failure signal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested request failure produces an error and zero output calls.
- **SC-002**: Every tested write failure produces zero success or persistence messages.
- **SC-003**: All existing filter and cancellation cases retain their behavior.
- **SC-004**: New failure regressions fail with the original source and pass with the repair.
- **SC-005**: All checks record zero socket and DNS attempts.

## Assumptions

- Only the initial response status is validated. Later-page validation is outside this issue.
- The public entry point continues to return `None` and retain its existing exception handling.
- Publication requires a separate decision. This change remains a local commit.
- The assigned base is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
