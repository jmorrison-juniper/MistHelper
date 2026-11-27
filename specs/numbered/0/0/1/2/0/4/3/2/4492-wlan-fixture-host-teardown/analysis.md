# Specification Analysis Report: WLAN fixture host teardown

## Findings

| ID | Category | Severity | Location | Finding | Resolution |
| - | - | - | - | - | - |
| F-1 | Defect in existing work | High | Issue #4492, "Steps to reproduce" | The reproduction path `tests/unit/config/foundation/support/refactors/network/configuration/` is absent on main (R-02). The command fails before any test runs. | D-6 uses the main path. |
| F-2 | Defect | High | `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`, line 45 | The fixture binds the resolver host and never restores it (R-01). The two named tests then read the fake host (R-08, R-10). | T001 adds the restore. |
| F-3 | Latent defect | Medium | CI order on main | Main root-units passes (R-40). Sorted collection runs the WLAN file after all 21 failing tests (R-37, R-38). The defect remains. | T005 and T006 run both shards. T003 and T004 cover the explicit order. |
| F-4 | Process risk | Medium | `.github/test-quality-baseline.json` | Baseline keys include `line_number` (R-24). Seven WLAN entries below line 46 would become new findings (R-23, R-25). | T002 shifts each value by four. |
| F-5 | Scope gap | Medium | Issue #4492, first paragraph | The issue says that 21 later tests fail. Only the two named tests read the resolver host directly in the log (R-09, R-11). The other 19 failures use file-specific seams (R-16 to R-19). | U-1, D-7, and T005. |
| F-6 | Stale issue comments | Low | Issue #4492 comments of 2026-11-08 and 2026-11-09 | The comments describe PR #4358 as a draft with conflicts. PR #4358 merged on 2026-11-13 (R-43). The issue remains open. | D-8 keeps the issue open until the merge. |
| F-7 | Unclear link | Low | Search for "4492" | PR #4357 matched the search through a session path token, not an issue link (R-77). | Excluded from the linked pull requests. |
| F-8 | Governance | Low | Issue labels | The issue keeps `needs-human-review`. | D-9 keeps the label and requires review before merge. |

## Consistency Review

- Spec and plan agree on the path, the seven-line block, and the +4 baseline shift.
- Plan and tasks agree on the file list. Tasks name no path outside the change map.
- Spec clarifications cite the same run IDs as research.md.
- The 21 named IDs in research.md match the CI log summary of 21 failures (R-41).
- The route in the plan matches the base-5 digits of 4492 (R-51, R-52).
- Each task names one verification command from the local gates table (R-57).

## Coverage Summary

| Requirement | Tasks | Verification (test or gate) |
| - | - | - |
| FR-001 | T001, T004 | Mutation proof and three-node sequence (quickstart Scenarios 2 and 4) |
| FR-002 | T001, T005 | Root-units shard (quickstart Scenario 7) |
| FR-003 | T001, T-LOCAL-GATES | Diff scope check (quickstart Scenario 8) |
| FR-004 | T001 | Log line count (quickstart Scenario 3) |
| FR-005 | T001 | Review of each changed line (quickstart Scenario 3) |
| FR-006 | T002 | Test-quality gate (quickstart Scenario 6) |
| FR-007 | T001 | Main path in every verification command (evidence rows R-01 to R-03) |
| FR-008 | T003, T004, T005, T006 | Three-node sequence and both shards (quickstart Scenarios 2, 4, and 7) |
| FR-009 | T-LOCAL-GATES | Local gates (quickstart Scenarios 5 to 8) |
| FR-010 | T-PR, T-MERGE | Pull request body check (quickstart Scenario 9) |
| FR-011 | T-LOCAL-GATES, T-PR | Pull request body lists only gates that ran |

Every requirement maps to at least one task and at least one verification command.

## Constitution Alignment

The Constitution Check in plan.md gives a result and a reason for each rule. No rule fails. Principles VI and VII need the comment and log lines in T001 (R-64, R-65).

## Unmapped Tasks

None. Every task maps to at least one requirement.

## Metrics

- Requirements: 11 (FR-001 to FR-011).
- Tasks: 10 (T001 to T006, and four final tasks).
- Decisions: 13 (D-1 to D-13). Human decisions: 0.
- Remote checks: 77 (R-01 to R-77).
- Named regression IDs: 21.
- Baseline entries that change: 7.
- Net line change in the fixture: +4.

## Defects in Existing Work

- F-1 is corrected by D-6 and the main path in every task.
- F-2 is corrected by T001.
- F-3 and F-4 are process defects. T002 corrects the baseline. T005 and T006 prove the shard behavior.

## Unresolved Items

- U-1 to U-9 remain open. Each item names its reason in research.md, section 9.
- No gate result exists in this record. The authoring phase runs no tool (brief rule 2).

## Convergence After Implementation

After T-MERGE, run quickstart Scenario 9 for the new main head. The main root-units shard must report success. The record then has no open defect for the 21 named IDs.
