# Specification Analysis Report: Count export write results

Scope: `spec.md`, `plan.md`, `tasks.md`, the files under `design/`, and the remote code on `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Findings

| ID | Severity | Finding | Location | Disposition |
| - | - | - | - | - |
| A-1 | Critical | `CountExporter._persist` discards the writer result. It prints the success notice after a false result. | `count_exporter.py` lines 212 to 216 (research rows 1 and 2) | Fixed by T002. |
| A-2 | Medium | The `MistHelper.py` comment states 70 count endpoints. The three tables hold 72. | `MistHelper.py` line 585 (row 22) | Out of scope (D-12). Separate documentation issue. |
| A-3 | Medium | The `mistapi` pin text in `copilot-instructions` says `>=0.64.0`. `pyproject.toml` says `>=0.64.1`, and `requirements.txt` pins `==0.64.1`. | rows 38, 41, and 42 | Out of scope (D-10). Both pins stay unchanged. |
| A-4 | High | Other writer call sites ignore the result in the same way. A local search found 139 such lines in 71 files. | Unverified item U-5 in `design/research.md` | Out of scope (D-4). Separate audit issue. |
| A-5 | Low | The root-logger calls in `_resolve` and `_run` bypass the module logger. | `count_exporter.py` (not cited by line) | Out of scope. |
| A-6 | Medium | Issue #4717 stayed open on 2026-11-26, seven days after PR #4847 merged. Its closing reference may have been missing. | `gh issue view 4717` state read on 2026-11-26 | T-PR adds `Closes #4720`. T-MERGE checks the issue state. |
| A-7 | Medium | `tests/unit/export/` (55 children) and `src/operations/exporting/export/` (49 children) are noncompliant parents. | rows 53 and 54 | Grandfathered by Principle I. Separate remediation issue. |
| A-8 | Low | The local count tables match the stated total of 72 operations. The generated menu reference states 37, 32, and 3. | `count_exporter.py` lines 51, 91, and 126 (rows 6 to 8). `documentation/menu_reference.md` lines 271 to 273 (row 30). | Consistent. No change. |
| A-9 | Medium | Open pull request #4813 changes `data_exporter.py`. This change reads that file and relies on its bool contract. | Open PR list read on 2026-11-26 | Risk R1 in `plan.md`. Rebase before T-PR. |

## Coverage Summary

| Requirement | Task | Test or verification |
| - | - | - |
| FR-001 | T002 | T001 cases with `False`, `None`, and `True` |
| FR-002 | T002 | T001 failure cases assert the error line text |
| FR-003 | T002 | T001 failure cases assert the `! Write failed for` prefix |
| FR-004 | T002 | T001 failure cases assert no `records exported to` text |
| FR-005 | T002 | T001 `True` cases assert the success notice text |
| FR-006 | T002 | T001 empty-response case asserts no writer call |
| FR-007 | T002 | T001 raised-error case asserts no success notice |
| FR-008 | T002 | T001 logging-order case asserts the info line precedes the success notice |
| FR-009 | T002 | Manual review item CHK-003 in `design/checklists/operator-output.md` |
| FR-010 | T002 | T003 contract guard and the existing persist test |
| FR-011 | T002 | T001 cases cover organization, site, and MSP |
| FR-012 | T001 | SC-001 run on unchanged source |
| FR-013 | T001 | Manual review item CHK-005 in `design/checklists/operator-output.md` |
| FR-014 | T001 | `git diff --name-status origin/main -- tests/unit/export` shows one `M` line |
| FR-015 | T006 | Symbol gate, and `git diff --name-only` shows no writer or registry path |
| FR-016 | T004 | STE gate, and manual review item CHK-006 |
| FR-017 | T005 | Changelog fragment guard test |
| FR-018 | T-LOCAL-GATES | `git diff --name-only` shows no `README.md` line |
| FR-019 | T-PR | Route check in `design/quickstart.md` Scenario 9 |
| FR-020 | T-PR | Child count check in `design/quickstart.md` Scenario 10 |
| FR-021 | T-LOCAL-GATES and T007 | Gate list in `design/quickstart.md` Scenario 8, and the test-quality ratchet |
| FR-022 | T-PR and T-REMOTE-CI | Hold recorded in `spec.md` clarifications, and no publication step runs |
| FR-023 | T-MERGE | `gh pr view` state check, after orchestrator authorization |

FR-009, FR-013, and FR-016 rely on a manual review item, because the local gates table has no automated comment or mock check. FR-014, FR-015, FR-018, and FR-020 rely on a command output, not a pytest case.

## Constitution Alignment

All seven principles pass in `plan.md`. Principle I passes, because the change adds no child to a noncompliant parent. The two folder debts are recorded in the Complexity Tracking table, with one separate remediation action.

## Unmapped Tasks

None. Each of the eleven tasks maps to at least one requirement.

## Metrics

| Metric | Value |
| - | - |
| Functional requirements | 23 |
| Success criteria | 6 |
| Tasks | 11 |
| Planned regression cases | 12 |
| Remote checks | 63 |
| Decisions | 14, with 0 human decisions |
| Findings | 9 |

## Unresolved Items

1. The publication and merge hold, which the issue owner must lift (D-7).
2. The other writer call sites, which need an audit issue (D-4).
3. The `mistapi` pin text drift in `copilot-instructions` (D-10).
4. The stale comment at `MistHelper.py` line 585 (D-12).
5. The two folder debts recorded in `plan.md` (Complexity Tracking).
6. The FR-009 comment review, because no automated gate checks inline comments.

## Convergence After Implementation

After T002, the count of unassigned writer call lines in the local tree drops by one, because `count_exporter.py` line 212 stores its result. The other 138 lines stay unchanged until the audit issue lands.
