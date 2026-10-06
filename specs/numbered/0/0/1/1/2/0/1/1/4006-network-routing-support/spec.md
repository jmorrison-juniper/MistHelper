# Feature Specification: Network Routing Support Package

**Feature Branch**: `network-routing-support-4006`

**Created**: 2026-10-06

**Status**: Implemented

**Input**: Issue #4006 moves three routing support modules into one package.

## User Scenarios and Testing

### User Story 1 - Keep the network package within the structure limit

As a maintainer, I need related support modules in one package so the network
package has five direct structural children.

**Independent Test**: Run the focused structure guard. It must report five
network children and three support children.

### User Story 2 - Preserve routing behavior

As an operator, I need routing commands to keep their current behavior after the
module move.

**Independent Test**: Run the routing utility and unparseable-response tests.
The tests must use only the canonical support paths.

## Requirements

- **FR-001**: Move the display, parsing, and payload modules into `support/`.
- **FR-002**: Remove each old module path without a wrapper or alias.
- **FR-003**: Preserve all module-level symbols and behavior.
- **FR-004**: Update active imports, mock targets, logger names, and links.
- **FR-005**: Require exactly five network children and three support children.
- **FR-006**: Do not edit historical specifications or performance inventories.

## Success Criteria

- **SC-001**: The focused structure guard reports five network children.
- **SC-002**: The focused structure guard reports three support children.
- **SC-003**: Focused routing tests and symbol guards pass.
- **SC-004**: Generated WebSocket menu API pages use canonical source links.

## Assumptions

- The move changes package ownership only.
- The existing routing tests define the behavior contract.
- The three routed specification files are the only feature records.
