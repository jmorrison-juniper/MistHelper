# Tasks: MistHelper Hot-Classes Refactor (Classes With `src/` Callers)

**Feature Directory**: `specs/1014-misthelper-refactor-hot-classes-with-src-callers/`
**Design docs consumed**: `spec.md` (24-row Dispatch Queue, FR-001..FR-030, SC-001..SC-020), `plan.md` (Cat A/E action-type split, pinned landing targets across 15 packages, Constitution Check PASS).

**Action-type legend** (from spec.md § Dispatch Queue):
- **Cat A — Facade removal**: delete delegation wrapper from `MistHelper.py`; the real `src/` implementation already exists. Rewire every `MistHelper.py` callsite AND — where the facade is also imported from `src/` — every `src/` caller to reference the real `src/` class directly. MUST run method-parity audit (FR-025) before deletion.
- **Cat E — Fresh cross-package extraction**: MistHelper.py holds the real class body while one or more `src/` modules currently reach it via `mh = importlib.import_module("MistHelper")` + `mh.<ClassName>`. Create the landing module (or fold into an existing class body), delete the class body from MistHelper.py, and rewire BOTH sides atomically in one commit (FR-003 Cat E + FR-005 + FR-027 + FR-028). MUST record callsite table (FR-027) and verify import-graph health (FR-028).

**Dispatch ordering** (FR-026, FR-023): the 24 candidates dispatch in a **global** Refs-ASC / LOC-DESC order — Cat A and Cat E interleave freely, no warmup separation. Serial per-PR workflow (FR-002): one PR open at a time. Analyzer catalog regenerates after every merge (FR-014) and re-ranks the remaining queue from the fresh output.

**Standard per-PR merge gates** (FR-015 / SC-005):
- Local (`feedback_prepush_black_ruff.md`): `black --check` clean, `ruff check` clean, `python -m py_compile MistHelper.py`, `python MistHelper.py --test` reports **0 failed / exit 0**.
- Analyzer: aggregate compliance ≥ 99.6/A+ (FR-017), new/edited files A+/100 (FR-016), no A+ regression (SC-004), `MistHelper.py` pylint non-regressing (FR-018).
- Remote: 15/15 functional CI jobs green, `mergeStateStatus: CLEAN` (no `--admin` bypass per `feedback_no_admin_bypass.md`).
- Cat A only: method-parity audit output pasted in PR body (FR-025 / SC-017).
- Cat E only: callsite table (MistHelper.py + `src/` + tests/ callsites enumerated) pasted in PR body (FR-027 / SC-018) AND import-graph health verified (FR-028 / SC-019).

**Breadcrumb template** (FR-007, mandatory at every deletion site):

```text
# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1014-misthelper-refactor-hot-classes-with-src-callers/spec.md.
```

**Import-graph health probe** (FR-028, mandatory for every Cat E PR):

```bash
python -c "import sys; import src.<pkg>.<mod> as m; assert 'MistHelper' not in sys.modules, sys.modules.keys(); print('OK')"
```

If the probe fails with `MistHelper` in `sys.modules`, the new landing module has inadvertently pulled MistHelper.py through the import graph — introduce the `configure_*_dependencies()` DI pattern (per E-11) rather than reinstating a `mh.<name>` lazy import.

---

## Phase A — Pre-work (single commit, no PR)

- [ ] T001 Pull fresh `main`; capture pre-initiative pylint baseline for `MistHelper.py` and record in `specs/1014-misthelper-refactor-hot-classes-with-src-callers/baseline_pylint.txt` (FR-018 / SC-015 anchor)
- [ ] T002 Regenerate `refactor_candidates.md` on current `main` head via `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`; commit alongside the baseline (FR-014 anchor for T010+); confirm the 24-row Cat A/E Hot-with-`src/`-callers set still matches the spec § Dispatch Queue
- [ ] T003 Capture pre-initiative aggregate compliance score and per-file compliance snapshot into `specs/1014-misthelper-refactor-hot-classes-with-src-callers/baseline_compliance.txt` (SC-003 / SC-004 anchor)
- [ ] T004 Verify SKIP_ALWAYS integrity: `grep -n "GlobalImportManager\|tqdm" tools/refactor_analyzer/**/*.py` confirms both symbols still in the skip-pin set (FR-009 / SC-008 anchor)
- [ ] T005 Verify Hot-source exclusion for the 12 out-of-scope MistHelper-only residuals: `grep -rn "class GlobalWiredClientReportGenerator\|class GatewayTestExporter\|class DatabaseSchemaUtils\|class TroubleshootUtils\|class FilterOperatorEngine\|class OrgDeviceStatsExporter\|class DeviceRebootManager\|class ARPCommandManager\|class SiteAnomalyExporter\|class OfflineDeviceReporter\|class OrgTicketManager\|class OrgExportUtils" src/` returns zero matches — confirms the 12 residuals remain MistHelper-only and outside this initiative's scope (FR-012 / SC-001 / spec.md § Out of Scope)

**Phase A checkpoint**: pre-initiative baselines captured; catalog regenerated and cross-checked against the 24-row queue; skip-pin integrity confirmed; out-of-scope 12-class residual list confirmed as MistHelper-only. Phase B dispatch may begin.

---

## Phase B — Interleaved Cat A + Cat E dispatch (positions 1-24)

Per FR-026, positions dispatch in global Refs-ASC / LOC-DESC across BOTH categories combined — no Cat A warmup separation. Each block below is one PR. Serial merge: complete every step of one block before opening the next block's PR (FR-002). Task-ID convention: `TNM0..TNM7` where NM is position number (e.g. Position 1 uses T010-T017, Position 24 uses T240-T247).

### Position 1 — SSHExecutionConfig (Cat E, 5 refs, 8 LOC)

Queue head. `@dataclass` body (8 LOC) — deliberately chosen at position 1 to validate the Cat E dual-side callsite-rewrite workflow at minimum blast radius (E-13). Landing target: `src/ssh/batch/execution_config.py`.

- [ ] T010 [P1-Prep] Read class body in `MistHelper.py`; enumerate `guideline_flags` from analyzer output (expect empty — this is a plain `@dataclass`); confirm `src/ssh/batch/` package exists or seed `__init__.py` in the extraction commit
- [ ] T011 [P1-Grep] `grep -rn "SSHExecutionConfig" src/ tests/`; enumerate exact file:line list including any `mh = importlib.import_module("MistHelper")` + `mh.SSHExecutionConfig` sites; record for the FR-013 audit (FR-013)
- [ ] T012 [P1-CallsiteTable] Draft the FR-027 callsite table for the PR body: (a) total count of MistHelper.py callsites, (b) exact `src/` file:line list to be rewritten, (c) exact `tests/` file:line list if any
- [ ] T013 [P1-Create] Create `src/ssh/batch/execution_config.py` with the extracted `@dataclass` body + FR-008 non-negotiables (ASCII-only, `pathlib.Path` if used, inline comments)
- [ ] T014 [P1-Rewire] Single atomic commit (FR-005 dual-side): (a) delete class body from `MistHelper.py`, (b) add FR-007 NOTE breadcrumb, (c) rewrite all MistHelper.py callsites, (d) rewrite every `src/` `mh.SSHExecutionConfig` callsite to `from src.ssh.batch.execution_config import SSHExecutionConfig` — zero `mh.SSHExecutionConfig` remainders survive (SC-009)
- [ ] T015 [P1-LocalGate+IGHealth] Run local merge gate: `black --check MistHelper.py src/ssh/batch/`, `ruff check MistHelper.py src/ssh/batch/`, `python -m py_compile MistHelper.py`, `python MistHelper.py --test` (0 failed / exit 0), AND run the FR-028 import-graph health probe: `python -c "import sys; import src.ssh.batch.execution_config as m; assert 'MistHelper' not in sys.modules; print('OK')"`
- [ ] T016 [P1-Compliance] Regenerate analyzer output; verify `src/ssh/batch/execution_config.py` at A+/100, aggregate ≥ 99.6/A+, `MistHelper.py` pylint non-regressing (FR-016 / FR-017 / FR-018)
- [ ] T017 [P1-PR+Merge] Open PR `refactor(1014): extract SSHExecutionConfig to src/ssh/batch/ (SC-001, position 1)`; paste callsite table (FR-027) + IG-health probe output (FR-028) into body; wait 15/15 green + CLEAN; merge (no `--admin`); pull `main`; regenerate `refactor_candidates.md` (FR-014); commit refreshed catalog

### Position 2 — SiteAutoUpgradeConfigurator (Cat E, 6 refs, 22 LOC)

Landing target: `src/firmware/site_auto_upgrade.py` (fold-in) — an existing firmware-package module receives the class body. Verify E-5 name-collision and E-1 destination-choice at PR time; FR-022 mandates the destination file remains A+/100 after the fold.

- [ ] T020 [P2-Prep] Read class body; enumerate `guideline_flags`; confirm `src/firmware/site_auto_upgrade.py` exists (fold target) and note its current A+/100 status per baseline
- [ ] T021 [P2-Grep] `grep -rn "SiteAutoUpgradeConfigurator" src/ tests/`; enumerate every `mh.SiteAutoUpgradeConfigurator` lazy-import site (FR-013)
- [ ] T022 [P2-CallsiteTable] Draft FR-027 callsite table for PR body
- [ ] T023 [P2-FoldIn] Add the extracted class body into `src/firmware/site_auto_upgrade.py` (fold-in per FR-004 / FR-022); apply FR-006 guideline-flag remediation in-flight if the analyzer surfaces any
- [ ] T024 [P2-Rewire] Single atomic commit: delete class body from `MistHelper.py`, add FR-007 breadcrumb, rewrite all MistHelper.py + `src/` callsites (FR-005) — zero `mh.SiteAutoUpgradeConfigurator` remainders (SC-009)
- [ ] T025 [P2-LocalGate+IGHealth] `black --check`, `ruff check`, `py_compile`, `--test` 0-failed; FR-028 probe: `python -c "import sys; import src.firmware.site_auto_upgrade as m; assert 'MistHelper' not in sys.modules; print('OK')"`
- [ ] T026 [P2-Compliance] Regenerate; verify `src/firmware/site_auto_upgrade.py` still A+/100 after fold (FR-022), aggregate ≥ 99.6/A+, MistHelper pylint non-regressing
- [ ] T027 [P2-PR+Merge] Open PR `refactor(1014): fold SiteAutoUpgradeConfigurator into src/firmware/site_auto_upgrade.py (SC-001, position 2)`; paste callsite table + IG-health output; 15/15 green + CLEAN; merge; regen catalog

### Position 3 — SSHConnectionConfig (Cat E, 6 refs, 9 LOC)

Second `@dataclass` at the queue head (E-13). Landing target: `src/ssh/batch/connection_config.py`.

- [ ] T030 [P3-Prep] Read `@dataclass` body; expect empty `guideline_flags`; `src/ssh/batch/` package already seeded from P1
- [ ] T031 [P3-Grep] `grep -rn "SSHConnectionConfig" src/ tests/`; enumerate all `mh.SSHConnectionConfig` sites (FR-013)
- [ ] T032 [P3-CallsiteTable] Draft FR-027 callsite table
- [ ] T033 [P3-Create] Create `src/ssh/batch/connection_config.py` with the extracted dataclass body + FR-008 non-negotiables
- [ ] T034 [P3-Rewire] Single atomic commit: delete, breadcrumb, MistHelper.py + `src/` callsites rewired (FR-005)
- [ ] T035 [P3-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.ssh.batch.connection_config`
- [ ] T036 [P3-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T037 [P3-PR+Merge] Open PR (SC-001, position 3); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 4 — RoutingUtils (Cat A, 12 refs, 22 LOC)

First Cat A of the initiative. Facade in `MistHelper.py` delegates to `src/network/routing_utils.py::RoutingUtils`. Method-parity audit (FR-025) mandatory before deletion.

- [ ] T040 [P4-Prep] Read facade body and `src/network/routing_utils.py::RoutingUtils` counterpart in full; note public method / static / classmethod / instance-attribute surface
- [ ] T041 [P4-Audit] Method-parity audit (FR-025): enumerate every public callable/attribute on the facade, confirm each is exposed with signature-equivalent semantics by the `src/` implementation; capture audit output verbatim for the PR body's fenced code block
- [ ] T042 [P4-Grep] `grep -rn "RoutingUtils" src/ tests/`; distinguish `src/network/routing_utils.py` self-references from external Cat A callers; if external `src/` sites exist that import the *facade*, they must also be rewired to the real class in this commit (FR-013)
- [ ] T043 [P4-Rewire] Single commit: (a) delete facade body from `MistHelper.py`, (b) add FR-007 NOTE breadcrumb pointing at `src/network/routing_utils.py::RoutingUtils`, (c) rewire all 12 MistHelper.py callsites (and any `src/` callers still importing the facade) — no `_Impl` alias, no `_configure_module()` helper, no factory `create()` indirection surviving
- [ ] T044 [P4-LocalGate] `black --check MistHelper.py src/network/`, `ruff check MistHelper.py src/network/`, `py_compile`, `--test` 0-failed
- [ ] T045 [P4-Compliance] Regenerate analyzer output; verify `src/network/routing_utils.py` still A+/100, aggregate ≥ 99.6/A+, MistHelper pylint non-regressing
- [ ] T046 [P4-PR] Open PR `refactor(1014): remove RoutingUtils facade (SC-001, position 4)`; paste method-parity audit output (FR-025 / SC-017) into body; push and wait for 15/15 green + mergeStateStatus CLEAN
- [ ] T047 [P4-Merge] Merge PR (no `--admin`); pull `main`; regenerate `refactor_candidates.md` (FR-014); commit refreshed catalog

### Position 5 — ValidationUtils (Cat E, 15 refs, 90 LOC)

Landing target: `src/validation/validation_utils.py`. Expect `oversize_25_lines` flags on some validators — FR-006 mandates in-flight decomposition.

- [ ] T050 [P5-Prep] Read class body; enumerate `guideline_flags`; confirm `src/validation/` package exists or seed `__init__.py`
- [ ] T051 [P5-Grep] `grep -rn "ValidationUtils" src/ tests/`; enumerate every `mh.ValidationUtils` lazy-import site (FR-013)
- [ ] T052 [P5-CallsiteTable] Draft FR-027 callsite table
- [ ] T053 [P5-Create] Create `src/validation/validation_utils.py` with class body + method decomposition to ≤ 25 lines + full FR-006/FR-008 remediation (`logging.info`/`logging.debug` envelopes, `%s` formatting, ASCII-only, `pathlib.Path`, `InputUtils.safe_input()` if applicable)
- [ ] T054 [P5-Rewire] Single atomic commit: delete, breadcrumb, MistHelper.py + `src/` callsites rewired (FR-005)
- [ ] T055 [P5-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.validation.validation_utils`
- [ ] T056 [P5-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T057 [P5-PR+Merge] Open PR (SC-001, position 5); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 6 — TimeUtils (Cat E, 27 refs, 29 LOC)

Landing target: `src/time/time_utils.py`. Small class body, high fan-out — the 27-caller rewire dominates the PR effort.

- [ ] T060 [P6-Prep] Read class body; enumerate `guideline_flags`; confirm `src/time/` package exists or seed `__init__.py`
- [ ] T061 [P6-Grep] `grep -rn "TimeUtils" src/ tests/`; enumerate every `mh.TimeUtils` site (FR-013)
- [ ] T062 [P6-CallsiteTable] Draft FR-027 callsite table (largest external fan-out to date — expect the `src/` list dominates)
- [ ] T063 [P6-Create] Create `src/time/time_utils.py` with class body + FR-006/FR-008 remediation
- [ ] T064 [P6-Rewire] Single atomic commit: delete, breadcrumb, all 27 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T065 [P6-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.time.time_utils`
- [ ] T066 [P6-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T067 [P6-PR+Merge] Open PR (SC-001, position 6); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 7 — OrgLevelAPFirmwareUpgrader (Cat E, 33 refs, 79 LOC)

Landing target: `src/firmware/org_ap_upgrader.py` (fold-in). Second firmware-package fold-in of the initiative — FR-022 mandates destination remains A+/100 after fold.

- [ ] T070 [P7-Prep] Read class body; enumerate `guideline_flags`; confirm `src/firmware/org_ap_upgrader.py` exists (fold target) and its baseline A+/100
- [ ] T071 [P7-Grep] `grep -rn "OrgLevelAPFirmwareUpgrader" src/ tests/`; enumerate every `mh.OrgLevelAPFirmwareUpgrader` site (FR-013)
- [ ] T072 [P7-CallsiteTable] Draft FR-027 callsite table
- [ ] T073 [P7-FoldIn] Fold class body into `src/firmware/org_ap_upgrader.py` (per FR-004 / FR-022); apply FR-006 in-flight remediation
- [ ] T074 [P7-Rewire] Single atomic commit: delete from `MistHelper.py`, breadcrumb, MistHelper.py + `src/` callsites rewired
- [ ] T075 [P7-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.firmware.org_ap_upgrader`
- [ ] T076 [P7-Compliance] Regenerate; destination A+/100 preserved (FR-022), aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T077 [P7-PR+Merge] Open PR (SC-001, position 7); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 8 — APIFetchUtils (Cat E, 34 refs, 221 LOC)

Landing target: `src/api/api_fetch_utils.py`. Heavy `oversize_25_lines` decomposition expected (E-2, E-10). 34 callers across MistHelper.py + `src/` — expect the `src/` fan-out to dominate.

- [ ] T080 [P8-Prep] Read class body; enumerate every `oversize_25_lines` flag; confirm `src/api/` package exists or seed `__init__.py`
- [ ] T081 [P8-Grep] `grep -rn "APIFetchUtils" src/ tests/`; enumerate `mh.APIFetchUtils` sites (FR-013)
- [ ] T082 [P8-CallsiteTable] Draft FR-027 callsite table
- [ ] T083 [P8-Create] Create `src/api/api_fetch_utils.py` with class body + heavy method decomposition (every method ≤ 25 lines, ≤ 5 params) + full FR-006/FR-008 remediation
- [ ] T084 [P8-Rewire] Single atomic commit: delete, breadcrumb, 34 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T085 [P8-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.api.api_fetch_utils`
- [ ] T086 [P8-Compliance] Regenerate; A+/100 new file (heavy-decomposition candidate — critical A+ target), aggregate ≥ 99.6/A+, pylint non-regressing (expect visible LOC delta)
- [ ] T087 [P8-PR+Merge] Open PR (SC-001, position 8); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 9 — OrgSiteExporter (Cat E, 43 refs, 112 LOC)

Landing target: `src/export/org_site_exporter.py`. First `src/export/` extraction of five in the initiative.

- [ ] T090 [P9-Prep] Read class body; enumerate `guideline_flags`; confirm `src/export/` package (existing from 1013)
- [ ] T091 [P9-Grep] `grep -rn "OrgSiteExporter" src/ tests/`; enumerate `mh.OrgSiteExporter` sites (FR-013)
- [ ] T092 [P9-CallsiteTable] Draft FR-027 callsite table
- [ ] T093 [P9-Create] Create `src/export/org_site_exporter.py` with class body + FR-006/FR-008 remediation
- [ ] T094 [P9-Rewire] Single atomic commit: delete, breadcrumb, 43 callsites rewired (FR-005)
- [ ] T095 [P9-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.export.org_site_exporter`
- [ ] T096 [P9-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T097 [P9-PR+Merge] Open PR (SC-001, position 9); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 10 — APICoreFetchUtils (Cat E, 43 refs, 47 LOC)

Landing target: `src/api/api_core_fetch_utils.py`. Package already seeded by position 8.

- [ ] T100 [P10-Prep] Read class body; enumerate `guideline_flags`
- [ ] T101 [P10-Grep] `grep -rn "APICoreFetchUtils" src/ tests/`; enumerate `mh.APICoreFetchUtils` sites (FR-013)
- [ ] T102 [P10-CallsiteTable] Draft FR-027 callsite table
- [ ] T103 [P10-Create] Create `src/api/api_core_fetch_utils.py` with class body + FR-006/FR-008 remediation
- [ ] T104 [P10-Rewire] Single atomic commit: delete, breadcrumb, 43 callsites rewired (FR-005)
- [ ] T105 [P10-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.api.api_core_fetch_utils`
- [ ] T106 [P10-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T107 [P10-PR+Merge] Open PR (SC-001, position 10); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 11 — InsightMetricsUtils (Cat E, 51 refs, 328 LOC)

Landing target: `src/analytics/insight_metrics_utils.py`. Heavy `oversize_25_lines` decomposition (E-2, E-10). One of six heavy-decomposition candidates in the initiative.

- [ ] T110 [P11-Prep] Read class body; enumerate every `oversize_25_lines` flag; confirm `src/analytics/` package exists or seed `__init__.py`
- [ ] T111 [P11-Grep] `grep -rn "InsightMetricsUtils" src/ tests/`; enumerate `mh.InsightMetricsUtils` sites (FR-013)
- [ ] T112 [P11-CallsiteTable] Draft FR-027 callsite table
- [ ] T113 [P11-Create] Create `src/analytics/insight_metrics_utils.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T114 [P11-Rewire] Single atomic commit: delete, breadcrumb, 51 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T115 [P11-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.analytics.insight_metrics_utils`
- [ ] T116 [P11-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing (expect large LOC delta)
- [ ] T117 [P11-PR+Merge] Open PR (SC-001, position 11); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 12 — GatewayStatsExporter (Cat A, 52 refs, 28 LOC)

Second Cat A. Facade in `MistHelper.py` delegates to `src/gateway/gateway_stats_exporter.py::GatewayStatsExporter`.

- [ ] T120 [P12-Prep] Read facade body and `src/gateway/gateway_stats_exporter.py::GatewayStatsExporter` counterpart; note public surface
- [ ] T121 [P12-Audit] Method-parity audit (FR-025): enumerate every public callable/attribute; confirm src/ parity; capture audit output for PR body
- [ ] T122 [P12-Grep] `grep -rn "GatewayStatsExporter" src/ tests/`; identify any `src/` callers that must also be rewired if they import the facade (FR-013)
- [ ] T123 [P12-Rewire] Single commit: delete facade body, add FR-007 breadcrumb, rewire all 52 MistHelper.py callsites (and any `src/` facade importers) to reference `src/gateway/gateway_stats_exporter.py::GatewayStatsExporter` directly
- [ ] T124 [P12-LocalGate] `black --check`, `ruff check`, `py_compile`, `--test` 0-failed
- [ ] T125 [P12-Compliance] Regenerate; `src/gateway/gateway_stats_exporter.py` still A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T126 [P12-PR] Open PR `refactor(1014): remove GatewayStatsExporter facade (SC-001, position 12)`; paste method-parity audit (FR-025 / SC-017); wait 15/15 green + CLEAN
- [ ] T127 [P12-Merge] Merge; pull; regenerate catalog

### Position 13 — GatewayExportUtils (Cat A, 78 refs, 98 LOC)

Third Cat A. Facade delegates to `src/gateway/gateway_export_utils.py::GatewayExportUtils`. High fan-out (78 refs) — method-parity audit rigor MUST enumerate the full facade surface (FR-025). Verify any `src/` facade importers.

- [ ] T130 [P13-Prep] Read facade body and `src/gateway/gateway_export_utils.py::GatewayExportUtils` counterpart; note public surface (expect wide static/classmethod set given fan-out)
- [ ] T131 [P13-Audit] Method-parity audit (FR-025): enumerate every public callable/attribute; confirm src/ parity; if any facade method absent from src/, port it in the same commit OR defer per FR-025(ii) with entry in spec.md § Deferred Candidates; capture audit for PR body
- [ ] T132 [P13-Grep] `grep -rn "GatewayExportUtils" src/ tests/`; identify `src/` facade importers requiring same-commit rewire (FR-013)
- [ ] T133 [P13-Rewire] Single commit: delete facade body, breadcrumb, rewire all 78 MistHelper.py callsites (and any `src/` facade importers) to reference the src/ class directly
- [ ] T134 [P13-LocalGate] Local gate 0-failed
- [ ] T135 [P13-Compliance] Regenerate; `src/gateway/gateway_export_utils.py` still A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T136 [P13-PR] Open PR `refactor(1014): remove GatewayExportUtils facade (SC-001, position 13)`; paste method-parity audit; wait 15/15 green + CLEAN
- [ ] T137 [P13-Merge] Merge; pull; regenerate catalog

### Position 14 — CacheUtils (Cat E, 81 refs, 264 LOC)

Landing target: `src/cache/cache_utils.py`. Heavy-decomposition candidate (E-2, E-10). 81 callers dominate the rewire effort.

- [ ] T140 [P14-Prep] Read class body; enumerate every `oversize_25_lines` flag; confirm `src/cache/` package exists or seed `__init__.py`
- [ ] T141 [P14-Grep] `grep -rn "CacheUtils" src/ tests/`; enumerate `mh.CacheUtils` sites — expect a substantial `src/` list (FR-013)
- [ ] T142 [P14-CallsiteTable] Draft FR-027 callsite table (large list — allocate careful enumeration)
- [ ] T143 [P14-Create] Create `src/cache/cache_utils.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T144 [P14-Rewire] Single atomic commit: delete, breadcrumb, 81 callsites rewired across MistHelper.py + `src/` (FR-005) — E-11 circular-import risk elevated given cache's broad reach; if IG probe fails, apply `configure_cache_dependencies()` DI pattern rather than reinstating `mh.CacheUtils`
- [ ] T145 [P14-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.cache.cache_utils` — CRITICAL: this candidate has elevated E-11 risk given cache module tends to be depended on by many `src/` modules that also touch MistHelper globals
- [ ] T146 [P14-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T147 [P14-PR+Merge] Open PR (SC-001, position 14); paste callsite table + IG-health output + (if used) DI-pattern rationale; 15/15 green + CLEAN; merge; regen catalog

### Position 15 — SSHRunnerManager (Cat A, 82 refs, 26 LOC)

Fourth Cat A. Facade delegates to `src/ssh/ssh_runner_manager.py::SSHRunnerManager`. High fan-out (82 refs) — mostly small-body facade with heavy caller list.

- [ ] T150 [P15-Prep] Read facade body and `src/ssh/ssh_runner_manager.py::SSHRunnerManager` counterpart; note public surface
- [ ] T151 [P15-Audit] Method-parity audit (FR-025); capture output for PR body
- [ ] T152 [P15-Grep] `grep -rn "SSHRunnerManager" src/ tests/`; identify `src/` facade importers (FR-013)
- [ ] T153 [P15-Rewire] Single commit: delete facade, breadcrumb, rewire all 82 MistHelper.py callsites (and `src/` facade importers) to reference the src/ class directly
- [ ] T154 [P15-LocalGate] Local gate 0-failed
- [ ] T155 [P15-Compliance] Regenerate; `src/ssh/ssh_runner_manager.py` A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T156 [P15-PR] Open PR `refactor(1014): remove SSHRunnerManager facade (SC-001, position 15)`; paste method-parity audit; wait 15/15 green + CLEAN
- [ ] T157 [P15-Merge] Merge; pull; regenerate catalog

### Position 16 — SiteExportUtils (Cat A, 86 refs, 145 LOC)

Fifth Cat A. Facade delegates to `src/export/site_export_utils.py::SiteExportUtils`. **Highest Cat A method-parity risk in the initiative** — spec § Dispatch Queue notes this facade uses `_configure_module()` and exposes a large static-method surface. The parity table MUST enumerate every static/classmethod exposed by the facade.

- [ ] T160 [P16-Prep] Read facade body in full including `_configure_module()`; read `src/export/site_export_utils.py::SiteExportUtils` counterpart; note public surface (expect wide static/classmethod set)
- [ ] T161 [P16-Audit] Method-parity audit (FR-025): enumerate every static/classmethod/attribute exposed by facade; confirm each in src/; if facade exposes any method absent from src/, port it in this commit OR defer per FR-025(ii); capture full audit table for PR body
- [ ] T162 [P16-Grep] `grep -rn "SiteExportUtils" src/ tests/`; identify `src/` facade importers requiring same-commit rewire (FR-013)
- [ ] T163 [P16-Rewire] Single commit: delete facade body + `_configure_module()` helper, breadcrumb, rewire all 86 MistHelper.py callsites (and any `src/` facade importers) — zero `_configure_module()` / `_Impl` / `create()` residue in `MistHelper.py`
- [ ] T164 [P16-LocalGate] Local gate 0-failed
- [ ] T165 [P16-Compliance] Regenerate; `src/export/site_export_utils.py` A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T166 [P16-PR] Open PR `refactor(1014): remove SiteExportUtils facade (SC-001, position 16 — highest Cat A method-parity risk)`; paste method-parity audit (fenced code block); wait 15/15 green + CLEAN
- [ ] T167 [P16-Merge] Merge; pull; regenerate catalog

### Position 17 — FilePathUtils (Cat E, 86 refs, 46 LOC)

Landing target: `src/utils/file_path_utils.py`. High fan-out (86 refs), modest class body.

- [ ] T170 [P17-Prep] Read class body; enumerate `guideline_flags`
- [ ] T171 [P17-Grep] `grep -rn "FilePathUtils" src/ tests/`; enumerate `mh.FilePathUtils` sites — expect a large `src/` list (FR-013)
- [ ] T172 [P17-CallsiteTable] Draft FR-027 callsite table
- [ ] T173 [P17-Create] Create `src/utils/file_path_utils.py` with class body + FR-006/FR-008 remediation (`pathlib.Path` non-negotiable is native to this class)
- [ ] T174 [P17-Rewire] Single atomic commit: delete, breadcrumb, 86 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T175 [P17-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.utils.file_path_utils`
- [ ] T176 [P17-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T177 [P17-PR+Merge] Open PR (SC-001, position 17); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 18 — PromptUtils (Cat E, 90 refs, 441 LOC)

Landing target: `src/ui/prompt_utils.py`. Heavy-decomposition candidate (E-2, E-10). Second-largest LOC in the queue after `OrgInventoryExporter`. Prompt-utilities class — `InputUtils.safe_input()` non-negotiable applies extensively (FR-008).

- [ ] T180 [P18-Prep] Read class body in full; enumerate every `oversize_25_lines` flag and every raw `input()` call site (FR-006 / FR-008); confirm `src/ui/` package (existing from 1013)
- [ ] T181 [P18-Grep] `grep -rn "PromptUtils" src/ tests/`; enumerate `mh.PromptUtils` sites (FR-013)
- [ ] T182 [P18-CallsiteTable] Draft FR-027 callsite table
- [ ] T183 [P18-Create] Create `src/ui/prompt_utils.py` with class body + heavy method decomposition + FR-006/FR-008 remediation (every raw `input()` → `InputUtils.safe_input()`, every method ≤ 25 lines, `logging.info`/`logging.debug` envelopes)
- [ ] T184 [P18-Rewire] Single atomic commit: delete, breadcrumb, 90 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T185 [P18-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.ui.prompt_utils` — E-11 risk moderate (UI layer typically imports few globals)
- [ ] T186 [P18-Compliance] Regenerate; A+/100 new file (large-LOC A+ target — hard), aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T187 [P18-PR+Merge] Open PR (SC-001, position 18); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 19 — OrgInventoryExporter (Cat E, 104 refs, 686 LOC)

Landing target: `src/export/org_inventory_exporter.py`. **Largest single-file candidate in the initiative** (686 LOC) — heaviest-decomposition candidate (E-2, E-10). Consider a scratch-branch dry-run compile check before the actual rewire commit.

- [ ] T190 [P19-Prep] Read class body in full; enumerate every `guideline_flag` (expect a substantial `oversize_25_lines` set); confirm `src/export/` package
- [ ] T191 [P19-Grep] `grep -rn "OrgInventoryExporter" src/ tests/`; enumerate `mh.OrgInventoryExporter` sites (FR-013)
- [ ] T192 [P19-CallsiteTable] Draft FR-027 callsite table
- [ ] T193 [P19-Create] Create `src/export/org_inventory_exporter.py` with class body + **exhaustive** method decomposition (every method ≤ 25 lines, ≤ 5 params) + full FR-006/FR-008 remediation
- [ ] T194 [P19-Rewire] Single atomic commit: delete, breadcrumb, 104 callsites rewired across MistHelper.py + `src/` (FR-005) — largest single-file rewire surface to date in the initiative
- [ ] T195 [P19-LocalGate+IGHealth] Local gate 0-failed (critical smoke run given surface size); FR-028 probe against `src.export.org_inventory_exporter`
- [ ] T196 [P19-Compliance] Regenerate; A+/100 new file (largest single A+ target — hardest of the initiative), aggregate ≥ 99.6/A+, pylint non-regressing (expect largest single-PR pylint delta of the initiative)
- [ ] T197 [P19-PR+Merge] Open PR (SC-001, position 19 — largest single-file candidate); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 20 — VirtualChassisManager (Cat A, 104 refs, 78 LOC)

Sixth and final Cat A. Facade delegates to `src/device/virtual_chassis.py::VirtualChassisManager`. High fan-out (104 refs) — the initiative's highest Cat A fan-out.

- [ ] T200 [P20-Prep] Read facade body and `src/device/virtual_chassis.py::VirtualChassisManager` counterpart; note public surface
- [ ] T201 [P20-Audit] Method-parity audit (FR-025); capture output for PR body
- [ ] T202 [P20-Grep] `grep -rn "VirtualChassisManager" src/ tests/`; identify `src/` facade importers (FR-013)
- [ ] T203 [P20-Rewire] Single commit: delete facade body, breadcrumb, rewire all 104 MistHelper.py callsites (and `src/` facade importers) to reference the src/ class directly
- [ ] T204 [P20-LocalGate] Local gate 0-failed
- [ ] T205 [P20-Compliance] Regenerate; `src/device/virtual_chassis.py` A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T206 [P20-PR] Open PR `refactor(1014): remove VirtualChassisManager facade (SC-001, position 20 — final Cat A)`; paste method-parity audit; wait 15/15 green + CLEAN
- [ ] T207 [P20-Merge] Merge; pull; regenerate catalog

### Position 21 — DataProcessingUtils (Cat E, 125 refs, 158 LOC)

Landing target: `src/data/data_processing_utils.py`. Heavy-decomposition candidate (E-2). Rewire surface at 125 callers requires meticulous review.

- [ ] T210 [P21-Prep] Read class body; enumerate `oversize_25_lines` flags; confirm `src/data/` package exists or seed `__init__.py`
- [ ] T211 [P21-Grep] `grep -rn "DataProcessingUtils" src/ tests/`; enumerate `mh.DataProcessingUtils` sites (FR-013)
- [ ] T212 [P21-CallsiteTable] Draft FR-027 callsite table (large list)
- [ ] T213 [P21-Create] Create `src/data/data_processing_utils.py` with class body + heavy method decomposition + FR-006/FR-008 remediation
- [ ] T214 [P21-Rewire] Single atomic commit: delete, breadcrumb, 125 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T215 [P21-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.data.data_processing_utils`
- [ ] T216 [P21-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T217 [P21-PR+Merge] Open PR (SC-001, position 21); paste callsite table + IG-health; 15/15 green + CLEAN; merge; regen catalog

### Position 22 — ConfigUtils (Cat E, 146 refs, 70 LOC)

Landing target: `src/config/config_utils.py`. Very high fan-out (146 refs); modest LOC.

- [ ] T220 [P22-Prep] Read class body; enumerate `guideline_flags`; confirm `src/config/` package exists or seed `__init__.py`
- [ ] T221 [P22-Grep] `grep -rn "ConfigUtils" src/ tests/`; enumerate `mh.ConfigUtils` sites (FR-013)
- [ ] T222 [P22-CallsiteTable] Draft FR-027 callsite table
- [ ] T223 [P22-Create] Create `src/config/config_utils.py` with class body + FR-006/FR-008 remediation
- [ ] T224 [P22-Rewire] Single atomic commit: delete, breadcrumb, 146 callsites rewired across MistHelper.py + `src/` (FR-005)
- [ ] T225 [P22-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.config.config_utils` — E-11 risk elevated (config is broadly imported)
- [ ] T226 [P22-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T227 [P22-PR+Merge] Open PR (SC-001, position 22); paste callsite table + IG-health + (if used) DI-pattern rationale; 15/15 green + CLEAN; merge; regen catalog

### Position 23 — DataExporter (Cat E, 168 refs, 345 LOC)

Landing target: `src/export/data_exporter.py`. Heavy-decomposition candidate (E-2, E-10). Very high fan-out (168 refs). Class body carries real state (`_router`, `_router_initialized`, `_last_snapshot_times`) — the E-11 DI-pattern option is applicable if the naive extraction pulls MistHelper globals through the router initialization path.

- [ ] T230 [P23-Prep] Read class body in full including state initialization; enumerate every `oversize_25_lines` flag; confirm `src/export/` package
- [ ] T231 [P23-Grep] `grep -rn "DataExporter" src/ tests/`; enumerate `mh.DataExporter` sites (FR-013)
- [ ] T232 [P23-CallsiteTable] Draft FR-027 callsite table (large list — allocate careful enumeration)
- [ ] T233 [P23-Create] Create `src/export/data_exporter.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation; if the router initialization path pulls MistHelper globals, introduce `configure_data_exporter_dependencies()` DI surface per E-11
- [ ] T234 [P23-Rewire] Single atomic commit: delete, breadcrumb, 168 callsites rewired across MistHelper.py + `src/` (FR-005) — second-largest rewire surface in the initiative
- [ ] T235 [P23-LocalGate+IGHealth] Local gate 0-failed; FR-028 probe against `src.export.data_exporter` — CRITICAL: real-state class with wide reach elevates E-11 circular-import risk
- [ ] T236 [P23-Compliance] Regenerate; A+/100 new file (large-LOC A+ target), aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T237 [P23-PR+Merge] Open PR (SC-001, position 23); paste callsite table + IG-health + (if used) DI-pattern rationale; 15/15 green + CLEAN; merge; regen catalog

### Position 24 — InputUtils (Cat E, 229 refs, 74 LOC)

Landing target: `src/ui/input_utils.py`. **Terminal candidate — highest fan-out (229 refs) in the queue.** `InputUtils.safe_input()` is a project non-negotiable (FR-008) — every module in the codebase calls it, so its extraction is the initiative's most-referenced rewire.

- [ ] T240 [P24-Prep] Read class body; enumerate `guideline_flags`; confirm `src/ui/` package
- [ ] T241 [P24-Grep] `grep -rn "InputUtils" src/ tests/`; enumerate `mh.InputUtils` sites — expect the **largest** `src/` list of the initiative (FR-013)
- [ ] T242 [P24-CallsiteTable] Draft FR-027 callsite table (largest list — allocate meticulous enumeration and consider a scratch-branch dry-run compile check before the actual rewire commit)
- [ ] T243 [P24-Create] Create `src/ui/input_utils.py` with class body + FR-006/FR-008 remediation
- [ ] T244 [P24-Rewire] Single atomic commit: delete, breadcrumb, 229 callsites rewired across MistHelper.py + `src/` (FR-005) — **largest single rewire surface in the initiative**. Consider tooling-assisted rewrite (e.g. a scripted `sed`-driven pass with manual review) to reduce human error over the 229-callsite surface
- [ ] T245 [P24-LocalGate+IGHealth] Local gate 0-failed (critical smoke run — this PR closes the initiative's operational body); FR-028 probe against `src.ui.input_utils` — E-11 risk is universal (nearly every module uses `InputUtils.safe_input()`)
- [ ] T246 [P24-Compliance] Regenerate; A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing (expect the largest single-PR pylint delta of the initiative)
- [ ] T247 [P24-PR+Merge] Open PR `refactor(1014): extract InputUtils to src/ui/ (SC-001, position 24 — terminal candidate, highest fan-out)`; paste callsite table + IG-health + (if used) DI-pattern rationale; 15/15 green + CLEAN; merge; regen catalog

**Phase B checkpoint** (SC-001 complete for non-deferred candidates): all 24 extractions merged (or recorded as deferred with rationale). Phase C closeout begins.

---

## Phase C — Closeout & aggregate verification

- [ ] T500 Verify SC-001: freshest `refactor_candidates.md` reports zero of the 24 Dispatch Queue classes in the Hot bucket (or each remaining entry is listed in spec.md § Deferred Candidates with rationale)
- [ ] T501 Verify SC-002: `MistHelper.py` physical line count drops by at least **3,000 lines** relative to the pre-initiative baseline
- [ ] T502 Verify SC-003 / SC-004: aggregate compliance ≥ 99.6/A+ at every intermediate `main` state (walkable via merged-PR sequence); zero previously-A+ files regressed
- [ ] T503 Verify SC-005: every merged PR had 15/15 green + `mergeStateStatus: CLEAN` + `black --check` clean + `ruff check` clean + `python MistHelper.py --test` 0-failed / exit 0; zero `--admin` bypasses except where root-cause-documented
- [ ] T504 Verify SC-006: every new file created during the initiative scores A+/100 on compliance (walk the Dispatch Queue landing-target column against `python tools/refactor_analyzer` output)
- [ ] T505 Verify SC-007: `grep -n "class .* = " MistHelper.py` shows zero wrapper shims / re-export aliases attributable to this initiative
- [ ] T506 Verify SC-008: SKIP_ALWAYS integrity — `GlobalImportManager` and `tqdm` unmodified across the initiative
- [ ] T507 Verify SC-009: zero `importlib.import_module("MistHelper")` + `mh.<ClassName>` remainders survive for any Cat E-extracted class — verifiable via `grep -rn "importlib.import_module.\"MistHelper\"" src/` returning zero matches OR matches only for out-of-scope classes
- [ ] T508 Verify SC-010: catalog regeneration recorded after every merge — walkable via commit history (24 catalog-refresh commits should follow the 24 extraction PRs)
- [ ] T509 Verify SC-011: zero forward-carried `guideline_flags` on any extracted class
- [ ] T510 Verify SC-012: NOTE breadcrumb present at every deletion site — `grep -c "extracted to .*::" MistHelper.py` matches merged-PR count (24 or 24-minus-deferred)
- [ ] T511 Verify SC-013: pre-push local-gate discipline maintained across the branch history
- [ ] T512 Verify SC-014: dispatch order matched Refs-ASC / LOC-DESC across BOTH Cat A + Cat E from the freshest catalog at each step (no warmup separation per FR-026)
- [ ] T513 Verify SC-015: `MistHelper.py` pylint non-regressing vs `baseline_pylint.txt` from T001
- [ ] T514 Verify SC-016: zero new SKIPPED conditionals introduced by any initiative PR
- [ ] T515 Verify SC-017: every Cat A PR contains a fenced-code-block method-parity audit in the description (6 PRs — positions 4, 12, 13, 15, 16, 20)
- [ ] T516 Verify SC-018: every Cat E PR contains a callsite table in the description (18 PRs — positions 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 14, 17, 18, 19, 21, 22, 23, 24)
- [ ] T517 Verify SC-019: every Cat E PR verified import-graph health per FR-028 — post-merge `python -c "import <landing_module>; print('OK')"` succeeds without `MistHelper` in `sys.modules` for each of the 18 Cat E landing modules
- [ ] T518 Regenerate `refactor_candidates.md` one last time on final `main` head; verify Hot-bucket count = pre-initiative-count minus 24 extracted minus any deferred; commit the terminal catalog snapshot
- [ ] T519 [Closeout PR] SC-020 — Open a docs-only PR (or extend the position-24 PR body) recording: (a) count of PRs merged (target 24), (b) final `MistHelper.py` LoC + pylint score, (c) final aggregate compliance score, (d) list of deferred candidates with rationale, (e) count of remaining Hot-bucket classes (target ~12 out-of-scope MistHelper-only residuals + any deferred); merge to close initiative 1014

---

## Dependencies

- **Phase A** (T001-T005) → gates Phase B (T010-T247). Phase A commits go direct to `main` (no PR); Phase B onwards is per-PR.
- **Phase B sequential ordering** (FR-002, FR-023, FR-026): position N's PR (T0N0 + subsequent 7 tasks) MUST merge before position N+1's PR opens. Global Refs-ASC / LOC-DESC across BOTH Cat A and Cat E — no warmup partitioning. Deferral (FR-013/FR-020/FR-025-ii) advances the next position without opening the deferred PR.
- **Per-candidate internal ordering** (within a single position's 8-task block):
  - **Cat A**: pre-flight (read) → method-parity audit (FR-025) → grep audit (FR-013) → single-commit delete+rewire+breadcrumb → local gate → compliance regen → PR open+CI wait → merge+catalog refresh.
  - **Cat E**: pre-flight (read) → grep audit (FR-013) → callsite-table draft (FR-027) → landing-module create/fold (FR-004) → single-commit delete+dual-side rewire+breadcrumb (FR-005) → local gate + IG-health probe (FR-028) → compliance regen → PR open+CI wait → merge+catalog refresh.
- **Phase C** (T500-T519) runs only after position 24 merges (T247). T519 is the initiative closeout doc commit.

## Parallel Opportunities

- **Zero cross-PR parallelism**: FR-002 mandates one open PR at a time. No two positions may be under PR simultaneously.
- **Within a candidate block**, the pre-flight tasks (read def-site, grep audit, callsite-table draft or method-parity audit, landing-module skeleton) MAY run in parallel by a single contributor at branch time, but the single delete+rewire+breadcrumb commit is atomic and non-parallelizable.
- **Method-parity audits** (T041, T121, T131, T151, T161, T201) for the 6 Cat A candidates MAY be conducted concurrently as advance research *before* opening any PR; the actual PR sequence remains strictly serial.
- **Callsite-table drafts** (T012, T022, T032, T052, T062, T072, T082, T092, T102, T112, T142, T172, T182, T192, T212, T222, T232, T242) for the 18 Cat E candidates MAY be drafted in a scratch document ahead of dispatch time to identify circular-import risk hotspots early — but each PR must re-run the grep against the current `main` head at branch time (FR-013 audit is real-time, not historical).

## Implementation Strategy

1. **No warmup partitioning (FR-026)**: unlike 1013, this initiative does not front-load Cat A. The 6 Cat A candidates are distributed across the queue (positions 4, 12, 13, 15, 16, 20) and interleave with Cat E purely by refs/LOC order. This preserves the smallest-blast-radius-first dispatch discipline.
2. **Queue-head validation (positions 1-3)**: the three smallest Cat E candidates (`SSHExecutionConfig` at 5r/8L, `SiteAutoUpgradeConfigurator` at 6r/22L, `SSHConnectionConfig` at 6r/9L) validate the Cat E dual-side rewire workflow at minimum blast radius. Two of the three are `@dataclass` bodies with typically-empty `guideline_flags` (E-13). Verify FR-005 atomic-rewire discipline and FR-028 IG-health probe on these before proceeding to higher-refs candidates.
3. **First Cat A checkpoint (position 4)**: `RoutingUtils` at 12r/22L is the queue's first facade-removal. Establish the FR-025 method-parity audit shape here so it's proven before the higher-fan-out Cat A candidates (positions 12, 13, 15, 16, 20).
4. **Cat A method-parity rigor scales with fan-out**: positions 13 (`GatewayExportUtils`, 78 refs), 15 (`SSHRunnerManager`, 82 refs), 16 (`SiteExportUtils`, 86 refs, `_configure_module()` risk), and 20 (`VirtualChassisManager`, 104 refs) require exhaustive parity tables. Position 16 is explicitly flagged as the initiative's highest Cat A method-parity risk (spec § Dispatch Queue).
5. **Heavy-decomposition candidates** (positions 8, 11, 14, 18, 19, 21, 23) MUST decompose in-flight (E-2, E-10, FR-006). Allocate meaningful engineering time — 221/328/264/441/686/158/345 LOC classes cannot land as monolithic method blocks and hit A+/100.
6. **E-11 circular-import DI escape hatch**: for Cat E candidates whose new landing module inadvertently pulls MistHelper globals (`apisession`, etc.) through the import graph, introduce the `configure_*_dependencies()` DI pattern (already used elsewhere in `src/`). Do NOT reinstate `mh.<name>` lazy imports in the new module. Elevated-risk candidates: `CacheUtils` (P14), `ConfigUtils` (P22), `DataExporter` (P23), `InputUtils` (P24) — each is broadly imported across `src/`.
7. **Terminal-candidate risk (position 24)**: `InputUtils` at 229 refs / 74 LOC is the initiative's final and highest-fan-out PR. The 229-callsite rewire surface benefits from tooling-assisted rewrite (scripted `sed` pass + manual review) rather than pure manual editing. Consider a scratch-branch dry-run compile check before the actual rewire commit.
8. **Analyzer regeneration is mandatory after every merge (FR-014)**: skipping the regen means the next dispatch is derived from stale ref counts and may re-order incorrectly per SC-014. Cat E extractions in particular can cascade-reduce reference counts on other Hot classes when a shared caller loses a `mh.<name>` block.
9. **Reclassification is a legitimate outcome (E-12, FR-020)**: if a Cat A candidate mid-initiative gains a new `src/` importer of the *facade*, it reclassifies to Cat E for the remainder. Conversely, if a Cat E candidate's `src/` callers all get refactored away by unrelated commits, it reclassifies out of scope entirely (deferred to a MistHelper-only follow-up). Record every reclassification in spec.md § Reclassifications.
10. **Deferral is a legitimate outcome (FR-013, FR-020, FR-025-ii)**: a candidate that surfaces an unresolvable parity gap (Cat A) or an intractable circular-import (Cat E) is deferred, not force-extracted. Deferrals are recorded in spec.md § Deferred Candidates and reduce the merged-PR count below 24 (see SC-020(a)).

## Format Validation

Every task above follows the strict checklist format: `- [ ] T### [Story?] Description with file path`. Task IDs are T001..T005 (5 pre-work tasks), T010..T247 (192 dispatch tasks across 24 positions × 8 tasks each), and T500..T519 (20 closeout tasks). Total: **217 tasks**. Story-label convention: `[P#-Stage]` where `#` is dispatch position (1-24) and `Stage` names the intra-block step (Prep, Grep, Audit, CallsiteTable, Create, FoldIn, Rewire, LocalGate, LocalGate+IGHealth, Compliance, PR, PR+Merge, Merge) — used as a candidate-block identifier rather than a P1/P2/P3 story priority (all dispatch tasks are effectively equal-priority User Story 1 or User Story 2 per spec.md § User Scenarios).
