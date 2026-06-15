# Tasks: Legacy Compat Shim Decomposition

**Input**: Design artifacts from `/specs/1002-legacy-compat-shim-decomposition/`
**Prerequisites**: `spec.md`, `checklists/requirements.md`

**Tests**: Included because spec explicitly requires test migration, parity checkpoints, and CI static guards.

**Organization**: Tasks grouped by user story for independent implementation/testing, with explicit symbol-level migration actions.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency)
- **[Story]**: User story phase label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes explicit file path(s)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock inventory, rollout tracking, and baseline parity artifacts before code churn.

- [ ] T001 Create migration tracker table for all inventoried shim symbols in `specs/1002-legacy-compat-shim-decomposition/migration-tracker.md`
- [ ] T002 Create adapter-expiry ledger for temporary adapters/dates/triggers in `specs/1002-legacy-compat-shim-decomposition/adapter-expiry-ledger.md`
- [ ] T003 Create pre-migration parity checklist for menu/export behavior in `specs/1002-legacy-compat-shim-decomposition/parity-checklist.md`
- [ ] T004 [P] Capture pre-migration internal reference baseline for `*_legacy` and facade symbols in `specs/1002-legacy-compat-shim-decomposition/baseline-internal-references.txt`
- [ ] T005 [P] Capture pre-migration test inventory for alias/facade dependencies in `specs/1002-legacy-compat-shim-decomposition/test-inventory.md`
- [ ] T006 Record phased rollback criteria and stop conditions in `specs/1002-legacy-compat-shim-decomposition/rollback-criteria.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build safety rails and acceptance gates before symbol retirement.

**⚠️ CRITICAL**: No symbol retirement starts until this phase is complete.

- [ ] T007 Add CI static guard script to detect retired shim symbol usage in `scripts/ci/check_retired_compat_symbols.py`
- [ ] T008 Wire static guard into workflow in `.github/workflows/ci.yml`
- [ ] T009 Add canonical ownership map document for all inventory rows in `specs/1002-legacy-compat-shim-decomposition/canonical-ownership-map.md`
- [ ] T010 Add transitional adapter annotation standard (expiry + trigger + owner) in `specs/1002-legacy-compat-shim-decomposition/adapter-policy.md`
- [ ] T011 Add phased acceptance gate checklist (Phase 1-5 signoff) in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`
- [ ] T012 Foundational gate: verify tracker + guards + ownership map complete in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`

**Checkpoint**: Foundation ready; symbol migration can begin with safe rollout controls.

---

## Phase 3: User Story 1 - Retire dead compatibility indirection (Priority: P1) 🎯 MVP

**Goal**: Remove/replace inventoried legacy wrappers and facades so canonical `src` ownership is explicit.

**Independent Test**: Static scan shows no internal references for retired symbols; shim-focused tests pass for canonical call paths.

### Implementation for User Story 1

#### MistHelper.py legacy delegates

- [ ] T013 [US1] Remove `get_csv_file_path_legacy` wrapper and migrate direct canonical callsites in `MistHelper.py`
- [ ] T014 [US1] Replace `export_const_insight_metrics_to_csv` legacy behavior with canonical export service entry in `MistHelper.py`
- [ ] T015 [US1] Remove `export_gateway_templates_to_csv_legacy` wrapper and migrate direct canonical export calls in `MistHelper.py`

#### Capture alias wrappers

- [ ] T016 [P] [US1] Keep `run()` as temporary adapter with explicit expiry metadata while routing to canonical `execute()` in `src/capture/site_pcap_wait_download_workflow.py`
- [ ] T017 [P] [US1] Keep `run()` as temporary adapter with explicit expiry metadata while routing to canonical `execute()` in `src/capture/org_pcap_wait_download_workflow.py`

#### Top-level compatibility facade hub (`__init__.py`) - retire/replace each branch explicitly

- [ ] T018 [US1] Retire `__getattr__` branch `DataProcessingUtils` and replace with direct canonical import path in `__init__.py`
- [ ] T019 [US1] Retire `__getattr__` branch `InsightMetricsUtils` (including legacy bridge surface) in `__init__.py`
- [ ] T020 [US1] Replace `__getattr__` branch `PromptUtils` with direct canonical import in `__init__.py`
- [ ] T021 [US1] Replace `__getattr__` branch `EnhancedSSHRunner` with direct canonical import in `__init__.py`
- [ ] T022 [US1] Retire `__getattr__` branch `SiteExportUtils` and replace with direct canonical import in `__init__.py`
- [ ] T023 [US1] Retire `__getattr__` branch `SiteClientExporter` and replace with direct canonical import in `__init__.py`
- [ ] T024 [US1] Retire `__getattr__` branch `OrgAlarmEventExporter` and replace with direct canonical import in `__init__.py`
- [ ] T025 [US1] Retire `__getattr__` branch `OrgExportUtils` and replace with direct canonical import in `__init__.py`
- [ ] T026 [US1] Replace `__getattr__` branch `APIDataFetcher` with direct canonical import in `__init__.py`
- [ ] T027 [US1] Replace `__getattr__` branch `ConfigUtils` with direct canonical import in `__init__.py`
- [ ] T028 [US1] Replace `__getattr__` branch `InputUtils` with direct canonical import in `__init__.py`
- [ ] T029 [US1] Replace `__getattr__` branch `OperationRegistry` with direct canonical import in `__init__.py`
- [ ] T030 [US1] Retire `__getattr__` branch `WAN2MigrationManager` and replace with direct canonical import in `__init__.py`
- [ ] T031 [US1] Retire `__getattr__` branch `ServicePingManager` and replace with direct canonical import in `__init__.py`
- [ ] T032 [US1] Retire `__getattr__` branch `TroubleshootUtils` and replace with direct canonical import in `__init__.py`
- [ ] T033 [US1] Retire `__getattr__` branch `SSHRunnerManager` and replace with direct canonical import in `__init__.py`
- [ ] T034 [US1] Retire `__getattr__` branch `OrgTicketManager` and replace with direct canonical import in `__init__.py`
- [ ] T035 [US1] Replace `__getattr__` branch `TimeUtils` with direct canonical import in `__init__.py`
- [ ] T036 [US1] Retire `__getattr__` branch `OrgInventoryExporter` and replace with direct canonical import in `__init__.py`
- [ ] T037 [US1] Retire `__getattr__` branch `OrgDeviceStatsExporter` and replace with direct canonical import in `__init__.py`
- [ ] T038 [US1] Keep `_noop_menu_action` as explicitly documented temporary adapter with expiry guard in `__init__.py`
- [ ] T039 [US1] Keep `_ensure_menu_coverage` as explicitly documented temporary adapter with expiry guard in `__init__.py`

#### Capture package lazy facade

- [ ] T040 [US1] Replace lazy `PacketCaptureManager` `__getattr__` facade with explicit export/import map in `src/capture/__init__.py`

#### Legacy export shim callsites

- [ ] T041 [P] [US1] Replace `InsightMetricsUtils.export_legacy()` call with canonical export/cache refresh path in `src/export/site_insights/site_metric_operation.py`
- [ ] T042 [P] [US1] Replace `InsightMetricsUtils.export_legacy()` call with canonical export/cache refresh path in `src/export/site_insights/device_metric_operation.py`

#### US1 acceptance gates

- [ ] T043 [US1] Gate: run static scan to confirm 0 internal references to retired `*_legacy` symbols and retired `__getattr__` branches using `scripts/ci/check_retired_compat_symbols.py`
- [ ] T044 [US1] Gate: update migration tracker status for all 30 inventory symbols (remove/direct-import/temporary-adapter + expiry) in `specs/1002-legacy-compat-shim-decomposition/migration-tracker.md`

**Checkpoint**: US1 complete when every inventory symbol has an executed action and static guard passes.

---

## Phase 4: User Story 2 - Preserve user-facing behavior during phased migration (Priority: P2)

**Goal**: Maintain menu/export parity and safe transitional behavior while shims are retired.

**Independent Test**: Menu/export parity checklist passes at each phase checkpoint; no untracked fallback growth.

### Tests and rollout gates for User Story 2

- [ ] T045 [P] [US2] Add menu parity regression tests for migration-scope operations in `tests/integration/test_menu_parity_legacy_shim_decomposition.py`
- [ ] T046 [P] [US2] Add export output-shape parity tests for impacted exports in `tests/integration/test_export_parity_legacy_shim_decomposition.py`
- [ ] T047 [US2] Add guard test preventing new unapproved `_noop_menu_action` registrations in `tests/unit/test_menu_fallback_growth_guard.py`
- [ ] T048 [US2] Add guard test preventing new unapproved `_ensure_menu_coverage` patching in `tests/unit/test_menu_coverage_growth_guard.py`
- [ ] T049 [US2] Add adapter-expiry enforcement tests for capture `run()` aliases and menu fallbacks in `tests/unit/test_compat_adapter_expiry_policy.py`
- [ ] T050 [US2] Add rollback-condition test matrix for parity failures and fallback regressions in `tests/integration/test_legacy_compat_rollback_conditions.py`

### Implementation and documentation for User Story 2

- [ ] T051 [US2] Wire parity checkpoint execution order (Phase 2->3->4->5) into `specs/1002-legacy-compat-shim-decomposition/parity-checklist.md`
- [ ] T052 [US2] Record transitional exceptions (if any) with explicit owner and expiry in `specs/1002-legacy-compat-shim-decomposition/adapter-expiry-ledger.md`
- [ ] T053 [US2] Gate: verify menu operations in migration scope pass pre/post parity criteria and capture evidence in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`
- [ ] T054 [US2] Gate: verify export output shape and error semantics remain equivalent and capture evidence in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`
- [ ] T055 [US2] Gate: verify no silent fallback growth beyond approved transitional list in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`

**Checkpoint**: US2 complete when parity and transitional risk gates pass without undocumented fallback usage.

---

## Phase 5: User Story 3 - Harden test suite around canonical interfaces (Priority: P3)

**Goal**: Move tests from alias/facade paths to canonical interfaces; keep adapter tests only while active.

**Independent Test**: Canonical-interface tests pass; shim-path tests removed or explicitly marked temporary with expiry.

### Test migration implementation for User Story 3

- [ ] T056 [US3] Create test migration map from legacy alias/facade imports to canonical imports in `specs/1002-legacy-compat-shim-decomposition/test-migration-map.md`
- [ ] T057 [US3] Migrate tests importing top-level facade names from `__init__.py` to canonical `src` module imports in `tests/unit/` and `tests/integration/`
- [ ] T058 [US3] Migrate tests asserting `InsightMetricsUtils.export_legacy` behavior to canonical site insights export interfaces in `tests/unit/` and `tests/integration/`
- [ ] T059 [US3] Migrate tests using capture workflow `run()` aliases to canonical `execute()` assertions in `tests/unit/` and `tests/integration/`
- [ ] T060 [US3] Remove or quarantine obsolete shim-path tests with explicit expiry markers in `tests/compat/legacy_shim_adapters/`
- [ ] T061 [US3] Add canonical-import enforcement test to fail on new test-time facade alias usage in `tests/unit/test_no_new_legacy_facade_imports.py`
- [ ] T062 [US3] Add canonical API smoke tests for site/device metric operations in `tests/unit/test_site_insights_canonical_exports.py`
- [ ] T063 [US3] Add final static-check test that rejects internal `export_legacy` references in `tests/unit/test_no_export_legacy_callsites.py`
- [ ] T064 [US3] Gate: run targeted shim decomposition test suite and record pass evidence in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`
- [ ] T065 [US3] Gate: verify 100% inventoried legacy-dependent tests are migrated or tracked as temporary with expiry in `specs/1002-legacy-compat-shim-decomposition/test-inventory.md`

**Checkpoint**: US3 complete when tests depend on canonical interfaces and shim-only tests are eliminated or time-bounded.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final retirement checks, docs/changelog, and release readiness.

- [ ] T066 Remove expired temporary adapters (capture `run()` aliases and menu fallback helpers) after expiry gates pass in `src/capture/site_pcap_wait_download_workflow.py`, `src/capture/org_pcap_wait_download_workflow.py`, and `__init__.py`
- [ ] T067 Run full internal reference audit and store results in `specs/1002-legacy-compat-shim-decomposition/final-internal-reference-audit.txt`
- [ ] T068 Update migration guidance from shim/facade paths to canonical paths in `README.md`
- [ ] T069 Add shim retirement/deprecation timeline entries in `CHANGELOG.md`
- [ ] T070 Add final decomposition summary and phase evidence in `specs/1002-legacy-compat-shim-decomposition/final-report.md`
- [ ] T071 Execute quality gates (`py_compile`, `ruff`, targeted pytest suites) and log outcomes in `specs/1002-legacy-compat-shim-decomposition/final-report.md`
- [ ] T072 Release gate: verify SC-001 through SC-007 closure and sign off in `specs/1002-legacy-compat-shim-decomposition/acceptance-gates.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately.
- **Phase 2 (Foundational)**: depends on Phase 1; blocks all user stories.
- **Phase 3 (US1 / P1)**: depends on Phase 2; executes symbol-level decomposition actions.
- **Phase 4 (US2 / P2)**: depends on US1 core actions; validates parity/risk during rollout.
- **Phase 5 (US3 / P3)**: depends on US1 symbol actions and US2 parity controls.
- **Phase 6 (Polish)**: depends on completion/signoff of US1-US3 gates.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories; delivers MVP decomposition inventory execution.
- **US2 (P2)**: depends on US1 migrated symbols to run real parity checks.
- **US3 (P3)**: depends on US1 canonical paths; informed by US2 transitional adapters and parity gates.

### Safe Rollout Ordering (Required)

1. Inventory lock + adapter policy (T001-T012)
2. Canonical enablement and shim decommissioning per symbol (T013-T042)
3. Static/reference gates before broad test churn (T043-T044)
4. Menu/export parity + fallback growth controls (T045-T055)
5. Test suite migration to canonical interfaces (T056-T065)
6. Expiry-based removals, docs/changelog, final signoff (T066-T072)

### Within Each User Story

- Implement symbol changes first, then run story gates.
- No adapter removal before parity and expiry gates pass.
- No final release signoff before SC closure evidence exists.

### Parallel Opportunities

- Phase 1: T004-T005 can run in parallel.
- Phase 3: T016/T017 and T041/T042 can run in parallel (different files).
- Phase 4: T045/T046 can run in parallel.
- Remaining tasks touching `__init__.py` and `MistHelper.py` run sequentially to avoid conflicts.

---

## Parallel Example: User Story 1

- Execute in parallel:
  - T016 (`src/capture/site_pcap_wait_download_workflow.py`)
  - T017 (`src/capture/org_pcap_wait_download_workflow.py`)
- Execute in parallel:
  - T041 (`src/export/site_insights/site_metric_operation.py`)
  - T042 (`src/export/site_insights/device_metric_operation.py`)
- Keep sequential:
  - T018-T039 in `__init__.py`
  - T013-T015 in `MistHelper.py`

---

## Implementation Strategy

### MVP First (US1 only)

1. Finish Phase 1 and Phase 2 safety rails.
2. Complete US1 symbol-level decomposition tasks (T013-T044).
3. Validate static scan and migration tracker closure.
4. Stop and review before broader parity/test migrations.

### Incremental Delivery

1. Deliver US1 decomposition inventory execution.
2. Deliver US2 parity/risk controls and acceptance evidence.
3. Deliver US3 test hardening to canonical interfaces.
4. Deliver Phase 6 final retirement + docs/changelog signoff.

### Acceptance Gates Summary

- **Gate A (Foundational)**: T012
- **Gate B (US1 symbol retirement)**: T043-T044
- **Gate C (US2 parity/risk)**: T053-T055
- **Gate D (US3 test migration)**: T064-T065
- **Gate E (Release readiness)**: T072

---

## Notes

- Task list explicitly enumerates each decomposition inventory symbol/file with removal/replacement/temporary-adapter action.
- Temporary adapters must include expiry date and removal trigger in tracker artifacts.
- New compatibility shim growth is disallowed unless explicitly tracked in ledger and gates.
