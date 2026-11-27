# Analysis: Report a missing latest WAN rate

## Consistency Review

- The spec, plan, and tasks name the same four files. Each file maps to at least one task.
- Each functional requirement has at least one task and at least one test or check. The table below gives the mapping.
- The plan targets pull request 4208 head `843be63`. Remote check R-53 confirms the defect at line 282.
- The security checklist covers the secret, input, and network rules of the plan. The requirements checklist covers the spec quality rules.

## Count Checks

| Item | STATUS.json | design/research.md | summary.md | Result |
| - | - | - | - | - |
| Remote checks | 83 | 83 rows | 83 | Match |
| Absent results | 4 | 4 rows | Not stated | Match |
| Stale results | 1 | 1 row | Not stated | Match |
| Decisions | 8 | 8 entries | 8 entries | Match |
| Human decisions | 0 | 0 entries | None | Match |
| Tasks | 10 | 10 entries | 10 tasks | Match |
| Requirements | 12 | 12 entries | 12 requirements | Match |
| Planned tests | 5 | 5 names | 5 tests | Match |

## Traceability Table

The table lists each requirement with its tasks and tests.

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T002, T003 | `test_null_latest_interval_is_unavailable_not_earlier_value`, `test_latest_interval_is_selected_by_start_time_not_position` |
| FR-002 | T002, T003 | `test_null_latest_interval_is_unavailable_not_earlier_value` |
| FR-003 | T002, T003 | `test_absent_latest_interval_is_unavailable_not_earlier_value` |
| FR-004 | T002, T003 | `test_null_latest_interval_is_unavailable_not_earlier_value`, `test_absent_latest_interval_is_unavailable_not_earlier_value` |
| FR-005 | T002, T003 | `test_measured_zero_latest_interval_remains_a_value`, `test_latest_interval_is_selected_by_start_time_not_position` |
| FR-006 | T002, T003 | `test_null_latest_interval_is_unavailable_not_earlier_value`, `test_all_null_intervals_keep_existing_no_value_reason` |
| FR-007 | T002, T003 | `test_latest_interval_is_selected_by_start_time_not_position` |
| FR-008 | T002, T003 | `test_measured_zero_latest_interval_remains_a_value` |
| FR-009 | T003, T006 | Existing test at line 323 of the target file (R-64) and the symbol gate |
| FR-010 | T002 | All five new tests use mocked responses |
| FR-011 | T003, T-LOCAL-GATES | Manual review of each touched line and function |
| FR-012 | T004, T005 | STE writing gate |

## Defects in Existing Work

| ID | Location | Defect | Severity | Action |
| - | - | - | - | - |
| AN-1 | `snapshot_client.py` line 241 on main (R-01) and line 282 on pull request head (R-53) | The builder selects the last valid value as the latest value. An earlier rate appears as current. | High | Fixed by this change after the merge. |
| AN-2 | Same lines | An absent trailing interval also gives an earlier value. The issue text does not describe this path. | High | Fixed by this change (D-3). |
| AN-3 | `snapshot_client.py` line 244 on main (R-04) | `coverage_fraction` holds a count. The one-interval guard at line 219 (R-03) keeps the value between zero and one. | Low | Superseded by pull request head line 285 (R-54). No action. |
| AN-4 | `snapshot_client.py` line 251 on main (R-05) | The builder reads metric-named arrays. The OpenAPI schema documents `results` and `rt` (R-47). | Medium | Superseded by pull request head line 264 (R-59). No action on main. |
| AN-5 | `snapshot_client.py` line 182 on pull request head (R-60) | The port path sets `partial` from quality and status events only. A missing latest rate does not set `partial`. Main counted missing rates at line 224 (R-06). | Medium | Not changed (D-6). Residual risk. Consumers that read only `partial` miss the gap. |
| AN-6 | `snapshot_client.py` line 271 on pull request head (R-55) | `_sample` has six parameters excluding `cls`. The function breaks the five-parameter limit. | Low | Recorded as debt. The change adds no parameter. A separate issue is recommended. |
| AN-7 | Issue 4682, reproduction step 3 | The step is ambiguous. Main rejects two intervals at line 219 (R-03). The reproduction needs a direct builder call on main or the ten-minute path on the pull request head (R-57). | Medium | The new tests use the ten-minute path. The quickstart repeats the reproduction. |
| AN-8 | Pull request 4208 | The review head `fbb23f8` is not an ancestor of the current head `843be63` (R-70). The branch changed after review. Line numbers in the issue may no longer match. | Medium | Task T001 re-reads the target lines before any edit. |
| AN-9 | Pull request 4208 | The owner comment on issue 4583 states that the pull request also owns `src/interfaces/wan_performance/domain/summary.py`. The fix does not change that file. | Low | No action. Recorded for overlap checks. |

## Verified Claims Without a Defect

- The main portal path keeps index positions (R-12, R-13). The browser reads the last hourly row (R-15). The main portal does not have the defect.
- Issue 4583 holds three comments that name issue 4682. The comments dated 2026-11-08 at 20:36:16Z, 20:43:09Z, and 21:31:17Z confirm the link.
- Pull request 4208 is open and conflicting. Its checks on head `843be63` show no failing conclusion.
- Issue 4682 is open with the labels `bug`, `web-portal`, and `in-progress`.
- No other open pull request changes `snapshot_client.py`. The open pull request list read on 2026-11-26 confirms this.

## Unresolved Items

- Unverified items U-1 to U-8 remain open. Section "Unverified" in `design/research.md` lists each one with its reason.
- Residual risks are listed in plan.md, section "Risks and Mitigations".

## Scope Check

- No live Mist call ran in this pass. Issue 4682 states zero live calls.
- No repository file changed. The drafting pass wrote only to the draft folder and the meta folder.
- No test, build, linter, formatter, or package install ran in this pass.
