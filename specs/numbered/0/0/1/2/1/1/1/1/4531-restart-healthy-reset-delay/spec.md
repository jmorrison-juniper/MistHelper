# Feature Specification: Restart healthy reset test repair

**Feature Branch**: `fix/4531-restart-healthy-reset-delay`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4531, "Test failure: restart healthy reset reports an unexpected delay"

**Input**: Issue 4531, merged pull request 4555, and the CI evidence in `design/research.md`.

## Terms

Each term has one meaning in this record.

- **Session script**: `container/scripts/misthelper-session.sh`. It starts the recorder again after each failed launch.
- **Shared helper**: `tests/unit/container/output_defaults/session.py`. It holds the recorder, the sandbox, and the process wrapper.
- **Recorder**: The synthetic `MistHelper.py` that the tests start. It sleeps the planned duration and exits with the planned code.
- **Launch**: One start of the recorder by the session script.
- **Planned duration**: One pair of exit code and seconds in a test plan.
- **Measured duration**: The value of `RUN_SECONDS` for one launch.
- **Healthy threshold**: The value of `MIN_HEALTHY_SECONDS`. The default is 30 seconds.
- **Healthy run**: A launch whose measured duration is at least the healthy threshold.
- **Healthy reset**: The effect of a healthy run. The failed-start count and the restart delay return to their first values.
- **Attempt limit**: The value of `MAX_START_ATTEMPTS`.
- **Restart delay**: The wait before the next launch. It doubles after each failed launch, up to a cap.
- **Controlled clock**: The `CLOCK_SOURCE` fixture. It sets each measured duration from the test plan.
- **Restart class**: The class `TestSessionRestarts`.
- **Restart case**: One of the eight test cases in the restart class.

## User Scenarios and Testing

### User Story 1 - Stable restart results on a loaded machine (Priority: P1)

A maintainer runs the unit suite on a busy machine. The restart class must return the same delays on every run. The result must not depend on real launch time.

**Why this priority**: The unexpected delay stopped a complete unit run during the audit for issue 1794. An unstable result hides real defects.

**Independent Test**: Run the restart class ten times in a row. All eight restart cases pass in each run.

**Acceptance Scenarios**:

1. **Given** a 2-second stall on the fourth launch, **When** the restart case runs, **Then** the delays are `[1, 2, 1, 2]`.
2. **Given** a 1-second plan and a 2-second threshold, **When** the plan runs, **Then** the attempt limit ends the session after delays `[1, 2]`.
3. **Given** a clock plan that lacks a duration for the second launch, **When** the second launch starts, **Then** the session exits with code 97 after two launch entries.

### User Story 2 - Compliant test changes (Priority: P1)

A reviewer checks the test change against constitution Principles VI and VII. Each changed or added test function logs each action before and after it. Each bash line in the controlled clock carries a comment.

**Why this priority**: The constitution states that code without either principle cannot pass review.

**Independent Test**: Read the two functions named in FR-005 and the `CLOCK_SOURCE` fixture. Then run the restart class. All eight restart cases pass.

**Acceptance Scenarios**:

1. **Given** the stall regression function, **When** a reviewer reads it, **Then** an info line precedes the source injection and a debug line follows it.
2. **Given** the clock exhaustion function, **When** a reviewer reads it, **Then** an info line precedes the session run and a debug line follows it.
3. **Given** the `CLOCK_SOURCE` fixture, **When** a reviewer reads it, **Then** each bash line carries a comment that states its purpose.

### User Story 3 - Traceable cause of the original failure (Priority: P2)

A reviewer finds the failing test, the failing assertion, the environment, and the cause status in one record.

**Why this priority**: The issue stays open for review until the cause status is clear.

**Independent Test**: Open `design/research.md`. The failing test ID, line 283, the assertion, the observed tuple, and the Unverified list are present.

**Acceptance Scenarios**:

1. **Given** the issue log, **When** a reviewer reads the record, **Then** the record names the test ID, the assertion, and both tuples.
2. **Given** the cause status, **When** a reviewer reads the record, **Then** the record marks the mechanism as probable and lists each unverified part.

### User Story 4 - Verified merge on the exact head (Priority: P2)

The pull request head passes CI with the restart cases reported as passed. A human reviewer approves the merge because the issue has the `needs-human-review` label.

**Why this priority**: The label requires a human review before merge.

**Independent Test**: Watch the checks on the pull request head. Confirm eight passed restart cases in the root-units shard log. Confirm that auto-merge waits for approval.

**Acceptance Scenarios**:

1. **Given** the pull request head, **When** CI finishes, **Then** the root-units shard reports the restart cases as passed and no required check fails.
2. **Given** a passing head, **When** the orchestrator authorizes the merge, **Then** the merge still waits for the human approval recorded on the pull request.

### Edge Cases

- A planned duration equals the healthy threshold (plan3, 2 seconds). The healthy reset must occur.
- A planned duration is one second below the healthy threshold (plan4, 1 second). The healthy reset must not occur.
- The fourth launch takes two extra real seconds (stall regression). The planned classification must stay the same.
- The clock plan lacks a duration for a later launch. The session must exit with code 97.
- An edit to the session script changes the text of a DEBUG trap command. The controlled clock can stop working. The result and launch-count assertions must fail.
- The issue environment (Python 3.13.13, pytest 9.1.1) differs from the pinned environment. That environment is out of scope.
- Another test in the same folder fails in one CI run. That failure is out of scope for this issue.

## Requirements

### Functional Requirements

- **FR-001**: The restart class MUST classify each launch from its planned duration, not real elapsed time.
- **FR-002**: A mismatch MUST fail with the return code, launch count, restart delays, and session output.
- **FR-003**: The restart class MUST cover the healthy threshold, its boundary, a delayed fourth launch, and clock exhaustion.
- **FR-004**: The restart defaults MUST stay 5 attempts, 30 healthy seconds, 2 initial seconds, and a 60-second cap.
- **FR-005**: Each changed or added test function MUST log before and after each action, in ASCII text.
- **FR-006**: Each bash line in `CLOCK_SOURCE` MUST carry an inline comment that states its purpose.
- **FR-007**: The session script and the shared helper MUST keep their behavior, and this issue MUST NOT edit them.
- **FR-008**: The restart class MUST pass on the pull request head in the root-units shard before the merge.

### Key Entities

- **Launch**: One start of the recorder. Its natural key is the session identifier and the launch number.
- **Planned duration**: One pair of exit code and seconds in a test plan. It sets the measured duration of one launch.
- **Restart controls**: The environment values for the attempt limit, the healthy threshold, the restart delay, and the delay cap.
- **Observation**: The return code, the launch entries, the restart delays, and the output of one session run.

Mist Cloud transport requirements do not apply. This issue calls no Mist Cloud API.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All tests in `tests/unit/container/output_defaults/test_session.py` pass on Python 3.15.2 with pytest 9.2.0.
- **SC-002**: The restart class passes ten consecutive local runs with no failure.
- **SC-003**: The pull request head reports no failed check and no failed restart case.
- **SC-004**: Each applicable local gate reports its expected result. Each other gate has a recorded reason.

## Clarifications

### Session 2026-11-26

- **Q**: Does this issue need a production change? **A**: No. The session script and the shared helper keep their behavior. The controlled clock removes the timing dependency from the test.
- **Q**: Does CI show the failure? **A**: No. None of the 16 CI runs that contain the restart class shows a failed restart case. The issue log is the only record of the failure.
- **Q**: Is the cause verified? **A**: No. The mechanism is probable. The original run did not record launch timing.
- **Q**: Does the merged fix need another test? **A**: No. The eight restart cases cover each boundary, the stall, and the clock exhaustion.
- **Q**: Who approves the merge? **A**: A human reviewer approves. The issue has the `needs-human-review` label.

## Assumptions

- The issue log came from the baseline test file at commit `d30ef1690e9c00698e0e462f54de793c7a2093b9`. Line 283 of that file matches the reported assertion.
- Local verification uses Python 3.15.2 and pytest 9.2.0, as the repository pins them.
- The tests use the Bash capability that `tests/unit/prod_readiness/operations/exporting/container/build_support/bash_support.py` reports.
- Pull request 4555 is the accepted test repair. This record completes the issue.

## Out of Scope

- Any change to `container/scripts/misthelper-session.sh`.
- Any change to the behavior of `tests/unit/container/output_defaults/session.py`.
- The cache slice of issue 1794, including commits `4202f0265fc4eaf3b0697a3ef620c912f06f75fa` and `b068614e4ca0d6828d711bdc876b1092de87bef7`.
- The `test_contract.py` failure that CI run 45459366990 shows.
- Any change to the default restart controls.
- A container build or a deployment.
