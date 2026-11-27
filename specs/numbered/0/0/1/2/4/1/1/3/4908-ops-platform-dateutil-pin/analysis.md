# Specification Analysis Report: Ops platform dateutil pin (issue #4908)

This review compares `spec.md`, `plan.md`, `tasks.md`, and the remote evidence in `design\research.md`. Each finding cites a remote row (RC-##) or an Unverified item (U-#).

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| F-1 | High | PR #4890 raises the ops pin to `python-dateutil==4.0.0`. Celery 5.7.0 requires `==2.9.0.post0`. | RC-16, RC-18, RC-50 | Resolved by D-1 and T001. |
| F-2 | High | The pip entry in Dependabot has no rule for python-dateutil. | RC-23, RC-25 | Resolved by T004. |
| F-3 | Medium | The ops requirements file has no resolution gate other than the install step. The pip-audit gate scans root requirements only. | RC-02, RC-09 | Accepted gap. Record the gap in the next audit issue. Out of scope. |
| F-4 | Low | The ops job comment says it runs 300 tests. The floor is 390. | RC-06, RC-07 | Stale comment. Out of scope. The owner corrects the comment in a separate change. |
| F-5 | Low | python-dateutil 4.0.0 drops six. The ops requirements file still lists `six==1.17.0` as required by python-dateutil. | RC-19, Sources S-3 | No change. The annotation becomes stale only when the ops pin moves. |
| F-6 | Medium | Principle IV steps 10 to 12 presume a product image. This change builds no image. | RC-34 | Recorded exception D-7. The owner confirms the exception in the pull request review. |
| F-7 | Low | PR #4889 bumps deepdiff to 9.2.1. The ops pyproject bounds deepdiff below 9.0. The same job fails for that PR. | RC-22, Out of Scope | Separate issue #4907. The cause is not examined in this record (U-8). |
| F-8 | Medium | Dependabot may apply the pip entry to the ops requirements file. The scope is unverified. | U-1 | Post-merge check in T-MERGE. |
| F-9 | Low | The gate issue for a pull request closes after the pull request closes or after a later passing run. | RC-37 | The fix pull request closes issue #4908 on merge. |

## Coverage Summary

| Requirement | Tasks | Tests | Result |
| - | - | - | - |
| FR-001 install resolves | T002, T-REMOTE-CI | Ops platform gate (`pytest --cov=src --cov-fail-under=56`) | Covered |
| FR-002 ops pin stays at 2.9.0.post0 | T001 | `test_ops_platform_dateutil_pin_matches_celery_pin`, `test_dateutil_pin_drift_is_detected` | Covered |
| FR-003 Dependabot rule blocks major updates | T004 | `test_dependabot_blocks_dateutil_major_updates` | Covered |
| FR-004 no blanket or other-package ignore | T004 | `test_dependabot_policy_detects_drift` (blanket case, other-dependency case) | Covered |
| FR-005 guard fails on pin drift | T005 | `test_dateutil_pin_drift_is_detected` | Covered |
| FR-006 guard fails on missing or narrowed rule | T005 | `test_dependabot_policy_detects_drift` (missing case, minor-only case) | Covered |
| FR-007 guard fails on missing pip entry | T005 | `test_dependabot_policy_detects_drift` (missing pip entry case) | Covered |
| FR-008 root pins unchanged | T003 | Existing `test_pyproject_declares_each_requirement` | Covered |
| FR-009 documentation section | T006 | STE gate for `documentation/quality-gates.md` | Covered |
| FR-010 changelog fragment | T007 | STE gate for the fragment | Covered |
| FR-011 record names evidence | T008 | STE gate for `spec.md` | Covered |

## Consistency Review

- The spec lists nine guard cases (SC-002). The plan lists nine cases in four functions. Tasks T005 and the coverage table agree.
- The spec lists 11 requirements. The tasks cite each `FR-###`, and the coverage table maps each one.
- The tasks list 12 task IDs. The metrics below use that count.
- The plan lists three modified files and one added fragment. The change map and T004 to T007 agree.
- The research table and `STATUS.json` both list 55 remote checks. The summary repeats that count.
- Each verification command comes from the Local gates table in `.github/copilot-instructions.md`.

## Unresolved Items

- U-1: Dependabot scope. Verified after merge by T-MERGE.
- U-2: Dependabot behavior for PR #4890 after the rule merges. A maintainer decides (D-4).
- U-7: Whether the ops job passes after the fix. Verified by T-REMOTE-CI.

## Metrics

- Requirements: 11 (FR-001 to FR-011).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 12 (T001 to T008, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).
- Planned test cases: 9.
- Decisions: 9 (D-1 to D-9). Human decisions: 0.
- Remote checks: 55 (RC-01 to RC-55). Absent: 3. Present: 52.
