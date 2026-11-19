# Corrective review and remaining work

This record describes candidate one.
Its 19-error result and unchecked task list are historical.
See `analysis.md` for the split candidate results.

## Result

The corrected candidate has 19 strict errors, zero warnings, and one analyzed file.
The baseline has 108 errors.
This is not a strict-clean completion.
Candidate one left T003, T007, T008, and T010 unchecked.

The correction preserves commits `ed7f550066e16a21aabac1132ffbd7906ead8718` and `aa185b899cfd8b073e2277fe3ec4d57a258836ed`.
The base remains `b7a18b7ead7b1de5882bcd288203c015b1eef792`.
The issue handoff records the corrective commit identifier.
No publication or merge is authorized.

## Rejected approaches

The original ten-error candidate expanded `__all__` and substituted dynamic imports.
Those changes did not establish the required contracts.
The correction removes all 44 private exports and restores the historical snapshot.
The explicit export list remains identical to the base, with 196 names.
Static SDK and address-normalizer imports are restored.
No checker rule is disabled.

## Real host interfaces

The original private names below now omit their leading underscore.
Each group has a verified production caller.
No alias preserves the previous private name.

| Caller | Public host helpers |
| - | - |
| `MainEntrypoint` and `ApplicationBootstrap` in `main_entrypoint.py` | `build_argument_parser`, `setup_runtime_flags`, `initialize_dependencies`, `configure_runtime_options`, `early_dependency_check`, `establish_mist_session`, `dispatch_main_mode` |
| `RunSystematicTestManager` in `run_systematic_test.py` | `print_systematic_banner`, `build_systematic_test_options`, `print_systematic_pre_run_counts`, `initialize_systematic_telemetry`, `resolve_systematic_test_context`, `execute_systematic_test_loop`, `finalize_systematic_telemetry`, `print_systematic_summary`, `report_systematic_outcome` |
| `RunInteractiveTestManager` in `run_interactive_test.py` | `build_interactive_test_runner` |
| `SwitchToInteractiveLoginManager` in `switch_to_interactive_login.py` | `print_switch_login_header`, `prompt_switch_login_confirmation`, `attempt_interactive_login_with_rollback`, `handle_interactive_login_success` |
| `MistSessionInitializer.initialize` in `initialize_mist_session.py` | `load_mistapi_module`, `introspect_apisession_class`, `attempt_all_session_strategies`, `log_failed_session_variants` |
| `_load_menu_actions` in `wsgi.py:91` | `configure_session_timeout` |

The source services resolve host helpers through the existing `SourceDependencyResolverService._resolve_host_symbol`.
That method reads the bound host with `getattr`.
WSGI imports the root module and calls its timeout helper directly.
The initializer handoff permits only its four matching references.
All other initializer body lines remain unchanged.

The nine mode handlers remain private.
The actual dispatcher now stores direct typed handlers in its local table.
It evaluates predicates in the same order and stops at the first match.
It binds handler replacements on each invocation.
The previous module-level `_MAIN_MODE_TABLE` is removed.
There is no second registry, getter layer, or compatibility adapter.

The symbol tool reports 27 removed names and 30 added names.
The removed names are 26 renamed helpers and the moved private table.
AST reconciliation confirms zero missing callable or class definitions.
This is an intentional interface change, not a clean unchanged-symbol result.

## Reproducible third-party analysis

Run this exact command from the repository root after the locked bootstrap:

```text
rtk bypass uvx --from pyright==1.1.414 pyright --project specs/numbered/0/0/1/2/3/0/1/3/4758-strict-pyright-repairs/design/contracts/pyright.json --outputjson
```

Omit `--outputjson` for text output.
The command exits 1 with `19 errors, 0 warnings, 0 informations`.
The committed configuration uses repository-relative paths and the worktree `.venv`.
It does not replace default project checks.
The baseline and the rejected candidate used the earlier session configuration.

The bounded declarations cover `scourgify.normalize_address_record`, the SDK root reexports, `LogSanitizer`, and `listSiteDevices`.
The endpoint signature matches the installed SDK, including optional filters and pagination.
The SDK session and response types remain the installed definitions.
The root reexports retain installed pagination contracts, including their existing incomplete return annotations.
The declarations do not claim complete SDK or scourgify coverage.
Direct imports of uncovered SDK internals can still report missing declarations.
The address declaration covers documented string-valued address fields and two-line normalization callbacks.
No vendor implementation is copied.

Static probes accept supported SDK and address calls with zero errors.
Negative probes reject integer address and site identifiers with two `reportArgumentType` errors.
Each probe analyzes one file.
No probe executes a network operation.

## Candidate-one held-contract diagnostic map

All locations below refer to `MistHelper.py`.
Candidate one kept the API and cache sources byte-identical to its base.
Candidate three applies only the annotations authorized by the user.
Its AST comparison confirms that function bodies, defaults, and imports are unchanged.

| Line | Rule | Required source contract |
| - | - | - |
| 1340 | `reportUnknownMemberType` | Cache callback |
| 3747 | `reportUnknownMemberType` | Cache callback |
| 3747 | `reportUnknownArgumentType` | Cache callback |
| 3773 | `reportUnknownMemberType` | API site records |
| 5868 | `reportUnknownMemberType` | API site records |
| 5907 | `reportUnknownMemberType` | API site records |
| 5930 | `reportUnknownMemberType` | API site records |
| 8066 | `reportUnknownVariableType` | API site records |
| 8066 | `reportUnknownMemberType` | API site records |
| 8067 | `reportUnknownArgumentType` | API site records |

The API contract is `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`.
The cache methods require `generate_function: Callable[[], object]`.
Candidate three applies these contracts without a cast, duplicate implementation, or consumer adapter.

## Preserved declarations

Each row retains one `reportUnusedFunction` error.
These nine errors are not ownership blockers.
An audit examined tracked Python loads, attribute receivers, and exact lookup strings.
Documentation references are not production calls.

| Root declaration and lines | Production or resolver call | Test or string reference |
| - | - | - |
| `_get_tuning_data_file_path`, 2445-2461 | None | `test_rate_limiting.py:885` calls the separate `rl` helper, not the root function |
| `_is_help_invocation`, 2490-2492 | None | `test_help_invocation_side_effect_free.py:39` returns the actual root helper |
| `_reject_unsupported_flag_variants`, 2495-2499 | None | No root caller or exact lookup string |
| `_exit_on_unsupported_flag`, 2502-2506 | None | No root caller or exact lookup string |
| `_snapshot_session_globals_to_state`, 2637-2648 | None | No root caller or exact lookup string |
| `_restore_session_globals_from_state`, 2651-2665 | None | No root caller or exact lookup string |
| `_validate_initialized_session`, 3421-3440 | None | `tests/unit/refactors/test_initialize_mist_session.py:73,142` retain mock keys and a zero-call assertion |
| `_install_default_request_timeout`, 3475-3506 | None | No root caller or exact lookup string |
| `_initialize_deferred_imports`, 7428-7436 | None | `test_main_entrypoint.py:51` retains a mock key, not a real invocation |

The full help-test path is `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py`.
The full entry-point-test path is `tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py`.
The separate rate-limit test is `tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py`.

The timeout audit also found a same-named `LoginOrchestrator` method.
That method is not the root helper.
Its source and tests remain unchanged.
The real root caller is WSGI, and its single reference now uses the public name.

### Separate cleanup candidate

The smallest independent cleanup is `_exit_on_unsupported_flag`, five lines with no tracked caller or test reference.
The same evidence identifies five other uncalled root declarations.
They are `_get_tuning_data_file_path`, `_reject_unsupported_flag_variants`, both session-state helpers, and `_install_default_request_timeout`.
Together, these six declarations occupy 86 physical lines.
A separately approved cleanup can remove them without touching the unrelated rate-limit helper.
Retain the three test-referenced seams until their intended test contracts are decided.
This correction removes none of the nine declarations.

## Validation and evidence

The final regression command records 1139 passed tests, two documented skips, and the existing Dash warning.
Its full expanded command and output are in `correction-regressions.txt`.
The skips require a pull-request event or an absent unregistered registry class.

`correction-gates.txt` records every exact command and exit code.
Compile, repository Ruff, changed-file Black, mypy, Bandit, pydocstyle, interrogate, Pylint, and Vulture exit 0.
Mypy checks 887 source files.
Docstring coverage is 98.9 percent.
Pylint scores 9.51 against the 9.5 threshold.
The changed-source complexity command reports every function within the threshold of 10.
Menu regeneration changes no generated reference.
The isolated WSGI test executes only its menu-loader function, not authentication or module startup.
The import tests exercise static import behavior through `sys.modules`.

The unrelated missing interactive timeout module is tracked separately in issue #4827.
Its source remains unchanged.
The focused Pylint reproduction exits 30 and scores 9.14.
Existing issues #4825 and #4826 retain the other unrelated findings.

The persistent session evidence retains the original baseline and rejected-candidate JSON and text.
The corrected reports are `pyright-correction.json` and `pyright-correction.txt`.
The session also retains `preserved-seam-references.json`, symbol results, preservation results, and positive and negative stub probes.
The post-commit test-quality result belongs in the final issue handoff.
Full-suite coverage, production sweeps, browsers, and dependency audits are not claimed.

## Bounded completion

1. Restore the API owner and obtain its annotation-only handoff.
2. Restore the cache owner and obtain its annotation-only handoff.
3. Apply the two contracts and rerun their focused regressions.
4. Obtain approval for the six-declaration cleanup and decide the three test-referenced seams.
5. Rerun the committed strict command and require one analyzed file with zero errors.
6. Complete the unchecked tasks only after that evidence exists.
