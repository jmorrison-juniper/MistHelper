# Specification Analysis Report: WAN Duplicate Sample Coverage

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the `design/` artifacts, and the remote checks in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-01 | High | The defect is not on `main`. `main` accepts at most one insight timestamp. | RC-02 | Fix after PR #4208 merges. Decision D-1. |
| A-02 | High | The issue names `summary.py`, but `main` has no such file. | RC-04, RC-12 | Treat the summary fix as part of the PR #4208 scope until the merge. |
| A-03 | High | PR #4208 owns both affected files. The PR is a draft with merge conflicts and 82 changed files. | PR #4208 metadata, read 2026-11-26. | Wait for the release. Task T002. |
| A-04 | Medium | The issue cites PR head `fbb23f8`. The current PR head is `843be63`. The defect persists at the current head. | RC-07 to RC-11 | Update the issue text with the current head. |
| A-05 | Medium | PR #4208 leaves four WAN directories with six children. The five-item rule allows five. | RC-21 to RC-24 | Record the debt. Open a separate remediation issue. |
| A-06 | Medium | The PR documentation says the congestion value needs all six samples known. The code counts raw values. | RC-17, RC-10, RC-11 | Update the documentation in task T011. |
| A-07 | Medium | The PR tests have no case for a repeated timestamp inside one response. | RC-15 | Add tests in tasks T003 to T005. |
| A-08 | Low | Issue #4583 comments name PR #4208 as the owner of `tests/guardrails/test_e2e_shard_partition.py`. The current PR file list lacks that path. | PR #4208 file list, read 2026-11-26. | Treat the comments as stale. This fix needs no action. |
| A-09 | Medium | The OpenAPI schema does not require `rt`. The PR code requires `rt`. | RC-45, and `snapshot_client.py` line 265 at the PR head. | Keep the fail-closed rule. Record it in `design/contracts/insight-sample.md`. |
| A-10 | Low | Issue #4681 carries `in-progress`, but its work is blocked. The repository has no `blocked` label. | `gh label list` output, read 2026-11-26. | Keep the labels. Decision D-6. |

## Consistency Review

### Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T003, T006 | Repeated and missing interval test in T003 |
| FR-002 | T003, T006 | Identical duplicate test in T003 |
| FR-003 | T003, T006 | Conflicting duplicate test with log assertion in T003 |
| FR-004 | T003, T006 | Repeated and missing interval test in T003 |
| FR-005 | T003, T006 | Repeated and missing interval test in T003 |
| FR-006 | T004, T007 | Unique aligned utilization test in T004 |
| FR-007 | T004, T006 | Six known and five known congestion tests in T004 |
| FR-008 | T005, T008 | Five sample and six sample summary tests in T005 |
| FR-009 | T007, T-LOCAL-GATES | Existing contract tests in `test_gateway_insights.py` |
| FR-010 | T003, T009 | Conflict log assertion in T003 |
| FR-011 | T010, T011 | Changelog guard test in T010. `git grep` check in T011. |
| FR-012 | T002, T-MERGE | PR state checks in T002 and T-MERGE |

Every requirement has at least one task and at least one test or verification command.

### Cross-Artifact Checks

- Each file path in `plan.md` appears in `tasks.md` and in the remote checks.
- The task count in `tasks.md` is 15. The count in `design/research.md` and `summary.md` must match `tasks` in `STATUS.json`.
- The remote check rows in `design/research.md` match the `remote_checks` array in `STATUS.json`, one for one.
- Each decision in `design/research.md` matches one entry in the `decisions` array of `STATUS.json`.

## Unresolved Items

- U-1: The release date of PR #4208 is unknown. The merge controls when task T002 completes.
- U-2: No live response proves that Mist repeats a timestamp. The fix stays defensive either way.
- U-3: This run did not read the manual refresh route response to a `ValueError`.
- U-4: The operator guide absence check used a local search only.
