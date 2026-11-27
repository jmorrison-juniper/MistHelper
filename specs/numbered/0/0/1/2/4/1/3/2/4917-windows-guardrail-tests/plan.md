# Implementation Plan: Windows guardrail test failures

**Branch**: `fix/4917-windows-guardrail-tests` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/3/2/4917-windows-guardrail-tests/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, and checklists stay under `design/`. This record omits the contracts folder, because the change alters no menu, command, API, or output shape.

## Summary

Six guardrail test files fail on a Windows workstation. The causes are Bash calls, a `uv` lookup on PATH only, a symlink privilege, and two path forms. This plan skips the Bash cases on Windows with a printed reason. The export guard uses the pinned `uv` in the environment folder. The symlink case skips only for WinError 1314. Paths are compared as path objects. One setup note records the Windows behavior. Ubuntu CI keeps every proof that Windows skips.

## Terms

| Term | Meaning in this record |
| - | - |
| Windows workstation | The Windows 11 workstation named in issue #4917 |
| Ubuntu CI | The `ubuntu-latest` jobs of `.github/workflows/ci.yml` |
| Guardrail test | A test module under `tests/guardrails` |
| Bash case | A test case that runs a Bash command |
| Environment folder | `.venv\Scripts` on Windows, or `.venv/bin` on Linux and macOS |
| Pinned uv | The `uv==0.13.9` line in `requirements-dev.txt` (RC-21) |
| Symlink case | The `symlink` parameter of `test_unsafe_feature_selection_fails` |

## Technical Context

**Language/Version**: Python, from the repository environment folder.

**Primary Dependencies**: pytest, `pathlib`, `shutil`, `os`, and `sys`. No new dependency.

**Storage**: Not applicable. The change writes no product output.

**Testing**: pytest on the Windows workstation and on Ubuntu CI (RC-13). Ruff, Black, Bandit, the test quality analyzer, and `symbol-diff` run locally (RC-42, RC-43).

**Target Platform**: Windows 11 workstation and Ubuntu CI.

**Project Type**: Test-only change with one setup note and one changelog fragment.

**Performance Goals**: Not applicable. The change adds no runtime path.

**Constraints**: Lines stay at 120 characters or fewer (RC-27). Each changed line carries an inline comment (RC-28).

**Scale/Scope**: Eight files: seven changed and one added.

## Constitution Check

*Gate: passes before research and after design.*

| Principle or rule | Result | Reason and evidence |
| - | - | - |
| I. Five-item rule | Pass | No new direct child enters `tests\guardrails`, which holds 79 tracked children (RC-40). The fragment is a unique process record under `changelog.d\`, which the exception allows (RC-32). The existing `tests\guardrails` debt is recorded in Complexity Tracking. |
| II. Class-based architecture | Pass | The changes edit existing methods and add one test method to `TestDependencyExport`. No wrapper function is added. |
| III. Safety first | Pass | No input handling changes. No output carries a secret. The tests make no network call. |
| IV. Full deployment pipeline | Pass with a recorded deviation | Steps 1 to 9 map to T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 and 11 do not trigger, because the container build trigger does not list tests, changelog, or setup guide paths (RC-19). T-MERGE checks the merged commit on `main` instead (D-9). Step 12 has no deployable change. |
| V. Observability and logging | Pass | Every new skip reason and message is ASCII. No secret reaches a log line. |
| VI. Inline comments | Pass | Task T011 audits each changed executable line for an inline comment (RC-28). |
| VII. Action logging | Pass | Each new action logs an `info` line before and a `debug` line after (RC-41). The symlink creation and the interpreter-folder lookup are the new actions. |
| Technology: file paths | Pass | The changes use `Path` objects. The `as_posix()` calls format text only (RC-44). |
| Technology: mistapi | Pass | No Mist REST or SDK call changes, so no mistapi method applies. |
| Technology: package manager | Pass | The guard uses the pinned `uv` (RC-21). No dependency file changes. |
| Technology: container runtime | Pass | No container, compose, or Podman file changes. |
| Technology: data directory | Pass | The change writes no product output. Test files keep temporary paths in `tmp_path`. |
| Development workflow: testing | Pass | The verification commands run on the Windows workstation and on Ubuntu CI. |
| Security findings | Pass | No `# nosec`, `# noqa`, or `# type: ignore` comment is added. The symlink proof remains on Ubuntu CI, and the skip stays precise (D-3). |
| Documentation | Pass | The setup note changes in the same change, as AGENTS.md requires (RC-36). The README is unchanged, because no operation changes. |
| Release notes | Pass | One fragment is added (D-8, RC-30). |
| Multi-agent Git workflow | Pass | The issue carries `in-progress` before the branch exists, and the branch comes from `main` (RC-46). No open pull request changes these paths (`research.md`, Linked work). |

## Architecture

The change touches tests and one setup note. No product code path changes. The export guard gains one fallback lookup. The Bash cases gain one platform skip. The symlink case gains one precise skip. The Git root check and the analytics message compare normalized paths.

## File Change Map

| Repository path | Action | Requirements | Change |
| - | - | - | - |
| `tests/guardrails/e2e_timeout_budget/test_browser_installation.py` | Modify | FR-002, FR-003, FR-004 | Add `skipif(sys.platform == "win32")` to the five functions that call `execute`, at lines 71, 92, 111, 140, and 156. The parametrized function at line 140 gets the decorator above its `parametrize`. Lines 66, 169, and 179 stay unchanged. |
| `tests/guardrails/test_snmp_base_oid_defaults.py` | Modify | FR-002, FR-003 | Add `skipif(os.name == "nt")` above the `parametrize` of `test_shell_overrides` (line 85). The other two tests stay active. |
| `tests/guardrails/test_dependency_export.py` | Modify | FR-005 | Add `import sys`. In `DependencyExport.find_uv` (lines 38 to 46), check the environment folder of `sys.executable` after PATH. Change the lambda at line 135 to accept any arguments. Add `test_pinned_uv_beside_interpreter_is_found` to `TestDependencyExport`. |
| `tests/guardrails/test_spec_route_contract.py` | Modify | FR-006, FR-011 | Add `import logging` and a module logger. Wrap the symlink creation at line 296 in `try`. Skip only when `winerror` equals 1314. Re-raise every other error. |
| `tests/guardrails/local_test_quality_loop/test_scope.py` | Modify | FR-007 | Replace the string comparison at lines 643 to 645 with a `Path` comparison. |
| `tests/guardrails/test_analytics_package_structure.py` | Modify | FR-008 | Use `as_posix()` for the message at line 75 and for the expected text at line 177. |
| `documentation/development-setup.md` | Modify | FR-010 | Add `### Guardrail tests on Windows` under `## Step 4: Check the setup` (line 168), before `## Work on a change` (line 176). |
| `changelog.d/issue-4917-windows-guardrail-tests.md` | Add | FR-012 | One `###` heading and one `Fixed` bullet that names issue #4917. |

No file under `src\`, `.github\workflows\`, or the dependency files changes (FR-013).

## Dependencies

- No new package. The change uses pytest and the standard library.
- The export guard uses the pinned `uv` 0.13.9 in the environment folder (RC-21). Ubuntu CI installs the same pin before the export guard runs (RC-14).
- The Windows workstation needs Git on PATH for the Git root test. That need exists today.

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| R-1 | Windows `uv export` writes the output path in its header with a form that `DependencyExport.render` does not replace (U-4). | If the export guard reports stale exports on Windows, accept both the backslash form and the slash form of the output path. Run T-LOCAL-GATES again. |
| R-2 | `symbol-diff` reports the added `logging` import in `test_spec_route_contract.py` as a module-level change. | Run the gate after the edit. The gate targets lost declarations, so an addition should pass. If it reports the addition, fix the cause and keep the gate result. Do not suppress the gate. |
| R-3 | The test quality analyzer reports a new finding for the new test. | Repair the test. Do not change the baseline file to hide a finding. |
| R-4 | A Windows workstation with the symbolic link privilege runs the symlink case, so the predicted counts differ. | SC-001 gives both predicted results. |
| R-5 | A PATH `uv` with another version wins over the pinned copy. | The precedence stays unchanged, so CI and the workstation behave as they do now. |
| R-6 | The Ubuntu shard gains a skip by mistake. | The skip conditions use Windows values only. T-REMOTE-CI and SC-002 check the Ubuntu result. |

## Rollback

1. If the pull request is open and unmerged, close it. Delete the branch `fix/4917-windows-guardrail-tests`, and remove its worktree.
2. If the pull request merged, create a new branch from `main`. Run `git revert` on the squash commit of the merged pull request. Open a pull request for the revert. Do not force-push `main`.
3. The revert restores the 23 Windows failures. It changes no product data, no runtime path, and no stored output.

Warning: a force-push to `main` removes other changes that depend on this commit. Use a revert pull request instead.

## Contracts

Omitted. The change alters no menu operation, command, API request, API response, or output column. The helper `DependencyExport.find_uv` is an internal test method that returns a path or raises an error.

## Complexity Tracking

| Item | Current state | After this change |
| - | - | - |
| `tests\guardrails` direct children | 79 tracked children (RC-40). The existing debt is grandfathered. | 79. No child is added. The remediation is a follow-up issue (T012). |
| `find_uv` size | 11 lines, including the decorator and the signature | At most 25 lines, with one more block and one more lookup |
| `test_unsafe_feature_selection_fails` size | 15 lines (lines 287 to 301 of `test_spec_route_contract.py`) | At most 25 lines, with one `try` block |
| `TestDependencyExport` methods | 4 methods | 5 methods, which is the limit |
| `DependencyExport` methods | 5 methods | 5 methods. No method is added. |
