# Implementation Plan: Preserve Pending Work Before Branch Cleanup

**Branch**: `chore/4822-preserve-pending-work` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record folder

**Input**: Numeric record route `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/`. The route follows the eight-level base-5 rule. See `design/research.md` R11.

## Summary

The owner reports that most preservation steps for issue #4822 already ran. This record verifies each claim or marks it open. It defines the remaining removal steps and their gates. The change adds documentation only. It adds no product code and no dependency change.

## Technical Context

**Language/Version**: Not applicable. The work uses Git, the GitHub CLI, PowerShell, and existing tests.

**Primary Dependencies**: Git for local reads. The GitHub CLI for read-only checks. `ste-linter` for the writing gate. pytest from the existing `.venv`.

**Storage**: Git refs in the local repository. Private archives and one bundle in the private recovery store, outside Git.

**Testing**: Read-only commands in `design/quickstart.md`. The guard tests named in FR-015. The focused offline tests named in TST-018.

**Target Platform**: Windows 11. The worktrees sit in cloud-synced folders.

**Project Type**: Process record. No product code changes.

**Performance Goals**: Not applicable. The change touches no runtime path.

**Constraints**: The main checkout stays unchanged. Nothing is pushed. File permissions stay unchanged. Ignored output is archived before removal.

**Scale/Scope**: Nine snapshots, four recovery branches, 34 registrations, two prunable admin directories, 330 local branches, and 84 remote checks against main at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule | Pass | The record adds one folder under the managed route. The feature root holds five children. `design/` holds four children. |
| Principle II, class-based architecture | Pass | The change has no code. |
| Principle III, safety first | Pass | Each removal needs a dry run, a verified copy, and an owner approval in the issue. |
| Principle IV, full deployment pipeline | Pass | Steps 1 to 9 apply to the record change. Steps 10 to 12 do not apply because no product file changes. |
| Principle V, observability | Pass | The record and the quickstart commands use ASCII output. |
| Principle VI, inline comments | Pass | The change has no code. |
| Principle VII, action logging | Pass | The change has no code. Each quickstart command prints its counts. |
| Mist REST transport | Pass | The process makes no Mist REST call. |
| Podman runtime | Pass | The process starts no container. |
| Test containers | Pass | The process starts no container. |
| File paths | Pass | The commands use literal paths or `Join-Path`. |
| Data directory | Pass | The change has no product output. Archives stay in the private recovery store. Exported test trees use the git-ignored `test-artifacts/` folder. |
| Changelog fragments | Pass | The change has no user-visible effect. `changelog.d/README.md` line 58 asks for no fragment in this case. |
| Spec escalation | Pass | The work includes destructive steps, so a specification is required. |
| Issue first | Pass | Issue #4822 exists. It must carry the `in-progress` label before the branch exists. |
| Branch name | Pass | `chore/4822-preserve-pending-work` targets main directly. |
| Labels | Pass | Issue #4822 has the type label `chore` and the scope label `tests`. |
| Pull request body | Pass | The body holds `Closes #4822`, the gate results, the changed files, and the rollback notes. |

## Architecture

The process has five stages. Each stage reads evidence before the next stage runs.

1. Inventory. List the snapshot tags, the recovery branches, and the registrations.
2. Verify copies. Check the archives, the bundle, and the Labs comparison.
3. Preserve ignored output. Archive it before any worktree folder removal.
4. Decide. Keep each unique branch. Remove only merged branches with verified copies.
5. Report. Post the blockers and the recovery identifiers on the issue.

Git and GitHub hold identifiers and counts only. The private recovery store holds the archives, the bundle, and the ignored output.

## File-by-File Change Map

| Exact repository path | Action | Purpose |
| - | - | - |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/spec.md` | Add | Requirements, user stories, and success criteria |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/plan.md` | Add | Context, constitution check, architecture, and rollback |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/tasks.md` | Add | Ordered tasks, gates, and test cases |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/analysis.md` | Add | Consistency review, findings, and blockers |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/research.md` | Add | Decisions, remote checks, local evidence, and unverified items |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/data-model.md` | Add | Entities, natural keys, and state transitions |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/quickstart.md` | Add | Read-only reproduction and verification commands |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/checklists/requirements.md` | Add | Specification quality checklist |
| `specs/numbered/0/0/1/2/3/2/4/2/4822-preserve-pending-work/design/checklists/recovery.md` | Add | Preservation and removal checklist |

No repository file is modified or deleted. The `design/contracts/` folder is omitted because no contract applies. See the next section.

Local Git changes are not repository files. They are listed in `tasks.md` and in `design/data-model.md`:

- Snapshot tags under `refs/tags/recovery/4822/` stay unchanged.
- Two merged branch refs are delete candidates in T011.
- Two admin directories under `.git\worktrees\` are prune candidates in T010.

## Contracts

The `design/contracts/` folder is omitted. No CLI, menu, API, or file-format contract applies to this record. The existing `worktree-cleanup` command stays unchanged.

## Dependencies

- No Python package changes. `requirements.txt` and `uv.lock` stay unchanged.
- Tools in use: `git`, the GitHub CLI for read-only checks, PowerShell, `ste-linter`, and pytest from `.venv`.
- The writing gate command appears in `.github/copilot-instructions.md` line 74 and in `documentation/quality-gates.md` line 283.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| Local-only copies are lost to a disk fault or Git garbage collection | Warning: Unique pending changes are lost. | Private archives and the bundle. No deletion before verification. Publication waits for FR-009. |
| The devtools cleanup removes ignored output | Warning: Logs, reports, and coverage data are lost. | Archive ignored output first (FR-004). Do not run `worktree-cleanup merged --apply` on these worktrees. |
| Force deletion removes unmerged commits | Warning: Branch commits become unreachable. | Use `git branch -d` only (FR-008). Never pass `--delete-branch` to the devtools command. |
| Windows locks an admin directory | Caution: Cleanup stays partial until the lock clears. | Close the app sessions first. Do not change permissions (FR-016, FR-017). Report the blocker. |
| The closing keyword closes issue #4822 at merge | Caution: The blocker report leaves the open issue list. | Create a blocker issue before T-MERGE (D-9). |
| Publication exposes operational data | Warning: Private data becomes public in a public repository. | Hold publication until a secret review and owner approval (D-2). |
| A snapshot restores `.specify/feature.json` | Caution: The Spec Kit feature state changes. | Exclude this file from every restore (D-14). |
| Recovery branches drift further from main | Caution: A later merge needs more conflict work. | Keep the commit identifiers. Do not rebase in this issue (D-8). |

## Rollback Steps

1. Record change. Open a revert pull request for the record merge commit. No product file changes.
2. Merged branch deleted in error. Run `git branch feat/4631-offline-jvd-preview 02d7d1798d9d5ab17d9de33da122d0b224adaf64`. For the agents branch, use tip `d29cfd3984bcd00074d7b73c6d786be9edce249c`.
3. Worktree folder removed in error. Restore the folder from its archive. Then run `git worktree repair` with the restored folder path.
4. Recovery branch deleted in error. Run `git branch` with the branch name and its commit from the table in `design/research.md`.
5. Snapshot tag or recovery branch published in error. Delete the remote ref. Then record the reason in the issue.
