# Analysis: Split tests/unit into domain packages

## 1. Consistency Review

| Area | Spec | Plan | Tasks | Remote evidence | Result |
| - | - | - | - | - | - |
| Root limit (FR-001, SC-001) | Five children or fewer | Target table row `./` lists five children | T005 ratchet and T071 final check | RC-01 counts 50 | Consistent. Not met yet. |
| Group limit (FR-002, SC-002) | Five children or fewer | Target table rows are five or fewer | Split rule and T030 to T041 | Counts come from the `main` tree listing | Consistent. Split groups are chosen in split tasks. |
| Collection parity (FR-003, SC-003) | Node IDs match after normalization | Test plan TP-2 | T002 baseline and T072 check | Baseline not captured (U-1) | Consistent. Open. |
| Active references (FR-004, SC-006) | Active paths updated | Reference table | T028, T033, T036, T038, T050, T051, T054, T070 | Inventory in research section 6 | Consistent. Backslash references are covered by T004. |
| Behavior (FR-005, SC-004) | File content unchanged | Change map | Focused tests in each batch | Not run | Consistent. Open. |
| Holds (FR-006, SC-005) | No held path moves | Holds table | T003 and T060 to T068 | H-1 to H-8 in research section 4 | Consistent. |
| No production change (FR-007) | No executable change | Decision D-8 | T074 production diff check | Production comments listed in research section 6 | Consistent. |
| Route | Numeric route from `spec-route.ps1` | Plan header | Record folder | Base-5 digits of 4142 are 113032 | Consistent. |

## 2. Requirement Coverage

- FR-001 maps to T005 and T071, and to test TP-1.
- FR-002 maps to T005, T030 to T041, and T071, and to test TP-1.
- FR-003 maps to T002 and T072, and to test TP-2.
- FR-004 maps to T004, T028, T033, T036, T038, T050, T051, T054, T070, and T075, and to tests TP-4 and TP-5.
- FR-005 maps to T010 to T027, T030 to T041, and T050 to T053, and to tests TP-3 and TP-6.
- FR-006 maps to T003 and T060 to T068, and to test TP-7.
- FR-007 maps to T074, and to test TP-8.

Each requirement maps to at least one task and at least one test.

## 3. Defects In The Existing Legacy Record

1. The legacy record claims 155 root entries. Main holds 50 (RC-39 and RC-01).
2. The legacy plan reports "Gate result: pass with staged work" while FR-001 is unmet (legacy plan line 44).
3. The legacy plan holds CI paths for PR #4208. PR #4208 changes no `.github` file (ledger S-4). This record updates CI in the same batch (D-7).
4. The legacy plan holds `upgrade_portal` for issue #2752. That issue is closed (ledger S-7).
5. The legacy plan keeps four `output_defaults` files at source because of relative imports. The stated reason is wrong. A whole-package move keeps the imports valid (RC-11, ledger S-8, D-4).
6. The legacy tasks T027 to T069 are marked complete. Their evidence comes from a branch and candidate commits. `main` confirms four sampled destinations and two sampled sources (ledger V-3 and V-4). The other claims are not confirmed (U-1 and U-2). This record does not carry them forward as complete.
7. The legacy holds for issues #2746, #2747, #2753, and #4126 went beyond their exact claims. This record narrows them (D-2).
8. PR #4208 adds `tests/unit/wan_performance/` as a new root child (RC-18). The legacy record does not mention it. Merging PR #4208 as filed would raise the root count to 51. H-1 blocks the merge until the owner rebases the path.
9. `Containerfile` and `Dockerfile` name `tests/unit/container/test_build_files_match.py`, a path that no longer exists. The defect predates this issue. Warning: editing a build file starts a container build. D-8 defers the fix to a follow-up issue.
10. `tests/unit/marvis/actions/` holds 11 children on `main`. This is a grandfathered violation until H-7 releases (plan section "Complexity Tracking").

## 4. Unresolved Items

1. Split tasks (T030 to T041, T050 to T053, T060 to T068) choose the file membership of each group at run time under section 6 of `tasks.md`. This record fixes the parents, the group names, and the counts, not every file. Mitigation: each task checks counts and node IDs.
2. The `org` split groups (T041) and the `utils` split groups (T038) are chosen at run time under the same rule.
3. The production and build-file comments in D-8 stay stale until the follow-up issue lands.
4. Issue #3300 holds a historical link to the analytics path. That link goes stale after T010 (D-3).
5. Session claims are not visible to this agent (U-6). T003 requires a coordinator check before each batch.
6. Issue #2746 may or may not name `tests/unit/test_issue_2971_census_repairs.py` in its scope (U-7). H-8 applies until the owner confirms.
7. The body of merged PR #4358 was not read (U-8).
8. The legacy folder under `specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages` is stale. The orchestrator replaces its content with this record in the final commit.
9. The legacy research and test map were read only in part (research section 1). Their unread rows are not carried forward.

## 5. Self-Review Results

- Orchestrator validator (read-only): status `complete`, no missing file, no child overflow, zero forbidden tokens, zero prose semicolons, 44 remote checks, 10 decisions, 0 human decisions, 7 requirements, and 60 tasks. The `record_dir` value matches the route.
- Semicolon search across all draft Markdown files: zero matches after the fixes in research D-2 and D-5.
- Phrasal verb, British spelling, and contraction search: one match (plan rollback wording), fixed.
- Count match: the 60 tasks in `tasks.md` equal the STATUS value. The 44 rows in research section 2 equal the STATUS `remote_checks`. The summary names the same counts.
- Child counts: the feature root holds 5 children, `design` holds 4, and `design/checklists` holds 1.
- Requirement coverage: each of FR-001 to FR-007 maps to a task and a test (section 2).
- Verification commands: each batch task uses a `pytest` command from the local gates table, or a `git grep` or `git diff` command from the same table. The final tasks T-PR, T-REMOTE-CI, and T-MERGE use GitHub commands. The brief defines these as remote steps, and the local gates table does not list them.

