# Feature Specification: Endpoint family stage two

**Feature Branch**: `feat/1807-endpoint-family-stage-two`

**Created**: 2026-09-12

**Status**: Implemented

**Input**: Issue #1807 asks MistHelper to finish the endpoint family backlog.

## Background

Stage one added four menus for simple endpoint calls. Those calls need no
identifier, or they need one organization, site, or MSP identifier.

The remaining read-only endpoint issues need more prompt flows. Many operations
share the same identifier tuple, so one menu row per operation would expand the
main menu too much.

Stage two adds grouped menus. The operator selects the operation, then enters
the identifiers in the SDK signature order.

## User Scenarios and Testing

### User Story 1 - Export an SLE endpoint (Priority: P1)

An operator chooses menu 263, selects an SLE operation, enters the site, scope,
scope identifier, metric, and optional classifier when required, then exports
the rows.

**Independent Test**: Mock all prompts and assert the SDK call receives values
in the table order.

### User Story 2 - Export a detail endpoint (Priority: P1)

An operator chooses menu 265, 266, or 267, selects one operation, and enters the
required identifiers. The exporter writes the result through the shared writer.

**Independent Test**: Parametrize each table row and verify its SDK signature.

### User Story 3 - Reject a bad selection safely (Priority: P2)

An operator enters text or a number outside the prompt range. The exporter logs
the problem and returns to the menu.

**Independent Test**: Mock bad answers and confirm that no SDK call starts.

### User Story 4 - Detect a phantom entry (Priority: P2)

A test imports each row, resolves the SDK function, and checks the required
identifier tuple. The test fails if a table row names a missing function.

**Independent Test**: Run the table integrity tests without a live Mist token.

## Requirements

- **FR-001**: The feature MUST add menus 263 through 268.
- **FR-002**: The menu entries MUST be `interactive_safe`.
- **FR-003**: The exporter MUST use `safe_input()` for operation selection and raw identifiers.
- **FR-004**: The exporter MUST use `mistapi.get_all()` for pagination.
- **FR-005**: The exporter MUST use `DataExporter.write_with_format_selection()`.
- **FR-006**: The tables MUST contain only operations that resolve in the installed SDK.
- **FR-007**: Each table entry MUST have a primary-key strategy.
- **FR-008**: The active `optimizeInstallerRrm` endpoint MUST not ship in this read-only family.
- **FR-009**: The known phantom operation MUST not ship in any table.

## Non-Goals

- Stage two does not add optional filter prompts.
- Stage two does not change a Mist cloud configuration.
- Stage two does not run the installer radio optimization endpoint.
