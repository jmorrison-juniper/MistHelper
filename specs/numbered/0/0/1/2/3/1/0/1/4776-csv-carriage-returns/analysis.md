# Specification Analysis Report: Preserve CSV Carriage Returns

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the design files, and the remote code on `main` and on PR #4813.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-01 | High | PR #4813 uses branch `jmorrison-juniper-csv-carriage-return-preservation`. The name does not follow `<type>/<issue>-<slug>`. | RC-43, RC-44, RC-59 | D-8. The new branch is `fix/4776-csv-carriage-returns`. |
| A-02 | High | PR #4813 changes only `write_to_csv`. The 52-week CSV writer receives escaped rows and writes them without a presentation step. | RC-11, RC-12, RC-13 | D-3. T013 and T006 cover the 52-week writer. |
| A-03 | Medium | PR #4813 grows `write_to_csv` from 25 to 29 lines. The legacy plan says no structural violation exists. | RC-04, RC-58 | The presenter keeps `write_to_csv` at 25 lines (T012). |
| A-04 | Medium | The new PR comprehension has executable lines without same-line comments. The new transformation has no info log before it and no debug log after it. | PR #4813 patch for `data_exporter.py` at hunk 405 | T011, T012, and T015 add comments and logs. |
| A-05 | Medium | The legacy record has no `analysis.md`. | RC-56 | This file is the required `analysis.md`. |
| A-06 | Medium | The legacy quickstart holds no exact commands. | RC-57 | `design/quickstart.md` lists each command. |
| A-07 | Medium | The issue names `tests/unit/websocket_streams/web/hardware/test_report.py`. The file is absent on `main` and on the PR branch. | RC-28, RC-29, RC-30 | D-7. The record uses tests that exist on `main`. |
| A-08 | Low | The legacy plan records its constitution check as prose. The brief asks for each rule with a result. | Legacy `plan.md` lines 22 to 33 | `plan.md` gives a result for each rule. |
| A-09 | Low | The PR docstring of `escape_multiline` says the function is for CSV compatibility. The function now serves every backend. | PR #4813 patch for `data_processing_utils.py` | T010 updates the docstring. |
| A-10 | Info | List values keep line feeds raw after the join. This behavior exists on `main` and in the PR tests. | RC-70 | Out of scope (FR-006). Recorded in U-7. |
| A-11 | Info | The SQLite writer passes its caller rows to `escape_multiline`. The function changes the caller rows in place. | RC-01, RC-10 | Pre-existing. D-4 covers the CSV path only. Recorded in U-8. |

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T001, T009, T010 | T003, T009 |
| FR-002 | T011, T012 | T004, T005 |
| FR-003 | T012, T013 | T005, T006 |
| FR-004 | T011, T012 | T004, T005 |
| FR-005 | T008, T013 | T007, T008 |
| FR-006 | T010 | T003 and the existing list-value test in the same file (RC-21) |
| FR-007 | T003 | T003 |
| FR-008 | T015 | `pylint src/ --fail-under=9.5` and the reviewer check |
| FR-009 | T014 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-010 | T002 | `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` |

Every requirement maps to at least one task and at least one test or check.

## Constitution Alignment

`plan.md` holds the rule-by-rule result table. The table has no FAIL result. Debt for existing violations appears in `plan.md` Complexity Tracking with remediation R-1, R-2, and R-3.

## Legacy Record Review (PR #4813 Branch)

The legacy record stays on the PR branch. This table counts its factual claims against the PR head and `main`. Claims that depend on unverified tests or containers are excluded.

| ID | Result | Legacy claim | Evidence |
| - | - | - | - |
| L-01 | verified | Shared helper has 69 call sites in 53 source files. | Local count at commit `f03c6c9`, which equals remote `main`. The five locally modified files hold no call site. |
| L-02 | verified | Shared line feed escaping stays in use. | RC-01 |
| L-03 | verified | The SQLite writer escapes rows before storage. | RC-10 |
| L-04 | verified | Shared classes already exceed the limits, and the change adds no class or module. | RC-03, RC-09 |
| L-05 | verified | The held hardware report stays unchanged. | RC-16 and the PR file list, which has no `csv_file.py` |
| L-06 | verified | New tests use temporary paths. | PR #4813 patch for `test_data_exporter.py` |
| L-07 | verified | CSV writing copies the records before escaping. | PR #4813 patch for `data_exporter.py` |
| L-08 | verified | The changelog fragment carries the issue name. | RC-32 |
| L-09 | verified | The managed route holds the feature records. | PR #4813 file list |
| L-10 | stale | The plan says no new structural violation is needed. | RC-58 |
| L-11 | absent | The record includes `analysis.md`. | RC-56 |
| L-12 | absent | The CSV change covers all CSV output. | RC-11, RC-12, RC-13 |
| L-13 | absent | The quickstart gives exact verification commands. | RC-57 |

Totals: 9 verified, 1 stale, 3 absent. The totals match `existing_record` in the STATUS file.

## Unmapped Tasks

None. Each task names at least one requirement or success criterion.

## Metrics

| Metric | Value |
| - | - |
| Requirements (FR) | 10 |
| Success criteria (SC) | 6 |
| Tasks | 19 |
| Tests planned | 14 |
| Remote checks | 71 |
| Decisions | 15 |
| Human decisions | 0 |
| Files changed | 12 (4 added, 8 modified) |

## Unresolved Items

- U-1: Principle IV steps 10 to 12 follow T-MERGE. The orchestrator owns the main build, the revision check, and the deployment.
- U-2: Issue #4773 may route EX rows through the shared path. The EX contract needs an owner review before that change merges.
- U-3: The issue names a test path that does not exist. The issue owner must name the file that runs the reproduction.
- U-4: The three classes and two folders above the limit need remediation issues (R-1 and R-2).
- U-5: Stored database rows keep their earlier values. No migration is planned.
- U-6: Primary key strategy fields were not read. T-PR checks each key field before the push (R-10).
- U-7: List values keep raw line feeds. A separate issue can decide whether they need escaping.
- U-8: The SQLite writer changes its caller rows in place. A separate issue can remove that side effect.
