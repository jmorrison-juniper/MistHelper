# Implementation Plan: MistHelper.py Refactor Extraction Initiative

**Branch**: `1010-misthelper-refactor-extraction` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1010-misthelper-refactor-extraction/spec.md`

## Summary

Systematically decompose `MistHelper.py` (~28K-line entrypoint monolith) into cohesive class modules under `src/refactors/` by consuming the analyzer catalog at `refactor_candidates.md`. The first-pass budget covers exactly 13 candidates — 2 Unused (delete only) and 11 Single-Use (move + rewrite single callsite + delete original) — processed in strict serial order (Unused first, then Single-Use LOC-DESC). Each extraction is a single PR that (a) creates the target module (or folds into an existing sibling module for `AddressComparisonCounters`), (b) rewrites the single callsite atomically, (c) deletes the original symbol from `MistHelper.py`, (d) resolves any analyzer `guideline_flags` in-flight, and (e) lands with all 15 functional CI jobs green and A+/100 compliance on affected files. No wrapper shims. No parallel branches. No `--admin` bypass except where `mergeStateStatus` is genuinely BLOCKED/DIRTY/BEHIND with root cause documented. Between merges, the analyzer is re-run and `refactor_candidates.md` is regenerated before the next PR is dispatched, so the queue always reflects the current `main` head.

## Technical Context

**Language/Version**: Python 3.13 (project target per repo tooling and CI matrix)
**Primary Dependencies**: standard library only for extraction targets; existing project deps preserved (no new dependencies introduced by this initiative)
**Storage**: N/A for extraction work itself; extracted `SQLiteDatabaseWriter` operates on a local SQLite file as it does today
**Testing**: `pytest` for unit/integration; existing 15 functional CI jobs (matrix build, ruff, mypy, compliance analyzer, refactor analyzer smoke, integration suites) as the mergeability contract
**Target Platform**: Windows-first CLI (project ships as `MistHelper.py` entrypoint); extracted modules must remain platform-neutral (use `pathlib.Path`, ASCII-only logs)
**Project Type**: Single-project CLI tool with a monolithic entrypoint being decomposed into `src/*` sub-packages
**Performance Goals**: No performance regression at any callsite after extraction; interactive latency for CLI menus unchanged
**Constraints**: Zero wrapper shims may be left in `MistHelper.py`; every extracted module lands at A+/100 compliance; repo-wide baseline stays ≥99.6/A+; no A+ file may regress; no touching of `SKIP_ALWAYS` (`GlobalImportManager`) or Hot bucket (4+ callers) symbols in first pass; serial PR workflow only
**Scale/Scope**: 13 PRs in first pass, ~811 LoC extraction budget targeting ≥600 lines of physical reduction in `MistHelper.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.4.0 (ratified 2026-03-05). Evaluated per the seven core principles.

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule (all menu options in groups of 5, cross-category prohibited) | PASS | Extraction is a code-organization change; no menu structure is added, removed, or reordered. |
| II. Class-Based Architecture (functions live inside cohesive classes) | PASS + REINFORCED | FR-005 explicitly refactors module-level function candidates into class-body methods on landing (`run_systematic_test`, `switch_to_interactive_login`, `run_interactive_test`, `listen_keyboard`). |
| III. Safety-First Development (destructive operations gated) | PASS | Extraction moves existing behavior; no new destructive operations introduced. Pre-existing safety gates on `SQLiteDatabaseWriter` and other candidates are preserved verbatim. |
| IV. Full Deployment Pipeline (15 CI jobs must pass, no --admin bypass) | PASS + REINFORCED | FR-011 codifies the CI gate; `feedback_no_admin_bypass.md` guidance applied — check `mergeStateStatus` before considering any bypass. |
| V. Observability & Logging (structured, ASCII-only, `safe_input`, `pathlib.Path`) | PASS + REINFORCED | FR-007 mandates ASCII-only logs, `safe_input()`, `pathlib.Path` in every extracted module. Analyzer `guideline_flags` covering these are resolved in the extraction PR (FR-006). |
| VI. Inline Comments Every 5-10 Lines (NON-NEGOTIABLE) | PASS + REINFORCED | Each new module under `src/refactors/` must land A+/100, which requires the inline-comment cadence. Any `missing_inline_comments` flag on extracted code is resolved in the same PR (FR-006). |
| VII. Action Logging Before Every Non-Trivial Action (NON-NEGOTIABLE) | PASS + REINFORCED | Any `missing_action_logging` flag on extracted code is resolved in the same PR (FR-006). Constitution's `[LOGIN]`, `[MENU]`, `[EXECUTE]`, `[SUCCESS]`, `[FAILURE]` prefix convention is preserved. |

**Result**: All seven principles pass. Two principles (VI, VII) are NON-NEGOTIABLE and are reinforced rather than at risk. No violations require Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/1010-misthelper-refactor-extraction/
├── plan.md                        # This file (/speckit.plan output)
├── spec.md                        # Feature specification (input)
├── research.md                    # Phase 0 output
├── data-model.md                  # Phase 1 output — extraction entities
├── quickstart.md                  # Phase 1 output — per-PR operator recipe
├── contracts/
│   ├── analyzer-output-contract.md    # Refactor analyzer → dispatcher contract
│   ├── extraction-pr-contract.md      # Per-PR contract (diff shape, checklist)
│   └── compliance-gate-contract.md    # A+/100 module + baseline preservation
├── checklists/
│   └── requirements.md            # Existing checklist (all items checked)
└── tasks.md                       # Phase 2 output (produced by /speckit.tasks, not by this command)
```

### Source Code (repository root)

```text
MistHelper.py                                # Entrypoint monolith — shrinks by ≥600 lines across 13 PRs
tools/refactor_analyzer/                     # Analyzer package — CONSUMED AS-IS, never modified (FR-018)
tools/compliance_analyzer/                   # Compliance analyzer — used to verify A+/100 on affected files
refactor_candidates.md                       # Regenerated after every merged extraction PR (FR-010)
data/full_repo_compliance_current.md         # Compliance baseline snapshot — must stay ≥99.6/A+
src/
├── refactors/                               # DESTINATION for 10 of 11 Single-Use extractions
│   ├── __init__.py                          # Existing
│   ├── serial_cc/                           # Existing sub-package (validates the pattern)
│   ├── sqlite_database_writer.py            # NEW — PR-03 (largest Single-Use)
│   ├── tui_launcher.py                      # NEW — PR-04
│   ├── data_directory_checker.py            # NEW — PR-05
│   ├── maps_manager_launcher.py             # NEW — PR-06
│   ├── service_ping_manager.py              # NEW — PR-08
│   ├── wan2_migration_manager.py            # NEW — PR-09
│   ├── systematic_test_runner.py            # NEW — PR-10 (holds run_systematic_test-as-method)
│   ├── interactive_login_switcher.py        # NEW — PR-11 (holds switch_to_interactive_login-as-method)
│   ├── interactive_test_runner.py           # NEW — PR-12 (holds run_interactive_test-as-method)
│   └── keyboard_listener.py                 # NEW — PR-13 (holds listen_keyboard-as-method)
└── inventory/
    └── csv_comparator.py                    # EXISTING — receives AddressComparisonCounters (PR-07) per FR-015
```

**Structure Decision**: Single-project layout. Every Single-Use extraction lands under `src/refactors/` with a per-symbol module file, **except** `AddressComparisonCounters` which folds into `src/inventory/csv_comparator.py::CsvComparatorManager` because its sole caller already lives there (FR-015). The existing `src/refactors/serial_cc/` sub-package validates this layout convention. Unused deletions (`PerformanceMonitor`, `MapViewerConfig`) create no new files — the definition is simply removed from `MistHelper.py`.

### PR Dispatch Queue (Authoritative Order)

Per FR-001 (Unused first, then Single-Use LOC-DESC) and FR-014 (exact 13-candidate first-pass budget):

| PR | Bucket | Candidate | LoC | Source in MistHelper.py | Destination |
|----|--------|-----------|-----|-------------------------|-------------|
| 01 | Unused | `PerformanceMonitor` | 40 | 365-404 | DELETE (no new file) |
| 02 | Unused | `MapViewerConfig` | 9 | 441-449 | DELETE (no new file) |
| 03 | Single-Use | `SQLiteDatabaseWriter` | 316 | 6949-7265 | `src/refactors/sqlite_database_writer.py` |
| 04 | Single-Use | `TUILauncher` | 154 | (see analyzer output) | `src/refactors/tui_launcher.py` |
| 05 | Single-Use | `DataDirectoryChecker` | 74 | (see analyzer output) | `src/refactors/data_directory_checker.py` |
| 06 | Single-Use | `MapsManagerLauncher` | 64 | (see analyzer output) | `src/refactors/maps_manager_launcher.py` |
| 07 | Single-Use | `AddressComparisonCounters` | 62 | (see analyzer output) | `src/inventory/csv_comparator.py::CsvComparatorManager` (FR-015 exception) |
| 08 | Single-Use | `ServicePingManager` | 50 | (see analyzer output) | `src/refactors/service_ping_manager.py` |
| 09 | Single-Use | `WAN2MigrationManager` | 48 | (see analyzer output) | `src/refactors/wan2_migration_manager.py` |
| 10 | Single-Use | `run_systematic_test` (module-level fn) | ~35 | (see analyzer output) | `src/refactors/systematic_test_runner.py` (as class method per FR-005) |
| 11 | Single-Use | `switch_to_interactive_login` (module-level fn) | ~30 | (see analyzer output) | `src/refactors/interactive_login_switcher.py` (as class method) |
| 12 | Single-Use | `run_interactive_test` (module-level fn) | ~28 | (see analyzer output) | `src/refactors/interactive_test_runner.py` (as class method) |
| 13 | Single-Use | `listen_keyboard` (module-level fn) | ~24 | (see analyzer output) | `src/refactors/keyboard_listener.py` (as class method) |

LOC figures are the analyzer's snapshot at spec creation; each PR uses the *fresh* analyzer output post-preceding-merge per FR-010, so line numbers may shift within tolerance.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 design artifacts landed:

- **I. Five-Item Rule** — Still PASS. No menu topology changed.
- **II. Class-Based Architecture** — Still PASS. Data-model and contracts explicitly require class-body landing for module-level function candidates.
- **III. Safety-First** — Still PASS. No new destructive paths.
- **IV. Full Deployment Pipeline** — Still PASS. `contracts/extraction-pr-contract.md` and `contracts/compliance-gate-contract.md` codify the 15-job gate and the no-`--admin` policy.
- **V. Observability & Logging** — Still PASS. `data-model.md` "Target Module" entity requires ASCII logs, `safe_input()`, and `pathlib.Path`; `contracts/compliance-gate-contract.md` requires flag resolution.
- **VI. Inline Comments** — Still PASS + NON-NEGOTIABLE. A+/100 module gate in the compliance contract enforces the 5-10 line comment cadence.
- **VII. Action Logging** — Still PASS + NON-NEGOTIABLE. `guideline_flags` resolution requirement in the PR contract enforces action logging on extracted code.

**Final verdict**: All seven principles pass post-design. No Complexity Tracking entries required.

## What This Plan Does NOT Do

- Does not open, sequence, or merge extraction PRs — that is the parent conversation's dispatch responsibility (Assumption 7 in spec).
- Does not modify `tools/refactor_analyzer/` (FR-018).
- Does not touch `SKIP_ALWAYS` symbols like `GlobalImportManager` (FR-008).
- Does not touch Hot bucket symbols with 4+ callers (FR-009).
- Does not batch multiple candidates into one PR (FR-002).
- Does not leave wrapper shims or forwarding functions (FR-003, SC-008).
- Does not scope second-pass Low-Use candidates or unrelated feature backlogs (FR-017, Assumption 6).
