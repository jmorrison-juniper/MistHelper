# Feature Specification: Runtime Dependency Exports

**Feature Branch**: `chore/4727-runtime-dependency-exports`

**Created**: 2026-11-10

**Status**: Draft

**Input**: Issue #4727: align runtime dependency versions and generated installation exports while preserving platform compatibility.

## User Scenarios & Testing

### User Story 1 - Install with aligned dependencies (Priority: P1)

An operator installs MistHelper through a supported installation method and receives the same approved package versions.

**Why this priority**: Dependency drift can break setup or run different package versions across installation methods.

**Independent Test**: Compare the resolved packages in each supported installation export.

**Acceptance Scenarios**:

1. **Given** the approved package versions, **When** an operator uses either supported installation export, **Then** each export selects the same version for all three requested packages.
2. **Given** the reviewed update set, **When** a maintainer resolves packages, **Then** the lock includes each compatible update and respects existing constraints.
3. **Given** the runtime dependency conditions before the update, **When** a maintainer regenerates the exports, **Then** all 11 existing runtime platform conditions remain unchanged.

### User Story 2 - Verify dependency integrity (Priority: P2)

A maintainer checks that the package records agree, that package constraints remain valid, and that available security audits report their results.

**Why this priority**: A consistent dependency set reduces installation failures and gives maintainers clear security evidence.

**Independent Test**: Run checks for dependency parity, package consistency, and audit results.

**Acceptance Scenarios**:

1. **Given** updated package records, **When** a maintainer runs the required checks, **Then** checks for parity and package consistency pass.
2. **Given** an unaudited dependency, **When** the audit completes, **Then** the report names it as unaudited.
3. **Given** the dependency update is ready for release, **When** a maintainer records the change, **Then** one release note describes the update.

### Edge Cases

- If a requested version violates a parent package constraint, the maintainer records the conflict and does not override the constraint.
- If export generation changes or removes a platform condition, the parity check fails.
- If an audit tool cannot inspect a dependency source, the audit report identifies the coverage gap.

## Requirements

### Functional Requirements

- **FR-001**: The dependency records MUST use the approved versions for `importlib-metadata` 10.2.0, `openai` 3.48.0, and `pypdfium2` 5.15.2.
- **FR-002**: The resolved package set MUST include every compatible update in the reviewed issue preview and MUST respect existing package constraints.
- **FR-003**: The runtime and development installation exports MUST match the resolved package records.
- **FR-004**: Maintainers MUST retain all 11 existing runtime platform conditions in the runtime dependency exports.
- **FR-005**: Maintainers MUST run parity and package consistency checks after they regenerate the exports.
- **FR-006**: The security audit MUST report no known vulnerabilities in packages it can audit from both exports and list each dependency source it cannot audit.
- **FR-007**: The change MUST include one release-note fragment.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All three requested package versions match the approved versions in the lock and both exports.
- **SC-002**: Every compatible update in the reviewed dependency set appears in the resolved package records.
- **SC-003**: All 11 existing runtime platform conditions remain present and unchanged.
- **SC-004**: The dependency parity and package consistency checks pass.
- **SC-005**: Audits of both exports report zero known vulnerabilities for checked packages and name each dependency source they cannot audit.
- **SC-006**: Operators can use either supported installation method without package-version drift.
- **SC-007**: The change includes one release note.

## Assumptions

- The target package versions are the versions requested in issue #4727.
- The reviewed issue preview defines the compatible package updates that belong in this change.
- Existing platform conditions define supported runtime platforms and must not be broadened or removed.
- A dependency source that an audit tool cannot inspect does not count as audited. The maintainer MUST report it.
- Maintainers MUST keep package updates that violate parent constraints out of scope until they resolve those constraints.
