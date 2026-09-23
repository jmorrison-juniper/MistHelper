# Feature Specification: Prune test output from the portal output scan

**Feature Branch**: `fix/3201-scan-prune-test-artifacts`

**Created**: 2026-09-23

**Status**: Implemented

**Input**: Issue #3201. "Every portal run walks 1,522 test-artifact directories, which adds about 56 seconds."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An operation finishes without a one-minute walk of test output (Priority: P1)

A NOC engineer runs an operation in the portal on port 8055. The result appears when the operation finishes its own work. The engineer does not wait an extra minute while the portal lists folders that a test suite left behind.

**Why this priority**: Every one of the 165 portal operations pays this cost. Measured in the container on 2026-09-23, the scan took 56.0 seconds warm and 77.6 seconds cold.

**Independent Test**: Time `OutputFileScanner._read_state()` inside the container before and after the change.

**Acceptance Scenarios**:

1. **Given** a data folder that holds `test-artifacts/` with 1,522 folders, **When** the portal scans after a run, **Then** the scan takes less than 5 seconds.
2. **Given** a test run wrote a file under `test-artifacts/`, **When** an operation finishes, **Then** the result panel does not name that file.
3. **Given** an operation wrote a report at the data root, **When** the scan runs, **Then** the result panel names that report.

### User Story 2 - The next test output folder cannot repeat the defect (Priority: P2)

A developer adds a test suite that writes into a new `data/test-...` folder. The unit tests fail before the change reaches the portal.

**Why this priority**: The defect came from a new test writer. A guard that names only today's folders would miss the next one.

**Independent Test**: Add a new test output folder name to a test module, and run the guard.

**Acceptance Scenarios**:

1. **Given** a test module names `data/<name>` and a word part of `<name>` is `test`, **When** the name is absent from `EXCLUDED_DIR_NAMES`, **Then** the guard fails and names the module.

### Edge Cases

- A file name such as `data/test.csv` is not a folder. The guard skips a name that has a suffix.
- `per-host-logs` holds real SSH transcripts. The prune list must never hold it. An existing test enforces this.
- A pruned folder at any depth is skipped, because the walk filters the folder names at each level.

## Requirements *(mandatory)*

- **FR-001**: The scan MUST NOT list any folder under `test-artifacts` or `test-control-byte-guard`.
- **FR-002**: The scanner MUST publish the count of folders that its most recent walk listed.
- **FR-003**: A guard MUST fail when a test module names a test output folder under `data/` that the scan does not prune.
- **FR-004**: The change MUST NOT prune a folder that holds operation output.

## Success Criteria *(mandatory)*

- **SC-001**: The container scan falls from 56.0 seconds to less than 5 seconds.
- **SC-002**: A site-scoped operation, such as menu 69, finishes at least 40 seconds sooner in the container.
- **SC-003**: Each new guard fails when the prune is removed, and passes when it is restored.

## Out of scope

- The test writers themselves. Issue #3202 tracks them, and the upgrade capture portal agent owns those modules.
- Deleting the existing `data/test-artifacts` folder. It can hold the other agent's live evidence.
