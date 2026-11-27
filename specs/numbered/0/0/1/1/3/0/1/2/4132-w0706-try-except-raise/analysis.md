# Analysis: W0706 try-except-raise handlers in MistHelper.py

This review compares the spec, the plan, the tasks, and the code on remote main. Row IDs such as R01 refer to the table in `design/research.md`.

## Consistency Review

| Check | Sources | Result |
| - | - | - |
| Handler count | The issue names eight line numbers. Main holds seven re-raise-only handlers (R02 to R08). | Explained. The eighth issue line (2331) is absent on main (R09). |
| Line numbers | The issue lines come from commit `61505c611`. Main lines come from blob `98d7828479ded6bc4c83d15e0c1847171cfbfd49` (R01). | The issue lines are stale. The plan uses main lines. |
| Source commit | GitHub returns HTTP 422 for commit `61505c611` (R10). The commit exists in the local object store only. | Local only. The issue cites a commit that GitHub does not return. |
| Blocker | An issue comment dated 2026-11-08 waits for PR #4607. PR #4607 merged on 2026-11-13. | The blocker is resolved. No dependency remains. |
| Open pull requests | Seven open pull requests exist. None changes `MistHelper.py`. | No overlap. T001 repeats this check. |
| CI pylint scope | `SRC_PATH` is `src/` (R32). | The W0706 rule in `MistHelper.py` has no CI gate. Test B covers the rule. |
| Changelog rule conflict | `changelog.d/README.md` rule 4 allows no fragment for an internal-only change (R49). The constitution requires one fragment for each change (R25). | The constitution governs (R26). One fragment is added (decision D-7). |
| Lint configuration | The pylint messages-control block disables five codes (R46). W0706 is not among them. | Pylint reports W0706 for this repository. |
| Pylint version | `requirements-dev.txt` pins `pylint==4.1.4` (R47). The local `.venv` holds `pylint-4.1.4.dist-info`. | The local source matches the pinned version (R67). |
| Local and remote content | Local HEAD is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local and remote `MistHelper.py` blobs are equal. | Local line numbers equal main line numbers. |
| Five-item debt | `changelog.d/` holds 335 children (R59). `tests/unit/` holds 50 (R60). `tests/guardrails/` holds 79 (R61). | Recorded in the plan debt table. |
| Function length | `_invoke_one_systematic_test` spans 26 lines, from main line 6594 to 6619. | Existing violation. Recorded in the plan. |
| Test module size | `tests/unit/test_issue_1709_narrow_except.py` holds 40 top-level test functions (R55). | Grandfathered. The change adds six functions. |

## Defects in Existing Work

1. A stray comment `# hi` appears at line 8372. It sits in the `finally` clause of the `__main__` block (R12, R01). It is a debug leftover. Out of scope for this change. Recommend a separate issue.
2. The `__main__` block spans 98 lines (main 8276 to 8373). A block of that size resists review. Out of scope for this change. Recommend a separate issue.
3. `documentation/COMPLIANCE_REPORT.md` cites `MistHelper.py` line numbers, for example line 3199 at row CMP-001 (R45). Those citations already drift. This change leaves them unchanged (decision D-10).
4. The issue carries an obsolete blocker comment. Its condition is now met, so the comment no longer applies. No code change follows from it.

## Unresolved Items

1. The pylint baseline on main is unverified. Rule 2 forbids a linter run during this research. Task T002 records the baseline before any edit.
2. The constitution pipeline steps 10 to 12 apply to a change with a fragment (R28 to R30). The orchestrator authorizes the merge and the deployment check. The agent makes no merge decision.
3. Recommended follow-up issues for the orchestrator: the stray `# hi` comment, the `__main__` block size, and the direct-child debt. Also the length of `_invoke_one_systematic_test`. This agent creates no issues.

## Requirement Coverage

Each requirement maps to at least one task and at least one test or gate. The mapping appears in `tasks.md` under Requirement Coverage. No requirement lacks a task. No requirement lacks a test or gate.

## Conclusion

The spec, the plan, and the tasks agree with remote main on the handler lines, the blob, the route, and the gates. The record has one open verification item: the pylint baseline, which T002 runs before any edit.
