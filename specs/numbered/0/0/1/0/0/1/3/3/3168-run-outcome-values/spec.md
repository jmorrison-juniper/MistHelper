# Feature Specification: Explicit Portal Run Outcomes

**Feature Branch**: `3168-run-outcome-values`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: Issue #3168 asks the portal to read an explicit empty-result outcome from migrated handlers and retain a measurable log-marker fallback for other handlers.

## User Scenarios & Testing

### User Story 1 - Report empty results (Priority: P1)

An operator sees an honest completion message when a handler finds no records and writes no file.

**Why this priority**: An empty result must not appear as silent success or failure.

**Independent Test**: Run a migrated handler that returns an empty-result outcome without a matching log marker.

**Acceptance Scenarios**:

1. **Given** a handler returns an empty-result outcome, **When** the portal finishes the run, **Then** the portal marks it completed and shows the supplied reason.
2. **Given** a handler returns a failed or missing-input outcome, **When** the portal finishes the run, **Then** the portal marks it failed with the supplied reason.

### User Story 2 - Keep legacy handlers safe (Priority: P1)

An operator receives the current result when a handler has not returned an explicit outcome.

**Why this priority**: Unmigrated handlers must keep the current behavior during migration.

**Independent Test**: Run a handler without an outcome and verify the existing log-marker classification remains active.

**Acceptance Scenarios**:

1. **Given** an unmigrated handler logs a known empty-result marker, **When** the portal finishes the run, **Then** the portal completes the run with that log reason.
2. **Given** an unmigrated handler logs no recognized result marker and writes no file, **When** the portal finishes the run, **Then** the portal fails the run as it does today.
3. **Given** an unmigrated handler reaches the marker fallback, **When** the portal classifies the run, **Then** the portal logs a cumulative fallback count.
4. **Given** a known empty-result handler message matches a legacy marker, **When** the marker or handler wording changes, **Then** a contract test fails.

### User Story 3 - Ignore prose changes for migrated handlers (Priority: P2)

A handler can revise its log wording without changing the portal run state.

**Why this priority**: A prose edit must not restore the silent-completion defect.

**Independent Test**: Change a migrated handler's log wording and verify its returned outcome still controls run state.

**Acceptance Scenarios**:

1. **Given** a migrated handler returns an empty-result outcome and logs unrelated wording, **When** the portal finishes the run, **Then** the portal completes the run using the returned reason.

### Edge Cases

- A handler outcome has already passed its own validation before the portal reads it.
- A handler returns no outcome. The portal must use the existing marker fallback.
- A handler returns a failure or missing-input outcome. The portal must not mark it completed.
- A handler reports an empty result while output files exist. The explicit outcome controls the run message, while discovered files remain visible.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST use a handler's explicit empty-result outcome without requiring matching log text.
- **FR-002**: The portal MUST use explicit failure and missing-input outcomes to mark the run failed.
- **FR-003**: The portal MUST preserve marker-based classification for handlers that do not return an explicit outcome.
- **FR-004**: The portal MUST log a cumulative count each time it uses the legacy empty-result marker fallback.
- **FR-005**: A change to log wording MUST NOT change run state when a handler returns an explicit outcome.
- **FR-006**: A test MUST connect each legacy empty-result marker to current handler wording that it recognizes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A migrated empty-result handler completes with its supplied reason when its log text contains no recognized marker.
- **SC-002**: Every tested unmigrated handler keeps its current marker-based result.
- **SC-003**: Each legacy empty-result fallback log record includes the menu number and the cumulative fallback count.
- **SC-004**: A test changes the migrated handler's log wording and confirms the run state remains unchanged.
- **SC-005**: A wording change in a tracked legacy handler causes its marker contract test to fail.

## Assumptions

- A handler may provide a structured outcome value.
- A handler that provides no structured outcome remains on the legacy path.
