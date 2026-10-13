# Feature Specification: Prevent Unsafe Stale Builds

**Feature Branch**: `fix/4164-compose-stale-build`

**Created**: 2026-10-13

**Status**: Draft

**Input**: Issue #4164: Stop container builds from stale checkouts unless the operator gives an explicit override.

## User Scenarios & Testing

### User Story 1 - Stop a stale build (Priority: P1)

An operator starts a local image build from a checkout that does not contain the latest main branch. The tool must stop before it can replace the published image.

**Why this priority**: A stale image can downgrade a running service and remove its revision label.

**Independent Test**: Place the checkout behind main, start a build without an override, and confirm that no build starts.

**Acceptance Scenarios**:

1. **Given** the checkout is behind main, **When** the operator starts a build without an override, **Then** the tool reports the number of missing commits and stops before the build.
2. **Given** the checkout matches or is ahead of main, **When** the operator starts a build, **Then** the tool continues with the existing build behavior.
3. **Given** the tool cannot update its knowledge of main, **When** the operator starts a build, **Then** the tool stops before the build and reports the update failure.

### User Story 2 - Allow a local stale build (Priority: P2)

An operator can request a stale build when testing old code. The tool must keep that image separate from the published image.

**Why this priority**: Operators sometimes need an older checkout, but a test image must not replace the published image.

**Independent Test**: Place the checkout behind main, start a build with the explicit override, and confirm that the build uses a local-only image name.

**Acceptance Scenarios**:

1. **Given** the checkout is behind main, **When** the operator starts a build with the explicit override, **Then** the build uses a local-only image name and leaves the published image name unchanged.
2. **Given** the operator uses the override for a current checkout, **When** the build starts, **Then** the override does not change normal compose command behavior.

### Edge Cases

- If fetching the latest main branch fails, the tool must stop without starting a build.
- If the checkout has diverged from main and is also behind, the tool must treat it as stale.
- If the checkout is ahead of main and is not behind, the tool may use the existing build behavior.
- The override must not reach the compose provider as an unsupported provider argument.

## Requirements

### Functional Requirements

- **FR-001**: The tool MUST refresh its knowledge of the latest main branch before each local image build.
- **FR-002**: The tool MUST stop the build if it cannot refresh the latest main branch.
- **FR-003**: The tool MUST count commits that main contains and the checkout does not contain.
- **FR-004**: The tool MUST stop a stale build by default and report the number of missing commits.
- **FR-005**: The tool MUST allow a stale build only when the operator gives an explicit override.
- **FR-006**: An allowed stale build MUST use a local-only image name and MUST NOT replace the published image name.
- **FR-007**: A build from a current checkout MUST keep the existing image naming behavior.
- **FR-008**: The override MUST apply only to the build command and MUST NOT alter other compose operations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every stale checkout without an override is stopped before the image build starts.
- **SC-002**: Every approved stale build uses a local-only image name and leaves the published image name unchanged.
- **SC-003**: Every current checkout keeps the existing build result.
- **SC-004**: Every failed update check stops the build and reports the reason.

## Assumptions

- Operators use the documented compose helper for local image builds.
- The helper uses `misthelper:local` as the local-only image name.
- A checkout ahead of main is not stale unless it is also behind main.
