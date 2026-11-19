# Verified private-code cleanup

## Historical checkpoint

This record describes the cleanup stage before the final API and cache annotations.
Its ten-error strict result is historical.
The final combined report is in [analysis.md](../../analysis.md).

## Result

The bounded cleanup removes thirteen unused private root functions.
The nine original declarations have no remaining production caller.
Four dependent helpers have callers only inside the removed code.
All 196 explicit exports remain unchanged.
No remaining root function body changes.
The live authentication-status helper has its approved public name.

At this cleanup stage, the strict report contained ten errors and one analyzed file.
The later authorized API and cache annotations resolve those errors.
The earlier eleven-error report remains preserved.
The additional initializer-reference handoff resolves its live authentication-status interface.
This checkpoint was not strict-clean.

## Caller verification

The audit parsed 2587 tracked Python files.
It examined name loads, attribute receivers, and exact lookup strings.
The source search checked `getattr`, `_MH`, `MistHelper`, and string-keyed references in `src/`, `scripts/`, and `tests/`.
Historical documentation is not a runtime caller.

The open pull-request comparison found no overlap with the three test edits.
Issue searches included their exact file names and matching issue comments.
The initializer test appears in old test commands, not a reservation on these edits.
The held ARP and cache tests remain unchanged.

Locations below identify definitions in commit `e5f796d9689e17b5a8ad7b5a43b0c349eb3dee90`.

| Removed root function | Previous lines | Verified disposition |
| - | - | - |
| `_get_tuning_data_file_path` | 2445-2461 | No root caller. The rate-limit test calls a different `rl` function. |
| `_is_help_invocation` | 2490-2492 | Only the obsolete help test called it. Tests now use the real parser and bootstrap. |
| `_reject_unsupported_flag_variants` | 2495-2499 | No caller or exact lookup string. Argparse handles invalid flags. |
| `_exit_on_unsupported_flag` | 2502-2506 | No caller or exact lookup string. Argparse owns the failure exit. |
| `_snapshot_session_globals_to_state` | 2637-2648 | No caller or exact lookup string. The application context owns state transfer. |
| `_restore_session_globals_from_state` | 2651-2665 | No caller or exact lookup string. The application context owns state transfer. |
| `_ensure_mist_get_method` | 3345-3364 | Its only caller was the removed validator. The configurator validates current sessions. |
| `_validate_initialized_session` | 3421-3440 | Only obsolete mock keys and a zero-call assertion remained. Tests now exercise the configurator. |
| `_install_default_request_timeout` | 3475-3506 | No caller or exact lookup string. The current configurator retains its timeout adapter. |
| `_report_tqdm_status` | 7390-7399 | Its only caller was the removed deferred-assignment helper. |
| `_apply_deferred_assignments` | 7402-7413 | Its only caller was the removed deferred cycle. |
| `_run_deferred_import_cycle` | 7416-7425 | Its only caller was the removed deferred initializer. |
| `_initialize_deferred_imports` | 7428-7436 | Only an obsolete mock key remained. The public dependency initializer is the live path. |

These definitions occupied 170 physical lines, excluding separating blank lines.
The audit found no other removed root definition.
AST comparison confirms identical remaining bodies and explicit exports after accounting for the approved definition rename.
The existing rate-limit helper and its tests remain unchanged.

## Meaningful behavior checks

Help tests execute the actual argument parser through the public `MainEntrypoint.run` path.
They verify both documented flags, mixed arguments, parser-supported abbreviations, and invalid tokens.
They prove that a help-like program name is not an argument.
A startup failure sentinel prevents dependency, log, or authentication work if parsing regresses.
Fresh subprocesses test both help flags from an empty temporary directory.
Neither subprocess creates `data/`.

The old helper rejected `-help`, but the actual parser accepts it.
Python also always supplies a program name in ordinary process arguments.
The replacement tests follow the real parser instead of retaining those artificial helper assumptions.
No production parser setting changes.

The first committed tests imported the whole `ApplicationBootstrap` class.
The quality analyzer inferred HTTP risk from its unrelated SDK log-sanitizer import.
Issue #4828 records that shared-tool defect for later repair.
The revised tests call the actual CLI entry point and fail if it reaches context activation.
They retain real parsing, stronger startup ordering, and the fresh subprocess checks.
No fake HTTP case, changed rule, baseline entry, or dynamic import bypasses the finding.

The test mapping below identifies the replacement behavior checks.

| Removed private seam | Replacement check |
| - | - |
| `_is_help_invocation` | `TestHelpArgumentParsing.test_help_stops_before_startup`, `test_program_name_is_not_a_help_argument`, and `TestHelpSubprocessInvocation.test_help_exits_without_runtime_files` |
| `_reject_unsupported_flag_variants` | `test_invalid_help_variants_fail_before_startup` and `test_hyphenated_test_flag_uses_standard_argparse_error` |
| `_exit_on_unsupported_flag` | `test_hyphenated_test_flag_uses_standard_argparse_error` |
| `_snapshot_session_globals_to_state` | `test_context_reads_writes_and_deletes` and `test_two_app_context_instances_do_not_share_state` |
| `_restore_session_globals_from_state` | `test_context_reads_writes_and_deletes` and `test_two_app_context_instances_do_not_share_state` |
| `_validate_initialized_session` | `test_supported_read_method_is_accepted` and `test_missing_read_method_is_rejected` |
| `_install_default_request_timeout` | No root caller or root test existed. `test_wsgi_menu_loader_uses_public_timeout_contract` checks the live timeout interface at `tests/unit/refactors/test_app_context_session_state.py:239`. |
| `_get_tuning_data_file_path` | No root caller or root test existed. A distinct helper in `src/foundation/support/utils/rate_limiting.py` is tested at `tests/unit/config/standalone/foundation/support/utilities/network/test_rate_limiting.py:885`. |
| `_initialize_deferred_imports` | No production call existed. The obsolete mock key was removed. `test_initialization_publishes_assignments_once` checks live dependency setup, and `test_help_stops_before_startup` checks the parser boundary. |

The help test now uses real parser cases instead of direct calls to the deleted predicate.
Its five test methods cover 16 cases and pass.

| Removed test method | Replacement behavior check |
| - | - |
| `test_bare_double_dash_help_is_detected` | `TestHelpArgumentParsing.test_help_stops_before_startup` and `TestHelpSubprocessInvocation.test_help_exits_without_runtime_files` cover `--help`. |
| `test_bare_short_help_flag_is_detected` | The same methods cover `-h`. |
| `test_help_combined_with_other_flags_is_detected` | `test_help_stops_before_startup` covers both combined flag sequences. |
| `test_empty_argv_and_program_only_are_not_detected` | `test_empty_argument_list_is_not_help` covers an empty parser input. `test_program_name_is_not_a_help_argument` covers the program-only case. |
| `test_program_name_is_ignored_even_if_it_matches` | `test_program_name_is_not_a_help_argument` covers `sys.argv == ["--help"]`. |
| `test_substring_and_case_variants_are_not_detected` | `test_invalid_help_variants_fail_before_startup` covers `--helpme`, `help`, and `--HELP`. The real parser accepts `--h` and `-help` as help forms, so `test_help_stops_before_startup` covers those forms. |
| `test_unrelated_flags_are_not_detected` | `test_program_name_is_not_a_help_argument` covers `--menu 1 --org abc`. |
| `test_early_dependency_check_is_guarded` | `test_help_stops_before_startup` and the subprocess check prove that help exits before startup. |
| `test_deferred_imports_conditional_includes_help` | The same parser and subprocess checks prove that help exits before deferred startup work. |
| `test_help_exits_cleanly_with_usage_on_stdout` | `TestHelpSubprocessInvocation.test_help_exits_without_runtime_files` covers both `--help` and `-h`, usage output, exit code, and absence of runtime files. |

The empty argument case uses `ApplicationBootstrap(argv=[])`.
The case remains safe because the test replaces context activation with a failing mock.

Session tests now observe `MistSessionConfigurator.configure_once`, not obsolete root mocks.
A failed session strategy must never reach that boundary.
Real validation cases accept `mist_get` and `get`, reject an absent read method, and preserve the session shape.
The existing context regression verifies one transport configuration pass.

Dependency tests run `initialize_dependencies` with only the package-import boundary mocked.
Both full and minimal paths publish the exact supplied object.
A second call performs no additional import.
Critical import failure retains exit code 1.
Test mode retains the explicit failed-import state without aborting.

## Contracts at this cleanup checkpoint

At this checkpoint, the API and cache sources remained byte-identical to the base.
The later user instruction authorized annotation-only changes in both files.
Their function bodies and defaults remain unchanged.
Dependency manifests and held tests remain unchanged.

| Current line | Rule | Held contract |
| - | - | - |
| 1340 | `reportUnknownMemberType` | Cache callback |
| 3600 | `reportUnknownMemberType` | Cache callback |
| 3600 | `reportUnknownArgumentType` | Cache callback |
| 3626 | `reportUnknownMemberType` | API site records |
| 5721 | `reportUnknownMemberType` | API site records |
| 5760 | `reportUnknownMemberType` | API site records |
| 5783 | `reportUnknownMemberType` | API site records |
| 7870 | `reportUnknownVariableType` | API site records |
| 7870 | `reportUnknownMemberType` | API site records |
| 7871 | `reportUnknownArgumentType` | API site records |

The final API annotation is `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`.
The final cache methods use `generate_function: Callable[[], object]`.
No caller cast, new adapter, or stub conceals either source contract.

Removing the dead validator exposed `reportUnusedFunction` on `_log_session_auth_status` at line 3314.
Unlike the thirteen removed functions, it has a real production caller.
The additional handoff permits its definition rename to `log_session_auth_status` and the single initializer reference.
`MistSessionConfigurator._validate_methods` now calls `_MH.log_session_auth_status` without changing arguments or control flow.
The helper body, authentication detection, logs, return values, and all transport behavior remain unchanged.
No alias or dummy root reference exists.

The audit examines every initializer `_MH` private attribute and exact private string value.
Before the rename, only `_log_session_auth_status` and `_parse_api_tokens` reference private root functions.
The latter has surviving root callers in `_collect_credential_problems` at line 2878 and `_systematic_test_has_api_token` at line 6519.
The string `_session` identifies the SDK transport attribute, not a root helper.
No additional private interface requires a rename after this cleanup.
The existing initializer test now observes the real public report for both supported read methods.

## Evidence

The existing strict configuration and bounded package stubs remain unchanged.
Run the exact strict command in [the plan](../../plan.md).
The new reports remain beside the original baseline and prior candidates in session storage.
`cleanup-reference-audit.json` records every matching tracked reference before deletion.
`cleanup-preservation.json` records removed definitions, unchanged bodies, and held-file comparisons.
`cleanup-regressions.txt` records 1145 passed tests, two documented skips, and the existing Dash warning.
`cleanup-gates.txt` records exact commands and exit codes.

Compile, repository Ruff, Black, mypy, Bandit, docstrings, Pylint, and Vulture pass.
Mypy checks 887 source files.
Docstring coverage is 99.0 percent.
Pylint scores 9.70 against the unchanged 9.5 threshold.
The final issue update records the refreshed reports and post-commit quality result.
No push, pull request, merge, or production operation occurs.
