# Specification Analysis Report: Stranded Branch Preservation

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the `design/` files, and the remote evidence in `design/research.md`.

**Method**: A read-only comparison of the record with the GitHub state and the report source at snapshot time. Each finding names its resolution.

## Findings

| ID | Severity | Finding | Resolution | Status |
| - | - | - | - | - |
| A-1 | High | The issue body lists 52 names. Three of them moved to archive names, and 49 still exist. | Scope comes from the live report rule (D-3). Archive names are processed as they are (D-4). | Resolved in the record |
| A-2 | High | The emulated in-scope set is 543. The 2026-11-23 report lists 505 names, and 38 emulated names are not in it. | Q-2 reruns before each batch and after the last batch (FR-012, T008, T024). | Open until T024 |
| A-3 | High | 102 branches are held by open pull requests. 62 of them wait on draft pull request #4208. | Holds release only after the blocking state changes (FR-013, T019 to T023). | Open (UR-1, UR-2, UR-3) |
| A-4 | Medium | Five open report issues share one title. The shared workflow searches for the title, misses it, and opens a new issue each week (R41, R42). The close path never finds the issue (R43). | A separate defect issue names the five numbers (D-8, T026). | Open (UR-4) |
| A-5 | Medium | AGENTS.md requires `Closes #<issue>` in a pull request body. A merge before the scope check closes the issue while branches remain. | The merge waits for the final scope check (D-7, FR-014, T-MERGE). | Resolved in the record |
| A-6 | Medium | AGENTS.md line 245 forbids two open pull requests on one file. A preservation pull request that stays open would break that rule. | Each preservation pull request closes in the same step. Held branches wait (D-1, D-2). | Resolved in the record |
| A-7 | Low | `requirements-dev.txt` pins misthelper-devtools at commit 2239e7bd (R12). The shared workflow runs commit 79a5e45 (R05). | The owner of the pin decides the alignment (UR-5). | Open |
| A-8 | Low | `ci.yml` runs pull request events only for `checks_requested` (R13). The title workflow runs on the opened event (R14). The trigger list of `ste-lint.yml` is not read. | T-REMOTE-CI reads the actual checks on the record pull request (UR-6). | Open |
| A-9 | Medium | The report excludes only three name prefixes, not bot authors. Eight bot-authored archive branches are therefore in scope. | The record follows the report rule as written (D-5). The emulation applies the same rule. | Resolved in the record |
| A-10 | Low | 28 branches are younger than seven days. They will age into scope. | The final scope check covers them (D-5, FR-012, T024). | Open until T024 |
| A-11 | Low | The route parent `numbered/0/0/1/2/1/3` gains a child. The guard limit is five children. | The plan table shows three children after the change (plan "Structure Decision"). | Resolved in the record |
| A-12 | Low | The emulation uses name matching for closed pull requests and ancestry for the head. The report uses the compare API for the same test. | Both tests answer the same question for each branch in the snapshot. The difference is recorded in UR-7. | Resolved in the record |
| A-13 | Low | The old WebSocket path that recovery branch 3575 changes is absent on main (R34). The current path exists (R35). | The stale path matters only to the content review of that branch, which is out of scope (spec "Out of Scope"). | Resolved in the record |

## Coverage Summary

| Requirement | Tasks | Checks |
| - | - | - |
| FR-001 | T001, T004, T008 | V-01 |
| FR-002 | T003, T008 | V-01 |
| FR-003 | T004, T009, T019 to T023 | V-02, V-09 |
| FR-004 | T010 to T018 | V-03 |
| FR-005 | T010 to T018 | V-04, V-06 |
| FR-006 | T010 to T018 | V-07, V-08 |
| FR-007 | T010 to T023, T024 | V-06, V-10 |
| FR-008 | T010 to T018 | V-05 |
| FR-009 | T010 to T018 | V-04, V-06 |
| FR-010 | T010 to T023, T025 | V-16 |
| FR-011 | T008 | V-01 |
| FR-012 | T008, T024 | V-01, V-11 |
| FR-013 | T019 to T023 | V-09 |
| FR-014 | T024, T-PR, T-REMOTE-CI, T-MERGE | V-11, V-17 |
| FR-015 | T006, T007, T-LOCAL-GATES | V-12, V-13, V-17 |
| FR-016 | T002, T026 | V-15 |
| FR-017 | T005, T007, T-LOCAL-GATES | V-18 |
| FR-018 | T027, T-LOCAL-GATES | V-14, V-19 |

Each requirement has at least one task and at least one check.

## Constitution Alignment

`plan.md` section "Constitution Check" lists each rule with its result. No rule has the result FAIL. Each rule that does not apply gives its reason.

## Unmapped Tasks

None. Each task maps to at least one requirement in the coverage table.

## Metrics

| Metric | Value |
| - | - |
| Branches on origin, excluding `main` | 597 |
| Open pull requests at snapshot | 7 |
| Pull requests of all states at snapshot | 2396 |
| In-scope branches | 543 |
| Ready branches | 441 |
| Held branches | 102 |
| Ready batches of at most 50 rows | 9 |
| Held groups | 5 |
| Remote claims in `design/research.md` | 54 |
| Decisions | 11 |
| Requirements | 18 |
| Tasks | 31 |
| Verification checks | 19 |
| Human decisions | 0 |

## Unresolved Items

- **UR-1**: Draft pull request #4208 holds 62 branches. The release trigger is the close or merge of #4208. The owner of #4208 decides. Task T023 waits for this trigger.
- **UR-2**: Draft pull request #4813 holds 12 branches. The release trigger is the close or merge of #4813. The owner of #4813 decides. Task T019 waits for this trigger.
- **UR-3**: Dependabot pull requests #4886, #4887, and #4888 hold 3, 4, and 21 branches. The release trigger is the close or merge of each pull request. Whether Dependabot closes these pull requests is not verified. Tasks T020 to T022 wait for these triggers.
- **UR-4**: Four open report issues duplicate issue #4583. The defect issue of task T026 owns the fix. The maintainers of misthelper-devtools make the change.
- **UR-5**: The `misthelper-devtools` pin in `requirements-dev.txt` differs from the workflow pin. The owner of `requirements-dev.txt` decides the alignment.
- **UR-6**: The trigger list of `ste-lint.yml` is not read. Task T-REMOTE-CI observes the checks that run on the record pull request.
- **UR-7**: 38 in-scope names do not appear in the 2026-11-23 report. The cause is not verified. Tasks T008 and T024 rerun Q-2, which records the current names.
