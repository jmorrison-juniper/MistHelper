# Implementation Plan: Mando Pin Conflict Behind the pydocstyle Gate Failure

**Branch**: `fix/4900-mando-radon-pin-conflict` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. Omit `design/contracts/` because no interface contract applies. See the Project Structure section.

## Summary

The Quality Gates pip install fails on pull request 4888. The pull request pins mando 0.8.2, and radon 6.0.1 requires mando below 0.8. Main already pins mando 0.7.1 and passes the same jobs. The plan keeps that pin, blocks Dependabot minor and major mando updates, closes pull request 4888 after the fix merges, and records the evidence.

## Technical Context

**Language/Version**: Python 3.15 for the test module. YAML for `.github/dependabot.yml`.

**Primary Dependencies**: pytest 9.2.0, PyYAML, radon 6.0.1, mando 0.7.1, and uv 0.13.9. The versions come from the `dev` extra in `pyproject.toml`.

**Storage**: Not applicable. The change writes no data store.

**Testing**: Guardrail tests under `tests/guardrails/`, the local gates table in `.github/copilot-instructions.md`, and the remote Quality Gates workflow.

**Target Platform**: GitHub Actions. The affected jobs run on `ubuntu-latest`. Two affected jobs run on Windows runners.

**Project Type**: Continuous integration configuration and dependency policy in a Python repository.

**Performance Goals**: Not applicable. No runtime code path changes.

**Constraints**: No quality gate is removed or relaxed. The requirements exports must match `uv.lock`. Each directory holds five children or fewer.

**Scale/Scope**: Two existing repository files, one new changelog fragment, one new record folder, and one remote pull request closure.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Source: `.specify/memory/constitution.md`, version 1.9.0 (line 4). Each row names one rule with its result and reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (line 38) | Pass, with recorded debt | The change adds one unique fragment to `changelog.d/`, which line 46 permits as a process record. That folder holds 335 children before this change. The remediation action is a separate issue. The route parents hold five children or fewer after the record is added. |
| II. Class-Based Architecture (line 91) | Pass | The change has no production code. The test edit adds data to an existing class and adds no function. |
| III. Safety-First (line 113) | Pass | The change has no input handling, no Mist Cloud operation, and no secret. Closing pull request 4888 needs orchestrator authorization. |
| IV. Full Deployment Pipeline (line 143) | Pass, with a timing note | Steps 1 to 9 run in the order of tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. The auto-merge workflow dispatches `container-build.yml` after each merge into main (`auto-merge.yml` line 65). An operator performs the deploy step. |
| V. Observability and Logging (line 182) | Pass | The change writes no runtime log. The new output is ASCII only. The test edit adds no logging call. |
| VI. Inline Comments (line 204) | Pass, with a required action | Each new line in the YAML block and in the snapshot block carries an inline comment. Closing braces are exempt. |
| VII. Action Logging (line 235) | Pass | The change adds no action. The existing policy fixture already logs before and after it reads the policy file. |
| Technology: Package Manager (line 298) | Pass | `requirements.txt`, `requirements-dev.txt`, `uv.lock`, and `pyproject.toml` do not change. `uv.lock` already locks mando 0.7.1. |
| Technology: File Paths | Pass | The change contains no path-building code. |
| Technology: Test Containers (line 302) | Not applicable | No container starts for this change. `Containerfile` installs requirements.txt only (line 111). |
| Technology: Mist Cloud | Not applicable | The change alters no Mist request or transport. |
| Development Workflow: Security Findings | Pass | No tool finding is suppressed. The Dependabot ignore declines an update. The residual risk is in analysis.md, item A-10. |
| Documentation: Release Notes (line 409) | Pass | One fragment is added under `changelog.d/`. The README rule four conflicts with this rule. The constitution supersedes that README (line 529). Decision D-3 records the choice. |
| Git Flow: branch and commit | Pass | The branch starts from `origin/main`. The commit title uses the Conventional Commits type `fix` and the scope `ci`. The pull request body holds `Closes #4900`. |
| Required Labels | Pass | Issue 4900 holds type label `bug` and scope label `ci`. Task T001 adds the status label `in-progress` before the branch is created. |
| SpecKit Escalation | Pass | The change touches three repository files, so a specification is required. This record is that specification. |
| Compliance review | Pass | Each principle has a result in this table. |

For repository structure, the commit title and pull request title use `fix(ci)`, which the title guard accepts. The change adds only its own unique fragment to `changelog.d/`. Product outputs under `data/` are not affected.

For a feature that uses Juniper Mist Cloud, the rules are not applicable. The change makes no Mist request.

## Architecture

The fix changes policy, not code. It has five parts:

1. Keep the `mando==0.7.1` pin on main. Do not change `requirements-dev.txt` or `uv.lock`.
2. Add a Dependabot `ignore` entry for mando minor and major updates in `.github/dependabot.yml`.
3. Add the same entry to the policy snapshot in `tests/guardrails/test_pr_title_workflow.py`, because that guard compares the complete policy.
4. Add one changelog fragment for the change.
5. Close pull request 4888 after the fix merges. The close happens on GitHub, not in the repository.

## File-by-File Change Map

| Action | Exact repository path | Change |
| - | - | - |
| Modify | `.github/dependabot.yml` | Add an `ignore` block to the pip entry, after line 11. The block names `mando` and lists the minor and major update types. |
| Modify | `tests/guardrails/test_pr_title_workflow.py` | Add the same `ignore` block to the pip entry of `POLICY_SNAPSHOTS["dependabot"]["updates"]`, after line 29. |
| Add | `changelog.d/issue-4900-mando-radon-pin-conflict.md` | One fragment with one `###` heading and one `Fixed` bullet. |
| Add | `specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/` | The record: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` with `research.md`, `data-model.md`, `quickstart.md`, and `checklists/requirements.md`. |
| No change | `requirements-dev.txt`, `requirements.txt`, `uv.lock`, `pyproject.toml`, `.github/workflows/ci.yml`, `.github/workflows/windows-timeout-budget.yml`, `.github/workflows/windows-audit-report.yml` | The pins and jobs stay as they are on main. |
| Remote action | Pull request 4888 and branch `dependabot/pip/mando-0.8.2` | Close without merge after the fix merges. Delete the branch. Not a repository file. |

## Dependencies

No new package is added. The change uses the existing development tools: pytest, ruff, black, pydocstyle, interrogate, symbol-diff, test-quality-analyzer, ste-linter, and gh.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/
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
```

The `design/contracts/` folder is omitted. The change alters no menu, CLI output, API shape, or portal contract. Each directory holds five children or fewer. The feature folder holds five children. The `design/` folder holds four children.

### Structural debt

The `changelog.d/` folder holds 335 direct children on 2026-11-26. The constitution permits one new process record in that folder (line 46). Remediation action: a separate issue, filed by the orchestrator, owns the release-time consolidation of merged fragments.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A Dependabot patch update changes requirements-dev.txt without uv.lock. The export guard then reports stale exports. | The export guard fails visibly. The reviewer checks each mando patch pull request before merge. |
| A security fix ships only in mando 0.8.x. The ignore block blocks it. | Radon limits mando to 0.7 for now. Decision D-5 opens a follow-up issue for radon. |
| A later radon release accepts mando 0.8. | Remove the ignore block and the snapshot entry in the same pull request as the radon update. |
| Pull request 4888 stays open and failing until it closes. | Task T-MERGE closes it after the fix merges. |
| Another job fails once the install step passes. | Task T-REMOTE-CI reads each failing job log and opens a new issue for each new cause. |
| The snapshot test fails if the YAML and snapshot differ. | Tasks T002 and T003 land in one commit. |
| The fragment rule conflicts between the constitution and the README. | Decision D-3 follows the constitution. A separate issue owns the README change. |

## Rollback Steps

1. Open a new pull request that reverts the squash commit on main. The revert removes the ignore block and reopens the Dependabot path for mando minor updates.
2. If only the ignore block causes a problem, remove the block from `.github/dependabot.yml` and the matching snapshot entry in one pull request.
3. To restore pull request 4888, create a branch from commit e86098cd by its SHA.

Warning: never force-push to main. A direct push bypasses the review and the required checks.

## Complexity Tracking

No violation needs justification. The only structural debt is the existing `changelog.d/` count, which the Constitution Check records.
