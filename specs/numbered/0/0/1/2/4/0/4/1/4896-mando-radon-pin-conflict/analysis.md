# Specification Analysis Report: Mando pin conflict in the pip-audit gate

This report checks the spec, the plan, the tasks, and the remote code against each other. Each finding cites the remote rows in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-1 | High | The issue body frames the failure as a CVE finding. The CVE scan never ran. | Step 5 failed, and step 6 was skipped (R-03, R-05). | The spec names the install failure as the cause (spec, Clarifications). |
| A-2 | High | Pull request #4888 changes only `requirements-dev.txt`. The lock still holds mando 0.7.1. The export guard and the lock guard would also reject mando 0.8.2. | R-02, R-20, R-25, R-26, R-27, R-28. The rejection is inferred from the code and was not run. | Decision D-1 keeps the pin at 0.7.1. |
| A-3 | High | The Dependabot pip entry holds no ignore rule, so the conflict recurs. | R-22, R-23, R-45. | Decision D-2 adds the rule. |
| A-4 | Medium | The issue cites commit 5bb4b385, which is a merge commit. The run head is commit e86098cd. Both commits exist. | R-07, R-08. | The research cites both commits. |
| A-5 | Medium | Repository documents disagree on the container build trigger. Line 420 says any push to main. Line 473 says a product-file change. The workflow filters on product paths, and the auto-merge dispatch starts the build after each merge. | R-52, R-53, R-55, R-64, R-68. | Decision D-8 follows the workflow files. The documentation conflict needs a separate issue. |
| A-6 | Medium | The changelog README skips fragments for internal-only changes. The constitution requires one fragment for each change. | R-32, R-33. | Decision D-6 follows the constitution. |
| A-7 | Medium | `tests/guardrails` holds 79 tracked entries on main. The local checkout holds 80, because of `__pycache__`, which is absent from the main tree. | R-30, and the local listing. | The main count governs. FR-012 forbids a new direct child. |
| A-8 | Low | Radon 6.0.1 is the newest release on PyPI. Radon may receive no fix for later conflicts. | R-47. | The range check fails closed for an unknown radon version (TC-3). A separate issue tracks a replacement. |
| A-9 | Low | Fifteen quality-gate issues name pull request #4888. Their closure rule is not confirmed for pull request issues. | R-44, R-38, U-3. | The owner verifies the closure after T-MERGE. |
| A-10 | Low | The guard test for the Dependabot rule depends on the YAML shape of the file. | TC-4 reads `.github/dependabot.yml` with `yaml.safe_load`. | TC-4 checks the rule and not the file layout. |
| A-11 | Info | Pull request #4673 failed at the same install step. | R-45. | Decision D-2 covers recurrence. A general resolver check is a follow-up (spec, Non-Goals). |

## Coverage Summary

| Requirement | Tasks | Test or check | Evidence |
| - | - | - | - |
| FR-001 | T001, T-LOCAL-GATES, T-REMOTE-CI | TC-1 and the remote check `pip-audit (CVE scan)` | R-13, R-43 |
| FR-002 | T001, T003 | TC-1 and TC-2 | R-13, R-15, R-20 |
| FR-003 | T002 | TC-4 | R-22, R-24, R-50 |
| FR-004 | T003 | TC-2 | R-21, R-46 |
| FR-005 | T003 | TC-3 | R-46 |
| FR-006 | T003 | TC-5 | R-22 |
| FR-007 | T006 | The existing guard `test_ci_gate_triggers.py` | R-09, R-29 |
| FR-008 | T006 | Manual review of the diff. No automated test covers a flag. | R-11 |
| FR-009 | T004 | The STE gate on the document | R-36, R-37 |
| FR-010 | T005 | The STE gate on the fragment | R-31, R-32 |
| FR-011 | T-MERGE | Manual check of the proof comment. No automated test covers a closing comment. | R-02 |
| FR-012 | T002, T003 | Manual review of the paths in the diff | R-30, R-69 |

FR-008, FR-011, and FR-012 use a manual check, because no automated check can prove them. The acceptance line of each task states the manual check.

## Constitution Alignment

- Principle I: The change adds no direct child under `tests/guardrails` or `.github`. The fragment is one required record under `changelog.d`. The debt is recorded in the plan.
- Principle II: The new checks are methods of `DependencyLock`. No wrapper function is added.
- Principle III: The change reads files and asserts results. It reads no secret and waits for no input.
- Principle IV: Steps 10 and 11 run in T-MERGE. Step 12 stays with the owner (D-8).
- Principles V to VII: The new code uses ASCII log text, inline comments, and action logging. T003 acceptance states each rule.

## Unmapped Tasks

None. Each task maps to at least one requirement:

- T001 maps to FR-002. T002 maps to FR-003. T003 maps to FR-002, FR-004, FR-005, and FR-006.
- T004 maps to FR-009. T005 maps to FR-010. T006 maps to FR-007 and FR-008.
- T-LOCAL-GATES maps to FR-001 to FR-010. T-PR maps to FR-001, FR-007, and FR-010.
- T-REMOTE-CI maps to SC-001 and SC-004. T-MERGE maps to FR-011 and SC-004.

## Metrics

- Requirements: 12 (FR-001 to FR-012).
- Tasks: 10 (T001 to T006, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Test cases: 5 (TC-1 to TC-5).
- Remote checks: 69 (R-01 to R-69).
- Decisions: 8 (D-1 to D-8). Human decisions: 0.
- Related issues: 15, which are #4891 to #4905 and #4688.
- Unverified items: 12 (U-1 to U-12).

## Unresolved Items

- U-1 to U-12 are listed in `design/research.md`.
- The owner verifies U-2 and U-3 after T-REMOTE-CI and T-MERGE.
- The owner handles the documentation conflict in A-5 and the general resolver check in A-11 in separate issues.

## Convergence After Implementation

1. After T-REMOTE-CI, the check `pip-audit (CVE scan)` reports success. The 26 jobs that logged `ResolutionImpossible` pass their install steps.
2. After T-MERGE, the latest Quality Gates run on main reports success for `pip-audit (CVE scan)`.
3. After T-MERGE, the owner reviews issues #4891 to #4905 for closure (U-3).
4. After T-MERGE, pull request #4888 is closed with its proof comment.
