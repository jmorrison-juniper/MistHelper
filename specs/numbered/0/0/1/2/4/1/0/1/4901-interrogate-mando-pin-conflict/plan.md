# Implementation Plan: Interrogate Gate Failure on PR #4888

**Branch**: `fix/4901-interrogate-mando-pin-conflict` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record `specs\numbered\0\0\1\2\4\1\0\1\4901-interrogate-mando-pin-conflict`. The route rule lives in `.specify/scripts/powershell/spec-route.ps1` (RV-24, RV-25).

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Keep research, data model, quickstart, and checklists under `design/`.

## Summary

The Interrogate check fails because PR #4888 raises `mando` to 0.8.2. Radon 6.0.1 requires `mando` below 0.8. Pip stops before the docstring command runs. `main` already pins `mando` 0.7.1. The fix adds a Dependabot ignore rule for `mando` 0.8 and later. It adds three policy cases, updates the policy snapshot, and adds one changelog fragment. PR #4888 closes after the fix merges.

## Technical Context

**Language/Version**: Python 3.15 or newer (copilot instructions, section "Language and environment", RV-34).

**Primary Dependencies**: pytest 9.2.0 (RV-67), PyYAML 6.0.4 (RV-68), and packaging 26.3 (RV-04). All three are pinned in `requirements-dev.txt`. The change adds no dependency.

**Storage**: Not applicable. The change writes no product data.

**Testing**: The guard tests in `tests/guardrails/` and the local gates of the copilot instructions (section "Local gates", RV-35).

**Target Platform**: The Interrogate job runs on a GitHub-hosted Linux runner (job definition, RV-08). Local runs use Windows 11 (RV-34).

**Project Type**: Repository configuration change and guard test change.

**Performance Goals**: Not applicable. The change adds no runtime code.

**Constraints**: The pip update stream runs weekly (RV-69). Branch protection requires up-to-date branches (Sources, branch protection read). The dev requirements file is generated from `uv.lock` (RV-03, RV-59).

**Scale/Scope**: Four changed paths. The record folder holds nine files.

## Constitution Check

*Gate: passes before research and after design.*

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule (RV-49) | Pass | The route parent `specs/numbered/0/0/1/2/4/1` holds two children after the change. The fragment is a unique record in `changelog.d/`, which the rule allows. |
| II. Class-based architecture | Pass | The three new cases are one method in the existing class `TestDependabotPolicy`. No wrapper function is added. |
| III. Safety first | Pass | The change reads no operator input and runs no destructive operation. |
| IV. Full deployment pipeline (RV-50) | Pass with a manual step | Steps 1 to 9 map to tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 need a manual dispatch of `container-build.yml` (RV-40, RV-51, RV-52). |
| V. Observability and logging | Pass | The new cases log in ASCII text with `%s` values. The fixture pattern is RV-22. |
| VI. Inline comments (RV-53) | Pass | Each new Python line and each new YAML line carries an inline comment. Task T007 checks this. |
| VII. Action logging (RV-54) | Pass | The new method logs before and after the policy read, as the fixture does (RV-22). |
| Technology: Mist transport | Not applicable | The change calls no Mist endpoint. |
| Technology: package manager | Pass | `requirements.txt` (RV-19) and `requirements-dev.txt` (RV-01) stay unchanged. `uv.lock` (RV-06) stays unchanged. |
| Technology: file paths | Pass | The test reads `.github/dependabot.yml` through `Path` objects, as the fixture does (RV-22). |
| Development workflow: testing (RV-35) | Pass | Task T-LOCAL-GATES runs the compile gate and the guard tests. |
| Documentation: one fragment (RV-55) | Pass | One fragment is added. The conflict with the fragment README is analysis item A-3. |
| Complexity escalation (RV-56) | Pass | The change touches more than two files, so this spec is required. |
| Multi-agent git workflow (RV-41, RV-42, RV-44, RV-47) | Pass | The issue is claimed first. The branch name follows the repository form (RV-42). The PR body holds `Closes #4901`. PR #4888 closes only with a proof. |
| Test quality ratchet (RV-36) | Pass | The ratchet runs after the local commit and before the push. |
| PR template guard item (RV-62) | Pass | The PR body states the measured count and one failing path for the new cases. Task T005 records that output. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/0/1/4901-interrogate-mando-pin-conflict/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
      ci-evidence.md
```

Contracts: Omitted. No interface contract applies. The change edits one policy file, one guard test, and adds one fragment. No output format, command, or API shape changes.

### Source Code (repository root)

| Path | Action | Change | Requirement |
|------|--------|--------|-------------|
| `.github/dependabot.yml` | Modify | Add an `ignore` list to the pip stream after line 11. The entry names `mando` and `versions: [">= 0.8"]`. Add a comment block above the entry. | FR-002, FR-003 |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same ignore list to `POLICY_SNAPSHOTS["dependabot"]["updates"][0]` after line 29 (RV-20). Add one parametrized method to `TestDependabotPolicy` after line 329. | FR-002, FR-003, FR-004 |
| `changelog.d/issue-4901-interrogate-mando-pin-conflict.md` | Add | One `###` heading and one `Changed` bullet that names issue #4901. | FR-008 |
| `specs/numbered/0/0/1/2/4/1/0/1/4901-interrogate-mando-pin-conflict/` | Add | This record. The files come from the draft folder. | FR-009, FR-010 |

Unchanged, and verified by the remote table: `requirements-dev.txt` (RV-01, RV-02), `uv.lock` (RV-06, RV-07), `requirements.txt` (RV-19), `.github/workflows/ci.yml` (RV-08 to RV-11), and all product code.

Deleted: none.

## Architecture

The Dependabot pip stream reads the pins that the repository declares. The new ignore rule removes `mando` 0.8 and later from the candidate updates. Dependabot then opens no pull request for `mando` 0.8. The pins and the lock stay at 0.7.1. The Interrogate job installs the file without a resolver error, and then it runs the docstring command.

## Dependencies

- No new package is added.
- The test uses `yaml` (PyYAML, RV-68) and `packaging.specifiers` (packaging, RV-04). Both packages are pinned in the development requirements.
- The ignore syntax follows the Dependabot options reference (RV-63) and the PEP 440 operator set (RV-65).

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| Dependabot rejects the rule syntax | The weekly run logs an error, or it opens a PR for `mando` 0.8 again | Check the next weekly run after the merge (U-1). Correct the syntax in a new change. |
| A radon release accepts `mando` 0.8 | The ignore rule blocks a valid update | Remove the rule in the same change that upgrades radon (spec Edge Cases). |
| The snapshot and `dependabot.yml` drift | The policy test fails | The test compares the whole policy, so drift fails at once (RV-21). |
| The docstring coverage falls below 90 percent | The Interrogate job fails for a new cause | Run the docstring command locally in T-LOCAL-GATES. Check the CI result in T-REMOTE-CI. |
| PR #4888 closes before the fix merges | The rejected bump loses its open record | T-MERGE closes PR #4888 only after the merge (D-2). |
| A hand edit of `requirements-dev.txt` | The export check fails, because the file must match `uv.lock` | The change does not edit the file (spec Edge Cases). |

## Rollback Steps

1. Open a revert pull request for the squash commit of the fix on `main`.
2. Reopen PR #4888 if its closure was wrong (Caution in research R6).
3. Confirm that the revert removes the ignore rule, the three cases, the snapshot entry, and the fragment.
4. Confirm that the Interrogate check passes on the reverted head before the revert merges.

## Complexity Tracking

No violation. The change adds no direct child to a noncompliant parent. It adds no file to `tests/guardrails/`. It edits existing files only, except for the record and the fragment.
