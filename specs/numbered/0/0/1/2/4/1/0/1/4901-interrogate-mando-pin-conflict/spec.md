# Feature Specification: Interrogate Gate Failure on PR #4888

**Feature Branch**: `fix/4901-interrogate-mando-pin-conflict`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4901, "CI: quality-gate `interrogate` failed (PR #4888)". The Quality Gates sync job opened this issue from run 45064243269 on 2026-11-22.

## Clarifications

### Session 2026-11-26

- Q: Which check failed, and at which step? → A: The check `Interrogate (docstring coverage)`, job `interrogate` in `.github/workflows/ci.yml`. Its step `Run pip install -r requirements-dev.txt` failed. The docstring command never ran.
- Q: Which rule failed? → A: The pip resolver rejected `mando==0.8.2` at `requirements-dev.txt` line 179. Radon 6.0.1 at line 365 requires `mando<0.8`. Research R1 holds the log lines.
- Q: Must `main` change its pin? → A: No. `main` already pins `mando==0.7.1` at line 179 and locks it in `uv.lock`. Only PR #4888 changes the pin.
- Q: Can the bump merge with a newer radon? → A: No. PyPI lists radon 6.0.1 as the latest release. Research R4 lists the alternatives.
- Q: Does a human decision apply? → A: No. The change involves no licensing, data destruction, credential policy, or product priority.
- Q: Where do the new tests go? → A: In class `TestDependabotPolicy` in `tests/guardrails/test_pr_title_workflow.py`. That class already reads `.github/dependabot.yml`.
- Q: What is the fragment name? → A: `issue-4901-interrogate-mando-pin-conflict.md`. The fragment rule uses this form when an issue exists and no pull request exists.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the rejected update from returning (Priority: P1)

The weekly Dependabot run must not propose a `mando` release that radon cannot accept. The pip update stream ignores `mando` releases from 0.8 onward. The `mando` pin stays in the 0.7 line.

**Why this priority**: The rejected update fails the Interrogate check on each new pull request until the rule exists.

**Independent Test**: Run the three new cases in `TestDependabotPolicy`. The cases pass only when the pip stream ignores 0.8.2 and 0.9.0 and allows 0.7.2.

**Acceptance Scenarios**:

1. **Given** the pip update stream in `.github/dependabot.yml`, **When** the policy test checks version 0.8.2, **Then** the stream ignores that version.
2. **Given** the same stream, **When** the policy test checks version 0.9.0, **Then** the stream ignores that version.
3. **Given** the same stream, **When** the policy test checks version 0.7.2, **Then** the stream does not ignore that version.

---

### User Story 2 - Restore a green Interrogate check on the fix pull request (Priority: P1)

The fix pull request installs `requirements-dev.txt` without a resolver error. The Interrogate job then runs the docstring command with a minimum of 90 percent.

**Why this priority**: Branch protection requires this check. No pull request can merge while it fails.

**Independent Test**: Read the CI run of the fix pull request. The Interrogate check and the 14 other required contexts report success.

**Acceptance Scenarios**:

1. **Given** the fix pull request head, **When** the Quality Gates run finishes, **Then** the job `interrogate` reports success.
2. **Given** the same run, **When** the job prints its result, **Then** the result line reads `RESULT: PASSED` with a minimum of 90.0 percent.

---

### User Story 3 - Close PR #4888 with proof that main keeps 0.7.1 (Priority: P2)

After the fix merges, PR #4888 closes without a merge. The closing comment names the merged fix and the head commit of PR #4888.

**Why this priority**: An open PR keeps a failing required check visible. The closing comment explains why the bump was rejected.

**Independent Test**: Read `requirements-dev.txt` on `main` after the merge. Line 179 reads `mando==0.7.1`, and PR #4888 reads `CLOSED`.

**Acceptance Scenarios**:

1. **Given** the merged fix, **When** a reader fetches `requirements-dev.txt` from `main`, **Then** line 179 reads `mando==0.7.1`.
2. **Given** PR #4888 is open, **When** the closing step finishes, **Then** PR #4888 reads `CLOSED` and its comment gives the proof.

### Edge Cases

- Caution: merging PR #4888 breaks the install step in every job that reads `requirements-dev.txt`. Reverting the merge restores the install.
- Caution: a hand edit of `requirements-dev.txt` breaks the export check. Do not edit that file by hand.
- A future radon release accepts mando 0.8. The same change must remove the ignore rule and update the pin.
- Caution: removing the ignore rule before that radon release reopens the conflict on the next weekly run.
- Dependabot rejects the rule syntax. The next weekly run logs an error. A new change then corrects the syntax.
- A later mando 0.7.x release appears. The ignore rule does not block it.
- Docstring coverage falls below 90 percent. The Interrogate job then fails for a new reason. The job log shows the measured value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `main` branch must keep `mando==0.7.1` in `requirements-dev.txt` and in `uv.lock`.
- **FR-002**: The pip update stream must ignore `mando` versions from 0.8 onward.
- **FR-003**: The pip update stream must not ignore `mando` patch releases in the 0.7 line.
- **FR-004**: The policy snapshot in the guard test must equal the complete `.github/dependabot.yml` after the change.
- **FR-005**: The Interrogate job must install `requirements-dev.txt` and run `interrogate` at 90 percent on the fix pull request.
- **FR-006**: The 15 required contexts must report success on the fix pull request head before the merge.
- **FR-007**: PR #4888 must close without a merge after the fix merges. The closing comment must carry a preservation proof.
- **FR-008**: The fix must add `changelog.d/issue-4901-interrogate-mando-pin-conflict.md`.
- **FR-009**: The record must name the failing check, the failing step, and the failing rule from the CI logs.
- **FR-010**: The record folder must be `specs\numbered\0\0\1\2\4\1\0\1\4901-interrogate-mando-pin-conflict`. Each parent folder must hold five children or fewer.

### Key Entities

- **Pip update stream**: The `pip` entry in `.github/dependabot.yml`. It holds the schedule, the labels, the commit prefix, and the ignore rules.
- **Ignore rule**: One entry under `ignore` in the pip stream. It holds a `dependency-name` and a `versions` range.
- **Pin**: One `name==version` line in `requirements-dev.txt`. `uv.lock` locks the same version.
- **Required context**: One status name that branch protection requires before a merge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The fix pull request shows success for `Interrogate (docstring coverage)` in one Quality Gates run.
- **SC-002**: None of the 26 jobs that failed on the resolver message shows that message on the fix head.
- **SC-003**: No new pull request for `mando` 0.8 or later opens in the first two weekly Dependabot runs after the merge.
- **SC-004**: All three new policy cases and the snapshot test pass.
- **SC-005**: PR #4888 reads `CLOSED`, and its closing comment names the merged fix.
- **SC-006**: The record names one check, one step, and one rule. Each name matches the CI log text.

## Assumptions

- A **check** is the status name that GitHub shows for one job. A **job** is one entry under `jobs:` in `ci.yml`.
- A **gate** is a group of quality checks. The Interrogate gate is the docstring coverage check.
- A **stream** is one update block in `.github/dependabot.yml`. A **pin** is one `name==version` line.
- No other stream in `.github/dependabot.yml` covers `mando`.
- The runtime file `requirements.txt` pins neither `mando` nor `radon`. The change affects the development toolchain only.
- GitHub branch protection reports 15 required contexts. Research R3 holds the evidence.

## Non-Goals

- No change to `requirements-dev.txt`, `uv.lock`, or `.github/workflows/ci.yml`.
- No radon upgrade and no change to the complexity command.
- No change to the shared `misthelper-devtools` workflows.
- No manual closure of the 14 sibling issues. The gate workflow closes them.
- No change to the README fragment rule. Analysis A-3 records the conflict.
