# Feature Specification: Zone Summary Validation

**Feature Branch**: `jmorrison-juniper-zone-summary-validation`

**Created**: 2026-10-28

**Status**: Implemented, publication checks pending

**Input**: Repair exactly one unsafe default in the zone analyzer for issue #2753.

## User Scenarios & Testing

### User Story 1 - Reject Missing Summary Statistics (Priority: P1)

A network operator must not receive a zero-site summary when a nonempty analysis lacks its statistics.

**Why this priority**: An incomplete report currently appears to confirm zero sites and no deviations.

**Independent Test**: Display an incomplete local analysis and confirm an explicit failure before the zone summary appears.

**Acceptance Scenarios**:

1. **Given** a nonempty analysis without statistics, **When** display starts, **Then** it reports the required field and stops before the zone summary.
2. **Given** null or non-dictionary statistics, **When** display starts, **Then** it reports the invalid field without exposing its value.
3. **Given** valid statistics, **When** display starts, **Then** the report remains unchanged.
4. **Given** an empty analysis, **When** display starts, **Then** the existing skip remains unchanged.
5. **Given** an explicitly empty statistics dictionary, **When** display starts, **Then** the existing zero-value display remains unchanged.

### Edge Cases

- False, zero, an empty string, and an empty list are not statistics dictionaries.
- The combined-results display must propagate the same refusal.
- Refusal must not print a zone summary or continue to later display sections.

## Requirements

### Functional Requirements

- **FR-001**: A nonempty zone analysis MUST provide a `zone_count_stats` dictionary before its summary appears.
- **FR-002**: Missing or invalid statistics MUST produce an error record and an explicit failure naming the field and display boundary.
- **FR-003**: The failure MUST NOT expose the rejected value or claim zero scanned sites.
- **FR-004**: Valid dictionaries, explicitly empty dictionaries, and empty analyses MUST retain their existing behavior.
- **FR-005**: The repair MUST change only the zone-summary display boundary and its direct evidence.

### Key Entities

- **Zone analysis**: The computed zone results presented to an operator.
- **Zone statistics**: The dictionary containing the site counts and descriptive zone measurements.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every missing or invalid statistics case fails visibly before a zone summary appears.
- **SC-002**: Complete reports retain their existing displayed counts and measurements.
- **SC-003**: Empty analyses still produce no zone section.
- **SC-004**: Exactly one production default receives a validation repair.

## Assumptions

- The historical assessment lists candidates, not proven defects.
- The normal analysis builder always supplies statistics. A missing dictionary in a nonempty analysis therefore indicates incomplete data.
- An explicitly empty dictionary remains an intentional accepted display input for this bounded change.
- Credentials, resource identifiers, firmware, upgrades, destructive operations, and exports remain outside this repair.
- Issue #2753 remains open for its remaining candidates.
