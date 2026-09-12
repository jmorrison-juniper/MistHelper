# Feature Specification: Simple endpoint family stage one

**Feature Branch**: `feat/1807-simple-endpoint-family`

**Created**: 2026-09-12

**Status**: Implemented

**Input**: Issue #1807 asks MistHelper to group simple Mist `get` and `list`
endpoints by identifier, instead of one menu entry per endpoint.

## Background

The endpoint backlog contains many read-only endpoints with the same shape.
Each operation needs only the Mist session, or one required identifier after the
session. A separate menu entry for each operation makes the menu hard to read.

`CountExporter` proved the family pattern. It gives the operator one prompt for
the operation, then it uses one export path for all related endpoints.

Stage one uses the same pattern for endpoints with no identifier, `org_id`,
`site_id`, or `msp_id`. Stage two will handle endpoints that need more
identifiers.

## User Scenarios and Testing

### User Story 1 - Export a simple global endpoint (Priority: P1)

An operator chooses menu 259, selects one no-identifier operation, and exports
all returned rows through the shared output selector.

**Independent Test**: Mock the SDK call, pagination, and writer. Confirm that
no identifier reaches the SDK call.

### User Story 2 - Export a simple scoped endpoint (Priority: P1)

An operator chooses menu 260, 261, or 262, selects one operation, selects the
required identifier, and exports all returned rows.

**Independent Test**: Mock each identifier prompt and confirm that the SDK call
receives the selected identifier.

### User Story 3 - Reject a bad selection safely (Priority: P2)

An operator enters text or a number outside the prompt range. The exporter logs
the problem and returns to the menu.

**Independent Test**: Mock bad answers and confirm that no SDK call starts.

### User Story 4 - Detect table drift (Priority: P2)

A test imports each table entry, resolves the SDK function, and reads the
signature. The test fails if a table row names a missing function or a wrong
required identifier.

**Independent Test**: Run the table integrity tests without a live Mist token.

## Requirements

- **FR-001**: The feature MUST add four menu entries: 259, 260, 261, and 262.
- **FR-002**: The menu entries MUST be `interactive_safe`.
- **FR-003**: The exporter MUST use `safe_input()` for operation selection.
- **FR-004**: The exporter MUST use `mistapi.get_all()` for pagination.
- **FR-005**: The exporter MUST use `DataExporter.write_with_format_selection()`.
- **FR-006**: The tables MUST contain only operations that resolve in the installed SDK.
- **FR-007**: Each table entry MUST have a primary-key strategy.
- **FR-008**: The known phantom operation MUST not ship in any table.

## Non-Goals

- Stage one does not implement endpoints with two or more required identifiers.
- Stage one does not add filters for optional parameters.
- Stage one does not change a Mist cloud configuration.
