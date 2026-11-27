# Specification Analysis Report: Radon Job Mando Pin Conflict

## Consistency Review

| ID | Area | Finding | Evidence | Disposition |
| - | - | - | - | - |
| A-01 | Issue title and check | The issue names the radon gate. The check failed at the install step, and the complexity step was skipped. | R-05, R-06 | The record names the install step as the failing step. The issue title stays as filed. |
| A-02 | Commit in the issue | The issue cites `5bb4b385`, the test merge commit. The run head is `e86098cd`, the PR head. | R-04, R-13 | Both commits appear in the record. Both hold the same `ci.yml` blob. |
| A-03 | PR file set | PR #4888 changes only `requirements-dev.txt`. `uv.lock` keeps mando 0.7.1. | R-11, R-16, R-20 | A second defect exists. After the install step passes, the lock guard test fails for mando 0.8.2 against the locked 0.7.1. |
| A-04 | Guard coverage | The declaration parity guard treats only `misthelper` annotations as direct. Mando carries `# via radon`. | R-21 | No guard checked the radon constraint before this change. FR-002 and FR-003 close this gap. |
| A-05 | Hidden gate results | 26 of 28 failed jobs failed in an install step. Two jobs failed in verification steps that read earlier results. | R-06, R-07 | The fix restores the install. The structural gap stays out of scope (`spec.md`, Out of Scope). |
| A-06 | Governance conflict | The constitution requires one fragment for each change (R-29). The changelog README exempts internal-only changes (R-34). | R-29, R-34 | D-6 follows the constitution. The orchestrator should align the two documents. |
| A-07 | Recurrence | Closed issue #4690 records an earlier radon install conflict. It cites a pyee and Playwright conflict. Its author closed it as a duplicate of #4686. | GitHub issue #4690 comment | The record names the pattern. A separate issue should split install failures from gate results. |
| A-08 | Sibling issues | Issues #4891 through #4905 cite PR #4888 and the same run. Each names a different gate. | GitHub issue list (read-only) | D-8. The orchestrator closes them after PR #4888 closes. |
| A-09 | Main status | The radon job passed on main in run 45774119357. | R-08 | No change to the complexity rule (FR-009). |
| A-10 | Mist API and SDK | Not applicable. The issue names no Mist endpoint and no `mistapi` call. | `spec.md`, Out of Scope | None. |

## Defects in Existing Work

- The Dependabot update for mando changed a package that radon pins. The change did not check the radon requirement (A-03, A-04).
- Dependabot has no ignore rule for mando. The bump could recur each week (R-18).
- The constitution and the changelog README disagree on fragments (A-06).

## Unresolved Items

- The sibling issues #4891 through #4905 need a decision after PR #4888 closes (D-8).
- PRs #4886, #4889, and #4890 and their issues #4906 through #4908 were not examined.
- The native Windows checks on PR #4888 come from other workflows. They were not examined.
- The live Dependabot docs page was not fetched. The github/docs source at a pinned commit replaces it (`design/research.md`, U-01).
- A split of install failures from gate results needs a new issue. The orchestrator files it.

## Coverage Summary

| FR | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T005 | TST-03, TST-04 |
| FR-002 | T001, T006, T007 | TST-01, TST-02 |
| FR-003 | T006, T007 | TST-03, TST-04 |
| FR-004 | T-MERGE | V-01 |
| FR-005 | T003, T004, T-PR | V-02 |
| FR-006 | T-PR | V-02 |
| FR-007 | T008, T-PR | V-04 |
| FR-008 | T002, T-REMOTE-CI | V-03 |
| FR-009 | T-PR | V-05 |
| FR-010 | T001, T-LOCAL-GATES | V-04 |

TST-01 to TST-04 are the four guard tests. V-01 to V-05 are the acceptance checks in `design/quickstart.md`. The total is 9 tests planned.

## Consistency Checks

- Requirements: 10 (`spec.md`). Tasks: 12 (`tasks.md`). Every requirement maps to at least one task and one test or check.
- Remote checks: 55. The count in `design/research.md` and in the STATUS file match. The summary repeats the count.
- Four final tasks exist: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- Every task names exact repository paths or states that no repository path applies. Every task names one command from the local gates table.

## Constitution Alignment

The record follows Principle I. It adds no direct child to a noncompliant parent. It follows Principle II. It adds classes, not wrappers. It follows the escalation rule (R-30). The constitution Documentation section governs the fragment (R-29), and D-6 records the override of the README exemption.
