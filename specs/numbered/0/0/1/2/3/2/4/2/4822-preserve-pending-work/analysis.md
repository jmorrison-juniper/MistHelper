# Specification Analysis Report: Preserve Pending Work Before Branch Cleanup

This review compares `spec.md`, `plan.md`, `tasks.md`, and the remote evidence in `design/research.md`. It lists each defect and each open item.

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| F-01 | High | Warning: Every recovery copy exists only in this local repository and the private store. | RC-20 to RC-37 in `design/research.md` return absent. | Hold publication (D-2). Report as B-02. |
| F-02 | High | Warning: The devtools dirty check ignores ignored output. | `worktree_cleanup.py` line 228 runs `git status --porcelain`. | Archive ignored output first (FR-004, D-5). |
| F-03 | High | Warning: The devtools delete option force-deletes branches. | `worktree_cleanup.py` line 237 runs `git branch -D`. | Never pass `--delete-branch` (D-4). |
| F-04 | Medium | The pull request body must hold `Closes #4822` under this record's task list. Open blockers remain. | T-PR in `tasks.md`. | Create a blocker issue before merge (D-9). Report as B-01 to B-05. |
| F-05 | Medium | Only one of seven issue 2977 record files reached main. | RC-11 and RC-12. Six files exist only in the recovery branch. | Keep the recovery branch. Plan a separate issue to publish the record. |
| F-06 | Medium | The main `spec.md` for issue 2977 differs from the snapshot by three lines. | `git diff --shortstat` reports three insertions and three deletions. | Owner chooses the correct text (U-12). Report as part of B-06. |
| F-07 | Medium | Issue #4624 is closed. Its fragment is absent on main and present in the `ap-report` snapshot. | RC-18. The `ap-report` snapshot adds `changelog.d/issue-4624-ap-warning-window.md`. | Owner reviews the fix before removal (U-13). Report as B-06. |
| F-08 | Medium | Owner comment 2 calls PR #4823 a draft. PR #4823 merged on 2026-11-19. | RC-03 and the PR state from `gh pr view`. | Correct the status in the blocker report. |
| F-09 | Low | The public record does not name the four removed branches. | T009 and U-04. | Owner names them. |
| F-10 | Medium | The `sync` snapshot parent is the tip of a branch that still has a live registration. The branch is merged by git and has no pull request. | Local evidence in `design/research.md`. No pull request has that head. | Report as B-05. Do not remove it in this issue. |
| F-11 | Low | The `release` and `sync` snapshots hold zero tracked files. | Snapshot table in `design/research.md`. | Their pending content exists only in the archive. Verify the archive (T006). |
| F-12 | Medium | The `requirements` snapshot changes `requirements.txt` and `uv.lock`. The owner reports a bootstrap failure. | Snapshot numstat: 3 and 3 lines in `requirements.txt`, 40 and 38 in `uv.lock`. RC-76 to RC-78. | Out of scope. Report as B-07. |
| F-13 | Low | Each recovery branch stays 42 commits behind main. | Local count `branch..main` in `design/research.md`. | Keep the commit identifiers (D-8). |
| F-14 | Low | No current registration matches the owner statement about a broken VMM registration. | Registration list in `design/research.md`. | Unverified (U-07). |
| F-15 | Low | The two Labs snapshots share 29 identical files. | TST-004 result. | The private comparison stays open (T005). |
| F-16 | Low | Two snapshots change `.specify/feature.json`. | Snapshot classification in `design/research.md`. RC-52 forbids such changes in read-only commands. | Exclude the file from every restore (D-14). |
| F-17 | Medium | The local gates table has no row for Git and GitHub evidence tasks. | `.github/copilot-instructions.md` lines 50 to 74 list no row for them. RC-49 and RC-50. | Each evidence task names a test case instead. Unresolved item U-16. |
| F-18 | Low | Owner comment 3 states that 414 `.github` entries match main. | Not re-counted in this record. | Unverified (U-09). |

## Coverage Summary

Each requirement maps to at least one task and one test case.

| Requirement | Tasks | Test cases |
| - | - | - |
| FR-001 | T001, T002 | TST-001, TST-002 |
| FR-002 | T003 | TST-003 |
| FR-003 | T006 | TST-006, TST-007 |
| FR-004 | T007 | TST-008 |
| FR-005 | T004, T005 | TST-004, TST-005 |
| FR-006 | T008 | TST-009, TST-010 |
| FR-007 | T009, T011 | TST-011, TST-012 |
| FR-008 | T011 | TST-013 |
| FR-009 | T012, T013 | TST-014 |
| FR-010 | T016, T-MERGE | TST-015 |
| FR-011 | T014, T-PR | TST-016 |
| FR-012 | T014 | TST-017 |
| FR-013 | T015 | TST-018 |
| FR-014 | T016, T-PR | TST-019 |
| FR-015 | T-LOCAL-GATES, T-REMOTE-CI | TST-020, TST-021 |
| FR-016 | T010 | TST-022 |
| FR-017 | T010 | TST-023 |

## Constitution Alignment

All constitution rules that apply to this record pass. The plan records each result in its constitution check table.

## Unmapped Tasks

No task lacks a requirement. Every task maps to at least one row in the coverage table.

## Metrics

| Measure | Count |
| - | - |
| Requirements (FR) | 17 |
| Tasks, including the four final tasks | 20 |
| Test cases (TST) | 23 |
| Remote checks (RC) | 84 |
| Decisions (D) | 14 |
| Human decisions | 1 |
| Blockers (B) | 7 |
| Unverified items (U) | 16 |

## Blockers

Each blocker appears in the issue report. Each one has a cause and a next action.

| ID | Blocker | Cause | Next action |
| - | - | - | - |
| B-01 | Two admin directories remain. Windows blocked their deletion, as the owner reports. | A Windows lock. This record does not identify the holding process. | Close the app sessions. Run T010 again. |
| B-02 | Recovery copies exist only locally. | The publication hold in D-2 and the absence of a pushed copy (RC-20 to RC-37). | Complete T012. The owner decides in T013. |
| B-03 | Private archives, the bundle, and the private Labs comparison remain unverified. | The private recovery store is outside this record. | Run T005 to T008 in the private store. |
| B-04 | The four removed branch names and their pull request state are not public. | The branches were deleted before this record. | The owner names the branches in T009. |
| B-05 | Branch `jmorrison-juniper-github-sync-update-merge` has a live registration. Git merges it, and no pull request names it. | An app session may use the folder (U-14). | The owner closes or confirms the session. A later issue decides the removal. |
| B-06 | The `ap-report` snapshot differs from main in eleven files. It also adds an issue #4624 fragment. The 2977 `spec.md` differs by three lines. | Unmerged or unreviewed content (F-06, F-07). | Review the content before any removal. Keep the tags. |
| B-07 | The `requirements` snapshot changes two dependency files. The bootstrap failure is not reproduced here. | Dependency work is outside this issue. | Open a separate issue for the dependency edits. |

## Convergence After Implementation

This issue converges when each condition holds.

1. Each open task in `tasks.md` has status `verified-present`, or each open item is a blocker with a next action.
2. Each removed branch is merged into main, or it has a verified recovery copy.
3. The main commit is unchanged.
4. The issue report names each blocker from the table above.
5. The record passes the writing gate and the route guard tests.
