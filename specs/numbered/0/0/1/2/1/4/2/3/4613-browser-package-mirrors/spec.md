# Feature Specification: Browser package mirrors

**Feature Branch**: `jmorrison-juniper-browser-dependency-transfer-delays-ci`

**Created**: 2026-11-06

**Status**: Implemented. Evidence reviewed. One manual squash merge is authorized under FR-007.

**Input**: Investigate and address #4613 without changing the browser job budget, test selection, assertions, required statuses, or CI policy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve the browser test budget (Priority: P1)

A contributor needs browser setup to avoid the package endpoint that repeatedly consumed more than nine minutes.

**Why this priority**: Incomplete browser results block delivery, even when every completed case passes.

**Independent Test**: Execute the setup configuration against a local runner fixture without a network or administrator access.

**Acceptance Scenarios**:

1. **Given** the current runner configuration, **When** setup runs, **Then** package requests use its existing official HTTPS alternatives.
2. **Given** an unfamiliar configuration, **When** setup runs, **Then** setup fails before changing that configuration.
3. **Given** an installation error, **When** setup fails, **Then** the browser gate cannot report success.

### User Story 2 - Preserve validation strength (Priority: P1)

A maintainer needs the complete browser suite and its existing failure rules after the setup repair.

**Independent Test**: Compare the workflow contracts with the unchanged baseline and exercise rejected mutations.

**Acceptance Scenarios**:

1. **Given** the repair, **When** the workflow runs, **Then** the same browser installer, package sources, test directories, and assertions remain.
2. **Given** a failed or incomplete shard, **When** the aggregator runs, **Then** the required result remains failed.
3. **Given** PR #4208, **When** its owner reconciles the workflow, **Then** its WAN evidence upload remains unchanged.
4. **Given** the exact published candidate passes all required checks and CodeQL, the branch is current with main, and the serial slot is available, **When** the user considers a merge, **Then** one manual squash merge is authorized.

### Edge Cases

- An absent mirror file or official alternative must stop setup.
- A repeated setup must not erase the original backup.
- A backup failure must prevent the configuration change.
- A slow alternative remains a possible external failure, not permission to increase the budget.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Remove only the measured slow endpoint from the runner mirror list.
- **FR-002**: Preserve all other mirror entries, package sources, suites, components, signature checks, and package installation commands.
- **FR-003**: Validate the known configuration before writing it and preserve its original content in a backup.
- **FR-004**: Preserve the 20-minute job limit, full shard selection, assertions, required names, services, and failure handling.
- **FR-005**: Prove successful setup, repeat behavior, invalid inputs, backup failure, and rejected workflow mutations without external requests.
- **FR-006**: Preserve PR #4208's separate WAN upload change without importing its product changes into this branch.
- **FR-007**: Do not retry CI, enable auto-merge, or bypass a check. The user authorizes one manual squash merge of the first published head containing this revision, only after all required checks and CodeQL pass on that exact head, the branch is current with main, and the repository's serial validation slot is available.
  Do not merge if any condition is false. This authorization does not apply to a changed head or change CI policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The configured package routes contain zero entries for the measured slow endpoint after setup.
- **SC-002**: Every other configuration entry and every browser validation requirement remains unchanged.
- **SC-003**: Every focused offline contract completes, including cases that must reject invalid setup.
- **SC-004**: A later normal CI run must complete every selected case within the existing budget before anyone claims measured runtime success.

## Assumptions

- The hosted runner retains its documented mirror-list format and official HTTPS alternatives.
- Removing the slow route preserves signed package identity because the alternatives serve the same Ubuntu archive.
- Offline equivalence does not measure hosted-runner transfer speed.
- Earlier silent test stalls in #3736 have no proved connection to these downloads.

## Evidence review and authorization

The user authorizes one manual squash merge of this PR after the required checks pass on the exact published head that contains this revision.
The branch must be current with main, and the repository's serial validation slot must be available.
Do not retry CI, enable auto-merge, bypass a check, or merge a changed head.
No merge occurs in this revision.
The branch remains owned by this session. PR #4208's workflow handover and upload-preservation requirement remain unchanged.

[The hosted evidence](design/research.md#hosted-validation-and-revision-review) supports SC-004 for two evaluated heads.
One successful run on each head does not guarantee future transfer speed.
The earlier merge prohibition is narrowed only by the limited authorization in revised FR-007.
If main advances or the branch changes, earlier checks do not establish readiness for the new candidate, and this authorization does not apply.
