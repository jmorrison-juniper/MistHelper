# Feature Specification: Dependency lock group

**Feature Branch**: `dependabot/pip/types-paramiko-5.1.0.20261030`

**Created**: 2026-11-15

**Status**: Specified

**Input**: Repair the shared dependency failures under issue #4811 in pull request #4806.
Group compatible updates that change the same dependency files.
Preserve each original revision and leave publication and merges to the coordinator.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install one consistent dependency set (Priority: P1)

A contributor installs the requested updates without different results between the supported installation methods.

**Why this priority**: Inconsistent dependency records stop installation and the required checks.

**Independent Test**: Compare all declared packages, the resolved package records, and both installation lists.

**Acceptance Scenarios**:

1. **Given** five compatible updates, **When** a contributor resolves dependencies, **Then** one consistent record includes all five requested versions.
2. **Given** a stale installation list, **When** the consistency check runs, **Then** it fails and names the stale input.
3. **Given** an incompatible update, **When** resolution or compatibility checks fail, **Then** the report identifies the blocker without hiding it.

### User Story 2 - Preserve the original work (Priority: P1)

A maintainer can recover every original revision before replacement work changes a branch.

**Why this priority**: Combining updates must not discard an original change.

**Independent Test**: Resolve each recovery reference and compare its full revision with the inspected original revision.

**Acceptance Scenarios**:

1. **Given** five original revisions, **When** local replacement work starts, **Then** five local recovery references retain those exact revisions.
2. **Given** no publication permission, **When** local work finishes, **Then** no remote branch or pull request metadata changes.
3. **Given** an unmerged replacement, **When** validation finishes, **Then** every original pull request and issue remains open.

### User Story 3 - Check the isolated application (Priority: P2)

An operator can distinguish a local application check from an authenticated staging check.

**Why this priority**: A local check must not imply that a cloud request succeeded.

**Independent Test**: Run the application checks in an isolated project container and record the result and resource removal.

**Acceptance Scenarios**:

1. **Given** the updated environment, **When** local checks run, **Then** dependency consistency and relevant application behavior pass.
2. **Given** no authorized staging token or verified staging organization, **When** smoke testing runs, **Then** the report states that authenticated staging testing did not run.
3. **Given** a temporary container, **When** testing ends, **Then** its named resources no longer exist.

### Edge Cases

- An original branch changes after inspection. Retain the inspected revision and require a fresh ownership check before publication.
- An update introduces a new incompatible interface. Do not repair unrelated product code within this dependency group.
- An installation or container prerequisite is unavailable. Report the exact failure and leave the affected acceptance criterion incomplete.
- Another merge advances the target branch. Rebase and repeat affected checks before publication.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The group MUST preserve the requested versions and issue mapping below.
- **FR-002**: The resolved dependency records and both generated installation lists MUST agree with the declarations.
- **FR-003**: The package manager MUST generate the resolved record and installation lists without manual lock edits.
- **FR-004**: Five recovery references MUST retain the inspected original revisions before replacement work.
- **FR-005**: Validation MUST cover consistency, updated tool compatibility, and the isolated application.
- **FR-006**: Authenticated staging requests MUST require authorized credentials and a verified staging organization.
- **FR-007**: Local work MUST NOT publish, change pull request metadata, close issues, merge, or enable automatic merging.
- **FR-008**: The group MUST NOT change application code, workflow files, baselines, exporters, or dependency update streams.

### Key Entities

| Issue | Original pull request | Package | Requested version |
| --- | --- | --- | --- |
| #4807 | #4802 | stevedore | 5.10.0 |
| #4808 | #4803 | ruff | 0.17.5 |
| #4809 | #4804 | gunicorn | 27.0.0 |
| #4810 | #4805 | uv | 0.13.8 |
| #4811 | #4806 | types-paramiko | 5.1.0.20261030 |

The group root is issue #4811. Pull request #4806 is the proposed replacement location.
The coordinator must verify a merged replacement on `main` before closing an original issue or pull request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five requested versions appear in one consistent dependency set, with zero consistency defects.
- **SC-002**: All five original revisions remain recoverable with exact revision equality.
- **SC-003**: Every selected compatibility check passes, or the report gives its exact blocker.
- **SC-004**: The report records one isolated container result and zero remaining temporary container resources.
- **SC-005**: The report separates authenticated staging results from local results without exposing secret values.

## Assumptions

- The five inspected updates have no human ownership hold. A later hold stops publication.
- Local recovery references satisfy preservation during local work. Remote recovery publication requires the coordinator's publication slot.
- Gunicorn's stricter request parsing requires application compatibility checks before the major-version update can proceed.
- No authorized staging credential or verified organization is available in this worktree.
- Existing dependency guards already exercise absent, stale, and invalid inputs. This change reuses those tests.
