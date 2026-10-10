# Feature Specification: RRM Dry-Run Precedence

**Feature Branch**: `fix/4051-rrm-dry-run-precedence`

**Created**: 2026-10-07

**Status**: Implemented

**Input**: Issue #4051 defines a fail-closed mode policy for destructive menu
291.

## User Scenarios

### User Story 1 - Omitted mode stays safe

As an operator, I need menu 291 to use a dry run when I do not select a mode.

**Acceptance Scenarios**:

1. **Given** no operation argument, CLI mode, or environment value, **When**
   menu 291 runs, **Then** it writes the before capture and sends no request.
2. **Given** a false, empty, or invalid `RRM_DRY_RUN` value, **When** menu 291
   runs, **Then** it sends no request.

### User Story 2 - Live mode needs explicit authority

As an operator, I need a live RRM request to require an explicit live choice
and the existing exact confirmation.

**Acceptance Scenarios**:

1. **Given** `--live-run`, **When** the operator types the exact selected action,
   **Then** the operation can send one request after the before capture.
2. **Given** `--live-run`, **When** the confirmation does not match, **Then** the
   operation sends no request.

### User Story 3 - Keep one environment policy owner

As a maintainer, I need one resolver to own `RRM_DRY_RUN` reads.

**Acceptance Scenarios**:

1. **Given** tracked product Python files, **When** the AST guard runs, **Then**
   it finds one read in `dry_run_policy.py`.
2. **Given** an outside read fixture, **When** the guard validates it, **Then**
   the guard fails and identifies the path.

## Requirements

- **FR-001**: The operation argument MUST use `None` for an absent mode.
- **FR-002**: Precedence MUST be operation argument, CLI mode, environment, then
  forced dry run.
- **FR-003**: A false or invalid environment value MUST NOT authorize live mode.
- **FR-004**: Process environment values MUST override `.env` values.
- **FR-005**: Live mode MUST require `--live-run` or an explicit false operation
  argument.
- **FR-006**: The durable before capture and exact action confirmation MUST
  remain mandatory for live mode.
- **FR-007**: One AST guard MUST scan tracked non-test Python files and reject
  every protected read outside the policy resolver.

## Success Criteria

- **SC-001**: Registered menu tests cover each precedence conflict and absence.
- **SC-002**: The guard reports a nonzero file count and exactly one read site.
- **SC-003**: The negative fixture proves that an outside read fails.
- **SC-004**: Operator documentation states that menu 291 defaults to dry run.
