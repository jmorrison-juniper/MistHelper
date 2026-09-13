# Implementation Plan: MistHelper.py Refactor — Hot-Functions Bounded Bundle

**Branch**: `1012-misthelper-refactor-hot-functions` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1012-misthelper-refactor-hot-functions/spec.md`
**Predecessors**: `specs/1010-misthelper-refactor-extraction/` (13 PRs merged), `specs/1011-misthelper-refactor-low-use/` (20 PRs merged) — both closed with baseline >=99.6/A+.

## Summary

Land a **single bounded PR** consuming the three highest-value hot-bucket actions surfaced by the post-1011 analyzer catalog. Unlike the per-candidate serial workflow of 1010/1011, this initiative bundles three independent hot-bucket changes into one atomic diff because each individual action is either (a) a zero-extraction convention pin (Action 1), (b) a small wrapper-plus-extract that would be uneconomic to split across separate PRs (Action 2), or (c) a public+private helper cluster whose four members share a single lifecycle contract (Action 3). The three actions are:

- **Action 1 — tqdm skip-pin (SC-001)**: No extraction. Add a mandatory NOTE breadcrumb at `MistHelper.py:635` documenting the `GlobalImportManager` rebind pattern that makes the fallback shim bootstrap-critical, so future refactor sweeps do not accidentally propose extracting it. Pin the analyzer's `SKIP_ALWAYS` conviction with a source-level marker.
- **Action 2 — `is_debug_mode` extract (SC-002/SC-005/SC-011)**: Extract `def is_debug_mode()` at `MistHelper.py:318-320` to `IsDebugMode.check()` (static) in `src/refactors/is_debug_mode.py`. Delete `EnvironmentUtils.is_debug_mode` wrapper at `MistHelper.py:5891-5900` outright (0 callers per clarification Q1). Rewrite **12 callsites**. Rename DI slot `is_debug_mode_fn` -> `check_fn` at 5 occurrences in `src/export/site_export_utils.py` (L32/L52/L64/L76/L337) + 1 kwarg at `MistHelper.py:13372`.
- **Action 3 — `execute_with_connection_pool_management` extract (SC-003/SC-005)**: Extract the public function plus three `_pool_*` private helpers at `MistHelper.py:7503-7576` to `ConnectionPoolExecutor` in `src/refactors/connection_pool_executor.py`. Public entry lands as `@staticmethod execute()`; three helpers land as private `@staticmethod` members. Rewrite **7 callsites** (`MistHelper.py:6309/10076/15399/15564`, `src/gateway/gateway_export_utils.py:48/550`, `src/gateway/gateway_stats_exporter.py:32`). Rename DI slot `connection_pool_fn` -> `execute_fn` at 6 occurrences (`src/gateway/overrides/_deps.py:18/33/41/49`, `src/gateway/overrides/device_data_fetcher.py:40`, + 1 kwarg at `MistHelper.py:15564`).

Edit-surface total: **19 callsite rewrites + 12 DI-slot rename occurrences + 5 mandatory NOTE breadcrumbs = 36 symbol-level edits** in one PR. Two new modules created under `src/refactors/`. Zero wrapper shims remain. All 15 functional CI jobs green; pylint >=8.74/10 non-regressing; aggregate compliance >=99.6/A+; new files A+/100. Constitution v1.4.0 all seven principles PASS; VI and VII (NON-NEGOTIABLE) reinforced by the A+/100 module gate.

## Technical Context

**Language/Version**: Python 3.13 (project target per repo tooling and CI matrix)
**Primary Dependencies**: standard library only for extraction targets; existing project deps preserved (no new dependencies introduced by this initiative)
**Storage**: N/A for extraction work itself
**Testing**: `pytest` for unit/integration; existing 15 functional CI jobs (matrix build, ruff, mypy, compliance analyzer, refactor analyzer smoke, integration suites) as the mergeability contract; local pre-push Black + Ruff gate (per `feedback_prepush_black_ruff.md`)
**Target Platform**: Windows-first CLI; extracted modules remain platform-neutral (`pathlib.Path`, ASCII-only logs)
**Project Type**: Single-project CLI tool with a monolithic entrypoint being decomposed into `src/*` sub-packages
**Performance Goals**: No performance regression at any callsite after extraction; interactive latency for CLI menus unchanged; `ConnectionPoolExecutor.execute()` preserves the original pool-management contract byte-for-byte
**Constraints**: Zero wrapper shims may be left in `MistHelper.py` (FR-003); every extracted module lands at A+/100 compliance; repo-wide baseline stays >=99.6/A+; pylint stays >=8.74/10; no `--admin` merge bypass (per `feedback_no_admin_bypass.md` — check `mergeStateStatus` first); analyzer `--skip` CLI flag drives the skip-pin (Action 1) with no code deletion; all 5 breadcrumb sites must land with the pinned template strings verbatim (FR-024, SC-014)
**Scale/Scope**: 1 PR bundling 3 actions; 19 callsite rewrites + 12 DI-slot rename occurrences + 5 breadcrumbs = 36 symbol-level edits; ~90 LoC extracted net; 2 new modules under `src/refactors/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.4.0 (ratified 2026-03-05). Evaluated per the seven core principles.

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule (all menu options in groups of 5, cross-category prohibited) | PASS | Extraction is a code-organization change; no menu structure is added, removed, or reordered. |
| II. Class-Based Architecture (functions live inside cohesive classes) | PASS + REINFORCED | Actions 2 and 3 each extract a module-level function into a class-body `@staticmethod` seam per FR-005 carry-forward. `def is_debug_mode()` becomes `IsDebugMode.check()`; `execute_with_connection_pool_management()` plus 3 private helpers become `ConnectionPoolExecutor.execute()` + 3 private static members. |
| III. Safety-First Development (destructive operations gated) | PASS | Extraction moves existing behavior; no new destructive operations introduced. The `EnvironmentUtils.is_debug_mode` wrapper deletion is safe because clarification Q1 confirmed 0 callers via grep audit. |
| IV. Full Deployment Pipeline (15 CI jobs must pass, no --admin bypass) | PASS + REINFORCED | FR-011 codifies the CI gate. `feedback_no_admin_bypass.md` applied — check `mergeStateStatus: CLEAN` before merging; do not cargo-cult `--admin`; SKIPPED conditionals are not blocking. |
| V. Observability & Logging (structured, ASCII-only, `safe_input`, `pathlib.Path`) | PASS + REINFORCED | Both new modules land ASCII-only logs, no `input()` (extraction targets don't prompt), `pathlib.Path` where paths are used. Analyzer `guideline_flags` on extracted code are resolved in-flight (FR-006 carry-forward). |
| VI. Inline Comments Every 5-10 Lines (NON-NEGOTIABLE) | PASS + REINFORCED | Both new modules under `src/refactors/` must land A+/100, which enforces the 5-10 line inline-comment cadence. |
| VII. Action Logging Before Every Non-Trivial Action (NON-NEGOTIABLE) | PASS + REINFORCED | Any `missing_action_logging` flag on extracted code is resolved in the same PR (FR-006 carry-forward). Constitution's `[LOGIN]`, `[MENU]`, `[EXECUTE]`, `[SUCCESS]`, `[FAILURE]` prefix convention preserved. `ConnectionPoolExecutor.execute()` retains its original `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` breadcrumbs verbatim. |

**Result**: All seven principles pass. Two principles (VI, VII) are NON-NEGOTIABLE and are reinforced rather than at risk. No violations require Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/1012-misthelper-refactor-hot-functions/
|-- plan.md                        # This file (/speckit.plan output)
|-- spec.md                        # Feature specification (input)
|-- research.md                    # Phase 0 output — decisions and rationale
|-- data-model.md                  # Phase 1 output — entities
|-- quickstart.md                  # Phase 1 output — single-PR operator recipe
|-- contracts/
|   |-- extraction-pr-contract.md      # Single-PR atomicity + 19-callsite rewrite contract
|   |-- di-slot-rename-contract.md     # 12-occurrence DI-slot rename across 5 naming layers
|   |-- breadcrumb-audit-contract.md   # SC-014 5-grep audit for pinned NOTE templates
|   `-- compliance-gate-contract.md    # pylint >=8.74, aggregate >=99.6/A+, new files A+/100
`-- checklists/
    `-- requirements.md            # Existing checklist
```

### Source Code (repository root)

```text
MistHelper.py                                # Entrypoint monolith — loses `is_debug_mode`,
                                             #   `EnvironmentUtils.is_debug_mode` wrapper,
                                             #   and `execute_with_connection_pool_management`
                                             #   + 3 `_pool_*` helpers. Gains 1 NOTE at :635
                                             #   (Action 1) + 1 NOTE at the is_debug_mode
                                             #   delete site + 1 NOTE at the
                                             #   execute_with_connection_pool_management
                                             #   delete site (Action 3). No NOTE at the
                                             #   EnvironmentUtils wrapper delete site
                                             #   (per Clarifications Q5).
tools/refactor_analyzer/                     # Analyzer package — CONSUMED AS-IS, never modified
                                             #   (FR-018 carry-forward). Action 1 uses the
                                             #   analyzer's `--skip` CLI flag if available; if
                                             #   not, the breadcrumb-only pin still satisfies
                                             #   SC-001.
tools/compliance_analyzer/                   # Compliance analyzer — used to verify A+/100 on
                                             #   the 2 new files and pylint >=8.74 aggregate.
refactor_candidates.md                       # Regenerated after this PR's merge (FR-010
                                             #   carry-forward).
data/full_repo_compliance_current.md         # Compliance baseline snapshot — must stay
                                             #   >=99.6/A+.
src/
|-- refactors/                               # DESTINATION for both new extractions
|   |-- __init__.py                          # Existing
|   |-- is_debug_mode.py                     # NEW — Action 2 target (IsDebugMode.check())
|   |-- connection_pool_executor.py          # NEW — Action 3 target
|   |                                        #   (ConnectionPoolExecutor.execute() + 3 privates)
|   `-- (many prior extractions preserved)   # Existing modules from 1010/1011 untouched
|-- export/
|   `-- site_export_utils.py                 # EDITED — DI slot rename
|                                            #   `is_debug_mode_fn` -> `check_fn` at 5 sites
|                                            #   (L32, L52, L64, L76, L337) + 1 NOTE
|                                            #   breadcrumb at the module-level slot
`-- gateway/
    |-- gateway_export_utils.py              # EDITED — 2 callsite rewrites (L48, L550) for
    |                                        #   `execute_with_connection_pool_management`
    |-- gateway_stats_exporter.py            # EDITED — 1 callsite rewrite (L32)
    `-- overrides/
        |-- _deps.py                         # EDITED — DI slot rename
        |                                    #   `connection_pool_fn` -> `execute_fn`
        |                                    #   at 4 sites (L18, L33, L41, L49) + 1 NOTE
        |                                    #   breadcrumb at the module-level slot
        `-- device_data_fetcher.py           # EDITED — DI slot rename
                                             #   `connection_pool_fn` -> `execute_fn` at :40
                                             #   (no NOTE breadcrumb — spec mandates only
                                             #   1 NOTE per DI cluster; the cluster's canonical
                                             #   NOTE lives on `_deps.py`)
```

**Structure Decision**: Single-project layout preserved from 1010/1011. Both new extractions land under `src/refactors/` as per-symbol module files, matching the established convention. Six cross-file editors (`site_export_utils.py`, `gateway_export_utils.py`, `gateway_stats_exporter.py`, `overrides/_deps.py`, `overrides/device_data_fetcher.py`, and MistHelper.py itself) participate in the atomic diff to close the extraction cleanly — no wrapper shims are left behind (FR-003).

### Edit Surface (Authoritative Manifest)

Per FR-014, FR-024, and SC-014 the PR must land exactly the following edits atomically:

| # | Category | File | Line(s) | Change |
|---|----------|------|---------|--------|
| 1 | Breadcrumb (Action 1) | `MistHelper.py` | 635 | Add NOTE explaining tqdm fallback + `GlobalImportManager` rebind pattern |
| 2 | New module (Action 2) | `src/refactors/is_debug_mode.py` | new | Create `IsDebugMode` class with `@staticmethod check()` |
| 3 | Delete (Action 2) | `MistHelper.py` | 318-320 | Remove `def is_debug_mode()` |
| 4 | Delete (Action 2) | `MistHelper.py` | 5891-5900 | Remove `EnvironmentUtils.is_debug_mode` wrapper (0 callers per Q1) |
| 5 | Callsite rewrite (Action 2) | `MistHelper.py` | 12 sites | Rewrite each `is_debug_mode()` -> `IsDebugMode.check()` |
| 6 | Breadcrumb (Action 2) | `MistHelper.py` | at delete site | Add extraction NOTE (pinned template) |
| 7 | DI rename (Action 2) | `src/export/site_export_utils.py` | 32, 52, 64, 76, 337 | `is_debug_mode_fn` -> `check_fn` (5 occurrences: slot, field, global list, LHS/RHS, kwarg) |
| 8 | DI rename (Action 2) | `MistHelper.py` | 13372 | kwarg `is_debug_mode_fn=` -> `check_fn=` |
| 9 | Breadcrumb (Action 2) | `src/export/site_export_utils.py` | at module-level slot (L32) | Add rename NOTE (pinned template — 1 NOTE per DI cluster) |
| 10 | New module (Action 3) | `src/refactors/connection_pool_executor.py` | new | Create `ConnectionPoolExecutor` class with `@staticmethod execute()` + 3 private `@staticmethod _pool_*()` helpers |
| 11 | Delete (Action 3) | `MistHelper.py` | 7503-7576 | Remove public function + 3 `_pool_*` helpers |
| 12 | Callsite rewrite (Action 3) | `MistHelper.py` | 6309, 10076, 15399, 15564 | Rewrite -> `ConnectionPoolExecutor.execute()` |
| 13 | Callsite rewrite (Action 3) | `src/gateway/gateway_export_utils.py` | 48, 550 | Rewrite -> `ConnectionPoolExecutor.execute()` |
| 14 | Callsite rewrite (Action 3) | `src/gateway/gateway_stats_exporter.py` | 32 | Rewrite -> `ConnectionPoolExecutor.execute()` |
| 15 | Breadcrumb (Action 3) | `MistHelper.py` | at delete site | Add extraction NOTE (pinned template) |
| 16 | DI rename (Action 3) | `src/gateway/overrides/_deps.py` | 18, 33, 41, 49 | `connection_pool_fn` -> `execute_fn` (4 occurrences) |
| 17 | DI rename (Action 3) | `src/gateway/overrides/device_data_fetcher.py` | 40 | `connection_pool_fn` -> `execute_fn` |
| 18 | DI rename (Action 3) | `MistHelper.py` | 15564 | kwarg `connection_pool_fn=` -> `execute_fn=` |
| 19 | Breadcrumb (Action 3) | `src/gateway/overrides/_deps.py` | at module-level slot (L18) | Add rename NOTE (pinned template — 1 NOTE per DI cluster) |

**Pinned breadcrumb templates** (FR-024, SC-014):

- Extraction/deletion: `# NOTE: <symbol> extracted to <new-callable>. See specs/1012-misthelper-refactor-hot-functions/spec.md.`
- Renamed DI slot: `# NOTE: renamed from <old-symbol>; wiring source <new-callable> at MistHelper.py:<line>.`

Note: DI rename NOTE uses the bare symbol name (`is_debug_mode`, `execute_with_connection_pool_management`) as `<old-symbol>`, not the DI slot suffix form. Exactly 1 rename NOTE per cluster (Action 2: site_export_utils.py; Action 3: _deps.py). The `EnvironmentUtils.is_debug_mode` wrapper deletion at MistHelper.py:5891 does NOT carry a breadcrumb (per Clarifications Q5). The `device_data_fetcher.py:40` and MistHelper.py kwarg sites (L13372, L15564) get their identifier renamed but do NOT carry rename NOTEs — the cluster's canonical NOTE lives on the module-level slot declaration.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 design artifacts landed:

- **I. Five-Item Rule** — Still PASS. No menu topology changed.
- **II. Class-Based Architecture** — Still PASS. Both extractions land as class-body `@staticmethod` seams (`IsDebugMode.check`, `ConnectionPoolExecutor.execute` + 3 private static helpers).
- **III. Safety-First** — Still PASS. `EnvironmentUtils.is_debug_mode` wrapper deletion validated by clarification Q1 grep audit (0 callers). No new destructive paths introduced.
- **IV. Full Deployment Pipeline** — Still PASS. FR-011 CI gate + `feedback_no_admin_bypass.md` guidance. Local pre-push Black + Ruff gate per `feedback_prepush_black_ruff.md`.
- **V. Observability & Logging** — Still PASS. Both new modules land ASCII-only; `pathlib.Path` where applicable; original `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` action-log prefixes preserved verbatim in `ConnectionPoolExecutor.execute()`.
- **VI. Inline Comments** — Still PASS + NON-NEGOTIABLE. A+/100 gate on `is_debug_mode.py` and `connection_pool_executor.py` enforces the 5-10 line cadence.
- **VII. Action Logging** — Still PASS + NON-NEGOTIABLE. `guideline_flags` resolution requirement (FR-006 carry-forward) enforces action-logging on extracted code.

**Final verdict**: All seven principles pass post-design. No Complexity Tracking entries required.

## What This Plan Does NOT Do

- Does not open, sequence, or merge the PR — that is the parent conversation's dispatch responsibility (Assumption 7 carry-forward).
- Does not modify `tools/refactor_analyzer/` (FR-018 carry-forward). Action 1's skip-pin uses the analyzer's `--skip` CLI flag if present or a source-level NOTE alone if not.
- Does not touch `SKIP_ALWAYS` symbols like `GlobalImportManager` (FR-008 carry-forward). The Action 1 NOTE at `MistHelper.py:635` documents the bootstrap dependency; it does not extract, delete, or modify the tqdm shim.
- Does not touch any other Hot-bucket symbols beyond the two targeted extractions (Actions 2 and 3).
- Does not batch a fourth action into this PR; scope is fixed at exactly the three clarification-approved actions (FR-014).
- Does not leave wrapper shims or forwarding functions (FR-003, SC-008 carry-forward).
- Does not modify external-file callers beyond the mechanical callsite rewrites and DI-slot renames (FR-019 carry-forward — the touched files are not required to reach A+/100 in this PR if they were not already there).
- Does not defer the `EnvironmentUtils.is_debug_mode` wrapper deletion to a follow-up PR; it lands in the same atomic diff as the extraction (SC-011).
