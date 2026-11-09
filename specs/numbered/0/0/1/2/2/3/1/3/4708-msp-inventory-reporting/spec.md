# Feature Specification: Accurate MSP inventory coverage

**Feature Branch**: `jmorrison-juniper-msp-inventory-reporting`

**Created**: 2026-11-09

**Status**: Ready

**Input**: Repair issue #4708 within the reserved source, tests, release note, and feature records.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read accurate batch results (Priority: P1)

The operator needs the successful count and the skipped or failed count after an MSP inventory batch.

**Why this priority**: An incorrect count can conceal missing inventory.

**Independent Test**: Supply successful, missing-ID, and failed organizations with no network access.

**Acceptance Scenarios**:

1. **Given** three successful organizations, **When** the batch ends, **Then** the summary reports three successes and zero skipped or failed organizations.
2. **Given** one success, one missing ID, and one failure, **When** the batch ends, **Then** the summary reports one success and two skipped or failed organizations.
3. **Given** a missing ID, **When** the batch processes that record, **Then** the console identifies the skipped organization and the cause.
4. **Given** no successes, **When** the batch ends, **Then** the summary reports zero successes and produces no combined reports.

### User Story 2 - Identify partial combined reports (Priority: P1)

The operator needs to distinguish partial combined reports from reports for every organization.

**Why this priority**: An unrestricted heading misrepresents the report coverage.

**Independent Test**: Supply two successes and one failure, then inspect every combined-report heading and captured export.

**Acceptance Scenarios**:

1. **Given** two successes and one failure, **When** combined reports appear, **Then** each heading identifies partial coverage and the successful and excluded counts.
2. **Given** two successes and no failures, **When** combined reports appear, **Then** each heading retains `All Orgs`.
3. **Given** excluded organizations, **When** valid organizations remain, **Then** the batch continues and exports only successful results.

### Edge Cases

- An empty organization list produces the existing no-organizations message.
- A successful organization with no device rows still counts as a successful run.
- One success does not meet the existing two-success requirement for combined reports.
- A failure before a success must not prevent the later organization from running.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Count successful runner returns, not organization-list entries.
- **FR-002**: Report the remaining entries as skipped or failed without claiming complete coverage.
- **FR-003**: Show a missing-ID warning in the console.
- **FR-004**: Identify partial coverage in each of the three combined-report headings.
- **FR-005**: Preserve all-success headings, export fields, filenames, and the two-success report threshold.
- **FR-006**: Continue after a missing ID or runner exception.
- **FR-007**: Use only mocked collaborators during validation, with DNS and sockets blocked.

### Key Entities

- **Organization result**: The output from a runner that returns successfully.
- **Batch coverage**: Successful count and skipped or failed count for the selected MSP.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested batch reports the exact successful count and excluded count.
- **SC-002**: All three partial-report headings identify incomplete coverage.
- **SC-003**: All three complete-report headings retain `All Orgs`.
- **SC-004**: Export records retain their existing fields and include only successful organizations.

## Assumptions

- A runner return counts as success even when its device lists are empty.
- The excluded count combines missing-ID records and runner exceptions.
- Console coverage labels do not change the export schema.
- No live service or irreversible operation is necessary.
