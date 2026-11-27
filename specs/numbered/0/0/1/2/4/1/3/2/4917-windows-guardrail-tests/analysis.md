# Specification Analysis Report: Windows guardrail test failures

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/quickstart.md`, and the remote code on `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the remote evidence map. Each finding names its location and its resolution. The test suite did not run, so each runtime claim appears under the unverified list in `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| --- | --- | --- | --- | --- | --- |
| A-01 | Defect in existing work | MEDIUM | `test_browser_installation.py`, `test_invalid_mirror_configuration_fails_without_a_write` | The `None` case asserts only a non-zero exit and a missing file. On Windows, Bash fails and leaves no file, so the case passes for the wrong reason. | This change skips the case on Windows (D-1). Follow-up issue A in T012 repairs the assertion on Ubuntu. |
| A-02 | Defect in existing work | MEDIUM | `tests\guardrails` | The folder holds 79 tracked children, which exceeds the five-item limit (RC-40). | Grandfathered by the constitution. This change adds no child (D-10). Follow-up issue B in T012 owns the remediation. |
| A-03 | Unverified claim in the issue | LOW | Issue #4917 body and PR #4918 body | Both sources state that the same 23 tests fail on `origin/main`. | The local blobs of the six guard files equal the remote blobs on `main`. The failure run is not reproduced (U-1). |
| A-04 | Missing evidence in the issue | LOW | Issue #4917 body | The issue does not give the SNMP failure text. The inference that `/bin/bash` causes it is unverified. | The fix skips the SNMP cases on Windows, so the exact text does not change the decision (U-2). |
| A-05 | Governance conflict | MEDIUM | `.github\copilot-instructions.md` line 451 (RC-33) and `constitution.md` line 409 (RC-30) | The repository instructions require a fragment only for a change that a user sees. The constitution requires one fragment for each change. | The constitution governs the repository. The change adds the fragment (D-8). |
| A-06 | Governance conflict | MEDIUM | `constitution.md` Principle IV (RC-29) and `container-build.yml` trigger (RC-19) | Steps 10 and 11 of Principle IV expect a main image build. This change does not trigger that build. | The plan records the deviation (D-9). T-MERGE checks the merged commit with `gh api`. |
| A-07 | Gap in process gates | LOW | `tasks.md` process tasks | The local gates table covers code only. Git and GitHub steps have no gate in that table. | Each process task names its `gh` or `git` command. No gate is claimed for them. |
| A-08 | Runtime risk | MEDIUM | `test_dependency_export.py`, `DependencyExport.render` | The export header may show the output path with a form that the `replace` call does not match (U-4). | R-1 in `plan.md` gives the fallback. T-LOCAL-GATES runs the export guard on the Windows workstation. |
| A-09 | Gate risk | LOW | `test_spec_route_contract.py`, module imports | The change adds `logging` for the action log (RC-41). `symbol-diff` may report the addition. | R-2 in `plan.md` gives the response. T-LOCAL-GATES runs `symbol-diff`. |
| A-10 | Consistency | MEDIUM | `spec.md` SC-001 | The predicted counts (1186 passed and 30 skipped, or 1187 and 29) depend on the issue baseline and on the symlink privilege. | SC-001 gives both predicted results. U-8 marks the counts as predictions until the Windows run. |
| A-11 | Consistency | LOW | `spec.md` FR-011 and `tasks.md` T005 | Principle VII (RC-41) requires logs for each action, and the symlink creation is an action. The spec adds the logs. | T005 names the `info` and `debug` lines. |
| A-12 | Label proposal | LOW | `META_DIR\4917-STATUS.json` | The proposed label `stage:speckit-artifacts-emitted` exists in the repository label list. | The orchestrator decides whether to apply it. |
| A-13 | Consistency | LOW | Changelog fragment and the five-item rule | The fragment adds a child under `changelog.d\`. | The constitution exception allows a unique process record under `changelog.d\` (RC-32). |
| A-14 | Environment fact | LOW | `DependencyExport.find_uv` and `requirements-dev.txt` | The environment folder holds `uv` 0.13.9, and CI installs the same pin (RC-21, RC-14). | The lookup order keeps PATH first. T-REMOTE-CI shows the CI result. |

## Coverage Summary

| Requirement | Tasks | Proving test or check | Notes |
| --- | --- | --- | --- |
| FR-001 | T010, T-LOCAL-GATES | `python -m pytest -q tests/guardrails` on Windows | Expected zero failures |
| FR-002 | T002, T003 | The 20 Bash cases of `test_browser_installation.py` and `test_snmp_base_oid_defaults.py` | Each case shows a skip reason on Windows |
| FR-003 | T002, T003, T-REMOTE-CI | The same 20 cases on Ubuntu CI | The skip condition uses Windows values only |
| FR-004 | T002 | `test_browser_setup_preserves_the_installer_contract` and `test_a_weaker_browser_installation_contract_fails` | YAML-only tests with no Bash call |
| FR-005 | T004 | `test_requirements_exports_match_the_lock`, `test_missing_uv_fails`, and `test_pinned_uv_beside_interpreter_is_found` | The new test proves the environment-folder lookup |
| FR-006 | T005 | `test_unsafe_feature_selection_fails[symlink]` | Skips only for WinError 1314 |
| FR-007 | T006 | `test_git_ignores_poisoned_locations` | `Path` comparison |
| FR-008 | T007 | `test_missing_root_fails_with_path_and_cause` | The message and the regex use POSIX paths |
| FR-009 | T010 | `git diff --name-status main -- tests/guardrails` | Only `M` rows, and no `A` row |
| FR-010 | T008 | `test_markdown_links.py`, `test_container_policy_docs.py`, and `ste-linter` | The note links no new target |
| FR-011 | T011, T004, T005 | `python -m ruff check .` and the diff review | Each changed line carries a comment |
| FR-012 | T009 | `test_changelog_fragment_policy.py` | Name and heading checks |
| FR-013 | T011, T-PR | `git diff --name-status main` | Only the eight listed paths appear |
| FR-014 | T001, T-PR, T-MERGE | `gh pr view` and `gh api repos/jmorrison-juniper/MistHelper/commits/main` | Issue, branch, commit, and merge steps |

## Consistency Checks

- The spec defines 14 requirements (FR-001 to FR-014) and 6 success criteria (SC-001 to SC-006). The plan and the tasks cite the same IDs.
- The tasks file defines 16 tasks: T001 to T012, plus T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- The change map in `plan.md` lists 8 paths: 7 modified and 1 added.
- The research file defines decisions D-1 to D-10. Each decision appears in the STATUS file.
- The research file defines 48 remote checks, and the STATUS file records the same 48 checks.

## Unresolved Items

- U-1 to U-8 in `design/research.md` remain open until the Windows run and the CI run. The predicted counts in `design/quickstart.md` depend on U-3 and U-8.
- A-01 and A-02 move to follow-up issues in T012. This change does not repair them.
