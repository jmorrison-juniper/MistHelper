# Analysis: Remediate the five-child debt of three folders

## Findings

| ID | Severity | Finding | Action |
| - | - | - | - |
| F-1 | High | The issue states 52, 10, and 16. Main at f03c6c9b holds 53, 10, and 17. Commit f03c6c9b (PR #4941) added one child to each of the three folders. Before that commit, the folders held 52, 9, and 16. The issue's count for `tests/unit/scripts/` was never correct. | Use the main counts for the baseline (D-10). Record the stale claims in research rows 1 to 3. |
| F-2 | High | The issue requires that no tracked file names an old path. Three historical documents name moved items outside `specs/` and `changelog.d/`. `specs/` and `changelog.d/` name many moved items. | Exclude the historical records from the sweep (D-7). The deviation is recorded. |
| F-3 | Medium | The brief's T-PR wording requires `Closes #<ISSUE>` in every pull request. The issue asks for one move group per pull request. | Use `Refs #4944` in PR-1 to PR-5 and `Closes #4944` in PR-6 (D-6). The deviation is recorded. |
| F-4 | High | A new file in `tests/guardrails/`, `tests/unit/scripts/`, or `scripts/` adds a direct child to a noncompliant parent. Principle I forbids that. | Put the guard cases and the path-depth cases in existing files (D-4, D-13). |
| F-5 | High | 24 moved modules compute the repository root from their own position. A move changes the required depth. A wrong depth loads the wrong folder, or writes data to the wrong place. | Use the path-depth table in `plan.md`. Each PR runs the sweep for `parents[` and `parent.parent`. |
| F-6 | High | `bootstrap_worktree.py` is imported or patched by string in at least eight test modules, plus `tests/conftest.py` and two e2e modules. | PR-4 changes each import and string in the same pull request (research rows 58 to 66, 122, 123, 125, 126, 138, and 139). |
| F-7 | High | `scripts/menu_api_map/render/pages.py` writes the command text into 16 generated menu API pages. `generate_menu_wiki.py` writes two menu reference pages. `generate_portal_menu_registry.py` writes the web portal registry docstring. The drift check compares generator output with committed pages. | PR-5 regenerates each page with its tool and runs `--check` (D-11). |
| F-8 | Medium | `scripts/wave1/run_wave1_gate.ps1` line 7 uses two `Split-Path -Parent` calls to find the project root. A move adds a level. | PR-3 adds a third call (plan path table). |
| F-9 | Medium | `ci.yml` lines 93 and 99 and `pyproject.toml` lines 410 and 411 name mypy and radon paths. `tests/guardrails/test_mypy_paths_openai_scripts.py` lines 26 and 27 pin the same paths. | PR-6 changes all four locations in one commit. |
| F-10 | Medium | `ruff` excludes `scripts`. The lint gate does not cover the moved files. | T-LOCAL-GATES compiles each changed file. The moved tests run under pytest. |
| F-11 | Medium | The working tree has five modified tracked files outside this scope. Four local-only folders exist on disk and do not appear on main. | Stage by explicit path (D-12). The guard counts tracked children only. |
| F-12 | Medium | Pytest imports `tests/unit/scripts` modules without `__init__.py` files. Basenames must stay unique. | The duplicate check on main found no duplicate moved basename. Each PR repeats the check (quickstart Scenario 7). |
| F-13 | Medium | `scripts/mist_ideas_analyzer.py` and `scripts/mist_ideas_distiller_v2.py` insert their own folder into `sys.path`. Each CLI moves with its package. | The insert stays valid. The docstrings change to the new invocation path. |
| F-14 | Low | An operator with a saved old command sees a missing file. | Documents, changelog fragments, and commit messages name the new paths (D-8). The risk is accepted. |
| F-15 | Low | `tests/guardrails/process_folder_baseline.json` governs the `specs/` process folders. It is a different baseline from the debt guard. | Keep the two baselines separate. The debt guard uses its own constant (D-4). |

## Coverage Summary

Each FR maps to at least one task and at least one test or verification command.

| Requirement | Tasks | Test or verification |
| - | - | - |
| FR-001 | T002, T003 to T007, T008 | Count commands in quickstart Scenario 2 and the guard test |
| FR-002 | T002 | `test_process_folder_structure.py` run with `-s` prints three lines |
| FR-003 | T002 | Growth case in the guard test |
| FR-004 | T001, T002, T003 to T007 | Baseline constant in each PR |
| FR-005 | T004 to T007 | Count command for `scripts/` in quickstart Scenario 2 |
| FR-006 | T004 to T006 | `pytest tests/unit/scripts` in each group task |
| FR-007 | T003 | `tests/guardrails/test_markdown_links.py` and the count command |
| FR-008 | T003 to T007 | Group test commands and the sweep in quickstart Scenario 5 |
| FR-009 | T004 to T007 | Path-depth cases (24 total) in `tests/unit/scripts/test_script_imports.py` |
| FR-010 | T003 to T007 | Sweep and document review in T-PR |
| FR-011 | T006 | `--check` command in quickstart Scenario 6 |
| FR-012 | T007, T008 | Sweep in quickstart Scenario 5 |
| FR-013 | T-PR | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-014 | T-LOCAL-GATES | Gate results in each pull request body |
| FR-015 | T-PR | `gh pr view <number> --json body` |
| SC-001 | T008 | Count commands in quickstart Scenario 2 |
| SC-002 | T008 | Sweep in quickstart Scenario 5 |
| SC-003 | T002 | Growth case in the guard test |
| SC-004 | T004 to T007 | Path-depth cases |
| SC-005 | T-LOCAL-GATES, T-REMOTE-CI | Gate results and remote check results |
| SC-006 | T006, T008 | `tests/guardrails/test_menu_number_uniqueness.py` and `tests/guardrails/test_operation_registry_menu_coverage.py` (quickstart Scenario 6) |

## Constitution Alignment

`plan.md` lists each rule with its result. The analysis found no violation without a recorded exception. The one exception is `compose.ps1` at the top level of `scripts/` (D-1). Principle I accepts it as a recorded exception with the remediation action.

## Unmapped Tasks

None. Each task names at least one requirement.

## Consistency Checks

- The PR sequence in `plan.md` matches the counts in `tasks.md` (T002 to T008) and the baselines in the STATUS file.
- The path-depth cases total 24 in `plan.md`, `tasks.md`, and `design/research.md`. The per-PR totals are 6, 8, 12, and 24.
- The remote check count is 143 in `design/research.md`, in the STATUS file, and in `summary.md`.
- The decision count is 14 in `design/research.md`, in the STATUS file, and in `summary.md`.
- The task count is 12 in `tasks.md`, in the STATUS file, and in `summary.md`.
- The requirement count is 15 in `spec.md`, in the STATUS file, and in the coverage table.
- The research rows 57 to 66 match the test-folder rows in `plan.md` PR-3 and PR-4.

## Metrics

- Requirements: 15 (FR-001 to FR-015). Success criteria: 6 (SC-001 to SC-006).
- Tasks: 12 (T001 to T008, and four final tasks).
- Moved items: 77, made of 52 `scripts/` children, 9 `tests/unit/scripts/` children, and 16 runbooks. `compose.ps1`, `test_script_imports.py`, and `SSR_ALARM_INDEX.md` stay.
- Path-depth cases: 24.
- Reference rows verified against main: 60.
- Remote checks: 143 (3 folders, 80 children, and 60 references).
- Decisions: 14. Human decisions: 0.
- Historical exclusions: 6 entries. They are two directories (`specs/` and `changelog.d/`), one changelog file (`CHANGELOG.md`), and three named files.

## Unresolved Items

- U-1 to U-7 in `design/research.md` remain open. Each has a reason and a task that resolves it in its pull request.
- No item needs a human decision. The historical exclusion and the closing keyword are recorded decisions, not human decisions.
