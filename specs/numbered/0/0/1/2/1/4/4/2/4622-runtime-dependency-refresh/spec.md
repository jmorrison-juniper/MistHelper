# Feature Specification: Runtime Dependency Refresh

**Feature Branch**: `chore/4622-runtime-dependency-refresh`

**Created**: 2026-11-06

**Status**: Draft

**Input**: Issue #4622 requests a safe refresh of the current runtime dependency versions.

## User Scenarios & Testing

### User Story 1 - Use refreshed runtime packages (Priority: P1)

An operator installs the refreshed MistHelper release and receives the requested runtime package versions.

**Why this priority**: Current package versions must resolve consistently for installation and operation.

**Independent Test**: Compare the requested runtime versions with the locked versions and both exported dependency files.

**Acceptance Scenarios**:

1. **Given** the requested runtime versions, **When** the dependency set is resolved, **Then** the lock records matching versions for all 23 requested updates.
2. **Given** the resolved lock, **When** the runtime and development dependency exports are generated, **Then** both exports match the lock.

### User Story 2 - Keep platform support intact (Priority: P1)

An operator installs MistHelper on a supported platform and retains the existing platform-specific package rules.

**Why this priority**: A dependency refresh must not remove or change supported platform conditions.

**Independent Test**: Compare platform markers before and after the refresh.

**Acceptance Scenarios**:

1. **Given** the current 11 platform markers, **When** the dependency files are refreshed, **Then** all 11 markers remain unchanged.
2. **Given** the refreshed dependency set, **When** the declared package versions are checked against the lock, **Then** declaration parity passes.

### Edge Cases

- If a requested version cannot resolve, do not publish a lock or exports that omit the request.
- If a platform marker changes or disappears, reject the refresh.
- If a package index rewrites package identity, use the public package index and verify the resulting lock identity.

## Requirements

### Functional Requirements

- **FR-001**: The refreshed dependency set MUST include all 23 requested runtime version updates.
- **FR-002**: The lock and both exported dependency files MUST contain matching package identities and versions.
- **FR-003**: The refresh MUST preserve all 11 existing platform markers.
- **FR-004**: The lock MUST include transitive dependencies required by the requested versions, including `tzdata==2026.6`.
- **FR-005**: The refresh MUST NOT change runtime source, dependency manifests, tests, workflows, or governance settings.
- **FR-006**: The change MUST include one unique release-note fragment for issue #4622.
- **FR-007**: The existing dependency export, lock, declaration parity, and SDK checks MUST pass.

## Key Entities

- **Requested dependency**: A runtime package and version requested for this refresh.
- **Lock record**: A resolved package identity and version, including required transitive packages and platform conditions.
- **Dependency export**: A generated runtime or development package list that reflects the lock.
- **Platform marker**: A condition that selects a dependency for a supported platform.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 23 requested runtime updates have matching resolved versions in the lock and both exports.
- **SC-002**: All 11 platform markers remain unchanged after the refresh.
- **SC-003**: Dependency export, lock, declaration parity, and SDK checks report no failures.
- **SC-004**: The dependency audit, package consistency check, and import checks report no failures.
- **SC-005**: One unique release-note fragment names issue #4622.

## Assumptions

- The current `requirements.txt` is the authoritative request for runtime package updates.
- UV lock resolution supplies the package identity and platform-specific resolution needed by the exports.
- Existing dependency guards provide the required failure checks. This feature adds no tests.
- Parent work owns dependency files, validation, the release-note fragment, commit, and pull request.
