# Specification Analysis Report: Top-Five Complexity Target Map

## Findings

| ID | Type | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - | - |
| A1 | Defect | High | The target map names `MistHelper.py` for all five targets. Four targets now live in other files. The lookup stops at the first missing target. | R01, R05 to R08, R09 to R13 | D-1, task T003 |
| A2 | Gap | High | No test checks the file of each target. The integration module checks only that each name is callable. | R14 | FR-004 and guard test 1, task T002 |
| A3 | Gap | High | No CI job runs the utility. The CI radon job covers the `RADON_PATHS` list, which does not include this script. | R17, R18, R19 | D-7 |
| A4 | Consistency | Medium | Spec-195 marks the utility complete (R45). Its target map still names `MistHelper.py` for four targets that moved. | R45, R01 | The spec-195 record stays unchanged. This record documents the drift. |
| A5 | Consistency | Low | The issue carries the `ci` label, but the utility is not a CI step. The timeout test imports the utility, so pytest loads it. | R16, R17 | No CI change (D-7). The label stays on the issue. |
| A6 | Debt | Medium | `main()` holds seven logical blocks and 26 lines. Its estimated CC is 13. The CI radon gate does not cover this file. | R26, R18, U-2 | Follow-up issue. Task T-LOCAL-GATES records the actual output. |
| A7 | Debt | Medium | The utility uses module-level functions, which Principle II forbids for production code. | R38 | Follow-up issue (D-6). |
| A8 | Debt | Low | `main()` and `_run_radon()` have no action logging. Several lines lack inline comments. | R35, R36 | Follow-up issue (D-6). |
| A9 | Conflict | Medium | The changelog README omits fragments for internal-only changes. The constitution requires one fragment for each change. | R29, R41 | D-9 adds one fragment. |
| A10 | Conflict | Low | The agent instructions name the fragment `pr-<number>.md` after the pull request exists. The README keeps the first name. | R43, R28 | D-8 keeps the issue name. |
| A11 | Process | Medium | Principle IV steps 10 to 12 assume that a product image builds. The container build runs only for product paths. | R40, R21 | D-10 records the steps as not triggered. |
| A12 | Behavior | Low | An uncaught exception ends the utility with a traceback and a non-zero exit code. A FAIL result also ends with a non-zero exit code. | R47, R48 | Kept as is. The contract records the ambiguity. |
| A13 | Risk | Low | The fix runs radon four times instead of once. The added run time is not measured. | U-3 | Task T004 records the run time. |
| A14 | Duplication | Info | The canonical target names appear in the integration test and in the fixture. | R14, R15 | Accepted. No change in this issue. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 map each target to its file | T002, T003 | Guard test 1 |
| FR-002 complete with PASS or FAIL | T002, T004 | Guard test 2 |
| FR-003 exit 0 for PASS and 1 for FAIL | T002, T004 | Guard test 3 |
| FR-004 name the target and file when absent | T002 | Guard test 1 |
| SC-001 five result lines | T004 | Manual run, recorded |
| SC-002 guard test fails before and passes after | T002, T003 | Guard test 1 |
| SC-003 five tests pass in the module | T-LOCAL-GATES | Module run |
| SC-004 no module-level name changed | T003, T-LOCAL-GATES | `symbol-diff` |

Every requirement maps to at least one task and at least one test. Three tests are planned, which matches `tests_planned` in STATUS.json.

## Constitution Alignment

Principle I, II, IV, VI, and VII show recorded debt or a documented exception. Each exception appears in `plan.md`, Complexity Tracking, and in D-6, D-7, and D-10. No rule fails without a recorded reason.

## Unresolved Items

- U-1: exact CC values of the five targets. Task T004 records them.
- U-2: CC of `main()`. The estimate is 13. A follow-up issue confirms the measured value.
- U-4: result of the test-quality analyzer. Task T-LOCAL-GATES records it.
- U-5: result of the CI integration shard. Task T-REMOTE-CI records it.

## Metrics

- Remote checks: 48 in STATUS.json, 48 rows in research.md, and 48 in the summary.
- Tasks: 10. Requirements: 4. Tests planned: 3. Decisions: 11. Human decisions: 0.
- Route: `0\0\1\2\3\3\2\2`, which equals the base-5 digits of 4837 padded to eight digits (R30, R31).
