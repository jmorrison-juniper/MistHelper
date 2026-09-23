# Feature Specification: Accurate operation labels

**Feature Branch**: `fix/3219-label-accuracy`

**Created**: 2026-09-23

**Status**: Implemented

**Input**: Issue #3219. "Operation labels show internal issue numbers, and menu 236 promises 32 operations but offers 33."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A label tells the truth about its chooser (Priority: P1)

A NOC engineer reads "Run any site-scoped Mist count endpoint (33 operations)", opens the row, and finds 33 choices.

**Independent Test**: Compare each promised count against the length of the table that its chooser prints.

**Acceptance Scenarios**:

1. **Given** menu 236, **When** the engineer reads the label, **Then** it promises 33 operations, and the chooser offers 33.
2. **Given** a developer adds a row to a chooser table, **When** the label keeps the old count, **Then** a unit test fails.

### User Story 2 - A label holds no internal tracking number (Priority: P2)

A label such as "Search WAN client events for a selected site" carries no "spec 899 / issue #1407".

**Acceptance Scenarios**:

1. **Given** any label in the portal or on the command line, **When** it holds `issue #N`, `spec N`, or `#NNN`, **Then** a unit test fails.

## Requirements *(mandatory)*

- **FR-001**: Menu 236 MUST promise 33 operations.
- **FR-002**: No label in `MistHelper.py` or `web_portal/menu_registry.py` MAY show an internal tracking number.
- **FR-003**: Each label that promises a count MUST map to a chooser table that a test compares.
- **FR-004**: The generated references MUST match the labels, so the drift job stays green.

## Success Criteria *(mandatory)*

- **SC-001**: The 15 corrected labels render in the portal and in both references.
- **SC-002**: Each guard fails when its defect returns.

## Out of scope

- Other label style differences, such as title case with a dash suffix on menus 198-202. The portal sweep records those.
