# Specification Analysis Report: Windows Bash Guardrail Skips

## Findings

| ID | Type | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - | - |
| A-1 | Cause | High | The browser module passes a Windows interpreter path to bash. Bash cannot run that path, so the command returns 127. | RC-02, issue #4877 text `assert 127 == 0` | D-1 and D-2 |
| A-2 | Cause | High | The SNMP module starts `/bin/bash`. Windows has no such path, so Python raises `FileNotFoundError`. | RC-15, issue #4877 text | D-1 and D-2 |
| A-3 | Count | Low | The issue reports 10 browser failures. The browser module holds 11 shell cases. The None case passes when bash runs. | RC-04 to RC-09, research F-1 | The record uses 11. The explanation stays unverified (research U-2). |
| A-4 | Defect | Medium | The None case cannot prove that the mirror logic ran. A broken harness passes it. | RC-08 | D-5 follow-up. Out of scope. |
| A-5 | Risk | Medium | A Windows skip counts as a pass in local reports. | RC-34, RC-22 | Ubuntu job, T-REMOTE-CI, and the spec Caution. |
| A-6 | Conflict | Low | The constitution requires one fragment for each change. The changelog README allows none for an internal change. | RC-39, RC-37, RC-33 | D-7 adds the fragment. |
| A-7 | Conflict | Low | Constitution steps 10 to 12 assume a build. The container trigger excludes this change. | RC-40, RC-28 | D-9. Evidence recorded in T-MERGE. |
| A-8 | Interpretation | Low | Constitution Principles VI and VII apply to modified code. This change modifies decorators and adds new lines only. | RC-65, RC-66 | D-10. The reviewer decides. |
| A-9 | Scope | Medium | Issue #4878 lists three other Windows guardrail failures. Their causes differ from bash. | Research F-13 | Out of scope. Related issue. |
| A-10 | Gap | Medium | The spec agent ran no test. The Windows counts derive from code. | Rule 2 of the brief | Unverified U-1. T-LOCAL-GATES runs the counts. |
| A-11 | Note | Low | The `contents` endpoint returned HTTP 404 with `?ref=main` for the two module paths. The blob endpoint returned the same content. | Research F-14 | Blob SHAs are used (RC-01 and RC-14). |
| A-12 | Note | Low | Mypy, Vulture, Pydocstyle, and Interrogate scope their paths away from tests. | RC-27 | Not applicable in T-LOCAL-GATES. |
| A-13 | Note | Low | The route `specs/numbered/0/0/1/2/4/0/0/2` is absent on `main`. | RC-44 | No collision. |
| A-14 | Note | Low | PR #4880 changed `documentation/development-setup.md`, which this change also edits. | Research F-10 | Rebase onto `main` before the edit. The File Change Map states it. |

## Coverage Summary

| Requirement | Tasks | Checks |
| - | - | - |
| FR-001 | T002, T003 | TC-02, TC-04 |
| FR-002 | T002, T003 | TC-06 |
| FR-003 | T002, T003 | TC-01, TC-03 |
| FR-004 | T-REMOTE-CI | TC-05 |
| FR-005 | T002, T003 | TC-07 |
| FR-006 | T-LOCAL-GATES | TC-02, TC-04 |
| FR-007 | T001, T-PR | TC-10 |
| FR-008 | T004 | TC-09 |
| FR-009 | T005 | TC-08 |
| FR-010 | T002, T003 | TC-11, TC-15 |
| FR-011 | T-PR | TC-13 |

Every requirement maps to at least one task and at least one check.

| Success criterion | Checks |
| - | - |
| SC-001 | TC-01, TC-02, TC-03, TC-04 |
| SC-002 | TC-05 |
| SC-003 | TC-08, TC-09, TC-12, TC-14 |
| SC-004 | TC-06 |
| SC-005 | TC-10 |

## Verification Checks

| ID | Check | Method |
| - | - | - |
| TC-01 | On a Windows host, eight non-shell browser cases pass. | Run the browser module with `-rs -q`. Read the summary. |
| TC-02 | On a Windows host, 11 browser shell cases skip, each with the named reason. | Run the browser module with `-rs -q`. Read the skip lines. |
| TC-03 | On a Windows host, three non-shell SNMP cases pass. | Run the SNMP module with `-rs -q`. Read the summary. |
| TC-04 | On a Windows host, nine SNMP shell cases skip, each with the named reason. | Run the SNMP module with `-rs -q`. Read the skip lines. |
| TC-05 | On Ubuntu, 31 cases pass and no case skips. | Read the `pytest_coverage_shards` job log. |
| TC-06 | Each folded reason names the cause and issue #4877. | Read the short summary from the Windows run. |
| TC-07 | Neither module holds a module-level mark. | Search both files for lines that start with `pytestmark`. Expect no match. |
| TC-08 | The changelog guard passes for the new fragment. | Run `tests/guardrails/test_changelog_fragment_policy.py`. |
| TC-09 | The container policy guard passes, and `ste-linter` scores the page at 80 or above. | Run `tests/guardrails/test_container_policy_docs.py` and `ste-linter`. |
| TC-10 | No path under `src/` or `MistHelper.py` changes. | Run `git diff --name-only origin/main` and read the paths. |
| TC-11 | Each new line uses ASCII characters only. | Search the changed files for characters outside ASCII. Expect no match. |
| TC-12 | No module-level name is removed. | Run `symbol-diff --base origin/main` on each changed Python module. |
| TC-13 | The pull request body names both follow-up items. | Read the pull request body. |
| TC-14 | The test quality gate reports zero new findings. | Run the test quality full-suite check from `.github/copilot-instructions.md`. |
| TC-15 | Each new executable line has an inline comment. | Review the diff during T-PR. |

## Metrics

- Requirements: 11 (FR-001 to FR-011).
- Tasks: 9, including one verified task.
- Planned cases: 31, with 20 shell cases and 11 non-shell cases.
- Decisions: 10, with 0 human decisions.
- Remote checks: 68, matching `research.md` and `STATUS.json`.
- Verification checks: 15.
- Follow-up items: 2.

## Constitution Alignment

- Principles I, II, III, V, and VI pass as the plan states.
- Principle IV passes with evidence for steps 10 to 12 (D-9).
- Principle VII passes under the interpretation in D-10.
- The release note rule passes with the fragment in D-7.

## Open Items

- OPEN-1: The Windows counts are not executed by the spec agent. T-LOCAL-GATES runs them.
- OPEN-2: The explanation of the 10 browser failures is inferred from code. The Windows run confirms or rejects it.
- OPEN-3: Issue #4878 keeps three Windows failures open. Its own change fixes them.
- OPEN-4: The orchestrator reviews the not-triggered evidence for steps 10 to 12 (D-9).
- OPEN-5: A reviewer decides the interpretation in D-10.

## Follow-up Items (not in this change)

1. Tighten the None case in `test_invalid_mirror_configuration_fails_without_a_write`. The assertion at line 146 and line 147 accepts any non-zero exit. The orchestrator files this issue.
2. Add a repository guard that requires the POSIX shell mark on each shell case. The orchestrator files this issue.
