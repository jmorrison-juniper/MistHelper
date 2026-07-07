# Tasks: MistHelper Hot-Classes Refactor (MistHelper-Only References)

**Feature Directory**: `specs/1013-misthelper-refactor-hot-classes/`
**Design docs consumed**: `spec.md` (47-row Dispatch Queue, FR-001..FR-026, SC-001..SC-017), `plan.md` (Cat A/B action-type split, pinned landing targets, Constitution Check PASS), `research.md` (destination-package rationale, method-parity audit shape, baseline gating).

**Action-type legend** (from spec.md § Dispatch Queue):
- **Cat A — Facade removal**: delete delegation wrapper from `MistHelper.py`, rewire callsites to the `src/` implementation that already exists, no new file created. MUST run method-parity audit (FR-025) before deletion.
- **Cat B — Fresh extraction**: create new file at `src/<subfolder>/<snake_case>.py` with the extracted class body, delete original from `MistHelper.py`, rewire callsites.

**Dispatch ordering** (FR-026, FR-023): the 4 Cat A candidates dispatch first (positions 1-4) as a warmup ahead of the 43 Cat B candidates. Within each block, Refs-ASC / LOC-DESC. Serial per-PR workflow (FR-002): one PR open at a time. Analyzer catalog regenerates after every merge (FR-014) and re-ranks the remaining queue from the fresh output.

**Standard per-PR merge gates** (FR-015 / SC-005):
- Local (`feedback_prepush_black_ruff.md`): `black --check` clean, `ruff check` clean, `python -m py_compile MistHelper.py`, `python MistHelper.py --test` reports **0 failed / exit 0**.
- Analyzer: aggregate compliance ≥ 99.6/A+ (FR-017), new/edited files A+/100 (FR-016), no A+ regression (SC-004), `MistHelper.py` pylint non-regressing (FR-018).
- Remote: 15/15 functional CI jobs green, `mergeStateStatus: CLEAN` (no `--admin` bypass per `feedback_no_admin_bypass.md`).
- Cat A only: method-parity audit output pasted in PR body (FR-025).

**Breadcrumb template** (FR-007, mandatory at every deletion site):

```text
# NOTE: <ClassName> extracted to <new-module-path>::<ClassName>. See specs/1013-misthelper-refactor-hot-classes/spec.md.
```

---

## Phase A — Pre-work (single commit, no PR)

- [ ] T001 Pull fresh `main`; capture pre-initiative pylint baseline for `MistHelper.py` and record in `specs/1013-misthelper-refactor-hot-classes/baseline_pylint.txt` (FR-018 anchor)
- [ ] T002 Regenerate `refactor_candidates.md` on current `main` head via `python -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`; commit alongside the baseline (FR-014 anchor for T003+)
- [ ] T003 Capture pre-initiative aggregate compliance score and per-file compliance snapshot into `specs/1013-misthelper-refactor-hot-classes/baseline_compliance.txt` (SC-003 / SC-004 anchor)
- [ ] T004 Verify SKIP_ALWAYS integrity: `grep -n "GlobalImportManager\|tqdm" tools/refactor_analyzer/**/*.py` confirms both symbols still in the skip-pin set (FR-009 / SC-008 anchor)
- [ ] T005 Verify Hot-source exclusion still applies: `grep -rn "class OrgConfigMigrationManager\|class DeviceUtilityCommands" src/` returns zero matches for any of the 43 Cat B classes (FR-012 / SC-009 anchor)

**Phase A checkpoint**: pre-initiative baselines captured; catalog regenerated; skip-pin integrity confirmed; Hot-source cross-check clean. Phase B (Cat A dispatch) may begin.

---

## Phase B — Cat A dispatch block (positions 1-4)

Cat A candidates are dispatched **first** per FR-026. Each block below is one PR. Serial merge: complete every step of one block before opening the next block's PR (FR-002).

### Position 1 — GatewayTemplateConfigManager (Cat A, 6 refs, 56 LOC)

Facade at `MistHelper.py:15596` delegates to `src/gateway/template_config.py::GatewayTemplateConfigManager`.

- [ ] T010 [P1-Prep] Read facade body at `MistHelper.py:15596-15651` and the `src/gateway/template_config.py::GatewayTemplateConfigManager` counterpart in full; note public surface (methods, static, classmethods, class attrs)
- [ ] T011 [P1-Audit] Run method-parity audit (FR-025): enumerate every public callable/attribute on the facade, confirm each is exposed with signature-equivalent semantics by `src/gateway/template_config.py::GatewayTemplateConfigManager`; capture the audit output verbatim for the PR body's fenced code block
- [ ] T012 [P1-Grep] Run `grep -rn "GatewayTemplateConfigManager" src/ tests/`; confirm zero matches (FR-013). Non-zero → defer per FR-013 and record in spec.md § Deferred Candidates
- [ ] T013 [P1-Rewire] In one commit: (a) delete facade body at `MistHelper.py:15596-15651`, (b) add the FR-007 NOTE breadcrumb at the deletion site pointing at `src/gateway/template_config.py::GatewayTemplateConfigManager`, (c) rewrite all 6 `MistHelper.py` callsites to construct the `src/` class directly (no `_Impl`, no `create()` indirection, no `_configure_module()` helper surviving)
- [ ] T014 [P1-LocalGate] Run local merge gate: `black --check MistHelper.py src/gateway/`, `ruff check MistHelper.py src/gateway/`, `python -m py_compile MistHelper.py`, `python MistHelper.py --test` (must report 0 failed / exit 0)
- [ ] T015 [P1-Compliance] Regenerate analyzer output; verify `src/gateway/template_config.py` still A+/100, aggregate score ≥ 99.6/A+, `MistHelper.py` pylint non-regressing (FR-016 / FR-017 / FR-018)
- [ ] T016 [P1-PR] Open PR titled `refactor(1013): remove GatewayTemplateConfigManager facade (SC-001, position 1)`; paste method-parity audit output into body; push and wait for 15/15 green + mergeStateStatus CLEAN
- [ ] T017 [P1-Merge] Merge PR (no `--admin`); pull `main`; regenerate `refactor_candidates.md` (FR-014); commit refreshed catalog as follow-up doc commit

### Position 2 — FirmwareManager (Cat A, 8 refs, 22 LOC)

Facade at `MistHelper.py:17376` is a factory (`create()` → `_Impl(config)`) delegating to `src/firmware/firmware_manager.py::FirmwareManager`.

- [ ] T020 [P2-Prep] Read facade body at `MistHelper.py:17376-17397` and `src/firmware/firmware_manager.py::FirmwareManager` counterpart; note the `FirmwareManagerConfig` construction pattern used by `create()`
- [ ] T021 [P2-Audit] Method-parity audit (FR-025): enumerate facade `create()` / `_Impl` public surface; confirm `src/` class exposes identical constructor signature and public methods; capture output for PR body
- [ ] T022 [P2-Grep] `grep -rn "FirmwareManager" src/ tests/` filtered against `src/firmware/firmware_manager.py` self-references; confirm zero external Cat A callers (FR-013)
- [ ] T023 [P2-Rewire] Single commit: delete facade body, add FR-007 NOTE breadcrumb, rewrite all 8 callsites to construct `src/firmware/firmware_manager.py::FirmwareManager(FirmwareManagerConfig(...))` directly (no factory `create()` surviving in `MistHelper.py`)
- [ ] T024 [P2-LocalGate] `black --check`, `ruff check`, `py_compile`, `MistHelper.py --test` all clean/0-failed
- [ ] T025 [P2-Compliance] Regenerate; verify `src/firmware/firmware_manager.py` still A+/100, aggregate ≥ 99.6/A+, MistHelper pylint non-regressing
- [ ] T026 [P2-PR] Open PR `refactor(1013): remove FirmwareManager facade (SC-001, position 2)`; paste parity audit; push; wait 15/15 green + CLEAN
- [ ] T027 [P2-Merge] Merge; pull; regenerate `refactor_candidates.md`; commit refreshed catalog

### Position 3 — SiteConfigManager (Cat A, 16 refs, 43 LOC)

Facade at `MistHelper.py:16926` delegates to `src/site/site_config_manager.py::SiteConfigManager`.

- [ ] T030 [P3-Prep] Read facade body at `MistHelper.py:16926-16968` and `src/site/site_config_manager.py::SiteConfigManager`; note public method set
- [ ] T031 [P3-Audit] Method-parity audit (FR-025) capturing every facade-exposed callable; confirm src/ parity; if a facade method is absent from src/, port it into src/ in the same PR OR defer per FR-025(ii)
- [ ] T032 [P3-Grep] `grep -rn "SiteConfigManager" src/ tests/` filtered against `src/site/site_config_manager.py` self-references; zero external matches expected (FR-013)
- [ ] T033 [P3-Rewire] Single commit: delete facade body, add FR-007 NOTE breadcrumb, rewrite all 16 callsites to import `src/site/site_config_manager.py::SiteConfigManager` directly
- [ ] T034 [P3-LocalGate] `black --check`, `ruff check`, `py_compile`, `MistHelper.py --test` all clean/0-failed
- [ ] T035 [P3-Compliance] Regenerate; verify `src/site/site_config_manager.py` still A+/100, aggregate ≥ 99.6/A+, MistHelper pylint non-regressing
- [ ] T036 [P3-PR] Open PR `refactor(1013): remove SiteConfigManager facade (SC-001, position 3)`; paste parity audit; push; wait 15/15 green + CLEAN
- [ ] T037 [P3-Merge] Merge; pull; regenerate `refactor_candidates.md`; commit refreshed catalog

### Position 4 — DeviceUtilityCommands (Cat A, 70 refs, 188 LOC)

Facade at `MistHelper.py:13527` fans out to **35 operation-subclasses** in `src/device/utility_commands.py`. Highest method-parity risk in Cat A per FR-025.

- [ ] T040 [P4-Prep] Read facade body at `MistHelper.py:13527-13714` in full; read `src/device/utility_commands.py` in full including all 35 op-subclasses; produce a written mapping of every facade method → src/ target method
- [ ] T041 [P4-Audit-Exhaustive] Method-parity audit (FR-025, particular rigor per spec.md § Cat A method-parity risk flag): enumerate every one of the 35 op-subclass dispatchers exposed by the facade + every direct method; confirm identical exposure in `src/device/utility_commands.py`; capture full audit output for PR body; if any mismatch exists, port to src/ in the same PR OR defer per FR-025(ii)
- [ ] T042 [P4-Grep] `grep -rn "DeviceUtilityCommands" src/ tests/` filtered against `src/device/utility_commands.py` self-references; zero external matches expected (FR-013)
- [ ] T043 [P4-Rewire] Single commit: delete facade body (all 188 LOC), add FR-007 NOTE breadcrumb, rewrite all 70 callsites (largest Cat A rewire surface) to reference `src/device/utility_commands.py::DeviceUtilityCommands` directly
- [ ] T044 [P4-LocalGate] `black --check`, `ruff check`, `py_compile`, `MistHelper.py --test` all clean/0-failed (higher risk of test-suite exposure given 70 callsites — allocate careful smoke run)
- [ ] T045 [P4-Compliance] Regenerate; verify `src/device/utility_commands.py` still A+/100, aggregate ≥ 99.6/A+, MistHelper pylint non-regressing; expect a visible pylint delta from the 188 LOC drop
- [ ] T046 [P4-PR] Open PR `refactor(1013): remove DeviceUtilityCommands facade + 35 op-subclass rewire (SC-001, position 4)`; paste exhaustive parity audit; push; wait 15/15 green + CLEAN
- [ ] T047 [P4-Merge] Merge; pull; regenerate `refactor_candidates.md`; commit refreshed catalog

**Phase B checkpoint** (SC-001 partial): all 4 Cat A facades removed; method-parity audits recorded in each PR body; no wrapper shims, `_Impl` aliases, or `create()` factories survive in `MistHelper.py`. Phase C (Cat B) may begin.

---

## Phase C — Cat B fresh-extraction block (positions 5-47)

Each Cat B candidate below is one PR. Per candidate, the workflow is: pre-flight read → external-caller grep audit (FR-013) → new-file creation with class body + in-flight `guideline_flags` remediation (FR-006) → callsite rewire + FR-007 NOTE breadcrumb (single commit) → local gate → analyzer regen → PR + CI wait → merge → catalog refresh (FR-014). All same-position tasks form one PR; do not batch across positions (FR-002).

### Position 5 — OrgConfigMigrationManager (4 refs, 675 LOC → `src/org/`)

- [ ] T050 [P5] Pre-flight: read class body at `MistHelper.py`, enumerate `guideline_flags` from analyzer output (expect `oversize_25_lines` on a 675-LoC class); `grep -rn "OrgConfigMigrationManager" src/ tests/` = 0 (FR-013)
- [ ] T051 [P5] Create `src/org/org_config_migration_manager.py` with the extracted class body; decompose every > 25-line method into ≤ 25-line helpers, add `logging.info`/`logging.debug` envelopes with `%s` formatting, ASCII-only log literals, `pathlib.Path` for filesystem ops, `InputUtils.safe_input()` for any interactive input (FR-006, FR-008)
- [ ] T052 [P5] Single commit: delete class body from `MistHelper.py`, add FR-007 NOTE breadcrumb, rewrite all 4 callsites to import from `src/org/org_config_migration_manager.py`
- [ ] T053 [P5] Local gate: `black --check`, `ruff check`, `py_compile`, `MistHelper.py --test` (0 failed / exit 0)
- [ ] T054 [P5] Analyzer regen: new file A+/100, no A+ regression, aggregate ≥ 99.6/A+, MistHelper pylint non-regressing
- [ ] T055 [P5] Open PR `refactor(1013): extract OrgConfigMigrationManager to src/org/ (SC-001, position 5)`; push; wait 15/15 green + CLEAN; merge; regenerate `refactor_candidates.md`

### Position 6 — DeviceUtils (4 refs, 97 LOC → `src/device/`)

- [ ] T060 [P6] Pre-flight read + `grep -rn "class DeviceUtils\b" src/ tests/` = 0 (FR-013); watch for name collision with any existing `DeviceUtils` at destination (E-5)
- [ ] T061 [P6] Create `src/device/device_utils.py` (or fold into existing device utility class if E-5 collision) with extracted body + in-flight guideline_flag remediation (FR-006 / FR-008)
- [ ] T062 [P6] Single commit: delete from `MistHelper.py`, add FR-007 breadcrumb, rewire all 4 callsites
- [ ] T063 [P6] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T064 [P6] Analyzer regen: A+/100 new file, no A+ regression, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T065 [P6] Open PR (SC-001, position 6); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 7 — SelfExportUtils (4 refs, 40 LOC → `src/export/`)

- [ ] T070 [P7] Pre-flight read + `grep -rn "class SelfExportUtils" src/ tests/` = 0 (FR-013)
- [ ] T071 [P7] Create `src/export/self_export_utils.py` with class body + guideline_flag remediation
- [ ] T072 [P7] Single commit: delete, breadcrumb, rewire 4 callsites
- [ ] T073 [P7] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T074 [P7] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T075 [P7] Open PR (SC-001, position 7); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 8 — MSPInventoryExporter (5 refs, 386 LOC → `src/export/`)

- [ ] T080 [P8] Pre-flight read; enumerate `oversize_25_lines` flags on 386-LOC class; `grep -rn "class MSPInventoryExporter" src/ tests/` = 0 (FR-013)
- [ ] T081 [P8] Create `src/export/msp_inventory_exporter.py` with class body + method decomposition to ≤ 25 lines + full FR-006/FR-008 remediation
- [ ] T082 [P8] Single commit: delete, breadcrumb, rewire 5 callsites
- [ ] T083 [P8] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T084 [P8] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing (expect visible LOC delta)
- [ ] T085 [P8] Open PR (SC-001, position 8); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 9 — TelemetryEmitter (5 refs, 214 LOC → `src/analytics/`)

- [ ] T090 [P9] Pre-flight read + `grep -rn "class TelemetryEmitter" src/ tests/` = 0 (FR-013)
- [ ] T091 [P9] Create `src/analytics/telemetry_emitter.py` with class body + guideline_flag remediation
- [ ] T092 [P9] Single commit: delete, breadcrumb, rewire 5 callsites
- [ ] T093 [P9] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T094 [P9] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T095 [P9] Open PR (SC-001, position 9); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 10 — InteractiveDisplayUtils (8 refs, 72 LOC → `src/ui/`)

- [ ] T100 [P10] Pre-flight read + `grep -rn "class InteractiveDisplayUtils" src/ tests/` = 0 (FR-013)
- [ ] T101 [P10] Create `src/ui/interactive_display_utils.py` with class body + guideline_flag remediation
- [ ] T102 [P10] Single commit: delete, breadcrumb, rewire 8 callsites
- [ ] T103 [P10] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T104 [P10] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T105 [P10] Open PR (SC-001, position 10); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 11 — DisplayUtils (8 refs, 70 LOC → `src/ui/`)

- [ ] T110 [P11] Pre-flight read + `grep -rn "class DisplayUtils\b" src/ tests/` = 0 (FR-013); watch for name collision with any existing `DisplayUtils` at destination (E-5)
- [ ] T111 [P11] Create `src/ui/display_utils.py` (or fold if collision per E-5) with class body + guideline_flag remediation
- [ ] T112 [P11] Single commit: delete, breadcrumb, rewire 8 callsites
- [ ] T113 [P11] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T114 [P11] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T115 [P11] Open PR (SC-001, position 11); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 12 — AuditAnalysisOps (8 refs, 66 LOC → `src/audit/`)

- [ ] T120 [P12] Pre-flight read + `grep -rn "class AuditAnalysisOps" src/ tests/` = 0 (FR-013); confirm `src/audit/` package exists or create `__init__.py` as part of this PR
- [ ] T121 [P12] Create `src/audit/audit_analysis_ops.py` with class body + guideline_flag remediation
- [ ] T122 [P12] Single commit: delete, breadcrumb, rewire 8 callsites
- [ ] T123 [P12] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T124 [P12] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T125 [P12] Open PR (SC-001, position 12); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 13 — OperationRegistry (9 refs, 461 LOC → `src/utils/`)

- [ ] T130 [P13] Pre-flight read; enumerate `oversize_25_lines` on 461-LOC class; `grep -rn "class OperationRegistry" src/ tests/` = 0 (FR-013)
- [ ] T131 [P13] Create `src/utils/operation_registry.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T132 [P13] Single commit: delete, breadcrumb, rewire 9 callsites
- [ ] T133 [P13] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T134 [P13] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T135 [P13] Open PR (SC-001, position 13); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 14 — SiteClientExporter (10 refs, 85 LOC → `src/export/`)

- [ ] T140 [P14] Pre-flight read + `grep -rn "class SiteClientExporter" src/ tests/` = 0 (FR-013)
- [ ] T141 [P14] Create `src/export/site_client_exporter.py` with class body + guideline_flag remediation
- [ ] T142 [P14] Single commit: delete, breadcrumb, rewire 10 callsites
- [ ] T143 [P14] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T144 [P14] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T145 [P14] Open PR (SC-001, position 14); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 15 — BulkRadiusWLANConfigManager (13 refs, 587 LOC → `src/site/`)

- [ ] T150 [P15] Pre-flight read; enumerate `oversize_25_lines` on 587-LOC class; `grep -rn "class BulkRadiusWLANConfigManager" src/ tests/` = 0 (FR-013)
- [ ] T151 [P15] Create `src/site/bulk_radius_wlan_config_manager.py` with class body + heavy method decomposition + FR-006/FR-008 remediation
- [ ] T152 [P15] Single commit: delete, breadcrumb, rewire 13 callsites
- [ ] T153 [P15] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T154 [P15] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T155 [P15] Open PR (SC-001, position 15); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 16 — EndpointConfig (13 refs, 10 LOC → `src/dataclasses/`)

- [ ] T160 [P16] Pre-flight read + `grep -rn "class EndpointConfig" src/ tests/` = 0 (FR-013); confirm `src/dataclasses/` exists or create `__init__.py`
- [ ] T161 [P16] Create `src/dataclasses/endpoint_config.py` with dataclass body (trivial 10 LOC) + FR-008 non-negotiables
- [ ] T162 [P16] Single commit: delete, breadcrumb, rewire 13 callsites
- [ ] T163 [P16] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T164 [P16] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T165 [P16] Open PR (SC-001, position 16); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 17 — ConstDefinitionsExporter (14 refs, 759 LOC → `src/export/`)

Largest single-file candidate in the queue. Expect heavy `oversize_25_lines` decomposition (E-2, E-10).

- [ ] T170 [P17] Pre-flight read; enumerate all `guideline_flags` on 759-LOC class; `grep -rn "class ConstDefinitionsExporter" src/ tests/` = 0 (FR-013)
- [ ] T171 [P17] Create `src/export/const_definitions_exporter.py` with class body + exhaustive method decomposition (every method ≤ 25 lines, ≤ 5 params) + full FR-006/FR-008 remediation
- [ ] T172 [P17] Single commit: delete, breadcrumb, rewire 14 callsites
- [ ] T173 [P17] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T174 [P17] Analyzer regen: A+/100 new file (critical — largest surface), aggregate ≥ 99.6/A+, pylint non-regressing (expect largest LOC delta of the initiative)
- [ ] T175 [P17] Open PR (SC-001, position 17); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 18 — OrgAlarmEventExporter (14 refs, 129 LOC → `src/export/`)

- [ ] T180 [P18] Pre-flight read + `grep -rn "class OrgAlarmEventExporter" src/ tests/` = 0 (FR-013)
- [ ] T181 [P18] Create `src/export/org_alarm_event_exporter.py` with class body + guideline_flag remediation
- [ ] T182 [P18] Single commit: delete, breadcrumb, rewire 14 callsites
- [ ] T183 [P18] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T184 [P18] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T185 [P18] Open PR (SC-001, position 18); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 19 — SiteConfigExporter (14 refs, 100 LOC → `src/export/`)

- [ ] T190 [P19] Pre-flight read + `grep -rn "class SiteConfigExporter" src/ tests/` = 0 (FR-013)
- [ ] T191 [P19] Create `src/export/site_config_exporter.py` with class body + guideline_flag remediation
- [ ] T192 [P19] Single commit: delete, breadcrumb, rewire 14 callsites
- [ ] T193 [P19] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T194 [P19] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T195 [P19] Open PR (SC-001, position 19); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 20 — OrgAdminExporter (14 refs, 94 LOC → `src/export/`)

- [ ] T200 [P20] Pre-flight read + `grep -rn "class OrgAdminExporter" src/ tests/` = 0 (FR-013)
- [ ] T201 [P20] Create `src/export/org_admin_exporter.py` with class body + guideline_flag remediation
- [ ] T202 [P20] Single commit: delete, breadcrumb, rewire 14 callsites
- [ ] T203 [P20] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T204 [P20] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T205 [P20] Open PR (SC-001, position 20); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 21 — APIDataFetcher (16 refs, 328 LOC → `src/api/`)

- [ ] T210 [P21] Pre-flight read; enumerate `oversize_25_lines` on 328-LOC class; `grep -rn "class APIDataFetcher" src/ tests/` = 0 (FR-013); confirm `src/api/` package exists
- [ ] T211 [P21] Create `src/api/api_data_fetcher.py` with class body + method decomposition + FR-006/FR-008 remediation
- [ ] T212 [P21] Single commit: delete, breadcrumb, rewire 16 callsites
- [ ] T213 [P21] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T214 [P21] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T215 [P21] Open PR (SC-001, position 21); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 22 — OrgTemplateExporter (18 refs, 144 LOC → `src/export/`)

- [ ] T220 [P22] Pre-flight read + `grep -rn "class OrgTemplateExporter" src/ tests/` = 0 (FR-013)
- [ ] T221 [P22] Create `src/export/org_template_exporter.py` with class body + guideline_flag remediation
- [ ] T222 [P22] Single commit: delete, breadcrumb, rewire 18 callsites
- [ ] T223 [P22] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T224 [P22] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T225 [P22] Open PR (SC-001, position 22); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 23 — GatewayHaExporter (18 refs, 139 LOC → `src/export/`)

- [ ] T230 [P23] Pre-flight read + `grep -rn "class GatewayHaExporter" src/ tests/` = 0 (FR-013)
- [ ] T231 [P23] Create `src/export/gateway_ha_exporter.py` with class body + guideline_flag remediation
- [ ] T232 [P23] Single commit: delete, breadcrumb, rewire 18 callsites
- [ ] T233 [P23] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T234 [P23] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T235 [P23] Open PR (SC-001, position 23); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 24 — LicenseExportUtils (20 refs, 168 LOC → `src/export/`)

- [ ] T240 [P24] Pre-flight read + `grep -rn "class LicenseExportUtils" src/ tests/` = 0 (FR-013)
- [ ] T241 [P24] Create `src/export/license_export_utils.py` with class body + guideline_flag remediation
- [ ] T242 [P24] Single commit: delete, breadcrumb, rewire 20 callsites
- [ ] T243 [P24] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T244 [P24] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T245 [P24] Open PR (SC-001, position 24); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 25 — DataCollectionManager (20 refs, 156 LOC → `src/analytics/`)

- [ ] T250 [P25] Pre-flight read + `grep -rn "class DataCollectionManager" src/ tests/` = 0 (FR-013)
- [ ] T251 [P25] Create `src/analytics/data_collection_manager.py` with class body + guideline_flag remediation
- [ ] T252 [P25] Single commit: delete, breadcrumb, rewire 20 callsites
- [ ] T253 [P25] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T254 [P25] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T255 [P25] Open PR (SC-001, position 25); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 26 — WiredClientManufacturerReportGenerator (20 refs, 129 LOC → `src/reports/`)

- [ ] T260 [P26] Pre-flight read + `grep -rn "class WiredClientManufacturerReportGenerator" src/ tests/` = 0 (FR-013)
- [ ] T261 [P26] Create `src/reports/wired_client_manufacturer_report_generator.py` with class body + guideline_flag remediation
- [ ] T262 [P26] Single commit: delete, breadcrumb, rewire 20 callsites
- [ ] T263 [P26] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T264 [P26] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T265 [P26] Open PR (SC-001, position 26); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 27 — SFPTransceiverDataProcessor (22 refs, 180 LOC → `src/reports/`)

- [ ] T270 [P27] Pre-flight read + `grep -rn "class SFPTransceiverDataProcessor" src/ tests/` = 0 (FR-013)
- [ ] T271 [P27] Create `src/reports/sfp_transceiver_data_processor.py` with class body + guideline_flag remediation
- [ ] T272 [P27] Single commit: delete, breadcrumb, rewire 22 callsites
- [ ] T273 [P27] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T274 [P27] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T275 [P27] Open PR (SC-001, position 27); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 28 — SitesByAPModelExporter (22 refs, 146 LOC → `src/export/`)

- [ ] T280 [P28] Pre-flight read + `grep -rn "class SitesByAPModelExporter" src/ tests/` = 0 (FR-013)
- [ ] T281 [P28] Create `src/export/sites_by_ap_model_exporter.py` with class body + guideline_flag remediation
- [ ] T282 [P28] Single commit: delete, breadcrumb, rewire 22 callsites
- [ ] T283 [P28] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T284 [P28] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T285 [P28] Open PR (SC-001, position 28); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 29 — OrgDeviceInventorySummary (22 refs, 69 LOC → `src/inventory/`)

- [ ] T290 [P29] Pre-flight read + `grep -rn "class OrgDeviceInventorySummary" src/ tests/` = 0 (FR-013); confirm `src/inventory/` exists or create `__init__.py`
- [ ] T291 [P29] Create `src/inventory/org_device_inventory_summary.py` with class body + guideline_flag remediation
- [ ] T292 [P29] Single commit: delete, breadcrumb, rewire 22 callsites
- [ ] T293 [P29] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T294 [P29] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T295 [P29] Open PR (SC-001, position 29); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 30 — CLIShellManager (23 refs, 161 LOC → `src/ssh/`)

- [ ] T300 [P30] Pre-flight read + `grep -rn "class CLIShellManager" src/ tests/` = 0 (FR-013)
- [ ] T301 [P30] Create `src/ssh/cli_shell_manager.py` with class body + guideline_flag remediation
- [ ] T302 [P30] Single commit: delete, breadcrumb, rewire 23 callsites
- [ ] T303 [P30] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T304 [P30] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T305 [P30] Open PR (SC-001, position 30); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 31 — OrgConfigExporter (24 refs, 168 LOC → `src/export/`)

Watch for internal sprawl per E-10 despite modest advertised LOC.

- [ ] T310 [P31] Pre-flight read; enumerate `oversize_25_lines` on likely-sprawling class; `grep -rn "class OrgConfigExporter" src/ tests/` = 0 (FR-013)
- [ ] T311 [P31] Create `src/export/org_config_exporter.py` with class body + method decomposition + FR-006/FR-008 remediation
- [ ] T312 [P31] Single commit: delete, breadcrumb, rewire 24 callsites
- [ ] T313 [P31] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T314 [P31] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T315 [P31] Open PR (SC-001, position 31); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 32 — OrgClientSecurityExporter (26 refs, 162 LOC → `src/export/`)

- [ ] T320 [P32] Pre-flight read + `grep -rn "class OrgClientSecurityExporter" src/ tests/` = 0 (FR-013)
- [ ] T321 [P32] Create `src/export/org_client_security_exporter.py` with class body + guideline_flag remediation
- [ ] T322 [P32] Single commit: delete, breadcrumb, rewire 26 callsites
- [ ] T323 [P32] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T324 [P32] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T325 [P32] Open PR (SC-001, position 32); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 33 — EnvironmentUtils (28 refs, 114 LOC → `src/utils/`)

- [ ] T330 [P33] Pre-flight read + `grep -rn "class EnvironmentUtils" src/ tests/` = 0 (FR-013)
- [ ] T331 [P33] Create `src/utils/environment_utils.py` with class body + guideline_flag remediation
- [ ] T332 [P33] Single commit: delete, breadcrumb, rewire 28 callsites
- [ ] T333 [P33] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T334 [P33] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T335 [P33] Open PR (SC-001, position 33); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 34 — SiteDeviceExporter (30 refs, 203 LOC → `src/export/`)

- [ ] T340 [P34] Pre-flight read + `grep -rn "class SiteDeviceExporter" src/ tests/` = 0 (FR-013)
- [ ] T341 [P34] Create `src/export/site_device_exporter.py` with class body + guideline_flag remediation
- [ ] T342 [P34] Single commit: delete, breadcrumb, rewire 30 callsites
- [ ] T343 [P34] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T344 [P34] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T345 [P34] Open PR (SC-001, position 34); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 35 — PromptClientUtils (31 refs, 210 LOC → `src/input/`)

- [ ] T350 [P35] Pre-flight read + `grep -rn "class PromptClientUtils" src/ tests/` = 0 (FR-013); confirm `src/input/` exists or create `__init__.py`
- [ ] T351 [P35] Create `src/input/prompt_client_utils.py` with class body + `InputUtils.safe_input()` in place of any raw `input()` + full FR-006/FR-008 remediation
- [ ] T352 [P35] Single commit: delete, breadcrumb, rewire 31 callsites
- [ ] T353 [P35] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T354 [P35] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T355 [P35] Open PR (SC-001, position 35); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 36 — GlobalWiredClientReportGenerator (32 refs, 251 LOC → `src/reports/`)

- [ ] T360 [P36] Pre-flight read + `grep -rn "class GlobalWiredClientReportGenerator" src/ tests/` = 0 (FR-013)
- [ ] T361 [P36] Create `src/reports/global_wired_client_report_generator.py` with class body + method decomposition + FR-006/FR-008 remediation
- [ ] T362 [P36] Single commit: delete, breadcrumb, rewire 32 callsites
- [ ] T363 [P36] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T364 [P36] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T365 [P36] Open PR (SC-001, position 36); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 37 — GatewayTestExporter (34 refs, 245 LOC → `src/export/`)

- [ ] T370 [P37] Pre-flight read + `grep -rn "class GatewayTestExporter" src/ tests/` = 0 (FR-013)
- [ ] T371 [P37] Create `src/export/gateway_test_exporter.py` with class body + guideline_flag remediation
- [ ] T372 [P37] Single commit: delete, breadcrumb, rewire 34 callsites
- [ ] T373 [P37] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T374 [P37] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T375 [P37] Open PR (SC-001, position 37); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 38 — DatabaseSchemaUtils (34 refs, 179 LOC → `src/db/`)

- [ ] T380 [P38] Pre-flight read + `grep -rn "class DatabaseSchemaUtils" src/ tests/` = 0 (FR-013); confirm `src/db/` exists or create `__init__.py`
- [ ] T381 [P38] Create `src/db/database_schema_utils.py` with class body + guideline_flag remediation
- [ ] T382 [P38] Single commit: delete, breadcrumb, rewire 34 callsites
- [ ] T383 [P38] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T384 [P38] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T385 [P38] Open PR (SC-001, position 38); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 39 — TroubleshootUtils (36 refs, 127 LOC → `src/troubleshooting/`)

- [ ] T390 [P39] Pre-flight read + `grep -rn "class TroubleshootUtils" src/ tests/` = 0 (FR-013); confirm `src/troubleshooting/` exists or create `__init__.py`
- [ ] T391 [P39] Create `src/troubleshooting/troubleshoot_utils.py` with class body + guideline_flag remediation
- [ ] T392 [P39] Single commit: delete, breadcrumb, rewire 36 callsites
- [ ] T393 [P39] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T394 [P39] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T395 [P39] Open PR (SC-001, position 39); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 40 — FilterOperatorEngine (37 refs, 110 LOC → `src/utils/`)

- [ ] T400 [P40] Pre-flight read + `grep -rn "class FilterOperatorEngine" src/ tests/` = 0 (FR-013)
- [ ] T401 [P40] Create `src/utils/filter_operator_engine.py` with class body + guideline_flag remediation
- [ ] T402 [P40] Single commit: delete, breadcrumb, rewire 37 callsites
- [ ] T403 [P40] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T404 [P40] Analyzer regen: A+/100, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T405 [P40] Open PR (SC-001, position 40); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 41 — DeviceRebootManager (46 refs, 396 LOC → `src/device/`)

Large candidate per E-10; heavy decomposition expected.

- [ ] T410 [P41] Pre-flight read; enumerate `oversize_25_lines` on 396-LOC class; `grep -rn "class DeviceRebootManager" src/ tests/` = 0 (FR-013)
- [ ] T411 [P41] Create `src/device/device_reboot_manager.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T412 [P41] Single commit: delete, breadcrumb, rewire 46 callsites
- [ ] T413 [P41] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T414 [P41] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T415 [P41] Open PR (SC-001, position 41); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 42 — ARPCommandManager (46 refs, 289 LOC → `src/device/`)

- [ ] T420 [P42] Pre-flight read + `grep -rn "class ARPCommandManager" src/ tests/` = 0 (FR-013)
- [ ] T421 [P42] Create `src/device/arp_command_manager.py` with class body + method decomposition + FR-006/FR-008 remediation
- [ ] T422 [P42] Single commit: delete, breadcrumb, rewire 46 callsites
- [ ] T423 [P42] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T424 [P42] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T425 [P42] Open PR (SC-001, position 42); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 43 — SiteAnomalyExporter (54 refs, 341 LOC → `src/export/`)

- [ ] T430 [P43] Pre-flight read; enumerate `oversize_25_lines` on 341-LOC class; `grep -rn "class SiteAnomalyExporter" src/ tests/` = 0 (FR-013)
- [ ] T431 [P43] Create `src/export/site_anomaly_exporter.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T432 [P43] Single commit: delete, breadcrumb, rewire 54 callsites
- [ ] T433 [P43] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T434 [P43] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T435 [P43] Open PR (SC-001, position 43); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 44 — OfflineDeviceReporter (54 refs, 273 LOC → `src/reports/`)

- [ ] T440 [P44] Pre-flight read + `grep -rn "class OfflineDeviceReporter" src/ tests/` = 0 (FR-013)
- [ ] T441 [P44] Create `src/reports/offline_device_reporter.py` with class body + method decomposition + FR-006/FR-008 remediation
- [ ] T442 [P44] Single commit: delete, breadcrumb, rewire 54 callsites
- [ ] T443 [P44] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T444 [P44] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T445 [P44] Open PR (SC-001, position 44); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 45 — OrgDeviceStatsExporter (58 refs, 414 LOC → `src/export/`)

Large candidate per E-10; heavy decomposition expected.

- [ ] T450 [P45] Pre-flight read; enumerate `oversize_25_lines` on 414-LOC class; `grep -rn "class OrgDeviceStatsExporter" src/ tests/` = 0 (FR-013)
- [ ] T451 [P45] Create `src/export/org_device_stats_exporter.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T452 [P45] Single commit: delete, breadcrumb, rewire 58 callsites
- [ ] T453 [P45] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T454 [P45] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T455 [P45] Open PR (SC-001, position 45); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 46 — OrgTicketManager (66 refs, 475 LOC → `src/org/`)

Large candidate per E-10; second-largest callsite fan-out (66) in Cat B.

- [ ] T460 [P46] Pre-flight read; enumerate `oversize_25_lines` on 475-LOC class; `grep -rn "class OrgTicketManager" src/ tests/` = 0 (FR-013)
- [ ] T461 [P46] Create `src/org/org_ticket_manager.py` with class body + heavy method decomposition + full FR-006/FR-008 remediation
- [ ] T462 [P46] Single commit: delete, breadcrumb, rewire 66 callsites (highest Cat B fan-out to date — allocate careful review)
- [ ] T463 [P46] Local gate: black, ruff, py_compile, `--test` 0-failed
- [ ] T464 [P46] Analyzer regen: A+/100 new file, aggregate ≥ 99.6/A+, pylint non-regressing
- [ ] T465 [P46] Open PR (SC-001, position 46); push; wait 15/15 green + CLEAN; merge; regenerate catalog

### Position 47 — OrgExportUtils (128 refs, 653 LOC → `src/export/`)

Terminal candidate — largest callsite fan-out (128) and second-largest LOC (653) in the queue. E-10 heavy-decomposition profile applies.

- [ ] T470 [P47] Pre-flight read; enumerate every `guideline_flag` on 653-LOC class; `grep -rn "class OrgExportUtils" src/ tests/` = 0 (FR-013)
- [ ] T471 [P47] Create `src/export/org_export_utils.py` with class body + exhaustive method decomposition (every method ≤ 25 lines, ≤ 5 params) + full FR-006/FR-008 remediation
- [ ] T472 [P47] Single commit: delete, breadcrumb, rewire all 128 callsites (largest single rewire surface in the initiative — allocate meticulous review and consider a dry-run compile check on a scratch branch first)
- [ ] T473 [P47] Local gate: black, ruff, py_compile, `--test` 0-failed (critical smoke run — this PR closes the initiative's operational body)
- [ ] T474 [P47] Analyzer regen: A+/100 new file (largest surface — hardest single A+ target), aggregate ≥ 99.6/A+, pylint non-regressing (expect the largest single-PR pylint delta of the initiative)
- [ ] T475 [P47] Open PR `refactor(1013): extract OrgExportUtils to src/export/ (SC-001, position 47 — final Cat B)`; push; wait 15/15 green + CLEAN; merge; regenerate catalog

**Phase C checkpoint** (SC-001 complete for non-deferred candidates): all 43 Cat B extractions merged (or recorded as deferred with rationale). Phase D closeout begins.

---

## Phase D — Closeout & aggregate verification

- [ ] T500 Verify SC-001: freshest `refactor_candidates.md` reports zero of the 47 Dispatch Queue classes in the Hot bucket (or each remaining entry is listed in spec.md § Deferred Candidates with rationale)
- [ ] T501 Verify SC-002: `MistHelper.py` LOC drop ≥ 8,000 relative to `baseline_pylint.txt` LOC captured in T001
- [ ] T502 Verify SC-003 / SC-004: aggregate compliance ≥ 99.6/A+ at every intermediate `main` state (walkable via merged-PR sequence); zero previously-A+ files regressed
- [ ] T503 Verify SC-005: every merged PR had 15/15 green + `mergeStateStatus: CLEAN` + `black --check` clean + `ruff check` clean + `python MistHelper.py --test` 0-failed / exit 0; zero `--admin` bypasses except where root-cause-documented
- [ ] T504 Verify SC-006: every new file created during the initiative scores A+/100 on compliance (`python tools/refactor_analyzer` reports A+/100 for each Cat B new file listed in spec.md § Dispatch Queue landing-target column)
- [ ] T505 Verify SC-007: `grep -n "class .* = " MistHelper.py` shows zero wrapper shims / re-export aliases attributable to this initiative
- [ ] T506 Verify SC-008: SKIP_ALWAYS integrity — `GlobalImportManager` and `tqdm` unmodified across the initiative
- [ ] T507 Verify SC-009: zero out-of-scope Hot-bucket classes extracted (the 29 excluded remain deferred)
- [ ] T508 Verify SC-010: catalog regeneration recorded after every merge — walkable via commit history
- [ ] T509 Verify SC-011: zero forward-carried `guideline_flags` on any extracted class
- [ ] T510 Verify SC-012: NOTE breadcrumb present at every deletion site — `grep -c "# NOTE: .* extracted to" MistHelper.py` matches merged-PR count
- [ ] T511 Verify SC-013: pre-push local-gate discipline maintained across the branch history
- [ ] T512 Verify SC-014: dispatch order matched Refs-ASC / LOC-DESC from the freshest catalog at each step (Cat A block first per FR-026, then Cat B block)
- [ ] T513 Verify SC-015: `MistHelper.py` pylint non-regressing vs `baseline_pylint.txt`
- [ ] T514 Verify SC-016: zero new SKIPPED conditionals introduced by any initiative PR
- [ ] T515 Regenerate `refactor_candidates.md` one last time on final `main` head; verify Hot-bucket count = original (76) - extracted count - deferred count; commit the terminal catalog snapshot
- [ ] T516 [Closeout PR] SC-017 — Open a docs-only PR (or extend the position-47 PR body) recording: (a) count of PRs merged (target 47), (b) final `MistHelper.py` LoC + pylint score, (c) final aggregate compliance score, (d) list of deferred candidates with rationale, (e) count of remaining Hot-bucket classes (target ~ 29 + any deferred); merge to close initiative 1013

---

## Dependencies

- **Phase A** (T001-T005) → gates Phase B (T010-T047). Phase A commits go direct to `main` (no PR); Phase B onwards is per-PR.
- **Phase B block ordering** (FR-026, mandatory Cat A-first): T010-T017 (P1) → T020-T027 (P2) → T030-T037 (P3) → T040-T047 (P4). No Cat B PR opens until all four Cat A merges land.
- **Phase C sequential ordering** (FR-002, FR-023): position N's PR (T050 + subsequent 5 tasks) must merge before position N+1's PR opens. Deferral (FR-013/FR-020) advances the next position without opening the deferred PR.
- **Per-candidate internal ordering** (within a single position's task block): pre-flight → grep audit → module creation (Cat B only) or method-parity audit (Cat A only) → single-commit delete+rewire+breadcrumb → local gate → analyzer regen → PR open → CI wait → merge → catalog refresh.
- **Phase D** (T500-T516) runs only after position 47 merges (T475). T516 is the initiative closeout doc commit.

## Parallel Opportunities

- **Zero cross-PR parallelism**: FR-002 mandates one open PR at a time. No two positions may be under PR simultaneously.
- **Within a candidate block**, the pre-flight tasks (read def-site, grep audit, module scaffold if Cat B) may run in parallel by a single contributor at branch time, but the single delete+rewire+breadcrumb commit is atomic and non-parallelizable.
- **Cat A method-parity audit** (T011, T021, T031, T041) MAY be conducted concurrently for all four Cat A candidates as advance research *before* opening any PR; the actual PR sequence remains strictly serial.

## Implementation Strategy

1. **Cat A warmup (FR-026)**: complete positions 1-4 first. These are low-risk facade deletions (the src/ implementation already exists and is CI-proven). Use this block to validate the initiative's rewire discipline and CI cycle time before the fresh-extraction workflow begins.
2. **Cat B by ascending refs**: positions 5-47 dispatch in Refs-ASC / LOC-DESC order from the freshest catalog. Small-refs candidates (4-9 refs) exercise the extraction shape against a small callsite fan-out before the workflow scales to the 46-128-refs tail.
3. **Method-parity audit rigor scales with facade breadth**: allocate extra prep time for position 4 (`DeviceUtilityCommands`, 35 op-subclasses) — this is the highest single-PR method-parity risk in the initiative.
4. **Heavy-decomposition candidates** (positions 5, 8, 13, 15, 17, 21, 41, 42, 43, 44, 45, 46, 47) MUST decompose in-flight (E-2, E-10, FR-006). Allocate meaningful engineering time for these — 675/759/587/653 LOC classes cannot land as monolithic method blocks and hit A+/100.
5. **Terminal-candidate risk (position 47)**: `OrgExportUtils` at 128 refs / 653 LOC is the initiative's final and most complex PR. Consider a scratch-branch dry-run compile check before the actual rewire commit.
6. **Analyzer regeneration is mandatory after every merge (FR-014)**: skipping the regen means the next dispatch is derived from stale ref counts and may re-order incorrectly per SC-014.
7. **Deferral is a legitimate outcome (FR-013, FR-020)**: a candidate that surfaces an external `src/` caller mid-initiative is deferred, not force-extracted. Deferrals are recorded in spec.md § Deferred Candidates and reduce the merged-PR count below 47 (see SC-017(a)).

## Format Validation

Every task above follows the strict checklist format: `- [ ] T### [Story?] Description with file path`. Task IDs are T001..T005 (5 pre-work tasks), T010..T047 (Cat A block, 32 tasks across 4 positions × 8 tasks each), T050..T475 (Cat B block, 258 tasks across 43 positions × 6 tasks each), and T500..T516 (17 closeout tasks). Total: **312 tasks**. Story-label convention: `[P#]` where # is dispatch position (1-47), used as a candidate-block identifier rather than a P1/P2/P3 story priority (all dispatch tasks are effectively equal-priority US1 per spec.md § User Story 1).
