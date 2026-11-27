# Feature Specification: Pylint gate failure from the mando 0.8.2 pin

**Feature Branch**: `fix/4897-pylint-mando-pin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4897, "CI: quality-gate `pylint` failed (PR #4888)". Pull request #4888 raises `mando` from 0.7.1 to 0.8.2 in `requirements-dev.txt`.

## Clarifications

### Session 2026-11-26

- Q: Which check failed? A: The check `Pylint (score gate)`, job 137338442217, in run 45064243269. Its step `Install dependencies` failed. Its step `Run Pylint` did not run.
- Q: Which rule failed? A: The pip dependency resolver. radon 6.0.1 requires `mando (<0.8,>=0.6)`. Pull request #4888 pins `mando==0.8.2` at `requirements-dev.txt` line 179.
- Q: Does main fail? A: No. Run 45774119357 on commit f03c6c9 passed. Its Pylint job and its Dependency lock and exports job passed.
- Q: Does a newer radon accept mando 0.8? A: No. PyPI reports radon 6.0.1 as the current release. It requires mando below 0.8.
- Q: Does a legacy record exist? A: No. No folder under `specs\` starts with `4897-`. No path on main contains `4897`.
- Q: Does the failure involve Mist API or mistapi behavior? A: No. The failure is a Python dependency conflict in the CI workflow.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the root cause of the failed check (Priority: P1)

A maintainer reads this record. The maintainer learns the failed check, the failed step, the failed rule, and the log lines. The maintainer does not search the raw log.

**Why this priority**: The issue title names `pylint`. The pylint score never ran, so the title points to the wrong cause.

**Independent Test**: Run the reproduction commands in `design\quickstart.md`. Each command returns the check name and the log lines that this record cites.

**Acceptance Scenarios**:

1. **Given** run 45064243269, **When** the maintainer reads the failed log of job 137338442217, **Then** the log shows the resolution error at lines 932 to 946.
2. **Given** that log, **When** the maintainer reads line 936, **Then** the line states that radon 6.0.1 depends on mando below 0.8.

### User Story 2 - Restore a passing Pylint check (Priority: P1)

An implementer delivers one pull request. The pull request holds `mando` at 0.7.1, adds a Dependabot ignore entry for `mando` 0.8 and later, and adds a guard test. The check `Pylint (score gate)` reaches `Run Pylint` and passes.

**Why this priority**: Each Quality Gates job that installs `requirements-dev.txt` fails until pip resolves the file.

**Independent Test**: Read the checks of the fix pull request. Job `Pylint (score gate)` shows `Install dependencies` and `Run Pylint` as successful.

**Acceptance Scenarios**:

1. **Given** the fix pull request, **When** its Quality Gates run finishes, **Then** job `Pylint (score gate)` reports success.
2. **Given** the requirements file of pull request #4888, **When** the new guard test runs, **Then** the test fails and names radon as the conflicting package.

### User Story 3 - Stop the repeated Dependabot pull request (Priority: P2)

The weekly pip update stream does not raise a `mando` version that radon 6.0.1 rejects.

**Why this priority**: While radon 6.0.1 stays pinned, each new bump produces another red check.

**Independent Test**: After the fix merges, observe the next scheduled Dependabot run. The run raises no `mando` pull request for version 0.8 or later.

**Acceptance Scenarios**:

1. **Given** the ignore entry on main, **When** Dependabot checks the pip stream, **Then** it does not raise a `mando` version of 0.8 or later.

### Edge Cases

- What happens when radon releases a version that accepts mando 0.8? Remove the ignore entry. Raise radon and mando in one pull request.
- What happens when Dependabot does not honor the `versions` key? The next scheduled run raises the same bump. The implementer records the result in the pull request body.
- What happens when main moves before the fix merges? Update the branch from main. Then rerun every required check.
- What happens when the test environment lacks radon? The new test fails with the metadata error. The test does not skip.
- What happens when a second mando pin appears? The new test fails, because it expects exactly one mando pin.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failed check, the failed step, the failed rule, and the log lines that prove each one.
- **FR-002**: The fix pull request MUST let the check `Pylint (score gate)` reach its step `Run Pylint`.
- **FR-003**: `requirements-dev.txt` MUST keep `mando` at a version that radon 6.0.1 accepts.
- **FR-004**: `requirements-dev.txt` and `uv.lock` MUST agree, so `uv lock --check` and the export guard pass.
- **FR-005**: The pip stream of `.github/dependabot.yml` MUST NOT raise a `mando` version that the radon requirement rejects.
- **FR-006**: The Dependabot policy snapshot in `tests/guardrails/test_pr_title_workflow.py` MUST equal the Dependabot file after the change.
- **FR-007**: A unit test MUST fail when a pinned `mando` version breaks the installed radon requirement.
- **FR-008**: Pull request #4888 MUST NOT merge. The implementer MUST close it after the fix merges.
- **FR-009**: The change MUST keep the pylint threshold at 9.5 and the Pylint job scope at `src/`.
- **FR-010**: The fix pull request MUST use a Conventional Commit title. Its body MUST contain `Closes #4897`.
- **FR-011**: `.github/copilot-instructions.md` MUST hold one entry for issue #4897 under Known pitfalls.
- **FR-012**: The change MUST add one release-note fragment under `changelog.d/`, as the constitution requires.
- **FR-013**: The change MUST NOT alter product code under `src/` or `MistHelper.py`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable: this change calls no Mist REST endpoint and owns no WebSocket transport.

### Key Entities *(include if feature involves data)*

Not applicable: this change adds no data entity. See `design\data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fix pull request, job `Pylint (score gate)` reports step `Run Pylint` as successful.
- **SC-002**: On the fix pull request, no failed job logs `ResolutionImpossible` in an install step.
- **SC-003**: The new guard test fails on the requirements file of pull request #4888, and it passes on the fix branch.
- **SC-004**: The Dependabot policy guard, the export guard, and the lock guard pass in CI.
- **SC-005**: The remote check count in `4897-STATUS.json` equals the row count of the remote table in `design\research.md`. The summary repeats the same count.

## Assumptions

- PyPI reports the current radon release. The check ran on 2026-11-26.
- The pip message in run 45064243269 names the real conflict. Its line 936 names radon 6.0.1.
- Dependabot accepts the `versions` key in an ignore entry. No source verifies this assumption yet. See `design\research.md`.
- Runtime requirements do not pin mando or radon. Development tools pull mando through radon.

## Out of Scope

- Changing the pylint threshold, the pylint scope, or the Pylint job.
- Replacing radon or the complexity gate.
- Changing the aggregate jobs or the quality-gate issue sync job.
- Changing the Windows workflows beyond the shared install fix.
- Changing Mist API calls, the mistapi pin, or product code.
