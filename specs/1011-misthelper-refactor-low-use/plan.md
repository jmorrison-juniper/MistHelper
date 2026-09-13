# Implementation Plan: MistHelper.py Refactor Extraction — Low-Use Second Pass

**Branch**: `1011-misthelper-refactor-low-use` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1011-misthelper-refactor-low-use/spec.md`
**Predecessor**: `specs/1010-misthelper-refactor-extraction/` (13 PRs merged, closed with baseline 99.6/A+ and MistHelper.py LoC drop >=600)

## Summary

Continue the systematic decomposition of `MistHelper.py` by consuming the **Low-Use bucket** (2 <= callers <= 3) surfaced by the post-PR-13-merge `refactor_candidates.md` (`unused=0, single-use=0, low-use=20, hot=80, skipped=1`). Each of the 20 candidates is a single serial PR that (a) creates the target module (or folds into an existing sibling module — `FirmwareManager` — for three firmware-related candidates), (b) rewrites all 2-3 callsites atomically in the same diff, (c) deletes the original symbol from `MistHelper.py`, (d) resolves any analyzer `guideline_flags` in-flight, (e) renames double-underscore analyzer-suggested filenames to single-underscore per FR-020, and (f) lands with all 15 functional CI jobs green and A+/100 compliance on affected files. Three candidates (`main`, `marvis_data_utils`, `MIST_WAN_TARGET_PORTS`) have cross-file callers and are dispatched as **P2 multi-file rewrites** after the P1 single-file cluster completes. No wrapper shims. No parallel branches. No `--admin` bypass except where `mergeStateStatus` is genuinely BLOCKED/DIRTY/BEHIND with root cause documented. Between merges, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched, so the queue always reflects the current `main` head.

## Technical Context

**Language/Version**: Python 3.13 (project target per repo tooling and CI matrix)
**Primary Dependencies**: standard library only for extraction targets; existing project deps preserved (no new dependencies introduced by this initiative)
**Storage**: N/A for extraction work itself
**Testing**: `pytest` for unit/integration; existing 15 functional CI jobs (matrix build, ruff, mypy, compliance analyzer, refactor analyzer smoke, integration suites) as the mergeability contract
**Target Platform**: Windows-first CLI; extracted modules remain platform-neutral (`pathlib.Path`, ASCII-only logs)
**Project Type**: Single-project CLI tool with a monolithic entrypoint being decomposed into `src/*` sub-packages
**Performance Goals**: No performance regression at any callsite after extraction; interactive latency for CLI menus unchanged
**Constraints**: Zero wrapper shims may be left in `MistHelper.py`; every extracted module lands at A+/100 compliance; repo-wide baseline stays >=99.6/A+; no A+ file may regress; no touching of `SKIP_ALWAYS` (`GlobalImportManager`) or Hot bucket (4+ callers) symbols; serial PR workflow only; `raw_input_call` flag on `WLANRadiusTimerManager` is resolved with `safe_input()` on landing (FR-006); double-underscore analyzer-suggested module names are renamed to single-underscore during landing (FR-020)
**Scale/Scope**: 20 PRs in second pass, ~2,749 LoC extraction budget targeting >=2,500 lines of physical reduction in `MistHelper.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.4.0 (ratified 2026-03-05). Evaluated per the seven core principles.

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule (all menu options in groups of 5, cross-category prohibited) | PASS | Extraction is a code-organization change; no menu structure is added, removed, or reordered. |
| II. Class-Based Architecture (functions live inside cohesive classes) | PASS + REINFORCED | FR-005 explicitly refactors module-level function candidates (`initialize_mist_session_interactive`, `initialize_mist_session`, `main`) into class-body methods on landing. |
| III. Safety-First Development (destructive operations gated) | PASS | Extraction moves existing behavior; no new destructive operations introduced. Pre-existing safety gates on `WLANRadiusTimerManager`, `WANProbeConfigManager`, and firmware managers are preserved verbatim. |
| IV. Full Deployment Pipeline (15 CI jobs must pass, no --admin bypass) | PASS + REINFORCED | FR-011 codifies the CI gate; `feedback_no_admin_bypass.md` guidance applied — check `mergeStateStatus` before considering any bypass. |
| V. Observability & Logging (structured, ASCII-only, `safe_input`, `pathlib.Path`) | PASS + REINFORCED | FR-007 mandates ASCII-only logs, `safe_input()`, `pathlib.Path` in every extracted module. Analyzer `guideline_flags` covering these (notably `raw_input_call` on `WLANRadiusTimerManager`, `non_ascii_logs` on multiple candidates) are resolved in the extraction PR (FR-006). |
| VI. Inline Comments Every 5-10 Lines (NON-NEGOTIABLE) | PASS + REINFORCED | Each new module under `src/refactors/` must land A+/100, which requires the inline-comment cadence. Any `missing_inline_comments` flag on extracted code (notably `FirmwareUpgradeStatusChecker`) is resolved in the same PR (FR-006). |
| VII. Action Logging Before Every Non-Trivial Action (NON-NEGOTIABLE) | PASS + REINFORCED | Any `missing_action_logging` flag on extracted code is resolved in the same PR (FR-006). Constitution's `[LOGIN]`, `[MENU]`, `[EXECUTE]`, `[SUCCESS]`, `[FAILURE]` prefix convention is preserved. |

**Result**: All seven principles pass. Two principles (VI, VII) are NON-NEGOTIABLE and are reinforced rather than at risk. No violations require Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/1011-misthelper-refactor-low-use/
|-- plan.md                        # This file (/speckit.plan output)
|-- spec.md                        # Feature specification (input)
|-- checklists/                    # Reserved for downstream /speckit.checklist runs
`-- contracts/                     # Reserved for downstream contract artifacts
```

### Source Code (repository root)

```text
MistHelper.py                                # Entrypoint monolith - shrinks by >=2,500 lines across 20 PRs
tools/refactor_analyzer/                     # Analyzer package - CONSUMED AS-IS, never modified (FR-018)
tools/compliance_analyzer/                   # Compliance analyzer - used to verify A+/100 on affected files
refactor_candidates.md                       # Regenerated after every merged extraction PR (FR-010)
data/full_repo_compliance_current.md         # Compliance baseline snapshot - must stay >=99.6/A+
src/
|-- refactors/                               # DESTINATION for 17 of 20 Low-Use extractions
|   |-- __init__.py                          # Existing
|   |-- serial_cc/                           # Existing sub-package
|   |-- wlanradius_timer_manager.py          # NEW - PR-14 (LOC 787, raw_input_call resolved)
|   |-- wanprobe_config_manager.py           # NEW - PR-15 (LOC 473)
|   |-- anomaly_metrics_discovery.py         # NEW - PR-16 (LOC 91)
|   |-- device_data_fetcher.py               # NEW - PR-17 (LOC 68)
|   |-- inventory_csvcomparator.py           # NEW - PR-18 (LOC 47)
|   |-- device_config_template_cloner_manager.py  # NEW - PR-20 (LOC 27)
|   |-- wanprobe_device_override_manager.py  # NEW - PR-21 (LOC 23)
|   |-- initialize_mist_session_interactive.py    # NEW - PR-23 (fn->method)
|   |-- initialize_mist_session.py           # NEW - PR-24 (fn->method)
|   |-- package_import_map.py                # NEW - PR-25 (assignment constant)
|   |-- main.py                              # NEW - PR-26 (P2 cross-file, fn->method)
|   |-- marvis_data_utils.py                 # NEW - PR-27 (P2 cross-file, assignment)
|   |-- fast_mode_backoff_multiplier.py      # NEW - PR-28 (FR-020 rename from fast__mode__backoff__multiplier)
|   |-- fast_mode_devices_per_thread.py      # NEW - PR-29 (FR-020 rename)
|   |-- fast_mode_sequential_max_retries.py  # NEW - PR-30 (FR-020 rename)
|   |-- fast_mode_use_connection_aware_threading.py  # NEW - PR-31 (FR-020 rename)
|   `-- mist_wan_target_ports.py             # NEW - PR-32 (P2 cross-file, FR-020 rename)
`-- firmware/
    `-- firmware_manager.py                  # EXISTING - receives 3 candidates per FR-015 exception:
                                             #   PR-19: FirmwareUpgradeStatusChecker (LOC 958)
                                             #   PR-22: BulkAPFirmwareUpgrader      (LOC 32)
                                             #   PR-33: BulkSwitchFirmwareUpgrader  (LOC 19)
```

**Structure Decision**: Single-project layout. 17 of 20 Low-Use extractions land under `src/refactors/` with a per-symbol module file. **Three exceptions** fold into the existing `src/firmware/firmware_manager.py::FirmwareManager` because their sole callers already live there (FR-015 — mirrors 1010's `AddressComparisonCounters -> CsvComparatorManager` pattern). Five module names are renamed from the analyzer's double-underscore suggestions (`fast__mode__backoff__multiplier.py` -> `fast_mode_backoff_multiplier.py`) per FR-020 to conform to PEP 8 module naming.

### PR Dispatch Queue (Authoritative Order)

Per FR-001 (LOC-DESC within priority band) and FR-014 (exact 20-candidate second-pass budget). P1 (single-file callers) is dispatched before P2 (cross-file callers) so any grep-audit failure in P2 does not block the P1 cluster:

| PR | Priority | Candidate | Kind | LoC | Refs | Source in MistHelper.py | Destination |
|----|----------|-----------|------|-----|------|-------------------------|-------------|
| 14 | P1 | `WLANRadiusTimerManager` | class | 787 | 3 | 20044, 21515 | `src/refactors/wlanradius_timer_manager.py` (resolve `raw_input_call`) |
| 15 | P1 | `WANProbeConfigManager` | class | 473 | 2 | 21720 | `src/refactors/wanprobe_config_manager.py` |
| 16 | P1 | `AnomalyMetricsDiscovery` | class | 91 | 2 | 12994 | `src/refactors/anomaly_metrics_discovery.py` |
| 17 | P1 | `DeviceDataFetcher` | class | 68 | 3 | 15292, 15309, 15325 | `src/refactors/device_data_fetcher.py` |
| 18 | P1 | `InventoryCSVComparator` | class | 47 | 3 | 16488, 21541 | `src/refactors/inventory_csvcomparator.py` |
| 19 | P1 | `FirmwareUpgradeStatusChecker` | class | 958 | 2 | firmware_manager.py:1746, 1753 | `src/firmware/firmware_manager.py::FirmwareManager` (FR-015; resolve `oversize_25_lines`, `missing_inline_comments`, `non_ascii_logs`) |
| 20 | P1 | `DeviceConfigTemplateClonerManager` | class | 27 | 2 | 21922 | `src/refactors/device_config_template_cloner_manager.py` |
| 21 | P1 | `WANProbeDeviceOverrideManager` | class | 23 | 2 | 21724 | `src/refactors/wanprobe_device_override_manager.py` |
| 22 | P1 | `BulkAPFirmwareUpgrader` | class | 32 | 2 | firmware_manager.py:1733, 1736 | `src/firmware/firmware_manager.py::FirmwareManager` (FR-015) |
| 23 | P1 | `initialize_mist_session_interactive` | fn | 18 | 3 | 2237, 19356, 23190 | `src/refactors/initialize_mist_session_interactive.py` (fn->method per FR-005) |
| 24 | P1 | `initialize_mist_session` | fn | 18 | 2 | 23195, 23258 | `src/refactors/initialize_mist_session.py` (fn->method per FR-005) |
| 25 | P1 | `PACKAGE_IMPORT_MAP` | assignment | 13 | 2 | 354, 538 | `src/refactors/package_import_map.py` |
| 26 | P2 | `main` | fn | 12 | 2 | MistHelper.py:23700 **+ src/maps/maps_manager.py:2794** | `src/refactors/main.py` (fn->method per FR-005; cross-file audit per FR-019) |
| 27 | P2 | `marvis_data_utils` | assignment | 4 | 3 | MistHelper.py:6594, 15736 **+ src/troubleshooting/marvis_troubleshoot_utils.py:21** | `src/refactors/marvis_data_utils.py` (cross-file audit per FR-019) |
| 28 | P1 | `FAST_MODE_BACKOFF_MULTIPLIER` | assignment | 3 | 3 | 1969, 9980, 15409 | `src/refactors/fast_mode_backoff_multiplier.py` (FR-020 rename) |
| 29 | P1 | `FAST_MODE_DEVICES_PER_THREAD` | assignment | 3 | 2 | 1972, 7470 | `src/refactors/fast_mode_devices_per_thread.py` (FR-020 rename) |
| 30 | P1 | `FAST_MODE_SEQUENTIAL_MAX_RETRIES` | assignment | 3 | 2 | 1977, 15549 | `src/refactors/fast_mode_sequential_max_retries.py` (FR-020 rename) |
| 31 | P1 | `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 2 | 1984, 7460 | `src/refactors/fast_mode_use_connection_aware_threading.py` (FR-020 rename) |
| 32 | P2 | `MIST_WAN_TARGET_PORTS` | assignment | 3 | 3 | MistHelper.py:1992, 15638 **+ src/gateway/gateway_export_utils.py:51** | `src/refactors/mist_wan_target_ports.py` (FR-020 rename; cross-file audit per FR-019) |
| 33 | P1 | `BulkSwitchFirmwareUpgrader` | class | 19 | 2 | firmware_manager.py:1832, 1833 | `src/firmware/firmware_manager.py::FirmwareManager` (FR-015) |

LOC figures and callsite line numbers are the analyzer's snapshot at spec creation; each PR uses the *fresh* analyzer output post-preceding-merge per FR-010, so line numbers may shift within tolerance. Reference counts may also shift (a Low-Use candidate could drop a caller during a preceding PR and become Single-Use, or gain a caller and become Hot — the fresh catalog is authoritative per FR-016).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 design artifacts landed:

- **I. Five-Item Rule** — Still PASS. No menu topology changed.
- **II. Class-Based Architecture** — Still PASS. Dispatch queue explicitly requires class-body landing for the three module-level function candidates (`initialize_mist_session_interactive`, `initialize_mist_session`, `main`).
- **III. Safety-First** — Still PASS. No new destructive paths.
- **IV. Full Deployment Pipeline** — Still PASS. FR-011 and the serial merge protocol enforce the 15-job gate and the no-`--admin` policy.
- **V. Observability & Logging** — Still PASS. FR-006/FR-007 require ASCII logs, `safe_input()`, and `pathlib.Path`; `raw_input_call` on `WLANRadiusTimerManager` and `non_ascii_logs` on `FirmwareUpgradeStatusChecker` are resolved in-flight.
- **VI. Inline Comments** — Still PASS + NON-NEGOTIABLE. A+/100 module gate enforces the 5-10 line comment cadence; `missing_inline_comments` flag on `FirmwareUpgradeStatusChecker` is resolved in the same PR.
- **VII. Action Logging** — Still PASS + NON-NEGOTIABLE. `guideline_flags` resolution requirement enforces action logging on extracted code.

**Final verdict**: All seven principles pass post-design. No Complexity Tracking entries required.

## What This Plan Does NOT Do

- Does not open, sequence, or merge extraction PRs — that is the parent conversation's dispatch responsibility (Assumption 7 in spec).
- Does not modify `tools/refactor_analyzer/` (FR-018).
- Does not touch `SKIP_ALWAYS` symbols like `GlobalImportManager` (FR-008).
- Does not touch Hot bucket symbols with 4+ callers (FR-009).
- Does not batch multiple candidates into one PR (FR-002).
- Does not leave wrapper shims or forwarding functions (FR-003, SC-008).
- Does not re-scope the Hot bucket (80 candidates, deferred to a future `1012-*` initiative if warranted).
- Does not bring external-file callers (in `src/maps/`, `src/troubleshooting/`, `src/gateway/`) up to A+/100 compliance — those are pre-existing modules and only the import/reference lines are rewritten (FR-019 scope-limited to grep audit).
