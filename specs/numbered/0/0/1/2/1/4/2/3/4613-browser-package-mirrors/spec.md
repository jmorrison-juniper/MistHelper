# Feature Specification: Browser package mirrors

**Feature Branch**: `jmorrison-juniper-browser-dependency-transfer-delays-ci`

**Created**: 2026-11-06

**Status**: Implemented. Evidence reviewed. Merge not authorized.

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
4. **Given** successful hosted evidence, **When** a maintainer considers a manual merge, **Then** current-base checks and separate user authorization remain required.

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
- **FR-007**: Do not retry CI or enable auto-merge. Consider a manual merge only after evidence review and this authorized specification revision.
  Require a current branch, successful required checks and CodeQL on the exact candidate, and the repository's serial validation slot.
  Require separate explicit user authorization before executing a merge. This revision does not grant that authorization or change CI policy.

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

The user selected: "Review the evidence and revise the specification before considering a merge".
This authorizes this revision, not a merge, an automatic merge, a CI retry, or a check bypass.
The branch remains owned by this session. PR #4208's workflow handover and upload-preservation requirement remain unchanged.

[The hosted evidence](design/research.md#hosted-validation-and-revision-review) supports SC-004 for two evaluated heads.
One successful run on each head does not guarantee future transfer speed.
The earlier absolute merge prohibition remains the historical instruction. Revised FR-007 permits consideration only under its stated conditions.
If main advances or this revision changes the candidate, earlier successful checks do not establish readiness for that new candidate.
