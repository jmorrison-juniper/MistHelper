# Analysis and local verification

## Final combined candidate

The branch `fix/4758-strict-pyright-session` now starts at current `origin/main` commit `390f535dab7331cdc6c95d808a850019dffe04d5`.
The pre-rebase implementation and focused-test commits remain on `preserve/strict-pyright-session-28212ef`.
Main advanced through PR #4839 during final validation.
The branch was rebased onto that commit with no overlapping changed paths.
The requested branch name already exists locally, so this candidate keeps its separate session branch.
The strict baseline on the original task base had 108 errors.
The final strict run analyzes three files and reports zero errors and zero warnings.

Run strict Pyright with this command:

```text
rtk bypass uvx --from pyright==1.1.414 pyright --project specs/numbered/0/0/1/2/3/0/1/3/4758-strict-pyright-repairs/design/contracts/pyright.json --outputjson
```

The JSON summary reports `filesAnalyzed: 3`, `errorCount: 0`, and `warningCount: 0`.
Text mode reports `0 errors, 0 warnings, 0 informations`.
Both commands exit 0.
The exact reports are `pyright-final.json` and `pyright-final.txt` in the session evidence directory.

The focused selection passes 410 tests with one existing Dash warning.
The parser and bootstrap tests pass 16 cases across the help and entry-point test modules.
It covers `--help`, `-h`, parser-supported abbreviations, invalid help tokens, program-name handling, unrelated flags, and side-effect-free subprocess calls.
The explicit export list remains equal to current main with 196 names.
AST comparison confirms that all 16 shared API and cache function bodies and defaults remain unchanged.
The five source annotations type two API list returns, two cache callbacks, and the CSV writer.
No imports changed.

| Check | Result |
| - | - |
| Full Ruff | Exit 0 |
| Full Black | Exit 0, 2,589 files unchanged |
| Changed-file `py_compile` | Exit 0 |
| CI-path mypy | Exit 0, 887 source files |
| Bandit on changed production files | Exit 0 |
| STE on the seven edited feature records | Exit 0, scores from 94 to 99 |
| STE on `documentation/CONTRIBUTING-MistHelper.md` | Exit 0, score 98 |
| Test-quality preflight | Exit 0, one test passed |
| Test-quality committed-change gate | Exit 0, 18 files and 10 findings checked, two skipped, zero parse errors, zero new findings |
| `symbol-diff --base origin/main MistHelper.py` | Exit 1, intentional change: 41 lost and 31 added names |
| Menu reference generators | Both exit 0 and leave no changed files |
| `git diff --check origin/main...HEAD` | Exit 0 |
| STE check for the contributor symbol map | Exit 0, score 98/100 |

`symbol-diff --base origin/main MistHelper.py` exits 1 because the entry-point interface changed.
It reports 41 lost and 31 added names.
The changes comprise 27 verified public renames, 13 unused private removals, one removed private mode table, and four new typed declarations.
The [correction record](design/contracts/correction.md) maps each public name to its production consumer.
The [cleanup record](design/contracts/cleanup.md) lists each removed declaration and its prior references.
The contributor symbol map now uses live names.
The whole-tree audit found no removed-root reference, resolver lookup, mock key, or dynamic root access in production code or tests.
The only same-name runtime helper is the separate rate-limit function in `rate_limiting.py` and its test.
Historical changelog, compliance, and feature records retain names from their original context.
One JSON evidence inventory retains captured pre-rename log strings under `detail`.
No configuration or automation file contains an old helper name.
The explicit export list remains unchanged with 196 names.
`DB_LAYER_AVAILABLE` existed in both optional-import branches and in `__all__` before this repair.
Its assignment now states the same Boolean value once after the guarded imports.

| Old private name | Public name | Verified production consumer |
| - | - | - |
| `_build_argument_parser` | `build_argument_parser` | `MainEntrypoint` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_setup_runtime_flags` | `setup_runtime_flags` | `ApplicationBootstrap` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_initialize_dependencies` | `initialize_dependencies` | `ApplicationBootstrap` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_configure_runtime_options` | `configure_runtime_options` | `ApplicationBootstrap` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_early_dependency_check` | `early_dependency_check` | `ApplicationBootstrap` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_establish_mist_session` | `establish_mist_session` | `ApplicationBootstrap` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_dispatch_main_mode` | `dispatch_main_mode` | `MainEntrypoint` in `src/foundation/support/refactors/main_entrypoint.py` |
| `_print_systematic_banner` | `print_systematic_banner` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_build_systematic_test_options` | `build_systematic_test_options` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_print_systematic_pre_run_counts` | `print_systematic_pre_run_counts` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_initialize_systematic_telemetry` | `initialize_systematic_telemetry` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_resolve_systematic_test_context` | `resolve_systematic_test_context` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_execute_systematic_test_loop` | `execute_systematic_test_loop` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_finalize_systematic_telemetry` | `finalize_systematic_telemetry` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_print_systematic_summary` | `print_systematic_summary` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_report_systematic_outcome` | `report_systematic_outcome` | `RunSystematicTestManager` in `src/foundation/support/refactors/run_systematic_test.py` |
| `_build_interactive_test_runner` | `build_interactive_test_runner` | `RunInteractiveTestManager` in `src/foundation/support/refactors/run_interactive_test.py` |
| `_print_switch_login_header` | `print_switch_login_header` | `SwitchToInteractiveLoginManager` in `src/foundation/support/refactors/switch_to_interactive_login.py` |
| `_prompt_switch_login_confirmation` | `prompt_switch_login_confirmation` | `SwitchToInteractiveLoginManager` in `src/foundation/support/refactors/switch_to_interactive_login.py` |
| `_attempt_interactive_login_with_rollback` | `attempt_interactive_login_with_rollback` | `SwitchToInteractiveLoginManager` in `src/foundation/support/refactors/switch_to_interactive_login.py` |
| `_handle_interactive_login_success` | `handle_interactive_login_success` | `SwitchToInteractiveLoginManager` in `src/foundation/support/refactors/switch_to_interactive_login.py` |
| `_load_mistapi_module` | `load_mistapi_module` | `MistSessionInitializer` in `src/foundation/support/refactors/initialize_mist_session.py` |
| `_introspect_apisession_class` | `introspect_apisession_class` | `MistSessionInitializer` in `src/foundation/support/refactors/initialize_mist_session.py` |
| `_attempt_all_session_strategies` | `attempt_all_session_strategies` | `MistSessionInitializer` in `src/foundation/support/refactors/initialize_mist_session.py` |
| `_log_failed_session_variants` | `log_failed_session_variants` | `MistSessionInitializer` in `src/foundation/support/refactors/initialize_mist_session.py` |
| `_configure_session_timeout` | `configure_session_timeout` | `_load_menu_actions` in `wsgi.py` |
| `_log_session_auth_status` | `log_session_auth_status` | `MistSessionConfigurator` in `src/foundation/support/refactors/initialize_mist_session.py` |

These are real cross-module resolver contracts.
`SourceDependencyResolverService._resolve_host_symbol` resolves the host module with `getattr`.
The new public names match each live consumer.
The Python source and test scan found no old root-helper reference, mock key, or old resolver string.
Historical artifacts retain old names as history or captured log text.

| Added or consolidated name | Existing behavior and reason |
| - | - |
| `_MistHelperContextModule` | A named `ModuleType` class replaces a generated type factory. Its read, write, and delete methods keep the existing module-to-`AppContext` behavior and provide static method contracts. `test_context_reads_writes_and_deletes` and `test_two_app_context_instances_do_not_share_state` cover this behavior. |
| `DB_LAYER_AVAILABLE: bool` | This existing exported flag keeps its `True` or `False` result. One assignment after optional imports replaces equal branch assignments. The export list does not change. |
| `RRM_DRY_RUN_DEFAULT: bool \| None` | This typed `None` default preserves the RRM handler's tri-state input and its lazy call path. `test_menu_291_handler_default_is_the_absent_marker` verifies the menu default. |
| `_build_policy_api` | This typed builder checks the authenticated session and serves the real menu 305 and 306 handlers. `test_policy_requires_session_before_client_creation` and `test_policy_preserves_authenticated_session` verify both paths. |

The removed nine private seams have no root caller through `getattr`, `_MH`, `MistHelper`, or a string-keyed lookup in `src`, `scripts`, or tests.
The four dependent helpers had callers only inside the removed private chain.
The cleanup record names all nine seams, each prior test reference, and its replacement behavior test.
The API and cache source diffs change five annotations and no imports.
AST comparison confirms that all 16 function bodies and defaults remain unchanged.

The split-candidate results below are historical.
They do not describe the final branch.
The corrective artifact review maps all requirements and success criteria to the task list.
All implementation tasks are complete.

### Historical candidate-three verification

Candidate three uses `fix/4758-strict-annotations` at commit `e47dce4232b6c5ee6731ec48d4e6a33ffd4d578d`.
Its base is `origin/main` at `19bec34ea1edfae30782fc0f23dde44b3516e369`.
Candidate one is `fix/4758-strict-contracts` at `bc6ae8bb41fc2bd43b8b1ca1b596e3d215e6f70f`.
Candidate two is `fix/4758-strict-dead-code` at `65c09bb5fb6c36745a1ee0ebd95593b11cc8380e`.
The preservation ref remains `preserve/strict-a5b1b2c` at `a5b1b2c952b7f63cac0a78a36be8443cc9bb9662`.

The candidate-three JSON report records 9 errors, 0 warnings, and one analyzed file.
The text report records `9 errors, 0 warnings, 0 informations`.
All nine diagnostics use `reportUnusedFunction` in `MistHelper.py`.
The exact reports are `candidate3-pyright.json` and `candidate3-pyright.txt` in the session evidence directory.
The AST report compares 16 functions against `origin/main`.
It confirms unchanged bodies, defaults, and imports, with only the three approved annotations changed.

The focused command for the API and cache tests passed 38 tests with one existing warning.
The following standard checks passed with exit code 0:

| Check | Result |
| - | - |
| `python -m ruff check .` | Exit 0 |
| `python -m black --check src/mist/access/api/api_core_fetch_utils.py src/foundation/persistence/cache/cache_utils.py` | Exit 0 |
| CI-path `python -m mypy` selection | Exit 0, 887 source files |
| Bandit on both changed source files | Exit 0 |
| `git diff --check origin/main...HEAD` | Exit 0 |
| Test-quality input preflight | Exit 0, one test passed |
| Test-quality committed-change gate | Exit 0, 17 files and 10 findings checked, 2 skipped, zero new findings |

The first test-quality command ran without the candidate environment on `PATH` and exited 1.
The candidate-local executable passed when called by its explicit path with exit code 0.
No push, pull request, merge, or issue closure occurred.

The original single-branch attempt used `b7a18b7ead7b1de5882bcd288203c015b1eef792`.
The split candidates use the later `origin/main` revision recorded above.
The original implementation commit is `ed7f550066e16a21aabac1132ffbd7906ead8718`.
The earlier verification-document commit identifier is recorded on issue #4758.
No push, pull request, merge, or automatic merge is authorized.

## Requirement coverage

| Requirement | Evidence | Result |
| - | - | - |
| FR-001 | Live main comparison, locked bootstrap, baseline JSON | Complete |
| FR-002 | Final strict report | Complete: zero errors across three files |
| FR-003 | Focused state, import, selector, admission, and dry-run regressions | Complete for owned changes |
| FR-004 | Source review, preserved declarations, unchanged rules | Complete |
| FR-005 | Narrow portal and annotation authorization, ARP ancestry, source comparison | Complete for the authorized changes |
| FR-006 | Mocked regression suite and absent-session admission cases | Complete |
| FR-007 | Separate issues #4825, #4826, and #4828 | Complete |
| FR-008 | Local implementation commit and verification records | Complete |

T003, T007, T008, T009, and T010 are complete.
The final strict report and all required focused evidence exist.

## Historical baseline and rejected candidate reports

The environment uses Python 3.15.2, locked dependencies, Pyright 1.1.414, and PowerShell 7.7.0.
The managed route came from `create-new-feature.ps1 -Json -DryRun -Number 4758 -ShortName strict-pyright-repairs`.
All later feature commands used command-scoped `SPECIFY_FEATURE_DIRECTORY`.
The shared selector remains unchanged.

The strict configuration is:

```json
{
  "include": [],
  "extraPaths": ["<worktree>"],
  "venvPath": "<worktree>",
  "venv": ".venv",
  "typeCheckingMode": "strict",
  "pythonVersion": "3.15",
  "pythonPlatform": "Darwin"
}
```

The exact configuration retains the absolute worktree paths in session storage.
The exact strict commands are:

```text
rtk uvx --from pyright==1.1.414 pyright --project /Users/jmorrison/.copilot/session-state/90c72d95-6afd-4b40-9e22-d8f6408487da/files/pyright-strict.json --outputjson MistHelper.py
rtk uvx --from pyright==1.1.414 pyright --project /Users/jmorrison/.copilot/session-state/90c72d95-6afd-4b40-9e22-d8f6408487da/files/pyright-strict.json MistHelper.py
```

Candidate one's commands exit 1 with `19 errors, 0 warnings, 0 informations`.
Candidate two's commands exit 1 with `10 errors, 0 warnings, 0 informations`.
Candidate three's commands exit 1 with `9 errors, 0 warnings, 0 informations`.
The baseline JSON records `filesAnalyzed: 1`, `errorCount: 108`, and `warningCount: 0`.
An earlier zero-file configuration is invalid and is not completion evidence.

Persistent session evidence uses these file names:

- `pyright-strict.json`: exact analyzer configuration.
- `pyright-baseline.json`: original baseline diagnostics.
- `pyright-baseline.txt`: readable diagnostics derived from that exact baseline JSON.
- `pyright-candidate.json`: exact final candidate diagnostics.
- `pyright-candidate.txt`: exact final Pyright text output.
- `gates-final.txt`: expanded commands and complete standard-gate output.

The evidence directory is `/Users/jmorrison/.copilot/session-state/90c72d95-6afd-4b40-9e22-d8f6408487da/files`.
The baseline text explicitly identifies its JSON origin.
It is not represented as a second baseline execution.

### Baseline diagnostic groups

| Rule | Count |
| - | - |
| reportUnusedFunction | 44 |
| reportUnknownArgumentType | 15 |
| reportUnknownMemberType | 12 |
| reportUnknownVariableType | 9 |
| reportUnknownLambdaType | 9 |
| reportPrivateUsage | 7 |
| reportMissingTypeStubs | 6 |
| reportArgumentType | 2 |
| reportUnnecessaryCast | 2 |
| reportConstantRedefinition | 1 |
| reportPossiblyUnboundVariable | 1 |

## Historical rejected-candidate diagnostic map

Locations below refer to the final candidate `MistHelper.py`.

| Location | Rule | Required source contract |
| - | - | - |
| 1387:43 | reportUnknownMemberType | Cache callback |
| 3794:24 | reportUnknownMemberType | Cache callback |
| 3794:24 | reportUnknownArgumentType | Cache callback |
| 3820:27 | reportUnknownMemberType | Site records |
| 5915:28 | reportUnknownMemberType | Site records |
| 5954:30 | reportUnknownMemberType | Site records |
| 5977:30 | reportUnknownMemberType | Site records |
| 8113:5 | reportUnknownVariableType | Site records |
| 8113:13 | reportUnknownMemberType | Site records |
| 8114:46 | reportUnknownArgumentType | Site records |

### Cache callback hold

This section records candidate one's decision to preserve the source contract.
Candidate three applies the annotation-only correction.

File: `src/foundation/persistence/cache/cache_utils.py`.
Issue #1794 comments `6737356357` and `6739412390` record the source and cache test history.

Required annotation: `generate_function: Callable[[], object]`.
Candidate three applies it to `check_and_generate_csv` and `_run_csv_generator`.
The method bodies and cache tests remain unchanged.
This contract accounts for three residual diagnostics.

### Site-record hold

This section records candidate one's decision to preserve the source contract.
Candidate three applies the annotation-only correction.

File: `src/mist/access/api/api_core_fetch_utils.py`.
Issue #4762 records the API pagination and error-handling work.

Required annotation: `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`.
The dictionary values are heterogeneous API data.
The keys are field names.
Candidate three applies the annotation and preserves the method body.
This contract accounts for seven residual diagnostics.

Candidate three changes no imports or method bodies.
No caller cast, duplicate implementation, ignored rule, or replacement stub conceals a diagnostic.

## Ownership and behavior

PR #4208 granted only two menu dictionary annotations in `web_portal/app.py`.
Both bodies remain unchanged.
The firmware selectors now expose public names without aliases.
Their callers and existing tests use the exact new names.

PR #4317 merged the previous bounded ARP session-token change.
Commit `5e890ed683fd070aa16afce09fd4a21cef250ff3` is an ancestor of the base.
Only the ARP `execute` signature changed.
Its credential behavior and body remain unchanged.
The held ARP test file remains unchanged.
Issue #2861 remains open.

The rejected candidate added private helper names to the explicit export contract.
The correction removes all 44 additions and restores the historical snapshot.
No helper implementation was deleted.
The named context module methods preserve all seven context fields.

Menu 291 keeps its lazy operation lookup and exactly one `None` default.
Tests reject a direct method reference because that method exposes two defaults.
The final default constant holds the same `None` value with its intended tri-state type.
Its precise cast contains no `Any` and applies to no external data.

The policy menus reject absent sessions before client construction.
They retain the exact authenticated session object.
Selectors remain lazy, so the repair adds no earlier organization prompt.

## Historical completed standard gates

`gates-final.txt` records every expanded command and its complete output.
The source selection contains `MistHelper.py` and the five changed supporting Python modules.
The test selection contains the two changed test files and eighteen related regression selections.

| Command | Result |
| - | - |
| `python -m py_compile` with all six changed sources | Exit 0, no output |
| `python -m ruff check .` | `All checks passed!` |
| `python -m black --check` with six sources and two tests | Eight files unchanged |
| `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | No issues in 887 source files |
| Combined `python -m pytest` selection with `-q --no-cov -rs` | 851 passed, two skipped, one warning |
| `bandit -c pyproject.toml -q` with six sources | Exit 0, no findings |
| `pydocstyle` with five supporting sources | Exit 0 |
| `interrogate` with six sources and `--fail-under 90` | 98.7 percent |
| `radon cc` with five product sources, piped to `complexity-gate --max 10` | All functions within the threshold |
| `pylint` with five product sources and `--fail-under=9.5` | 9.75/10 |
| `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Exit 0, no findings |
| `python scripts/generate_menu_wiki.py` | Generated the matching menu references |
| `python -m scripts.menu_api_map` | Examined 307 menus and updated matching handler text |
| Managed route and process-folder guard selection | 56 passed with command-scoped PowerShell |
| `markdown-link-check` with the feature and release note | Ten files examined, zero broken links |

Every command uses the isolated `.venv` and the `rtk` prefix.
The Pylint score passes, but its pre-existing SDK member defect remains recorded in #4825.

The changelog event guard skips outside a pull request event.
The portal guard skips its unregistered-class case because no such registry entry exists.
Neither skip is reported as a successful assertion.
The Dash deprecation warning is tracked in #4826.

The symbol command compares all six changed sources against the exact base.
It reports zero lost module-level names.
Its exit 1 identifies added names, not an unchanged symbol table.
Additions include the named context type, policy admission helper, absent-mode constant, and necessary imports.
`DB_LAYER_AVAILABLE` already existed in conditional branches and now has one assignment.
The source diff removes 127 nonblank, noncomment physical lines.
Typed replacements preserve every existing module-level declaration.
AST comparisons confirm unchanged bodies for both portal methods, ARP `execute`, and `OrgExportUtils.export_data`.

All ten feature and release-note documents pass the STE score threshold.
Scores range from 83 through 99, with no unread or skipped file.
Regeneration after staging produces no further changes.

The route guard command is:

```text
PATH="/Users/jmorrison/.copilot/session-state/b93b25d8-d5a8-455c-9640-1d473a7b54a1/files/powershell:$PATH" rtk bypass .venv/bin/python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py -q --no-cov
```

`spec-gates.txt` preserves its complete output.
The first attempt could not locate `pwsh` on PATH.
The corrected command uses only the existing verified executable and changes no global installation.

### Evidence fingerprints

| File | SHA-256 |
| - | - |
| pyright-baseline.json | `b700af85bb07f9d96a6f878d1ba37a601583fe0871ece8845045ec8921c665a5` |
| pyright-baseline.txt | `6b7184ae65a2eb78c754e7fe3ca6a792b29a3e04e608f16098dd98d5ac3206fa` |
| pyright-candidate.json | `9fc940b40340d424d554d078aef75369419b3ad1f11c9723728172557781f6df` |
| pyright-candidate.txt | `f70c074a4da622736ea5245234d9527bd1d5ef24ede36ee4a3000b9ea8cbd635` |
| gates-final.txt | `c654b921f53640c38e2207ecf84cd9aa738f67ec45639457b0fe9236b0513594` |

The test-quality input preflight passed after the implementation commit.
It read and validated all four required inputs.
The committed-diff analyzer examined two changed test files and eight findings.
It reported zero new findings against the unchanged baseline.
Its summary reported two skipped checks and zero parse errors.

The exact commands are:

```text
rtk git fetch --no-tags origin '+refs/heads/main:refs/remotes/origin/main'
rtk git rev-parse --verify 'origin/main^{commit}'
rtk bypass .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
rtk bypass .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

The preflight result is `1 passed`.
The analyzer result is:

```text
gate_scope: 2 files checked, 8 findings checked
test_quality_analyzer: 8 findings (0/0/8/0), 2 skipped, 0 parse errors
gate: 0 new findings vs baseline
```

`test-quality-preflight.txt` and `test-quality-final.txt` preserve the complete outputs.
`symbols-final.txt` records the final six-source comparison and every intentional addition.
No standard gate was represented as passing before it ran.

Full-suite coverage, production safe sweeps, browser runs, and dependency audits were not run.
This change alters no dependency manifest, browser element, or production configuration.
All selected API and destructive-operation regression dependencies remain mocked.

## Historical rejected intermediate changes

The direct RRM method reference failed the existing absent-default-shape test.
The final implementation restores the original lambda shape and passes that regression.
A cast around the entire lambda did not infer its parameter and was removed.
A cast inside the default violated Ruff's function-call-default rule and was moved to the typed default constant.
No related test was weakened.

An exploratory pytest command named a nonexistent import-side-effect file and collected no tests.
That command is not verification evidence.
The correct side-effect-free help regression ran successfully in the combined final selection.

## Separate findings

Issue #4825 records the absent `mistapi.api.v1.orgs.invites.listOrgInvites` SDK method.
The base already calls it.
Local SDK introspection confirmed its absence without an API request.
The repair remains deferred.

Issue #4826 records the Dash plugin's deprecated `pytest_addhooks` marker configuration.
Current tests pass, but the warning identifies future pytest compatibility work.
Dependency manifests remain unchanged.

Issue #4828 records the test-quality analyzer inference defect.
Issues #4825, #4826, and #4828 remain open.

## Historical bounded completion procedure

1. Restore both archived owner sessions through the application.
2. Obtain annotation-only handoffs for the two named source contracts.
3. Preserve their current bodies, unpublished changes, tests, and publication holds.
4. Apply only the two callback annotations and the site-record return annotation.
5. Repeat the recorded strict command and require one analyzed file with zero errors and zero warnings.
6. Repeat focused regressions, standard gates, and the committed-diff test-quality procedure.
7. Check T003, T008, and T010 only after their evidence exists.

Do not close issue #4758 or publish this branch while the ownership or publication holds remain active.

## Historical local delivery

The implementation commit contains 23 files.
It includes the specification, plan, tasks, analysis, supporting records, tests, and generated references.
The verification-document commit checks T012 and T016 after their evidence exists.
Fourteen tasks are complete, and two diagnostic tasks remain unchecked.
The repository auto-commit configuration disables the optional implementation hook.
The explicit local commits preserve that setting and include the required coauthor trailer.

The worktree has no uncommitted source repair.
No remote branch, existing ref, dependency hold, or publication hold was removed.

## Historical bounded cleanup verification

The cleanup removes thirteen verified unused private functions, including four dependent helpers.
All remaining root definitions and all 196 explicit exports match commit `e5f796d9689e17b5a8ad7b5a43b0c349eb3dee90`.
The session preserves the exact caller audit and AST comparison in `cleanup-reference-audit.json` and `cleanup-preservation.json`.
No held API/cache source, dependency manifest, or held test changes.

The complete established regression selection reports 1145 passed tests and two documented skips.
The existing Dash warning remains tracked separately.
The route and process-folder guards report 56 passed tests.
The twelve feature and release-note documents pass the unchanged STE threshold.
The standard gates pass, with 887 mypy files, 99.0 percent docstring coverage, and Pylint 9.70.
The changed-source complexity check passes the unchanged threshold of 10.
Exact commands and complete outputs remain in the new `cleanup-*.txt` session reports.

The real help tests replace the obsolete helper detector.
Session tests observe the current configuration seam and real method validation.
Dependency tests verify both import modes, assignment publication, once-only execution, and critical failure behavior.
No parser setting, transport policy, production call, or confirmation changes.
The final local commit and post-commit quality result belong in the issue handoff.
The first cleanup commit is `838046104f606c008b034e0176ccd34ddf44a5f9`.
Its quality gate found two new HTTP-coverage requirements caused by the broad bootstrap-class import.
Issue #4828 records that shared-tool inference defect.
The revised help cases test the real public CLI entry point and parser.
No analyzer setting, baseline, import visibility, or HTTP case conceals that defect.

## Historical pre-annotation interface verification

This section records the ten-error candidate before the API and cache annotations.
Its error count and incomplete-task notes do not describe the final combined candidate above.

The additional PR #4208 handoff permits one authentication-status reference and its directly related module documentation.
The root definition now uses `log_session_auth_status`.
The configurator calls that public name with the original session and method.
AST comparison against `23053c8d4d2c05ed12571e7a8521aa86631d5337` proves the complete root change is the definition name.
The initializer comparison permits only its module documentation and that one attribute name.
All function bodies, arguments, control flow, authentication logs, transport settings, and explicit exports remain unchanged.

The audit checks every initializer `_MH` private attribute and exact private string value.
Before the rename, its private root references were `_log_session_auth_status` and `_parse_api_tokens`.
The latter retains root callers in `_collect_credential_problems` and `_systematic_test_has_api_token`.
The string `_session` names the SDK transport, not a root helper.
No additional private interface requires a rename.
`final-interface-audit-before.json` and `final-interface-preservation.json` preserve the exact locations and comparisons.

At this stage, the strict report had ten errors and one analyzed file.
Seven errors required the API site-record return contract.
Three errors required the cache callback contract.
The later authorized annotations resolve these errors.
The final reports are `pyright-final.json` and `pyright-final.txt`.

The established regression selection passes 1145 tests, with two documented skips and the existing Dash warning.
After formatting, the initializer tests and managed route guards pass 67 tests.
The real validation tests observe the public authentication report while executing its original body.
Compile, repository Ruff, Black, mypy, Bandit, pydocstyle, interrogate, Pylint, and Vulture pass again.
Mypy checks 887 source files.
Docstring coverage remains 99.0 percent.
Pylint remains 9.70 against the unchanged 9.5 threshold.
`interface-gates-final.txt` and `interface-regressions.txt` preserve the expanded commands and outputs.
The initial Black check requested only test-signature formatting.
The formatter corrected it before the complete successful gate run.

At this historical stage, T003, T008, and T010 remained unchecked.
The user later authorized the annotation-only API and cache changes.
The final combined report completes T010.
No production request occurs.
