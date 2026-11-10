# Feature Specification: Python 3.15 Baseline

**Feature Branch**: `4734-python-315-baseline`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User request to remove local virtual environments, set Python 3.15 as the minimum, create a new environment, verify script startup, and merge the change.

## User Scenarios & Testing

### User Story 1 - Create a Supported Local Environment (Priority: P1)

An operator creates a clean local environment with stable Python 3.15 and starts MistHelper.

**Why this priority**: The operator needs a working environment before using or testing MistHelper.

**Independent Test**: Create a clean Windows environment and start the MistHelper command without a Python version error.

**Acceptance Scenarios**:

1. **Given** stable Python 3.15 is available, **When** an operator follows the setup guide, **Then** the new environment uses Python 3.15.
2. **Given** the new environment is active, **When** the operator starts MistHelper, **Then** the command exits without a startup error.

### User Story 2 - Install Supported Packages (Priority: P2)

A maintainer installs either Python project with Python 3.15 or newer and receives a clear rejection below that version.

**Why this priority**: Package metadata must match the runtime that maintainers test and support.

**Independent Test**: Check package metadata and installation behavior with Python 3.14 and 3.15.

**Acceptance Scenarios**:

1. **Given** Python 3.14, **When** a maintainer installs either project, **Then** the package rejects the interpreter.
2. **Given** Python 3.15, **When** a maintainer installs either project, **Then** dependency resolution completes.

### User Story 3 - Build and Release on Python 3.15 (Priority: P3)

A maintainer uses the supported Python version for CI, release builds, and product containers.

**Why this priority**: Published artifacts must use the same supported runtime as local development.

**Independent Test**: Run the relevant build and test jobs with Python 3.15.

**Acceptance Scenarios**:

1. **Given** a change to the Python support configuration, **When** CI runs, **Then** its Python jobs use Python 3.15.
2. **Given** a release or product container build, **When** the build completes, **Then** the artifact uses Python 3.15.
3. **Given** a merged image and operator approval, **When** deployment completes, **Then** its revision matches the merge commit and its health checks pass.

### Edge Cases

- If a stable Python 3.15 installer is unavailable, the setup process must report the cause.
- If a required dependency does not support Python 3.15, the build must stop and show a failure message.
- If a virtual environment is in use, the cleanup must retain it and report the process ID.
- If dependency exports change, platform markers must remain correct for each supported operating system.
- If deployment approval is absent, the process must not deploy the image.

## Requirements

### Functional Requirements

- **FR-001**: The MistHelper package MUST require Python 3.15 or newer.
- **FR-002**: The Mist Ops Platform package MUST require Python 3.15 or newer.
- **FR-003**: The setup process MUST create a local environment with stable Python 3.15.
- **FR-004**: CI, release builds, and product containers MUST use Python 3.15 or newer.
- **FR-005**: Setup instructions MUST state the Python 3.15 minimum.
- **FR-006**: Dependency lock and export files MUST install on Python 3.15 and retain valid platform markers.
- **FR-007**: The standard startup check MUST confirm that MistHelper starts in a fresh Python 3.15 environment.
- **FR-008**: Cleanup MUST remove each `.venv` directory in a registered MistHelper worktree only after it confirms that no process uses it.
- **FR-009**: Cleanup MUST NOT remove virtual environments outside registered MistHelper worktrees.
- **FR-010**: The lock MUST resolve `importlib-metadata` 10.2.0, `openai` 3.48.0, and `pypdfium2` 5.15.2. Both exports MUST come from the lock, and the runtime export MUST preserve all 11 original platform markers.
- **FR-011**: After merge, the release process MUST verify the image revision and deployment health.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both Python packages accept Python 3.15.2 and reject Python 3.14.
- **SC-002**: All first-party runtime, setup, CI, release, and container declarations use Python 3.15 or newer.
- **SC-003**: A clean Windows environment reports Python 3.15.2 and starts MistHelper with exit code zero.
- **SC-004**: Dependency installation and all relevant required checks pass with Python 3.15.
- **SC-005**: Cleanup removes every pre-existing registered `.venv`. Setup then creates one fresh environment in the feature worktree and removes no other path.
- **SC-006**: The deployed image revision matches the merge commit, and the container and portal health checks pass after approved deployment.

## Assumptions

- Python 3.15.2 is the current stable Python 3.15 release.
- The Python 3.15 minimum applies to both the root project and the separately configured Mist Ops Platform.
- The product continues to support Windows, macOS, and Linux.
- Cleanup covers `.venv` directories in registered MistHelper worktrees after an active-process check. Virtual environments outside those worktrees remain out of scope.
- The runtime dependency updates from issue #4727 remain in scope, but open pull requests retain ownership of their files.
- The branch must pass repository checks and use the protected pull request flow. This work does not bypass branch protection.
- Production deployment requires separate explicit approval.
