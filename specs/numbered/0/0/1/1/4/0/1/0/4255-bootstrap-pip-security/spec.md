# Feature Specification: Bootstrap pip security

**Feature Branch**: `jmorrison-juniper-bootstrap-pip-security`

**Created**: 2026-10-26

**Status**: Approved

**Input**: Repair the bootstrap pip advisories from issue #4255 and preserve related issue #4360.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a safe development environment (Priority: P1)

A developer runs the worktree bootstrap and receives an installer without the reported pip advisories.

**Why this priority**: The current bootstrap leaves a vulnerable installer in each new development environment.

**Independent Test**: Create an environment through the bootstrap and audit its installed packages.

**Acceptance Scenarios**:

1. **Given** a new worktree, **When** bootstrap succeeds, **Then** its pip version has none of the four reported advisories.
2. **Given** an existing environment with vulnerable pip, **When** bootstrap succeeds, **Then** its pip version meets the same security requirement.
3. **Given** either supported installer, **When** package installation fails, **Then** bootstrap reports failure and stops.

### Edge Cases

- The selected index cannot supply a safe pip release.
- uv is absent, so bootstrap uses environment-local pip.
- The environment already contains a newer safe pip release.
- A worktree has only one requirement file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A successful requirement installation MUST install pip 26.2.2 or newer.
- **FR-002**: Bootstrap MUST preserve the selected installer, package-source policy, interpreter path, and failure behavior.
- **FR-003**: Bootstrap MUST NOT change runtime requirement declarations or suppress advisory findings.
- **FR-004**: A regression test MUST reject the previous installation command for both supported installers.
- **FR-005**: Validation MUST report the requirements-audit result separately from the installed-environment audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A newly prepared environment has zero reported pip advisory findings.
- **SC-002**: All focused bootstrap tests pass for both installer choices and all supported interpreter path layouts.
- **SC-003**: The repair changes zero runtime dependency declarations.

## Assumptions

- pip 26.2.2 is the minimum verified safe release recorded in issue #4360.
- The existing package source can supply a supported release that meets the minimum version.
- The independent temporary-environment `ensurepip` failure remains outside this repair.
- Both issue records remain open until merged-source evidence supports closure.
