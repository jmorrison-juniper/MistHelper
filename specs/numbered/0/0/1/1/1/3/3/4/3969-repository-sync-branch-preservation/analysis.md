# Analysis: Repository Sync Branch Preservation

## Consistency review

| Requirement | Tasks | Test |
| - | - | - |
| FR-001 | T002, T-PR, T-REMOTE-CI | VC-01 |
| FR-002 | T001 | VC-02 |
| FR-003 | T004, T005, T007, T011 | VC-03, VC-04 |
| FR-004 | T004, T005, T006, T007 | VC-03, VC-04 |
| FR-005 | T006 | VC-05 |
| FR-006 | T009, T010 | VC-06 |
| FR-007 | T012 | VC-07 |
| FR-008 | T013 | VC-08 |
| FR-009 | T003, T014 | VC-09 |
| FR-010 | T003 | VC-10 |
| FR-011 | T008 | VC-11 |
| FR-012 | T015 | VC-12 |
| FR-013 | T016 | VC-13 |
| FR-014 | T017 | VC-14 |
| FR-015 | T-LOCAL-GATES | VC-15 |
| FR-016 | T018 | VC-16 |

Count checks:

- Requirements: 16 in spec.md. The STATUS file reports 16.
- Tasks: 22 in tasks.md. The STATUS file reports 22.
- Tests: 16 verification commands. The STATUS file reports 16.
- Remote checks: 106 rows in design/research.md. The STATUS file and the summary report 106.
- Decisions: 11 in design/research.md. The STATUS file reports 11.
- Class arithmetic: 4 + 135 + 129 + 47 + 7 + 7 + 0 = 329 local branches besides main. Deletions: 4 + 135 + 129 + 47 + 7 = 322. Kept: 7. Total: 329.
- Tags: 129 + 47 + 5 = 181 new tags.

## Defects in the sync report and owner notes

- DEF-1 Stale counts. The report lists 268 local branches, 217 squash-merged branches, and 14 unpublished branches. Now 329 local branches besides main, 264 name matches to merged pull requests, and 58 local branches with no pull request and no GitHub branch. Evidence: R89, L2, L3.
- DEF-2 Stale pull request states. The report lists 14 pull requests as open, behind, failing, or blocked. All 14 are now merged or closed. Evidence: R70 to R83.
- DEF-3 Name matching misleads. The name `fix/2746-fm-http-status` matches merged pull request #3077 and closed pull request #3956. Its local tip equals the head of #3956. Evidence: L5.
- DEF-4 Coordination issue. Issue #2295 is closed, but its body asks to keep it open. Its sub-issue table does not list #3969. Evidence: R87.
- DEF-5 Owner note on fix/3217-access-log-fields-update. The owner note of 2026-10-30 is correct. The branch has no GitHub copy and no pull request. Merged pull request #3778 used a head whose tip diverges from the local branch. Evidence: R49, R88, R98, L6.
- DEF-6 Unverifiable claims. The report names two sessions and five worktrees that this record cannot observe. Evidence: U-1, U-2.
- DEF-7 Window activity. Four squash merges and two pull request creations landed in the sync window. All used the owner account. The report states that its run merged and created none. Attribution is unverified. Evidence: R84, R85, R86, U-4.
- DEF-8 Closed heads without a GitHub copy. Four closed pull request heads have no GitHub branch. Their commits exist now as local commits only. Evidence: R93 to R96, L5.
- DEF-9 Merge commits hidden by cherry. The cherry output for backup/main-local-2026-09-24 lists one line. Three commits lie beyond origin/main, and two of them are merge commits. The class E recheck therefore counts merge commits. Evidence: L9.

## Unresolved items

- U-GAP-1 Gate table. The local gates table has no gate for branch or tag state. Each sync task uses a read-only command. The owner accepts this rule or adds a gate.
- U-GAP-2 Remote check schema. The remote check schema has no branch row type. This record puts the full ref name in the path field and `none` in the blob field for absent objects. The owner accepts this format or changes the schema.
- U-GAP-3 STE scope. AGENTS.md requires each Markdown file to pass the STE gate. The copilot-instructions STE row names specific files (R17). This record applies the gate to each record file. The owner confirms the scope.
- U-GAP-4 One command for each task. The record format requires one verification command for each task from the local gates table. Branch and tag tasks cannot meet that rule. The owner accepts the read-only command set in design/quickstart.md.

## Consistency with the remote repository

- Each governing document cited in the record has a remote check row: R01 to R43.
- The reference record files exist on GitHub main: R42 and R43.
- The local clone equals GitHub main: R45. The five modified paths do not touch any governing document.
