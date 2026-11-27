# Specification Analysis Report: Black Gate Failure From the Mando Pin

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| F-1 | High | Pull request #4888 raises a pinned transitive package without a new lock. | R-02, R-16, R-17, R-51 | Do not merge. Keep mando at 0.7.1 (D-2, D-4). |
| F-2 | High | The Black job name hides a pip failure. The Black format check never runs. | R-07, R-52 | Record the step evidence (D-1). No workflow change (D-8). |
| F-3 | Medium | Pull request #4888 would also fail the lock guard and the export guard after pip succeeds. | R-14, R-15, R-16. Unverified: U-4. | Keep the pin unchanged (D-5). |
| F-4 | Medium | Dependabot can propose mando 0.8.x again after pull request #4888 closes. | R-20 | Add the ignore rule (D-3). |
| F-5 | Medium | The changelog rules conflict. The constitution requires a fragment for each change. The README says to add none for an internal-only change. | R-26, R-27, R-28, R-25 | Add the fragment (D-7). The owner reconciles the rules. |
| F-6 | Low | Grandfathered five-children debt exists in `changelog.d\` and `tests\guardrails\`. The lock guard module now holds 11 top-level names. | R-30, R-31 | Record in plan Complexity Tracking. Remediation is a separate issue. |
| F-7 | Low | Fourteen sibling gate issues stay open while pull request #4888 stays open. | R-58. Unverified: U-5. | Owner action (U-5). |
| F-8 | Info | Twenty-six of 28 failed jobs show the same resolver conflict. Two jobs failed on upstream results. | R-55 | No more work for this issue beyond the pin fix. |
| F-9 | Info | Main passes all 33 jobs in run 45774119357. | R-56, R-57 | Use main as the baseline for SC-001 and SC-002. |

Caution: merging pull request #4888 stops the install step in each job that installs `requirements-dev.txt`. A revert restores the install, but the failed runs stay in the history.

## Coverage Summary

| Requirement | Task | Test or check | Status |
| - | - | - | - |
| FR-001 | T004, T-PR | Remote rows R-52 to R-55 | Verified-present (remote) |
| FR-002 | T005 | `test_lock_satisfies_every_requirement` at line 68 of the lock guard | Open until run |
| FR-003 | T002 | First new test, `DependabotPolicy` samples | Open until run |
| FR-004 | T002 | First new test, `DependabotPolicy` samples | Open until run |
| FR-005 | T001 | Second new test, negative case | Open until run |
| FR-006 | T-MERGE | `test_lock_satisfies_every_requirement` on updated main | Open until merge |
| FR-007 | T003 | `test_changelog_fragment_policy.py`, `ISSUE_NAME` rule at line 39 | Open until run |
| FR-008 | T004 | `test_process_folder_structure.py` line 133 and `test_spec_route_contract.py` line 464 | Open until run |
| FR-009 | T-LOCAL-GATES, T-PR | Local gate table in `plan.md` | Open until run |

Every requirement maps to at least one task and one test or check. No task lacks a requirement.

## Constitution Alignment

- Five-item rule: passes for new directories. Two grandfathered folders receive no new direct child (R-30, R-31). The touched module records its debt in `plan.md`.
- Class-based architecture: passes. The new logic lives in `DependabotPolicy`.
- Safety-first input: passes. The guard reads fixed repository files only.
- Full deployment pipeline: passes with the stated exceptions in `plan.md`.
- Inline comments and action logging: each new code line and read carries the required comment and log.

## Unmapped Tasks

None. Every task maps to at least one requirement.

## Metrics

- Failed jobs in run 45064243269: 28. Resolver conflict: 26. Downstream aggregator failures: 2.
- Sibling gate issues open: 14.
- Remote checks recorded: 96.
- Requirements: 9. Tasks: 9. Tests planned: 2. Decisions: 12. Human decisions: 0.
- Markdown files in the record: 10. Changelog fragments added: 1.

## Convergence After Implementation

- `main` keeps mando 0.7.1 and stays green (F-9).
- The pip entry carries the ignore rule (T002).
- Dependabot does not propose mando 0.8.x while radon 6.0.1 stays the dev pin.
- Pull request #4888 stays open until the owner acts (U-2, U-5).

## Unresolved Items

- U-a. Owner: close or keep pull request #4888. The owner uses the Dependabot tools after this change merges. Evidence: R-24, D-4.
- U-b. Owner: reconcile the changelog README with the constitution. Evidence: R-26, R-28.
- U-c. Maintainer: remediate the grandfathered five-children debt in `changelog.d\`, `tests\guardrails\`, and the lock guard module. Evidence: R-30, R-31, F-6.
- U-d. Implementer: confirm after merge that Dependabot accepts the `versions` range. Evidence: R-45. Unverified: U-1.
- U-e. Owner: confirm that the sibling issues close when pull request #4888 closes. Unverified: U-5.
