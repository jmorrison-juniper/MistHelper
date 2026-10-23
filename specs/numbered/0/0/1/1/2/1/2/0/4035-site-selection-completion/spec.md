# Feature Specification: Site selection completion

**Feature Branch**: `jmorrison-juniper-fix-4035-site-selection-completion`

**Created**: 2026-10-23

**Status**: Ready

**Input**: Repair issue #4035 without changing genuine empty or failed operation results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm a selected site (Priority: P1)

An operator selects a site through menu 92. The portal confirms the selection without requiring a data export.

**Why this priority**: The current failure message contradicts a successful selection.

**Independent Test**: Execute menu 92 with a controlled site selection and no output file.

**Acceptance Scenarios**:

1. **Given** an available site, **When** the operator selects it, **Then** the portal reports completion without an export failure.
2. **Given** an invalid selection, **When** no site is selected, **Then** the portal does not report successful selection.

### User Story 2 - Preserve other terminal results (Priority: P2)

An operator can still distinguish an empty export from a failed operation.

**Why this priority**: A selection repair must not hide a genuine export failure.

**Independent Test**: Execute controlled empty, silent, and failed handlers through the terminal assessment.

**Acceptance Scenarios**:

1. **Given** an export with an explicit empty-result reason, **When** it ends, **Then** the portal displays that reason.
2. **Given** an export without result evidence, **When** it ends, **Then** the portal reports failure.
3. **Given** a handler exception, **When** it ends, **Then** the portal retains the failure reason.

### Edge Cases

- A blank selection, a missing selection, and a non-string result do not prove successful selection.
- A site identifier returned by a different menu does not prove export completion.
- A selected site requires no new output file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 92 MUST report completion after a successful site selection.
- **FR-002**: The completion message MUST explain that selection requires no output file.
- **FR-003**: Missing or invalid selections MUST NOT report successful selection.
- **FR-004**: Other menus MUST retain their existing empty-result and failure behavior.
- **FR-005**: Existing site-selection callers MUST retain their selected identifier or absent-selection result.
- **FR-006**: Tests MUST use controlled input without production credentials or device changes.

### Key Entities

- **Site selection**: The identifier returned after the operator selects a site.
- **Operation result**: The terminal status, completion message, error message, and output files for one portal run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All controlled successful selections report completion with zero required output files.
- **SC-002**: All controlled missing, blank, and invalid selections avoid successful selection completion.
- **SC-003**: All controlled empty-export and failed-operation cases retain their previous terminal status and explanation.

## Assumptions

- Menu 92 remains available as a selection action.
- The existing selector validates the operator choice and returns a nonblank identifier on success.
- This change adds no cloud transport and performs no production operation.
