# Implementation Plan: Pin the verified auto-merge commit

**Branch**: `fix/4906-auto-merge-verified-pin` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record omits `design/contracts/`, because no interface contract applies. The change alters one workflow value and one test constant. It exposes no menu, command, output, or API shape.

## Summary

Move the auto-merge verified commit from `d63a120487cecf750184cb178387cdc25c0a7635` to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Change the pin in `.github/workflows/auto-merge.yml` and the constant in `tests/guardrails/test_auto_merge_issue_close.py` in one commit. The reusable workflow blob SHA is `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` at both commits. The merge-recovery behavior stays the same.

## Technical Context

**Language/Version**: Python 3.15. The repository requires Python 3.15 or newer, and CI sets `PYTHON_VERSION` to 3.15.

**Primary Dependencies**: pytest and PyYAML. The guard file imports both. `requirements-dev.txt` installs both in CI.

**Storage**: Not applicable. The change reads two YAML files and writes no data.

**Testing**: pytest. The targeted command is `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`.

**Target Platform**: GitHub Actions on `ubuntu-latest` for CI. Windows 11, macOS, and Linux for local runs.

**Project Type**: Repository CI configuration with one guard test. The change adds no product code.

**Performance Goals**: Not applicable. The guard reads two files in milliseconds.

**Constraints**: Lines stay 120 columns or fewer (`pyproject.toml` line 202). The pin and the verified commit stay full 40-character SHAs (`FULL_COMMIT` at line 45 of the guard file).

**Scale/Scope**: Two changed lines in two files, plus one record folder.

## Constitution Check

*Gate result: pass before research. Re-checked after design: pass.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The route parents `0/0/1/2` and `0/0/1/2/4` already hold the digits that this record uses, so `0/0/1/2` keeps five children. The change adds one child under `4/1`, which then holds two children. It creates `4/1/1` and `4/1/1/1`, each with one child. No direct entry is added to `specs/`. Existing debt: `specs/` holds 795 direct entries on main. Of these, 792 are grandfathered legacy entries in `tests/guardrails/process_folder_baseline.json`, and three are managed roots (`live`, `numbered`, and `skills`). Remediation is tracked as item U-3 in `analysis.md`. |
| II. Class-based architecture | Pass | The change adds no function and no class. It edits one constant and one workflow value. |
| III. Safety-first | Pass | The change adds no input handling and no destructive operation. The auto-merge job scopes stay `actions`, `contents`, and `pull-requests` with write access. The guard test `test_the_job_grants_each_scope_of_the_shared_jobs` checks those scopes. No secret enters the change. |
| IV. Full deployment pipeline | Pass with a recorded exception | Steps 1 to 9 apply: local gates, Conventional Commit title, rebase, push, pull request, CI, and squash merge. Steps 10 to 12 do not apply. The change edits no product file, and it adds no changelog fragment. The `container-build.yml` row in `.github/copilot-instructions.md` line 473 names a push that changes a product file. |
| V. Observability and logging | Pass | The change adds no runtime code and no log statement. The added comments use ASCII only. |
| VI. Inline comments | Pass | The edited constant line gets an inline comment. The two comment lines above it explain the evidence. The workflow line keeps its existing comment. |
| VII. Action logging | Pass | The change adds no action. The guard file performs no runtime action that needs a log. |
| Technology: mistapi | Not applicable | The change makes no Mist API request. |
| Technology: UV, Podman, Zscaler | Not applicable | No dependency, container, or registry push changes. |
| Technology: file paths | Pass | The record uses repository-relative paths only. |
| Technology: output backends, operational store, database keys, data directory | Not applicable | The change writes no product output and no operational record. |
| Development workflow: menu operations and README | Not applicable | No menu operation changes, so the README stays unchanged. |
| Development workflow: security findings | Pass | Bandit runs over the guard file. The change adds no suppression comment. |
| Release notes | Pass | `changelog.d/README.md` rule 4 at line 58 allows no fragment for an internal-only change. The pull request body states the reason. |
| SpecKit escalation | Pass | The change touches two files and one record. This record is the specification written before the change. |
| Multi-agent git workflow | Pass | Issue 4906 exists and receives the `in-progress` label. The branch `fix/4906-auto-merge-verified-pin` starts from main. The pull request title uses Conventional Commits. The Dependabot branch receives no push. |

## Architecture

The auto-merge job in `.github/workflows/auto-merge.yml` calls the reusable workflow in `jmorrison-juniper/misthelper-devtools` at one full commit SHA. The pin is line 61. The guard file parses the same workflow with PyYAML. It builds an expected value from the verified commit constant at line 46 and compares the value at line 145. The `root-and-contracts` shard runs `tests/guardrails` at `.github/workflows/ci.yml` line 255. The shard step is at line 304. The coverage gate job `pytest` fails when any shard fails, at line 356.

## File-by-File Change Map

| Path | Action | Lines | Reason |
| - | - | - | - |
| `.github/workflows/auto-merge.yml` | Modify | 61 | Change the pin to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Keep the existing comment `# Verified post-merge dispatch`. |
| `tests/guardrails/test_auto_merge_issue_close.py` | Modify | 44 to 46 | Change the verified commit constant to the same commit. Add two comment lines above it and one inline comment on it. |
| `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/` | Add | New folder | Add this record. Its files are `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/checklists/requirements.md`, and `design/checklists/security.md`. |

No file is deleted. The changelog, the documentation, and the requirements files stay unchanged.

## Dependencies

- No new package is added. The guard file uses pytest and PyYAML, and the CI install log lists both packages.
- The change depends on the reusable workflow at `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Its blob SHA matches the verified blob (rows R-14 and R-15).
- The change depends on the record guards in `tests/guardrails/` (TP-18 to TP-20).
- The replacement pull request depends on no other open pull request.

## Test Plan

The plan names 20 test functions. A parametrized test counts once. The 17 tests in the guard file run in file order.

| ID | Test | File | Purpose |
| - | - | - | - |
| TP-01 | `TestAutoMergeWorkflowTriggers::test_closed_event_starts_the_workflow` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the closed event trigger. |
| TP-02 | `TestAutoMergeWorkflowTriggers::test_existing_merge_events_survive` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the merge event triggers. |
| TP-03 | `TestAutoMergeWorkflowTriggers::test_a_branch_push_starts_the_orphan_report` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the push trigger and the report request. |
| TP-04 | `TestAutoMergeWorkflowTriggers::test_the_schedule_backstop_survives` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the schedule and the manual start. |
| TP-05 | `TestAutoMergeWorkflowTriggers::test_workflow_grants_no_blanket_permission` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the empty top-level permissions. |
| TP-06 | `TestAutoMergeJob::test_the_job_calls_the_shared_workflow` | `tests/guardrails/test_auto_merge_issue_close.py` | Check the shared call and the full-SHA pattern. |
| TP-07 | `TestAutoMergeJob::test_merge_recovery_uses_the_verified_shared_commit` | `tests/guardrails/test_auto_merge_issue_close.py` | Check the pin against the verified commit. This is the failing test. |
| TP-08 | `TestAutoMergeJob::test_the_job_grants_each_scope_of_the_shared_jobs` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the job scopes. |
| TP-09 | `TestAutoMergeJob::test_each_main_workflow_accepts_a_dispatch` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the main workflow list. |
| TP-10 | `TestCloseLinkedIssuesJob::test_close_job_calls_the_shared_workflow` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the close job call. |
| TP-11 | `TestCloseLinkedIssuesJob::test_workflow_can_close_an_issue` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the issue scope. |
| TP-12 | `TestCloseLinkedIssuesJob::test_close_job_accepts_only_a_real_pull_request_merge` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the merge condition. |
| TP-13 | `TestCloseLinkedIssuesJob::test_close_job_allows_the_schedule_backstop` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the schedule path. |
| TP-14 | `TestCloseLinkedIssuesWorkflow::test_a_merge_and_a_schedule_start_the_workflow` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the close workflow triggers. |
| TP-15 | `TestCloseLinkedIssuesWorkflow::test_the_job_calls_the_shared_workflow` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the close workflow call. |
| TP-16 | `TestCloseLinkedIssuesWorkflow::test_the_job_skips_a_pull_request_that_did_not_merge` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the merge condition in the close workflow. |
| TP-17 | `TestCloseLinkedIssuesWorkflow::test_the_job_can_close_an_issue` | `tests/guardrails/test_auto_merge_issue_close.py` | Keep the close workflow scopes. |
| TP-18 | `test_specs_structure_matches_baseline` | `tests/guardrails/test_process_folder_structure.py` | Confirm the record adds no invalid direct child under `specs/`. |
| TP-19 | `test_numeric_feature_route_remains_stable` | `tests/guardrails/test_spec_route_contract.py` | Confirm the numbered route for issue 4906. |
| TP-20 | `test_feature_branch_that_edits_no_changelog_passes` | `tests/guardrails/test_changelog_fragment_policy.py` | Confirm the changelog policy accepts a feature branch without a changelog edit. |

TP-19 uses PowerShell. Run it where `pwsh` is available. CI runs it in the `root-and-contracts` shard.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The reusable workflow changes at the new commit. | The blob SHA check (rows R-14 to R-16 in `design/research.md`) and the full-SHA pin. |
| The guard checks equality only, so a harmful upstream commit passes. | Review the blob SHA before the change. Record the evidence in the guard file comment (decision D-9). Analysis item A-4 records this limit. |
| Main moves before the merge. | Rebase, then rerun the guard file (T004 and T-PR). |
| Dependabot opens a second update. | Apply the same rule: change the pin and the verified commit in one commit. |
| The record lands outside the route or breaks the five-child rule. | Run the route guard and the process folder guard (T005). |
| A CI check fails for a cause outside this change. | Read the failed job log. Track each unrelated cause in a separate issue (T-REMOTE-CI). |

## Rollback Steps

1. Revert the replacement pull request as one commit on a new branch from main.
2. Confirm that the pin and the verified commit both name `d63a120487cecf750184cb178387cdc25c0a7635`.
3. Rerun `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`. Expect 17 passed.
4. Reopen pull request 4886 only when the orchestrator authorizes the reopen.

Caution: a revert that changes one line alone makes the guard fail on main. Revert both lines in one commit.

Warning: never force push to main. A force push rewrites shared history and can remove commits that other agents need.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/
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
      security.md
```

### Source Code (repository root)

```text
.github/workflows/auto-merge.yml                  (modify line 61)
tests/guardrails/test_auto_merge_issue_close.py   (modify lines 44 to 46)
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing debt: `specs/` holds 795 direct entries on main, and 792 legacy entries are grandfathered | The baseline in `tests/guardrails/process_folder_baseline.json` records the legacy entries. | This change does not touch the root. Reducing the root needs a separate remediation issue (U-3 in `analysis.md`). |
