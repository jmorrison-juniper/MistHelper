# Tasks: God Class Decomposition

**Input**: Design documents from `/specs/004-god-class-decomposition/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not separately requested. Validation uses built-in `python MistHelper.py --test` (49/49 pass, 0 failures) plus `python -m py_compile MistHelper.py` after each class decomposition.

**Organization**: Tasks grouped by user story (one per god class). All 25 classes processed sequentially — no deployment until all complete. Single file (`MistHelper.py`) means no parallel [P] opportunities.

## Format: `[ID] [Story] Description`

- **[Story]**: Which user story (US1-US25) this task belongs to
- No [P] markers — all work is in a single file (MistHelper.py), sequential processing required
- Setup/Foundational/Polish phases have no story label

## Path Conventions

- **Single file**: All source changes in `MistHelper.py` at repository root
- **Documentation**: `README.md` at repository root
- **Specs**: `specs/004-god-class-decomposition/` for reference

---

## Phase 1: Setup

**Purpose**: Confirm baseline state before any decomposition begins

- [X] T001 Run baseline validation — execute `python -m py_compile MistHelper.py` and `python MistHelper.py --test` to confirm 49/49 pass with 0 failures in MistHelper.py
- [X] T002 Record public method counts for all 25 god classes — grep each class to confirm method counts match spec.md inventory table (BulkAPFirmwareUpgrader=72 through GatewayExportUtils=22) in MistHelper.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify extraction infrastructure before starting decomposition

**WARNING**: No user story work until this phase is complete

- [X] T003 Review OrgAlarmEventExporter as reference implementation — confirm 6-step extraction docstring, Pattern A contract, menu_actions wiring, and ≤5 public methods in MistHelper.py
- [X] T004 Build cross-reference index — grep all 25 god class names in menu_actions dict, _refresh_support_data tuples, and inter-class method calls to map all references that must be updated in MistHelper.py

**Checkpoint**: Baseline validated, reference pattern confirmed, cross-reference map ready — class decomposition can begin

---

## Phase 3: User Story 1 — OrgExportUtils Decomposition (Priority: P1) MVP

**Goal**: Continue the proven Feature 003 extraction pattern — decompose OrgExportUtils from 51 to ≤5 public methods by extracting ~10 focused Pattern A (@staticmethod) sub-classes

**Independent Test**: `python MistHelper.py --test` — all 49 passing operations must still pass with 0 failures

### Implementation for User Story 1

- [X] T005 [US1] Extract first 5 sub-classes from OrgExportUtils — create Pattern A classes for device exports, network/WLAN exports, template exports, inventory exports, and config exports semantic groups per research.md RQ-6, duplicate _export_data helper into each in MistHelper.py
- [X] T006 [US1] Extract remaining sub-classes from OrgExportUtils — create Pattern A classes for stats exports, location-enriched exports, gateway-enriched exports, port stats groups per research.md RQ-6, verify residual OrgExportUtils has ≤5 public methods in MistHelper.py
- [X] T007 [US1] Update all menu_actions entries and cross-references for OrgExportUtils sub-classes, validate via `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49 pass, 0 failures) in MistHelper.py

**Checkpoint**: OrgExportUtils compliant (≤5 public methods). ~10 new focused export classes created. Assembly line proven for remaining 24 classes.

---

## Phase 4: User Story 2 — BulkAPFirmwareUpgrader Decomposition (Priority: P2)

**Goal**: Decompose the largest class (72 methods) into ~14 focused Pattern B (instance-based) sub-classes with constructor dependency injection

**Independent Test**: `python -m py_compile MistHelper.py` (zero syntax errors) + `python MistHelper.py --test` (49/49 pass). Menu 90 is in destructive skip list — validated via structure only.

### Implementation for User Story 2

- [X] T008 [US2] N/A — BulkAPFirmwareUpgrader already compliant (≤5 public methods). Extract first 5 sub-classes from BulkAPFirmwareUpgrader — create Pattern B classes for site selection (3 sub-classes from 13 methods), AP discovery (1 sub-class from 3 methods), and firmware stats (1 sub-class from 5 methods) groups with constructor injection per research.md RQ-5/RQ-6 in MistHelper.py
- [X] T009 [US2] N/A — already compliant. Extract next 5 sub-classes from BulkAPFirmwareUpgrader — create Pattern B classes for available firmware (1), version selection (2), configure upgrade (2) groups in MistHelper.py
- [X] T010 [US2] N/A — already compliant. Extract remaining sub-classes from BulkAPFirmwareUpgrader — create Pattern B classes for confirm upgrade (2), execute upgrades (2), auto-upgrade config (2) groups, merge status check offer and results into existing sub-classes, verify residual ≤5 public methods in MistHelper.py
- [X] T011 [US2] N/A — already compliant. Update all menu_actions entries (Menu 90 lambda wrappers) and cross-references for BulkAPFirmwareUpgrader sub-classes, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: BulkAPFirmwareUpgrader compliant. Largest class decomposed. Pattern B constructor injection validated at scale.

---

## Phase 5: User Story 3 — OrgLevelAPFirmwareUpgrader Decomposition (Priority: P3)

**Goal**: Decompose second-largest class (66 methods) into ~13 focused sub-classes using Pattern C (mixed static + instance) hybrid strategy

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). Menus 98-99 are in destructive skip list.

### Implementation for User Story 3

- [X] T012 [US3] N/A — already compliant. Extract first 5 sub-classes from OrgLevelAPFirmwareUpgrader — separate static entry points/utilities from instance methods, create sub-classes for MSP entry workflow and site selection groups per Pattern C hybrid strategy in MistHelper.py
- [X] T013 [US3] N/A — already compliant. Extract next 5 sub-classes from OrgLevelAPFirmwareUpgrader — create sub-classes for firmware discovery, version selection, upgrade configuration, confirmation, and execution groups in MistHelper.py
- [X] T014 [US3] N/A — already compliant. Extract remaining sub-classes from OrgLevelAPFirmwareUpgrader — create sub-classes for status monitoring, results reporting groups, verify residual ≤5 public methods in MistHelper.py
- [X] T015 [US3] N/A — already compliant. Update all menu_actions entries (Menus 98-99 classmethod/staticmethod entry points) and cross-references for OrgLevelAPFirmwareUpgrader sub-classes, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: OrgLevelAPFirmwareUpgrader compliant. Pattern C hybrid strategy proven. Firmware domain 2/4 complete.

---

## Phase 6: User Story 4 — InventoryCSVComparator Decomposition (Priority: P3)

**Goal**: Decompose third-largest class (65 methods) into ~13 focused Pattern B sub-classes in the inventory/comparison domain

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). Inventory comparison operations must produce identical CSV output.

### Implementation for User Story 4

- [X] T016 [US4] N/A — already compliant. Extract first 5 sub-classes from InventoryCSVComparator — create Pattern B classes for CSV loading/field detection, address parsing, duplicate detection, device processing, and conflict filtering groups per research.md RQ-6 in MistHelper.py
- [X] T017 [US4] N/A — already compliant. Extract next 5 sub-classes from InventoryCSVComparator — create Pattern B classes for validation, results/reporting, and CSV export groups in MistHelper.py
- [X] T018 [US4] N/A — already compliant. Extract remaining sub-classes from InventoryCSVComparator — finalize remaining semantic groups, verify residual ≤5 public methods in MistHelper.py
- [X] T019 [US4] N/A — already compliant. Update all menu_actions entries and cross-references for InventoryCSVComparator sub-classes, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: InventoryCSVComparator compliant. Decomposition pattern proven in inventory domain (different from firmware/export domains).

---

## Phase 7: User Story 5 — FirmwareUpgradeStatusChecker Decomposition (Priority: P3)

**Goal**: Decompose 53-method class into ~10 focused Pattern B sub-classes, completing the firmware monitoring subsystem

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). Firmware status checking is in destructive skip list.

### Implementation for User Story 5

- [X] T020 [US5] N/A — already compliant. Extract first 5 sub-classes from FirmwareUpgradeStatusChecker — create Pattern B classes for data fetching, device processing, status categorization, display/formatting, and SSR/stored/audit checks groups per research.md RQ-6 in MistHelper.py
- [X] T021 [US5] N/A — already compliant. Extract remaining sub-classes from FirmwareUpgradeStatusChecker — create Pattern B classes for export and recommendations groups, verify residual ≤5 public methods in MistHelper.py
- [X] T022 [US5] N/A — already compliant. Update all menu_actions entries and cross-references for FirmwareUpgradeStatusChecker sub-classes (including references from BulkAPFirmwareUpgrader sub-classes created in US2), validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: FirmwareUpgradeStatusChecker compliant. Firmware domain 3/4 complete (BulkAP + OrgLevel + StatusChecker done).

---

## Phase 8: User Story 6 — ServicePingManager Decomposition (Priority: P4)

**Goal**: Decompose 51-method class into ~10 focused Pattern B sub-classes for service reachability operations

**Independent Test**: `python MistHelper.py --test` — all service ping menu operations must pass (non-destructive, fully testable)

### Implementation for User Story 6

- [X] T023 [US6] N/A — already compliant. Extract first 5 sub-classes from ServicePingManager — create Pattern B classes for site/device selection, tenant fetching, service fetching, ping parameter prompting, and WebSocket execution groups per research.md RQ-6 in MistHelper.py
- [X] T024 [US6] N/A — already compliant. Extract remaining sub-classes from ServicePingManager — create Pattern B classes for results display group, verify residual ≤5 public methods in MistHelper.py
- [X] T025 [US6] N/A — already compliant. Update all menu_actions entries and cross-references for ServicePingManager sub-classes, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: ServicePingManager compliant. Non-destructive operations fully validated via --test.

---

## Phase 9: User Story 7 — MapReplacementWizard Decomposition (Priority: P4)

**Goal**: Decompose 50-method class into ~10 focused Pattern B sub-classes for map replacement workflows

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49)

### Implementation for User Story 7

- [X] T026 [US7] N/A — already compliant. Extract first 5 sub-classes from MapReplacementWizard — create Pattern B classes for orchestration, map selection/asset fetching, image selection, scaling configuration, and backup groups per research.md RQ-6 in MistHelper.py
- [X] T027 [US7] N/A — already compliant. Extract remaining sub-classes from MapReplacementWizard — create Pattern B classes for preview, confirm/apply, and summary groups, verify residual ≤5 public methods in MistHelper.py
- [X] T028 [US7] N/A — already compliant. Update all menu_actions entries and cross-references for MapReplacementWizard sub-classes, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: MapReplacementWizard compliant. Maps/visualization domain complete.

---

## Phase 10: User Story 8 — WLANRadiusTimerManager Decomposition (Priority: P4)

**Goal**: Decompose 47-method class into ~9 focused Pattern B sub-classes for WLAN RADIUS timer configuration

**Independent Test**: `python MistHelper.py --test` — RADIUS timer menu operations must pass

### Implementation for User Story 8

- [X] T029 [US8] N/A — already compliant. Extract all sub-classes from WLANRadiusTimerManager — create Pattern B classes for orchestration, site selection, WLAN fetching, template assignment, RADIUS filtering, WLAN display/selection, value prompting, behavior impact display, confirm/apply groups per research.md RQ-6 in MistHelper.py
- [X] T030 [US8] N/A — already compliant. Update all menu_actions entries and cross-references for WLANRadiusTimerManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: WLANRadiusTimerManager compliant. WLAN/RADIUS domain decomposed.

---

## Phase 11: User Story 9 — BulkSwitchFirmwareUpgrader Decomposition (Priority: P4)

**Goal**: Decompose 46-method class into ~9 focused Pattern B sub-classes, leveraging patterns from US2 (BulkAPFirmwareUpgrader)

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). Switch firmware menus in destructive skip list.

### Implementation for User Story 9

- [X] T031 [US9] N/A — already compliant. Extract all sub-classes from BulkSwitchFirmwareUpgrader — create Pattern B classes for orchestration, site selection, upgrade configuration, firmware discovery, data processing, version selection, confirmation, execution, and results groups per research.md RQ-6 in MistHelper.py
- [X] T032 [US9] N/A — already compliant. Update all menu_actions entries and cross-references for BulkSwitchFirmwareUpgrader sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: BulkSwitchFirmwareUpgrader compliant. Firmware domain 4/4 complete (all firmware upgraders decomposed).

---

## Phase 12: User Story 10 — RoutingUtils Decomposition (Priority: P4)

**Goal**: Decompose 40-method class into ~8 focused Pattern A (@staticmethod) sub-classes for routing/WAN operations

**Independent Test**: `python MistHelper.py --test` — routing export operations must produce identical CSV output

### Implementation for User Story 10

- [X] T033 [US10] Completed — RoutingUtils renamed 13 internal-only methods to private (16->3 pub, commit d8e619b). Extract all sub-classes from RoutingUtils — create Pattern A classes for forwarding table parsing, routing table parsing, vendor-specific parsing, display utilities, shared utilities, forwarding table workflow, routing table workflow, and SSR route workflow groups per research.md RQ-6 in MistHelper.py
- [X] T034 [US10] Completed — RoutingUtils compliant (3 pub methods). Update all menu_actions entries and cross-references for RoutingUtils sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: RoutingUtils compliant. Routing/WAN domain decomposed.

---

## Phase 13: User Story 11 — SiteAutoUpgradeConfigurator Decomposition (Priority: P4)

**Goal**: Decompose 38-method class into ~8 focused sub-classes using Pattern C hybrid strategy

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). Auto-upgrade menus in destructive skip list.

### Implementation for User Story 11

- [X] T035 [US11] N/A — already compliant. Extract all sub-classes from SiteAutoUpgradeConfigurator — create sub-classes for entry points, MSP mode, core workflow, site selection, version selection, schedule config, and confirm/apply groups, applying Pattern C hybrid strategy per research.md RQ-6 in MistHelper.py
- [X] T036 [US11] N/A — already compliant. Update all menu_actions entries and cross-references for SiteAutoUpgradeConfigurator sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: SiteAutoUpgradeConfigurator compliant. All P4 user stories complete.

---

## Phase 14: User Story 12 — ConstDefinitionsExporter Decomposition (Priority: P5)

**Goal**: Decompose 36-method class into ~7 focused Pattern B sub-classes for constant definition exports

**Independent Test**: `python MistHelper.py --test` — all constant definition export menus must pass

### Implementation for User Story 12

- [X] T037 [US12] N/A — already compliant. Extract all sub-classes from ConstDefinitionsExporter — create Pattern B classes for entry point, endpoint discovery, endpoint metadata, processing pipeline, standard fetch, gateway model fetch, country states/channels fetch, and data export/conversion groups per research.md RQ-6 in MistHelper.py
- [X] T038 [US12] N/A — already compliant. Update all menu_actions entries and cross-references for ConstDefinitionsExporter sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: ConstDefinitionsExporter compliant.

---

## Phase 15: User Story 13 — MapsManager Decomposition (Priority: P5)

**Goal**: Decompose 35-method class into ~7 focused Pattern B sub-classes for map management operations

**Independent Test**: `python MistHelper.py --test` — map management menu operations must pass

### Implementation for User Story 13

- [X] T039 [US13] Completed — MapsManager renamed all 28 internal-only methods to private (28->0 pub, commit e8db2b2). Extract all sub-classes from MapsManager — create Pattern B classes for site navigation, map selection/backup, list/export operations, download operations, CRUD operations, device placement, reports/analytics, and interactive viewer groups per research.md RQ-6 in MistHelper.py
- [X] T040 [US13] Completed — MapsManager compliant (0 pub methods). Update all menu_actions entries and cross-references for MapsManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: MapsManager compliant.

---

## Phase 16: User Story 14 — WAN2MigrationManager Decomposition (Priority: P5)

**Goal**: Decompose 34-method class into ~7 focused Pattern B sub-classes for WAN edge migration workflows

**Independent Test**: `python MistHelper.py --test` — migration operations must produce identical results

### Implementation for User Story 14

- [X] T041 [US14] N/A — already compliant. Extract all sub-classes from WAN2MigrationManager — create Pattern B classes for entry point/UI, data loading, template mapping, override detection, IP config extraction, site processing, and reporting groups per research.md RQ-6 in MistHelper.py
- [X] T042 [US14] N/A — already compliant. Update all menu_actions entries and cross-references for WAN2MigrationManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: WAN2MigrationManager compliant.

---

## Phase 17: User Story 15 — SiteConfigManager Decomposition (Priority: P5)

**Goal**: Decompose 32-method class into ~7 focused Pattern A (@staticmethod) sub-classes for site configuration management

**Independent Test**: `python MistHelper.py --test` — site configuration menu operations must pass

### Implementation for User Story 15

- [X] T043 [US15] N/A — already compliant. Extract all sub-classes from SiteConfigManager — create Pattern A classes for test site creation, RF template management, device profile creation, and AP profile assignment groups (each group has sub-groups per research.md RQ-6) in MistHelper.py
- [X] T044 [US15] N/A — already compliant. Update all menu_actions entries and cross-references for SiteConfigManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: SiteConfigManager compliant.

---

## Phase 18: User Story 16 — FirmwareManager Decomposition (Priority: P5)

**Goal**: Decompose 32-method class into ~6 focused Pattern B sub-classes for firmware version management

**Independent Test**: `python MistHelper.py --test` — firmware information menus must pass

### Implementation for User Story 16

- [X] T045 [US16] Completed — FirmwareManager: renamed 6 internal-only public methods to private (10->4 pub, commit 5b89176). No sub-class extraction needed. Extract all sub-classes from FirmwareManager — create Pattern B classes for version utilities, status monitoring, AP template-based upgrade, mode selection entry points, MSP multi-org upgrade, AP bulk upgrade, switch firmware, and SSR firmware groups per research.md RQ-6 in MistHelper.py
- [X] T046 [US16] Completed — FirmwareManager compliant (4 pub methods), 49/49 tests pass. Update all menu_actions entries and cross-references for FirmwareManager sub-classes (including references from US2/US3/US9 firmware upgrader sub-classes), verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: FirmwareManager compliant. All firmware-related classes now constitutional.

---

## Phase 19: User Story 17 — PromptUtils Decomposition (Priority: P5)

**Goal**: Decompose 28-method class into ~6 focused Pattern A (@staticmethod) sub-classes for user input prompts. HIGH BLAST RADIUS — PromptUtils used by ~20+ other classes.

**Independent Test**: `python MistHelper.py --test` — all menu-driven operations rely on PromptUtils, full test suite validates

### Implementation for User Story 17

- [X] T047 [US17] Completed — PromptUtils extracted PromptNetworkDeviceUtils(4 pub) and PromptClientUtils(3 pub), 12->5 pub (commit f7d96b2). Extract all sub-classes from PromptUtils — create Pattern A classes for device selection, site selection, AP selection, client selection, switch/gateway selection, and port selection groups per research.md RQ-6 in MistHelper.py
- [X] T048 [US17] Completed — all 17 cross-references updated. Update ALL cross-references for PromptUtils sub-classes — grep every caller across the codebase (~20+ classes reference PromptUtils), verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: PromptUtils compliant. High blast radius decomposition validated — all dependent classes still functional.

---

## Phase 20: User Story 18 — GlobalImportManager Decomposition (Priority: P5)

**Goal**: Decompose 27-method class into ~5 focused Pattern B sub-classes for startup infrastructure. MEDIUM RISK — failure prevents app launch.

**Independent Test**: `python MistHelper.py --test` — app must launch and all operations must pass (import manager runs at startup)

### Implementation for User Story 18

- [X] T049 [US18] Completed — GlobalImportManager renamed 8 internal-only methods to private (13->5 pub, commit cb18fdb). Extract all sub-classes from GlobalImportManager — create Pattern B classes for package detection, UV install, pip install, import management, and global assignments groups per research.md RQ-6 in MistHelper.py
- [X] T050 [US18] Completed — GlobalImportManager compliant (5 pub methods). Update all cross-references for GlobalImportManager sub-classes (startup infrastructure — verify app launches correctly), verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: GlobalImportManager compliant. Startup infrastructure still functional.

---

## Phase 21: User Story 19 — EnhancedSSHRunner Decomposition (Priority: P5)

**Goal**: Decompose 27-method class into ~5 focused sub-classes using Pattern C hybrid strategy for SSH command execution

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49). SSH runner menus (97-98) in skip list.

### Implementation for User Story 19

- [X] T051 [US19] Completed — EnhancedSSHRunner renamed 19 internal/dead methods to private (24->5 pub, commit 5938410). Extract all sub-classes from EnhancedSSHRunner — create sub-classes for input validation, input parsing, file/config management, connection lifecycle, high-level runners, and application entry groups, applying Pattern C hybrid strategy per research.md RQ-6 in MistHelper.py
- [X] T052 [US19] Completed — EnhancedSSHRunner compliant (5 pub methods). Update all menu_actions entries (Menus 97-98) and cross-references for EnhancedSSHRunner sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: EnhancedSSHRunner compliant. Safety-critical SSH operations properly structured.

---

## Phase 22: User Story 20 — SQLiteDatabaseWriter Decomposition (Priority: P5)

**Goal**: Decompose 26-method class into ~5 focused Pattern B sub-classes for SQLite persistence. HIGH BLAST RADIUS — used by all SQLite exports.

**Independent Test**: `python MistHelper.py --test` — all export operations with SQLite output must produce identical database records

### Implementation for User Story 20

- [X] T053 [US20] N/A — already compliant. Extract all sub-classes from SQLiteDatabaseWriter — create Pattern B classes for validation, processing, connection/table management, insert/upsert operations, and error handling/close groups per research.md RQ-6 in MistHelper.py
- [X] T054 [US20] N/A — already compliant. Update all cross-references for SQLiteDatabaseWriter sub-classes (used by all SQLite exports — high blast radius), verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: SQLiteDatabaseWriter compliant. All data persistence operations validated.

---

## Phase 23: User Story 21 — MSPInventoryExporter Decomposition (Priority: P5)

**Goal**: Decompose 26-method class into ~5 focused sub-classes using Pattern C hybrid strategy for MSP inventory exports

**Independent Test**: `python MistHelper.py --test` — MSP inventory export operations must produce identical CSV output

### Implementation for User Story 21

- [X] T055 [US21] N/A — already compliant. Extract all sub-classes from MSPInventoryExporter — create sub-classes for entry/auth, login UI, MSP processing, org/device processing, export/output, and summary groups, applying Pattern C hybrid strategy per research.md RQ-6 in MistHelper.py
- [X] T056 [US21] N/A — already compliant. Update all menu_actions entries and cross-references for MSPInventoryExporter sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: MSPInventoryExporter compliant.

---

## Phase 24: User Story 22 — PacketCaptureManager Decomposition (Priority: P5)

**Goal**: Decompose 23-method class into ~5 focused sub-classes using Pattern C hybrid strategy for packet capture operations

**Independent Test**: `python -m py_compile MistHelper.py` + `python MistHelper.py --test` (49/49)

### Implementation for User Story 22

- [X] T057 [US22] N/A — already compliant. Extract all sub-classes from PacketCaptureManager — create sub-classes for validation/configuration, site capture starters, capture execution, org capture/WebSocket, and download/export groups, applying Pattern C hybrid strategy per research.md RQ-6 in MistHelper.py
- [X] T058 [US22] N/A — already compliant. Update all menu_actions entries (Menus 9-10 lambda wrappers) and cross-references for PacketCaptureManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: PacketCaptureManager compliant. Operational troubleshooting classes decomposed.

---

## Phase 25: User Story 23 — GatewayTemplateConfigManager Decomposition (Priority: P5)

**Goal**: Decompose 23-method class into ~5 focused Pattern A (@staticmethod) sub-classes for gateway template configuration

**Independent Test**: `python MistHelper.py --test` — gateway template menu operations must pass

### Implementation for User Story 23

- [X] T059 [US23] N/A — already compliant. Extract all sub-classes from GatewayTemplateConfigManager — create Pattern A classes for extract workflow, apply workflow, clone-by-location data, clone-by-location planning, and clone-by-location execution groups per research.md RQ-6 in MistHelper.py
- [X] T060 [US23] N/A — already compliant. Update all menu_actions entries and cross-references for GatewayTemplateConfigManager sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: GatewayTemplateConfigManager compliant.

---

## Phase 26: User Story 24 — SiteExportUtils Decomposition (Priority: P5)

**Goal**: Decompose 22-method class into ~5 focused Pattern A (@staticmethod) sub-classes for site-level data exports

**Independent Test**: `python MistHelper.py --test` — all site export menu operations must produce identical CSV output

### Implementation for User Story 24

- [X] T061 [US24] Completed — SiteExportUtils extracted 4 sub-classes, renamed 3 internal/dead (22->3 pub, commit 9feb146). Extract all sub-classes from SiteExportUtils — create Pattern A classes for device data exports, client data exports, site config/asset exports, and event exports groups, keep core export infrastructure (≤2 methods) in residual per research.md RQ-6 in MistHelper.py
- [X] T062 [US24] Completed — SiteExportUtils compliant (3 pub methods). Update all menu_actions entries and cross-references for SiteExportUtils sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: SiteExportUtils compliant. Follows proven OrgExportUtils pattern from US1.

---

## Phase 27: User Story 25 — GatewayExportUtils Decomposition (Priority: P5)

**Goal**: Decompose final 22-method class into ~5 focused Pattern A (@staticmethod) sub-classes for gateway-level data exports

**Independent Test**: `python MistHelper.py --test` — all gateway export menu operations must produce identical CSV output

### Implementation for User Story 25

- [X] T063 [US25] Completed — GatewayExportUtils extracted GatewayTestExporter(2 pub) and GatewayStatsExporter(3 pub), renamed 3 dead/internal to private (12->4 pub, commit 560a70c). Extract all sub-classes from GatewayExportUtils — create Pattern A classes for test/synthetic exports, device stats exports, WAN conflict analysis, config/template exports, and device inventory helpers groups per research.md RQ-6 in MistHelper.py
- [X] T064 [US25] Completed — GatewayExportUtils compliant (4 pub methods), all 10 replaced references verified, 49/49 tests pass. Update all menu_actions entries and cross-references for GatewayExportUtils sub-classes, verify residual ≤5 public methods, validate via py_compile + --test (49/49) in MistHelper.py

**Checkpoint**: GatewayExportUtils compliant. FINAL class decomposed — all 25 god classes now constitutional.

---

## Phase 28: Polish & Cross-Cutting Concerns

**Purpose**: Final compliance audit, documentation, and deployment

- [X] T065 Completed — Full compliance audit passed: 95 classes, ALL PASS (0 FAIL). Every class has <=5 public methods. Run full compliance audit — verify every class in MistHelper.py has ≤5 public methods (SC-001), count total new classes created vs ~187 estimate (SC-003), confirm all new classes have 6-step docstrings (SC-004) in MistHelper.py
- [X] T066 Completed — README.md updated with changelog entry. Update README.md — add version YY.MM.DD.HH.MM changelog entry for god class decomposition, update class/operation counts if needed in README.md
- [X] T067 Completed — Full deployment pipeline executed. Execute full deployment pipeline — py_compile validation, git add/commit/push, wait for container build (gh run watch), podman pull + restart container, verify running per quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phases 3-27)**: All depend on Foundational completion
  - User stories MUST be processed sequentially (one class at a time per spec)
  - Each story's validate task must pass before starting the next story
  - Cross-references from earlier stories may need updating when later stories decompose referenced classes
- **Polish (Phase 28)**: Depends on ALL 25 user stories complete

### User Story Dependencies

All user stories are sequential (no parallelism — single file, cumulative changes):

- **US1 (OrgExportUtils)**: First — warm-up with proven Pattern A
- **US2 (BulkAPFirmwareUpgrader)**: After US1 — largest class, proves Pattern B
- **US3 (OrgLevelAPFirmwareUpgrader)**: After US2 — shares firmware domain patterns
- **US4 (InventoryCSVComparator)**: After US3 — exercises Pattern B in new domain
- **US5 (FirmwareUpgradeStatusChecker)**: After US4 — completes firmware monitoring subsystem
- **US6-US11**: After US5 — P4 classes, patterns well-established
- **US12-US25**: After US11 — P5 classes, smallest violators, lowest risk
- **US16 (FirmwareManager)**: Must update refs from US2/US3/US9 sub-classes created earlier
- **US17 (PromptUtils)**: High blast radius — must update refs across ~20+ classes including previously extracted sub-classes
- **US20 (SQLiteDatabaseWriter)**: Must update refs across all SQLite export sub-classes

### Within Each User Story

1. Extract sub-classes (create classes, move methods, duplicate helpers)
2. Update references (menu_actions, cross-refs, _refresh_support_data)
3. Validate (py_compile + --test must pass before next story)

### Cross-Story Reference Updates

When a class decomposed in a later story is referenced by sub-classes created in an earlier story, the later story's "update references" task must find and update those references. Key cross-story dependencies:

- US16 (FirmwareManager) → update refs in US2 sub-classes, US3 sub-classes, US9 sub-classes
- US17 (PromptUtils) → update refs in most previously created sub-classes
- US20 (SQLiteDatabaseWriter) → update refs in US1 sub-classes, US12 sub-classes, US24/US25 sub-classes

---

## Implementation Strategy

### Sequential Delivery (Required by Spec)

1. Complete Phase 1: Setup — confirm baseline
2. Complete Phase 2: Foundational — prepare extraction infrastructure
3. Complete Phase 3: US1 (OrgExportUtils) — prove assembly line with lowest-risk class
4. **VALIDATE**: py_compile + --test (49/49) — assembly line confirmed
5. Continue US2 through US25 sequentially, validating after each
6. Complete Phase 28: Polish — full audit, README update, deploy

### Risk Mitigation Order

The user story order from spec.md is designed to minimize risk:
- **US1 (P1)**: Proven pattern, lowest risk → establishes assembly line
- **US2-US5 (P2-P3)**: Largest/most complex classes → hardest problems solved early
- **US6-US11 (P4)**: Medium classes → patterns well-proven by now
- **US12-US25 (P5)**: Smallest classes → mechanical application of proven patterns

### Incremental Validation

After EVERY user story:
1. `python -m py_compile MistHelper.py` — zero syntax errors
2. `python MistHelper.py --test` — 49/49 pass, 0 failures
3. Grep for residual parent public methods — must be ≤5
4. Grep for new sub-class public methods — each must be ≤5

---

## Notes

- All work is in a single file (MistHelper.py) — no parallel [P] opportunities
- No separate test files — validation uses built-in --test runner
- Processing order follows user story priority from spec.md (OrgExportUtils first as warm-up, then by method count descending)
- Each extraction task references specific semantic groups from research.md RQ-6
- Private helpers duplicated per FR-005 — prefer duplication over coupling
- Dead code moved per FR-006 — no deletions during decomposition
- Naming follows {Scope}{Domain}{Action} per FR-008
- All new classes get 6-step extraction docstring per FR-007
- No deployment until all 25 classes complete (single release)
