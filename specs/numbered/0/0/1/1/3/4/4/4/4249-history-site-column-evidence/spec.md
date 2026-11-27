# Feature Specification: History Site Column Failure Evidence

**Feature Branch**: `fix/4249-history-site-column-evidence`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4249, "Test failure: test_the_history_of_one_site_shows_no_site_column"

**Input**: Issue #4249 and its comments, CI run 38860502112, and the state of `main` on 2026-11-26.

## Clarifications

### Session 2026-11-26

- Q: Which assertion failed in run 38860502112? A: The job log names no assertion. It holds no `AssertionError` and no traceback. Candidate statements are in `analysis.md`, finding A-05.
- Q: Does the issue stay open? A: The issue state is OPEN. The owner comment of 2026-10-25 says it remains open for a future failure with a traceback or retained evidence. A follow-up issue keeps the root cause open (decision D-5).
- Q: Is the failing commit on `main`? A: Yes. Commit `351871c4345405cdd035b043b046f046f192ddc1` is an ancestor of `main`.
- Q: Does a product change fix the failure? A: No. No root cause is verified. The feature changes no product code and no test logic (decision D-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the diagnostics of a failed or canceled E2E shard (Priority: P1)

A maintainer opens a failed or canceled E2E shard. The diagnostics artifact keeps the shard log, the phase trail, and the browser output folder. The guard fails when the workflow stops keeping them.

**Why this priority**: The root cause cannot be found without evidence. The job log of the failed run holds no traceback.

**Independent Test**: Run `python -m pytest tests/guardrails/test_e2e_shard_partition.py`. The guard passes on the current workflow and fails for each removed rule.

**Acceptance Scenarios**:

1. **Given** the shard workflow on `main`, **When** the guard reads the diagnostics step, **Then** the guard passes and reports five checked rules.
2. **Given** a workflow whose diagnostics step runs only after a failure, **When** the guard reads it, **Then** the guard fails with the condition message.
3. **Given** a workflow whose diagnostics step drops the browser output folder, **When** the guard reads it, **Then** the guard fails with the trace message.

---

### User Story 2 - Read the documented procedure for a failed shard (Priority: P2)

A maintainer reads the browser gate in the quality gates page. The page names the diagnostics artifact and its files. The page states that a canceled shard log can lack the traceback.

**Why this priority**: The gate page is the first page that an operator reads. A clear procedure shortens the next diagnosis.

**Independent Test**: Read the browser gate paragraph in `documentation/quality-gates.md`. Check that it names the artifact, the failure screenshot, and the trace.

**Acceptance Scenarios**:

1. **Given** a failed E2E shard, **When** the maintainer reads the gate page, **Then** the page names the artifact that starts with `e2e-diagnostics`.
2. **Given** a canceled E2E shard, **When** the maintainer reads the gate page, **Then** the page warns that the shard log can lack the traceback.

---

### User Story 3 - Name the failing statement from a retained failure (Priority: P2)

A maintainer receives a future failed run of the history test. The run keeps the failure screenshot and the trace. The maintainer names the failing statement in the issue.

**Why this priority**: The owner asked for this data in the issue. This feature provides the path to collect it.

**Independent Test**: Open the diagnostics artifact of a failed run. The failure screenshot shows the page, and the trace shows the failing action.

**Acceptance Scenarios**:

1. **Given** a failed run with a completed job, **When** the maintainer reads the shard log, **Then** the log names the failed test and its traceback.
2. **Given** a canceled run, **When** the maintainer opens the diagnostics artifact, **Then** the maintainer finds the failure screenshot and the trace of the failed test.

---

### Edge Cases

- A shard is canceled before the history test runs. The artifact then holds no evidence for that test.
- The screenshot retry fails a second time. The failure screenshot is missing, but the trace remains.
- The shard log lacks the traceback. Pytest prints failure details only in its terminal summary.
- The history test passes in a later run. The fault stays intermittent, and no retry hides it.
- Two shards fail in one run. Each shard uploads its own diagnostics artifact.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The shard workflow MUST upload the diagnostics artifact after a failed or canceled shard.
- **FR-002**: The diagnostics artifact MUST keep the shard log, the phase trail, and the browser output folder.
- **FR-003**: Each shard pytest command MUST keep its timeout, screenshot, trace, and output options.
- **FR-004**: The guard tests MUST fail when FR-001 or FR-002 no longer holds.
- **FR-005**: The change MUST NOT change the test assertions, the timeouts, the retries, or the history page code.
- **FR-006**: The gate page MUST describe the diagnostics artifact and how to read it.
- **FR-007**: The gate page MUST state that a canceled shard log can lack the traceback.
- **FR-008**: The change MUST add one changelog fragment.
- **FR-009**: The change MUST NOT add a direct child to `tests/guardrails` or to `tests/e2e/upgrade_portal`.
- **FR-010**: The pull request MUST name a follow-up issue for the unverified root cause before the merge.
- **FR-011**: The record MUST list each candidate cause as unverified and name the check that decides it.

### Key Entities

- **Diagnostics artifact**: An upload whose name starts with `e2e-diagnostics`, followed by the shard name. It keeps the three paths below.
- **Shard log**: The file that holds the pytest output of one shard. The `tee` command in the pytest step writes it.
- **Phase trail**: The file `test-artifacts/e2e-phase-trail.jsonl`. The diagnostics upload keeps it when it exists.
- **Browser output folder**: The folder `test-artifacts/issue-4229-browser`. Pytest-playwright writes the failure screenshot and the trace of each failed test here.
- **Failure screenshot**: The file `test-failed-1.png` in the folder of a failed test.
- **Trace**: The file `trace.zip` in the folder of a failed test.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The main guard test case and the five mutation cases pass on the current workflow. Each mutation case proves that the audit raises an assertion.
- **SC-002**: Each applicable local gate in `tasks.md` exits with its expected result for each changed file.
- **SC-003**: The required check `E2E smoke tests` passes on the pull request, and the checks on `main` pass after the merge.
- **SC-004**: The next failed run of the history test keeps a failure screenshot and a trace in its diagnostics artifact. This criterion depends on a future run.
- **SC-005**: The record names the failing statement when a retained failure exists. This criterion depends on a future run.

## Assumptions

- The shard workflow on `main` keeps the blob that the remote check confirmed on 2026-11-26.
- The pinned packages `pytest-playwright==0.10.0` and `pytest-timeout==2.4.0` keep the option names that the local package shows.
- The owner accepts a wait for the next failed run before any product change.
- The history page code stays unchanged during this feature.

## Out of Scope

- Finding and fixing the root cause of the failure.
- Changing the test assertions, the test timeouts, or the screenshot retry.
- Adding a pytest hook that prints each traceback at failure time.
- Changing the shard layout, the matrix rows, or the required check name.
- Changing the history page, its route, or its template.
