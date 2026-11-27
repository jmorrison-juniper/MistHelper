# Specification Analysis Report: Stranded Branch Preservation

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the `design` folder, and the constitution (version 1.9.0, last amended 2026-10-06).

**Method**: A read-only review of the record against the remote evidence in `design/research.md` and the inventory in `design/data-model.md`. Each finding names its source.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| F-01 | Defect | HIGH | `misthelper-devtools:.github/workflows/reusable-stranded-branch-report.yml` line 156 | The title search returns no match, so each run opens one tracking issue. Ten tracking issues exist. Each successful run from 2026-09-27 to 2026-11-23 created one of them. | D-7, tasks T020 to T022 |
| F-02 | Scope drift | HIGH | Issue #4911 body | The report lists 505 rows. Of these, 434 are archive rows. This record covers 51 rows. | D-1, task T015 |
| F-03 | Stale evidence | MEDIUM | Owner comments of 2026-11-09 | The owner comparisons used `main` at `3964d21d`. Current `main` is `f03c6c9b`, committed 2026-11-26T07:15:01Z. The 49 recorded heads are unchanged. Content equivalence is not rechecked. | D-4, unverified item U-2 |
| F-04 | Unverified | HIGH | Two local-only branches | Neither branch exists on GitHub or in this clone. Owner comments report both in another worktree. | D-13, tasks T006 and T014 |
| F-05 | Conflict | MEDIUM | Constitution pull request rules and `documentation/quality-gates.md` line 118 | The constitution requires a closing line in each pull request description, such as `Closes #4719`. The quality gates guide uses `Refs` for a preparation pull request. | D-8 |
| F-06 | Conflict | MEDIUM | Constitution Principle IV, steps 10 to 12 | The container build runs only for a product file change. A record change builds no image, so the steps cannot run as written. | D-10 |
| F-07 | Conflict | LOW | `changelog.d/README.md` line 58 and constitution release-note rule | The README exempts an internal-only change from a fragment. The constitution requires one fragment for each change. | D-9 |
| F-08 | Privacy | HIGH | Branch `recovery/2977-handoff-20261004` | The owner placed a privacy hold on the source. This record holds metadata only. | D-5, task T013 |
| F-09 | Overlap | MEDIUM | Open draft pull requests #4208 and #4813 | Four branches share one changed path each with these pull requests. The shared paths are two entries of `deploy/.env.example`, one refactor test module, and one export test module. | D-6, task T012 |
| F-10 | Stale owner claim | LOW | Owner comments that name pull requests #4701, #4493, #4615, #4358, #4404, and #4322 | None of these pull requests is open now. The seven open pull requests are #4890, #4889, #4888, #4887, #4886, #4813, and #4208. | Recorded here. No action. |
| F-11 | Gap | MEDIUM | Owner publication hold | The hold blocks tasks T011 to T014. No preservation pull request exists yet. | D-3, task T010 |

## Coverage Summary

| Requirement | Tasks | Checks |
| - | - | - |
| FR-001 | T001, T002 | TC-01 |
| FR-002 | T001 | TC-02 |
| FR-003 | T011, T012, T013 | TC-03 |
| FR-004 | T010, T011 | TC-04 |
| FR-005 | T011, T012 | TC-05 |
| FR-006 | T013 | TC-06 |
| FR-007 | T012 | TC-07 |
| FR-008 | T006, T014 | TC-08 |
| FR-009 | T003, T004, T020 | TC-09 |
| FR-010 | T004, T021 | TC-10 |
| FR-011 | T022 | TC-10 |
| FR-012 | T005, T-LOCAL-GATES | TC-11 |
| FR-013 | T-PR, T-REMOTE-CI, T-MERGE | TC-11 |
| FR-014 | T007 | TC-12 |
| FR-015 | T015 | TC-01 |
| FR-016 | T-LOCAL-GATES | TC-12 |

Every requirement maps to at least one task and at least one check. Every task maps to at least one requirement. No task is unmapped.

## Constitution Alignment

The constitution check in `plan.md` records 18 rows. Seventeen rows pass. Principle IV, steps 10 to 12, fails. Finding F-06 explains the failure. Decision D-10 keeps the record reviewable, and the owner decides whether to amend the constitution or the workflow trigger.

## Unresolved Items

- F-01: The upstream fix is not available. Tasks T020 to T022 wait for it.
- F-02: The 454 extra rows of issue #4911 have no owner assessment. Task T015 handles them.
- F-03: Content equivalence against current `main` is not rechecked. Deletion stays out of scope for this reason.
- F-04: The two local-only branches have no verified local existence. Task T014 handles them.
- F-05: The closing keyword closes issue #4719 on merge. The next report opens a new tracking issue until task T021 lands.
- F-06: Constitution steps 10 to 12 cannot run for a record change. The owner decides the remedy.

## Metrics

| Measure | Value |
| - | - |
| Branches in scope | 51 |
| Commits ahead, total | 66 |
| Changed path entries, total | 515 |
| Batch 1, clean branches | 46 |
| Batch 2, overlap branches | 4 |
| Batch 3, privacy-held branch | 1 |
| Requirements | 16 |
| Tasks | 20 |
| Checks | 12 |
| Remote verification rows | 96 |
| Decisions | 13 |
| Human decisions | 0 |

## Convergence After Implementation

- After tasks T011 and T012, check TC-03 finds 50 of 51 branches with a draft preservation pull request. Check TC-03 finds 51 after task T013.
- After task T021, the weekly report names no branch whose current head has a pull request.
- After task T022, check TC-10 finds exactly one open tracking issue.
