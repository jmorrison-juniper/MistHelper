# Specification Analysis Report: Dependabot mando pin for the dependency_lock job

## Findings

- **F-1 (defect in pull request #4888)**: The pull request changes `requirements-dev.txt` to `mando==0.8.2`. It leaves `uv.lock` at `mando` 0.7.1 (rows RC-07, RC-13). The lock and the export disagree.
- **F-2 (conflict with radon)**: Radon 6.0.1 requires `mando` below 0.8 (rows RC-48, RC-49). The pip resolver rejects the pull request (row RC-04).
- **F-3 (missing protection)**: The Dependabot pip update block holds no `ignore` entry (row RC-18). Dependabot can raise the same pin on each run.
- **F-4 (commit citation)**: Issue #4903 cites commit `5bb4b385`. That commit is GitHub's test merge commit (row RC-01). The pull request head is `e86098cd` (row RC-02). Both commits exist, so the citation does not block the work.
- **F-5 (documentation gap)**: `documentation/quality-gates.md` omits the `dependency_lock` job from its job list and its table (row RC-23). The gap predates this issue. This change closes the gap for the `dependency_lock` job.
- **F-6 (policy snapshot coupling)**: The policy guard pins the full Dependabot policy (rows RC-20, RC-21). A new `ignore` entry fails the guard until the snapshot changes. The plan includes the snapshot change (T004).
- **F-7 (skipped steps)**: Steps 5 and 6 of the failed job read as `skipped` (row RC-04). The static evidence predicts that both steps would fail on the pull request head (item U-4). The prediction is not observed.
- **F-8 (shared failure)**: Seven sampled jobs show the same resolver error (row RC-05). Fourteen sibling issues cite pull request #4888 (row RC-51).
- **F-9 (missing route)**: The route folder for issue 4903 does not exist on `main` (row RC-35). The route script computes the route (rows RC-33, RC-34). T007 creates the folder.
- **F-10 (no legacy record)**: No legacy record exists (row RC-36). The reuse steps do not apply.

## Coverage Summary

| FR | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T001, T-LOCAL-GATES, T-REMOTE-CI | `tests/guardrails/test_dependency_lock_workflow.py`, and the check "Dependency lock and exports" on the fix head |
| FR-002 | T003, T-REMOTE-CI | `tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy::test_complete_policy` |
| FR-003 | T004 | `tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy::test_unrelated_changes_fail` with the two new rows |
| FR-004 | T002, T-LOCAL-GATES | `tests/guardrails/test_dependency_lock_file.py::test_lock_satisfies_every_requirement`, and `tests/guardrails/test_dependency_export.py::test_requirements_exports_match_the_lock` |
| FR-005 | T006 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-006 | T005 | `ste-linter` on `documentation/quality-gates.md`, and `tests/guardrails/test_complexity_gate_limit.py` |
| FR-007 | T-MERGE | Release check: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state --jq .state` returns `CLOSED` |
| FR-008 | T007 | `tests/guardrails/test_process_folder_structure.py`, and `ste-linter` on the record |

## Constrained-Field Coverage

Not applicable: no data field with a constrained domain changes. The `update-types` values appear in the rows that the policy snapshot lists.

## Constitution Alignment

See `plan.md`, section Constitution Check. Each rule carries a pass or a not-applicable result. No rule fails.

## Unmapped Tasks

None. T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE map to the requirements through their acceptance statements.

## Metrics

- Requirements: 8 (`FR-001` to `FR-008`).
- Tasks: 11 (2 evidence, 5 implementation, 4 final).
- Tests planned: 17. These are the 15 existing cases of `TestDependabotPolicy` and the 2 new mutation rows.
- Remote checks: 52. The rows appear in `design/research.md` and in the status file.
- Decisions: 6. Human decisions: 0.

## Unresolved Items

- **U-1 to U-7**: Each item appears in `design/research.md`, section Unverified. The items cover Dependabot semantics, skipped steps, sibling issue closure, the local pip result, and the two unsampled Windows checks.
- **Post-merge check**: The first Dependabot run after the merge must not propose a mando update of 0.8 or later. The check runs after the merge, outside this record.

## Convergence After Implementation

- The `dependency_lock` job reports success on the fix pull request head.
- The guard tests in `tests/guardrails` pass on the fix branch.
- The sibling issues remain open until the orchestrator reviews them after pull request #4888 closes.
