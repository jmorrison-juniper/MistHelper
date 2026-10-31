# Feature Specification: Local build revision

**Feature Branch**: `jmorrison-juniper-local-build-revision`

**Created**: 2026-10-31

**Status**: Approved for implementation

**Input**: Issue #4165 requests revision labels for local builds and revision comparisons against `origin/main`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify a local build (Priority: P1)

An operator builds an image and reads its source revision without comparing individual source files.

**Why this priority**: An absent revision prevents reliable identification of a deployed local image.

**Independent Test**: Build through a simulated provider and inspect the revision passed to the build.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the operator builds, **Then** the image label holds the full checkout commit.
2. **Given** a changed checkout, **When** the operator builds, **Then** the label holds the full commit followed by `-dirty`.
3. **Given** a failed revision read, **When** the operator builds, **Then** the command stops before the provider builds.

### User Story 2 - Compare a local image (Priority: P1)

An operator checks a local image against the known main revision with the same comparison used for a published image.

**Why this priority**: Operators need the same freshness decision for both image sources.

**Independent Test**: Supply clean and dirty labels to the revision command with controlled repository history.

**Acceptance Scenarios**:

1. **Given** a clean label equal to main, **When** the operator checks it, **Then** the command reports current and succeeds.
2. **Given** a clean older label, **When** only non-image files changed, **Then** the command reports current and succeeds.
3. **Given** a clean older label, **When** image files changed, **Then** the command names those files and fails.
4. **Given** a dirty label, **When** the operator checks it, **Then** the command explains that uncommitted content prevents verification and fails.

### Edge Cases

- Staged, unstaged, and untracked non-ignored files all mark a build dirty.
- Ignored runtime files do not mark a build dirty.
- An absent label cannot identify either the image source or its freshness.
- Malformed labels and unknown commits fail with an explicit cause.
- Build success and failure both preserve the caller environment.
- Existing stale-build refusal and local-only stale image tags remain unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each helper build MUST record its full source commit in the image revision label.
- **FR-002**: Each changed checkout MUST append `-dirty` to the recorded revision.
- **FR-003**: The revision command MUST compare clean local labels through the existing image-input comparison.
- **FR-004**: A dirty label MUST NOT receive a current result, because its commit cannot describe the complete image content.
- **FR-005**: An unavailable source revision or checkout status MUST stop the build with an explicit cause.
- **FR-006**: Temporary build metadata MUST NOT change the caller environment after the build.
- **FR-007**: The change MUST preserve the existing stale-build policy and CI revision labels.

### Key Entities

- **Image revision**: A full source commit with an optional dirty marker.
- **Image inputs**: The existing source path set used for freshness decisions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All clean-build cases identify the exact source commit.
- **SC-002**: All dirty-build cases identify uncommitted content and refuse a verified-current result.
- **SC-003**: All existing clean-image freshness cases keep their previous result.
- **SC-004**: No revision-read failure starts a provider build.

## Assumptions

- Dirty means any staged, unstaged, or untracked non-ignored change in the repository.
- A dirty image cannot prove equivalence with a commit, even when its base commit equals main.
- The revision command continues to use the locally available `origin/main` reference.
- Direct container builds outside the helper remain outside this issue.
