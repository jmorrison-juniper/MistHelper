# Feature Specification: Missing Zone Map Validation

**Feature Branch**: `jmorrison-juniper-missing-zone-map-validation`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Require an explicit dictionary before the missing-common-zones display claims all sites have the common zones configured. Preserve explicit empty maps, valid nonempty maps, display caps, and the empty-analysis skip."

## User Scenarios & Testing

### User Story 1 - Trust the missing-zone summary (Priority: P1)

An operator reads a zone analysis report and needs the missing-zone summary to reflect complete analysis data.

**Why this priority**: A false reassurance can hide sites that need configuration changes.

**Independent Test**: Provide missing, null, and wrong-type results. Confirm the report fails visibly and does not claim that all sites have the common zones.

**Acceptance Scenarios**:

1. **Given** a zone analysis with no missing-zone result, **When** the report renders that section, **Then** it reports a validation failure and does not claim that all sites have the common zones.
2. **Given** a null or non-dictionary missing-zone result, **When** the report renders that section, **Then** it reports a validation failure and does not claim that all sites have the common zones.
3. **Given** an explicit empty missing-zone result, **When** the report renders that section, **Then** it states that all sites have the common zones.
4. **Given** a nonempty missing-zone result, **When** the report renders that section, **Then** it lists the affected sites and preserves the existing display cap.

### Edge Cases

- An empty zone analysis still skips the zone section.
- A complete analysis with an explicit empty missing-zone result still displays the reassurance.
- Invalid results fail before the section prints a count or a reassurance.

## Requirements

### Functional Requirements

- **FR-001**: A rendered missing-zone summary MUST receive an explicit dictionary of sites that lack common zones.
- **FR-002**: The report MUST log an error and raise a visible validation failure when the missing-zone result is absent or is not a dictionary.
- **FR-003**: The report MUST state that all sites have the common zones only when the explicit dictionary is empty.
- **FR-004**: The report MUST preserve the existing affected-site details and display cap for a nonempty dictionary.
- **FR-005**: An empty zone analysis MUST continue to skip the zone section.

### Key Entities

- **Zone analysis**: The collected summary that the operator reads.
- **Missing-zone result**: The site-to-missing-zones data that supports the report statement.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every missing, null, or wrong-type result in the required test cases produces a logged validation failure and no reassurance.
- **SC-002**: An explicit empty result still produces the existing reassurance.
- **SC-003**: A nonempty result still lists affected sites and limits the list to the existing cap.
- **SC-004**: An empty zone analysis produces no zone-section output.

## Assumptions

- The zone-analysis producer supplies a dictionary, including an explicit empty dictionary when no sites lack common zones.
- Existing site details and the display cap remain unchanged.
- This slice changes no Mist API calls, exports, identifiers, credentials, upgrades, or destructive operations.
