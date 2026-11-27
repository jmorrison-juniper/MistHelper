# Implementation Plan: Merge queue rollout and acceptance

**Branch**: `docs/3071-merge-queue-rollout` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/spec.md`. The route check uses base 5. The number 3071 equals 44241 in base 5. Padded to eight digits, it gives 0 0 0 4 4 2 4 1, which matches the route.

## Summary

The preparation merged on `main` as PR #4362. The `merge_group` triggers and the guard contracts exist on `main`. This change records the current rollout state. It corrects the stale workflow table, documents the owner gate, adds one guard method, and adds one release-note fragment. It changes no workflow file and no repository setting. Owner activation and two verified queued merges stay outside this change.

## Technical Context

- **Language/Version**: Python 3.15 or newer, from `pyproject.toml` line 23. GitHub Actions YAML, with no change.
- **Primary Dependencies**: pytest and PyYAML in the existing guard module. `ste-linter` and `markdown-link-check` for the documentation gates.
- **Storage**: None.
- **Testing**: One new guard method in `tests/guardrails/test_ci_gate_triggers.py`. Existing guard modules run without change.
- **Target Platform**: GitHub Actions on `main`. Windows, macOS, or Linux for local gates.
- **Project Type**: Repository configuration and documentation.
- **Performance Goals**: No change to runner minutes, because no workflow file changes.
- **Constraints**: Strict protection stays on. The 15 required context names stay unchanged. No repository setting changes in this change.
- **Scale/Scope**: Two required-context workflows and 15 required contexts. Three repository files change, plus one fragment and nine record files.

## Constitution Check

Each rule of the constitution version 1.9.0 has a result. The rule text is at `.specify/memory/constitution.md`.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The record folder holds five children. `changelog.d` holds 335 entries and `tests/guardrails` holds many files. Both are grandfathered debt. The change adds one fragment, which the constitution allows as a unique record. The guard module gets no new top-level name. |
| II. Class-based architecture | Pass | The new guard method joins the existing class `TestPullRequestTrigger`. No wrapper function is added. |
| III. Safety-first | Pass | The change touches no keyboard input, no destructive operation, and no production device. Owner activation stays a separate gated step. |
| IV. Full deployment pipeline | Pass with steps | The tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. The main image build starts only for product file changes, as the `container-build.yml` row of `.github/copilot-instructions.md` line 473 states. This change changes no product file, so the image build does not start. |
| V. Observability and logging | Pass | The new test writes ASCII output only. The test prints the count of examined items, as the module does. |
| VI. Inline comments | Pass with condition | Each new line of the test method carries an inline comment in the same style as the module. |
| VII. Action logging | Pass with condition | The new test prints the examined count, as the module does. Documentation needs no action logging. |
| Technology constraints | Pass | Python 3.15 is the target. The change adds no Mist call, no container, no dependency, no path code, and no product output. |
| Development workflow: menu operations | Not applicable | No menu operation changes. |
| Development workflow: release notes | Pass with decision | The change adds one fragment (decision D-6). `CHANGELOG.md` stays unchanged. |
| Escalation to SpecKit | Pass | The change touches more than three files, so a specification exists. |
| Multi-agent git workflow | Pass | Issue #3071 is open and carries `in-progress`. The branch name carries the issue number. No open pull request changes a target file (R-58). |
| Pull request checklist: Closes keyword | Fail with accepted deviation | The constitution requires the Closes keyword with the issue number in each pull request body (R-40). This pull request uses `Refs #3071` (decision D-5), because operational acceptance is incomplete and the owner requires the issue to stay open. The coordinator must accept the deviation. The pull request body states the reason. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      workflows.md
    checklists/
      requirements.md
```

### Source Code (repository root)

No product source changes. The file change map below lists every changed file.

## Architecture

The rollout has four stages.

1. **Preparation (complete)**. `ci.yml` and `codeql.yml` declare `merge_group`. The guard contracts exist. The serial merge slot is active. PR #4362 merged this stage.
2. **Documentation (this change)**. The workflow table names the queue candidates. The procedure states the current state. The guard method fails on drift. One fragment is added.
3. **Owner activation (outside this change)**. The owner confirms the review rule. The owner enables the merge queue with strict protection and the 15 required contexts unchanged. The owner sets batch size one and a finite status check timeout.
4. **Verification and retirement (outside this change)**. The owner verifies two verification candidates. The owner records the evidence on issue #3071. A later documentation change retires the serial merge slot text.

## File-by-File Change Map

| Path | Action | Change | Requirements |
| - | - | - | - |
| `.github/copilot-instructions.md` | Modify | Rows 467 and 468 of the workflow table name merge queue candidates for `ci.yml` and `codeql.yml`. | FR-006 |
| `documentation/quality-gates.md` | Modify | Under the heading `## Merge queue preparation and activation` (line 92), state the preparation as complete (PR #4362, merge commit `00633cad3a544190a1fbf4fd1999308e91b90c4a`). Add the review rule step and the batch size step to the owner verification steps. Add a `### Constraints` subsection. Keep the heading text unchanged. | FR-007, FR-013, FR-014 |
| `tests/guardrails/test_ci_gate_triggers.py` | Modify | Add one method named `test_queue_docs_name_each_queue_workflow` to `TestPullRequestTrigger`, after line 146. The method reads the two table rows and the procedure heading. | FR-008 |
| `changelog.d/issue-3071-merge-queue-rollout.md` | Add | One fragment with one heading and one `Changed` bullet that names issue #3071. | Constitution release-note rule (R-65) |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/spec.md` | Modify | Revised specification. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/plan.md` | Modify | Revised plan. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/tasks.md` | Modify | Revised tasks. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/analysis.md` | Modify | Revised analysis. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/research.md` | Modify | Decisions, remote verification table, legacy verification table, sources, and unverified items. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/data-model.md` | Modify | Entities and state transitions. | FR-003, FR-012 |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/quickstart.md` | Modify | Read-only checks, local gates, and owner verification commands. | All |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/contracts/workflows.md` | Modify | Trigger and concurrency contract. | FR-001 to FR-005 |
| `specs/numbered/0/0/0/4/4/2/4/1/3071-merge-queue-support/design/checklists/requirements.md` | Modify | Specification quality checklist. | All |

Not changed: every file under `.github/workflows/`, `AGENTS.md`, `documentation/contributing.md`, `.ste-linter.toml`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `CHANGELOG.md`, and every product file. The path `.github/instructions/git-flow-multi-agent.instructions.md` is not created (decision D-4).

## Dependencies

- **Runtime**: None added.
- **Verification tools**: pytest, ruff, black, bandit, radon with `complexity-gate`, `symbol-diff`, `ste-linter`, `markdown-link-check`, and `test-quality-analyzer`. The repository development requirements supply them, as `.github/copilot-instructions.md` lists.
- **GitHub access**: `gh` for read calls and for the pull request. No write call changes a setting.
- **External documentation**: The public `github/docs` repository, read through the GitHub API (references R-61 to R-64).

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The owner activates the merge queue before `merge_group` reaches `main`. | Every merge waits. Warning: required checks can stay absent and prevent every merge. | `merge_group` already reaches `main` (R-01, R-10). Owner step O-2 checks `main` before activation. |
| The three review rule reads conflict (R-53). | A merge might need an approval, or might not. | Owner step O-1 confirms the rule before activation (FR-014). |
| The `CodeQL` context does not report on a queue commit. | The queue stalls on that candidate. | The owner records the result. The owner disables the queue rule if the context stays absent. Caution: the recovery keeps strict protection. |
| `ste-lint.yml` becomes a required context later. | The queue stalls on a context without `merge_group`. | The constraint text in `documentation/quality-gates.md` requires the trigger first (decision D-3). |
| The shared auto-merge workflow behaves differently under the queue (unverified, U-2). | A labeled pull request might not enter the queue. | Verification candidates enter the queue by hand first (FR-013). The `auto-merge` label waits for the evidence. |
| Documentation drifts again. | A contributor follows a wrong trigger list. | The guard method fails on drift (FR-008). |
| The constitution `Closes` rule conflicts with `Refs #3071`. | The coordinator may reject the pull request. | Decision D-5 gives the reason in the pull request body. The coordinator decides. |
| The new test changes the test quality ratchet. | The ratchet gate fails. | T-LOCAL-GATES runs the ratchet commands. The baseline stays unchanged. |

## Rollback Steps

1. For this change, revert the squash commit through a new pull request. Do not force-push `main`.
2. For owner activation, disable the "Require merge queue" setting on `main`. Keep strict protection and the 15 required contexts. Return to the serial merge slot. Check each queued pull request after the change.
3. For a workflow trigger defect, revert only the trigger change in a new pull request. Do this only while the queue stays inactive.

## Rollout Owner Steps

These steps are not numbered tasks, because an agent cannot run them. Each step needs owner action or owner approval.

- **O-1**: Confirm the review rule with the three reads in `design/quickstart.md`. Record the result on issue #3071.
- **O-2**: Confirm that `ci.yml` and `codeql.yml` on `main` declare `merge_group`. Use the blob checks in `design/quickstart.md`.
- **O-3**: Approve owner activation. Enable "Require merge queue" on `main`. Keep strict protection and the 15 required contexts unchanged. Set the merge limits to a minimum of one and a maximum of one. Set the status check timeout to 60 minutes (decision D-8).
- **O-4**: Add the first verification candidate to the merge queue by hand. Record the queue commit SHA, the result of each required context, the merge commit, and the main run ID on issue #3071.
- **O-5**: Repeat O-4 with a second verification candidate.
- **O-6**: After both candidates succeed, approve a documentation pull request that retires the serial merge slot text in `.github/copilot-instructions.md` and `documentation/quality-gates.md`.
- **O-7**: Close issue #3071 after the evidence from O-4 and O-5 is on the issue.

## Validation

The tasks in `tasks.md` define the local and remote gates. Each applicable gate from the local gates table of `.github/copilot-instructions.md` runs in T-LOCAL-GATES. Each gate that does not apply names its reason in T-LOCAL-GATES.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| The pull request body uses `Refs #3071`, not `Closes #3071` (constitution rule R-40). | The owner requires issue #3071 to stay open until acceptance evidence exists. | `Closes #3071` closes the operational issue before the evidence exists, and it breaks the owner instruction in the issue thread. |
