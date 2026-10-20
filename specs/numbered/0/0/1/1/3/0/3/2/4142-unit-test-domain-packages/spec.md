# Feature Specification: Unit Test Domain Packages

**Feature Branch**: `jmorrison-juniper-4142-test-package-deconfliction`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Split tests/unit/ into domain packages to resolve debt C-1 from issue #4142."

## User Scenarios & Testing

### User Story 1 - Find tests by domain (Priority: P1)

An engineer needs to find a unit test by the area that it checks. The test tree groups tests by domain and limits each new structural level to five children.

**Why this priority**: A predictable tree helps engineers find and maintain tests.

**Independent Test**: Inspect the final unit test tree and count the direct children at each new level.

**Acceptance Scenarios**:

1. **Given** the final unit test tree, **When** an engineer inspects `tests/unit/`, **Then** the directory contains no more than five direct children.
2. **Given** a new grouping directory, **When** an engineer counts its direct children, **Then** the count does not exceed five.

### User Story 2 - Run the existing unit tests (Priority: P1)

An engineer needs to run the same unit tests after the test files move.

**Why this priority**: A directory reorganization must not omit tests or change their results.

**Independent Test**: Collect the unit tests before and after the moves, then run the affected tests.

**Acceptance Scenarios**:

1. **Given** the test files in their new locations, **When** the repository test commands run, **Then** they collect every unit test that the previous tree collected.
2. **Given** a test or tool that refers to an old path, **When** the move completes, **Then** the reference uses the new path.

### User Story 3 - Avoid conflicts with active work (Priority: P1)

An engineer needs to keep active pull request and session-claimed files at their current paths until their owners release them.

**Why this priority**: Path moves must not conflict with work that is in review.

**Independent Test**: Compare each moved path with current open pull request file lists and active session claims.

**Acceptance Scenarios**:

1. **Given** an open pull request owns a test path, **When** another test package moves, **Then** the owned path remains unchanged.
2. **Given** the owning pull request has merged and its owner accepts the handoff, **When** the move resumes, **Then** the new path includes the merged changes.
3. **Given** an active session claims a test path, **When** another test package moves, **Then** the claimed path remains unchanged until its owner clears the claim.

## Edge Cases

- A test import, test selector, lint rule, or workflow may name a test path.
- A moved package may lack an `__init__.py` file or may expose helpers to another test tree.
- An open pull request may change its file list while the move plan is active.
- An active session may claim a path before its pull request opens.
- A test name may be duplicated in another domain package.

## Requirements

### Functional Requirements

- **FR-001**: The final `tests/unit/` directory MUST contain no more than five direct children.
- **FR-002**: Each new grouping directory MUST contain no more than five direct children.
- **FR-003**: The repository test commands MUST discover every unit test collected before the moves.
- **FR-004**: Each active import, selector, lint rule, workflow, and current document reference MUST use the new test path. Historical specifications, incident records, migration records, and handoff records MUST remain unchanged.
- **FR-005**: The change MUST preserve each test's existing behavior and package helper access.
- **FR-006**: The change MUST NOT move a pull request path before its owner accepts the post-merge handoff. The change MUST NOT move an actively claimed path before its owner clears the claim.
- **FR-007**: The change MUST NOT alter Mist API behavior or production runtime behavior.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `tests/unit/` has no more than five direct children after the final move.
- **SC-002**: Every new grouping directory has no more than five direct children.
- **SC-003**: The final pytest collection includes every test case collected before the moves.
- **SC-004**: All moved tests pass with the same results as before the move.
- **SC-005**: No open pull request or active session loses or conflicts with a test path that it owns.

## Assumptions

- Test discovery remains recursive under `tests/`, as configured in the repository.
- Engineers can use domain groups that follow the existing source package boundaries.
- The final domain groups will reuse existing directories under `tests/unit/`. The change will not add a direct child to that root.
- Move a package only after its ownership claims clear. Split its contents by test topic when a destination group would exceed five direct children, including package markers.
- Keep each actively claimed file at its current path until its owner releases the claim.
- The change moves only paths without an open pull request owner or active session claim.
- The initial grouping map is an implementation assumption and will be recorded in the plan.
