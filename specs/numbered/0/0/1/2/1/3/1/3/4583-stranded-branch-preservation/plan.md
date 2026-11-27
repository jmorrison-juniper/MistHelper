# Implementation Plan: Stranded Branch Preservation

**Branch**: `chore/4583-stranded-branch-preservation` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/1/3/1/3/4583-stranded-branch-preservation/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Preserve each in-scope stranded branch with a closed draft pull request. Hold each branch that shares a changed file with an open pull request. Verify that the report names no branch. The record changes no product file.

## Technical Context

- **Language/Version**: Not applicable. The procedure runs in PowerShell with `gh` and `git`.
- **Primary Dependencies**: `gh` for GitHub reads and writes. `git` for read-only ancestry and diff checks. pytest in the repository `.venv` runs the guard tests at execution time.
- **Storage**: GitHub holds all state. The record stores no database.
- **Testing**: Guard tests `tests/guardrails/test_spec_route_contract.py` and `tests/guardrails/test_process_folder_structure.py`. The STE linter checks the style. Nineteen verification checks V-01 to V-19 appear in `design/quickstart.md`.
- **Target Platform**: A Windows 11 host with a checkout of MistHelper. GitHub is the remote.
- **Project Type**: A GitHub operations procedure with a Spec Kit record. No product code.
- **Performance Goals**: Not measured. The procedure waits five seconds between rows.
- **Constraints**: One open preservation pull request at a time. No branch deletion. Backoff on HTTP 403 and 429.
- **Scale/Scope**: 543 in-scope branches at the snapshot. 441 ready and 102 held. Seven open pull requests at the snapshot.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution is version 1.9.0 (R21). Each rule has one result.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | PASS | Each record directory holds five children or fewer. Check V-17 and Q-8 confirm the count. |
| I. Managed roots | PASS | The record sits under `specs/numbered/`, a managed root. No direct child of `specs/` is added. |
| I. Process folder baseline | PASS | The baseline file keeps its 792 legacy entries (R18, R20). This record changes no baseline entry. |
| II. Class-based architecture | PASS | No product code is added. The quickstart script is runbook text, not committed code. |
| III. Safety-first | PASS | No destructive operation is in scope. FR-007 forbids branch deletion, and the close command omits `--delete-branch`. |
| III. Secrets | PASS | The record names only the token variable. Check V-19 scans for token prefixes. |
| IV. Full deployment pipeline | PASS | The record follows local gates, a Conventional Commit, a branch, a pull request, CI, and a squash merge. No product file changes, so the container build does not run. |
| V. Observability | PASS | The procedure logs each write before and after it runs. The record uses ASCII text only. |
| VI. Inline comments | PASS | No product code is added. The quickstart script is documentation text in a Markdown code block. |
| VII. Action logging | PASS | The execution log records the call, the number, and the result for each write. No product code is added. |
| Mist REST transport | PASS | No Mist REST request is in scope. No mistapi method is needed. |
| Package manager and container | PASS | No dependency change. No container starts. |
| File paths | PASS | The record uses repository-relative paths. No code path handling is added. |
| Data directory | PASS | No product output is written. No file goes under `data/`. |
| Output backends, operational store, export boundary | PASS | Not applicable. The feature exports nothing and stores no coordination record. |
| Menu operations | PASS | Not applicable. No menu operation is added. |
| Issue first | PASS | Issue #4583 exists. The `in-progress` label is added at the claim step. |
| File overlap | PASS | Each held branch waits for the open pull request that shares its files (FR-003). |
| MistHelper.py hot file | PASS | The record changes no `MistHelper.py` file. |
| Required labels | PASS | Issue #4583 carries the type label `chore` and the scope label `ci`. |

The post-design check gives the same results. The design adds no product file.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/1/3/1/3/4583-stranded-branch-preservation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      preservation-pull-request.md
    checklists/
      requirements.md
      safety.md
```

### Source Code

No source code changes. The procedure writes pull requests and comments on GitHub only.

## Structure Decision

The record uses the eight-level base-5 route for issue 4583. The helper `Get-SpecRadixSegments` (R15) computes the route `0/0/1/2/1/3/1/3`.

| Directory | Children before | Children after | Limit |
| - | - | - | - |
| `specs/numbered/0/0/1/2/1/3` | 2 (`2`, `3`) | 3 (`1`, `2`, `3`) | 5 |
| `specs/numbered/0/0/1/2/1/3/1` | 0 (new) | 1 (`3`) | 5 |
| `specs/numbered/0/0/1/2/1/3/1/3` | 0 (new) | 1 (the record folder) | 5 |
| Record folder root | 0 (new) | 5 (`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design`) | 5 |
| `design` | 0 (new) | 5 (`research.md`, `data-model.md`, `quickstart.md`, `contracts`, `checklists`) | 5 |

## File Change Map

The paths are relative to the record folder `specs/numbered/0/0/1/2/1/3/1/3/4583-stranded-branch-preservation/`.

| Path | Action | Purpose |
| - | - | - |
| `spec.md` | Add | User stories, requirements, and success criteria |
| `plan.md` | Add | Technical context, constitution check, and structure |
| `tasks.md` | Add | Ordered tasks and the final gates |
| `analysis.md` | Add | Consistency review and unresolved items |
| `design/research.md` | Add | Decisions, branch evidence, and remote checks |
| `design/data-model.md` | Add | Entities, states, and snapshot counts |
| `design/quickstart.md` | Add | Commands and verification checks |
| `design/contracts/preservation-pull-request.md` | Add | Request and proof shapes |
| `design/checklists/requirements.md` | Add | Specification quality checklist |
| `design/checklists/safety.md` | Add | Safety checklist |

Directories added: `specs/numbered/0/0/1/2/1/3/1`, `specs/numbered/0/0/1/2/1/3/1/3`, and the record folder. Files modified: none. Files deleted: none. Branches deleted: none.

## Implementation Outline

1. Record (T007): copy the ten record files to the route on the record branch. Commit them after the local gates pass.
2. Scope (T008 and T009): run Q-1 and Q-2. Record the work order and the holds.
3. Preservation (T010 to T023): run ready batches W01 to W09 in order. Run held groups after each release check.
4. Closure (T024 to T027): run the final scope check, review the log, file the defect issue, and post the summary.
5. Final gates: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Dependencies

- Tools: `gh` authenticated for the repository, `git` for read-only checks, and PowerShell.
- Execution-time tools: pytest in the repository `.venv` for the guard tests, and `ste-linter` for the style check.
- External services: the GitHub API. Blocking pull requests #4208, #4813, #4886, #4887, and #4888 hold branches.
- No package or dependency manifest changes.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| GitHub rate limit | A batch stops early | Pacing and backoff (FR-010). The run resumes at the stopped row. |
| Accidental branch deletion | A branch loses its only copy | The close command omits `--delete-branch`. Check V-10 counts branches. |
| Overlap with an open pull request | Two open pull requests share a file | Q-2 shows the lane before each create (FR-003). |
| Head moves after the snapshot | A preservation names an old head | Check V-06 compares the head before the create and after the close. |
| Scope drift | A new or aged branch is missed | Q-2 reruns before each batch and after the last batch (FR-012, V-11). |
| Failed close | Two open preservation pull requests | The stop rule (FR-010) requires a close before any create. |
| Notification volume | Owners receive many events | Each title names its purpose. Each close carries a proof comment. Batches pause between runs. |
| Emulation differs from the report | The count differs from the report command | Q-2 and the report issue count (V-11, V-15) confirm the result. Analysis UR-7 records the difference. |
| Duplicate report issues remain open | Manual cleanup remains | The separate defect issue (T026) owns the fix. |
| Held groups remain open | Closure waits for the owner | Analysis UR-1 to UR-3 record the dependency. |

## Rollback Steps

1. Reopen a closed preservation pull request with `gh pr reopen` when its review starts. Close it again after the review. No branch changed, so no branch restore is needed.
2. Restore a missing branch from its pull request head with a non-forced push. The quickstart section "Rollback" gives the command.
3. For the record pull request, close it before merge. After a merge, open a new pull request that reverts the merge commit.
4. Stop the run at any failed verification check. Keep the open state, and record the row for review.

## Complexity Tracking

None. The plan needs no violation of a constitution rule.
