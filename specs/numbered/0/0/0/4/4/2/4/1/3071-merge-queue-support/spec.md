# Feature Specification: Protected merge queue validation

**Feature Branch**: `jmorrison-juniper-merge-queue-support`

**Created**: 2026-10-20

**Status**: Specified

**Input**: Prepare merge queue validation for #3071 without changing protection or enabling the queue.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate the merge candidate (Priority: P1)

A maintainer needs every required check to measure the queued merge candidate.
The checks must retain their current names.

**Why this priority**: Missing checks prevent queue operation. Checks against an older base do not protect the merge result.

**Independent Test**: Inspect both required-check workflows and reject a missing queue event or a changed required name.

**Acceptance Scenarios**:

1. **Given** a queue candidate, **When** GitHub requests checks, **Then** both required-check workflows measure that candidate.
2. **Given** the current required contexts, **When** queue checks report, **Then** all 15 context names remain unchanged.
3. **Given** two candidates, **When** the second starts, **Then** it cannot cancel validation of the first candidate.

### User Story 2 - Preserve existing checks (Priority: P1)

A contributor needs pull request checks and merged-tree checks to retain their existing behavior.

**Why this priority**: Queue preparation must not weaken existing protection.

**Independent Test**: Check pull request events, main events, concurrency, checkout references, and aggregate check names.

**Acceptance Scenarios**:

1. **Given** a pull request against any base, **When** its head changes, **Then** existing checks still start.
2. **Given** a merged tree, **When** main validation starts, **Then** a later run does not cancel that validation.
3. **Given** a failed required check, **When** another check completes, **Then** the failure remains a merge blocker.

### User Story 3 - Separate preparation from activation (Priority: P2)

The owner needs an explicit activation boundary and recorded acceptance evidence.

**Why this priority**: Enabling the queue before its checks exist can prevent every merge.

**Independent Test**: Review deployment instructions and confirm that the preparation change modifies no repository setting.

**Acceptance Scenarios**:

1. **Given** the preparation pull request, **When** it merges, **Then** #3071 remains open until operational acceptance succeeds.
2. **Given** separate owner approval, **When** the owner enables the queue, **Then** strict protection and required names remain unchanged.
3. **Given** two low-risk candidates, **When** queue validation and merges succeed, **Then** the owner records the evidence before replacing serialization.

### Edge Cases

- Missing or malformed workflow input must fail the contract check.
- A missing queue trigger or renamed required context must fail a direct mutation test.
- Cancelled, timed-out, stale, and skipped required results are unresolved, not successful.
- A queue run has no pull request head. It must measure its own candidate commit.
- The application-owned CodeQL context requires live evidence after activation.
- Another open pull request holds part of `ci.yml`. Only its released trigger section is available.
- The historical merge instruction path does not exist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both workflows that supply required checks MUST accept queue check requests.
- **FR-002**: The 15 required context names MUST remain unchanged.
- **FR-003**: Queue validation MUST measure the candidate commit.
- **FR-004**: Queue candidates MUST have separate concurrency groups and MUST NOT cancel another candidate.
- **FR-005**: Existing pull request, main, and post-merge validation MUST remain available.
- **FR-006**: Contract tests MUST report examined counts and reject trigger, name, checkout, and cancellation regressions.
- **FR-007**: This change MUST NOT modify repository settings, protection, required contexts, or queue configuration.
- **FR-008**: Documentation MUST separate preparation, owner activation, operational verification, and recovery.
- **FR-009**: The preparation pull request MUST NOT automatically close #3071.
- **FR-010**: Implementation MUST preserve reserved browser evidence and the historical coverage-fetch repair.

### Key Entities

- **Candidate**: The proposed merge result that must pass the required checks.
- **Required context**: A stable check name that branch protection requires before a merge.
- **Activation evidence**: Queue commit, check results, merge result, and unchanged protection recorded after owner activation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 15 existing required context names remain unchanged.
- **SC-002**: Both required-check workflows accept queue check requests.
- **SC-003**: Every tested trigger, name, checkout, or cancellation mutation fails the contract decision.
- **SC-004**: The preparation change modifies zero repository settings.
- **SC-005**: After owner activation, two candidates merge without a manual rebase loop and retain successful required checks.

## Assumptions

- Queue activation requires a separate owner decision and does not belong to this pull request.
- Strict protection stays enabled throughout the rollout.
- Existing queue references provide separate concurrency groups without another grouping mechanism.
- The user approved `documentation/quality-gates.md` instead of restoring the absent historical instruction path.
- That documentation substitution is an explicit exception to the issue's original fourth acceptance criterion.
- PR #4208 released only the `ci.yml` trigger section. Other held sections require another handover before editing.
- The current serialized merge process remains until operational acceptance succeeds.
