# Implementation Plan: MistHelper.py Refactor — Hot-Classes With `src/` Callers Serial Extraction

**Branch**: `1014-misthelper-refactor-hot-classes-with-src-callers` | **Date**: 2026-07-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md`
**Predecessors**: `specs/1010-misthelper-refactor-extraction/` (13 PRs merged), `specs/1011-misthelper-refactor-low-use/` (20 PRs merged), `specs/1012-misthelper-refactor-hot-functions/` (1 bounded PR merged), `specs/1013-misthelper-refactor-hot-classes/` (47 PRs merged) — all four closed with baseline `>=99.6/A+`.

## Summary

Land the fifth-pass refactor initiative: **24 serial per-PR extractions** targeting Hot-bucket classes in `MistHelper.py` whose reference sites include at least one caller outside `MistHelper.py` (in `src/`, primarily). One class per PR. Dispatch order is global **Refs-ASC / LOC-DESC** across BOTH categories combined (per FR-026, no Cat A warmup separation — Cat A candidates in this queue cluster at higher refs bands so front-loading them as a warmup block would push their dispatch to the tail against the FR-023 dispatch rule). This mirrors the serial workflow of 1010/1011/1013 (one candidate per PR) and deliberately does **not** repeat the bounded-bundle pattern of 1012 or the Cat A warmup ordering of 1013.

**Two action-types govern the PR shape** (per FR-003 and the 2026-07-08 catalog audit):

- **Cat A — Facade removal (6 candidates, positions 4, 12, 13, 15, 16, 20)**: The `MistHelper.py` class is a delegation wrapper; the real implementation already lives in `src/` at a specific path. The PR **deletes the facade + rewires callsites (BOTH `MistHelper.py` and, where the facade is imported from `src/`, the corresponding `src/` callers)** — no new file is created. Every Cat A PR MUST record a method-parity audit in the PR description per FR-025 before the facade is deleted, comparing the facade's public surface against the `src/` counterpart to prove semantic equivalence. Silent facade deletion is prohibited.
- **Cat E — Fresh cross-package extraction (18 candidates, all remaining positions)**: MistHelper.py holds the **real** class body; one or more `src/` modules currently reach it via `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>` lazy pattern. The PR extracts the class body to the landing target, rewires MistHelper.py callsites, AND rewires every `src/` lazy-import callsite in the **same commit** (per FR-003 Cat E + FR-005 + FR-027). Zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` remainders may survive the merge. Cat E adds a new action-type not present in 1013.
- **Cat B — MistHelper-only fresh extraction**: 0 candidates in this queue by construction (all 24 have external `src/` callers). If mid-initiative reclassification drops a candidate to MistHelper-only per FR-020 / E-12, it is deferred to a follow-up initiative rather than proceeding under Cat B here.
- **Cat C — Name-clash-distinct**: 0 candidates in the 2026-07-08 audit; category listed for completeness only.

Each extraction PR delivers, by category:

- **Cat A PR delivers**: (a) facade deletion from `MistHelper.py`; (b) every `MistHelper.py` callsite rewritten in the same commit to import directly from the pre-existing `src/` module; (c) every `src/` (or other first-party) callsite that imports the facade name from `MistHelper` — if any — rewritten in the same commit; (d) method-parity audit output pasted in the PR description under a `Method-Parity Audit` heading (FR-025); (e) mandatory single-line NOTE breadcrumb at the facade-deletion site pointing at the pre-existing `src/` module; (f) all 15 functional CI jobs green; (g) `MistHelper.py` pylint score non-regressing against the pre-initiative baseline; (h) repo-wide aggregate compliance `>=99.6/A+`; (i) `black --check` and `ruff check` clean; (j) `python MistHelper.py --test` reporting 0 failed with exit 0. No new file is created. Zero wrapper shims. Zero re-export modules. Zero backward-compatibility aliases.
- **Cat E PR delivers**: (a) class body moved to a cohesive module in the landing package (new file, or fold into an existing class body when semantically appropriate); (b) every `MistHelper.py` callsite rewritten in the same commit; (c) **every `src/` (or other first-party) lazy-import callsite rewritten in the SAME commit** — the `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>` pattern replaced with `from src.<package>.<module> import <ClassName>`; (d) original class body deleted from `MistHelper.py`; (e) mandatory single-line NOTE breadcrumb at the class-body-deletion site pointing at the newly created `src/` file (FR-007 template); (f) callsite table pasted in the PR description under a `Callsite Table` heading (FR-027) enumerating `MistHelper.py` count + exact `src/` file:line list + any `tests/` callsites; (g) import-graph health verified per FR-028 (`python -c "import <landing_module>"` succeeds without traversing `MistHelper.py`); (h) any analyzer `guideline_flags` on the moved class resolved in-flight (no deferral); (i) all 15 functional CI jobs green; (j) new/edited module at A+/100 compliance; (k) repo-wide aggregate compliance `>=99.6/A+`; (l) `MistHelper.py` pylint score non-regressing against the pre-initiative baseline; (m) `black --check` and `ruff check` clean; (n) `python MistHelper.py --test` reporting 0 failed with exit 0. Zero wrapper shims. Zero re-export modules. Zero backward-compatibility aliases. **Zero `mh.<ClassName>` lazy-import remainders** for the extracted class name.

Sum of the 24 candidates' LoC across both categories: ~3,395. SC-002 target: `MistHelper.py` physical LoC drops by `>=3,000` lines relative to pre-initiative baseline (headroom for class-body overhead and reasonable decomposition retention in destination modules). Note that Cat A rows contribute a smaller LoC drop each (facade wrappers are typically 22-145 lines) whereas Cat E rows contribute via full class-body movement (8-686 lines each); the Cat E block therefore accounts for the bulk of the SC-002 drop.

## Technical Context

**Language/Version**: Python 3.13 (project target per Constitution v1.4.0 and the repo tooling / CI matrix)
**Primary Dependencies**: standard library only for extraction targets; existing project deps preserved (no new dependencies introduced by this initiative)
**Storage**: N/A for extraction work itself
**Testing**: `pytest` for unit/integration; the 15 functional CI jobs (matrix build, ruff, mypy, compliance analyzer, refactor analyzer smoke, integration suites) as the mergeability contract; `python MistHelper.py --test` smoke test (0 failed / exit 0) as an additional merge gate per FR-015; local pre-push Black + Ruff gate per `feedback_prepush_black_ruff.md`; **import-graph health check** per FR-028 for Cat E PRs (`python -c "import <landing_module>"` succeeds without touching `MistHelper.py`, verifiable via `sys.modules` inspection)
**Target Platform**: Windows-first CLI; extracted modules stay platform-neutral (`pathlib.Path` everywhere, ASCII-only log literals)
**Project Type**: Single-project CLI tool with a monolithic entrypoint (`MistHelper.py`) being decomposed into `src/*` sub-packages
**Performance Goals**: No performance regression at any callsite after extraction; interactive CLI menu latency unchanged; extracted class bodies preserve their original method contracts byte-for-byte, with any in-flight decomposition (E-2) only splitting internal method bodies rather than altering call semantics
**Constraints**: Zero wrapper shims may be left in `MistHelper.py` (FR-003 carry-forward, extended for Cat E dual-side rewrite); zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` remainders for any Cat E-extracted class name (FR-005 / SC-009); every new/edited module lands at A+/100 compliance (FR-016); repo-wide baseline stays `>=99.6/A+` (FR-017); `MistHelper.py` pylint stays non-regressing against the pre-initiative baseline (FR-018); no `--admin` merge bypass as a routine unblock (per `feedback_no_admin_bypass.md` — check `mergeStateStatus: CLEAN` first); every extraction site carries the pinned NOTE breadcrumb (FR-007, SC-012); `refactor_candidates.md` is regenerated after every merged PR before the next dispatch (FR-014); pre-dispatch grep audit is mandatory for every PR (FR-013); no new SKIPPED CI conditionals introduced (FR-019); every Cat A PR carries a method-parity audit in its PR description (FR-025); every Cat E PR carries a callsite table in its PR description (FR-027) and verifies import-graph health (FR-028); global Refs-ASC / LOC-DESC ordering across BOTH categories combined per FR-026 (no Cat A warmup separation)
**Scale/Scope**: 24 serial PRs (one class per PR: 6 Cat A + 18 Cat E); ~3,395 LoC total addressed; SC-002 requires `MistHelper.py` shrinks by `>=3,000` physical lines; landing distribution spans 15 packages (see Project Structure below); `src/refactors/` receives **zero** candidates; 24 mandatory NOTE breadcrumbs (one per merged PR); at most one open PR at a time (FR-023)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.4.0 (ratified 2026-03-05). Evaluated per the seven core principles.

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule (all menu options in groups of 5, cross-category prohibited) | PASS | Extraction is a code-organization change; no menu structure is added, removed, or reordered by any of the 24 PRs. User-facing behavior is preserved exactly (FR-021). |
| II. Class-Based Architecture (functions live inside cohesive classes) | PASS + REINFORCED | Every one of the 24 candidates is already a class; the extraction lands each as a cohesive class body in the destination module per FR-004. Bare module-level function/assignment landings are prohibited. Cat A PRs preserve class-body cohesion by removing dead facades that duplicate a real class already living in `src/` — after the facade is deleted, exactly one canonical class body exists per name across the codebase. Cat E PRs move the real class body intact into a new landing file (or fold into an existing package class body when the semantic fit is clear) AND collapse the `mh.<ClassName>` lazy-import pattern to a direct import, eliminating the interim circular-import workaround. |
| III. Safety-First Development (destructive operations gated) | PASS + REINFORCED | Extraction moves existing behavior; no new destructive operations are introduced. Pre-dispatch grep audit (FR-013) confirms the exact `MistHelper.py` + `src/` + `tests/` callsite set before deletion. Cat A PRs carry an additional safety gate: FR-025 method-parity verification (enumerate facade methods -> confirm each is exposed with equivalent signature by the `src/` counterpart -> paste audit output in PR description before deletion). Cat E PRs carry two additional safety gates: FR-027 mandatory callsite table (proves every `mh.<ClassName>` remainder is rewritten) and FR-028 import-graph health verification (proves the landing module doesn't re-introduce the very circular import the lazy pattern was working around). Silent facade deletion and silent Cat E extraction are both prohibited. |
| IV. Full Deployment Pipeline (15 CI jobs must pass, no --admin bypass) | PASS + REINFORCED | FR-015 codifies the CI gate. `feedback_no_admin_bypass.md` guidance applied — check `mergeStateStatus: CLEAN` before merging; do not cargo-cult `--admin`; SKIPPED conditionals are non-blocking. FR-019 additionally forbids introducing *new* SKIPPED conditionals via this initiative. |
| V. Observability & Logging (structured, ASCII-only, `safe_input`, `pathlib.Path`) | PASS + REINFORCED | Every new/edited module lands ASCII-only logs, no raw `input()` (replaced by `InputUtils.safe_input()` where applicable), `pathlib.Path` in place of `os.path`. Analyzer `guideline_flags` (`non_ascii_logs`, `raw_input_call`, `hardcoded_separator`) are resolved in-flight per FR-006 — never deferred. Cat A PRs have no new file to lint but MUST preserve the pre-existing `src/` module's compliance grade. |
| VI. Inline Comments Every 5-10 Lines (NON-NEGOTIABLE) | PASS + REINFORCED | Every new/edited module must land A+/100 per FR-016, which enforces the 5-10 line inline-comment cadence. The `missing_inline_comments` `guideline_flag` is resolved during the move per FR-006. Cat A PRs preserve the pre-existing `src/` module's cadence unchanged. |
| VII. Action Logging Before Every Non-Trivial Action (NON-NEGOTIABLE) | PASS + REINFORCED | Every extracted class body preserves its original `[LOGIN]` / `[MENU]` / `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` action-log prefixes verbatim, and any `missing_action_logging` `guideline_flag` on the moved class is resolved in-flight per FR-006. `%s` placeholder formatting used throughout. |

**Result**: All seven principles pass. Principles II and III are reinforced by the new Cat E action-type + the FR-027 callsite-table gate + the FR-028 import-graph health gate. Principles VI and VII are NON-NEGOTIABLE and are reinforced rather than at risk by the A+/100 per-file gate and the FR-006 in-flight `guideline_flags` resolution rule. No violations require Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/1014-misthelper-refactor-hot-classes-with-src-callers/
|-- plan.md                        # This file (/speckit.plan output)
|-- spec.md                        # Feature specification (input)
`-- checklists/                    # Optional per-run analyzer checklists as needed
```

No `contracts/` sub-directory. This initiative's contracts (extraction PR shape by category, NOTE breadcrumb template, method-parity audit shape, callsite-table shape, import-graph-health shape, compliance gates) are already exhaustively specified in `spec.md` (FR-001 through FR-030, SC-001 through SC-020). Adding a separate contracts folder would duplicate that content without adding audit value; the pinned FR-007 breadcrumb template, the FR-025 method-parity audit template, and the FR-027 callsite-table template are the only cross-file contracts and all live in the spec.

No `data-model.md`. The initiative moves code; it does not introduce data entities. The Key Entities section of `spec.md` is a conceptual glossary rather than a persistent-data schema; it is complete as-is in `spec.md` and does not warrant a duplicate data-model artifact.

No `research.md` and no `quickstart.md`. Prior initiatives 1010/1011/1013 gathered rationale-heavy decisions into `research.md`; this initiative's rationale is compact (Cat A + Cat E workflow is a natural extension of the 1013 Cat A + Cat B workflow) and lives inline in this plan (Summary + Technical Context + Constitution Check). A `quickstart.md` mid-flight recipe is unnecessary because contributors are following the 1013 workflow verbatim except for the additional Cat E dual-side atomic rewrite step, which is fully specified in FR-003 Cat E + FR-005 + FR-027 + FR-028.

### Source Code (repository root)

```text
MistHelper.py                                # Entrypoint monolith — loses 24 class bodies
                                             #   over 24 merged PRs (6 facade deletions +
                                             #   18 fresh cross-package extractions).
                                             #   Gains 24 NOTE breadcrumbs (one per merged
                                             #   PR, pinned FR-007 template).
                                             #   Target: >=3,000 LoC drop (SC-002).
tools/refactor_analyzer/                     # Analyzer package — CONSUMED AS-IS, never modified
                                             #   (FR-011 carry-forward from 1010/1011/1012/1013).
tools/compliance_analyzer/                   # Compliance analyzer — used to verify A+/100 on
                                             #   every new/edited module and >=99.6/A+ aggregate.
refactor_candidates.md                       # Regenerated after every merged PR (FR-014).
                                             #   Freshest catalog is the authoritative source
                                             #   for the next dispatch (User Story 3).
                                             #   LOCAL-ONLY artifact — never committed.
data/full_repo_compliance_current.md         # Compliance baseline snapshot — must stay
                                             #   >=99.6/A+ throughout (FR-017).
data/full_repo_compliance_1014_baseline.md   # NEW — captured on first branch commit.
                                             #   Pinned baseline for FR-017/SC-003
                                             #   non-regression audit.
data/pylint_MistHelper_1014_baseline.txt     # NEW — captured on first branch commit.
                                             #   Pinned pylint baseline for FR-018/SC-015
                                             #   non-regression audit.
src/
|-- ssh/                                     # Position 1 (Cat E) + position 3 (Cat E) targets;
|   |                                        #   position 15 (Cat A) target.
|   |-- batch/
|   |   |-- execution_config.py              # Cat E position 1: SSHExecutionConfig (@dataclass,
|   |   |                                    #   5 refs / 8 LoC). New file.
|   |   `-- connection_config.py             # Cat E position 3: SSHConnectionConfig (@dataclass,
|   |                                        #   6 refs / 9 LoC). New file.
|   `-- ssh_runner_manager.py                # Cat A position 15: MistHelper.py::SSHRunnerManager
|                                            #   facade deleted; callsites rewired here.
|                                            #   No new file created.
|-- firmware/                                # Positions 2 (Cat E fold-in) + 7 (Cat E fold-in).
|   |-- site_auto_upgrade.py                 # Cat E position 2: SiteAutoUpgradeConfigurator
|   |                                        #   folded in (6 refs / 22 LoC). Existing file.
|   `-- org_ap_upgrader.py                   # Cat E position 7: OrgLevelAPFirmwareUpgrader
|                                            #   folded in (33 refs / 79 LoC). Existing file.
|-- network/                                 # Position 4 (Cat A) target.
|   `-- routing_utils.py                     # Cat A position 4: MistHelper.py::RoutingUtils
|                                            #   facade deleted; callsites rewired here.
|                                            #   No new file created.
|-- validation/                              # Position 5 (Cat E) target.
|   `-- validation_utils.py                  # Cat E position 5: ValidationUtils (15 refs /
|                                            #   90 LoC). New file.
|-- time/                                    # Position 6 (Cat E) target.
|   `-- time_utils.py                        # Cat E position 6: TimeUtils (27 refs /
|                                            #   29 LoC). New file.
|-- api/                                     # Positions 8 (Cat E) + 10 (Cat E) targets.
|   |-- api_fetch_utils.py                   # Cat E position 8: APIFetchUtils (34 refs /
|   |                                        #   221 LoC). New file.
|   `-- api_core_fetch_utils.py              # Cat E position 10: APICoreFetchUtils (43 refs /
|                                            #   47 LoC). New file.
|-- export/                                  # Positions 9 (Cat E) + 16 (Cat A) + 19 (Cat E) +
|   |                                        #   23 (Cat E) targets — largest cluster (5 rows).
|   |-- org_site_exporter.py                 # Cat E position 9: OrgSiteExporter (43 refs /
|   |                                        #   112 LoC). New file.
|   |-- site_export_utils.py                 # Cat A position 16: MistHelper.py::SiteExportUtils
|   |                                        #   facade deleted; callsites rewired here.
|   |                                        #   No new file created.
|   |                                        #   FR-025 method-parity audit rigorous
|   |                                        #   (86 refs, delegates many static/class methods).
|   |-- org_inventory_exporter.py            # Cat E position 19: OrgInventoryExporter
|   |                                        #   (104 refs / 686 LoC — largest LoC in queue).
|   |                                        #   New file. Substantial internal decomposition.
|   `-- data_exporter.py                     # Cat E position 23: DataExporter (168 refs /
|                                            #   345 LoC). New file. Reclassified E from A
|                                            #   during scoping — real class body with
|                                            #   _router/_router_initialized/_last_snapshot_times
|                                            #   state, not a delegation wrapper.
|-- analytics/                               # Position 11 (Cat E) target.
|   `-- insight_metrics_utils.py             # Cat E position 11: InsightMetricsUtils (51 refs /
|                                            #   328 LoC). New file. Significant decomposition.
|-- gateway/                                 # Positions 12 (Cat A) + 13 (Cat A) targets.
|   |-- gateway_stats_exporter.py            # Cat A position 12: MistHelper.py::GatewayStatsExporter
|   |                                        #   facade deleted; callsites rewired here.
|   |                                        #   No new file created.
|   `-- gateway_export_utils.py              # Cat A position 13: MistHelper.py::GatewayExportUtils
|                                            #   facade deleted; callsites rewired here.
|                                            #   No new file created.
|-- cache/                                   # Position 14 (Cat E) target.
|   `-- cache_utils.py                       # Cat E position 14: CacheUtils (81 refs /
|                                            #   264 LoC). New file. Substantial decomposition.
|-- utils/                                   # Position 17 (Cat E) target.
|   `-- file_path_utils.py                   # Cat E position 17: FilePathUtils (86 refs /
|                                            #   46 LoC). New file.
|-- ui/                                      # Positions 18 (Cat E) + 24 (Cat E) targets.
|   |-- prompt_utils.py                      # Cat E position 18: PromptUtils (90 refs /
|   |                                        #   441 LoC). New file. Substantial decomposition.
|   `-- input_utils.py                       # Cat E position 24: InputUtils (229 refs /
|                                            #   74 LoC). New file — the highest-refs candidate
|                                            #   in the queue, deliberately at tail to defer
|                                            #   until dual-side workflow is well-exercised.
|-- device/                                  # Position 20 (Cat A) target.
|   `-- virtual_chassis.py                   # Cat A position 20: MistHelper.py::VirtualChassisManager
|                                            #   facade deleted; callsites rewired here.
|                                            #   No new file created.
|-- data/                                    # Position 21 (Cat E) target.
|   `-- data_processing_utils.py             # Cat E position 21: DataProcessingUtils
|                                            #   (125 refs / 158 LoC). New file.
|-- config/                                  # Position 22 (Cat E) target.
|   `-- config_utils.py                      # Cat E position 22: ConfigUtils (146 refs /
|                                            #   70 LoC). New file.
`-- refactors/                               # RECEIVES ZERO candidates in this initiative.
    `-- (pre-existing 1010/1011/1012/1013 files) # Prior extractions preserved; not extended.
```

**Structure Decision**: Single-project layout preserved from 1010/1011/1012/1013. Every row of the Dispatch Queue is pinned to a specific landing target in `spec.md`, all advisory per FR-029 (the PR may override at dispatch time if a closer semantic fit exists) — `src/refactors/` receives **zero** candidates in this initiative, continuing the 1013 practice of per-row semantic-fit destinations. The six Cat A rows target the pre-existing `src/network/routing_utils.py`, `src/gateway/gateway_stats_exporter.py`, `src/gateway/gateway_export_utils.py`, `src/ssh/ssh_runner_manager.py`, `src/export/site_export_utils.py`, and `src/device/virtual_chassis.py` — the PR only deletes the facade + rewires callsites (both `MistHelper.py` and, where applicable, `src/`), no file is created. The 18 Cat E rows spread across 15 existing/new packages: `src/export/` accepts 3 Cat E + 1 Cat A = 4 total (largest cluster), `src/ssh/` accepts 2 Cat E (batch subpackage) + 1 Cat A = 3 total, `src/api/` accepts 2 Cat E, `src/firmware/` accepts 2 Cat E fold-ins, `src/gateway/` accepts 2 Cat A, `src/ui/` accepts 2 Cat E, all others accept 1. No candidate is split across multiple PRs — even the six very-large Cat E candidates (E-10: `OrgInventoryExporter` 686 LoC, `PromptUtils` 441 LoC, `DataExporter` 345 LoC, `InsightMetricsUtils` 328 LoC, `CacheUtils` 264 LoC, `APIFetchUtils` 221 LoC) land as one PR each, with internal decomposition (E-2 / FR-006) folded into the same PR to satisfy the `<=25`-line-per-method rule and the aggregate score floor.

### Dispatch Queue (Authoritative)

Per FR-001, FR-023, and FR-026, the 24 candidates dispatch in **global Refs-ASC / LOC-DESC order across BOTH categories combined** — Cat A and Cat E interleave freely. This departs from the 1013 practice of front-loading Cat A as a warmup block because Cat A candidates in this queue cluster at higher refs bands (12, 52, 78, 82, 86, 104) and would push their dispatch to the tail against the FR-023 dispatch rule. A strict global Refs-ASC ordering better front-loads small-blast-radius extractions regardless of category, using the three smallest Cat E candidates (SSHExecutionConfig, SiteAutoUpgradeConfigurator, SSHConnectionConfig — all `@dataclass` or near-`@dataclass` at 8-22 LoC) as the queue-head validation of the Cat E dual-side rewrite workflow at minimum blast radius. Within each refs-band, ties break by LOC descending (bigger LOC lands earlier at same refs). The table below reflects the post-1013 catalog snapshot (2026-07-08 regenerated from `origin/main` at 2aacb20).

| # | Refs | LOC | Class | Cat | Landing target |
|---:|---:|---:|---|:-:|---|
| 1 | 5 | 8 | SSHExecutionConfig | E | `src/ssh/batch/execution_config.py` |
| 2 | 6 | 22 | SiteAutoUpgradeConfigurator | E | `src/firmware/site_auto_upgrade.py` (fold-in) |
| 3 | 6 | 9 | SSHConnectionConfig | E | `src/ssh/batch/connection_config.py` |
| 4 | 12 | 22 | RoutingUtils | A | `src/network/routing_utils.py` |
| 5 | 15 | 90 | ValidationUtils | E | `src/validation/validation_utils.py` |
| 6 | 27 | 29 | TimeUtils | E | `src/time/time_utils.py` |
| 7 | 33 | 79 | OrgLevelAPFirmwareUpgrader | E | `src/firmware/org_ap_upgrader.py` (fold-in) |
| 8 | 34 | 221 | APIFetchUtils | E | `src/api/api_fetch_utils.py` |
| 9 | 43 | 112 | OrgSiteExporter | E | `src/export/org_site_exporter.py` |
| 10 | 43 | 47 | APICoreFetchUtils | E | `src/api/api_core_fetch_utils.py` |
| 11 | 51 | 328 | InsightMetricsUtils | E | `src/analytics/insight_metrics_utils.py` |
| 12 | 52 | 28 | GatewayStatsExporter | A | `src/gateway/gateway_stats_exporter.py` |
| 13 | 78 | 98 | GatewayExportUtils | A | `src/gateway/gateway_export_utils.py` |
| 14 | 81 | 264 | CacheUtils | E | `src/cache/cache_utils.py` |
| 15 | 82 | 26 | SSHRunnerManager | A | `src/ssh/ssh_runner_manager.py` |
| 16 | 86 | 145 | SiteExportUtils | A | `src/export/site_export_utils.py` |
| 17 | 86 | 46 | FilePathUtils | E | `src/utils/file_path_utils.py` |
| 18 | 90 | 441 | PromptUtils | E | `src/ui/prompt_utils.py` |
| 19 | 104 | 686 | OrgInventoryExporter | E | `src/export/org_inventory_exporter.py` |
| 20 | 104 | 78 | VirtualChassisManager | A | `src/device/virtual_chassis.py` |
| 21 | 125 | 158 | DataProcessingUtils | E | `src/data/data_processing_utils.py` |
| 22 | 146 | 70 | ConfigUtils | E | `src/config/config_utils.py` |
| 23 | 168 | 345 | DataExporter | E | `src/export/data_exporter.py` |
| 24 | 229 | 74 | InputUtils | E | `src/ui/input_utils.py` |

**Reordering rule (FR-014 / FR-026 / User Story 3)**: After every merged PR, regenerate `refactor_candidates.md` and re-sort the *remaining candidates* by fresh Refs-ASC / LOC-DESC before dispatching the next PR. Unlike 1013, this initiative does NOT partition into Cat A / Cat E blocks — the fresh sort is global across all remaining candidates. A candidate whose ref count shifts (e.g. because an earlier extraction indirectly removed some of its callers) is repositioned in the global order. A candidate whose classification drops below Hot bucket is deferred out of scope per FR-020. A Cat A candidate whose `src/` callers add a new `mh.<facade-class-name>` import reclassifies to Cat E per E-12; a Cat E candidate whose `src/` callers are refactored away by an unrelated commit reclassifies to MistHelper-only and is deferred to a follow-up initiative per FR-020.

**Pinned NOTE breadcrumb template** (FR-007, SC-012) — verbatim, one line per merged PR at the deletion site in `MistHelper.py`:

```text
# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md.
```

Per-Cat variation:

- **Cat A PRs** place the breadcrumb at the **facade-deletion site**. `<new-module-path>` points at the pre-existing `src/` file that already houses the real implementation (e.g. `src/network/routing_utils.py`, `src/gateway/gateway_stats_exporter.py`, `src/ssh/ssh_runner_manager.py`, `src/export/site_export_utils.py`, `src/device/virtual_chassis.py`, `src/gateway/gateway_export_utils.py`). No file is created by the Cat A PR.
- **Cat E PRs** place the breadcrumb at the **class-body-deletion site**. `<new-module-path>` points at the newly created `src/` file inside the landing package (e.g. `src/ssh/batch/execution_config.py`, `src/ui/input_utils.py`).

Post-merge grep audit: `grep -n "# NOTE: .* extracted to .*::.* See specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md." MistHelper.py` should return exactly `N` hits after `N` merged PRs.

**Pinned Callsite Table template** (FR-027, SC-018) — every Cat E PR description contains this table under a `Callsite Table` heading:

```text
### Callsite Table

| Kind | File | Line | Snippet before | Snippet after |
|---|---|---:|---|---|
| MistHelper.py | MistHelper.py | <line> | `<ClassName>(...)` or `self.<attr> = ...` | `<new-import>.<ClassName>(...)` |
| src/ (lazy import) | src/<path>/<file>.py | <line> | `mh = importlib.import_module("MistHelper"); mh.<ClassName>(...)` | `from src.<pkg>.<mod> import <ClassName>; <ClassName>(...)` |
| tests/ | tests/<file>.py | <line> | ... | ... |

Total MistHelper.py callsites rewritten: <M>
Total src/ callsites rewritten: <N>
Total tests/ callsites rewritten: <T>
```

**Pinned Import-Graph-Health check** (FR-028, SC-019) — every Cat E PR description includes:

```text
### Import-Graph Health

```bash
python -c "import sys; import <landing_module>; assert 'MistHelper' not in sys.modules, 'landing module traversed MistHelper.py'; print('OK')"
```
Result: OK
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 design artifacts landed (this `plan.md`):

- **I. Five-Item Rule** — Still PASS. No menu topology changed by any of the 24 PRs; user-facing behavior preserved exactly per FR-021.
- **II. Class-Based Architecture** — Still PASS + REINFORCED. Every candidate is already a class; extraction lands each as a cohesive class body per FR-004. Cat A PRs actively reinforce cohesion by removing dead facades whose existence duplicated a `src/` counterpart — post-Cat-A, exactly one canonical class body exists per name across the codebase. Cat E PRs preserve cohesion by moving the class body intact into a new landing file (or fold into an existing package class body when appropriate) AND collapse the `mh.<ClassName>` lazy-import escape hatch into a direct import, eliminating an interim architectural workaround.
- **III. Safety-First** — Still PASS + REINFORCED. Pre-dispatch grep audit (FR-013) is the pre-deletion safety check analogous to 1013's / 1012's Q1 "0 callers" gate, extended to enumerate both `MistHelper.py` and `src/` callsites. Cat A PRs carry an additional safety gate via FR-025: enumerate facade methods -> confirm each is exposed by the `src/` counterpart with equivalent signature -> paste the audit output in the PR description before deletion. Cat E PRs carry two additional safety gates: FR-027 (callsite table proves every `mh.<ClassName>` remainder is rewritten in the same commit) and FR-028 (import-graph health verification proves the landing module doesn't re-introduce the very circular import the lazy pattern was working around). No new destructive paths introduced.
- **IV. Full Deployment Pipeline** — Still PASS + REINFORCED. FR-015 CI gate + `feedback_no_admin_bypass.md` + `feedback_prepush_black_ruff.md`. FR-019 additionally forbids introducing *new* SKIPPED conditionals via this initiative.
- **V. Observability & Logging** — Still PASS + REINFORCED. FR-006 requires in-flight resolution of `non_ascii_logs`, `raw_input_call`, and `hardcoded_separator` flags on Cat E extractions; no deferrals. Cat A PRs have no new file to lint but MUST preserve the pre-existing `src/` module's compliance grade.
- **VI. Inline Comments** — Still PASS + NON-NEGOTIABLE. A+/100 per-file gate (FR-016) enforces the 5-10 line inline-comment cadence on every new/edited Cat E module.
- **VII. Action Logging** — Still PASS + NON-NEGOTIABLE. FR-006 requires in-flight resolution of `missing_action_logging` flag on Cat E extractions; original `[LOGIN]` / `[MENU]` / `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` prefixes preserved verbatim when already present.

**FR-025 (method-parity gate) callout**: This gate is the Cat A analog to the FR-006 in-flight `guideline_flags` resolution rule. Where Cat E PRs prove correctness by moving the class body byte-for-byte (with only internal decomposition allowed) AND by pasting the FR-027 callsite table demonstrating full dual-side rewire, Cat A PRs prove correctness by auditing that every method the facade exposed is exposed by the `src/` counterpart with an equivalent signature. The audit output is a mandatory PR-description artifact; silent facade deletion is prohibited. The highest-fanout Cat A candidate is `SiteExportUtils` (position 16, 86 refs) which the audit script confirms delegates a large number of static methods — its dispatch PR MUST enumerate every static/classmethod exposed by the facade in the parity table.

**FR-026 (global ordering, no Cat A warmup) callout**: The 6 Cat A candidates in this queue cluster at higher refs bands (12, 52, 78, 82, 86, 104) — front-loading them as a warmup block (as 1013 did) would push their dispatch to positions 1-6 against the FR-023 dispatch rule that requires processing candidates in refs-ascending order for smallest-blast-radius-first. Global Refs-ASC / LOC-DESC ordering across both categories better front-loads small-blast-radius extractions regardless of category. The three smallest Cat E candidates cluster at the queue head — `SSHExecutionConfig` (5r/8L, position 1), `SiteAutoUpgradeConfigurator` (6r/22L, position 2), `SSHConnectionConfig` (6r/9L, position 3) — two of which are `@dataclass` bodies with typically empty `guideline_flags` — deliberately chosen at the queue head to validate the Cat E dual-side callsite-rewrite workflow at minimum blast radius before the higher-risk larger-LoC extractions begin.

**FR-027 (Cat E callsite table) callout**: Cat E extractions are inseparable across two sides — MistHelper.py and every `src/` lazy importer. The callsite table is the mandatory PR-description artifact that lets a reviewer verify the atomic dual-side rewire in one glance and lets a post-merge auditor grep-verify that zero `mh.<ClassName>` remainders survive. Silent Cat E extraction without the callsite table is prohibited.

**FR-028 (Cat E import-graph health) callout**: The `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>` pattern that Cat E PRs eliminate exists in `src/` today *specifically to avoid* the circular import that would occur if a `src/` module did `from MistHelper import <ClassName>` at module-load time. When the class body moves to a fresh landing target, that circular concern may re-emerge if the new landing module imports symbols still living in `MistHelper.py` (e.g. globals such as `apisession`). The import-graph-health check proves the landing module doesn't re-introduce the circular import — silent regression to a `mh.<name>` lazy import in the new landing module is prohibited (FR-028). If a genuine cycle remains, the PR may inject a `configure_*_dependencies()` DI surface (a pattern already used elsewhere in `src/`) but MUST NOT leave a lazy `mh.<name>` import.

**Final verdict**: All seven principles pass post-design. No Complexity Tracking entries required.

## What This Plan Does NOT Do

- Does not open, sequence, or merge any of the 24 PRs — that is the parent conversation's dispatch responsibility (carry-forward from 1010/1011/1012/1013 Assumption 7).
- Does not modify `tools/refactor_analyzer/` (FR-011 carry-forward). The analyzer is consumed as-is; the initiative only invokes it via its documented CLI surface.
- Does not touch any symbol in the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, `tqdm` by convention per 1012) — FR-009 carry-forward, SC-008.
- Does not re-refactor any class already extracted in 1010, 1011, 1012, or 1013 — FR-010.
- Does not touch any Hot-bucket class without a `src/` external caller — the 12 residual MistHelper-only Hot-bucket classes recorded in `spec.md` "Out of Scope" remain deferred to a follow-up initiative (`1015+`) — FR-012, FR-030.
- Does not touch any Hot-bucket function or assignment. The initiative is Hot **classes** only; Hot functions were handled by 1012 (three targeted), Hot assignments and any remaining Hot functions remain deferred.
- Does not batch multiple classes into a single PR — FR-002, contrast with 1012's bounded-bundle pattern.
- Does not leave wrapper shims, forwarding functions, re-export modules, or backward-compatibility aliases in `MistHelper.py` — FR-003, SC-007. This applies uniformly to both Cat A and Cat E.
- Does not create new `src/` files for Cat A candidates. The real implementation already exists at the pinned landing target; the Cat A PR only removes the dead facade + rewires callsites (both `MistHelper.py` and, where applicable, `src/`). Only Cat E rows create new files (or fold into existing files).
- Does not defer method-parity verification for any Cat A PR. FR-025 requires the audit be recorded in the PR description under a `Method-Parity Audit` heading before facade deletion; silent facade deletion is prohibited. This applies with particular rigor to the `SiteExportUtils` PR (dispatch position 16, 86 refs, many delegating static methods).
- Does not defer callsite-table publication for any Cat E PR. FR-027 requires the table be recorded in the PR description under a `Callsite Table` heading in the same PR; silent Cat E extraction is prohibited.
- Does not defer import-graph-health verification for any Cat E PR. FR-028 requires the `python -c "import <landing_module>"` check succeed without traversing `MistHelper.py` in the same PR; if a genuine cycle remains, a `configure_*_dependencies()` DI surface may be introduced but a `mh.<name>` lazy import may NOT survive in the new landing module.
- Does not partition Cat A and Cat E into separate dispatch blocks. Both categories interleave freely under global Refs-ASC / LOC-DESC ordering per FR-026, unlike 1013's front-loaded Cat A warmup block. Reordering per FR-014 shuffles remaining candidates in a single global order — Cat A and Cat E share the same queue.
- Does not defer any analyzer `guideline_flag` on a moved Cat E class to a follow-up PR — FR-006, SC-011.
- Does not split any single candidate across multiple PRs, even the six very-large Cat E candidates (E-10) — the internal decomposition per E-2 is folded into the same PR.
- Does not introduce new features, new commands, new CLI flags, or user-facing behavior changes — FR-021.
- Does not modify external-file callers of a moved class beyond what's required by the extraction itself. Files touched only for callsite rewrite are not required to reach A+/100 in the same PR *if they were not already there* — FR-022 applies only when the extracted class is folded into an existing destination package's class body.
- Does not raise the compliance baseline. The initiative preserves `>=99.6/A+` aggregate; it does not attempt to reach 100/A+.
- Does not enumerate the follow-up initiative that will address the 12 residual MistHelper-only Hot-bucket classes; that follow-up (`1015+`) is out of scope for this spec — FR-030.
- Does not add a `contracts/` directory, `data-model.md`, `research.md`, or `quickstart.md`. The initiative's contracts are exhaustively captured in `spec.md` (FR-001-FR-030, SC-001-SC-020); adding duplicate documents would not add audit value.
- Does not use `src/refactors/` as a landing target for any of the 24 rows. Every row is pinned to a domain-fitting existing or new package in `spec.md`, all advisory per FR-029.
- Does not commit `refactor_candidates.md` to the repository. The catalog is a LOCAL-ONLY artifact regenerated after every merged PR; the branch state must NOT include it.
