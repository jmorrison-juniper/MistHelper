# Specification Analysis Report: Mixed WAN History Summaries

**Scope**: Consistency review across `spec.md`, `plan.md`, `tasks.md`, and the remote code on GitHub. The review reads each claim against the remote checks in `design/research.md`. Each finding names its remote check numbers.

## Findings

| ID | Severity | Finding | Evidence | Disposition |
| - | - | - | - | - |
| A-01 | High | The repair commit adds no inline comments or action logging to the changed link-event block. | Remote checks 52, 53, and 54 (`summary.py` lines 337 to 354). Constitution Principles VI and VII: remote checks 10 and 11. | Fixed by T003 and T006. |
| A-02 | High | PR 4208 is a draft, and its merge state is DIRTY and CONFLICTING. | Design research, Linked work. | Blocks T-PR and T-MERGE. Decisions D-8 and D-9 cover the rebase and the stop rule. |
| A-03 | Medium | The PR body refers to issue 4794 without a closing keyword, so a merge does not close it. | Remote check 47. AGENTS rule: remote check 94. | Fixed by T-PR (decision D-10). |
| A-04 | Medium | Repair commit d7a706d covers three issues in one commit. Its message names 4793, 4794, and 4795, and its file list includes history store and portal files. | Remote checks 97 and 98. | Open. The orchestrator files a separate issue for the mixed commit. This change keeps to the 4794 lines. |
| A-05 | Medium | The mixed-hour test asserts only the daily summary. The build also creates weekly, monthly, and rolling summaries through the same helper. | Remote checks 55, 56, 57, and 62. | Fixed by T004 (decision D-2). |
| A-06 | Low | No test asserts a `None` link-event summary for snapshot-only periods. | Remote check 99. The `_has_events` path is covered by remote check 54. | Fixed by T005. |
| A-07 | Medium | The mistapi version wording differs across the repository. The copilot instructions say `>=0.64.0,<0.65`. Pyproject says `>=0.64.1,<0.65`. Requirements pin `0.64.1`. | Remote checks 7, 23, and 25. | Out of scope. Decision D-11 files a separate issue. |
| A-08 | Low | The issue cites commit 15c69b11 and a macOS run. Neither exists on GitHub. | Remote check 46. | Unverified item U-4. The reproduction relies on code reading. |
| A-09 | Info | The snapshot premise holds. Ordinary snapshot records do not name `flap_count`, except in the gateway insight set. | Remote check 72. | Consistent with the spec, assumption A-2. |
| A-10 | Info | Only `live.html` reads the link-event fields. Integration modules hold no field name. | Remote checks 66, 68, 69, and 83. | Consistent with the risk entry on type changes in `plan.md`. |
| A-11 | Info | Each summary selects one identity before it builds. | Remote check 88. | Consistent with the identity edge case in `spec.md`. |
| A-12 | Info | The existing empty-period test covers the zero-match edge case. | Remote check 87. | Consistent with the edge case in `spec.md`. |

## Coverage Summary

Each requirement maps to at least one task and at least one test. The test column names the test or the review item. Review items sit in `design/checklists/regression.md`.

| Requirement | Tasks | Test or review |
| - | - | - |
| FR-001 | T004 | `test_mixed_event_and_ordinary_hours_ignore_absent_event_metrics` |
| FR-002 | T003, T004 | The same mixed-hour test |
| FR-003 | T003, T004 | The same mixed-hour test |
| FR-004 | T004 | The same mixed-hour test, with `expected_hours` from each period |
| FR-005 | T005 | `test_snapshot_only_hours_leave_event_summary_absent` |
| FR-006 | T003 | `test_missing_event_evidence_does_not_report_zero_flaps_or_minutes` |
| FR-007 | T003 | `test_known_zero_flaps_do_not_infer_known_duration_minutes` |
| FR-008 | T004 | The mixed-hour test across all period kinds |
| FR-009 | T007 | `test_live_link_event_view_renders_missing_evidence_as_unknown` |
| FR-010 | T002, T004, T005 | The three regression tests and the snapshot-only guard |
| FR-011 | T003, T006 | Review item RG-07 in `design/checklists/regression.md` |
| FR-012 | T-PR, T-REMOTE-CI, T-MERGE, T009 | Remote read of main after T-MERGE (SC-005) |

Every task maps to at least one requirement. No task is unmapped.

## Constitution Alignment

`plan.md` lists each rule with its result. Two rules fail at the candidate head: Principle VI (inline comments) and Principle VII (action logging). Both pass after T003 and T006. The branch naming rule fails with a justified deviation (decision D-1). The PR checklist fails until T-PR adds the closing keyword.

## Metrics

- Requirements: 12 (FR-001 to FR-012).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 13 (T001 to T009, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).
- Tests planned: 5. Three existing regression tests, one extended test, and one new snapshot-only test. The e2e test is existing.
- Remote checks: 106. Present: 94. Absent: 9. Partial: 2. Stale: 1.
- Decisions: 11. Human decisions: 1 (D-5).

## Convergence After Implementation

The change converges when these statements hold:

1. Head runs the new test file with zero failures.
2. Parent worktree fails the three regression tests with the expected errors (T002).
3. Every changed block has a same-line comment (T003 and T006).
4. The link-event block builds an info line before and a debug line after the period build (T003).
5. The PR body names `Closes #4794` (T-PR).
6. Main holds the None-safe event code after the merge (T-MERGE).

## Unresolved Items

- U-1 to U-10 in `design/research.md` remain unverified. Each entry gives the reason.
- A-04 remains open until the orchestrator files a separate issue for the mixed repair commit.
- A-02 blocks T-PR until the rebase succeeds with conflicts of 20 lines or fewer.
- D-5 remains open until a human approves or defers publication.
