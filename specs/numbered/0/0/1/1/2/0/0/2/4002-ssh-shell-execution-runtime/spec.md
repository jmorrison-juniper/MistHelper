# Feature Specification: SSH Shell Execution Runtime Package

**Feature Branch**: `4002-ssh-shell-execution-runtime`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #4002: Move the SSH shell execution package under the SSH runtime package.

## User Scenarios & Testing

### User Story 1: Keep the SSH package within the structure limit

As a maintainer, I need shell execution under runtime so the SSH package has five direct structural children.

**Independent Test**: Run the focused SSH structure guard and inspect the two package child counts.

### User Story 2: Preserve shell execution behavior

As a developer, I need `ShellExecutor` and `_CollectState` at the canonical moved module without behavior changes.

**Independent Test**: Run the focused shell executor, console echo, SSH runner, and symbol-preservation tests.

### User Story 3: Remove duplicate import paths

As a maintainer, I need active imports and mock targets to use one canonical runtime path.

**Independent Test**: Search tracked active files and run the focused tests without the old module path.

## Requirements

- **FR-001**: Move `src/operations/execution/ssh/shell_execution/` to `src/operations/execution/ssh/runtime/shell_execution/`.
- **FR-002**: Preserve `ShellExecutor`, `_CollectState`, and all shell execution behavior.
- **FR-003**: Update runtime imports, test imports, mock targets, and the T013b path comment.
- **FR-004**: Do not leave a compatibility wrapper, alias, or fallback import at the old path.
- **FR-005**: Keep `ssh/` at five structural children and `runtime/` at five or fewer.
- **FR-006**: Add the exact old-to-new mapping to the public symbol-preservation guard.
- **FR-007**: Add one unique release-note fragment and the routed Spec Kit artifacts.
- **FR-008**: Do not edit historical specs 1780, 198, 1034, or 2448, performance inventory records, or shared generated records.

## Success Criteria

- **SC-001**: The old shell execution directory is absent.
- **SC-002**: The moved package contains its metadata and executor module.
- **SC-003**: Focused SSH tests pass with canonical imports only.
- **SC-004**: Structure and symbol-preservation guards pass.
- **SC-005**: Required quality gates pass before the local commit.

## Assumptions

- The existing moved module source remains unchanged.
- `runtime/__init__.py` is the required existing runtime package metadata.
- No web interface or Mist Cloud behavior changes are required.
