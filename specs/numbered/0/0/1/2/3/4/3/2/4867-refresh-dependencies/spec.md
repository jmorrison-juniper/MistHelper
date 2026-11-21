# Feature Specification: Refresh And Pin Project Dependencies

**Feature Branch**: `4867-refresh-dependencies`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Get all of our packages up to date and then re-pin them."

## User Scenarios & Testing

### User Story 1 - Refresh Root Python Packages (Priority: P1)

A maintainer refreshes the root Python package set. The maintainer sees that compatible packages use current stable versions. The lock and pip exports remain reproducible.

**Why this priority**: The root package set protects the main application and every local quality gate.

**Independent Test**: Run the UV lock check, export both requirement files, and run dependency parity guards.

**Acceptance Scenarios**:

1. **Given** the root manifest and lock are current, **When** UV performs an upgrade lock, **Then** every compatible package resolves for Python 3.15.
2. **Given** an upgraded lock exists, **When** the pip exports are generated, **Then** both exported requirement files use exact resolved versions.

### User Story 2 - Refresh Ops Platform Packages (Priority: P2)

A maintainer refreshes the Mist Ops Platform dependencies. The platform continues to use supported Python 3.15 packages.

**Why this priority**: The platform has a separate package manifest and test gate.

**Independent Test**: Install the platform dependencies and run the platform test gate.

**Acceptance Scenarios**:

1. **Given** the platform manifest is updated, **When** its test environment is installed, **Then** the environment resolves without conflict.
2. **Given** the platform tests are available, **When** the package refresh is complete, **Then** the platform suite passes with at least 56 percent coverage.

### User Story 3 - Refresh Ops Portal Packages (Priority: P3)

A maintainer refreshes npm packages for the Ops Portal. The manifest and lock describe one consistent dependency set.

**Why this priority**: The portal has npm and browser test dependencies that must remain synchronized.

**Independent Test**: Run npm audit, typecheck, lint, and tests after npm ci.

**Acceptance Scenarios**:

1. **Given** package.json allows an npm update, **When** npm refreshes the dependency graph, **Then** package-lock.json records the exact resolved set.
2. **Given** the refreshed lock is present, **When** npm ci runs, **Then** the portal typecheck, lint, and tests pass.

### User Story 4 - Verify Complete Package Refresh (Priority: P4)

A maintainer verifies the full refresh before merge. The report gives the changed package set and any compatibility exception.

**Why this priority**: A package refresh can affect unrelated gates, so verification must cover every package surface.

**Independent Test**: Run the applicable local gates and compare dependency manifests with their lock records.

**Acceptance Scenarios**:

1. **Given** the package refresh is complete, **When** dependency and security gates run, **Then** no stale manifest or known runtime vulnerability remains.
2. **Given** a package cannot safely advance, **When** the verification reports the package, **Then** the report names the compatibility blocker and the retained floor.

### Edge Cases

- A package has no stable release that supports Python 3.15.
- A package major release changes a public API used by the application.
- A lock update changes a transitive dependency that is not declared directly.
- An open dependency pull request already changes the same manifest.
- A package update fails npm audit or pip-audit.

## Requirements

### Functional Requirements

- **FR-001**: The change MUST refresh compatible packages in the root Python dependency manifest.
- **FR-002**: The change MUST refresh compatible packages in the Mist Ops Platform dependency manifest.
- **FR-003**: The change MUST refresh compatible npm packages in the Ops Portal.
- **FR-004**: The root UV lock MUST remain valid for Python 3.15.
- **FR-005**: requirements.txt MUST contain exact versions derived from the root UV lock.
- **FR-006**: requirements-dev.txt MUST contain exact versions derived from the root UV lock and development extra.
- **FR-007**: The Ops Portal package-lock.json MUST match package.json.
- **FR-008**: The change MUST preserve package constraints that protect supported behavior or prevent a known incompatible release.
- **FR-009**: The change MUST run each applicable dependency, lint, type, test, security, and build gate.
- **FR-010**: The change MUST report each package that remains out of date with a named compatibility reason.
- **FR-011**: The change MUST not expose a credential or secret in a manifest or lock file.
- **FR-012**: The change MUST not close or disable an existing dependency update stream.

### Key Entities

- **Root Python Manifest**: Direct and development package constraints in pyproject.toml.
- **UV Lock**: Resolved package versions and transitive dependencies for the root project.
- **Pip Export**: Exact runtime and development package lists in requirements.txt and requirements-dev.txt.
- **Ops Platform Manifest**: The package constraints and test tools in mist-ops-platform/pyproject.toml.
- **Ops Portal Manifest**: The direct npm dependencies in ops-portal/package.json.
- **Npm Lock**: The exact resolved npm dependency graph in ops-portal/package-lock.json.

## Success Criteria

### Measurable Outcomes

- **SC-001**: UV lock check returns success after the refresh.
- **SC-002**: The two pip exports match the regenerated UV lock with no manual version drift.
- **SC-003**: npm ci completes for the Ops Portal with package-lock.json and package.json synchronized.
- **SC-004**: The applicable local test suites pass after package installation.
- **SC-005**: The runtime pip-audit check reports no known vulnerability.
- **SC-006**: The Ops Portal npm audit reports no high or higher advisory.
- **SC-007**: The final report lists every package that could not advance and its compatibility reason.
- **SC-008**: The final pull request merges without a dependency lock conflict.

## Assumptions

- Python 3.15.2 remains available for local validation.
- Compatible package releases support Python 3.15.
- Existing package constraints protect behavior that a new major release may change.
- Podman container builds that need a local registry remain on GitHub Actions.
- The user wants complete dependency refresh scope across the root project and both portals.
