# Analysis and local verification

## Status

This is a partial repair, not a strict-clean completion.
The strict baseline has 108 errors.
The final interface candidate has ten errors.
Both reports analyze exactly one file and report zero warnings.
Ten errors require two reserved source contracts.
The additional name-only handoff resolves the live authentication-status interface.
The cleanup removes all nine audited private declarations and four dependent helpers.
The original ten-error candidate used rejected export and import approaches.
The historical sections below retain that evidence, not an accepted completion claim.
The [cleanup record](design/contracts/cleanup.md) gives the current commands, caller evidence, and residual map.
The [correction record](design/contracts/correction.md) preserves the previous nineteen-error result.
The corrective artifact review maps all twelve requirements and success criteria to the sixteen tasks.
Three tasks remain incomplete.
SC-003 preserves live implementations and explicit exports while allowing verified private-code removal and genuine host-interface renames.

The initial and refreshed `origin/main` revision is `b7a18b7ead7b1de5882bcd288203c015b1eef792`.
The worktree HEAD matched that revision before edits.
The implementation commit is `ed7f550066e16a21aabac1132ffbd7906ead8718`.
The final verification-document commit identifier is recorded on issue #4758.
No push, pull request, merge, or automatic merge is authorized.

## Requirement coverage

| Requirement | Evidence | Result |
| - | - | - |
| FR-001 | Live main comparison, locked bootstrap, baseline JSON | Complete |
| FR-002 | Final interface strict report | Incomplete: ten errors |
| FR-003 | Focused state, import, selector, admission, and dry-run regressions | Complete for owned changes |
| FR-004 | Source review, preserved declarations, unchanged rules | Complete |
| FR-005 | Narrow portal handoff, ARP ancestry, held-file comparison | Partial: API and cache handoffs unavailable |
| FR-006 | Mocked regression suite and absent-session admission cases | Complete |
| FR-007 | Separate issues #4825 through #4828 | Complete |
| FR-008 | Local implementation commit and verification records | Complete |

T003 and T008 remain unchecked because ownership blocks their completion.
T007 is complete after the approved authentication-status interface rename.
T010 remains unchecked for the held contracts.
Do not treat their dependency status as a released hold.

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

The candidate commands exit 1 with `10 errors, 0 warnings, 0 informations`.
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

File: `src/foundation/persistence/cache/cache_utils.py`.
Issue #1794 comments `6737356357` and `6739412390` reserve the source and its cache tests.
Owner session: `ffe5c6ac-bbd0-4e91-95cf-fc4c003a8d8f`.
The owner is archived, and the coordinator cannot obtain a handoff without restoration.

Required annotation: `generate_function: Callable[[], object]`.
Apply it to `check_and_generate_csv` and `_run_csv_generator` only after a handoff.
Keep both bodies and the held cache test file unchanged.
This contract accounts for three residual diagnostics.

### Site-record hold

File: `src/mist/access/api/api_core_fetch_utils.py`.
Issue #4762 owns an unpublished pagination and error-handling repair.
Owner session: `37b17b82-441d-48ef-b9f9-44b62de4faaa`.
The owner is archived, and the coordinator cannot obtain a handoff without restoration.

Required annotation: `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`.
The dictionary values are heterogeneous API data.
The keys are field names.
Keep the unpublished repair, method body, and publication holds intact.
This contract accounts for seven residual diagnostics.

Neither file changed.
No caller cast, duplicate implementation, ignored rule, or replacement stub conceals these errors.

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
Thirteen tasks are complete, and three ownership-dependent tasks remain unchecked.
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

## Final approved interface verification

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

The refreshed strict JSON and text report ten errors, zero warnings, and one analyzed file.
Seven errors require the held API site-record return contract.
Three errors require the held cache callback contract.
The current line and rule map remains in the cleanup record.
The committed configuration and bounded stubs remain unchanged.
`pyright-interface.json` and `pyright-interface.txt` preserve the actual analyzer output.
The final immutable handoff identifies matching commit-specific copies and their hashes.

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

T007 is complete.
T003, T008, and T010 remain unchecked for the archived API/cache owners and the absent zero-error result.
Neither held source file, dependency manifests, held tests, nor publication permission changed.
The final issue handoff records the post-commit quality preflight and comparison result.
No push, pull request, merge, or production request occurs.
