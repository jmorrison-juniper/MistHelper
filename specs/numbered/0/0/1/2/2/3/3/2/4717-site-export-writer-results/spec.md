# Feature Specification: Site export write results

**Feature Branch**: `jmorrison-juniper-site-export-writer-results`

**Created**: 2026-11-09

**Status**: Approved for local repair. Publication remains on hold.

**Input**: Issue #4717. Correct the two site exporters that report success after a failed write.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a failed write (Priority: P1)

The operator must see an error when the application list or system event export cannot save its records.

**Why this priority**: A false success message can hide missing incident data.

**Independent Test**: Supply one synthetic record and a failed writer result for each export.

**Acceptance Scenarios**:

1. **Given** a failed write, **When** either export returns, **Then** an error identifies the endpoint and output filename.
2. **Given** a failed write, **When** either export returns, **Then** no message claims persistence or export success.
3. **Given** a successful write, **When** either export returns, **Then** the existing success messages remain unchanged.

### Edge Cases

- An empty result reports no data and does not call the writer.
- A writer exception still leaves the persistence method and reaches the existing menu error handler.
- Every normal persistence and menu return remains `None`.
- The existing filename, record transformation, row count, and endpoint metadata remain unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both site exports MUST report a failed writer result at error level.
- **FR-002**: A failed writer result MUST prevent both persistence and export success messages.
- **FR-003**: A successful writer result MUST preserve the existing output contract.
- **FR-004**: Empty results and exceptions MUST preserve their existing behavior.
- **FR-005**: The repair MUST NOT change shared pagination or another exporter.
- **FR-006**: Verification MUST use synthetic records with socket, DNS, and SQLite access blocked before collection.
- **FR-007**: The local commit and review evidence MUST remain available without publication.

### Key Entities

- **Write result**: The existing success or failure signal from the selected output writer.
- **Site export**: Application records or system events, with the existing site-derived filename and endpoint identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both failed-write cases produce an error and zero false success messages.
- **SC-002**: All six independent success, empty-result, and exception controls retain their existing result.
- **SC-003**: Verification records zero socket, DNS, and SQLite access attempts.
- **SC-004**: The reserved shared tests pass without changes to another issue's files.

## Assumptions

- The existing writer returns a Boolean. This repair uses that established contract.
- The two source files and their shared tests form one reserved logical file group.
- No Mist transport, authentication, endpoint, or pagination behavior changes.
- The requested base is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
- The app-managed branch replaces the branch-creation hook.
- PowerShell is unavailable. The route follows the eight-digit base-5 algorithm in `spec-route.ps1`.
- The active specification selector remains unchanged to prevent an ownership conflict.
