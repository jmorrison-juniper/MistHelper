# Feature Specification: Eliminate 33 ARCH-DELEGATE Wrappers + 3 ARCH-NAMING Smells in `MistHelper.py`

**Feature Branch**: `refactor/440-mh-delegate-naming`
**Created**: 2026-06-24
**Status**: Draft
**Issue**: [#440](https://github.com/jmorrison-juniper/MistHelper/issues/440) (Part of [#431](https://github.com/jmorrison-juniper/MistHelper/issues/431))
**Input**: User request: "Start a speckit workflow for just Architecture (DELEGATE+NAMING). Refer to the agents and copilot-instructions files for guidance on coding styles. WE SHOULD touch the facades and do this correctly per our coding guidelines -- do NOT defer to a 'facade guardrails' pattern."

## Problem / Goal *(mandatory)*

### Problem

A fresh `tools/check_compliance.py` run against the live `MistHelper.py` flags **33 `ARCH-DELEGATE`** and **3 `ARCH-NAMING`** violations. Both stem from the same root cause documented in `.github/copilot-instructions.md` and `agents.md`:

> **"No wrappers: All functionality lives within appropriately named classes, never use standalone wrapper functions."**

As classes were extracted into `src/`, `MistHelper.py` accumulated a layer of thin pass-through methods (delegators) plus three indirection-named symbols (`device_events_52w_legacy`, `_metric_compatible_with_platform`, `export_legacy`). The Architecture category is **pinned at the penalty cap** while any delegator survives, so the score cannot improve until the full set lands together.

### Goal

Drive `ARCH-DELEGATE` and `ARCH-NAMING` to **0** in `MistHelper.py` by **genuinely eliminating** every wrapper (delete dead ones, inline/rewire live ones, convert the one stateful facade to a factory) and renaming/removing the three indirection-named symbols -- **never** by suppressing or by adding new shims. Six flagged entries are genuine **detector false positives** (Python dunder forwarders and nested closures, which are not architectural wrappers); these are fixed at the source -- the analyzer -- in keeping with the project's "fix over suppress" rule.

### Violation Inventory (must reach 0 in `MistHelper.py`)

| Category | Count | Source |
|----------|-------|--------|
| ARCH-DELEGATE | 33 | fresh `check_compliance.py` |
| ARCH-NAMING | 3 | fresh `check_compliance.py` |
| **Total** | **36** | — |

### Non-Goals

- **No `src/` behavior changes.** `src/` import-site updates are limited to the two `export_legacy` -> `export_const_insight_metrics` call references and nothing else.
- **No new wrappers, facades, aliases, or `# noqa`/analyzer suppressions** to "ease" migration. The migration terminates here.
- **No STRUCT-*, CONV-*, or other category work.** Inline-comment coverage improves implicitly on touched lines (NON-NEGOTIABLE rule) but is not a dedicated objective.
- **Do not** rename the separate `src/export/site_insights_exporter.py::_metric_compatible_with_platform` (L64) -- it is a distinct, correctly-named `src` symbol.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Architectural Compliance to Green (Priority: P1)

As a maintainer enforcing the "no wrappers" NON-NEGOTIABLE, I need every `ARCH-DELEGATE` and `ARCH-NAMING` violation in `MistHelper.py` eliminated so the gate stops flagging the file and future contributors cannot cite existing wrappers as license to add more.

**Independent Test**: `python tools/check_compliance.py MistHelper.py`; `ARCH-DELEGATE` and `ARCH-NAMING` counters MUST be 0.

**Acceptance Scenarios**:

1. **Given** the fresh baseline (33 ARCH-DELEGATE + 3 ARCH-NAMING), **When** the cleanup completes, **Then** `check_compliance.py MistHelper.py` reports 0 for both categories.
2. **Given** the 6 dunder/closure false positives, **When** the analyzer fix lands, **Then** `tools/compliance_analyzer` no longer flags Python special-method forwarders or nested closures as delegators, and a regression test proves a *real* class-level delegator is still flagged.
3. **Given** the existing guardrail tests, **When** the live delegators are removed, **Then** all guardrail + unit tests still pass (callers repointed to the `src` implementations).

### Edge Cases

- **`device_events_52w_legacy` name collision**: the intended non-indirection name `device_events_52w` already exists (the live delegator at L9600). The legacy method + its `_52w_*` helper cluster are **dead, superseded** code (only their own test references them) -> **DELETE** the cluster and its test rather than rename.
- **`export_legacy` is dependency-injected**: `src/export/site_insights_exporter.py` binds the injected dep to module name `InsightMetricsUtils`, so `src` callers reach the renamed method via `_parent.InsightMetricsUtils.export_const_insight_metrics()`. Two `src` operation modules + two test `SimpleNamespace` DI attrs must rename in lock-step, and the `export_legacy` guardrail allowlist tightens to empty.
- **Stateful facade `FirmwareManager`**: unlike the stateless delegators, it is instantiated (`FirmwareManager(apisession, org_id)`) at 5 call sites. Inlining is not viable; convert to a `@staticmethod create(...)` factory returning the fully-wired `src` implementation, and repoint the 5 call sites.

## Disposition Table *(authoritative -- fresh line numbers)*

### ARCH-DELEGATE (33)

| # | Line | Symbol | Disposition |
|---|------|--------|-------------|
| 1 | 1355 | `DateTimeHandler.__call__` | **EXEMPT** (dunder) -- analyzer fix |
| 2 | 2930 | `_mist_get_impl` | **EXEMPT** (nested closure) -- analyzer fix |
| 3-11 | 11364-11404 | `OrgDeviceInventorySummary._fetch_switch_physical_inventory`, `_aggregate_switch_counts`, `_fetch_gateway_physical_inventory`, `_aggregate_gateway_counts`, `_fetch_all_counts`, `_fetch_versions_per_model`, `_display_pivot_and_export`, `_display_and_export`, `_resolve_safe_org_name` | **DELETE** (zero callers) |
| 12 | 11409 | `OrgDeviceInventorySummary._run_for_org` | **REWIRE** callbacks L11431/L11452 to `src` impl, then **DELETE** |
| 13-15 | 11424-11442 | `_fetch_org_list`, `_display_combined_pivot_and_export`, `_build_combined_reports` | **DELETE** (zero callers) |
| 16 | 14234 | `ServicePingManager.__getattr__` | **EXEMPT** (dunder) -- analyzer fix |
| 17 | 15849 | `GatewayTestExporter.fetch_device_stats` | **EXEMPT** (nested closure) -- analyzer fix |
| 18-21 | 16177-16201 | `TroubleshootUtils._fetch_org_insights`, `_process_insight_response`, `_log_endpoint_error`, `_handle_insights_error` | **DELETE** (zero callers) |
| 22 | 16317 | `SSHRunnerManager.by_gateway_template` | **INLINE** at menu L21631, then **DELETE** |
| 23 | 16322 | `SSHRunnerManager._collect_missing_data` | **REPOINT** guardrail tests to `src`, then **DELETE** |
| 24-28 | 16333-16369 | `_execute_ssh`, `_select_gateway_template`, `_filter_gateways`, `_display_filtered_gateways`, `_execute_by_template` | **DELETE** (zero callers) |
| 29 | 16364 | `SSHRunnerManager._confirm_execution` | **REPOINT** guardrail tests to `src`, then **DELETE** |
| 30 | 16596 | `ARPCommandManager.on_error` | **EXEMPT** (nested closure) -- analyzer fix |
| 31 | 16790 | `AddressComparisonCounters.increment_parse_failure` | **DELETE** (zero callers) |
| 32 | 16873 | `WAN2MigrationManager.__getattr__` | **EXEMPT** (dunder) -- analyzer fix |
| 33 | 18506 | `FirmwareManager.check_firmware_upgrade_status` (facade class) | **FACTORY-CONVERT** class to `create()`; repoint 5 call sites |

### ARCH-NAMING (3)

| # | Line | Symbol | Disposition |
|---|------|--------|-------------|
| 1 | 9773 | `OrgAlarmEventExporter.device_events_52w_legacy` (+ `_52w_*` cluster) | **DELETE** dead cluster + its test |
| 2 | 14034 | `SiteExportUtils._metric_compatible_with_platform` (facade) | **RENAME** -> `_metric_supported_on_platform` (forwards to unchanged `src`) |
| 3 | 15199 | `InsightMetricsUtils.export_legacy` | **RENAME** -> `export_const_insight_metrics` (8 touch points + tighten guardrail) |

## Approach: Analyzer "Fix Over Suppress" *(mandatory rationale)*

The 6 EXEMPT entries are not architectural wrappers; they are language constructs the detector mis-classifies:

- **Dunder forwarders** (`__call__`, `__getattr__`) are Python's *prescribed* delegation protocol (e.g., `__getattr__` proxies attribute access). The `_is_stub` check already exempts dunders (precedent); `_is_delegation` must too.
- **Nested closures** forward outer-scope state by design; the `analyze` pass uses `ast.walk` (flat) and loses parent context, so closures look like top-level delegators. The fix threads an `is_nested` flag so only class-/module-level functions are eligible for the delegation rule.

This is the project's documented "fix over suppress" stance: correct the detector once, with regression tests, rather than scatter per-line suppressions. The fix is conservative -- it narrows ONLY dunders and nested functions; every real class-level delegator stays flagged (proven by a regression test).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `ARCH-DELEGATE` and `ARCH-NAMING` counts for `MistHelper.py` MUST be 0 post-change.
- **FR-002**: Every deleted symbol MUST be proven caller-free across `MistHelper.py`, `tests/`, and `src/` before deletion.
- **FR-003**: Live delegators (`_run_for_org`, `by_gateway_template`, `_collect_missing_data`, `_confirm_execution`, FirmwareManager methods) MUST have their callers/tests repointed to the `src` implementation; behavior MUST be preserved.
- **FR-004**: The analyzer fix MUST add unit tests proving (a) dunder forwarders are not flagged, (b) nested closures are not flagged, (c) a real class-level delegator IS still flagged.
- **FR-005**: The `export_legacy` guardrail (`test_no_export_legacy_callsites.py`) MUST remain enforcing (allowlist tightened to empty set).

### Coding-Standard Requirements (NON-NEGOTIABLE -- from `agents.md` / `copilot-instructions.md`)

- **CR-001 Inline comments**: every touched executable line carries an inline comment explaining *why*.
- **CR-002 Action logging**: `logging.info()` before each meaningful operation, `logging.debug()` after with a result summary; ASCII-only (no Unicode/emoji).
- **CR-003 safe_input**: any retained input path uses `InputUtils.safe_input` (no bare `input()`).
- **CR-004 Class-based**: no standalone wrapper functions introduced; the FirmwareManager factory is a `@staticmethod` on the class.
- **CR-005 5-Item Rule**: no new function exceeds 5 params / 25 lines / 5 blocks.
- **CR-006 Paths**: `os.path.join` / `pathlib.Path`, never hardcoded separators.

## Test Plan *(mandatory)*

Local workaround (corrupted venv -- dash plugin autoload only): run affected tests with
`$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; & ".venv\Scripts\python.exe" -m pytest <files> -o addopts="" -q`
(add `--noconftest` for `test_compliance_analyzer.py`).

1. **Analyzer**: `tests/unit/test_compliance_analyzer.py` -- new dunder-exempt, closure-exempt, and still-flagged regression cases pass.
2. **SSH guardrails**: `tests/guardrails/test_wave1_logging_envelopes.py`, `test_wave1_safe_input_paths.py` -- repointed to `src` `SSHRunnerManager` with injected deps; pass.
3. **Exports**: `tests/unit/test_exports.py`, `tests/unit/export/test_site_insights_exporter.py`, `tests/unit/export/test_site_export_utils.py` -- renamed DI attrs + monkeypatches pass.
4. **Guardrail**: `tests/unit/test_no_export_legacy_callsites.py` -- passes with empty allowlist.
5. **Deletion safety**: `tests/unit/test_device_events_52w_exporter.py` still passes (live path coverage); `tests/unit/test_device_events_52w_legacy.py` removed with the dead cluster.
6. **Gates**: `python -m py_compile MistHelper.py`; `python -m ruff check MistHelper.py tools/compliance_analyzer/analyzers.py`; `python -m black --check MistHelper.py tools/compliance_analyzer/analyzers.py`.
7. **Score**: re-run `extract_viol.py` + `check_compliance.py` -> ARCH-DELEGATE=0, ARCH-NAMING=0.

## Acceptance Criteria *(mandatory)*

- [x] `check_compliance.py MistHelper.py` -> `ARCH-DELEGATE` = 0, `ARCH-NAMING` = 0. (score 30.0 -> 54.0; Architecture un-pinned)
- [x] No new wrappers/aliases/`# noqa`/suppressions introduced.
- [x] All 6 exemptions are detector fixes (dunder/closure), each covered by a regression test; a real delegator remains flagged.
- [x] FirmwareManager is a `create()` factory; 5 call sites repointed; behavior preserved.
- [x] `export_legacy` renamed across all 8 touch points; guardrail allowlist empty and passing.
- [x] Dead `device_events_52w_legacy` + `_52w_*` cluster + its test removed; live `device_events_52w` path unaffected.
- [x] Every touched line carries an inline *why* comment; action logging added; ASCII-only.
- [x] `py_compile`, `ruff`, `black` all green on `MistHelper.py` and `analyzers.py`.
- [x] Affected unit + guardrail tests pass via the local workaround. (20 passed; 1 pre-existing wcwidth venv failure unrelated to this change)
- [ ] PR links this spec and Issue #440 ("Part of #431"); CodeQL + all gates green before `auto-merge`.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Architecture stays pinned at cap if any delegate survives | Land all 33+3 + 6 analyzer exemptions together; verify empirically via `check_compliance.py` |
| Deleting a "dead" method that has a hidden caller | Grep `MistHelper.py` + `tests/` + `src/` for each symbol before deletion (FR-002) |
| Hot-file contention with PR #406 | Keep this PR small/focused; rebase on `main`, never branch from feature branches |
| black reformats multi-line factory call | Write the factory's wiring call single-line |
| Guardrail test breaks after repoint | Use the `_make_deps()` template from `tests/unit/ssh/test_ssh_runner_manager.py` |
