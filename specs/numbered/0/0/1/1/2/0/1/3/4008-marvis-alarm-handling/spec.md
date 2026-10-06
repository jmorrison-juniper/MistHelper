# Feature Specification: Marvis Alarm Handling Package

**Feature Branch**: `4008-marvis-alarm-handling`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #4008 isolates the Marvis alarm modules without compatibility wrappers.

## User Scenarios and Testing

### User Story 1 - Keep the actions package within the structure limit

As a maintainer, I need alarm handling in one package so the actions package has
five structural children.

**Independent Test**: Run the focused structure guard and inspect both package
child sets.

### User Story 2 - Preserve alarm behavior

As an operator, I need alarm joins and acknowledgements to keep their current
imports, symbols, logging, and behavior after the move.

**Independent Test**: Run the focused Marvis action tests and the public symbol
preservation guard.

## Acceptance Criteria

1. `acknowledgement.py` and `alarms.py` exist only under `alarm_handling`.
2. The actions package has `alarm_handling`, `client.py`, `model.py`,
   `operation.py`, and `selection.py`.
3. The alarm handling package has `acknowledgement.py` and `alarms.py`.
4. Active imports, patch targets, logger targets, and documentation use canonical
   paths.
5. Module-level symbols and runtime behavior stay unchanged.
