# Feature Specification: Required Device Identity for Inventory Failure Records

**Feature Branch**: `jmorrison-juniper-audit-defaults-missing-inputs`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Repair missing device identity in inventory comparison failure records and guard this bounded candidate for issue #2753."

## User Scenarios & Testing

### User Story 1 - Identify every failed device record (Priority: P1)

An operator reviews an inventory comparison failure and needs a device ID to identify the affected device.

**Why this priority**: A row without a device ID cannot identify the device that caused the failure.

**Independent Test**: Give the comparison a failure record with no device ID and confirm that it reports the missing field instead of writing an unidentified row.

**Acceptance Scenarios**:

1. **Given** a failure record has no device ID, **When** the comparison records the failure, **Then** it reports the missing device ID and writes no row.
2. **Given** a failure record has a blank or non-string device ID, **When** the comparison records the failure, **Then** it reports invalid input and writes no row.
3. **Given** a failure record has a valid device ID, **When** the comparison records the failure, **Then** the row contains the original device ID.

## Edge Cases

- The device ID is absent, blank, or not a string.
- The comparison fails while the failure row is being created.
- The source file is absent or cannot be parsed by the bounded candidate scan.

## Requirements

### Functional Requirements

- **FR-001**: Each inventory comparison failure row MUST have a nonblank string device ID.
- **FR-002**: The comparison MUST report a missing or invalid device ID and MUST NOT write an unidentified failure row.
- **FR-003**: The comparison MUST preserve the supplied device ID when it is valid.
- **FR-004**: The bounded candidate scan MUST report its file and candidate counts and MUST fail when it cannot read or parse its source.
- **FR-005**: The guard MUST fail when an empty-string device ID default returns to the selected source.

## Key Entities

- **Inventory failure row**: A record that identifies a device and explains why its address comparison failed.
- **Device ID**: The source identifier that lets an operator connect a failure row to one device.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Missing, blank, and non-string device IDs produce a visible refusal and no failure row.
- **SC-002**: A valid device ID remains unchanged in each failure row.
- **SC-003**: The bounded scan parses one source file and reports zero empty-string device ID defaults.
- **SC-004**: A controlled reintroduction of the empty-string default makes the scan guard fail.

## Assumptions

- Mist device IDs are nonblank strings.
- A comparison failure row without a device ID cannot meet its purpose.
- This slice changes only the two inventory failure-record paths and their direct tests.
- This slice makes no Mist request and changes no production state.
