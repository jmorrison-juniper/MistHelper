# Specification Analysis Report: Operator Guide Operation Count

This report checks the spec, the plan, and the tasks against the remote code on `main`. Each R-number points to `design/research.md`.

## Findings

| ID | Finding | Evidence | Disposition |
| - | - | - | - |
| A-1 | Issue #4915 states that the generated menu reference lists menus up to 308. The reference lists 308 actionable menu operations, numbered 1 to 309. | R-03, R-05 | Defect in the issue text. The fix removes the count, so it does not depend on the number. The spec records the answer in its clarifications. |
| A-2 | The operator guide states `303 operations` and `numbered 1 to 304`. | R-01 | Defect in the guide. Task T003 removes the sentence. |
| A-3 | The wiki home page states 269 actionable menu operations. | R-12 | Defect outside this issue. Decision D-5 keeps it out of scope. A follow-up issue is recommended. |
| A-4 | PR #4918 removed the operation count from the README. The copilot instructions and the constitution still tell authors to update the README operation count. | R-13, R-11, R-14. Pull request #4918 body and files list (source: `gh pr view 4918`). | Defect outside this issue. The governed instruction files need an owner review. A follow-up issue is recommended. |
| A-5 | Continuous integration does not grade the operator guide with the STE gate. The local STE row in the copilot instructions also omits the guide. Pre-commit grades the guide on each developer machine. | R-47, R-68, R-49 | Accepted for this change. T-LOCAL-GATES runs the STE gate on the guide. D-5 defers the continuous integration gap to a follow-up issue. |
| A-6 | The quality gates page says the STE workflow grades that page. The workflow file lists five files, and the page is not one of them. | R-60, R-47 | Defect outside this issue. A follow-up documentation fix is recommended. |
| A-7 | Principle IV steps 10 to 12 cannot run for a documentation-only change. The build paths exclude the guide, and the image excludes the documentation folder. Principle IV also says that no step may be skipped. | R-18, R-19, R-20, R-56, R-57, R-58 | Conflict recorded. Decision D-6 records the exception. The orchestrator confirms it. A constitution clarification is a follow-up. |
| A-8 | Folder debt: `changelog.d` holds 335 direct children, and `tests/guardrails` holds 79. | R-81, R-82, R-16 | Debt recorded in `plan.md`, as Principle I requires. A remediation issue is the follow-up action. |
| A-9 | A count written in words, such as `three hundred operations`, passes the guard. | Spec edge case. | Accepted residual risk. The menu reference stays the source of the count. |
| A-10 | Issue #4917 is open. It reports 23 failing guardrail tests on a Windows workstation. | GitHub issue view, `gh issue view 4917` (open, title verified). | T-LOCAL-GATES compares any failing guard with that report. A new failure blocks the change. |
| A-11 | The pre-commit STE hook excludes `specs/`. The record files get no hook check. | R-49 | T-LOCAL-GATES runs ste-linter on each record file by name. |
| A-12 | The route levels stay within five children. The route target does not exist yet. | R-83, R-84, R-85 | No defect. T005 copies the record after checking these counts. |
| A-13 | Issue #4155 closed on 2026-10-09 with the same stale count. The count returned. | GitHub issue view, `gh issue view 4155` (closed, closedAt verified). | D-1 removes the source of the drift. The guard test detects a repeat. |
| A-14 | T-PR, T-REMOTE-CI, and T-MERGE verify with GitHub commands. The local gates table has no row for them. | R-52, R-53 | Documented exception to the verification rule. The commands come from the workflow rows in the copilot instructions. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001: no operation count in the guide | T002, T003 | `test_operator_guide_defers_the_count_to_the_menu_reference` (count check) |
| FR-002: link to the menu reference | T002, T003 | The same test (link check and target check) |
| FR-003: STE score of 80 or above | T-LOCAL-GATES | ste-linter command, both modes (Scenario 4) |
| FR-004: no generator input or generated page changes | T-LOCAL-GATES | Menu reference drift check and git diff (Scenario 6) |
| FR-005: one Fixed fragment | T004 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-006: neighboring guards pass | T-LOCAL-GATES, T-REMOTE-CI | `test_hardware_shell_lock_docs.py`, `test_metrics_gateway_container_contract.py` (Scenario 8), and CI (R-41) |
| FR-007: guard fails before the edit and passes after | T001, T002, T003 | The guard test, run before and after T003 (Scenarios 2 and 3) |
| FR-008: record passes the structure and route guards | T005 | `test_process_folder_structure.py`, `test_spec_route_contract.py` (Scenario 7) |

Every requirement maps to at least one task and at least one test.

## Constitution Alignment

`plan.md` lists each rule and its result. One rule fails: Principle IV steps 10 to 12 (A-7). The decision D-6 records the exception.

## Unmapped Tasks

None. Each task names at least one requirement.

## Metrics

- Requirements: 8 (FR-001 to FR-008).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 9.
- Planned test functions and methods: 78. One is new. The other 77 are existing cases in the six guard modules that Scenarios 2 to 8 run.
- Remote checks: 92 (R-01 to R-92). Each one appears in the remote verification table of `design/research.md`.
- Decisions: 8 (D-1 to D-8).
- Human decisions required: 0.
- Unverified items: 6 (see `design/research.md`).

## Convergence After Implementation

The implementer confirms each item before the pull request opens.

1. `documentation/operator-guide.md` holds no `operations` count and no `numbered 1 to` range.
2. The guard test failed once before T003 and passed after T003.
3. The guide, the fragment, and each record file score 80 or above in ste-linter, in the structural mode.
4. The fragment name is `issue-4915-operator-guide-count.md`, and it holds one Fixed bullet.
5. The menu reference and the wiki copy have no diff after the generator runs.
6. The record folder sits at `specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count`.
7. The pull request title passes the Conventional Commits check, and the body holds `Closes #4915`.
8. The STATUS counts still match the research table: 92 remote checks, 8 decisions, 0 human decisions.
