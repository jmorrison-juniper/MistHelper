# Specification Analysis Report: Quality gate failure from the mando 0.8.2 pin

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/quickstart.md`, the remote evidence in `design/research.md`, and the constitution (version 1.9.0).

**Method**: A read-only review of the CI log, the remote tree, the pull request, and the local guard tests. No test, linter, or install ran in the spec phase.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A-1 | Defect in existing work | HIGH | Pull request #4888, `requirements-dev.txt` line 179 (R11) | The pull request pins `mando==0.8.2`. Radon 6.0.1 requires `mando` below 0.8 (R10, R41). The install step fails for 26 jobs (R03, R04). | Resolved by D-1. Main keeps `mando==0.7.1`. |
| A-2 | Defect in existing work | HIGH | Pull request #4888 file list (R06) and `requirements-dev.txt` line 1 (R48) | The pull request edits a file that `uv export` generates. `uv.lock` still pins `mando` 0.7.1 (R18). The export guard compares the file with the lock output (R17), so the guard fails even when pip resolves. | Resolved by D-1. The guard result on the pull request content is unverified (U-5). |
| A-3 | Defect in dependency metadata | MEDIUM | Commit `e86098cd` (R08) and `requirements-dev.txt` line 180 (R11) | Dependabot records `mando` as `direct:development`. The pinned line marks `mando` as transitive with `# via radon`. | Recorded. D-2 blocks the update. The Dependabot classification is outside this change. |
| A-4 | Consistency | MEDIUM | `tests/guardrails/test_pr_title_workflow.py` lines 18 to 29 and 284 (R22, R23) | A new `ignore` entry in the pip stream fails the complete-policy comparison unless the snapshot changes too. | Resolved by T004. |
| A-5 | Conflict in governing text | LOW | `changelog.d/README.md` line 58 (R25) and constitution line 409 (R28) | README rule 4 says add no fragment for an internal-only change. The constitution says each change adds one unique fragment. | Resolved by D-4. The constitution governs (R29). The owner may align the README wording in a separate change. |
| A-6 | Unresolved | MEDIUM | PyPI index (R40) and the upstream source (U-1) | No radon release accepts `mando` 0.8. The ignore rule and the pin test stay until a release exists. | Open. The owner checks radon releases before the rule is removed. |
| A-7 | Unresolved | MEDIUM | `changelog.d/` direct children (R27) | The folder holds 335 direct children. The constitution allows the fragment as a direct child (R28). This is existing debt. | Recorded in `plan.md` Complexity Tracking. A separate remediation issue is required. |
| A-8 | Consistency | LOW | Issue body (commit `5bb4b385`, R07) and run head (`e86098cd`, R01) | The issue names a test-merge commit. The run head is the pull request head. | Recorded in `spec.md` Issue Facts. No fix needed. |
| A-9 | Coverage | LOW | Jobs `pytest (coverage gate)` and `E2E smoke tests` (R05) | Both jobs fail only because upstream jobs failed. They pass only when the upstream jobs pass. | Covered by T-REMOTE-CI. |

## Coverage Summary

| Requirement | Has task | Task IDs | Tests and checks |
| - | - | - | - |
| FR-001 | Yes | T001 | Quickstart section 1, log lines 561, 565, and 574 |
| FR-002 | Yes | T002, T-LOCAL-GATES | Test targets 4 and 5, and the unchanged-file check in quickstart section 3 |
| FR-003 | Yes | T003, T004 | Test target 1, the complete-policy test |
| FR-004 | Yes | T005 | Test target 2, the pin test |
| FR-005 | Yes | T006 | Test target 3, the fragment guard |
| FR-006 | Yes | T007 | STE gate in quickstart section 3 |
| FR-007 | Yes | T-LOCAL-GATES | Quickstart sections 3 and 4 |
| FR-008 | Yes | T-PR, T-REMOTE-CI | Quickstart section 6, the pull request body and the required checks |
| FR-009 | Yes | T-MERGE | Quickstart section 6, the state of pull request #4888 |
| FR-010 | Yes | T-MERGE | Process check: the orchestrator authorizes the action. No automated test covers this rule. |

| Success criterion | Verified by |
| - | - |
| SC-001 | T001 |
| SC-002 | T-LOCAL-GATES, test targets 1 to 5 |
| SC-003 | T-REMOTE-CI |
| SC-004 | T-LOCAL-GATES, unchanged-file check |
| SC-005 | T-MERGE |

## Unmapped Tasks

None. Each task maps to at least one requirement or success criterion.

## Constitution Alignment

The constitution check in `plan.md` has no failed row. Its one recorded debt item is the `changelog.d/` folder (A-7). The change adds one unique fragment, as the constitution allows (R28). The change adds no direct child to a noncompliant parent. The record folder sits in a route leaf that holds no entries (R36).

## Metrics

| Metric | Value |
| - | - |
| Functional requirements | 10 |
| Success criteria | 5 |
| Tasks | 11 |
| Test targets | 5 |
| Remote checks | 51 |
| Decisions | 6 |
| Human decisions | 0 |
| Unverified items | 7 |
| Findings | 9 |

## Convergence After Implementation

After the change merges, the install step should pass for each of the 26 jobs named in A-1. The two downstream jobs in A-9 should then pass. Dependabot should stop proposing mando minor and major updates. Each claim is checked by task T-REMOTE-CI and task T-MERGE. Three items remain open after the merge: A-6, A-7, and the Dependabot behavior in U-2 and U-3.
