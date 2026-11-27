# Implementation Plan: Dependabot mando pin for the dependency_lock job

**Branch**: `fix/4903-mando-radon-pin` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Pull request #4888 raised `mando` from 0.7.1 to 0.8.2 in `requirements-dev.txt`. Radon 6.0.1 requires `mando` below 0.8. The pip install in the `dependency_lock` job cannot resolve, so the job fails. The fix keeps `mando` at 0.7.1. It also stops Dependabot from proposing a minor or major `mando` update. The change edits one Dependabot file, one guard snapshot, and one gate document. It adds one changelog fragment and this record.

## Technical Context

**Language/Version**: Python, with the version named by `PYTHON_VERSION` in `.github/workflows/ci.yml`.

**Primary Dependencies**: pip, uv, radon 6.0.1, mando 0.7.1, PyYAML, and pytest for the guard tests.

**Storage**: Not applicable. The change touches no data store.

**Testing**: pytest guard tests in `tests/guardrails`.

**Target Platform**: `ubuntu-latest` for the `dependency_lock` job. Windows 11 for local checks.

**Project Type**: CI configuration, one guard test snapshot, one gate document, and one changelog fragment.

**Performance Goals**: Not applicable. The change alters no runtime path.

**Constraints**: Dependabot runs on its configured schedule. The guard fails when the snapshot differs from the policy.

**Scale/Scope**: Four repository paths and one record folder.

## Constitution Check

Each rule below carries a result and a reason. Rule text comes from `.specify/memory/constitution.md`.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (line 38) | Pass | The record uses the managed root `specs/numbered/` and the base-5 route. Each level holds five children or fewer. The changelog fragment is the only new direct child of `changelog.d/`. |
| II. Class-Based Architecture (no wrappers) | Pass | The two new mutation rows extend the existing `TestDependabotPolicy` class. The change adds no wrapper function. |
| III. Safety-First | Pass | The change adds no keyboard input, no destructive operation, and no external input. |
| IV. Full Deployment Pipeline (line 143) | Pass | The plan runs local gates, commits with a Conventional Commit subject, rebases, pushes, opens a pull request, waits for CI, and squash merges. No main image build runs, because `container-build.yml` does not list `.github/dependabot.yml`. |
| V. Observability and ASCII logging | Pass | The change alters no product log output. The new text is ASCII. |
| VI. Inline Comments (line 204) | Pass | Each added YAML line and each added test row carries a comment. Each changed snapshot line carries a comment. |
| VII. Action Logging (line 235) | Pass | The change adds no action code. The existing guard test body stays unchanged. |
| Technology: UV and requirements parity | Pass | `requirements.txt`, `requirements-dev.txt`, and `uv.lock` stay unchanged, so the export parity holds. |
| Technology: Python 3.15 or newer | Pass | No code path targets an older Python version. |
| Technology: mistapi as the only Mist access | Not applicable | The change calls no Mist API. |
| Technology: Podman and test containers | Not applicable | The change starts no container. |
| Technology: File paths | Not applicable | The change adds no path code. |
| Technology: Data directory and output backends | Not applicable | The change writes no product output. |
| Development: Testing | Pass | The local gates in `tasks.md` run the changed guard and each affected guard. |
| Security findings: fix over suppress | Pass | The change adds no `#nosec`, `noqa`, or `type: ignore` comment. |
| Documentation (line 398) and release notes (line 409) | Pass | The gate document gets the mando pin section. One changelog fragment is added. `CHANGELOG.md` stays unchanged. |
| Audience standard | Pass | The new gate text uses plain words for junior NOC engineers. |
| Complexity-Driven SpecKit Escalation (line 420) | Pass | The change touches four repository paths and one record. This record is the required specification. |
| Multi-Agent Git Workflow (line 453) | Pass | Issue #4903 exists. The branch `fix/4903-mando-radon-pin` starts from `main`. The commit subject uses Conventional Commits. The pull request body holds `Closes #4903`. No step pushes to `main`. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      dependabot-policy.md
    checklists/
      requirements.md
```

### Source Code (repository root)

| Path | Action | Change | Requirement |
| - | - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` block to the pip update block, after line 11. | FR-002, FR-004 |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same `ignore` block to the pip entry of `POLICY_SNAPSHOTS["dependabot"]`, after line 29. Add two rows to the mutation list of `test_unrelated_changes_fail`. | FR-003 |
| `documentation/quality-gates.md` | Modify | Add `dependency_lock` to the job ID list. Add one table row after the `pip_audit` row (line 57). Add a section before `## Exclusion drift report` (line 167). | FR-006 |
| `changelog.d/issue-4903-mando-radon-pin.md` | Add | One `Fixed` entry for this change. | FR-005 |
| `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/` | Add | This record, copied from the draft folder. | FR-008 |

Not changed: `requirements-dev.txt`, `requirements.txt`, `uv.lock`, `pyproject.toml`, `.github/workflows/ci.yml`, and `CHANGELOG.md`.

## Implementation Outline

1. Add the `in-progress` label to issue #4903. The orchestrator authorizes this step.
2. Create the branch `fix/4903-mando-radon-pin` from `origin/main` in a separate worktree.
3. Edit `.github/dependabot.yml`, the policy snapshot, and `documentation/quality-gates.md`.
4. Add the changelog fragment and copy this record into the repository route.
5. Run the local gates listed in `tasks.md`.
6. Commit, rebase, push, open the pull request, and watch CI. Merge after orchestrator authorization.

## Dependencies

- No package dependency changes.
- `tests/guardrails/test_pr_title_workflow.py` reads `.github/dependabot.yml`.
- The `dependency_lock` job reads `requirements-dev.txt`, `uv.lock`, and `tests/guardrails/test_dependency_export.py`.

## Contracts

`design/contracts/dependabot-policy.md` defines the required shape of the pip update block.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| Dependabot does not honor the ignore. | A later `mando` 0.8 pull request fails the `dependency_lock` job again. | Close each such pull request. Verify after the first Dependabot run. Item U-1 in `research.md` tracks this risk. |
| A security update names `mando` and bypasses the ignore. | A failing pull request remains open. | The `dependency_lock` job blocks the merge. A maintainer decides whether to replace radon. Item U-2 tracks this risk. |
| The policy snapshot weakens during review. | The Dependabot policy guard stops protecting the pin. | The two new mutation rows fail when the ignore is removed or weakened. The reviewer reads the snapshot diff. |
| The gate document fails the writing gate. | The file scores below 80 in the writing gate, and the change stays incomplete. | Run `ste-linter` on the file before the commit. |
| A route folder breaks the five-children rule. | The record cannot merge under the structure guard. | The base-5 route holds five digits at most per level. Run `tests/guardrails/test_process_folder_structure.py`. |
| Closing pull request #4888 hides a real defect. | The defect stays open without a visible failing check. | Close pull request #4888 only after the fix merges and the `dependency_lock` job passes on the fix head. |

## Rollback Steps

1. Open a new pull request that reverts the squash-merge commit.
2. Run the local gates in `tasks.md` on the revert branch.
3. Wait for CI. Merge after orchestrator authorization.

Warning: do not force-push `main`. A force push removes commits that other agents use.
