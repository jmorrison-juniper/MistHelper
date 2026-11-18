# Verified private-code cleanup

## Result

The bounded cleanup removes thirteen unused private root functions.
The nine original declarations have no remaining production caller.
Four dependent helpers have callers only inside the removed code.
All 196 explicit exports remain unchanged.
No remaining root function body changes.

The interim strict report contains eleven errors, zero warnings, and one analyzed file.
Ten errors require the held API and cache contracts.
One error names a live authentication-status helper with a held initializer caller.
The requested name-only handoff remains pending.
This is not a strict-clean completion.

## Caller verification

The audit parsed 2587 tracked Python files.
It examined name loads, attribute receivers, and exact lookup strings.
The source search also examined the removed names in production modules and tests.
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
AST comparison confirms identical remaining definitions and explicit exports.
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

Session tests now observe `MistSessionConfigurator.configure_once`, not obsolete root mocks.
A failed session strategy must never reach that boundary.
Real validation cases accept `mist_get` and `get`, reject an absent read method, and preserve the session shape.
The existing context regression verifies one transport configuration pass.

Dependency tests run `initialize_dependencies` with only the package-import boundary mocked.
Both full and minimal paths publish the exact supplied object.
A second call performs no additional import.
Critical import failure retains exit code 1.
Test mode retains the explicit failed-import state without aborting.

## Remaining contracts

The API source and cache source remain byte-identical to the base.
Dependency manifests and held tests remain unchanged.
The two archived owners still require restoration and narrow handoffs.

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

The API annotation remains `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`.
The cache methods still require `generate_function: Callable[[], object]`.
No caller cast, new adapter, or stub conceals either held source contract.

Removing the dead validator exposes `reportUnusedFunction` on `_log_session_auth_status` at line 3314.
Unlike the thirteen removed functions, it has a real production caller.
`MistSessionConfigurator._validate_methods` calls `_MH._log_session_auth_status` at initializer line 144.
The additional request covers only that reference and directly related documentation.
Do not delete the live helper or add a dummy root reference.

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
The final issue comment will identify the immutable commit and post-commit quality result.
No publication, merge, production operation, or hold release occurs.
