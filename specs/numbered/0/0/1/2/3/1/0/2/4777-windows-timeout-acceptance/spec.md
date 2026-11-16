# Feature Specification: Native Windows Timeout Acceptance

**Feature Branch**: `[4777-windows-timeout-acceptance]`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Add optional native Windows acceptance for the timeout budget guard without changing the existing test or its limits."

## User Scenarios & Testing

### User Story 1 - Verify the Timeout Guard on Windows (Priority: P1)

A maintainer needs evidence that the existing timeout-budget guard passes on native Windows after its timing repair.

**Why this priority**: The prior failure occurred only on Windows, so a non-Windows run cannot confirm the repair.

**Independent Test**: Push a change to a non-main branch that touches a relevant file and confirm the complete guard module reports the expected result.

**Acceptance Scenarios**:

1. **Given** a non-main push changes a relevant file, **When** the acceptance run finishes, **Then** it reports seven tests with no skips, errors, or failures.
2. **Given** the guard collects no tests or collects an unexpected number, **When** the acceptance run checks the result, **Then** it fails.
3. **Given** the run executes outside native Windows, **When** it checks the platform, **Then** it fails before claiming acceptance.

### Edge Cases

- A skipped, failed, or errored test must fail the acceptance run.
- A push to `main` or a change outside the relevant paths must not start this optional run.
- A canceled or timed-out run does not count as acceptance evidence.
- The run must not access Mist credentials, production data, live operations, or a browser.

## Requirements

### Functional Requirements

- **FR-001**: The project MUST provide an optional acceptance run for the existing timeout-budget guard.
- **FR-002**: The acceptance run MUST execute the full existing guard module on native Windows.
- **FR-003**: The acceptance run MUST confirm the native operating system and a supported Python version.
- **FR-004**: The acceptance run MUST require recorded test, skip, error, and failure counts, exactly seven tests, and zero skips, errors, and failures.
- **FR-005**: The acceptance run MUST fail when a count is absent, no tests run, the count differs, or any test skips, errors, or fails.
- **FR-006**: The acceptance run MUST start only for a non-main push that changes a relevant path.
- **FR-007**: The acceptance run MUST be bounded and safely cancel older runs for the same branch.
- **FR-008**: The acceptance run MUST use read-only repository access and MUST NOT persist checkout credentials.
- **FR-009**: The acceptance run MUST NOT require manual dispatch, services, Mist credentials, production data, live operations, or a browser.
- **FR-010**: The existing test module and its thresholds MUST remain unchanged.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A qualifying non-main push runs all seven tests in the existing guard module.
- **SC-002**: Acceptance succeeds only when all seven tests pass and zero tests skip or error.
- **SC-003**: The run ends or cancels within its configured time limit.
- **SC-004**: The existing guard module remains unchanged.

## Assumptions

- The current module collects seven tests, with no parametrized cases. The workflow contract will pin this measured count and fail if it changes.
- The native Windows run provides acceptance evidence only after a real push run succeeds. Local checks do not replace this evidence.
- The run remains optional and does not add a required status check.
