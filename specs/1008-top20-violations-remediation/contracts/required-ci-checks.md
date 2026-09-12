# Contract: Required CI Checks (234+ Green Per PR)

**Feature**: Top-20 Compliance Violations Remediation
**Contract type**: Merge gate specification
**Source of truth**: GitHub branch protection rules on `main` at the time each PR
merges. This document is a **snapshot** of what those rules were expected to require
as of 2026-07-02; the live GitHub configuration is authoritative if the two ever
diverge.

**Status for this initiative**: FR-010 and SC-005 require **all 234+ required checks**
to be green on every PR before squash-merge. No check may be marked optional, skipped,
or bypassed to unblock a merge.

## How to enumerate the current required checks

The exact required-checks list evolves with the workflow files in
`.github/workflows/`. Do NOT hard-code the list into any PR body or automation.
Instead, enumerate it live at PR time:

```powershell
# List all required status checks on the main branch.
gh api "repos/:owner/:repo/branches/main/protection/required_status_checks" `
  --jq '.contexts[]' `
  | Sort-Object `
  | Get-Unique
```

The resulting list is the contract for the PR currently in flight. If a check is added
to that list mid-initiative, subsequent PRs must satisfy the enlarged list. If a check
is removed, remaining PRs are still held to the stricter (2026-07-02) set - the
initiative does not relax under branch-protection changes (spec Assumption line 151).

## Categories of required checks (as of 2026-07-02)

The 234+ figure aggregates across the following check families. These are the
categories a remediation PR must pay attention to; the live list is authoritative for
exact names.

### Build and packaging

- Container image build (`.github/workflows/container-build.yml`)
- Wheel / sdist build (if configured)
- Podman image publish smoke (may be gated behind label)

### Static analysis

- `ruff check .` across the repo
- `black --check .`
- `mypy --strict` on packages currently under strict
- `pyright` (if configured; on some Windows agents)
- `bandit` security scan
- `pip-audit` / `safety` dependency-vuln scan
- `codeql` code scanning (multiple language matrices)

### Compliance

- `python -m tools.compliance_analyzer .` full-repo run with a minimum-score gate
- `python -m tools.compliance_analyzer <changed-files>` per-file gate

### Tests

- `pytest tests/unit/` unit test suite
- `pytest tests/integration/` integration suite (Skips 14, 18, 63-65, 90-100 per
  Constitution)
- Snapshot / golden-file tests where applicable

### Documentation and metadata

- README version-string check (must match commit prefix `version YY.MM.DD.HH.MM`)
- Menu operation count check (README table vs. code registry)
- Changelog entry required for new operations

### Cross-platform matrices

Many checks run on both `ubuntu-latest` and `windows-latest`, and across Python 3.13
and 3.14 (if present). The matrix multiplies the check count above into the "234+"
aggregate.

## Verification protocol

For every PR:

1. Open the PR. Wait for CI to schedule all required jobs.
2. Run `gh pr checks <pr-number> --watch` until all statuses settle.
3. If any required check is `fail` or `pending` past its expected duration:
   - Diagnose using `gh run view <run-id> --log-failed`.
   - Fix in-branch (push a follow-up commit). Do NOT retry to mask a genuine
     failure. Retries are permitted only for infrastructure flakes with evidence
     (e.g., transient network on a package install step, reproducible on `main`).
4. Only when every required check is `pass`, run `gh pr merge <pr> --squash --delete-branch`.

## Post-merge verification

After each squash-merge:

```powershell
# Confirm main is at the merge SHA.
git checkout main
git pull --ff-only
git log -1 --oneline

# Confirm the target file's post-refactor score on main.
python -m tools.compliance_analyzer <path>
# Expected: score >= 95.0, grade A+.

# Confirm repo-wide score has not regressed.
python -m tools.compliance_analyzer .
# Expected: overall score monotonically non-decreasing across the campaign.
```

## Non-compliance

If any of the following are true, the PR does not merge:

- A required check is `fail` and the failure was caused by this PR's changes (fix in
  the same PR).
- A required check is `fail` due to a genuine flake (retry once with evidence; if
  still flaky, file an issue and pause).
- A required check is `skipped` because the PR modified a workflow file to mark it
  optional (revert the workflow change; the initiative may not relax any gate).
- A required check is `pending` beyond twice its historical p95 duration (file an
  infrastructure issue; do not force-merge).

## Coordination with other in-flight work

Per Constitution Multi-Agent Git Workflow rules and spec Assumption line 156:

- Only ONE remediation PR from this campaign may be in the `open-for-merge` state at
  a time.
- Other agents' PRs against unrelated files may run in parallel provided they touch
  none of the twenty target files, and provided they do not modify
  `tools/compliance_analyzer/` or related config.
- If another agent's PR merges to `main` and pushes new violations into a not-yet-
  refactored target file, this initiative's PR for that file uses the post-drift
  score as its baseline (spec Edge Case line 99).
