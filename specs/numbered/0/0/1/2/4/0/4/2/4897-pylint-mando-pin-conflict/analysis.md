# Specification Analysis Report: Pylint gate failure from the mando 0.8.2 pin

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-1 | High | Pull request #4888 edits a uv-generated export by hand. It leaves `uv.lock` and `pyproject.toml` unchanged. | RC-10, RC-13, RC-15, RC-16 | Hold the pin at 0.7.1 (R1). |
| A-2 | High | The Pylint job cannot reach its score step while the pin is 0.8.2. | RC-29, RC-30 | Keep the pin, and add the ignore entry (R1, R2). |
| A-3 | Medium | The issue title names `pylint`, but the pylint score never ran. The failed step is `Install dependencies`. | RC-02, RC-03, RC-29 | This record names the step and the rule. The title format belongs to the sync job, which this change does not edit. |
| A-4 | Medium | The issue cites commit `5bb4b385`. That commit is a test merge that GitHub creates. The run head is `e86098cd`. | RC-27, RC-28 | This record cites both commits. |
| A-5 | Medium | 26 failed jobs and two Windows checks show the same resolution error. | RC-31, RC-32 | T-REMOTE-CI verifies each check on the fix pull request. |
| A-6 | Low | Two aggregate jobs fail after an upstream job fails. Their failed steps are `Verify dependency lock job` and `Verify E2E shards`. | RC-31 | No change. Both pass when their upstream jobs pass. |
| A-7 | Medium | The pip stream has no ignore entry, and it runs weekly. The same bump can return each week. | RC-18, RC-19 | Add the ignore entry (D-2). |
| A-8 | Medium | The policy snapshot freezes the whole Dependabot file. An ignore entry breaks the snapshot test until the snapshot changes. | RC-21, RC-22 | T004 changes the snapshot in the same commit as T003. |
| A-9 | Low | The lock guard module holds eight top-level names, which is above the five-item limit. | RC-24 | Complexity Tracking records the debt and names a remediation issue. |
| A-10 | Medium | The constitution requires one fragment for each change. The README exempts internal-only changes. | RC-45, RC-46, RC-47 | Add the fragment (D-6). |
| A-11 | Low | Main moved from base commit `00d9a16e` to `f03c6c9`. The requirements file has the same blob on both. | RC-11, RC-33 | The conflict is not a main regression. The fix branch updates from main before its run. |
| A-12 | Medium | No source verifies whether Dependabot accepts the `versions` key. | U-1 | Check the next scheduled Dependabot run. |
| A-13 | Low | This record does not investigate the pip note about "no matching distributions" for mando. | U-2 | No effect on the decision. The decision rests on the radon requirement. |
| A-14 | Low | Reading their source, this record infers that the guard tests fail on the PR branch. This record does not run them. | RC-23, RC-24 | T006 proves the red state of the new test. T-REMOTE-CI proves the others. |

## Coverage Summary

| Requirement | Task | Test or check |
| - | - | - |
| FR-001 | T001, T002 | Scenario 1 and Scenario 2 in `design\quickstart.md` |
| FR-002 | T-REMOTE-CI | CI job `Pylint (score gate)`, step `Run Pylint` |
| FR-003 | T002, T009 | `test_pinned_mando_satisfies_radon_requirement`, `test_lock_satisfies_every_requirement` |
| FR-004 | T009 | `test_requirements_exports_match_the_lock`, `test_lock_is_current_with_pyproject` |
| FR-005 | T003 | `test_complete_policy` after the snapshot change, and the next-run check in User Story 3 |
| FR-006 | T004 | `test_complete_policy`, `test_unrelated_changes_fail` |
| FR-007 | T005, T006 | `test_pinned_mando_satisfies_radon_requirement` in green and red states |
| FR-008 | T-MERGE | `gh pr view 4888` state check |
| FR-009 | T009 | Diff check that `.github/workflows/ci.yml` stays unchanged, and job step `Run Pylint` |
| FR-010 | T-PR | Conventional Commits PR title check in CI |
| FR-011 | T007 | STE gate on `.github/copilot-instructions.md` |
| FR-012 | T008 | `test_changelog_fragment_policy.py` |
| FR-013 | T009 | Diff check of changed paths against `src\` and `MistHelper.py` |
| SC-001 | T-REMOTE-CI | CI job result |
| SC-002 | T-REMOTE-CI | CI log search for `ResolutionImpossible` |
| SC-003 | T006 | Red-state run on the pull request #4888 pin |
| SC-004 | T-REMOTE-CI | CI guard results |
| SC-005 | Self-review of this record | Counts in `4897-STATUS.json`, `design\research.md`, and `4897-summary.md` |

## Constitution Alignment

- Principle I: the change adds no direct child under `tests\guardrails`. Existing debt is in Complexity Tracking of the plan.
- Principles VI and VII: T005 requires an inline comment and action logging for each new line.
- The release-note rule: the constitution governs the conflict with the README exemption. Decision D-6 records the choice.
- No conflict remains between the constitution and the change.

## Unmapped Tasks

None. Each task maps to at least one requirement or success criterion.

## Metrics

- Requirements: 13 (FR-001 to FR-013).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 13.
- Tests planned: 6 test functions.
- Decisions: 6 (D-1 to D-6). Human decisions: 0.
- Remote checks: 50. Each check has one row in `design\research.md` and one entry in `4897-STATUS.json`.

## Convergence After Implementation

The implementer repeats these checks on the fix branch before the merge:

1. The Pylint (score gate) job reports `Run Pylint` as successful.
2. No install step logs `ResolutionImpossible`.
3. The new test passes on the fix branch and fails on the pull request #4888 pin.
4. The Dependabot policy guard passes with the snapshot.
5. The next scheduled Dependabot run raises no mando version of 0.8 or later.

## Unresolved Items

- U-1: Dependabot accepts the `versions` key with the value `>= 0.8`. Reason: the docs page was not readable through the available tools. Action: check the next scheduled run.
- U-2: This record does not investigate the meaning of the pip note about "no matching distributions" for mando. Reason: the root cause rests on the radon requirement in the same log.
- U-3: Dependabot may raise the bump again if the ignore entry does not work. Reason: Dependabot run history is not readable through the available tools. Action: the User Story 3 check.
- U-4: This record does not confirm the latest mando release on PyPI. Reason: the JSON response stops before the version field. No decision depends on it.
