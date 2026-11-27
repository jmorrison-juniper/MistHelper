# Specification Analysis Report: Interrogate Gate Failure on PR #4888

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, the remote code on `main`, and PR #4888.

**Method**: A read-only pass compared each requirement with its task and its test or check. The pass also compared the CI log with the remote files. Each finding below has a resolution in this record.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A-1 | Defect | HIGH | PR #4888 changes `requirements-dev.txt` line 179 only | The bump changes the export but not `uv.lock`. `uv.lock` keeps `mando` 0.7.1 at line 1301 (RV-06). The export guard would fail for PR #4888. The guard did not run in this session. | Rejected by D-1. The fix keeps 0.7.1. |
| A-2 | Defect | HIGH | `.github/dependabot.yml`, pip stream lines 3 to 11 (RV-16) | The pip stream has no ignore rule for `mando` (RV-17). The weekly schedule (RV-69) can propose the same bump again. | Fixed by T007. |
| A-3 | Conflict | MEDIUM | Constitution line 409 (RV-55) and fragment README line 58 (RV-28) | The constitution requires one fragment for each change. The README allows no fragment for an internal change. | Decided by D-6. The fragment is added. The README rule stays unchanged. |
| A-4 | Coupling | MEDIUM | Policy snapshot (RV-20) and whole-policy assertion (RV-21) | A new `ignore` key fails the equality assertion until the snapshot changes. | Fixed by T006. |
| A-5 | Reporting | LOW | Issue #4901 body | The issue names commit `5bb4b385`. That commit is the GitHub test merge of head `e86098c` onto base `00d9a16`. The job log reads `HEAD is now at 5bb4b38 Merge e86098cdc2b189d217805b3b4060ef609cbc37af into 00d9a16e998b0cb5e10b6ed77da0fa909670d64f`. | Research R1 records it. The reproduction uses the run head. |
| A-6 | Scope | LOW | Run 45064243269 | Twenty-eight jobs failed. Twenty-six show the resolver message. Two fail in aggregator steps (research R2). | T-REMOTE-CI checks each failed job on the fix head. |
| A-7 | Mapping | LOW | Issue #4894 | The title names `pytest`. The job is `pytest (coverage gate)`, matched by title. | Unverified item U-5. |
| A-8 | Ambiguity | LOW | Dependabot rule syntax | Dependabot accepts or rejects the rule only during a run. | Unverified item U-1. |
| A-9 | Dependency | LOW | Constitution steps 10 to 12 (RV-50, RV-51, RV-52) | The container build runs on a product-file push or a manual dispatch (RV-40). This change edits no product file. | Decided by D-8. Unverified item U-4. |

## Coverage Summary

| Requirement | Task IDs | Test or check | Gap |
|-------------|----------|---------------|-----|
| FR-001 | T003, T004, T-LOCAL-GATES, T-MERGE | `tests/guardrails/test_dependency_export.py` (RV-59) | None |
| FR-002 | T005, T007 | Policy cases for 0.8.2 and 0.9.0 | None |
| FR-003 | T005, T007 | Policy case for 0.7.2 | None |
| FR-004 | T006, T007 | `test_complete_policy` and the whole-policy assertion (RV-21) | None |
| FR-005 | T-LOCAL-GATES, T-REMOTE-CI | Local docstring command. CI job `Interrogate (docstring coverage)` | The docstring value on the fix head is unverified (U-2) |
| FR-006 | T-REMOTE-CI | `gh pr checks --watch` against the 15 required contexts | None |
| FR-007 | T-PR, T-MERGE | `gh pr view 4888 --json state,mergedAt` | Closure waits for the merge |
| FR-008 | T008, T-PR | `Get-ChildItem changelog.d -Filter 'issue-4901-*'` | None |
| FR-009 | T009 | Review of the record against the CI log (`design\checklists\ci-evidence.md`) | None |
| FR-010 | T009 | `tests/guardrails/test_spec_route_contract.py` (RV-23) | None |

Tasks T001 and T002 carry the tag `[process]`. They follow repository rules and map to no requirement. No task is unmapped.

## Metrics

| Metric | Value |
|--------|-------|
| Functional requirements | 10 |
| Success criteria | 6 |
| Tasks | 13 |
| New test cases | 3 |
| Remote checks | 69 |
| Decisions | 8 |
| Human decisions | 0 |
| Findings | 9 |
| Unverified items | 7 |

## Constitution and Repository Rules

The plan section "Constitution Check" lists each rule with its result. No rule fails. Principle IV passes with a manual dispatch for steps 10 to 12 (RV-40, RV-51, RV-52).

## Unresolved Items

- U-1, Dependabot accepts the rule. The decision point is T-MERGE and the next weekly run.
- U-2, the docstring value on the fix head. The decision point is T-REMOTE-CI.
- U-4, the image content after the merge. The decision point is T-MERGE.
- U-3, U-5, U-6, and U-7 do not block the plan. Research lists them under Unverified.
