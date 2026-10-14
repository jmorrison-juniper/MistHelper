# Feature Specification: Menu 93 Inventory Output

**Feature Branch**: `[jmorrison-juniper-fix/4037-menu-93-inventory-output]`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Show the valid Menu 93 SiteInventory.csv file in the completed operation result when a standalone database warning appears."

## User Scenarios & Testing

### User Story 1 - Review the inventory result (Priority: P1)

An operator runs Menu 93 and reviews the completed inventory result.

**Why this priority**: The inventory file is the operation result. Hiding it prevents the operator from checking the devices.

**Independent Test**: Run Menu 93 with mocked data and a standalone database warning. Confirm that the completed result lists the file and displays its rows.

**Acceptance Scenarios**:

1. **Given** Menu 93 writes a valid inventory file and reports a database warning, **When** the operation completes, **Then** the result lists the inventory file.
2. **Given** the operation lists the inventory file, **When** the operator opens the result, **Then** the file rows remain available.

### User Story 2 - Review an empty result (Priority: P2)

An operator runs a site operation that has no data and writes only a prompt cache file.

**Why this priority**: A cache file must not appear as a valid operation result when the operation has no data.

**Independent Test**: Run a cache-only case with an explicit no-data message. Confirm that the result omits the cache file.

**Acceptance Scenarios**:

1. **Given** an operation writes only a prompt cache and reports no data, **When** it completes, **Then** the result omits the cache file and states the empty result.

### Edge Cases

- A database warning that contains the word "no" but does not report empty data must not hide an existing inventory file.
- A genuine no-data message must still remove a prompt cache when the cache is the only file.
- A missing inventory file must not appear in the completed result.

## Requirements

### Functional Requirements

- **FR-001**: The completed result MUST list each existing file produced by Menu 93.
- **FR-002**: An unrelated database warning MUST NOT change the list of operation files.
- **FR-003**: A genuine no-data message MUST continue to remove a prompt cache when it is the only output.
- **FR-004**: The completed result and its completion notice MUST present the same output file names.

### Key Entities

- **Operation result**: The files and rows that an operator can review after an operation completes.
- **Prompt cache**: A helper file that can support an operation but is not always that operation's result.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every mocked Menu 93 run that writes an inventory file presents its name in the completed result and completion notice.
- **SC-002**: Every tested cache-only run with an explicit no-data message omits that cache from the completed result.
- **SC-003**: Tests use mocked operation data and make no live service request.

## Assumptions

- Menu 93 treats `SiteInventory.csv` as its operation result.
- Other site operations may use `SiteInventory.csv` only as a prompt cache.
- A database connectivity warning does not prove that the operation returned no data.
