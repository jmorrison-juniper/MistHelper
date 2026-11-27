# Implementation Plan: Netcool Runbook Smoke Package Conformance

**Branch**: `chore/4945-netcool-runbook-smoke-conformance` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/2/4/0/4945-netcool-runbook-smoke-conformance/spec.md`

**Input**: Numeric specification from `/specs/numbered/[eight-base-5-segments]/[feature]/spec.md`. The route for issue 4945 is `0/0/1/2/4/2/4/0`. The route follows the base-5 rule of `.specify/scripts/powershell/spec-route.ps1` (function `Get-SpecRadixSegments`, line 4 on `main`). Issue 4945 encodes to `124240` in base 5, and the eight-level pad gives `00124240`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The package `scripts/netcool_runbook_smoke/` breaks the constitution limits in three ways. Fourteen functions break a function limit. Eight modules hold six top-level names when the module logger counts. The CI gates skip the package. The change restructures the package into sub-packages, splits fourteen functions, adds gate steps, adds guards, and rewrites weak comments. Public behavior stays the same.

## Technical Context

**Language/Version**: Python 3.15. `ci.yml` sets `PYTHON_VERSION` to `'3.15'` at line 77 on `main`.

**Primary Dependencies**: `structlog` for logs, `mistapi` 0.64.1 for the Mist REST client (installed at `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`), and the standard library (`argparse`, `dataclasses`, `threading`, `urllib.parse`).

**Storage**: None for the package. The evidence file is a JSON file under `test-artifacts/netcool-runbook-smoke/`. The path comes from the function `default_path` at `documents.py` line 734 on `main`.

**Testing**: pytest with `--timeout=120` in the `pytest_coverage_shards` job (`ci.yml` line 311 on `main`). Ruff, black, mypy, bandit, radon, Vulture, pydocstyle, and Interrogate run as separate gates.

**Target Platform**: The Windows 11 development host and the Ubuntu runner (`ci.yml` `runs-on: ubuntu-latest`, line 142 on `main`).

**Project Type**: Command-line tool package under `scripts/`.

**Performance Goals**: No change. The request budget and the call timeout keep their current values.

**Constraints**: Function limits from FR-001 to FR-003. Class limit from FR-004. Module limit from FR-005. Directory limit from FR-006. Each limit uses the counting rules in `research.md` decisions D-1 to D-5.

**Scale/Scope**: Eleven Python files today. About 37 Python files after the change, including `__init__.py` files. Five test modules stay in place. Approximately 4,600 lines move or change.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after the design. The result is below.*

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule | Pass after the change. Fail today. | Today fourteen functions break a function limit, and eight modules hold six top-level names with the logger counted. The change restructures the package to pass FR-001 to FR-006. |
| Principle I, direct child of a noncompliant parent | Pass | The package stays one direct child of `scripts/`, as the existing exception allows (issue #4937, closed). The change adds no direct child to `scripts/` or `tests/unit/scripts/`. |
| Principle I, process record | Pass | The spec record adds one unique folder under the route `0/0/1/2/4/2/4/0`. The route parent `0/0/1/2/4/2` holds one child today and two after the change. |
| Principle I, managed root | Pass | The route uses `specs/numbered/`, a managed root. The constitution names the managed roots in Principle I (`constitution.md` line 38 on `main`). |
| Principle II, class-based design | Pass | Each helper lives in a class. No standalone function wraps a method. |
| Principle III, safety first | Pass | The package reads no operator input after the change. The redaction in `EvidenceRedactor` and `LogSetup.scrub_text` stays in place. |
| Principle IV, deployment pipeline | Pass with a recorded exception | Steps 1 to 9 run in `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE`. Steps 10 and 11 run in `T-MERGE`. Step 12 does not apply, because the image contents do not change. Decision D-22 records the reason. |
| Principle V, observability | Pass | Log output stays ASCII. Structured logs stay. The redaction rule stays. |
| Principle VI, inline comments | Pass after rewrite | Each executable statement gains a comment on its first physical line. Decision D-23 records the check. |
| Principle VII, action logging | Pass after rewrite | Each touched action gains an info log before it and a debug log after it. |
| Technology, mistapi only | Pass | The package calls `APISession.mist_get` only. No direct HTTP request exists. |
| Technology, data directory | Pass | Evidence stays under `test-artifacts/`. The package writes no product output under `data/`. |
| Technology, container | Pass | The `Dockerfile` COPY lines (70 to 149 on `main`) copy `src/`, `web_portal/`, and selected files. The only sources that contain `scripts` live under `container/scripts/`. The repository `scripts/` folder is not copied, so the image contents do not change. |
| Testing, guard that can fail | Pass | Each new guard prints its examined counts and fails at zero (FR-015, FR-016). |
| Security findings, fix over suppress | Pass | No suppression comment is added. Decision D-13 forbids a relaxing override. |
| Documentation, changelog fragment | Pass | One fragment is added. Decision D-16 records why the constitution overrides the internal-only rule in `changelog.d/README.md` line 58. |
| Git flow, issue first and labels | Pass | Issue #4945 exists. It carries `refactor`, `tests`, and `in-progress`. The branch name uses the `chore` type from `AGENTS.md`. |
| Mist Cloud transport | Pass | No owned transport. The SDK pin allows the installed version (`mistapi` 0.64.1). |

## Architecture

### Current state

| Item | Current value | Source on `main` |
| - | - | - |
| Package root children, repository convention | 5. Four modules and the `checks/` directory. | Tree on `main` for `scripts/netcool_runbook_smoke` (blob `b178eed8`). |
| `checks/` children, repository convention | 5. Five modules. | Tree on `main` for `scripts/netcool_runbook_smoke/checks` (blob `84897820`). |
| Modules with six top-level names when the logger counts | 8 | `__main__.py`, `client.py`, `command.py`, `documents.py`, `checks/__init__.py`, `checks/identity.py`, `checks/scope.py`, `checks/searches.py`. |
| Classes with more than five methods | 0 | Scan of class bodies. |
| Functions that break a limit | 14 | Table below. |
| CI gates that examine the package | 0 of 7 | `ci.yml` lines 93, 99, 101, 104, 107 name no package path. `pyproject.toml` lines 206, 324, 506 exclude `scripts`. |

### Functions that break a limit

Remote line numbers come from the blob of `main`. Code lines exclude docstrings, comment-only lines, and blank lines. Decision D-1 explains the rule.

| Function | Lines on `main` | Code lines | Statements in the largest block | Breached limit | Target home |
| - | - | - | - | - | - |
| `FilterProbes.filter_verdict` | `checks/scope.py` 111 to 147 | 26 | 8 | lines and statements | `checks/scope/filters.py`, class `TypeFilterVerdict` |
| `FilterProbes.record` | `checks/scope.py` 149 to 181 | 25 | 9 | statements | `checks/scope/filters.py`, class `ProbeRecorder` |
| `ScopeChecks.smk_08` | `checks/scope.py` 209 to 240 | 25 | 9 | statements | `checks/scope/sites.py`, class `SiteSearchRoll` |
| `ScopeChecks.smk_09` | `checks/scope.py` 242 to 277 | 25 | 12 | statements | `checks/scope/filters.py`, class `FilterRequests` |
| `ScopeChecks._site_part` | `checks/scope.py` 279 to 314 | 24 | 7 | statements | `checks/scope/sites.py`, class `SiteSearchJudge` |
| `SiteListing.first_site` | `checks/scope.py` 338 to 377 | 29 | 7 | lines and statements | `checks/scope/sites.py`, class `SiteListing` helpers |
| `InventoryReader.count_sum` | `checks/scope.py` 406 to 425 | 10 | 6 | statements | `checks/scope/inventory.py`, class `InventorySummaries` |
| `InventoryReader.webhook_part` | `checks/scope.py` 457 to 488 | 22 | 7 | statements | `checks/scope/inventory.py`, class `InventorySummaries` |
| `InventoryChecks.smk_10` | `checks/scope.py` 528 to 557 | 20 | 12 | statements | `checks/scope/inventory.py`, class `InventoryChecks` helpers |
| `InventoryChecks._judge` | `checks/scope.py` 559 to 595 | 26 | 10 | lines and statements | `checks/scope/inventory.py`, class `InventoryJudge` |
| `SearchChecks.smk_06` | `checks/searches.py` 448 to 480 | 22 | 11 | statements | `checks/searches/search_checks.py`, class `SearchChecks` helpers |
| `SearchChecks.smk_07` | `checks/searches.py` 482 to 508 | 19 | 11 | statements | `checks/searches/search_checks.py`, class `SearchChecks` helpers |
| `CallGovernor._attempt` | `client.py` 428 to 469 | 28 | 10 | lines and statements | `transport/call_governor.py`, class `CallGovernor` |
| `CallGovernor._run_with_timeout` | `client.py` 471 to 508 | 19 | 9 | statements | `transport/timed_call.py`, class `TimedCall` |

The issue names the same fourteen functions. Under the physical line count with docstrings, 43 functions would break the 25-line limit. Decision D-1 explains why this plan uses code lines.

### Target layout and dependency direction

The dependency direction runs from the top to the bottom of this list. A module may import only from the layers below it.

1. `transport/` imports the standard library and `structlog` only.
2. `settings/` imports the standard library and `structlog` only.
3. `reporting/` imports the standard library and `structlog` only.
4. `checks/core/` imports `transport/` and `reporting/`.
5. `checks/catalogs.py`, `checks/identity/`, `checks/scope/`, and `checks/searches/` import `checks/core/`, `transport/`, and `reporting/`.
6. `__main__.py` imports `settings/`, `transport/`, `reporting/`, and `checks/`.

No module in layers 1 to 3 imports a module in layers 4 to 6. This rule blocks cycles (spec edge case, FR-008).

### File-by-file change map

Paths are repository paths. Source lines are line ranges on `main`.

| Action | Path | Source on `main` | Content |
| - | - | - | - |
| Modify | `scripts/netcool_runbook_smoke/__init__.py` | Same file, line 8 | Keep `__version__`. Add no re-export. |
| Modify | `scripts/netcool_runbook_smoke/__main__.py` | Lines 489 to 717 stay. Lines 54 to 488 move. | Keep `CheckSequence`, `SmokeCommand`, and the entry point at line 717. Add `RunReport` from `command.py` lines 290 to end. |
| Add | `scripts/netcool_runbook_smoke/settings/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/settings/smoke_settings.py` | `__main__.py` lines 54 to 222 | Class `SmokeSettings`. |
| Add | `scripts/netcool_runbook_smoke/settings/settings_loader.py` | `__main__.py` lines 223 to 393, and `command.py` lines 206 to 289 | Classes `SettingsLoader` and `EnvFileReader`. |
| Add | `scripts/netcool_runbook_smoke/settings/identity_rules.py` | `__main__.py` lines 394 to 488 | Class `IdentityRules`. |
| Add | `scripts/netcool_runbook_smoke/transport/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/transport/call_record.py` | `client.py` lines 33 to 233 | Class `CallRecord`. |
| Add | `scripts/netcool_runbook_smoke/transport/pages.py` | `client.py` lines 234 to 349, and 512 to 671 | Classes `PageSet` and `PageWalker`. |
| Add | `scripts/netcool_runbook_smoke/transport/call_governor.py` | `client.py` lines 350 to 470 | Class `CallGovernor`. The method `_run_with_timeout` leaves this file. |
| Add | `scripts/netcool_runbook_smoke/transport/timed_call.py` | `client.py` lines 471 to 508 | Class `TimedCall`, which replaces `_run_with_timeout`. |
| Add | `scripts/netcool_runbook_smoke/transport/read_client.py` | `client.py` lines 672 to end | Class `ReadOnlyMistClient`. |
| Delete | `scripts/netcool_runbook_smoke/client.py` | Whole file | Replaced by `transport/`. |
| Delete | `scripts/netcool_runbook_smoke/command.py` | Whole file | Replaced by `reporting/logging_setup.py`, `settings/settings_loader.py`, and `__main__.py`. |
| Delete | `scripts/netcool_runbook_smoke/documents.py` | Whole file | Replaced by `reporting/`. |
| Add | `scripts/netcool_runbook_smoke/reporting/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/reporting/sources.py` | `documents.py` lines 25 to 423 | Classes `MarkdownTables`, `RunbookClaims`, and `OpenApiIndex`. |
| Add | `scripts/netcool_runbook_smoke/reporting/redaction.py` | `documents.py` lines 424 to 668 | Class `EvidenceRedactor`. |
| Add | `scripts/netcool_runbook_smoke/reporting/evidence.py` | `documents.py` lines 669 to end | Class `EvidenceWriter`, including `default_path` at line 734. |
| Add | `scripts/netcool_runbook_smoke/reporting/logging_setup.py` | `command.py` lines 31 to 205 | Classes `TracebackFreeFormatter`, `StandardLogging`, and `LogSetup`. |
| Modify | `scripts/netcool_runbook_smoke/checks/__init__.py` | Lines 38 to end move out | Becomes an empty file. |
| Add | `scripts/netcool_runbook_smoke/checks/core/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/checks/core/results.py` | `checks/__init__.py` lines 38 to 417 | Classes `CheckStatus`, `CheckResult`, and `StopRun`. |
| Add | `scripts/netcool_runbook_smoke/checks/core/context.py` | `checks/__init__.py` lines 418 to end | Classes `CheckContext` and `EvidenceBuilder`. |
| Move | `scripts/netcool_runbook_smoke/checks/core/support.py` | `checks/support.py` lines 27 to end | Classes `SessionOpener` and `RequestTrail`. |
| Modify | `scripts/netcool_runbook_smoke/checks/catalogs.py` | Lines 25 to end | Import paths only. |
| Add | `scripts/netcool_runbook_smoke/checks/identity/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/checks/identity/loading.py` | `checks/identity.py` lines 34 to 261 | Classes `DocumentLoader` and `RunbookStructure`. |
| Add | `scripts/netcool_runbook_smoke/checks/identity/privilege.py` | `checks/identity.py` lines 262 to 412 | Class `PrivilegeReader`. |
| Add | `scripts/netcool_runbook_smoke/checks/identity/usage.py` | `checks/identity.py` lines 413 to 537 | Class `UsageReader`. |
| Add | `scripts/netcool_runbook_smoke/checks/identity/identity_checks.py` | `checks/identity.py` lines 538 to end | Class `IdentityChecks`. |
| Delete | `scripts/netcool_runbook_smoke/checks/identity.py` | Whole file | Replaced by `checks/identity/`. |
| Add | `scripts/netcool_runbook_smoke/checks/scope/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/checks/scope/filters.py` | `checks/scope.py` lines 28 to 183 | Classes `FilterProbes`, `TypeFilterVerdict`, `ProbeRecorder`, and `FilterRequests`. |
| Add | `scripts/netcool_runbook_smoke/checks/scope/sites.py` | `checks/scope.py` lines 184 to 379 | Classes `ScopeChecks`, `SiteListing`, `SiteSearchJudge`, and `SiteSearchRoll`. |
| Add | `scripts/netcool_runbook_smoke/checks/scope/inventory.py` | `checks/scope.py` lines 380 to end | Classes `InventoryReader`, `InventorySummaries`, `InventoryChecks`, and `InventoryJudge`. |
| Delete | `scripts/netcool_runbook_smoke/checks/scope.py` | Whole file | Replaced by `checks/scope/`. |
| Add | `scripts/netcool_runbook_smoke/checks/searches/__init__.py` | None | Empty file. |
| Add | `scripts/netcool_runbook_smoke/checks/searches/observations.py` | `checks/searches.py` lines 33 to 174 | Class `SearchObservations`. |
| Add | `scripts/netcool_runbook_smoke/checks/searches/families.py` | `checks/searches.py` lines 175 to 240 | Class `FamilyJudge`. |
| Add | `scripts/netcool_runbook_smoke/checks/searches/counts.py` | `checks/searches.py` lines 241 to 394 | Classes `CountComparison` and `CountVerdict`. |
| Add | `scripts/netcool_runbook_smoke/checks/searches/search_checks.py` | `checks/searches.py` lines 395 to end | Classes `SearchChecks` and `SearchRollup`. |
| Delete | `scripts/netcool_runbook_smoke/checks/searches.py` | Whole file | Replaced by `checks/searches/`. |
| Delete | `scripts/netcool_runbook_smoke/checks/support.py` | Whole file | Moved to `checks/core/support.py`. |
| Modify | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` | Import lines 24, plus new tests | Import paths for `transport/`. Add tests TEST-11 and TEST-16. |
| Modify | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py` | Import lines 18 to 40, plus new tests | Import paths for `checks/` and `settings/`. Add tests TEST-12 to TEST-15. |
| Modify | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py` | Import lines 23 to 28 | Import paths for `__main__`, `reporting/`, and `transport/`. |
| Modify | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py` | Import line 17 | Import paths for `reporting/`. |
| Modify | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py` | Import line 20 | Import paths for `reporting/sources.py`. |
| Modify | `tests/guardrails/test_nested_package_structure.py` | Lines 1 to 17 and the test functions after line 169 | Add the package scan, the limit scanner, and tests TEST-01 to TEST-05, TEST-10, and TEST-17. Keep the `src` ratchet unchanged. |
| Modify | `tests/guardrails/test_ci_gate_triggers.py` | Module docstring and the test functions | Add tests TEST-06 to TEST-09 for the seven gates. |
| Modify | `.github/workflows/ci.yml` | Lines 93, 99, 101, 104, 107, 165, 451, and the seven gate jobs | Add the package path to five variables (lines 93, 99, 101, 104, 107). Add an explicit Ruff step after line 165 and an explicit Bandit step after line 451. Add one count step to each of the seven gate jobs. The coverage line 311 does not change (decision D-14). |
| Add | `changelog.d/issue-4945-netcool-runbook-smoke-conformance.md` | None | One `### Changed` heading and one bullet that names issue 4945. |

The change plan leaves `pyproject.toml` unchanged. Decision D-12 records the reason. The change plan leaves `documentation/quality-gates.md` unchanged. That file names the gate variables and does not list the package paths.

### New classes and helper homes

Each helper goes into a class with room for another method. A class that holds five methods gets a new class in the same module. The rule also keeps each module at five names or fewer, with the logger included.

| Module | Class | Methods | Helper role |
| - | - | - | - |
| `checks/scope/filters.py` | `FilterProbes` | `limit_outcome`, `device_types`, `window` | Existing probe helpers. |
| `checks/scope/filters.py` | `TypeFilterVerdict` | `judge`, `_records_or_failure`, `_type_outcome` | Splits `filter_verdict`. |
| `checks/scope/filters.py` | `ProbeRecorder` | `record`, `_limit_fact`, `_device_fact`, `_window_fact` | Splits `record`. |
| `checks/scope/filters.py` | `FilterRequests` | `build` | Builds the six requests of `smk_09`. |
| `checks/scope/sites.py` | `ScopeChecks` | `__init__`, `smk_08`, `smk_09`, `_device_keys` | Keeps the two checks. |
| `checks/scope/sites.py` | `SiteListing` | `first_site`, `_failure_for`, `_identifier` | Splits `first_site`. |
| `checks/scope/sites.py` | `SiteSearchJudge` | `judge` | Holds `_site_part`. |
| `checks/scope/sites.py` | `SiteSearchRoll` | `resolve_site`, `roll_up` | Splits `smk_08`. |
| `checks/scope/inventory.py` | `InventoryReader` | `items`, `list_part`, `last_trouble` | Existing list helpers. |
| `checks/scope/inventory.py` | `InventorySummaries` | `count_sum`, `webhook_part`, `_bucket_total` | Splits `count_sum` and `webhook_part`. |
| `checks/scope/inventory.py` | `InventoryChecks` | `__init__`, `smk_10`, `_requests`, `_rows`, `_field_names` | Keeps the check. `_requests` holds the request list of `smk_10`. |
| `checks/scope/inventory.py` | `InventoryJudge` | `judge`, `_status_for` | Splits `_judge`. |
| `checks/searches/search_checks.py` | `SearchChecks` | `__init__`, `smk_06`, `smk_07`, `_read_families` | Splits the two checks. |
| `checks/searches/search_checks.py` | `SearchRollup` | `summarize`, `headline` | Holds `_summarize` and `_headline`. |
| `transport/call_governor.py` | `CallGovernor` | `execute`, `_pause`, `backoff_seconds`, `_attempt`, `_refuse` | Splits `_attempt`. |
| `transport/timed_call.py` | `TimedCall` | `run`, `_start_worker`, `_collect` | Holds the body of `_run_with_timeout`. |

Each new method keeps a single job. Each method has a docstring, a comment on each statement, an info log before its action, and a debug log after it.

### Import and naming rules

- Public names keep their class names. Only the import path changes (FR-009).
- Each `__init__.py` file stays empty. It holds no re-export, no alias, and no shim (FR-008).
- The entry point keeps the name `__main__.py` at the package root (FR-010).
- Module logger names change with the module path. The `LogSetup.PACKAGE_LOGGERS` tuple (`command.py` line 63) names the package prefix `scripts.netcool_runbook_smoke`. Child loggers inherit that level. TEST-10 proves the prefix rule.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/4/0/4945-netcool-runbook-smoke-conformance/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      package-layout.md
      cli-output.md
      ci-steps.md
    checklists/
      requirements.md
      structure.md
      ci.md
```

### Source Code (repository root)

```text
scripts/netcool_runbook_smoke/
  __init__.py
  __main__.py
  settings/
    __init__.py
    smoke_settings.py
    settings_loader.py
    identity_rules.py
  transport/
    __init__.py
    call_record.py
    pages.py
    call_governor.py
    timed_call.py
    read_client.py
  reporting/
    __init__.py
    sources.py
    redaction.py
    evidence.py
    logging_setup.py
  checks/
    __init__.py
    catalogs.py
    core/
      __init__.py
      results.py
      context.py
      support.py
    identity/
      __init__.py
      loading.py
      privilege.py
      usage.py
      identity_checks.py
    scope/
      __init__.py
      filters.py
      sites.py
      inventory.py
    searches/
      __init__.py
      observations.py
      families.py
      counts.py
      search_checks.py
```

Each directory above holds five children or fewer, excluding `__init__.py` (FR-006, decision D-4). The `checks/` directory holds `catalogs.py`, `core/`, `identity/`, `scope/`, and `searches/`, which is five children.

**Structure Decision**: The sub-packages follow the five-child rule and the layer order in "Target layout and dependency direction". The tests stay in the five existing modules under `tests/unit/scripts/netcool_runbook_smoke/`.

## Complexity Tracking

The constitution requires a table that separates grandfathered debt from new design (Governance, `constitution.md` line 548 on `main`).

### Grandfathered debt, not changed by this plan

| Violation | Why it stays | Tracking |
| - | - | - |
| `scripts/` holds 53 children on `main`, and the package is one of them. | Issue #4937 closed with the written exception for `scripts/netcool_runbook_smoke/`. | Issue #4944 tracks the remediation of `scripts/`. |
| `tests/unit/scripts/` holds 10 children on `main`, and the package test folder is one of them. | The same exception applies. The change adds no child. | Issue #4944 tracks the remediation of `tests/unit/scripts/`. |
| `tests/guardrails/` holds 79 children on `main`. | The change adds no file to this folder. The guards extend existing files. | Not tracked by this plan. The folder predates this change. |

### New design, justified in writing

| Violation or choice | Why needed | Simpler alternative rejected because |
| - | - | - |
| Seven new sub-package directories under the package | Fourteen functions need helpers, and each full class and each full module needs a neighbor. | A helper added to a full class breaks FR-004. A helper added to a full module breaks FR-005. |
| Nine new helper classes | Each helper needs a class with room for it. | A standalone function breaks the class-based rule of AGENTS.md and Principle II. |
| The package root keeps `__main__.py` | The runbook command `python -m scripts.netcool_runbook_smoke` needs the entry point at the package root. | Moving the entry point needs a runbook text change, which the issue excludes. |

## Dependencies

- Local tools in `.venv\Scripts`: `complexity-gate.exe`, `symbol-diff.exe`, `vulture.exe`, `radon.exe`, `interrogate.exe`, `pydocstyle.exe`, and `ste-linter.exe`. The `misthelper_devtools` package 0.6.4 supplies the first two and the linter (`.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info`).
- CI installs the gate tools with `pip install -r requirements-dev.txt` (`ci.yml` line 163 on `main`). The pinned versions of those tools are listed under "Unverified" in `design/research.md`.
- No new package enters the dependency manifests. The change adds no requirement.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: a wrong import path breaks the runbook command. | FR-010 and TEST-10 import every module and run the command test. |
| Caution: Bandit skips the explicit package path, because `[tool.bandit]` lists `scripts` in `exclude_dirs` (`pyproject.toml` line 506). | The count step fails at zero. TEST-08 injects a violation. |
| Caution: Ruff may skip an explicit path that `extend-exclude` names (`pyproject.toml` line 206). | The count step fails at zero. TEST-08 injects a violation. |
| Caution: mypy in strict mode finds errors in the current package. The count of errors is not measured yet. | T004 measures the errors first. The fixes change code and add no suppression. |
| Caution: radon, Vulture, pydocstyle, or Interrogate finds findings in the current package. | T004 measures the findings first. The fixes change code and add no threshold change. |
| Caution: a logger name change hides package logs. | TEST-10 proves that the `scripts.netcool_runbook_smoke` prefix covers each new logger. |
| Caution: symbol-diff reports removed names for deleted modules. | The pull request body lists each moved name and its new path (FR-025). |
| Caution: the test-quality analyzer reports new findings for the new tests. | The local gate runs before the push. The baseline file stays unchanged. |
| Caution: coverage falls below 95 percent after the split. | TEST-11 to TEST-16 cover each new class. T-LOCAL-GATES measures the value. |
| Caution: a new import creates a cycle. | The layer order blocks the cycle. TEST-10 imports every module. |
| Caution: the structure scanner reports a false violation. | TEST-01 to TEST-05 use fixture files with known counts. |
| Warning: a commit pushed after the squash merge creates an orphan pull request that nobody merges. | Do not push to the branch after the merge. Open a new issue and a new branch from `main`. |
| Warning: a force push to `main` removes commits from other agents. | Do not force-push `main`. Use a revert pull request if a merged change needs reversal. |

## Rollback Steps

1. Before the merge, close the pull request, and delete the branch after a preservation proof (AGENTS.md, "Preserve work before you close an unmerged pull request").
2. After the merge, open a revert pull request. Do not force-push `main`.
3. Re-run `T-LOCAL-GATES` on the revert branch before the merge.
