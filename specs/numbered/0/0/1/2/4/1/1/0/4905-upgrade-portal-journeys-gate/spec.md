# Feature Specification: Upgrade Portal Journeys Gate on PR 4888

**Feature Branch**: `fix/4905-upgrade-portal-journeys-gate`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4905: The CI quality gate `upgrade_portal_journeys` failed on pull request #4888. Dependabot raised mando from 0.7.1 to 0.8.2. Pip could not resolve `requirements-dev.txt`, so the journeys gate stopped in its install step.

## Clarifications

### Session 2026-11-26

- Q: Which check, job, step, and rule failed? → A: The check `Upgrade portal journeys` (job `upgrade_portal_journeys`) failed in step `Install dependencies` of run 45064243269 and job 137339161249. The rule is pip resolution: `ResolutionImpossible` between `requirements-dev.txt` line 365 (`radon==6.0.1`) and `mando==0.8.2`. No journey test ran (research.md, E-1).
- Q: Does main fail the same gate? → A: No. Run 45774119357 on main concluded success for every job, including `Upgrade portal journeys` (research.md, E-4).
- Q: Which commit does the issue cite? → A: The issue cites merge commit `5bb4b385`. The failed job ran on PR head `e86098c`. Both SHAs appear in the record (research.md, E-3).
- Q: Does a newer radon release accept mando 0.8? → A: No. The newest radon release, 6.0.1, requires mando from 0.6 up to, but not including, 0.8 (research.md, D-1).
- Q: May the agent close PR 4888? → A: Only after the fix merges and the orchestrator authorizes the closure. The rule in the instruction file needs that authorization (research.md, D-4, U-2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Name the failure from the CI logs (Priority: P1)

A maintainer reads the record and repeats the read-only commands in the quickstart. The maintainer gets the same failed step and the same pip error text as the record.

**Why this priority**: The maintainer must know whether the failure is a test, a lint, or an install. Only the exact rule answers that question.

**Independent Test**: Run the reproduction commands in `design/quickstart.md`, sections 2 to 4. Compare the output with `design/research.md`, section E-1.

**Acceptance Scenarios**:

1. **Given** run 45064243269, **When** the maintainer reads the failed log, **Then** the output names step `Install dependencies` and the `ResolutionImpossible` error.
2. **Given** job 137339161249, **When** the maintainer reads the job steps, **Then** step 4 has the conclusion `failure` and step 6 has the conclusion `skipped`.

---

### User Story 2 - Keep mando on the tested pin (Priority: P1)

A maintainer keeps mando at 0.7.1. Dependabot no longer proposes mando 0.8 or later releases, and the policy guard protects that rule.

**Why this priority**: The bump blocks the journeys gate on every pull request that installs the development requirements.

**Independent Test**: Run `tests/guardrails/test_pr_title_workflow.py`. The live policy passes. Each mutation of the mando entry fails.

**Acceptance Scenarios**:

1. **Given** the merged change, **When** the policy guard runs, **Then** the live policy equals the policy snapshot.
2. **Given** the mando ignore entry is removed, **When** the policy guard runs, **Then** the guard fails.
3. **Given** the mando range changes to `>=0.9`, **When** the policy guard runs, **Then** the guard fails.
4. **Given** the range `>=0.8`, **When** the guard checks mando 0.8.2 and mando 0.7.1, **Then** 0.8.2 is blocked and 0.7.1 is allowed.

---

### User Story 3 - Close the blocked pull request with proof (Priority: P2)

After the fix merges and the orchestrator authorizes the closure, PR 4888 closes. The branch `dependabot/pip/mando-0.8.2` stays on the remote at `e86098c`, and the closing comment names that branch.

**Why this priority**: An open PR keeps a red gate with no path to green. Closure makes the decision visible without losing the bumped commit.

**Independent Test**: Read the PR state and head with `gh pr view 4888` after closure (quickstart section 12).

**Acceptance Scenarios**:

1. **Given** the fix merged and the authorization exists, **When** the closure runs, **Then** PR 4888 reads `CLOSED`.
2. **Given** PR 4888 is closed, **When** a maintainer reads its head, **Then** the head is `e86098cdc2b189d217805b3b4060ef609cbc37af`.
3. **Given** PR 4888 is closed, **When** a maintainer reads its comments, **Then** a comment names the surviving branch and its commit.

---

### Edge Cases

- A later radon release accepts mando 0.8. The ignore entry then blocks a valid release. The entry comment names the removal condition, and the removal occurs in the same change as the radon bump.
- Dependabot rejects the range form. The pip update stream reports a configuration error. The first pip run after the merge confirms the form (U-1).
- PR 4888 stays red until the closure. The red state is expected, and the gate on main stays green.
- A future change moves a pin in `requirements-dev.txt` without a lock change. The export guard fails in the dependency lock job.
- Gate issues 4891 to 4904 stay open until PR 4888 closes. Their closure follows the closure step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST name the failed check, job, run, step, and rule. Its evidence MUST match the CI logs.
- **FR-002**: The record MUST state that no journey test ran. It MUST state that the upload failed as a result.
- **FR-003**: The change MUST NOT edit `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, or `uv.lock`.
- **FR-004**: The pip update stream MUST ignore mando 0.8 and later releases. Its comment MUST name issue 4905 and PR 4888.
- **FR-005**: The github-actions and npm update streams MUST stay unchanged.
- **FR-006**: The policy guard MUST fail when the pip ignore entry is removed or its range changes.
- **FR-007**: The change MUST add one changelog fragment for issue 4905 with one `Changed` bullet.
- **FR-008**: The record MUST be committed under `specs\numbered\0\0\1\2\4\1\1\0\4905-upgrade-portal-journeys-gate`.
- **FR-009**: Each changed file MUST pass the local gates that apply to it before the commit.
- **FR-010**: PR 4888 MUST close only after the fix merges and the orchestrator authorizes the closure. The closing comment MUST name the surviving branch and its commit.
- **FR-011**: Gate issues 4891 to 4904 MUST close after PR 4888 closes.

### Key Entities *(include if feature involves data)*

- **Pip update stream**: The `pip` entry in `.github/dependabot.yml`. It holds the schedule, the labels, the commit prefix, and the new ignore list.
- **Mando ignore entry**: The rule with `dependency-name` `mando` and `versions` `[">=0.8"]`.
- **Journeys gate job**: The job `upgrade_portal_journeys` in `.github/workflows/ci.yml`. It installs the requirement files and runs the journey harness.
- **Pull request 4888**: The Dependabot pull request that raises mando to 0.8.2. Its head is `e86098c`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `Upgrade portal journeys` job on the merge commit concludes `success` (quickstart section 9, TST-011).
- **SC-002**: After the next pip update run, no open pull request proposes mando 0.8 or a later release (TST-010 and the pull request list).
- **SC-003**: The policy guard passes for the live file and fails for each of the two mutations (TST-001 to TST-003).
- **SC-004**: PR 4888 reads `CLOSED` on head `e86098c`, and its comments name the preservation proof (TST-009).

## Assumptions

- The evidence in `design/research.md` is current on 2026-11-26. The main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Radon 6.0.1 remains the newest release on PyPI (R-65).
- Dependabot accepts a PEP 440 range in `versions` for the pip update stream. The evidence is partial (U-1).
- The orchestrator authorizes the merge and the closure of PR 4888 (U-2).
- Mando is a dev-only transitive pin. It is absent from `requirements.txt` (R-06).

## Out of Scope

- Replacing radon or the complexity gate.
- Changing the journeys harness, its evidence path, or its service containers.
- Adding a row for the journeys gate to `documentation/quality-gates.md`. This gap predates the issue (analysis A-9).
- Changing the Dependabot entries for github-actions and npm.
- Changing the mando pin on main.
- Closing gate issues before the closure step.
