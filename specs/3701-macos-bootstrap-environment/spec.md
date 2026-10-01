# Feature Specification: macOS bootstrap environment

**Feature Branch**: `jmorrison-juniper-macos-bootstrap-environment`

**Created**: 2026-10-01

**Status**: Specified

**Input**: Repair the confirmed environment creation failure in issue #3701.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a working environment (Priority: P1)

A contributor creates a fresh worktree environment on macOS without a manual recovery command.

**Why this priority**: The current bootstrap stops before it installs any dependency.

**Independent Test**: Create one real environment with the supported native interpreter. Run its interpreter and import its standard modules.

**Acceptance Scenarios**:

1. **Given** a fresh macOS worktree, **When** the bootstrap creates its environment, **Then** the interpreter starts and pip is available.
2. **Given** a supported POSIX platform, **When** the bootstrap creates its environment, **Then** interpreter links preserve the base installation.
3. **Given** Windows, **When** the bootstrap creates its environment, **Then** interpreter copies and the Windows interpreter path remain selected.

---

### User Story 2 - Keep optional installer support (Priority: P2)

A contributor can create an environment when uv is absent.

**Why this priority**: The existing pip installation path must remain available.

**Independent Test**: Create a real environment without uv discovery. Run the existing offline installer contracts.

**Acceptance Scenarios**:

1. **Given** no uv executable, **When** environment creation runs, **Then** the standard library creates the environment and supplies pip.
2. **Given** either supported installer, **When** dependencies install, **Then** source selection, transport controls, and credential protection remain unchanged.

---

### User Story 3 - Recover a partial environment (Priority: P3)

A contributor uses the explicit recreation command after an earlier copied-interpreter failure.

**Why this priority**: An existing interpreter path does not prove that an earlier environment works.

**Independent Test**: Recreate an owned partial environment. Confirm that the repaired interpreter works and a neighboring directory remains unchanged.

**Acceptance Scenarios**:

1. **Given** an existing environment without a recreation request, **When** creation runs, **Then** the existing environment remains unchanged.
2. **Given** an owned partial environment, **When** recreation runs, **Then** only that environment is replaced.
3. **Given** a creation error, **When** creation stops, **Then** the error propagates without a success report.

### Edge Cases

- An environment path contains spaces.
- A partial environment contains the failed copied interpreter.
- The platform is Windows, Linux, or macOS.
- uv is absent.
- Environment creation or directory removal raises an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bootstrap must create a working environment with the supported macOS interpreter.
- **FR-002**: POSIX creation must preserve interpreter library resolution through links. Windows creation must retain copies.
- **FR-003**: Environment creation must not require uv or change installer selection.
- **FR-004**: Creation must retain pip and must not request a dependency upgrade.
- **FR-005**: Existing environment reuse and explicit recreation must retain their current behavior.
- **FR-006**: Creation errors must propagate without a success report.
- **FR-007**: Documentation must distinguish fresh creation from explicit recovery of an earlier partial environment.
- **FR-008**: Tests must cover native creation, platform decisions, recreation, reuse, failure, and adjacent bootstrap behavior.
- **FR-009**: Tests must count measured environments and decisions. A direct negative case must prove that the checks can fail.
- **FR-010**: The repair must remain unpublished until the parent grants the full verified-main SHA for position 34.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The original native copied-interpreter failure is recorded before implementation.
- **SC-002**: Real repaired environments start, import required modules, and report distinct environment and base prefixes.
- **SC-003**: Three platform decisions select copies only for Windows.
- **SC-004**: Focused adjacent contracts pass without browser downloads, cloud calls, or production resources.
- **SC-005**: Every changed executable region has coverage of at least 80 percent.
- **SC-006**: The local handoff includes a clean committed tree, exact evidence, and no publication or actual-main claim.

## Assumptions

- Python 3.13 or newer is required.
- The original sanitized trace in issue #3701 is the defect record.
- The existing installation policy from issue #3399 remains authoritative.
- The parent confirms documentation ownership before that file changes.
- Native Windows, containers, live APIs, and publication are outside this local preparation.
- The separate pip-audit temporary-environment defect in issue #3612 remains outside this repair.
