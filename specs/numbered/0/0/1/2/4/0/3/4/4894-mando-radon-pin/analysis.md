# Specification Analysis Report: Keep mando inside the radon requirement

## Review Scope

This review checks spec.md, plan.md, tasks.md, the research, and the remote code. The remote code is `main` and the head of pull request #4888. GitHub reads used GET requests only.

## Findings

| ID | Category | Severity | Location | Finding | Resolution |
| - | - | - | - | - | - |
| F-01 | Root cause | High | Run 45064243269, job 137338442288, step `Install dependencies` | pip reports that radon 6.0.1 requires mando below 0.8. The pull request pins `mando==0.8.2` at requirements-dev.txt line 179 (RC-05). | D-1 keeps mando at 0.7.1. |
| F-02 | Defect in existing work | High | Pull request #4888, commit e86098cd | Dependabot changed a transitive pin by hand. requirements-dev.txt line 180 reads `# via radon`. The commit message labels mando as `direct:development`. | D-2 closes the pull request. D-3 adds the ignore entry. |
| F-03 | Defect in existing work | High | requirements-dev.txt and uv.lock | The pull request edits the generated export only. uv.lock still locks 0.7.1 (RC-08). The export guard would fail this edit on its own. The guard never ran, because the install stopped first. | D-1 keeps the export equal to the lock. The export guard stays in place. |
| F-04 | Scope | Medium | Run 45064243269, runs 45064235051 and 45064235097 | 28 jobs in run 45064243269 and two Windows jobs stop at an install step. No test runs on the pull request head. | One root cause. The record keeps one issue for the install failures. Head test results stay open in U-03. |
| F-05 | Record discrepancy | Low | Issue body, commit 5bb4b385 | The issue cites 5bb4b385, the pull_request merge commit. The run head is e86098cd. Both commits have tree 38314c25 (RC-01, RC-02). | The record cites both commits. The tested tree is the same. |
| F-06 | Check name | Low | Issue title and the failing checks | The issue names gate `pytest`. The check `pytest (coverage gate)` (job 137338980629) fails at `Verify dependency lock job` (ci.yml line 339). The four shard checks fail at `Install dependencies` (ci.yml line 290). | FR-008 requires both names. |
| F-07 | Policy conflict | Medium | changelog.d/README.md line 58, copilot-instructions line 451, constitution line 409 | The constitution requires one fragment for each change. The README says no fragment for an internal-only change. The copilot-instructions limit fragments to user-visible changes. | D-5 adds the fragment, because the constitution supersedes practice documents (line 529). FR-010 opens Issue A. |
| F-08 | Folder debt | Low | changelog.d (335 files), tests/guardrails (77 files) | The Five-Item Rule debt exists in both folders. The change adds one fragment and no child to tests/guardrails. | D-4 and FR-010 (Issue B). |
| F-09 | Trigger scope | Low | windows-timeout-budget.yml line 14 and windows-audit-report.yml line 14 | Both Windows workflows run on a push when a listed path changes. The fix changes none of those paths. Their checks are absent, not failed. | T-REMOTE-CI excludes them from the acceptance list. |
| F-10 | Pin history | Low | ci.yml comments `(issue #1779)`, issue #1779 | Issue #1779 created the pinned install rule. Its title says unpinned tools can fail CI on an unrelated commit. | Related issue 1779. The rule stays. |
| F-11 | Guard origin | Low | tests/guardrails/test_dependency_export.py line 1 | The guard cites issue #3400. That issue is open. | Related issue 3400. The file keeps its scope and gains a Dependabot class. |
| F-12 | Required checks | Low | Branch protection of main | The branch requires 15 contexts and strict mode (RC-31). `pytest (coverage gate)` is required. `Dependency lock and exports` is not required, but the required gate reads its result. | TC-009 reads that job directly. |
| F-13 | Head result | Medium | Fix pull request head, not yet opened | The CI result of the fix head is unknown. | U-03, resolved by T-REMOTE-CI. |
| F-14 | Style | Low | This record | The record avoids semicolons, contractions, Latin abbreviations, and placeholder words. | The read-only draft validator checks these rules. See the consistency checks. |

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T-REMOTE-CI | TC-001, TC-009 |
| FR-002 | T-LOCAL-GATES, T-REMOTE-CI | TC-009, TC-010, TC-011 |
| FR-003 | T004 | TC-002, TC-003 |
| FR-004 | T003, T004 | TC-002, TC-003 |
| FR-005 | T-PR | TC-008 |
| FR-006 | T005 | TC-006 |
| FR-007 | T-PR | TC-007 |
| FR-008 | T006 | TC-005 |
| FR-009 | T-PR, T-MERGE | TC-004 |
| FR-010 | T007 | TC-012 |

Success criteria: SC-001 maps to TC-009 and TC-010. SC-002 maps to TC-002 and TC-003. SC-003 maps to TC-007. SC-004 maps to TC-008. SC-005 is measured after the first weekly Dependabot run, so no test is planned for it.

## Consistency Checks

| Check | Result |
| - | - |
| Requirements in spec.md, FR-001 to FR-010 | 10. STATUS `requirements` is 10. |
| Tasks in tasks.md, T001 to T007 and four final tasks | 11. STATUS `tasks` is 11. |
| Tests in tasks.md, TC-001 to TC-012 | 12. STATUS `tests_planned` is 12. |
| Remote checks in research.md, RC-01 to RC-36 | 36. STATUS `remote_checks` is 36. The summary states 36. |
| Decisions in research.md, D-1 to D-6 | 6. STATUS `decisions` is 6. Human decisions are 0. |
| Route for 4894 in base 5, eight places | 0 0 1 2 4 0 3 4. This equals the ROUTE value from the brief. |
| Folder limits | The feature root holds 5 children. `design` holds 5. `design/checklists` holds 1. |
| Forbidden tokens and prose semicolons | Checked by the read-only draft validator after the final edit. |

## Unresolved Items

- U-03: CI results of the fix head. T-REMOTE-CI resolves this item.
- U-01: Dependabot handling of ignore entries for security updates. Not verified in this run.
- U-02: Branch state after pull request #4888 closes. Not verified in this run.
- U-04: Coverage and Pylint results of the current head. The install stopped first, so no result exists.
- U-05: Any radon release after 6.0.1. PyPI was read once on 2026-11-26.
- U-06: The cause of the failed upload steps in two E2E jobs. Those logs were not read.
