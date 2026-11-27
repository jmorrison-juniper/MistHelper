# Feature Specification: Bandit Gate Dependency Conflict

**Feature Branch**: `4895-bandit-gate-mando-conflict`

**Created**: 2026-11-26

**Status**: Draft

**Input**: CI quality-gate failure report for issue #4895, titled "CI: quality-gate `bandit` failed (PR #4888)".

## Clarifications

### Session 2026-11-26

- Q: Which check failed? A: The job `Bandit (security)` in workflow `Quality Gates`, run 45064243269, job 137336719159. The job is defined at `.github/workflows/ci.yml` lines 413 to 451.
- Q: Which step failed? A: The step `Run pip install -r requirements-dev.txt`, at `.github/workflows/ci.yml` line 435. GitHub skipped the next two steps.
- Q: Which rule failed? A: No Bandit rule ran. pip stopped with `ResolutionImpossible`, because `mando==0.8.2` conflicts with `radon==6.0.1`.
- Q: Which commit failed? A: The PR #4888 head, `e86098cdc2b189d217805b3b4060ef609cbc37af`. The issue cites `5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71`, which is a GitHub test-merge commit.
- Q: Does `main` fail the same check? A: No. Run 45774119357 on `main` succeeded. Its Bandit steps 5 to 7 succeeded.
- Q: Is a newer radon release available? A: No. The PyPI project page shows radon 6.0.1 as the latest release.
- Q: Do other checks share the cause? A: Yes. 26 of 28 failed jobs in run 45064243269 show the same pip error.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the verified cause of the failed gate (Priority: P1)

A maintainer reads why PR #4888 failed the Bandit gate. The record names the check, the step, the error, and the conflicting pins.

**Why this priority**: A verified cause is required before any safe fix can be chosen.

**Independent Test**: Run the reproduction commands in `design/quickstart.md`. Each named check, step, and error line matches the record.

**Acceptance Scenarios**:

1. **Given** run 45064243269, **When** the maintainer reads the failed log of job 137336719159, **Then** the log shows `ERROR: ResolutionImpossible` and both conflicting pins.
2. **Given** the step list of job 137336719159, **When** the maintainer reads steps 6 and 7, **Then** each step shows `skipped`, which counts as unknown.

---

### User Story 2 - Block the conflicting pin from `main` and from PR #4888 (Priority: P1)

A reviewer cannot merge a `mando` pin that radon 6.0.1 rejects. A guard test fails on that pin.

**Why this priority**: One conflicting pin stops the install step in 26 jobs at the same time.

**Independent Test**: Run `python -m pytest tests/guardrails/test_dependency_declaration_parity.py`. The real-file case passes on `main`. The same case fails when `requirements-dev.txt` pins `mando==0.8.2`.

**Acceptance Scenarios**:

1. **Given** `requirements-dev.txt` pins `mando==0.7.1`, **When** the guard runs, **Then** the guard passes.
2. **Given** a synthetic pin of `mando==0.8.2`, **When** the guard runs, **Then** the guard reports the conflict with `mando (<0.8,>=0.6)`.

---

### User Story 3 - Stop Dependabot from raising the same bump again (Priority: P2)

Dependabot does not open another major or minor `mando` pull request while radon 6.0.1 is pinned.

**Why this priority**: A repeated bump repeats the failure and opens more gate issues.

**Independent Test**: Run `python -m pytest tests/guardrails/test_pr_title_workflow.py`. The complete policy snapshot includes the `mando` ignore entry.

**Acceptance Scenarios**:

1. **Given** `.github/dependabot.yml`, **When** the guard reads the pip stream, **Then** the stream ignores `mando` major and minor updates.
2. **Given** the ignore entry is removed, **When** the guard runs, **Then** the policy snapshot test fails.

---

### Edge Cases

- What happens when radon publishes a release that accepts `mando` 0.8? The ignore entry becomes stale. The maintainer removes it in the pull request that raises radon.
- What happens when `mando` publishes 0.7.2? The ignore entry allows patch updates, so the update proceeds.
- What happens when radon is not installed in the test environment? The guard fails and names the missing package. It does not skip.
- What happens when PR #4888 closes before the fix merges? Dependabot can raise the bump again. Merge the fix first.
- What happens when Bandit reports a real finding later? The gate stays strict. This change adds no suppression or exclusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `requirements-dev.txt` MUST keep `mando` at `0.7.1` while `radon==6.0.1` is pinned.
- **FR-002**: The guard MUST fail when the pinned `mando` violates the installed radon requirement.
- **FR-003**: The guard MUST fail for the synthetic pin `mando==0.8.2` against `mando (<0.8,>=0.6)`.
- **FR-004**: `.github/dependabot.yml` MUST ignore `mando` major and minor updates in the pip stream.
- **FR-005**: The complete policy snapshot MUST include the same `mando` ignore entry.
- **FR-006**: The change MUST add no direct child to `tests/guardrails`, which already holds 77 files.
- **FR-007**: PR #4888 MUST NOT merge while its head pins `mando==0.8.2`.
- **FR-008**: The change MUST keep every gate command in `ci.yml` and every exclusion unchanged.
- **FR-009**: The change MUST add no `# nosec`, `# noqa`, or exclusion for Bandit or Ruff.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The feature makes no Mist Cloud call. It changes one dependency policy file and two guard test files.

### Key Entities *(include if feature involves data)*

- **Dependency pin**: An exact version line in `requirements-dev.txt`. The natural key is the package name. The `mando` pin is `0.7.1` on `main`.
- **Dependency constraint**: The requirement that radon 6.0.1 declares for `mando`. The natural key is the declaring package and the required package.
- **Gate job**: A CI job with a fixed name. The natural key is the job database ID. The Bandit job ID is 137336719159.
- **Dependabot ignore rule**: A rule in the pip stream of `.github/dependabot.yml`. The natural key is the ecosystem and the dependency name.
- **Gate issue**: An issue that the quality gate sync opens for one failed gate. The natural key is the issue number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fix pull request head, the step `Run Bandit` in job `Bandit (security)` shows `success`.
- **SC-002**: On the PR #4888 head content, the real-file guard case fails with the radon conflict message.
- **SC-003**: After PR #4888 closes, no open pull request pins `mando` above `0.7.x` while radon 6.0.1 is pinned.
- **SC-004**: The 15 gate issues for PR #4888 close after PR #4888 closes and a `main` run completes.
- **SC-005**: The remote check count is 32 in `STATUS.json`, in `design/research.md`, and in `summary.md`.

## Assumptions

- The repository stays on GitHub with Dependabot enabled for pip.
- CI runs Python 3.15, as set in `.github/workflows/ci.yml` line 77.
- radon 6.0.1 is still the newest radon release when the fix runs. The implementer checks PyPI again before the pull request.
- The maintainer authorizes the closure of PR #4888 and the `auto-merge` label.
- The repository is public, so standard runners cost no minutes, as `.github/copilot-instructions.md` line 478 states.

## Out of Scope

- Changing the Bandit command, its exclude list, or its severity setting.
- Adding a suppression for any Bandit or Ruff finding.
- Changing the radon version or the `radon` gate.
- Editing `uv.lock`, which already pins `mando` at 0.7.1.
- Changing the shared `quality_gate_issues` workflow in `misthelper-devtools`.
- Closing the 15 gate issues by hand.
