# Feature Specification: Specs Intake Routing

**Feature Branch**: `3750-spec-intake-routing`

**Feature Path**: `specs/numbered/0/0/1/1/0/0/0/0/3750-spec-intake-routing/`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3750. Freeze new flat `specs/` intake and route new records
through bounded managed roots.

## User Scenarios & Testing

### User Story 1 - Create a routed numeric record (Priority: P1)

As a maintainer, I want a numeric feature record in a bounded route.

**Independent Test**: Create a numeric feature and check its eight route levels.

### User Story 2 - Preserve timestamp records (Priority: P2)

As a maintainer, I want a timestamp feature record under `specs/live/`.

**Independent Test**: Create a timestamp feature and check its managed root.

### User Story 3 - Protect legacy records (Priority: P1)

As a maintainer, I want the guard to preserve old records and reject new flat entries.

**Independent Test**: Add a fabricated direct child and verify that the guard fails.

## Requirements

- **FR-001**: The generator MUST route numeric records through eight base-5 levels.
- **FR-001a**: Numeric feature 3750 MUST use
  `specs/numbered/0/0/1/1/0/0/0/0/3750-spec-intake-routing/`.
- **FR-002**: The generator MUST route timestamp records under `specs/live/`.
- **FR-003**: The guard MUST read a nonempty legacy baseline.
- **FR-004**: The guard MUST report examined counts.
- **FR-005**: The guard MUST reject a new direct child outside the managed roots.
- **FR-006**: The phase records MUST use the numeric route for feature 3750.

## Scope

This phase routes numeric feature 3750 and freezes new flat `specs/` intake.
Timestamp intake remains under `specs/live/`. Changelog migration remains a separate change.
