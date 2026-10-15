# Feature Specification: Count Catalog Completeness

**Feature Branch**: `3995-sdk-count-catalog`

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Add the two missing Mist count operations to the existing count catalog. Keep its completeness check and preserve the established organization fingerprint path and export identity. Fix issue #4240 in a separate change from pull request #4236."

## User Scenarios & Testing

### User Story 1 - Select an organization count (Priority: P1)

A network operator can select each supported organization count operation from the existing organization count menu.

**Why this priority**: The incomplete catalog fails the test gate and hides two supported count operations.

**Independent Test**: Compare the operation choices with the supported count operations and test selection with mocked responses.

**Acceptance Scenarios**:

1. **Given** the supported catalog includes organization variable and fingerprint counts, **When** the operator opens the organization count menu, **Then** both choices appear.
2. **Given** the operator selects either new choice, **When** the operation returns count rows, **Then** the exporter stores those rows with the established identity for that operation.
3. **Given** the site fingerprint count remains unsupported, **When** the catalog is checked, **Then** it stays excluded while the organization fingerprint count remains available.

### Edge Cases

- If the supported count catalog changes, the completeness test reports the missing or extra operation.
- If an operation lacks a persistence strategy, the strategy test fails.

## Requirements

### Functional Requirements

- **FR-001**: The organization count choices MUST include each supported organization count operation.
- **FR-002**: The site and service-provider count choices MUST retain their supported operations and existing intentional exclusions.
- **FR-003**: Each count operation MUST have a persistence identity that matches its exported row shape.
- **FR-004**: The organization fingerprint count MUST retain its organization scope and established export identity.
- **FR-005**: The catalog tests MUST detect missing operations, extra operations, unresolved operations, and missing persistence strategies.

### Key Entities

- **Count operation**: A supported Mist operation that returns count rows for an organization, site, or service provider.
- **Persistence identity**: The fields that identify an exported count row when the exporter stores it.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The catalog matches every supported count operation, except the one documented unsupported site fingerprint count.
- **SC-002**: Both missing organization operations resolve to callable SDK functions and pass mocked selection and export tests.
- **SC-003**: Every catalog operation has a verified persistence strategy, including the organization fingerprint operation.
- **SC-004**: No existing menu number or unrelated firmware behavior changes.

## Assumptions

- Operators use the existing count menus and do not need new menu numbers.
- The site fingerprint count remains excluded because Mist supports the organization endpoint instead, as recorded in issues #3334 and #3691.
- The organization fingerprint operation keeps its existing composite identity because the fingerprint census exports site, grouping field, and value.
