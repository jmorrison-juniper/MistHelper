# Analysis: Lint repair for W0212 and W0201 findings

This review checks the specification, the plan, the tasks, and the remote code of `main`. Remote evidence rows (RC) are in `design/research.md`.

## Inventory of Findings

| Finding | File | Owner run at 0d881744 (blob c6df4393 or 02119600) | Main at 98d78284 or d9b4d79e | State on main | Evidence |
|---|---|---|---|---|---|
| W0212 protected load `_select_msps` and `_select_orgs_from_msp` | `MistHelper.py` | Lines 4969, 4970, 5906, 5907 | Public `select_msps` and `select_orgs_from_msp` at lines 4790, 4791, 5735, 5736 | Removed. Commit aa8d12e90 (#4853). | RC-05, RC-07 |
| W0212 protected store `_deferred_init_done` | `MistHelper.py` | Lines 7455, 7792, 7808 | Public `deferred_init_done` at lines 7576 and 7592 | Removed. Commit aa8d12e90 (#4853). | RC-06, RC-07 |
| W0212 protected call `_handle_interactive_invalid_selection` | `tests/unit/test_menu_entry_metadata.py` | Line 82 | Line 84 | Open | RC-03 |
| W0212 protected call `_handle_interactive_empty_input` | `tests/unit/test_menu_entry_metadata.py` | Line 91 | Line 93 | Open | RC-04 |
| W0201 attribute stores of `_uv_available`, `_uv_checked`, `_last_uv_update_check` | `MistHelper.py` | No finding | Stores at lines 1381 to 1383, 1479, 1480, 1554, and 1560. `__init__` calls the helper at line 1349. | No finding under the per-attribute rule | RC-33, D-2 |

Counts by stage:

- The issue title reports 11 findings in two files. The issue body reports 7 W0212 and 4 W0201 findings. Those line numbers belong to commit 61505c611, which GitHub does not return (RC-09).
- The owner run at commit 0d881744 reports 9 W0212 findings (7 in `MistHelper.py`, 2 in the test file) and no W0201 finding. The Python AST walk in this run reproduces those counts exactly (validation in `design/research.md`, method).
- Main at blob 98d78284 reports 2 W0212 findings, both in the test file, and no W0201 finding.

## Defects in Existing Work

1. The issue body cites commit 61505c611 and branch `3519-juniper-rma-correlation`. GitHub returns HTTP 422 for the commit and HTTP 404 for the branch (RC-09, RC-10). A local object exists, but that object is not pushed evidence. The issue line numbers apply to no remote commit.
2. The issue title says 11 findings. Main holds 2. The title and the body are stale.
3. Issue comments dated 2026-11-08 and 2026-11-10 say that PR #4607 owns `MistHelper.py`. PR #4607 merged on 2026-11-13 (RC-13). The ownership hold no longer applies. The publication hold in the comments dated 2026-11-10 has no end date. It stays in force until the orchestrator authorizes the pull request.
4. The issue expects each attribute to be declared in `__init__`. On main, `__init__` calls `_initialize_dependency_tracking` at line 1349, and that helper declares the three attributes at lines 1381 to 1383. Pylint 4.1.4 accepts that design (RC-33). The expected outcome and the code differ. Decision D-2 records the deviation.
5. The local gates table runs pylint on `src/` only (`ci.yml` line 78, RC-22). The CI gate does not block these two files. The local gate table also omits the test tree from mypy, pydocstyle, interrogate (RC-19 to RC-21), and vulture (RC-37).
6. Two repository documents disagree on changelog fragments. Constitution line 409 requires one fragment for each change. The fragment README exempts internal-only changes (`changelog.d/README.md`, rule 4). Copilot-instructions line 451 requires a fragment for a user-visible change. The constitution governs (its Governance section names it the authoritative source). Decision D-4 follows the constitution. The README contradicts the constitution, so a maintainer should correct the README.
7. The test module holds nine top-level names. The five-item rule allows five. The module is grandfathered debt. The change adds no top-level name.
8. The owner candidate test and the analyzer candidate live outside the repository. This run cannot read them. Issue comments dated 2026-11-10 state that the released analyzer reports two new HTTP findings for the candidate. The change does not reuse the candidate.

## Consistency Review

### Requirement to task and check

| Requirement | Task | Test or check |
|---|---|---|
| FR-001 zero W0212 in the test file | T001, T002, T-LOCAL-GATES | Pylint command in quickstart. Cases in `test_unknown_or_non_numeric_selection_exits` and `test_empty_selection_does_not_exit`. |
| FR-002 zero findings in `MistHelper.py`, no edit | T001, T-LOCAL-GATES | Pylint command in quickstart. The four unchanged test functions that read `MistHelper.menu_actions` must still pass. |
| FR-003 exit code 1 and refusal text | T002 | `test_unknown_or_non_numeric_selection_exits` (2 cases). |
| FR-004 notice count and no exit | T002 | `test_empty_selection_does_not_exit` (1 case). |
| FR-005 restore replaced values | T002 | The two tests above. The monkeypatch teardown restores each value. |
| FR-006 no suppression or alias | T002, T-PR | Diff review in T-PR. Test-quality gate in T-LOCAL-GATES. |
| FR-007 direct mode | T002 | The two tests above. The container check returns false. |
| FR-008 one fragment | T003 | `tests/guardrails/test_changelog_fragment_policy.py`. |
| FR-009 applicable gates pass | T-LOCAL-GATES, T-REMOTE-CI, T-MERGE | Gate commands listed in each task. |
| FR-010 35 cases, same names, no new top-level name | T002, T-LOCAL-GATES | Pytest case count. Symbol check (no module-level name changed). |

Each requirement maps to at least one task and at least one test or check. FR-006 and FR-009 map to gate checks, because no unit test can prove the absence of a suppression.

### Spec, plan, and tasks

- The plan lists two calls, one import, and four replacements. Task T002 lists the same four replacements and the import.
- The changelog file name is `issue-4133-lint-w0212-w0201.md` in the plan, in task T003, and in the change map. The name matches the fragment README rule for an issue without a pull request.
- The case count 35 comes from the source: 3 non-parametrized tests, 29 boundary cases, 2 invalid-selection cases, and 1 empty-selection case. Pytest verifies the count in T001.

### Spec and remote code

- The record names `MistHelper.py` line numbers from main. Each line comes from the decoded blob 98d78284, and the SHA-1 check matched (RC-01).
- The record names the test file lines 84 and 93 from blob d9b4d79e (RC-03, RC-04).

## Unresolved Items

1. The publication hold in the issue comments stays in force. The orchestrator authorizes T-PR and T-MERGE.
2. The test-quality gate result is unknown until T-LOCAL-GATES runs. The planned test calls only `dispatch_main_mode`. The analyzer reads only the bodies of called functions (RC-35, RC-36). That body names none of the four HTTP modules.
3. This run did not execute pylint, because rule 2 prohibits running a linter. The AST walk reproduces the owner counts on 0d881744. The quickstart pylint command must run in T-LOCAL-GATES.
4. Principle VII applies to AI-generated code by its literal wording. The plan passes it by scope. A reviewer can require a logger. A logger adds one top-level name to a module that already exceeds the five-item limit.
5. The split of the test module belongs in a separate issue. The orchestrator files that issue. This run cannot write to GitHub.
6. The owner candidate content is not available. This record does not reuse it.
