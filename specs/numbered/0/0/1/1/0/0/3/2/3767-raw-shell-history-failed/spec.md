# Feature Specification: Raw shell history test failure (issue 3767)

**Feature Branch**: `docs/3767-raw-shell-history-failed`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 3767, "Test failure: raw shell history reaches FAILED during native qualification". Labels: `bug`, `needs-investigation`, `tests`, `runtime`.

**Record route**: `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm the failure evidence (Priority: P1)

A maintainer confirms the failing test, the failing assertion, and the CI scan result. The maintainer runs only GET requests against GitHub.

**Why this priority**: A fix for the wrong test or the wrong commit hides the real defect.

**Independent Test**: Read `design/research.md`. Run the GET commands in `design/quickstart.md`. Each count and line number matches the record.

**Acceptance Scenarios**:

1. **Given** the record, **When** a maintainer reads the failure rows, **Then** the record names the test, the assertion, and the accepted-main line numbers.
2. **Given** the CI scan table, **When** a maintainer repeats the scan, **Then** the same failing runs and the same log lines appear.

---

### User Story 2 - Identify the branch that sets FAILED (Priority: P1)

A maintainer runs one controlled reproduction. The repository does not change. The structured log shows which branch set the FAILED state.

**Why this priority**: The issue states that the cause is unknown. A fix made before the branch is known can cause a wrong change.

**Independent Test**: Run the controlled command in `design/quickstart.md` once. Compare the log with the signature table in `design/data-model.md`.

**Acceptance Scenarios**:

1. **Given** the run fails, **When** the log shows the dead-peer signature, **Then** the record marks hypothesis H1 as confirmed.
2. **Given** the run passes, **When** no failure occurs, **Then** the record marks the failure as not reproduced and keeps the issue open.

---

### User Story 3 - Apply an authorized fixture change (Priority: P2)

After the owner authorizes the change, a maintainer changes only the close timing of the raw-output test device. The assertions stay the same.

**Why this priority**: The fix must remove the timing race without weakening the test.

**Independent Test**: Run the test file in the pinned Python environment. Run the test quality gate. Both pass, and the assertion lines do not change.

**Acceptance Scenarios**:

1. **Given** the owner authorizes the change, **When** the close timing changes, **Then** the test still asserts the `FINISHED` state and the exact history bytes.
2. **Given** the change is in review, **When** a reviewer compares the diff, **Then** only the device close timing differs.

### Edge Cases

- If the CI logs for a run expire, the record counts that run as unreadable. The record never counts an unreadable run as passed.
- If the controlled run fails with another signature, the record stops. A new record starts for that branch.
- If the controlled run passes, the record keeps the issue open and claims no fix.
- If the owner does not authorize a fixture change, the follow-up stays blocked. This record remains the only change.
- If `recovery/3760-handoff-20261004` merges first, the #3760 fixture reservation changes. The orchestrator checks that branch before merge.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failing test, its file path, its assertion, and the accepted-main line numbers.
- **FR-002**: The record MUST report the CI scan counts. The record MUST NOT claim a CI FAILED result without a log line.
- **FR-003**: The record MUST name the code branch that sets FAILED, with accepted-main and current-main lines.
- **FR-004**: The record MUST define one controlled run that classifies the branch from log events and changes no repository file.
- **FR-005**: The record MUST state the environment confounders. These are the local Python 3.13 report and the untracked `coverage.ini` file.
- **FR-006**: The record MUST assess the candidate server change and the candidate test file. The record MUST NOT treat them as the cause without log evidence.
- **FR-007**: This record MUST NOT weaken a test, change a timeout, retry to green, override a fixture, bypass a source path, or change production behavior.
- **FR-008**: Any authorized fixture change MUST keep the `FINISHED` assertion and the exact history assertion.
- **FR-009**: The record MUST use the managed route, the five-children limit, and the writing rules of `AGENTS.md`.
- **FR-010**: The record MUST define the local gates, the pull request, the remote CI watch, and the merge gate. Each step has a verification command.

### Key Entities

- **Failing test**: One pytest function in `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. It expects the `FINISHED` state.
- **Raw-output device**: The test class `RawOutputDevice`. It sends output frames, then a close frame after 0.2 seconds.
- **Keepalive controller**: The reader component that sends pings and closes a silent peer.
- **Terminal outcome**: The mapping from one connection close to a session state and a plain reason.
- **CI scan**: The set of failing `ci.yml` runs created from 2026-10-03 to 2026-11-26.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each remote check row has a path, a ref, a blob SHA, a result, and a line. The STATUS count equals the research table count.
- **SC-002**: The controlled run produces a signature from the table in `design/data-model.md`. Otherwise, the record states that the failure does not reproduce.
- **SC-003**: After authorization, the changed test file passes once in the pinned environment. The assertion lines do not change.
- **SC-004**: Each Markdown file in the record scores 80 or above in the STE gate.
- **SC-005**: The record contains no placeholder marker, no semicolon, and no contraction.

## Out of Scope

- Changes to the production keepalive default in `src/websocket_streams/live/transport/endpoint.py`.
- Changes to the owned WebSocket transport, the SDK contract test, or the installed mistapi package.
- Changes to the candidate branch `recovery/3760-handoff-20261004`.
- Changes to the Python version pin or to the CI workflow.
- Changes to `ShellLogAssertions`, which the #3761 reservation covers (U-7).

## Assumptions

- Accepted main commit `d4d1110352eeab3d9f9d483242232c12f6de4d2d` is the baseline of the failing run.
- Candidate commit `12f10ece0901452bd71eb1baa563ee77de5687db` differs from accepted main by two test fixture paths only.
- The private execution log named in the issue is not in the repository. Its hashes are recorded, but its content is unavailable.
- The issue comments of 2026-10-03 and 2026-10-26 allow one bounded reproduction. The comments state no source change.

## Clarifications

### Session 2026-11-26

- Q: Which Python version applies to the controlled run? A: Python 3.15.2. `pyproject.toml` requires 3.15, and CI uses 3.15.
- Q: Is `coverage.ini` a tracked file? A: No. The file is absent on accepted main and on current main. The controlled run uses the tracked coverage settings in `pyproject.toml`.
- Q: Does the CI scan reproduce the failure? A: No. No scanned failing run shows the test as FAILED.
- Q: Does this record authorize a fixture change? A: No. The issue limits scope to a read-only diagnosis.
