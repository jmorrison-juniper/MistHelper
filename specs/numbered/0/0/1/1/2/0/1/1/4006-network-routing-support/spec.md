# Feature Specification: Network Routing Support Package

**Feature Branch**: `4006-network-routing-support`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #4006: isolate network routing support modules."

## User Scenarios & Testing

### User Story 1 - Keep the routing package within the structure limit

As a maintainer, I need shared routing helpers in one package, so the network package remains easy to navigate.

**Independent Test**: Run the focused routing structure guard.

### User Story 2 - Preserve routing behavior

As a developer, I need canonical imports and patch targets, so routing behavior remains unchanged.

**Independent Test**: Run the focused routing tests and the public symbol guard.

## Requirements

- **FR-001**: Move the display, parsing, and payload modules into `network/support/`.
- **FR-002**: Preserve all module-level symbols and runtime behavior without wrappers.
- **FR-003**: Update active imports, tests, logger names, payload documentation paths, and generated menu pages.
- **FR-004**: Keep the network package at five structural children and support at three.
- **FR-005**: Do not edit historical specifications or performance inventory records.

## Success Criteria

- **SC-001**: The focused structure guard reports counts of five and three.
- **SC-002**: Focused routing tests and symbol checks pass.
- **SC-003**: No active file retains an old routing support path.
