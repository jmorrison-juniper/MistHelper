# Specification Analysis Report: Organization Invites Export Handles a Missing mistapi Function

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the files in `design/`, and GitHub main at commit `f03c6c9`.

**Method**: A read-only review. The review compares each legacy claim with GitHub main. It maps each requirement to a task and a test. It lists defects in existing work and the items that stay open.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A-1 | Inconsistency | High | Legacy `plan.md` line 13. RV-14, RV-15 | The legacy plan says Python 3.13. The pyproject file requires Python 3.15. | Corrected in this record. |
| A-2 | Inconsistency | High | Legacy `spec.md` line 13. RV-19 | The legacy spec says the work is committed in `b2249e25`. The commit exists neither on GitHub nor locally. | Removed. This record cites merge commit `0686430`. |
| A-3 | Underspecification | Medium | Edge Cases. RV-33, RV-34 | A later release that adds `listOrgInvites` writes through the default primary key strategy. The constitution requires a defined strategy. | Open. Decision D-9. The trigger is in the plan Risks table. |
| A-4 | Defect | Medium | `_invites` lines 727, 728, 729, 730, and 734. RV-42 | Principle VI breach. Adjacent lines lack a reason comment. | Fixed by T010. |
| A-5 | Defect | High | `_invites` lines 733 to 735. RV-43 | Principle VII breach. No INFO record before and no DEBUG record after the shared export call. | Fixed by T011. Tested by T008. |
| A-6 | Defect | Low | `_invites` line 718. RV-41 | `AGENTS.md` requires a declared return type. | Fixed by T009. |
| A-7 | Defect | Medium | Three invites pages. RV-08 to RV-10 | Each page names a list endpoint that no source defines. The link target is the POST page. | Fixed by T012 to T014. |
| A-8 | Coverage | Medium | Absent-path test lines 985 and 986. RV-05 | The `any` check passes with two errors. No test checks the shared export. | Fixed by T007. |
| A-9 | Coverage | Low | `_invites` logs. No test | No test checks the log order. | Fixed by T008. |
| A-10 | Inconsistency | Medium | Legacy `tasks.md` lines 43 and 44. RV-13, RV-21 | Publication tasks stay open after pull request #4829 merged. That pull request used `Refs`, so the issue stayed open. | Superseded by T-PR, which uses `Closes #4825`. |
| A-11 | Inconsistency | Low | Legacy `spec.md` line 7. RV-12 | The status reads "Local commit ready. Publication pending." | Replaced by this record. |
| A-12 | Inconsistency | Medium | Legacy `spec.md` line 88, legacy `plan.md` line 14, `.github/copilot-instructions.md` line 21, and the constitution Technology section. RV-16, RV-18 | The legacy record and the instruction file say `>=0.64.0,<0.65`. The pyproject file says `>=0.64.1,<0.65`. The constitution says `0.59+`. | This record uses the pyproject value. The instruction and constitution text is out of scope. A follow-up issue is recommended. |
| A-13 | Ambiguity | Low | Legacy `plan.md` Risks. LC-20 | "The guard handles both cases" overstates the guard. A renamed function is skipped, not followed. | Restated in the spec Edge Cases. |
| A-14 | Evidence | Low | Legacy `tasks.md` line 14. LC-21 | Task T001 cites `spec.md` as investigation evidence. | Replaced by `design/research.md`. |
| A-15 | Historical defect | Low | `specs/009-api-docs-enrichment/research.md` line 93. RV-37 | Specification 009 names `listOrgInvites` under `orgs.invites`. | Out of scope. The historical record stays unchanged. A follow-up note is recommended. |
| A-16 | Pre-existing debt | Low | `org_export_utils.py`, about 20 export lines including line 733. D-7 | The `# type: ignore[no-untyped-call]` comment appears widely in the module. | Out of scope. A follow-up issue is recommended. |
| A-17 | Pre-existing defect | Low | `documentation/api/orgs/DELETE_orgs_org_id_admins_admin_id.md` line 69, local file | The link text reads `POST_orgs_org_id_admins.md`, but the target is `POST_orgs_org_id_invites.md`. This item is not a dependency of this record. The remote blob was not checked. | Out of scope. A follow-up note is recommended. |
| A-18 | Unverified | Low | Issue #4825 log line 721. U-2 | The base commit places the call at line 714. | Recorded in the research Unverified list. |
| A-19 | Dead code | Medium | RV-35, RV-36, D-3 | `_invites` has no caller on GitHub main. A defect in it has no operator impact. | Kept by D-3. A follow-up issue decides on removal. |

## Coverage Summary

| Requirement | Has task | Task IDs | Test | Notes |
| - | - | - | - | - |
| FR-001 | Yes | T001, T002, T004 | `test_invites` | Supported path |
| FR-002 | Yes | T001, T003, T007 | Absent-path test | One ERROR record |
| FR-003 | Yes | T001, T003 | Absent-path test | No exception |
| FR-004 | Yes | T001, T007 | Absent-path test with the export check | No file and no fetch |
| FR-005 | Yes | T001 | None. Verified by review of the diff and RV-35 | No substitute function |
| FR-006 | Yes | T002, T004 | `test_invites` | Arguments unchanged |
| FR-007 | Yes | T008, T011 | Log-order test | INFO before, DEBUG after |
| FR-008 | Yes | T010 | None. Verified by review of the diff | Comments on changed and adjacent lines |
| FR-009 | Yes | T009 | None. Verified by review of the diff | Return type `None` |
| FR-010 | Yes | T005, T012, T013, T014 | Markdown link guard, and the search in quickstart step 5 | No list endpoint |
| FR-011 | Yes | T007 | Absent-path test | Exact count and no export call |

## Consistency Review

- The spec, plan, and tasks name the same file paths and line ranges. The line ranges come from GitHub main at commit `f03c6c9`.
- The plan constitution check matches analysis items A-4, A-5, and A-6.
- The FR numbers in the spec match the tasks and the coverage table above.
- Decisions D-1 to D-13 in `design/research.md` match the plan Risks table and the tasks.
- The legacy record has 15 verified claims, 7 stale claims, and 1 absent claim (research Legacy Claim Checks). Three claims are unverified and not counted.

## Unresolved Items

- A-3. The primary key strategy for a future `listOrgInvites`. The trigger is a pinned mistapi release that defines the function. The plan Risks table gives the mitigation.
- A-12. The mistapi version text in the instruction file and the constitution. A follow-up issue is recommended.
- A-15. The historical mention in specification 009. No change is planned.
- A-16. The module-wide `# type: ignore[no-untyped-call]` pattern. A follow-up issue is recommended.
- A-17. The mislabeled link on the admin delete page. A follow-up note is recommended.
- A-19. The method with no caller. A follow-up issue decides on removal.
- A-18 and U-1. The issue log line number and the legacy test results. These values are not reproduced in this record.

This record does not create GitHub issues. The orchestrator opens the follow-up issues after the record is accepted.
