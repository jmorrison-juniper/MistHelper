# Feature Specification: Locked Dependency Exports

**Feature Branch**: `3999-locked-dependency-exports`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User request: "Do all you need to do to get it successfully merged?"

## User Scenarios & Testing

### User Story 1 - Install compatible dependencies (Priority: P1)

An operator installs MistHelper from either the runtime or development requirements file. Both files describe the same locked package versions and preserve platform-specific rules.

**Why this priority**: Mismatched exports can install different packages or violate the project constraints.

**Independent Test**: Compare both committed exports with fresh exports from the lock.

**Acceptance Scenarios**:

1. **Given** a valid lock, **When** the runtime and development exports are generated, **Then** both committed files match their generated output.
2. **Given** a package has a project version limit or platform marker, **When** exports are generated, **Then** each limit and marker remains effective.

### Edge Cases

- If an available package version exceeds a project limit, keep the latest version that satisfies the limit.
- If a runtime package changes, update the development export that also contains runtime packages.

## Requirements

### Functional Requirements

- **FR-001**: The lock MUST hold each selected package version within its declared project limits.
- **FR-002**: The runtime and development requirements files MUST match their locked exports.
- **FR-003**: The exports MUST preserve platform markers from the lock.
- **FR-004**: A dependency update MUST NOT change the existing lock workflow.
- **FR-005**: The project MUST retain its Gunicorn limit below version 27.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Both requirements exports match the lock output with zero differences.
- **SC-002**: All dependency export and lock checks pass.
- **SC-003**: The dependency audit reports zero known vulnerabilities.

## Assumptions

- `uv.lock` remains the source of truth for package versions.
- The requested update includes compatible package upgrades only.
- Gunicorn 27 is excluded because the project limits Gunicorn to versions below 27.
