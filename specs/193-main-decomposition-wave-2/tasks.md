# Tasks: Main file decomposition wave 2 (serial, hard-gated)

**Input**: Design documents from `/specs/193-main-decomposition-wave-2/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/serial-decomposition-contract.md`, `quickstart.md`

**Tests**: Required by spec for every phase (unit/integration/parity/risk-control checks)

**Organization**: Strict serial execution by phase (1 through 9). No parallel decomposition tasks are allowed in this wave.

## Phase 0: Scope Guard + Serial Gate Policy (US1)

**Goal**: Lock the wave scope and hard-gate behavior before any extraction work starts.
**Independent Test**: Scope guard checklist exists and is acknowledged before Phase 1.

- [ ] T000 [US1] Record explicit out-of-scope guard in `specs/193-main-decomposition-wave-2/checklists/scope-guard.md` confirming `GlobalImportManager` is excluded from this wave and must not be modified except import rewiring strictly required by moved classes
- [ ] T000A [US1] Record hard-gate remediation policy in `specs/193-main-decomposition-wave-2/checklists/scope-guard.md`: any failed validation/parity/import/runtime check must be remediated in-phase and re-run to pass before signoff
- [ ] T000B [US1] Create shared import-cycle gate test `tests/contract/test_import_graph.py` with assertions covering extracted module boundaries and one-way layering (`MistHelper.py` orchestrator -> `src/*` modules)
- [ ] T000C [US1] Create shared runtime coupling gate harness `tests/integration/test_runtime_coupling.py` with phase-selectable fixtures/profiles (`phase_1` through `phase_9`)
- [ ] T000D [US2] Create deterministic parity contract at `specs/193-main-decomposition-wave-2/contracts/parity-contract.md` defining baseline sources, normalization rules, comparison dimensions, and fail criteria
- [ ] T000E [US2] Capture pre-refactor parity baseline artifacts for all targeted menu/API/backend paths in `specs/193-main-decomposition-wave-2/checklists/parity-baseline/`
---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Omitted in this plan because decomposition tasks are intentionally serial
- **[Story]**: `[US1]` serial decomposition control, `[US2]` parity preservation, `[US3]` final documentation integrity
- Every task includes explicit file paths

## Phase 1: SiteInventoryHealthAnalyzer + SiteAnalyticsConfigurator (US1/US2)

**Goal**: Extract easiest analytics cluster with zero behavior drift.
**Independent Test**: Menu `7` and `169` execute with parity and all phase gates are green.

- [x] T001 [US1] Extract `SiteInventoryHealthAnalyzer` from `MistHelper.py` into `src/analytics/site_inventory_health_analyzer.py`
- [x] T002 [US1] Extract `SiteAnalyticsConfigurator` from `MistHelper.py` into `src/analytics/site_analytics_configurator.py` and keep only orchestration/delegation in `MistHelper.py`
- [x] T003 [US1] Add or update analytics unit tests in `tests/unit/analytics/test_site_inventory_health_analyzer.py` and `tests/unit/analytics/test_site_analytics_configurator.py`
- [x] T004 [US1] Run mandatory automated validation for Phase 1 (`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `python MistHelper.py --test`) and record output in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md`
- [x] T004A [US1] Verify constitution compliance for Phase 1 changed code (inline comments on all changed executable lines + action logging before/after meaningful actions) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md`
- [ ] T004B [US1] Execute full deployment pipeline for Phase 1 changes (commit/push, CI wait, container image pull, container restart, runtime verification) and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md`
- [x] T005 [US2] Execute menu behavior parity checks for impacted operations (`7`, `169`) and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-1-menu-parity.md`
- [x] T006 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 1 exports and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-1-output-parity.md`
- [x] T007 [US1] Execute circular import checks for Phase 1 module boundaries using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md`
- [x] T008 [US1] Execute runtime coupling checks for Phase 1 using `tests/integration/test_runtime_coupling.py` with `phase_1` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md`
- [x] T009 [US1] Verify hard gate pass and sign off Phase 1 in `specs/193-main-decomposition-wave-2/checklists/phase-1-gate.md` before starting Phase 2

---

## Phase 2: TroubleshootUtils + SSHRunnerManager (US1/US2)

**Goal**: Extract troubleshooting/SSH runners while preserving interactive semantics.
**Independent Test**: Menu `139`, `175`, and `176` behave identically with parity and hard-gate pass.

- [x] T010 [US1] Extract troubleshoot logic from `MistHelper.py` into `src/troubleshooting/marvis_troubleshoot_utils.py`
- [x] T011 [US1] Extract SSH runner logic from `MistHelper.py` into `src/ssh/ssh_runner_manager.py` with delegator-only orchestration left in `MistHelper.py`
- [x] T012 [US1] Add or update tests in `tests/unit/troubleshooting/test_marvis_troubleshoot_utils.py` and `tests/unit/ssh/test_ssh_runner_manager.py`
- [x] T013 [US1] Run mandatory automated validation for Phase 2 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md`
- [x] T013A [US1] Verify constitution compliance for Phase 2 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md`
- [x] T013B [US1] Execute full deployment pipeline for Phase 2 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md`
- [x] T014 [US2] Execute menu behavior parity checks for operations `139`, `175`, `176` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-2-menu-parity.md`
- [x] T015 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 2 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-2-output-parity.md`
- [x] T016 [US1] Execute circular import checks for Phase 2 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md`
- [x] T017 [US1] Execute runtime coupling checks for Phase 2 using `tests/integration/test_runtime_coupling.py` with `phase_2` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md`
- [x] T018 [US1] Verify hard gate pass and sign off Phase 2 in `specs/193-main-decomposition-wave-2/checklists/phase-2-gate.md` before starting Phase 3

---

## Phase 3: WAN2MigrationManager + WANProbeDeviceOverrideManager (US1/US2)

**Goal**: Extract WAN migration/override managers with destructive safeguards unchanged.
**Independent Test**: Menu `149` and `167` parity remains intact and hard-gate pass is recorded.

- [x] T019 [US1] Extract WAN2 migration logic from `MistHelper.py` into `src/gateway/wan2_migration_manager.py`
- [x] T020 [US1] Extract WAN probe device override logic from `MistHelper.py` into `src/gateway/wan_probe_device_override_manager.py` and preserve orchestration in `MistHelper.py`
- [x] T021 [US1] Add or update tests in `tests/unit/gateway/test_wan2_migration_manager.py` and `tests/unit/gateway/test_wan_probe_device_override_manager.py`
- [x] T022 [US1] Run mandatory automated validation for Phase 3 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md`
- [x] T022A [US1] Verify constitution compliance for Phase 3 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md`
- [x] T022B [US1] Execute full deployment pipeline for Phase 3 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md`
- [x] T023 [US2] Execute menu behavior parity checks for operations `149`, `167` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-3-menu-parity.md`
- [x] T024 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 3 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-3-output-parity.md`
- [x] T025 [US1] Execute circular import checks for Phase 3 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md`
- [x] T026 [US1] Execute runtime coupling checks for Phase 3 using `tests/integration/test_runtime_coupling.py` with `phase_3` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md`
- [x] T027 [US1] Verify hard gate pass and sign off Phase 3 in `specs/193-main-decomposition-wave-2/checklists/phase-3-gate.md` before starting Phase 4

---

## Phase 4: SiteConfigManager (US1/US2)

**Goal**: Extract site configuration manager with grouped destructive operations unchanged.
**Independent Test**: Menu `171-174` parity and hard-gate criteria pass.

- [x] T028 [US1] Extract `SiteConfigManager` from `MistHelper.py` into `src/site/site_config_manager.py`
- [x] T029 [US1] Reduce `MistHelper.py` to orchestration/delegation for `SiteConfigManager` entrypoints and remove duplicated implementation blocks
- [x] T030 [US1] Add or update tests in `tests/unit/site/test_site_config_manager.py`
- [x] T031 [US1] Run mandatory automated validation for Phase 4 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md`
- [x] T031A [US1] Verify constitution compliance for Phase 4 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md`
- [x] T031B [US1] Execute full deployment pipeline for Phase 4 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md`
- [x] T032 [US2] Execute menu behavior parity checks for operations `171-174` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-4-menu-parity.md`
- [x] T033 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 4 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-4-output-parity.md`
- [x] T034 [US1] Execute circular import checks for Phase 4 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md`
- [x] T035 [US1] Execute runtime coupling checks for Phase 4 using `tests/integration/test_runtime_coupling.py` with `phase_4` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md`
- [x] T036 [US1] Verify hard gate pass and sign off Phase 4 in `specs/193-main-decomposition-wave-2/checklists/phase-4-gate.md` before starting Phase 5

---

## Phase 5: SiteExportUtils (US1/US2)

**Goal**: Extract site export stack while preserving export shape and backend behavior.
**Independent Test**: Menu `70-86` parity and backend parity checks pass.

- [ ] T037 [US1] Extract `SiteExportUtils` from `MistHelper.py` into `src/export/site_export_utils.py`
- [ ] T038 [US1] Split high-complexity insights branch into `src/export/site_insights_exporter.py` and keep `MistHelper.py` orchestration only
- [ ] T039 [US1] Add or update tests in `tests/unit/export/test_site_export_utils.py` and `tests/unit/export/test_site_insights_exporter.py`
- [ ] T040 [US1] Run mandatory automated validation for Phase 5 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md`
- [ ] T040A [US1] Verify constitution compliance for Phase 5 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md`
- [ ] T040B [US1] Execute full deployment pipeline for Phase 5 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md`
- [ ] T041 [US2] Execute menu behavior parity checks for operations `70-86` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-5-menu-parity.md`
- [ ] T042 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 5 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-5-output-parity.md`
- [ ] T043 [US1] Execute circular import checks for Phase 5 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md`
- [ ] T044 [US1] Execute runtime coupling checks for Phase 5 using `tests/integration/test_runtime_coupling.py` with `phase_5` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md`
- [ ] T045 [US1] Verify hard gate pass and sign off Phase 5 in `specs/193-main-decomposition-wave-2/checklists/phase-5-gate.md` before starting Phase 6

---

## Phase 6: OrgDeviceInventorySummary (US1/US2)

**Goal**: Extract org device inventory summary and MSP modes with invariant output shape.
**Independent Test**: Menu `13` parity and export parity remain unchanged.

- [ ] T046 [US1] Extract `OrgDeviceInventorySummary` from `MistHelper.py` into `src/inventory/org_device_inventory_summary.py`
- [ ] T047 [US1] Extract MSP-specific orchestration into `src/inventory/org_device_inventory_msp.py` and leave `MistHelper.py` as delegator only
- [ ] T048 [US1] Add or update tests in `tests/unit/inventory/test_org_device_inventory_summary.py` and `tests/unit/inventory/test_org_device_inventory_msp.py`
- [ ] T049 [US1] Run mandatory automated validation for Phase 6 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md`
- [ ] T049A [US1] Verify constitution compliance for Phase 6 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md`
- [ ] T049B [US1] Execute full deployment pipeline for Phase 6 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md`
- [ ] T050 [US2] Execute menu behavior parity checks for operation `13` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-6-menu-parity.md`
- [ ] T051 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 6 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-6-output-parity.md`
- [ ] T052 [US1] Execute circular import checks for Phase 6 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md`
- [ ] T053 [US1] Execute runtime coupling checks for Phase 6 using `tests/integration/test_runtime_coupling.py` with `phase_6` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md`
- [ ] T054 [US1] Verify hard gate pass and sign off Phase 6 in `specs/193-main-decomposition-wave-2/checklists/phase-6-gate.md` before starting Phase 7

---

## Phase 7: GatewayExportUtils (US1/US2)

**Goal**: Extract hardest gateway export surfaces without changing gateway semantics.
**Independent Test**: Menu `31-36`, `99`, `163` parity plus backend consistency passes.

- [ ] T055 [US1] Extract `GatewayExportUtils` from `MistHelper.py` into `src/gateway/gateway_export_utils.py`
- [ ] T056 [US1] Extract gateway stats/override branches into `src/gateway/gateway_stats_exporter.py` and `src/gateway/gateway_override_analyzer.py` with `MistHelper.py` delegator-only wiring
- [ ] T057 [US1] Add or update tests in `tests/unit/gateway/test_gateway_export_utils.py`, `tests/unit/gateway/test_gateway_stats_exporter.py`, and `tests/unit/gateway/test_gateway_override_analyzer.py`
- [ ] T058 [US1] Run mandatory automated validation for Phase 7 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md`
- [ ] T058A [US1] Verify constitution compliance for Phase 7 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md`
- [ ] T058B [US1] Execute full deployment pipeline for Phase 7 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md`
- [ ] T059 [US2] Execute menu behavior parity checks for operations `31-36`, `99`, `163` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-7-menu-parity.md`
- [ ] T060 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 7 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-7-output-parity.md`
- [ ] T061 [US1] Execute circular import checks for Phase 7 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md`
- [ ] T062 [US1] Execute runtime coupling checks for Phase 7 using `tests/integration/test_runtime_coupling.py` with `phase_7` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md`
- [ ] T063 [US1] Verify hard gate pass and sign off Phase 7 in `specs/193-main-decomposition-wave-2/checklists/phase-7-gate.md` before starting Phase 8

---

## Phase 8: ServicePingManager (US1/US2)

**Goal**: Extract websocket service ping orchestration with transport contract parity.
**Independent Test**: Menu `120` behavior, timeout handling, and outputs remain parity-aligned.

- [ ] T064 [US1] Extract `ServicePingManager` from `MistHelper.py` into `src/websocket/service_ping_manager.py`
- [ ] T065 [US1] Extract discovery and payload composition logic into `src/websocket/service_ping_discovery.py` and keep `MistHelper.py` orchestration only
- [ ] T066 [US1] Add or update tests in `tests/unit/websocket/test_service_ping_manager.py` and `tests/unit/websocket/test_service_ping_discovery.py`
- [ ] T067 [US1] Run mandatory automated validation for Phase 8 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md`
- [ ] T067A [US1] Verify constitution compliance for Phase 8 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md`
- [ ] T067B [US1] Execute full deployment pipeline for Phase 8 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md`
- [ ] T068 [US2] Execute menu behavior parity checks for operation `120` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-8-menu-parity.md`
- [ ] T069 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 8 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-8-output-parity.md`
- [ ] T070 [US1] Execute circular import checks for Phase 8 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md`
- [ ] T071 [US1] Execute runtime coupling checks for Phase 8 using `tests/integration/test_runtime_coupling.py` with `phase_8` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md`
- [ ] T072 [US1] Verify hard gate pass and sign off Phase 8 in `specs/193-main-decomposition-wave-2/checklists/phase-8-gate.md` before starting Phase 9

---

## Phase 9: PacketCaptureManager (US1/US2)

**Goal**: Complete canonical packet capture extraction with single-source ownership.
**Independent Test**: Menu `134` and `135` parity and all hard-gate checks pass.

- [ ] T073 [US1] Complete `PacketCaptureManager` migration by finalizing canonical implementation in `src/capture/packet_capture.py` and removing duplicate logic from `MistHelper.py`
- [ ] T074 [US1] Extract/normalize download and poll loop responsibilities into `src/capture/packet_capture_download.py` when either function length exceeds 25 lines, complexity exceeds 10, or duplicate download/poll logic remains in `MistHelper.py`; retain only orchestration in `MistHelper.py`
- [ ] T075 [US1] Add or update tests in `tests/unit/capture/test_packet_capture_manager.py` and `tests/unit/capture/test_packet_capture_download.py`
- [ ] T076 [US1] Run mandatory automated validation for Phase 9 and record output in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md`
- [ ] T076A [US1] Verify constitution compliance for Phase 9 changed code (inline comments + before/after action logging) and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md`
- [ ] T076B [US1] Execute full deployment pipeline for Phase 9 changes and record run IDs/status in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md`
- [ ] T077 [US2] Execute menu behavior parity checks for operations `134`, `135` and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-9-menu-parity.md`
- [ ] T078 [US2] Execute API + backend parity checks (CSV/SQLite/polyglot) for Phase 9 affected outputs and capture evidence in `specs/193-main-decomposition-wave-2/checklists/phase-9-output-parity.md`
- [ ] T079 [US1] Execute circular import checks for Phase 9 extracted modules using `tests/contract/test_import_graph.py` and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md`
- [ ] T080 [US1] Execute runtime coupling checks for Phase 9 using `tests/integration/test_runtime_coupling.py` with `phase_9` profile and record evidence in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md`
- [ ] T081 [US1] Verify hard gate pass and sign off Phase 9 in `specs/193-main-decomposition-wave-2/checklists/phase-9-gate.md` before starting final documentation sync

---

## Post-Phase 9: Documentation Sync + Final Audit (US3)

**Goal**: Synchronize documentation and confirm completeness/accuracy.
**Independent Test**: Required docs and wiki are updated, verified, and signed off with zero stale references.

- [ ] T082 [US3] Update decomposition outcomes in `README.md` and verify all phase/module references are current
- [ ] T083 [US3] Update release notes and decomposition traceability in `CHANGELOG.md`
- [ ] T084 [US3] Update Mermaid/architecture documentation in `documentation/diagrams/core/architecture-overview.md`, `documentation/diagrams/infrastructure/container-architecture.md`, and `mist-ops-platform/docs/architecture.md`
- [ ] T085 [US3] Synchronize GitHub wiki pages in `../MistHelper.wiki/` with repository documentation updates and record changed wiki page list in `specs/193-main-decomposition-wave-2/checklists/wiki-sync.md`
- [ ] T086 [US3] Execute completeness + accuracy audit checklist in `specs/193-main-decomposition-wave-2/checklists/final-doc-audit.md` (README + CHANGELOG + Mermaid/architecture docs + wiki + link validation + stale-reference scan + module ownership note verification for all 9 phases)
- [ ] T087 [US3] Record final signoff for wave completion in `specs/193-main-decomposition-wave-2/checklists/final-signoff.md`

---

## Dependencies & Execution Order

### Hard Serial Phase Chain (Mandatory)

1. Phase 1 (`T001-T009`) must be complete and signed off before Phase 2 starts.
2. Phase 2 (`T010-T018`) must be complete and signed off before Phase 3 starts.
3. Phase 3 (`T019-T027`) must be complete and signed off before Phase 4 starts.
4. Phase 4 (`T028-T036`) must be complete and signed off before Phase 5 starts.
5. Phase 5 (`T037-T045`) must be complete and signed off before Phase 6 starts.
6. Phase 6 (`T046-T054`) must be complete and signed off before Phase 7 starts.
7. Phase 7 (`T055-T063`) must be complete and signed off before Phase 8 starts.
8. Phase 8 (`T064-T072`) must be complete and signed off before Phase 9 starts.
9. Phase 9 (`T073-T081`) must be complete and signed off before documentation sync starts.
10. Post-Phase-9 documentation tasks (`T082-T087`) close the feature.
11. Scope guard tasks (`T000-T000A`) must be complete before Phase 1 starts.
12. Phase 0 bootstrap tasks (`T000B-T000E`) must be complete before any phase gate checks are executed.

### Within-Phase Order (Mandatory)

For each phase, tasks must execute in this exact sequence:

1. Extraction/refactor (`x01-x02`)
2. Test update/addition (`x03`)
3. Mandatory automated validation (`x04`) + constitution compliance verification (`x04A`) + full deployment pipeline (`x04B`)
4. Parity checks for menu/API/backend outputs (`x05-x06`)
5. Circular import and runtime coupling checks (`x07-x08`)
6. Gate verification/signoff (`x09`)

Mandatory remediation loop rule for every phase:

- If any validation/parity/import/runtime check fails, remediate within the same phase, re-run failed checks until all pass, then complete gate signoff.

### Parallel Opportunities

None by design. This wave intentionally forbids parallel decomposition execution.

---

## Implementation Strategy

### MVP Scope

- MVP = complete Phase 1 (`T001-T009`) with hard gate signoff.

### Incremental Delivery

1. Deliver one signed-off phase at a time (1 -> 9).
2. Commit at least once per task group (extraction, tests, validation/parity/risk checks, signoff).
3. Treat every failed gate as an in-phase remediation loop; do not advance until resolved.

### Audit-Ready Evidence

- Every phase must produce gate evidence in `specs/193-main-decomposition-wave-2/checklists/phase-<N>-gate.md`.
- Final evidence must include `wiki-sync.md`, `final-doc-audit.md`, and `final-signoff.md`.
<!-- End of tasks list -->
<!-- EOF -->

