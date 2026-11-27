# Feature Specification: Vulture Gate Mando Radon Conflict

**Feature Branch**: `fix/4899-vulture-gate-mando-radon-conflict`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4899. The quality gate `vulture` failed on pull request #4888, which bumps `mando` from 0.7.1 to 0.8.2.

## Terms

- **Check name**: The status name that GitHub shows, for example `Vulture (dead code)`.
- **Job ID**: The key under `jobs:` in `.github/workflows/ci.yml`, for example `vulture`.
- **Fix pull request**: The pull request that this specification plans.

## Clarifications

### Session 2026-11-26

- Q: Which check failed, and at which step? → A: The check `Vulture (dead code)` failed at step 4, `Run pip install -r requirements-dev.txt`. Run 45064243269, job 137336718674, shows it. Step 5, `Detect dead code`, did not run.
- Q: Did vulture find dead code? → A: No. The vulture scan never started. The log holds no vulture output, because the install failed first.
- Q: Which rule failed? → A: pip reported `ResolutionImpossible`. Pull request #4888 pins `mando==0.8.2`. The pinned `radon==6.0.1` requires `mando<0.8,>=0.6`.
- Q: Can the fix raise `radon` instead? → A: No. The upstream default branch and tag `v6.0.1` still require `mando>=0.6,<0.8`.
- Q: Does a person need to decide? → A: No. No licensing, data, credential, or product priority decision applies.
- Q: Does the change need a release-note fragment? → A: Yes. The constitution requires one fragment for each change. The changelog README allows no fragment for an internal-only change. The constitution governs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vulture job reaches its scan (Priority: P1)

The maintainer opens the fix pull request. The Vulture job installs the pinned tools and then runs the vulture scan.

**Why this priority**: The failing check blocks the pull request flow. Every later Dependabot pull request for `mando` repeats the failure.

**Independent Test**: Read the Quality Gates run of the fix pull request. Confirm that step 5 succeeds and that no resolver error appears.

**Acceptance Scenarios**:

1. **Given** the fix pull request, **When** its Quality Gates run ends, **Then** step `Detect dead code` of the `Vulture (dead code)` check concludes success.
2. **Given** the fix pull request, **When** an operator reads the failed logs of its run, **Then** no line contains `ResolutionImpossible`.

---

### User Story 2 - Dependabot stops the mando 0.8 bump (Priority: P1)

Dependabot checks the pip ecosystem each week. Without a rule, it proposes `mando` 0.8.2 again.

**Why this priority**: Without this rule, the same failure returns after the fix.

**Independent Test**: Run the policy guard in `tests/guardrails/test_pr_title_workflow.py` with the rule present, removed, and changed.

**Acceptance Scenarios**:

1. **Given** the pip stream with the mando rule, **When** the policy guard runs, **Then** the guard passes.
2. **Given** the pip stream without the mando rule, **When** the policy guard runs, **Then** the guard fails with a Dependabot message.
3. **Given** the mando rule that starts at 0.9, **When** the policy guard runs, **Then** the guard fails with a Dependabot message.

---

### User Story 3 - Maintainer learns why mando stays pinned (Priority: P2)

A maintainer reads the quality gate guide and the Dependabot file. Both name the cause and the removal condition.

**Why this priority**: A later maintainer can remove the rule safely only when the reason is known.

**Independent Test**: Read the note in `documentation/quality-gates.md` and the comment in `.github/dependabot.yml`. Confirm that both name `radon==6.0.1` and the removal condition.

**Acceptance Scenarios**:

1. **Given** the quality gate guide, **When** a reader opens the vulture row, **Then** the note names the install step and the removal condition.
2. **Given** the changelog folder, **When** the fragment guard runs, **Then** `changelog.d/issue-4899-mando-radon-pin.md` passes.

---

### Edge Cases

- A later `mando` release (0.8.x or 0.9.x) appears: the rule blocks every version from 0.8 upward. No pull request opens.
- Radon releases a version that accepts `mando` 0.8: remove the rule and move the `mando` pin in one change.
- Dependabot rejects the rule syntax: Dependabot stops every pip update. Revert the fix commit to restore the previous state.
- A person reopens pull request #4888: the same resolver conflict fails again. Step T-MERGE closes it after the merge.
- A fix pull request job fails for a different cause: file a separate issue with the full error output before any fix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Vulture job MUST run its scan step on the fix pull request.
- **FR-002**: The fix MUST keep `mando==0.7.1` in `requirements-dev.txt` and in `uv.lock`.
- **FR-003**: Dependabot MUST NOT propose `mando` 0.8 or later while `main` pins `radon==6.0.1`.
- **FR-004**: The pip stream of `.github/dependabot.yml` MUST hold one ignore rule for `mando` with versions `>= 0.8`.
- **FR-005**: The policy guard MUST fail when a person removes the mando rule or changes its lower bound.
- **FR-006**: The fix MUST NOT change the vulture command, its paths, its threshold, or any other gate.
- **FR-007**: The quality gate guide MUST name the install-step failure and the removal condition of the rule.
- **FR-008**: The change MUST add one release-note fragment that names issue #4899 and one change type.
- **FR-009**: The record MUST name the failing check, job ID, run ID, step, and resolver rule.
- **FR-010**: A maintainer MUST close pull request #4888 as superseded after the fix merges, with a comment that names the fix pull request.
- **FR-011**: The change MUST NOT add a direct child to `tests/guardrails`, which already holds 79 direct children.
- **FR-012**: The fix pull request run MUST show no `ResolutionImpossible` line in any job.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The fix pull request shows zero failed steps in the `Vulture (dead code)` job.
- **SC-002**: The fix pull request run holds zero lines that contain `ResolutionImpossible`.
- **SC-003**: The policy guard passes with the rule present and fails in both changed cases.
- **SC-004**: The next weekly Dependabot pip run opens no pull request for `mando` 0.8 or later.
- **SC-005**: Quality Gates on `main` stay green for every job after the fix merges.

## Assumptions

- `main` keeps `mando==0.7.1` and `radon==6.0.1` until a deliberate pin change.
- Dependabot applies `ignore.versions` with the package manager range pattern, as the GitHub docs state.
- The Quality Gates run 45774119357 on commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca concluded success.
- The other pins and gate settings stay unchanged.

## Out of Scope

- Upgrading `radon` or `mando`.
- Changing the vulture threshold, the scan paths, or the job structure.
- Repairing the other failed checks on pull request #4888 beyond the shared resolver conflict.
- Reading the Windows checks of runs 45064235051 and 45064235097.
- Splitting `tests/guardrails`, which is existing debt tracked separately.
- Closing open related gate issues before their gates pass on `main`.
- Mist API and `mistapi` behavior. This change sends no Mist request.
