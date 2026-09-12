# Feature Specification: Complete Tier 3 Capture Output

**Feature Branch**: `fix/2443-tier3-capture-output`

**Created**: 2026-09-10

**Status**: In progress

**Input**: Issue #2443 and the live Playwright usability test of the upgrade capture portal.

## User Scenarios and Testing

### User Story 1 - Inspect the full capture (Priority: P1)

An operator opens a verified Tier 3 capture and inspects every stored section.
The page shows devices, all client groups, ports, PoE, radios, tunnels, BGP peers, and alarms.

**Why this priority**: The portal reports that Tier 3 completed, but it hides most Tier 3 records.

**Independent Test**: Open a stored Tier 3 capture with one row in each section. Confirm that each table is visible.

**Acceptance Scenarios**:

1. **Given** a verified Tier 3 capture, **When** the operator opens it, **Then** every stored section has a labeled table.
2. **Given** an empty Tier 3 section, **When** the operator opens it, **Then** the page states that the section has no row.
3. **Given** a Tier 2 capture, **When** the operator opens it, **Then** the page states that Tier 3 data was not requested.

---

### User Story 2 - Export the full capture (Priority: P1)

An operator downloads a capture and receives every record that the stored document contains.
Each row has a stable kind and retains every safe source field.

**Why this priority**: An incomplete file cannot prove the site state before or after an upgrade.

**Independent Test**: Export a capture with every client and Tier 3 section. Compare the source count with each exported kind count.

**Acceptance Scenarios**:

1. **Given** a Tier 3 capture, **When** the operator downloads CSV, **Then** every stored record has one export row.
2. **Given** the same capture, **When** the operator downloads JSON, **Then** the JSON has the same rows as the CSV.
3. **Given** a record with a new safe field, **When** the portal exports it, **Then** `details_json` retains that field.
4. **Given** a record with a credential field, **When** the portal exports it, **Then** the file excludes that field.

---

### User Story 3 - Prevent a hidden regression (Priority: P2)

A browser test opens the same Tier 3 result that an operator opens.
The test verifies the visible sections and the exported row kinds.

**Why this priority**: The current E2E suite passes without checking the hidden Tier 3 records.

**Independent Test**: Run the Tier 3 browser test against the local stand-in portal.

**Acceptance Scenarios**:

1. **Given** stand-in Tier 3 data, **When** the browser opens the capture, **Then** all section test identifiers are visible.
2. **Given** the export links, **When** the browser reads the files, **Then** all expected kinds are present.
3. **Given** the required stand-in rows, **When** an assertion fails, **Then** the test fails and does not skip.

### Edge Cases

- A section can be empty after a successful read.
- A capture can use Tier 2 and contain no `extras` map.
- An extra record can contain an unknown safe field from a newer Mist response.
- A section can contain more than the page row cap.
- A stored record can contain a field whose name identifies a credential.

## Requirements

### Functional Requirements

- **FR-001**: The page MUST render the guest client section of a verified capture.
- **FR-002**: The page MUST render the six Tier 3 sections when the capture tier is 3.
- **FR-003**: The page MUST show an explicit empty-state sentence for each empty Tier 3 section.
- **FR-004**: The page MUST show an explicit Tier 2 note when Tier 3 data was not requested.
- **FR-005**: Each table MUST use stable `data-testid` values.
- **FR-006**: Each table MUST apply the existing 500-row display cap and state each cut.
- **FR-007**: The export MUST use stable kinds for devices, all client groups, and all Tier 3 sections.
- **FR-008**: Each export row MUST retain every safe source field in `details_json`.
- **FR-009**: The export MUST remove credential fields before it builds `details_json`.
- **FR-010**: CSV and JSON MUST contain the same row set.
- **FR-011**: Tier 2 exports MUST keep their current device and client rows.
- **FR-012**: Browser coverage MUST verify the page and export behavior with Tier 3 stand-in data.
- **FR-013**: The fix MUST not start an upgrade or change Mist configuration.

### Key Entities

- **Capture section view**: The label, stable key, columns, rows, held count, and requested state of one section.
- **Export row**: One stored record with a stable kind, common columns, and a safe JSON detail field.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A Tier 3 capture with records in all sections shows nine result tables.
- **SC-002**: The exported count for each kind equals the stored count for that section.
- **SC-003**: A new safe field survives in `details_json` without a source change.
- **SC-004**: All targeted unit, contract, and browser tests pass with no required Tier 3 skip.
- **SC-005**: A second live Tier 3 capture shows the stored section counts on the page and in both exports.

## Assumptions

- The collector and ArangoDB schema remain unchanged.
- The existing 500-row page cap remains the display limit.
- `details_json` is the compatibility field for section-specific and future fields.
- The comparison calculation remains outside this repair. Issue #2443 covers capture visibility and capture exports.
- The live verification uses read-only Mist API calls and writes one capture document.
