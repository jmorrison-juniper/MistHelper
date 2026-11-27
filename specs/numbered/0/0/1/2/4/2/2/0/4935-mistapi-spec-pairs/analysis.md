# Specification Analysis Report: Check Every Operation Pair in the mistapi Spec Guard

**Date**: 2026-11-26

**Scope**: The spec, plan, tasks, design files, guard file on `main`, spec files 4934, 511, 591, 932, and 595, and the constitution.

**Method**: A read-only pass compared the specification with the code on GitHub `main`. The pass also surveyed each spec file and simulated the SDK check. Each claim cites a remote check in `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| F1 | Defect | HIGH | Guard lines 52 to 54 and 67 to 77 | The helper keeps the last operation line and the last module line. The guard checks one pair in each file. The old guard examines 462 declarations for 489 operation lines. | Fixed by T004 and T005. |
| F2 | Defect | HIGH | Spec file 511, line 10 | An operation line has no module line. The old helper skipped the file without a message. The new guard fails on `main` until the file changes. | Fixed by T003. |
| F3 | Stale record | HIGH | Spec file 511, lines 14, 15, and 69 | The record says the SDK lacks `countOrgClientFingerprints`. The installed SDK defines it in `mistapi.api.v1.orgs.insights`. Line 69 names a module that the SDK lacks. | Lines 14 and 15 are fixed by T003. Line 69 stays in Out of Scope. |
| F4 | Design gap | MEDIUM | Spec files 591 and 932 | Each file has an operation line and prose in the module position. The SDK lacks each function. | Resolved by the declared absences with a drift check (D-3). |
| F5 | Conflict | LOW | `changelog.d/README.md` line 58 and constitution line 409 | The README allows no fragment for an internal change. The constitution requires one fragment for each change. | Resolved by constitution precedence (D-10). The owner can reconcile the two texts. |
| F6 | Stale comment | LOW | Guard line 77 | The comment says that a spec without a module path needs an upstream decision. | Replaced by T004. |
| F7 | Frozen mismatch | LOW | Spec file 595, line 14 | The frozen spec declares `mistapi.api.v1.orgs.aos`. The SDK lacks `getOrgAosRegisterCmd`. | Out of scope. The frozen list excludes the file by design (FR-009). |
| F8 | Documentation drift | LOW | `documentation/MIST_API_MISSING_ENDPOINTS.md` line 246 | The file lists `listWebhookTopics` as missing. The installed SDK defines it. | Out of scope. A separate issue must cover it. |
| F9 | Approximation | MEDIUM | Research R4 | The simulation uses a regular expression, not the `ast` scan. | The gate run in T-LOCAL-GATES is the authority. |
| F10 | Name collision | LOW | Installed SDK | The name `show` has two top-level definitions. No operation pair uses it. | No action. |
| F11 | Guard gap | LOW | Guard, module lines | A module line without an operation line is ignored. The survey found no such line on `main`. | Owner decision. Out of scope, and recorded as D-5. |

## Coverage Summary

Test names: TST-1 is `test_declared_sdk_modules_define_the_declared_operation`, updated. TST-2 is `test_wrong_first_pair_fails_the_guard`. TST-3 is `test_operation_without_module_line_fails_the_guard`. TST-4 is `test_empty_spec_tree_fails_the_guard`. TST-5 is `test_declared_absence_fails_when_sdk_defines_operation`.

| Requirement | Task | Test or check | Notes |
| - | - | - | - |
| FR-001 | T005, T006 | TST-1 | The spec file of issue 4934 contributes 25 pairs. |
| FR-002 | T004 | TST-2, TST-3 | Pairing uses the next module line. |
| FR-003 | T004, T006 | TST-3 | Orphan pairs carry no module. |
| FR-004 | T006 | TST-1, TST-2 | Mismatches use the failure helper. |
| FR-005 | T006 | TST-4 | Zero pairs fail. |
| FR-006 | T006 | TST-5 | The drift check uses the SDK map. |
| FR-007 | T006 | TST-1, TST-2 | The summary line is printed on each run. |
| FR-008 | T003 | TST-1 | Spec file 511 then passes the real guard. |
| FR-009 | T005 | TST-1 | The frozen list is unchanged. |
| FR-010 | T007 | TST-2 | The proof step fails the old logic. |
| FR-011 | T-PR | File list review | The pull request holds four file groups. |
| FR-012 | T010 | Record check | No record line begins with a guard prefix. |
| FR-013 | T004, T005 | Review checklist | Inline comments and logging lines. |
| FR-014 | T004, T006 | Review checklist | Parameter, block, and line limits. |
| FR-015 | T009 | Changelog guard | `test_changelog_fragment_policy.py` runs in the shard. |
| FR-016 | T006 | Symbol gate | No module-level name is added. |

## Consistency Review

| Check | Result |
| - | - |
| The examined count of 489 equals the survey count. | Yes. The survey has 490 operation lines, and 1 belongs to the frozen file. See research R3. |
| The file list in the plan equals FR-011. | Yes. The plan lists four file groups. |
| The task count equals the STATUS file. | Yes. There are 14 tasks. |
| The requirement count equals the STATUS file. | Yes. There are 16 requirements. |
| The planned test count equals the STATUS file. | Yes. There are 5 tests. |
| The remote check rows equal the research table. | Yes. There are 50 rows in each. |
| The summary count equals the remote check rows. | Yes. The summary states 50. |
| The route equals the base-5 computation. | Yes. See research R11. |
| The line references to spec file 511 agree. | Yes. Lines 14 to 16 appear in the spec, the plan, and task T003. |
| The clarification answers match the requirements and tasks. | Yes. |

## Unresolved Items

1. Owner decision: whether a module line without an operation line should fail the guard (F11, D-5).
2. Separate issue: refresh spec file 511 beyond lines 14 to 16, including line 69 (F3).
3. Separate issue: correct `documentation/MIST_API_MISSING_ENDPOINTS.md` for `listWebhookTopics` (F8).
4. Owner decision: reconcile the constitution with `changelog.d/README.md` on fragments for internal changes (F5).
5. Verify in T-LOCAL-GATES: the real guard prints 489 examined pairs and zero defects (F9).
6. Verify in T-LOCAL-GATES: the test quality analyzer reports zero new findings for the new tests. This record did not run the analyzer.

## Metrics

- Spec files on `main`: 910.
- Operation lines in the non-frozen spec files: 489.
- Module pairs in the non-frozen spec files: 486 before the change and 487 after the change.
- Declared absences: 2.
- Requirements: 16. Success criteria: 6. Tasks: 14. Planned tests: 5. Decisions: 12. Remote checks: 50.

## Convergence After Implementation

After tasks T003 to T010 complete, these statements hold:

- The real guard prints `mistapi spec module guard: examined 489 operation pairs, 0 defects.`
- The spec file of issue 4934 contributes 25 checked pairs.
- Spec file 511 declares `mistapi.api.v1.orgs.insights`.
- Spec files 591 and 932 hold declared absences that the SDK confirms.
- The frozen list and spec file 595 remain unchanged.
