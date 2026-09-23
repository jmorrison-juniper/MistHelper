# Feature Specification: Keep plumbing lines out of the Execution Log

**Feature Branch**: `fix/3229-log-plumbing` | **Created**: 2026-09-23 | **Status**: Implemented

**Input**: Issue #3229. "The Execution Log shows internal dependency lines that bury the operation result."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The operator reads the result, not the plumbing (Priority: P1)

A NOC engineer runs menu 4. The Execution Log shows what the operation did, such as "! 0 current guest users exported to OrgCurrentGuests.csv". The Debug Log panel holds the dependency resolution lines.

**Acceptance Scenarios**:

1. **Given** a run that resolves its dependencies, **When** the Execution Log renders, **Then** no `Resolving ...` line appears in it.
2. **Given** the same run, **When** the engineer opens the Debug Log panel, **Then** each `Resolving ...` line appears there.
3. **Given** the resolver logs a WARNING, **When** the log renders, **Then** the warning appears in the Execution Log.

## Requirements *(mandatory)*

- **FR-001**: The portal MUST route the eight plumbing INFO messages to the debug channel.
- **FR-002**: `script.log` MUST keep each message at INFO. The repository logging standard requires it.
- **FR-003**: A test MUST fail when a plumbing message in the source no longer matches a routing prefix.

## Out of scope

- A change to the log level at the source.
