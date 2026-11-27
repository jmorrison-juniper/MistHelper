# Implementation Plan: Stranded branch pull request coverage

**Branch**: `docs/4818-stranded-branch-pr-coverage` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\spec.md`

**Input**: Numeric record from the route `specs\numbered\0\0\1\2\3\2\3\3`, computed from issue 4818 (research.md R6).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design\`.

## Summary

The replica names 537 stranded branches on 2026-11-26 (RC-049). Each branch holds commits above `main` and has no pull request that keeps its head. This plan gives each named branch one draft pull request. The plan adds no code, no workflow, and no test. The rollout runs in four phases: evidence, record, pilot, and batches. The owner approves the volume before the batches start (D-12).

## Technical Context

**Language/Version**: Not applicable. The change adds Markdown records and one changelog fragment.

**Primary Dependencies**: `gh` for GitHub reads and writes. `git` for read-only evidence. `misthelper-devtools` 0.6.4 for the report command (RC-045). `ste-linter`, `pytest`, and `pwsh` for the local gates.

**Storage**: GitHub branches, pull requests, and issues. No local data store.

**Testing**: The Markdown gate, the folder guard, the route guard, and the changelog guard for the record. The report command and the replica for the rollout.

**Target Platform**: GitHub `jmorrison-juniper/MistHelper`. The operator runs PowerShell on Windows 11.

**Project Type**: Repository process record. No product code changes.

**Performance Goals**: Ten draft pull requests per batch. A batch completes its check runs before the next batch starts (FR-007).

**Constraints**: 80 content-generating requests per minute and 500 per hour (S-2). No branch deletion (FR-004). No push to a local-only branch (FR-015). The repository is public (RC-050).

**Scale/Scope**: 537 stranded branches. 1,720 commits above `main` in total (research.md R2). 526 distinct head commits.

## Constitution Check

Each rule has a verdict and a reason. The constitution is `.specify\memory\constitution.md` (RC-007, RC-008, RC-113).

| Rule | Verdict | Reason |
| - | - | - |
| I. Five-item rule | Pass | The feature root holds five children. The `design\` folder holds five children. `design\contracts` holds one file. `design\checklists` holds two files. The route parents hold no children before this record (RC-034). |
| I. Managed roots for numbered records | Pass | The route starts at `specs\numbered`, a managed root (RC-007). The leaf holds no entry before this record (RC-034). |
| II. Class-based architecture | Not applicable | No code changes. |
| III. Safety first | Pass | The rollout deletes no branch and runs no destructive operation (FR-004). The owner approves the volume (FR-020). |
| IV. Full deployment pipeline | Pass | The record goes through local gates, explicit staging of eleven files, a Conventional Commit, a rebase on `origin/main`, a push of a new branch, a pull request, CI, and a squash merge (T-LOCAL-GATES to T-MERGE). No workflow pushes to `main` (RC-008). |
| IV. Container build after merge | Pass | The container build workflow starts only for product file changes (RC-114). The record changes no product file, so steps 10 to 12 of the pipeline do not apply. |
| Escalation to Spec Kit | Pass | The change touches more than three files and needs a specification (RC-115). This record provides it. |
| V. Observability and logging | Not applicable | No code and no log output. |
| VI. Inline comments | Not applicable | No code. |
| VII. Action logging | Not applicable | No code. |
| Technology: mistapi | Not applicable | The record calls no Mist endpoint. |
| Technology: container runtime | Not applicable | No container starts. |
| Technology: file paths | Pass | The record names paths with backslashes for the Windows operator. The quickstart uses PowerShell. |
| Documentation: changelog fragment | Pass | One fragment is added (D-8, RC-113). |
| Documentation: README | Not applicable | No operation count or menu row changes. |
| Escalation to Spec Kit | Pass | The change touches more than three files and needs a specification (RC-115). This record provides it. |
| Multi-agent git: issue first | Pass | Issue 4818 exists and carries the `in-progress` label (RC-004). |
| Multi-agent git: one concern per pull request | Pass | The record pull request changes the record and one fragment only. Each preservation pull request holds no code change. |
| Multi-agent git: closing keyword | Pass with a recorded deviation | The record pull request uses `Refs #4818`. D-8 records the reason. |

## Architecture

The process has five steps. Each step reads the live state before it writes.

```text
Live report (replica) -> Pilot (5) -> Stop rule -> Owner approval -> Batches (10) -> Ledger comments
                                                                             |
                                             Report exit 0 -> Owner closes trackers
```

- **Live report**: The report, or the replica, lists the stranded names in oldest-head order (FR-019).
- **Pilot**: Five draft pull requests open first. The pilot records the gate issue count (FR-006, SC-005).
- **Stop rule**: The rollout stops when a branch head differs from the recorded head, or when a retry fails three times (FR-008).
- **Owner approval**: The owner approves the volume in a tracker comment (FR-020, D-12).
- **Batches**: Each batch opens up to ten draft pull requests. Each batch finishes its check runs before the next batch starts (FR-007).
- **Ledger comments**: Each pilot and batch adds one new comment to the tracker (FR-010).

## Pilot Scope

The pilot uses the five oldest stranded heads (FR-019). The replica produced these rows on 2026-11-26.

| Order | Branch | Head commit | Last commit |
| - | - | - | - |
| 1 | `archive/laptop-20261121/preservation/2746-pr3011-turn0` | 560f0eff3134dcb6fb08acaee85a5146597d6147 | 2026-09-19T02:17:25Z |
| 2 | `archive/laptop-20261121/refactor/2926-portal-handlers-c` | 21d2d65598d8d6f75684b3c4dc02bb22f35df855 | 2026-09-20T00:52:47Z |
| 3 | `archive/laptop-20261121/fix/2746-fm-http-status` | 94cc4e17db403ff6a70a985f9897e4857f34e7f1 | 2026-09-20T12:52:41Z |
| 4 | `archive/laptop-20261121/test/3164-harness-controls` | 2569a15adb7c98b8a6127d7268248b4cdc264722 | 2026-09-22T09:33:48Z |
| 5 | `fix/3158-wip-controls` | 0f6b375e71243311b5cf5856fe9f220842a14e3b | 2026-09-28T21:33:52Z |

The pilot list is a snapshot. Task T004 rebuilds it before the pilot starts.

## Preservation Pull Request Shape

The shape is in `design\contracts\preservation-pull-request.md`. The key fields are:

- Base `main`, head the existing branch, draft state on.
- Title `chore(git): preserve the head of` followed by the branch name. The title passes the title check (RC-112).
- Body with `Refs #4818` and no closing keyword.
- Labels `chore` and `ci` (RC-117 shows both labels on the tracker).
- No auto-merge label. No review request. No new commit.

## File-by-File Change Map

| Path | Action | Purpose |
| - | - | - |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\spec.md` | Add | User stories, requirements, success criteria, and clarifications |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\plan.md` | Add | This plan |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\tasks.md` | Add | Ordered tasks with verification commands |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\analysis.md` | Add | Consistency review and defects |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\research.md` | Add | Evidence, decisions, remote checks, and unverified items |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\data-model.md` | Add | Entities, keys, and state transitions |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\quickstart.md` | Add | Reproduction steps and verification commands |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\contracts\preservation-pull-request.md` | Add | Interface contract for each pull request and ledger comment |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\checklists\requirements.md` | Add | Specification quality checklist |
| `specs\numbered\0\0\1\2\3\2\3\3\4818-stranded-branch-pr-coverage\design\checklists\rollout.md` | Add | Rollout readiness checklist |
| `changelog.d\issue-4818-stranded-branch-pr-coverage.md` | Add | One changelog fragment (D-8) |

No other repository path changes. Workflows, guard tests, `requirements-dev.txt`, `documentation\`, and `.specify\` stay unchanged (FR-016).

## Dependencies

- `gh` authenticated as `jmorrison-juniper` for each read and write.
- `git` with the local objects for `main` and each stranded branch. The commands in quickstart.md read objects only.
- `misthelper-devtools` 0.6.4 in `.venv`. It supplies the report command (RC-045).
- `ste-linter` with `.ste-linter.toml` at the repository root. The Markdown gate uses it (RC-116).
- `pytest` and `pwsh`. The route guard requires `pwsh` for its executable checks (RC-026).

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| R-1 | 537 draft pull requests start 537 Quality Gates runs | Pilot first (T005 to T009). Batches of ten. Owner approval (T010, D-12). |
| R-2 | Failed gates open quality-gate issues per pull request | The pilot counts them (T007). The owner closes each issue after the disposition. Stop rule. Eighteen such issues are open today (RC-051). |
| R-3 | Content-creation limits block a burst | Pace requests. Wait and retry after a secondary response (FR-008, S-2). |
| R-4 | The scope grows during the rollout | Rerun the replica before each batch (T011). |
| R-5 | A branch head moves during the rollout | Compare each head with the recorded head after each batch (T008, T013). |
| R-6 | A closing keyword closes the tracker | Body contract with `Refs` only. Check on every pull request (T017). |
| R-7 | A preservation pull request merges by mistake | No auto-merge label. No review request. Check the labels (T013). |
| R-8 | Four duplicate trackers stay open | The owner closes them after the report is clean (T019). |
| R-9 | The replica and the report disagree | The report is the authority. The final report run decides (T016). |
| R-10 | A local-only branch reaches the remote | No push rule (FR-015). Check for a 404 on each named local branch (T023). |
| R-11 | The devtools pin drift changes the rule | The installed version is recorded (RC-045). A follow-up issue names the drift (T022). |
| R-12 | The repository becomes private | Each batch checks the visibility (RC-050). A private repository changes the cost analysis. Stop and report. |

## Rollback Steps

1. Stop the rollout. Start no new batch.
2. For each pull request created in error, add a comment that gives the reason. Then close the pull request. A closed pull request keeps its head (RC-043, RC-044).
3. Do not delete any branch during rollback. No branch changed during the rollout.
4. To revert the record, open a new branch from `main`. Revert the squash commit on that branch. Do not push to the merged branch. AGENTS.md (line 235) requires a squash merge and forbids direct pushes to `main`.
5. The revert removes the changelog fragment in the same commit.

Warning: Deleting a branch that has no pull request removes its only copy. Restore the branch from the pull request head before any deletion.

## Complexity Tracking

No violation exists. The record adds no direct child to a noncompliant parent. The route parents hold no children before this record (RC-034).
