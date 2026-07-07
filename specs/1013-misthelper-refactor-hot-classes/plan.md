# Implementation Plan: MistHelper.py Refactor — Hot-Classes Serial Extraction

**Branch**: `1013-misthelper-refactor-hot-classes` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1013-misthelper-refactor-hot-classes/spec.md`
**Predecessors**: `specs/1010-misthelper-refactor-extraction/` (13 PRs merged), `specs/1011-misthelper-refactor-low-use/` (20 PRs merged), `specs/1012-misthelper-refactor-hot-functions/` (1 bounded PR merged) — all three closed with baseline `>=99.6/A+`.

## Summary

Land the fourth-pass refactor initiative: **47 serial per-PR extractions** targeting Hot-bucket classes in `MistHelper.py` whose reference sites are exclusively inside `MistHelper.py` (no `src/`, `tests/`, or other first-party callers). One class per PR. Dispatch order front-loads the 4 Category A (facade-removal) candidates as a low-risk warmup (positions 1-4), then continues with the 43 Category B (fresh-extraction) candidates in Refs-ASC / LOC-DESC order (positions 5-47) derived from the freshest `refactor_candidates.md` at each hop. This mirrors the serial workflow of 1010/1011 (one candidate per PR) and deliberately does **not** repeat the bounded-bundle pattern of 1012.

**Two action-types govern the PR shape** (per FR-003 and the 2026-07-07 collision audit):

- **Cat A — Facade removal (4 candidates, positions 1-4)**: The `MistHelper.py` class is a delegation wrapper; the real implementation already lives in `src/` at a specific path (verified by a same-name class-definition audit on 2026-07-07). The PR **deletes the facade + rewires callsites** — no new file is created. Every Cat A PR MUST record a method-parity audit in the PR description per FR-025 before the facade is deleted, comparing the facade's public surface (methods, static methods, classmethods, instance attributes) against the `src/` counterpart to prove semantic equivalence. Silent facade deletion is prohibited.
- **Cat B — Fresh extraction (43 candidates, positions 5-47)**: No `src/` collision. The PR extracts the class body to the landing package (new file created inside the noted package, or folded into an existing class body when semantically appropriate), deletes the original class body from `MistHelper.py`, and rewrites every callsite in the same commit. This is the 1010/1011 pattern.
- **Cat C — Name-clash-distinct**: 0 candidates found in the 2026-07-07 audit; category listed for completeness only.

Each extraction PR delivers, by category:

- **Cat A PR delivers**: (a) facade deletion from `MistHelper.py`; (b) every `MistHelper.py` callsite rewritten to import directly from the pre-existing `src/` module in the same commit; (c) method-parity audit output pasted in the PR description under a `Method-Parity Audit` heading (FR-025); (d) mandatory single-line NOTE breadcrumb at the facade-deletion site pointing at the pre-existing `src/` module; (e) all 15 functional CI jobs green; (f) `MistHelper.py` pylint score non-regressing against the pre-initiative baseline; (g) repo-wide aggregate compliance `>=99.6/A+`; (h) `black --check` and `ruff check` clean; (i) `python MistHelper.py --test` reporting 0 failed with exit 0. No new file is created. Zero wrapper shims. Zero re-export modules. Zero backward-compatibility aliases.
- **Cat B PR delivers**: (a) class body moved to a cohesive module in the landing package (new file, or fold into an existing class body when semantically appropriate); (b) every `MistHelper.py` callsite rewritten in the same commit; (c) original class body deleted from `MistHelper.py`; (d) mandatory single-line NOTE breadcrumb at the class-body-deletion site pointing at the newly created `src/` file (FR-007 template); (e) any analyzer `guideline_flags` on the moved class resolved in-flight (no deferral); (f) all 15 functional CI jobs green; (g) new/edited module at A+/100 compliance; (h) repo-wide aggregate compliance `>=99.6/A+`; (i) `MistHelper.py` pylint score non-regressing against the pre-initiative baseline; (j) `black --check` and `ruff check` clean; (k) `python MistHelper.py --test` reporting 0 failed with exit 0. Zero wrapper shims. Zero re-export modules. Zero backward-compatibility aliases.

Sum of the 47 candidates' LoC across both categories: ~12,150. SC-002 target: `MistHelper.py` physical LoC drops by `>=8,000` lines relative to pre-initiative baseline (headroom for class-body overhead and reasonable decomposition retention in destination modules). Note that Cat A rows contribute only a small LoC drop each (facade wrappers are typically 22-188 lines) whereas Cat B rows contribute via full class-body movement (10-759 lines each); the Cat B block therefore accounts for the bulk of the SC-002 drop.

## Technical Context

**Language/Version**: Python 3.13 (project target per Constitution v1.4.0 and the repo tooling / CI matrix)
**Primary Dependencies**: standard library only for extraction targets; existing project deps preserved (no new dependencies introduced by this initiative)
**Storage**: N/A for extraction work itself
**Testing**: `pytest` for unit/integration; the 15 functional CI jobs (matrix build, ruff, mypy, compliance analyzer, refactor analyzer smoke, integration suites) as the mergeability contract; `python MistHelper.py --test` smoke test (0 failed / exit 0) as an additional merge gate per FR-015; local pre-push Black + Ruff gate per `feedback_prepush_black_ruff.md`
**Target Platform**: Windows-first CLI; extracted modules stay platform-neutral (`pathlib.Path` everywhere, ASCII-only log literals)
**Project Type**: Single-project CLI tool with a monolithic entrypoint (`MistHelper.py`) being decomposed into `src/*` sub-packages
**Performance Goals**: No performance regression at any callsite after extraction; interactive CLI menu latency unchanged; extracted class bodies preserve their original method contracts byte-for-byte, with any in-flight decomposition (E-2) only splitting internal method bodies rather than altering call semantics
**Constraints**: Zero wrapper shims may be left in `MistHelper.py` (FR-003 carry-forward, formalized across Cat A + Cat B); every new/edited module lands at A+/100 compliance (FR-016); repo-wide baseline stays `>=99.6/A+` (FR-017); `MistHelper.py` pylint stays non-regressing against the pre-initiative baseline (FR-018); no `--admin` merge bypass as a routine unblock (per `feedback_no_admin_bypass.md` — check `mergeStateStatus: CLEAN` first); every extraction site carries the pinned NOTE breadcrumb (FR-007, SC-012); `refactor_candidates.md` is regenerated after every merged PR before the next dispatch (FR-014); pre-dispatch grep audit is mandatory for every PR (FR-013); no new SKIPPED CI conditionals introduced (FR-019); every Cat A PR carries a method-parity audit in its PR description (FR-025); Cat A candidates occupy dispatch positions 1-4 as a low-risk warmup (FR-026)
**Scale/Scope**: 47 serial PRs (one class per PR: 4 Cat A + 43 Cat B); ~12,150 LoC total addressed; SC-002 requires `MistHelper.py` shrinks by `>=8,000` physical lines; landing distribution spans 15 existing packages (see Project Structure below); `src/refactors/` receives **zero** candidates; 47 mandatory NOTE breadcrumbs (one per merged PR); at most one open PR at a time (FR-023)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.4.0 (ratified 2026-03-05). Evaluated per the seven core principles.

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule (all menu options in groups of 5, cross-category prohibited) | PASS | Extraction is a code-organization change; no menu structure is added, removed, or reordered by any of the 47 PRs. User-facing behavior is preserved exactly (FR-021). |
| II. Class-Based Architecture (functions live inside cohesive classes) | PASS + REINFORCED | Every one of the 47 candidates is already a class; the extraction lands each as a cohesive class body in the destination module per FR-004. Bare module-level function/assignment landings are prohibited. Cat A PRs preserve class-body cohesion by removing dead facades that duplicate a real class already living in `src/` — after the facade is deleted, exactly one canonical class body exists per name across the codebase. Cat B PRs move the class body intact into a new landing file (or fold into an existing package class body when the semantic fit is clear). |
| III. Safety-First Development (destructive operations gated) | PASS + REINFORCED | Extraction moves existing behavior; no new destructive operations are introduced. Pre-dispatch grep audit (FR-013) confirms zero external callers before deletion. Cat A PRs carry an additional safety gate: FR-025 method-parity verification (enumerate facade methods → confirm each is exposed with equivalent signature by the `src/` counterpart → paste audit output in PR description before deletion). Silent facade deletion is prohibited. |
| IV. Full Deployment Pipeline (15 CI jobs must pass, no --admin bypass) | PASS + REINFORCED | FR-015 codifies the CI gate. `feedback_no_admin_bypass.md` guidance applied — check `mergeStateStatus: CLEAN` before merging; do not cargo-cult `--admin`; SKIPPED conditionals are non-blocking. FR-019 additionally forbids introducing *new* SKIPPED conditionals via this initiative. |
| V. Observability & Logging (structured, ASCII-only, `safe_input`, `pathlib.Path`) | PASS + REINFORCED | Every new/edited module lands ASCII-only logs, no raw `input()` (replaced by `InputUtils.safe_input()` where applicable), `pathlib.Path` in place of `os.path`. Analyzer `guideline_flags` (`non_ascii_logs`, `raw_input_call`, `hardcoded_separator`) are resolved in-flight per FR-006 — never deferred. Cat A PRs have no new file to lint but MUST preserve the pre-existing `src/` module's compliance grade. |
| VI. Inline Comments Every 5-10 Lines (NON-NEGOTIABLE) | PASS + REINFORCED | Every new/edited module must land A+/100 per FR-016, which enforces the 5-10 line inline-comment cadence. The `missing_inline_comments` `guideline_flag` is resolved during the move per FR-006. Cat A PRs preserve the pre-existing `src/` module's cadence unchanged. |
| VII. Action Logging Before Every Non-Trivial Action (NON-NEGOTIABLE) | PASS + REINFORCED | Every extracted class body preserves its original `[LOGIN]` / `[MENU]` / `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` action-log prefixes verbatim, and any `missing_action_logging` `guideline_flag` on the moved class is resolved in-flight per FR-006. `%s` placeholder formatting used throughout. |

**Result**: All seven principles pass. Principles II and III are reinforced by the new Cat A action-type + FR-025 method-parity gate. Principles VI and VII are NON-NEGOTIABLE and are reinforced rather than at risk by the A+/100 per-file gate and the FR-006 in-flight `guideline_flags` resolution rule. No violations require Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/1013-misthelper-refactor-hot-classes/
|-- plan.md                        # This file (/speckit.plan output)
|-- spec.md                        # Feature specification (input)
|-- research.md                    # Phase 0 output — Decision blocks
|-- quickstart.md                  # Phase 1 output — mid-flight contributor recipe
`-- checklists/
    `-- requirements.md            # Existing checklist
```

No `contracts/` sub-directory. This initiative's contracts (extraction PR shape by category, NOTE breadcrumb template, method-parity audit shape, compliance gates) are already exhaustively specified in `spec.md` (FR-001 through FR-026, SC-001 through SC-017) and the `research.md` decisions. Adding a separate contracts folder would duplicate that content without adding audit value; the pinned FR-007 breadcrumb template and the FR-025 method-parity audit template are the only cross-file contracts and both live in the spec.

No `data-model.md`. The initiative moves code; it does not introduce data entities. The Key Entities section of `spec.md` is a conceptual glossary rather than a persistent-data schema; it is complete as-is in `spec.md` and does not warrant a duplicate data-model artifact.

### Source Code (repository root)

```text
MistHelper.py                                # Entrypoint monolith — loses 47 class bodies
                                             #   over 47 merged PRs (4 facade deletions +
                                             #   43 fresh extractions). Gains 47 NOTE
                                             #   breadcrumbs (one per merged PR, pinned
                                             #   FR-007 template).
                                             #   Target: >=8,000 LoC drop (SC-002).
tools/refactor_analyzer/                     # Analyzer package — CONSUMED AS-IS, never modified
                                             #   (FR-011 carry-forward from 1010/1011/1012).
tools/compliance_analyzer/                   # Compliance analyzer — used to verify A+/100 on
                                             #   every new/edited module and >=99.6/A+ aggregate.
refactor_candidates.md                       # Regenerated after every merged PR (FR-014).
                                             #   Freshest catalog is the authoritative source
                                             #   for the next dispatch (User Story 3).
data/full_repo_compliance_current.md         # Compliance baseline snapshot — must stay
                                             #   >=99.6/A+ throughout (FR-017).
data/full_repo_compliance_1013_baseline.md   # NEW — captured on first branch commit
                                             #   (Decision 7). Pinned baseline for FR-017/SC-003
                                             #   non-regression audit.
data/pylint_MistHelper_1013_baseline.txt     # NEW — captured on first branch commit
                                             #   (Decision 7). Pinned pylint baseline for
                                             #   FR-018/SC-015 non-regression audit.
src/
|-- gateway/                                 # Cat A row 1 target — pre-existing.
|   `-- template_config.py                   # Cat A: MistHelper.py::GatewayTemplateConfigManager
|                                            #   facade deleted; callsites rewired here.
|                                            #   No new file created.
|-- firmware/                                # Cat A row 2 target — pre-existing.
|   `-- firmware_manager.py                  # Cat A: MistHelper.py::FirmwareManager factory
|                                            #   facade deleted (create() + _Impl indirection
|                                            #   removed); callsites rewired to construct the
|                                            #   real class here. No new file created.
|-- site/                                    # Cat A row 3 target + Cat B destinations.
|   |-- site_config_manager.py               # Cat A: MistHelper.py::SiteConfigManager facade
|   |                                        #   deleted; callsites rewired here.
|   `-- (Cat B new files as dispatched)      # e.g. site_client_exporter.py,
|                                            #   bulk_radius_wlan_config_manager.py,
|                                            #   site_config_exporter.py, site_device_exporter.py,
|                                            #   site_anomaly_exporter.py,
|                                            #   sites_by_ap_model_exporter.py
|-- device/                                  # Cat A row 4 target + Cat B destinations.
|   |-- utility_commands.py                  # Cat A: MistHelper.py::DeviceUtilityCommands facade
|   |                                        #   deleted (35 op-subclass wrappers rewired to
|   |                                        #   direct imports here). FR-025 method-parity
|   |                                        #   audit is particularly rigorous for this row.
|   `-- (Cat B new files as dispatched)      # e.g. device_utils.py, device_reboot_manager.py,
|                                            #   arp_command_manager.py
|-- export/                                  # Cat B — largest cluster (20 candidates land here).
|   `-- (Cat B new files as dispatched)      # Accepted as flat layout for this initiative;
|                                            #   sub-partitioning explicitly deferred pending
|                                            #   noise emergence. e.g. self_export_utils.py,
|                                            #   msp_inventory_exporter.py,
|                                            #   const_definitions_exporter.py,
|                                            #   org_alarm_event_exporter.py, ...
|-- utils/                                   # Cat B — 4 candidates land here.
|   `-- (Cat B new files as dispatched)      # e.g. operation_registry.py,
|                                            #   environment_utils.py, filter_operator_engine.py
|-- reports/                                 # Cat B — 4 candidates land here.
|   `-- (Cat B new files as dispatched)      # e.g. wired_client_manufacturer_report_generator.py,
|                                            #   sfp_transceiver_data_processor.py,
|                                            #   offline_device_reporter.py,
|                                            #   global_wired_client_report_generator.py
|-- analytics/                               # Cat B — 2 candidates land here.
|   `-- (Cat B new files as dispatched)      # e.g. telemetry_emitter.py,
|                                            #   data_collection_manager.py
|-- ui/                                      # Cat B — 2 candidates land here.
|   `-- (Cat B new files as dispatched)      # e.g. interactive_display_utils.py,
|                                            #   display_utils.py
|-- org/                                     # Cat B — 2 candidates land here.
|   `-- (Cat B new files as dispatched)      # e.g. org_config_migration_manager.py,
|                                            #   org_ticket_manager.py
|-- audit/                                   # Cat B — 1 candidate lands here (audit_analysis_ops).
|-- dataclasses/                             # Cat B — 1 candidate lands here (endpoint_config).
|-- api/                                     # Cat B — 1 candidate lands here (api_data_fetcher).
|-- inventory/                               # Cat B — 1 candidate lands here (org_device_inventory_summary).
|-- ssh/                                     # Cat B — 1 candidate lands here (cli_shell_manager).
|-- input/                                   # Cat B — 1 candidate lands here (prompt_client_utils).
|-- db/                                      # Cat B — 1 candidate lands here (database_schema_utils).
|-- troubleshooting/                         # Cat B — 1 candidate lands here (troubleshoot_utils).
`-- refactors/                               # RECEIVES ZERO candidates in this initiative.
    `-- (pre-existing 1010/1011/1012 files)  # Prior extractions preserved; not extended.
```

**Structure Decision**: Single-project layout preserved from 1010/1011/1012. Every row of the Dispatch Queue is pinned to a specific landing target in `spec.md` — `src/refactors/` receives **zero** candidates in this initiative, breaking from the 1010/1011 "default landing zone" pattern in favour of per-row semantic-fit destinations. The four Cat A rows target the pre-existing `src/gateway/template_config.py`, `src/firmware/firmware_manager.py`, `src/site/site_config_manager.py`, and `src/device/utility_commands.py` — the PR only deletes the facade + rewires callsites, no file is created. The 43 Cat B rows spread across 15 existing packages: `src/export/` accepts 20 (accepted as flat for this initiative; sub-partitioning explicitly deferred pending noise emergence), `src/device/` accepts 4 Cat B + 1 Cat A, `src/utils/` accepts 4, `src/reports/` accepts 4, `src/analytics/` accepts 2, `src/ui/` accepts 2, `src/org/` accepts 2, `src/site/` accepts 2 Cat B + 1 Cat A, `src/gateway/` accepts 1 Cat A, `src/firmware/` accepts 1 Cat A, all others accept 1. No candidate is split across multiple PRs — even the seven very-large Cat B candidates (E-10: `OrgExportUtils` 653 LoC, `OrgConfigMigrationManager` 675 LoC, `ConstDefinitionsExporter` 759 LoC, `BulkRadiusWLANConfigManager` 587 LoC, `OrgTicketManager` 475 LoC, `OperationRegistry` 461 LoC, `OrgDeviceStatsExporter` 414 LoC) land as one PR each, with internal decomposition (E-2 / FR-006) folded into the same PR to satisfy the `<=25`-line-per-method rule and the aggregate score floor.

### Dispatch Queue (Authoritative)

Per FR-001, FR-023, and FR-026, the 47 candidates dispatch in a two-block order: **Cat A block first (positions 1-4)** as a low-risk warmup because the `src/` implementation is already merged and CI-proven; then **Cat B block (positions 5-47)** in Refs-ASC / LOC-DESC order derived from the freshest `refactor_candidates.md` at each hop. Within each block, ordering is Refs-ASC / LOC-DESC (same rule). The table below reflects the post-1012 catalog snapshot (2026-07-07) with the 2026-07-07 collision audit result baked in.

| # | Refs | LoC | Class | Cat | Landing target |
|---:|---:|---:|---|:-:|---|
| 1 | 6 | 56 | GatewayTemplateConfigManager | A | `src/gateway/template_config.py` |
| 2 | 8 | 22 | FirmwareManager | A | `src/firmware/firmware_manager.py` |
| 3 | 16 | 43 | SiteConfigManager | A | `src/site/site_config_manager.py` |
| 4 | 70 | 188 | DeviceUtilityCommands | A | `src/device/utility_commands.py` |
| 5 | 4 | 675 | OrgConfigMigrationManager | B | `src/org/` |
| 6 | 4 | 97 | DeviceUtils | B | `src/device/` |
| 7 | 4 | 40 | SelfExportUtils | B | `src/export/` |
| 8 | 5 | 386 | MSPInventoryExporter | B | `src/export/` |
| 9 | 5 | 214 | TelemetryEmitter | B | `src/analytics/` |
| 10 | 8 | 72 | InteractiveDisplayUtils | B | `src/ui/` |
| 11 | 8 | 70 | DisplayUtils | B | `src/ui/` |
| 12 | 8 | 66 | AuditAnalysisOps | B | `src/audit/` |
| 13 | 9 | 461 | OperationRegistry | B | `src/utils/` |
| 14 | 10 | 85 | SiteClientExporter | B | `src/export/` |
| 15 | 13 | 587 | BulkRadiusWLANConfigManager | B | `src/site/` |
| 16 | 13 | 10 | EndpointConfig | B | `src/dataclasses/` |
| 17 | 14 | 759 | ConstDefinitionsExporter | B | `src/export/` |
| 18 | 14 | 129 | OrgAlarmEventExporter | B | `src/export/` |
| 19 | 14 | 100 | SiteConfigExporter | B | `src/export/` |
| 20 | 14 | 94 | OrgAdminExporter | B | `src/export/` |
| 21 | 16 | 328 | APIDataFetcher | B | `src/api/` |
| 22 | 18 | 144 | OrgTemplateExporter | B | `src/export/` |
| 23 | 18 | 139 | GatewayHaExporter | B | `src/export/` |
| 24 | 20 | 168 | LicenseExportUtils | B | `src/export/` |
| 25 | 20 | 156 | DataCollectionManager | B | `src/analytics/` |
| 26 | 20 | 129 | WiredClientManufacturerReportGenerator | B | `src/reports/` |
| 27 | 22 | 180 | SFPTransceiverDataProcessor | B | `src/reports/` |
| 28 | 22 | 146 | SitesByAPModelExporter | B | `src/export/` |
| 29 | 22 | 69 | OrgDeviceInventorySummary | B | `src/inventory/` |
| 30 | 23 | 161 | CLIShellManager | B | `src/ssh/` |
| 31 | 24 | 168 | OrgConfigExporter | B | `src/export/` |
| 32 | 26 | 162 | OrgClientSecurityExporter | B | `src/export/` |
| 33 | 28 | 114 | EnvironmentUtils | B | `src/utils/` |
| 34 | 30 | 203 | SiteDeviceExporter | B | `src/export/` |
| 35 | 31 | 210 | PromptClientUtils | B | `src/input/` |
| 36 | 32 | 251 | GlobalWiredClientReportGenerator | B | `src/reports/` |
| 37 | 34 | 245 | GatewayTestExporter | B | `src/export/` |
| 38 | 34 | 179 | DatabaseSchemaUtils | B | `src/db/` |
| 39 | 36 | 127 | TroubleshootUtils | B | `src/troubleshooting/` |
| 40 | 37 | 110 | FilterOperatorEngine | B | `src/utils/` |
| 41 | 46 | 396 | DeviceRebootManager | B | `src/device/` |
| 42 | 46 | 289 | ARPCommandManager | B | `src/device/` |
| 43 | 54 | 341 | SiteAnomalyExporter | B | `src/export/` |
| 44 | 54 | 273 | OfflineDeviceReporter | B | `src/reports/` |
| 45 | 58 | 414 | OrgDeviceStatsExporter | B | `src/export/` |
| 46 | 66 | 475 | OrgTicketManager | B | `src/org/` |
| 47 | 128 | 653 | OrgExportUtils | B | `src/export/` |

**Reordering rule (FR-014 / FR-026 / User Story 3)**: After every merged PR, regenerate `refactor_candidates.md` and re-sort the *remaining Cat B candidates* by fresh Refs-ASC / LOC-DESC before dispatching the next PR. The Cat A block cannot shift because it only contains 4 entries and they are already correctly ordered by Refs-ASC / LOC-DESC (6/56 → 8/22 → 16/43 → 70/188). A Cat B candidate whose ref count shifts (e.g. because an earlier extraction indirectly removed some of its callers) is repositioned within the Cat B block. A candidate whose classification drops below Hot bucket is deferred out of scope per FR-020. A candidate whose grep audit surfaces a new `src/` caller is deferred per FR-013. Under no circumstances does a Cat B PR interleave into the Cat A block or vice versa.

**Pinned NOTE breadcrumb template** (FR-007, SC-012) — verbatim, one line per merged PR at the deletion site in `MistHelper.py`:

```text
# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.
```

Per-Cat variation:

- **Cat A PRs** place the breadcrumb at the **facade-deletion site**. `<new-module-path>` points at the pre-existing `src/` file that already houses the real implementation (e.g. `src/gateway/template_config.py`, `src/firmware/firmware_manager.py`, `src/site/site_config_manager.py`, `src/device/utility_commands.py`). No file is created by the Cat A PR.
- **Cat B PRs** place the breadcrumb at the **class-body-deletion site**. `<new-module-path>` points at the newly created `src/` file inside the landing package (e.g. `src/org/org_config_migration_manager.py`).

Post-merge grep audit: `grep -n "# NOTE: .* extracted to .*::.* See specs/1013-misthelper-refactor-hot-classes/spec.md." MistHelper.py` should return exactly `N` hits after `N` merged PRs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 design artifacts landed (`research.md` and this `plan.md`):

- **I. Five-Item Rule** — Still PASS. No menu topology changed by any of the 47 PRs; user-facing behavior preserved exactly per FR-021.
- **II. Class-Based Architecture** — Still PASS + REINFORCED. Every candidate is already a class; extraction lands each as a cohesive class body per FR-004. Cat A PRs actively reinforce cohesion by removing dead facades whose existence duplicated a `src/` counterpart — post-Cat-A, exactly one canonical class body exists per name across the codebase. Cat B PRs preserve cohesion by moving the class body intact into a new landing file (or fold into an existing package class body when appropriate).
- **III. Safety-First** — Still PASS + REINFORCED. Pre-dispatch grep audit (FR-013) is the pre-deletion safety check analogous to 1012's Q1 "0 callers" gate. Cat A PRs carry an additional safety gate via FR-025: enumerate facade methods → confirm each is exposed by the `src/` counterpart with equivalent signature → paste the audit output in the PR description before deletion. FR-025 explicitly calls out `DeviceUtilityCommands` (35 op-subclass wrappers at dispatch position 4) for particularly rigorous audit output. No new destructive paths introduced.
- **IV. Full Deployment Pipeline** — Still PASS + REINFORCED. FR-015 CI gate + `feedback_no_admin_bypass.md` + `feedback_prepush_black_ruff.md`. FR-019 additionally forbids introducing *new* SKIPPED conditionals via this initiative.
- **V. Observability & Logging** — Still PASS + REINFORCED. FR-006 requires in-flight resolution of `non_ascii_logs`, `raw_input_call`, and `hardcoded_separator` flags on Cat B extractions; no deferrals. Cat A PRs have no new file to lint but MUST preserve the pre-existing `src/` module's compliance grade.
- **VI. Inline Comments** — Still PASS + NON-NEGOTIABLE. A+/100 per-file gate (FR-016) enforces the 5-10 line inline-comment cadence on every new/edited Cat B module.
- **VII. Action Logging** — Still PASS + NON-NEGOTIABLE. FR-006 requires in-flight resolution of `missing_action_logging` flag on Cat B extractions; original `[LOGIN]` / `[MENU]` / `[EXECUTE]` / `[SUCCESS]` / `[FAILURE]` prefixes preserved verbatim when already present.

**FR-025 (method-parity gate) callout**: This gate is the Cat A analog to the FR-006 in-flight `guideline_flags` resolution rule. Where Cat B PRs prove correctness by moving the class body byte-for-byte (with only internal decomposition allowed), Cat A PRs prove correctness by auditing that every method the facade exposed is exposed by the `src/` counterpart with an equivalent signature. The audit output is a mandatory PR-description artifact; silent facade deletion is prohibited.

**FR-026 (Cat A-first ordering) callout**: The 4 Cat A candidates occupy dispatch positions 1-4 as an intentional risk-front-load. Cat A PRs carry lower semantic risk (the `src/` implementation is already merged and CI-proven — the PR only removes the dead facade + rewires callsites) than Cat B PRs (which move fresh code into a new landing file). Running Cat A first validates the initiative's callsite-rewrite discipline against a smaller edit surface and warms reviewer discipline against the FR-025 method-parity gate before the fresh-extraction workflow begins at position 5.

**Final verdict**: All seven principles pass post-design. No Complexity Tracking entries required.

## What This Plan Does NOT Do

- Does not open, sequence, or merge any of the 47 PRs — that is the parent conversation's dispatch responsibility (carry-forward from 1010/1011/1012 Assumption 7).
- Does not modify `tools/refactor_analyzer/` (FR-011 carry-forward). The analyzer is consumed as-is; the initiative only invokes it via its documented CLI surface.
- Does not touch any symbol in the analyzer's `SKIP_ALWAYS` bucket (`GlobalImportManager`, `tqdm` by convention per 1012) — FR-009 carry-forward, SC-008.
- Does not re-refactor any class already extracted in 1010, 1011, or 1012 — FR-010, SC-009.
- Does not touch any Hot-bucket class with a non-`MistHelper.py` caller. The 29 excluded classes remain deferred to a future initiative (post-1013) that will address multi-file rewrite discipline — FR-012, SC-009.
- Does not touch any Hot-bucket function or assignment. The initiative is Hot **classes** only; Hot functions were handled by 1012 (three targeted), Hot assignments and any remaining Hot functions remain deferred.
- Does not batch multiple classes into a single PR — FR-002, contrast with 1012's bounded-bundle pattern.
- Does not leave wrapper shims, forwarding functions, re-export modules, or backward-compatibility aliases in `MistHelper.py` — FR-003, SC-007. This applies uniformly to both Cat A and Cat B.
- Does not create new `src/` files for Cat A candidates. The real implementation already exists at the pinned landing target; the Cat A PR only removes the dead facade + rewires callsites. Only Cat B rows create new files.
- Does not defer method-parity verification for any Cat A PR. FR-025 requires the audit be recorded in the PR description under a `Method-Parity Audit` heading before facade deletion; silent facade deletion is prohibited. This applies with particular rigour to the `DeviceUtilityCommands` PR (dispatch position 4, 35 op-subclass wrappers).
- Does not interleave Cat A and Cat B rows. Cat A rows occupy dispatch positions 1-4 exclusively; Cat B rows occupy 5-47 exclusively (per FR-026). Reordering per FR-014 only shuffles remaining Cat B candidates within the Cat B block.
- Does not defer any analyzer `guideline_flag` on a moved Cat B class to a follow-up PR — FR-006, SC-011.
- Does not split any single candidate across multiple PRs, even the seven very-large Cat B candidates (E-10) — the internal decomposition per E-2 is folded into the same PR.
- Does not introduce new features, new commands, new CLI flags, or user-facing behavior changes — FR-021.
- Does not modify external-file callers of a moved class beyond what's required by the extraction itself. Files touched only for callsite rewrite are not required to reach A+/100 in the same PR *if they were not already there* — FR-022 applies only when the extracted class is folded into an existing destination package's class body.
- Does not raise the compliance baseline. The initiative preserves `>=99.6/A+` aggregate; it does not attempt to reach 100/A+.
- Does not enumerate the 29 excluded Hot-bucket classes or the future initiative that will address them; those are out of scope for this spec.
- Does not add a `contracts/` directory or `data-model.md`. The initiative's contracts are exhaustively captured in `spec.md` (FR-001-FR-026, SC-001-SC-017) and `research.md` (decisions); adding duplicate documents would not add audit value.
- Does not use `src/refactors/` as a landing target for any of the 47 rows. Every row is pinned to a domain-fitting existing package in `spec.md`.
