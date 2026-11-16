# Feature Specification: Main workflow recovery

**Feature Branch**: `jmorrison-juniper-post-merge-consumer-integration`

**Created**: 2026-11-16

**Status**: Local implementation

**Input**: Issue #4763 and the coordinator's consumer scope.

## User Scenarios & Testing

### User Story 1 - Recover main checks (Priority: P1)

A maintainer needs the main checks to run after an automatic merge.
The maintainer can then examine the merged revision.

**Why this priority**: A merge can otherwise leave the main checks stale.

**Independent Test**: Check the consumer configuration and observe an approved ordinary merge.

**Acceptance Scenarios**:

1. **Given** a confirmed immediate merge, **When** recovery runs, **Then** the main checks are eligible to start.
2. **Given** a pending merge request, **When** no merge is confirmed, **Then** the request alone does not establish a merge.
3. **Given** a missed merge event, **When** a scheduled or manual recovery runs, **Then** recovery remains available.

### Edge Cases

- A canceled run must not continue recovery.
- A closed pull request that did not merge must not start merge recovery.
- Main can advance before a backstop runs, so a later run does not prove coverage of an earlier revision.

## Requirements

### Functional Requirements

- **FR-001**: Use the reviewed shared recovery revision.
- **FR-002**: Include the quality, code scanning, container, and STE workflows in recovery.
- **FR-003**: Preserve the existing permissions, triggers, default-branch guard, and issue-close behavior.
- **FR-004**: Do not treat an enabled pending request as a confirmed merge.
- **FR-005**: Preserve manual, scheduled, and merged-close recovery.
- **FR-006**: Do not create a test merge or start a live workflow for this change.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four named main workflows accept manual recovery and a main push.
- **SC-002**: The consumer guard rejects the old revision and a missing workflow.
- **SC-003**: Hosted acceptance remains open until an approved ordinary merge supplies evidence.

## Assumptions

- The reviewed shared revision owns the merge and recovery behavior.
- A local configuration test cannot establish hosted dispatch timing.
