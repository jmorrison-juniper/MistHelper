# Implementation Plan: Ruff (lint) check failure from the mando 0.8.2 pin

**Branch**: `fix/4891-dependabot-mando-ignore` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric record route `specs\numbered\0\0\1\2\4\0\3\1`. The route rule is in `.specify\scripts\powershell\spec-route.ps1` (RV-40 to RV-42).

Repository paths in this plan use Git form, with forward slashes. The record path uses backslashes, as the orchestrator requires.

## Summary

PR #4888 pins mando 0.8.2 in `requirements-dev.txt`. Radon 6.0.1 requires mando below 0.8. The pip install step fails with a resolver conflict, so the Ruff (lint) check never runs `ruff check .`. `main` already pins mando 0.7.1. This plan adds one narrow Dependabot ignore entry, three guard cases, and one changelog fragment. It changes no pin.

## Technical Context

- **Language/Version**: Python 3.15 or newer (RV-38). Configuration in YAML (Dependabot).
- **Primary Dependencies**: pytest for the guard cases. PyYAML is already used by a guard module (RV-39). No new dependency.
- **Storage**: Not applicable. No data store changes.
- **Testing**: pytest guard cases in `tests/guardrails`. The local gates table runs them (RV-48), and CI pytest shards run them.
- **Target Platform**: Windows 11 for local development. The Quality Gates workflow runs in CI (run 45064243269).
- **Project Type**: CI configuration, one guard module, and one changelog fragment.
- **Performance Goals**: Not applicable. No runtime path changes.
- **Constraints**: No product file changes (RV-36). No new direct child under `tests/guardrails` (RV-43, RV-44). The fragment name uses the issue form (RV-61).
- **Scale/Scope**: Three guard cases, one ignore entry of four YAML lines, one fragment, one record folder.

## Constitution Check

*Gate result after design: Pass. Each rule has a result and a reason. Principles VI and VII are checked again in T002 and T003.*

The Core Principles start at line 38 (RV-46).

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule | Pass, with recorded debt | The change adds no direct child to `tests/guardrails`, which holds 79 children (RV-43). Each new record level holds at most three children (RV-45). Existing debt: `tests/guardrails` (grandfathered). Separate remediation: analysis DEF-07. |
| II. Class-Based Architecture | Pass | The guard uses class `DependabotPolicy` for helpers and class `TestDependabotMandoIgnore` for cases. No wrapper function. |
| III. Safety-First | Pass | The guard reads YAML with a safe loader (RV-39 pattern). It takes no user input and no secret. |
| IV. Full Deployment Pipeline | Pass, steps 10 to 12 not triggered | Steps 1 to 9 run in T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 need a product change, and this change has none (RV-36, RV-37, decision D-6). |
| V. Observability and Logging | Pass | Log messages use ASCII only. Each file read logs before and after the read. |
| VI. Inline Comments (NON-NEGOTIABLE) | Pass in design | Each executable line of the new code gets an inline comment. The YAML entry gets comment lines that explain the reason. T002 and T003 check it. |
| VII. Action Logging (NON-NEGOTIABLE) | Pass in design | Each action in the guard logs an `info` line before it and a `debug` line after it. T002 checks it. |
| Mist Cloud constraints | Not applicable | No Mist Cloud request, no mistapi change, and no WebSocket transport. |
| Commit and title form | Pass | The commit subject and the pull request title use `fix(ci): ignore mando minor updates that radon 6.0.1 blocks`, which the constitution accepts (RV-47). |
| Process folder rule | Pass | The change adds only its own record and its own fragment (RV-44, RV-20). |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\0\3\1\4891-ruff-gate-mando-conflict\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    checklists\
      requirements.md
```

The `design\contracts\` folder is omitted. No interface contract applies. The change adds no menu, CLI, portal, API, or file format. The Dependabot entry is configuration, and the guard cases are its contract.

### File-by-file change map

| Path (Git form) | Action | Purpose | Requirements |
| --- | --- | --- | --- |
| `.github/dependabot.yml` | Modify | Add the mando ignore entry to the pip block, after line 11 (RV-52, RV-15). | FR-002, FR-003 |
| `tests/guardrails/test_dependency_export.py` | Modify | Add helper class `DependabotPolicy`, test class `TestDependabotMandoIgnore`, and three cases. Name issue #4891 in the module docstring. | FR-004 |
| `changelog.d/issue-4891-dependabot-mando-ignore.md` | Add | One fragment with one `###` heading and one `Fixed` bullet (RV-19, RV-61). | FR-005 |
| `specs/numbered/0/0/1/2/4/0/3/1/4891-ruff-gate-mando-conflict/` | Add | This record, copied from the draft folder (RV-42, D-7). | FR-006 |
| `requirements-dev.txt` | No change | Already pins mando 0.7.1 (RV-01). | FR-001 |
| `uv.lock` | No change | Already locks mando 0.7.1 (RV-05). | FR-001 |
| `pyproject.toml` | No change | Declares radon 6.0.1 and no direct mando (RV-07, RV-08). | FR-001 |
| `.github/workflows/ci.yml` | No change | The jobs already run the gates (RV-09 to RV-14). | FR-008 |
| `documentation/quality-gates.md` | No change | The job-list drift is out of scope (analysis DEF-03). | None |

## Dependencies

- No package is added or changed.
- The Dependabot pip update block gains one ignore entry. No other Dependabot setting changes.
- The guard cases use PyYAML and the standard library only.

## Implementation Outline

1. T001: Confirm that the mando 0.7.1 pin and the lock agree on `main`. No edit.
2. T002: Write the three guard cases first. Cases 1 and 2 fail on `main`.
3. T003: Add the ignore entry. Cases 1 and 2 pass.
4. T004: Add the fragment.
5. T005: Copy the record folder.
6. T-LOCAL-GATES: Commit the test change, run the test-quality procedure, and run the other applicable local gates.
7. T-PR: Rebase, push the branch, and open the fix pull request.
8. T-REMOTE-CI: Watch the required checks until each one reports success.
9. T-MERGE: Add the auto-merge label after authorization. Check the merged `main` and the closed issue.

### Guard design (no code in this record)

- Class `DependabotPolicy` has two static methods. Method `read_pip_ignores` reads the YAML file with `yaml.safe_load`, finds the update block whose ecosystem is `pip`, and returns its `ignore` list. Method `find_gap` returns a message when no mando entry covers semver-minor updates, or when the entry blocks semver-patch updates. It returns None otherwise.
- Class `TestDependabotMandoIgnore` has three cases. The first reads the real file, asserts that the list is not empty, asserts that `find_gap` returns None, and prints the count of entries examined. The second asserts that the mando entry does not block semver-patch updates. The third calls `find_gap` with an empty list and asserts that the message names mando.
- Each method stays within five parameters, five logical blocks, and 25 lines (constitution Principle I).

## Complexity Tracking

| Violation or debt | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| `tests/guardrails` holds 79 direct children (grandfathered, RV-43). | The guard cases must sit in an existing guard module, next to the export guard that Dependabot changes affect. | A new file or package adds a direct child to a noncompliant parent (RV-44). |

Existing debt is recorded here. The separate remediation action is analysis DEF-07, outside this change.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| --- | --- | --- |
| R-01: Dependabot ignores the `update-types` filter for pip (U-01). | A pip pull request for mando can still open. | The pins stay at 0.7.1 in every case. The next weekly run shows the result (RV-52). A follow-up issue starts if it fails. |
| R-02: A future radon release accepts mando 0.8. | The ignore entry blocks a valid upgrade. | The YAML comment names the removal condition. A separate change removes the entry. |
| R-03: PR #4888 stays open and failing (U-02). | Red checks remain in the pull request list. | Decision D-3. T-MERGE records the state. No manual close occurs. |
| R-04: The Ruff (lint) check finds rule violations once the install passes (U-03). | The fix pull request shows a lint failure. | `main` passed the job (RV-29). A new finding opens a new issue under the error pipeline. |
| R-05: OneDrive file locks block a branch switch. | `git checkout` fails in the repository path. | Use a worktree outside the repository path (RV-56). |
| R-06: The record fails a process guard (U-06). | A CI shard fails on the fix pull request. | T005 runs the Full tests shard before the fix pull request opens. |

Caution: a broad ignore entry hides future security updates for mando. The entry allows patch updates (FR-003).

## Rollback Steps

1. Before the merge, remove the fix commit from the fix branch with a revert commit, or close the fix pull request. Do not close PR #4888.
2. After the merge, make a new branch from `main`. Revert the entry in a new pull request that names a new issue.
3. Effect: without the entry, the weekly pip stream can propose mando 0.8.x again. The Ruff (lint) check fails for such a pull request, as it did for PR #4888 (RV-04, run 45064243269).
