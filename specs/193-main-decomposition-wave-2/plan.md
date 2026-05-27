# Implementation Plan: Main file decomposition wave 2 (serial, hard-gated)

**Branch**: `193-main-decomposition-wave-2` | **Date**: 2026-05-26 | **Spec**: `specs/193-main-decomposition-wave-2/spec.md`  
**Input**: Feature specification from `specs/193-main-decomposition-wave-2/spec.md`

## Summary

Decompose 9 class clusters from `MistHelper.py` in strict easiest-to-hardest sequence with a hard phase gate after each phase. Each phase performs: extraction -> tests -> quality gates -> parity checks -> import/coupling checks -> sign-off. No phase advances until all checks pass. After phase 9, execute a terminal documentation synchronization phase with completeness audit across repository docs and wiki.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: mistapi 0.59+, pytest/pytest-cov, ruff, black, mypy, tqdm, PrettyTable  
**Storage**: CSV/SQLite/ArangoDB/Redis outputs via existing exporter flows, JSON report artifacts under `data/`  
**Testing**: `python MistHelper.py --test` + targeted pytest tests under `tests/` + parity smoke checks  
**Target Platform**: Windows 11 local dev + containerized runtime (Podman primary)  
**Project Type**: Python CLI + modular `src/` package  
**Performance Goals**: Zero behavior drift; no material increase in runtime for touched menu paths; preserve current fast-mode behavior  
**Constraints**: Exact 9-phase decomposition order; hard stop on any failed gate; preserve menu IDs/output schemas; no `GlobalImportManager` in scope  
**Scale/Scope**: 9 class clusters, multiple menu paths (`7`, `13`, `31`, `60-86`, `87`, `88`, `139`, `148-150`, `166-167`, `169`, `171-174`, `175-176` and packet capture `134-135`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [PASS] Five-item rule preserved by splitting class clusters into bounded feature modules.
- [PASS] Class-based architecture preserved (no standalone wrapper shims beyond transitional delegators with bounded removal plan).
- [PASS] Safety-first input handling preserved (`safe_input`/typed confirmations unchanged).
- [PASS] Observability requirements preserved (no logging removal allowed during extraction).
- [PASS] Inline comments + action logging requirements remain enforceable for all newly generated code.
- [PASS] Full deployment/validation pipeline remains unchanged; phase gates require syntax/lint/format/test each step.

Post-design re-check status: [PASS] (module boundaries and dependency rules defined; no constitutional exceptions required).

## Project Structure

### Documentation (this feature)

```text
specs/193-main-decomposition-wave-2/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── serial-decomposition-contract.md
│   └── parity-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
MistHelper.py
src/
├── analytics/
├── capture/
├── gateway/
├── inventory/
├── ssh/
├── site/
├── export/
└── troubleshooting/
tests/
├── unit/
├── integration/
└── parity/
```

**Structure Decision**: Single-project modular Python layout. Continue reducing `MistHelper.py` to orchestration/dispatch while migrating implementation classes into semantically aligned `src/*` modules.

## Serial hard-gate execution model

For every phase below, this gate is mandatory before advancing:

1. Extraction complete and importable.
2. New/updated tests pass.
3. Quality commands pass (`py_compile`, `ruff`, `black --check`, `--test`).
4. Menu/API/backend parity checks pass.
5. Circular import and runtime coupling checks pass.
6. Phase sign-off evidence recorded.

Phase 0 bootstrap prerequisites before Phase 1 execution:

- Import graph gate test exists (`tests/contract/test_import_graph.py`).
- Runtime coupling harness exists (`tests/integration/test_runtime_coupling.py`).
- Deterministic parity contract exists (`specs/193-main-decomposition-wave-2/contracts/parity-contract.md`).
- Baseline parity artifacts are captured under `specs/193-main-decomposition-wave-2/checklists/parity-baseline/`.

If any step fails: fix within current phase; do not start next phase.

## Detailed phase plan (exact decomposition order preserved)

### Phase 1 (easiest): `SiteInventoryHealthAnalyzer` + `SiteAnalyticsConfigurator`

**Source cluster**: classes at `MistHelper.py` (~`30155`, `30707`) and their helper methods (`_scan_for_deviations`, `_apply_standard_configuration`, `_group_devices_by_site`, report/export helpers).  
**Target modules**:
- `src/analytics/site_analytics_configurator.py`
- `src/analytics/site_inventory_health_analyzer.py`

**Dependency/coupling controls**:
- New modules may depend only on shared utility contracts (`ConfigUtils`, `APICoreFetchUtils`, `DataExporter`, `InputUtils`) injected or imported from low-level utility modules.
- `MistHelper.py` keeps menu registration and thin delegator only.
- Prohibit reverse imports from `src/analytics/*` into `MistHelper.py` internals.

**Test strategy**:
- New tests: `tests/unit/analytics/test_site_analytics_configurator.py`, `tests/unit/analytics/test_site_inventory_health_analyzer.py`.
- Update existing: menu action mapping checks for options `7` and `169`.
- Smoke checks: run menu test mode paths for both operations (non-destructive for `7`; guarded confirmation path for `169`).

### Phase 2 (easy-medium): `TroubleshootUtils` + `SSHRunnerManager`

**Source cluster**: classes at `MistHelper.py` (~`22517`, `23125`) including Marvis workflows and SSH execution helpers (`_collect_missing_data`, `_execute_ssh`, template-targeted flows).  
**Target modules**:
- `src/troubleshooting/marvis_troubleshoot_utils.py`
- `src/ssh/ssh_runner_manager.py`

**Dependency/coupling controls**:
- Extract command-specific helpers into module-private functions/classes; expose class API only.
- No direct import of menu registry in extracted modules.
- Centralize env/config reads via existing utility layer; avoid duplicated globals.

**Test strategy**:
- New tests: `tests/unit/troubleshooting/test_marvis_troubleshoot_utils.py`, `tests/unit/ssh/test_ssh_runner_manager.py`.
- Update existing: CLI/menu routing for options `139`, `175`, `176`.
- Smoke checks: dry interactive flows with mocked `safe_input` + mocked mistapi and SSH backends.

### Phase 3 (medium): `WAN2MigrationManager` + `WANProbeDeviceOverrideManager`

**Source cluster**: classes at `MistHelper.py` (~`23982`, `25651`) handling site variable setup, override detection, and device-level probe application.  
**Target modules**:
- `src/gateway/wan2_migration_manager.py`
- `src/gateway/wan_probe_device_override_manager.py`

**Dependency/coupling controls**:
- Keep destructive confirmation and audit/report writing inside module service layer.
- No circular links with template config manager or menu registry; use explicit dependency arguments where practical.
- Keep CSV file access centralized through `FilePathUtils`/`CacheUtils` only.

**Test strategy**:
- New tests: `tests/unit/gateway/test_wan2_migration_manager.py`, `tests/unit/gateway/test_wan_probe_device_override_manager.py`.
- Update existing: destructive confirmation gate tests for menu options `149`, `167`.
- Smoke checks: dry-run flows (`--dry-run`-equivalent) and non-destructive planning output parity.

### Phase 4 (medium): `SiteConfigManager`

**Source cluster**: class at `MistHelper.py` (~`26229`) with grouped destructive site/profile/template operations (`171-174`, RF template and profile assignment helpers).  
**Target module**:
- `src/site/site_config_manager.py`

**Dependency/coupling controls**:
- Segment internal sub-services (`test_sites`, `rf_templates`, `device_profiles`) inside module to avoid monolith recreation.
- Keep explicit confirmation strings unchanged.
- Maintain single orchestration entry class from `MistHelper.py`.

**Test strategy**:
- New tests: `tests/unit/site/test_site_config_manager.py` with per-subservice suites.
- Update existing: confirmation phrase enforcement and CSV artifact generation assertions.
- Smoke checks: test-mode/mocked API runs for `171-174` guarded paths.

### Phase 5 (medium): `SiteExportUtils`

**Source cluster**: class at `MistHelper.py` (~`17813`) covering site export helpers (`_export_data`, insights/device insights, stats/metrics exports, and supporting normalization helpers).  
**Target modules**:
- `src/export/site_export_utils.py`
- `src/export/site_insights_exporter.py` (split high-complexity insights branch)

**Dependency/coupling controls**:
- Keep exporter interface (`DataExporter`) as sole output boundary.
- Avoid importing packet capture or unrelated managers; isolate utility dependencies.
- Enforce module-private helpers for metric compatibility and MAC normalization.

**Test strategy**:
- New tests: `tests/unit/export/test_site_export_utils.py`, `tests/unit/export/test_site_insights_exporter.py`.
- Update existing: menu mapping tests for options `70-86` and site insight entries.
- Smoke checks: representative site export calls with mocked API pagination and output writer assertions.

### Phase 6 (medium-hard): `OrgDeviceInventorySummary`

**Source cluster**: class at `MistHelper.py` (~`14007`) including physical-count aggregation, MSP modes, combined pivots, and export composition.  
**Target modules**:
- `src/inventory/org_device_inventory_summary.py`
- `src/inventory/org_device_inventory_msp.py` (MSP-specific orchestration split)

**Dependency/coupling controls**:
- Separate aggregation logic from interactive prompt flow.
- No direct dependence on menu globals inside aggregation layer.
- Stabilize data contract between summary core and output formatter.

**Test strategy**:
- New tests: `tests/unit/inventory/test_org_device_inventory_summary.py`, `tests/unit/inventory/test_org_device_inventory_msp.py`.
- Update existing: menu option `13` dispatch and MSP mode behavior.
- Smoke checks: pivot generation parity and export row/column invariants.

### Phase 7 (hard): `GatewayExportUtils`

**Source cluster**: class at `MistHelper.py` (~`21649`) including management IP correlation, device configs, WAN override detection, template-based exports, and helper fetch functions.  
**Target modules**:
- `src/gateway/gateway_export_utils.py`
- `src/gateway/gateway_stats_exporter.py`
- `src/gateway/gateway_override_analyzer.py`

**Dependency/coupling controls**:
- Break mutual dependencies by moving shared fetch/transform functions into a gateway-common utility module (`src/gateway/common.py`) if needed.
- Keep stats exporter and override analyzer independent of menu wiring.
- Forbid cross-import cycles among gateway modules via import-linter checks.

**Test strategy**:
- New tests: `tests/unit/gateway/test_gateway_export_utils.py`, `tests/unit/gateway/test_gateway_stats_exporter.py`, `tests/unit/gateway/test_gateway_override_analyzer.py`.
- Update existing: options `31-36`, `99`, `163` data flow checks.
- Smoke checks: CSV correlation outputs and override report shape validation.

### Phase 8 (hard): `ServicePingManager`

**Source cluster**: class at `MistHelper.py` (~`18595`) covering tenant/service discovery, payload creation, websocket setup, result display, and cleanup orchestration.  
**Target modules**:
- `src/websocket/service_ping_manager.py`
- `src/websocket/service_ping_discovery.py`

**Dependency/coupling controls**:
- Keep websocket transport abstraction in existing websocket layer; manager composes it.
- No direct import from CLI/menu modules.
- Keep payload schema contract stable and covered by contract tests.

**Test strategy**:
- New tests: `tests/unit/websocket/test_service_ping_manager.py`, `tests/unit/websocket/test_service_ping_discovery.py`.
- Update existing: menu option `120` routing and timeout handling tests.
- Smoke checks: mocked websocket command lifecycle including timeout and success paths.

### Phase 9 (hardest): `PacketCaptureManager`

**Source cluster**: class at `MistHelper.py` (~`6255`) already partially extracted; complete migration of remaining methods and remove duplicate source logic from `MistHelper.py`.  
**Target modules**:
- `src/capture/packet_capture.py` (complete class surface)
- `src/capture/packet_capture_download.py` (download/poll loop split if required)

**Dependency/coupling controls**:
- One canonical implementation in `src/capture`; `MistHelper.py` retains delegator only.
- Keep capture payload validation and download logic separate to reduce cycle risk.
- Preserve API compatibility for menu options `134`, `135`.

**Test strategy**:
- New tests: `tests/unit/capture/test_packet_capture_manager.py`, `tests/unit/capture/test_packet_capture_download.py`.
- Update existing: packet-capture menu integration tests.
- Smoke checks: capture-mode selection, payload construction, and result-handling parity with mocked APIs.

## Terminal documentation synchronization phase (post-Phase 9)

This phase starts only after Phase 9 gate passes.

**Artifacts to synchronize**:
- `README.md`
- `CHANGELOG.md`
- Mermaid/architecture docs under repo documentation directories
- GitHub wiki pages corresponding to decomposition/module ownership

**Completeness verification checklist**:
- [ ] 9-phase outcomes documented with source->target module ownership map.
- [ ] No stale ownership references to moved class implementations in `MistHelper.py`.
- [ ] Menu option references still accurate.
- [ ] Mermaid diagrams reflect new module boundaries and data flow.
- [ ] Wiki pages semantically match repository docs for same topics.
- [ ] Links resolve and file paths exist.

## Dependency and circular-import prevention controls

1. **One-way layering**: `MistHelper.py` (orchestration) -> `src/*` feature modules -> shared utilities. Reverse import forbidden.
2. **No menu-registry imports in extracted modules**: extracted code must not depend on `menu_actions`.
3. **Shared utility access through stable utility modules only** (`ConfigUtils`, `FilePathUtils`, `CacheUtils`, `DataExporter`, etc.).
4. **Import graph check per phase**: run cycle detection (`python -m pytest tests/contract/test_import_graph.py` or equivalent checker script) and fail gate on cycle.
5. **Runtime coupling check per phase**: detect hidden global state dependence via targeted tests with isolated mocks/fixtures.

## Validation commands (run at every phase gate)

```text
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py
python -m black --check MistHelper.py
python MistHelper.py --test
```

Additional per-phase checks:
- Run newly added/updated targeted tests for affected modules.
- Run parity smoke tests for touched menu paths.
- Run circular import/runtime coupling checks.

## Workstreams

1. **WS1 - Serial decomposition execution** (Phases 1-9, strict order)
2. **WS2 - Terminal documentation synchronization and completeness audit** (post-Phase 9 only)

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
