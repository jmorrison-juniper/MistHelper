# Implementation Plan: W0706 try-except-raise handlers in MistHelper.py

**Branch**: `chore/4132-w0706-try-except-raise` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Feature specification for issue 4132. The record folder is `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`.

## Summary

Delete seven re-raise-only handler pairs from `MistHelper.py`. Keep each `except Exception` handler that follows them. Keep every stop signal on its existing path. Add guard tests and stop-path tests to the narrow-except suite. Add the comments and action logging that the repository rules require in each touched function. Add one changelog fragment.

## Technical Context

- **Language/Version**: Python 3.15 or newer (constitution Technology section, R31).
- **Primary Dependencies**: None added. Pylint 4.1.4 (R47) and pytest run the checks.
- **Storage**: Not applicable.
- **Testing**: pytest, module `tests/unit/test_issue_1709_narrow_except.py` (R54).
- **Target Platform**: Windows, macOS, and Linux. The change adds no platform-specific code.
- **Project Type**: Single entry script with a menu (`MistHelper.py`).
- **Performance Goals**: None. The change adds two log calls to each of four functions and one log call to each of two functions.
- **Constraints**: No behavior change. ASCII-only log text. No suppression comment.
- **Scale/Scope**: Seven handler pairs (14 lines), six touched functions, one test module, one fragment, and one record folder.

## Constitution Check

The check passes before research and after design. Each rule shows its result and reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with recorded debt | The change adds no direct child to `tests/unit/` (R60). It adds one unique fragment to `changelog.d/`, which already holds 335 children (R59). |
| II. Class-Based Architecture | Pass | The change adds no wrapper function. It edits existing functions only. |
| III. Safety-First | Pass | Stop signals keep their path. The change edits no input handling and no `safe_input` call. |
| IV. Full Deployment Pipeline | Pass with tasks | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow steps 1 to 12 (R27 to R30). |
| V. Observability | Pass | New log text is ASCII. New logs use `%s` formatting and carry no secret. |
| VI. Inline Comments | Pass with tasks | Each touched line without a comment gets one (R23). |
| VII. Action Logging | Pass with tasks | Each touched external call or context read gets an info line before it and a debug line after it (R24). |
| Technology: mistapi | Pass | The change calls no Mist endpoint and no SDK function. The pin stays `mistapi==0.64.1` (R48). |
| Technology: Containers | Not applicable | The change starts no container. |
| Technology: File paths | Not applicable | The change adds no path construction. |
| Security findings: fix over suppress | Pass | The change removes the pattern. It adds no suppression (R17). |
| Documentation: release notes | Pass | One fragment is added (R25). |
| Specification escalation | Pass | The change touches three files, so this record is required. |
| Multi-agent git workflow | Pass | The issue exists with type `lint` and scope `MistHelper.py`. No open pull request changes `MistHelper.py`. |

## Five-Item Debt and Touched Violations

The constitution requires a record of each existing violation that this change touches. Each row names a separate remediation.

| Item | Measure on main | Action in this change | Separate remediation |
| - | - | - | - |
| `changelog.d/` direct children | 335 (R59) | Adds one unique fragment, which the constitution allows | Issue to reduce direct children through the release process |
| `tests/unit/` direct children | 50 (R60) | Adds no child | Issue to move test modules into compliant packages |
| `tests/guardrails/` direct children | 79 (R61) | Adds no child | Issue to move guard modules into compliant packages |
| `tests/unit/test_issue_1709_narrow_except.py` top-level functions | 40 (R55) | Adds six top-level test functions | Issue to split the module into compliant packages |
| `_invoke_one_systematic_test` length | 26 lines (main 6594 to 6619) | Stays at 26 lines, because two lines leave and two lines join | Issue to extract a helper |
| `__main__` block length | 98 lines (main 8276 to 8373) | Loses two lines | Issue to move the block into a function |

Every other touched function stays under 25 lines. `_check_and_upgrade_package` stays at 23 lines. `_run_tui_event_loop` stays at 20 lines. `_execute_interactive_menu_action` drops to 17 lines.

## Architecture and Change Map

A re-raise-only handler catches a stop signal and raises it again. The `except Exception` handler that follows never catches a stop signal (R65, R66). Deleting each pair therefore keeps the stop path.

Line numbers below refer to main at blob `98d7828479ded6bc4c83d15e0c1847171cfbfd49` (R01). Edit each function by its unique text, and read each line again before the edit.

| ID | Function (main line) | Lines to delete | Surviving handler | Additions to the touched function |
| - | - | - | - | - |
| M1 | `GlobalImportManager._check_and_upgrade_package` (1802) | 1820 to 1821 | `except Exception as e:` (1822) | Info line before the `_run_pip_show` call (1810), debug line after it |
| M2 | `_invoke_one_systematic_test` (6594) | 6610 to 6611 | `except Exception as exc:` (6612) | Info line before `func(**invoke_kwargs)` (6600), debug line after it |
| M3 | `_fast_mode_from_global` (6650) | 6654 to 6655 | `except Exception as error:` (6656) | Info line before the context read (6653), debug line after it. Return the stored flag. |
| M4 | `_fast_mode_from_cli_args` (6661) | 6666 to 6667 | `except Exception as error:` (6668) | Info line before the `args` read (6664), debug line after it. Return the stored flag. |
| M5 | `_run_tui_event_loop` (7795) | 7811 to 7812 | `except Exception as error:` (7813) | Info line before `tui.run()` (7808) |
| M6 | `_execute_interactive_menu_action` (8080) | 8094 to 8095 | `except Exception as error:` (8096) | Info line before `func()` (8089) |
| M7 | `__main__` block (8276) | 8343 to 8344 | `except Exception as e:` (8345) | None. The `finally` clause stays at line 8368 (R12). |

Each surviving handler comment gets this sentence: `Stop signals derive from BaseException and pass this handler.` The sentence keeps the reason in the code after the handler lines leave.

Log text uses the module logger, `%s` formatting, and ASCII characters only. A debug line after a read reports the stored value. It never reports a secret.

## Test Design

All new tests go in `tests/unit/test_issue_1709_narrow_except.py`. Each test function carries a docstring, and each line carries an inline comment.

| Function | Cases | Purpose | Passes before the change |
| - | - | - | - |
| `test_reraise_detector_flags_synthetic_handler` | 1 | Proves that the detector finds a re-raise-only handler in synthetic source. | Yes |
| `test_misthelper_has_no_reraise_first_handler` | 1 | Parses `MistHelper.py` with `ast`. Asserts zero offenders, states the examined count, and asserts no `try-except-raise` suppression text. | No. Reports seven offenders. |
| `test_main_block_keeps_keyboard_interrupt_and_finally` | 1 | Checks the handler names of the first try statement in the `__main__` block and checks that its `finally` clause exists. | No. A `SystemExit` handler exists. |
| `test_operator_stop_propagates` | 10 | Each stop signal reaches the caller unchanged, for ten function and signal pairs. | Yes |
| `test_ordinary_exception_is_still_handled` | 3 | A `RuntimeError` still returns the existing fallback in three functions. | Yes |
| `test_touched_fast_mode_readers_log_before_and_after` | 2 | An info record precedes a debug record for each fast-mode reader. | No. No info record exists. |

Stop-path setups for `test_operator_stop_propagates`:

- `_check_and_upgrade_package`: create the instance with `GlobalImportManager.__new__`. Patch `_run_pip_show` to raise the stop signal. Call with `("requests", "requests>=2.0")`. Cases use `KeyboardInterrupt` and `SystemExit(3)`.
- `_invoke_one_systematic_test`: pass a case whose function raises the stop signal, a `MagicMock` emitter, and an empty kwargs dict. Assert that `emit_test_fail` is not called. Cases use `KeyboardInterrupt` and `SystemExit(3)`.
- `_fast_mode_from_global`: patch `MistHelper.MainEntrypoint` with an object whose `context.fast_mode_enabled` raises the stop signal. Cases use `KeyboardInterrupt` and `SystemExit(3)`.
- `_fast_mode_from_cli_args`: patch `MistHelper.args` with `raising=False`. Its `fast` attribute raises the stop signal. Cases use `KeyboardInterrupt` and `SystemExit(3)`.
- `_run_tui_event_loop`: patch `src.interfaces.visualization.ui.tui.MistHelperTUI` with a class whose `run` raises `SystemExit(3)`. Patch `MistHelper.MainEntrypoint` with a context that has `apisession`. Patch `_handle_tui_exception` to fail if called.
- `_execute_interactive_menu_action`: call with `"7"`, a function that raises `SystemExit(3)`, and `container_mode=False`. Patch `_dispatch_post_menu_success` and `_handle_post_menu_exception` to fail if called.

Ordinary-exception setups for `test_ordinary_exception_is_still_handled`: `_check_and_upgrade_package` returns `True`, `_fast_mode_from_global` returns `False`, and `_fast_mode_from_cli_args` returns `False` when a `RuntimeError` occurs.

Integration evidence comes from the full pytest shards and the safe sweep `python MistHelper.py --test`. No integration boundary changes, so no new integration test is added.

## File-by-File Change Map

| Path | Action | Detail |
| - | - | - |
| `MistHelper.py` | Modify | Changes M1 to M7 |
| `tests/unit/test_issue_1709_narrow_except.py` | Modify | Adds `import ast` with an inline comment, the detector helper, and six test functions (18 cases) |
| `changelog.d/issue-4132-w0706-try-except-raise.md` | Add | One `###` heading and one `Changed` bullet that names issue 4132 |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/spec.md` | Add | Specification |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/plan.md` | Add | This plan |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/tasks.md` | Add | Task list |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/analysis.md` | Add | Consistency review |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/research.md` | Add | Decisions, remote checks, sources, unverified items |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/data-model.md` | Add | Not applicable line |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/quickstart.md` | Add | Reproduction and verification commands |
| `specs/numbered/0/0/1/1/3/0/1/2/4132-w0706-try-except-raise/design/checklists/requirements.md` | Add | Specification quality checklist |
| `CHANGELOG.md` | None | Must not change (constitution, R69) |
| `README.md`, `documentation/**` | None | No user-visible behavior change |
| `tests/guardrails/process_folder_baseline.json` | None | The record uses a managed root |
| `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` | None | No dependency or tool change |
| `.github/workflows/ci.yml` | None | CI scope stays unchanged (decision D-10) |

## Contracts

Omitted. The change alters no menu, no CLI option, no output column, and no API shape. The `design/contracts/` folder does not exist.

## Dependencies

- Pylint 4.1.4 is the pinned linter (R47). It runs the checks in T-LOCAL-GATES.
- Mistapi 0.64.1 stays pinned in `requirements.txt` (R48). The change does not use it.
- No package is added, removed, or upgraded.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| A later edit adds `except BaseException` below a removed handler | Stop signals are caught and the operator cannot stop the run | Caution: reviewers must reject the edit. Test B covers re-raise-only handlers only. |
| The new log lines break a caplog assertion in an existing test | A test fails in the full shards | Run the full shards in T-LOCAL-GATES. Test F checks presence only. |
| Line numbers move before the edit | A wrong line is deleted | Locate each handler by its unique text and re-read the line first. |
| CI pylint does not scan `MistHelper.py` (R32) | A regression stays unreported | Test B reads the rule in every test run. |
| Historical line citations drift (R45) | A documentation citation points to other code | Citations stay unchanged. CI `check-citations` scans `src` and `tests` only (R36). |
| `changelog.d/` grows | The five-item debt rises by one | The debt table records the change and the separate remediation. |

## Rollback

1. Create a branch from `main`. Run `git revert` on the squash commit and open a pull request.
2. Run `python -m pylint MistHelper.py` and confirm the seven W0706 lines return.

Caution: a revert restores the seven W0706 messages. No data or schema changes.

Warning: do not force-push `main` to remove a commit. The force push replaces shared history and cannot be undone for other clones.
