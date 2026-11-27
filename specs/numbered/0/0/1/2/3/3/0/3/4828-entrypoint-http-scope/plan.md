# Implementation Plan: Entry-point test quality for HTTP status scope

## Summary

Finish issue #4828 in two stages. Stage one removes one duplicate argument test in this repository. Stage two pins the analyzer fix from `misthelper-devtools`, refreshes the baseline, and closes the issue. The analyzer change stays outside this repository.

## Technical Context

- **Language**: Python 3.15 or newer. The requirement appears in `.github/copilot-instructions.md`, section "Language and environment".
- **Test tooling**: pytest, ruff, and black. The CI jobs run `ruff check .` (RC-53) and `black --check --diff .`.
- **Test quality analyzer**: misthelper-devtools at commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-28, RC-29, RC-30).
- **Mist SDK**: mistapi 0.64.1 (RC-31). This record does not change the SDK.
- **Host**: Windows 11 with the local `.venv`. The commands use forward slashes in repository paths.
- **Scope**: One test module changes in this repository. Three test modules keep baseline findings. The baseline file changes after the analyzer pin.

## Constitution Check

| Principle | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one folder under an empty route (RC-45). Each new folder holds five children or fewer. The test edit removes lines and adds no parameter or block. |
| II. Class-Based Architecture | Pass | `TestMainEntrypointRun` keeps its remaining methods. No wrapper function is added. |
| III. Safety-First | Pass | No input handling or destructive operation changes. No menu in the destructive set changes. |
| IV. Full Deployment Pipeline | Pass | The plan runs local gates, commits, rebases, pushes, opens a pull request, passes CI, and squash merges. Steps 10 to 12 also apply, because `pyproject.toml` and `uv.lock` trigger `container-build.yml` (RC-41, RC-59). |
| V. Observability and Logging | Pass | No runtime log statement changes. The deleted test contains no log statement. |
| VI. Inline Comments | Pass | The change adds no code line. The pin comment in `pyproject.toml` changes with the pin (T006). |
| VII. Action Logging | Pass | No action in product code changes. |
| Technology constraints | Pass | mistapi stays the only Mist interface. The change adds no HTTP request. |
| Testing constraints | Pass | `python -m py_compile MistHelper.py` runs before the commit (constitution line 370). |
| Security findings | Pass | No finding gets suppressed. The analyzer rules stay enabled (RC-21, RC-22). |
| Documentation | Pass | No user-visible behavior changes, so no changelog fragment is added (`.github/copilot-instructions.md`, section "Git and GitHub in this repository"). |
| Spec records | Pass | The route follows the base-5 rule (RC-44, RC-45). |
| Complexity-driven escalation | Pass | The change touches five files. The constitution requires a spec for three or more files. |

## Architecture

**CLI path**: `MistHelper.py` calls `MainEntrypoint.run` (`src/foundation/support/refactors/main_entrypoint.py`, line 400, RC-10). `run` constructs `ApplicationBootstrap`, whose constructor calls `_parse_arguments` (lines 129 to 132). Argparse exits for help before `bootstrap_for_cli` runs (line 148).

**Startup path**: `bootstrap_for_cli` calls `_run_common_startup` (line 173). That method calls `_configure_logging` (line 193). `_configure_logging` calls `_install_log_sanitizer` (lines 219 to 228). The method imports `mistapi.__logger.LogSanitizer` at line 222 (RC-09).

**Web path**: `wsgi.py` loads `ApplicationBootstrap` (line 22) and calls `bootstrap_for_web` (line 32, RC-42). The web path reaches the same startup methods.

**Analyzer path** (misthelper-devtools at `2239e7bd`): `_risk_from_import_from` (line 304) calls `_risk_from_symbol` (lines 323 to 328). For a class, `_risk_from_symbol` inspects the whole class body (RC-32). `_risk_from_source` (line 356) checks each node with `_node_has_http_status_risk`, which spans lines 370 to 379. That method treats a from-import of `mistapi` as HTTP status risk (RC-33, RC-34). `MissingFailureModeDetector` emits `missing_fm_http_4xx` at line 708 and `missing_fm_http_5xx` at line 717 (RC-35, RC-36).

## File-by-File Change Map

| Path | Action | Change | Requirement |
| - | - | - | - |
| `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` | Modify | Delete lines 158 to 166, which hold `test_empty_argument_list_reaches_normal_startup` and one blank line. | FR-003 |
| `pyproject.toml` | Modify | Change the pin on line 123 and the comment on line 122 to the fixed commit. | FR-006 |
| `uv.lock` | Modify | Regenerate with `uv lock`. The `misthelper-devtools` blocks near lines 1532 and 1584 to 1586 change. | FR-006 |
| `requirements-dev.txt` | Modify | Change the pin on line 197. Regenerate the file with the export command in line 2. | FR-006 |
| `.github/test-quality-baseline.json` | Modify | Remove stale entries (RC-18, RC-19) and any other stale entry. Add no entry. | FR-007 |
| `specs/numbered/0/0/1/2/3/3/0/3/4828-entrypoint-http-scope/` | Add | Add this record. | Process |
| `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` in `misthelper-devtools` | Modify, external | Limit class inspection to the code under test. Exclude the `mistapi` logging module from HTTP risk. | FR-005 |
| `src/misthelper_devtools/test_quality_analyzer/fixtures/good/` in `misthelper-devtools` | Add, external | Add the good fixture for the unrelated logging import. The folder path is inferred (Unverified U-08). | FR-005 |

**Not changed**: `src/foundation/support/refactors/main_entrypoint.py`, `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py`, `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py`, `.github/test-quality-config.toml`, `.github/workflows/ci.yml`, `CHANGELOG.md`, and `changelog.d/`.

## Dependencies

- **misthelper-devtools**: Pinned at `2239e7bd` (RC-28 to RC-30). The fixed commit replaces the pin after the external fix merges. Owner: the misthelper-devtools repository.
- **mistapi 0.64.1**: Unchanged (RC-31).
- **uv**: Regenerates `uv.lock` and `requirements-dev.txt`. The CI job `dependency_lock` checks the lock (RC-25).
- **Open pull request 4888**: Changes `requirements-dev.txt` (RC-49).
- **Record 4758**: Related and closed. Its entry-point contract states the help-test rule (RC-43).
- **New runtime dependency**: None.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| R-1: The analyzer fix does not merge. | The issue stays open, and three modules keep baseline debt. | Keep T004 to T007 as blocked tasks. Report the blocker. |
| R-2: The baseline refresh adds entries. | The gate can hide a new finding. | Stop on each added line. Review each removed line in the pull request (T007). |
| R-3: The pin change starts `container-build.yml`. | A container image builds after merge. | Follow Principle IV steps 10 to 12 (T-MERGE). |
| R-4: Pull request 4888 edits the same file. | A merge conflict on `requirements-dev.txt`. | Wait for it to merge, or rebase after it merges (T-PR). |
| R-5: The duplicate deletion removes the only case for an input. | A parser case loses coverage. | Verify the help case `["MistHelper.py"]` before the deletion (T001, T003). |
| R-6: Baselined modules gain tests that import the bootstrap class. | Growth stays hidden from the gate. | Review each test diff in the three modules (analysis A-03). |
| R-7: The pin comment names the old release. | A reader trusts a wrong release tag. | Update `pyproject.toml` line 122 with the pin (T006). |
| R-8: Shared workflow pins name a different commit. | Advisory drift between two pins. | Keep the workflow pins unchanged in this record (analysis A-06). |

Caution: Do not add `--roots` to a baseline command. The command then drops entries for files that the scan does not reach.

## Rollback Steps

1. Revert the test deletion commit on the pull request branch with `git revert`. Do not force-push.
2. Revert the pin commit with `git revert`. Run `uv lock --check` to confirm the lock.
3. Revert the baseline commit with `git revert`. Run the full-suite gate.
4. If the change breaks `main`, open a new issue. Branch again from `main`.

## Project Structure and Folder Limits

- Feature root: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`. That is five children.
- `design\`: `research.md`, `data-model.md`, `quickstart.md`, `contracts\`, and `checklists\`. That is five children.
- `design\contracts\`: two files. `design\checklists\`: one file.
- The route folder `specs\numbered\0\0\1\2\3\3\0\3` is empty on `main`. The record adds one child to that folder.

## Contracts

Two interface contracts apply. `design\contracts\cli-entrypoint.md` describes help and argument behavior. `design\contracts\test-quality-gate.md` describes the gate command and the baseline commands.

## Complexity Tracking

| Item | Kind | Remediation |
| - | - | - |
| `test_main_entrypoint.py` keeps the bootstrap import for logging tests. | Grandfathered debt | T004 to T007. Removed when the analyzer fix pins. |
| `test_app_context_session_state.py` keeps the bootstrap import for web tests. | Grandfathered debt | T004 to T007. Removed when the analyzer fix pins. |
| `test_fast_mode_small_seams.py` keeps the bootstrap import for fast-mode tests. | Grandfathered debt | T004 to T007. Removed when the analyzer fix pins. |
| Analyzer class-body scope and `mistapi` import rule. | Grandfathered debt in another repository | T004 and T005. |
| New design in this change. | None | No new violation is added. |
