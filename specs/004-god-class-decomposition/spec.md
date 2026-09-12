# Feature Specification: God Class Decomposition

**Feature Branch**: `004-god-class-decomposition`  
**Created**: 2026-03-03  
**Status**: Draft  
**Input**: User description: "look for any god-classes and work on breaking them up and bringing them into compliance with our constitution, while not breaking the scripts functionality"

## Problem Statement

MistHelper's `MistHelper.py` contains 25+ classes that violate the Constitution's 5-Item Rule (Principle I), which mandates a maximum of 5 children per class. The worst offenders have 50-72 methods each — up to 14x the constitutional limit. Feature 003 established a proven extraction pattern by decomposing 5 alarm/event methods from `OrgExportUtils` into `OrgAlarmEventExporter`. This feature applies that same proven pattern systematically to bring the most critical god classes into compliance.

### Current Violations Inventory

| Class                        | Methods | Over Limit | Line  |
|------------------------------|---------|------------|-------|
| BulkAPFirmwareUpgrader       | 72      | 14.4x      | 39413 |
| OrgLevelAPFirmwareUpgrader   | 66      | 13.2x      | 42605 |
| InventoryCSVComparator       | 65      | 13x        | 23585 |
| FirmwareUpgradeStatusChecker | 53      | 10.6x      | 38543 |
| OrgExportUtils               | 51      | 10.2x      | 10809 |
| ServicePingManager           | 51      | 10.2x      | 14858 |
| MapReplacementWizard         | 50      | 10x        | 28569 |
| WLANRadiusTimerManager       | 47      | 9.4x       | 45438 |
| BulkSwitchFirmwareUpgrader   | 46      | 9.2x       | 44435 |
| RoutingUtils                 | 40      | 8x         | 15858 |
| SiteAutoUpgradeConfigurator  | 38      | 7.6x       | 41395 |
| ConstDefinitionsExporter     | 36      | 7.2x       | 17516 |
| MapsManager                  | 35      | 7x         | 29338 |
| WAN2MigrationManager         | 34      | 6.8x       | 24724 |
| SiteConfigManager            | 32      | 6.4x       | 27366 |
| FirmwareManager              | 32      | 6.4x       | 36254 |
| PromptUtils                  | 28      | 5.6x       | 9330  |
| GlobalImportManager          | 27      | 5.4x       | 883   |
| EnhancedSSHRunner            | 27      | 5.4x       | 51158 |
| SQLiteDatabaseWriter         | 26      | 5.2x       | 8457  |
| MSPInventoryExporter         | 26      | 5.2x       | 41056 |
| PacketCaptureManager         | 23      | 4.6x       | 4376  |
| GatewayTemplateConfigManager | 23      | 4.6x       | 20437 |
| SiteExportUtils              | 22      | 4.4x       | 12725 |
| GatewayExportUtils           | 22      | 4.4x       | 18693 |

### Scope Decision

This feature addresses **all 25 violating classes** systematically, bringing the entire codebase into constitutional compliance in a single feature.

### Phasing Strategy

**One class at a time, sequential.** User story priority determines implementation order (OrgExportUtils first as warm-up, then largest classes). The table below shows all 25 classes sorted by method count for reference; actual processing order follows the user story numbering (US1-US25). Between each class:
- Validate with Pylance (zero type errors)
- Validate with `python -m py_compile MistHelper.py` (zero syntax errors)
- Run `python MistHelper.py --test` (zero failures on non-skipped operations)

**No deployment until all 25 classes are complete.** The full suite of decompositions is committed and deployed as a single release once all classes pass validation.

**Processing Order** (by method count, descending):
1. BulkAPFirmwareUpgrader (72)
2. OrgLevelAPFirmwareUpgrader (66)
3. InventoryCSVComparator (65)
4. FirmwareUpgradeStatusChecker (53)
5. OrgExportUtils (51)
6. ServicePingManager (51)
7. MapReplacementWizard (50)
8. WLANRadiusTimerManager (47)
9. BulkSwitchFirmwareUpgrader (46)
10. RoutingUtils (40)
11. SiteAutoUpgradeConfigurator (38)
12. ConstDefinitionsExporter (36)
13. MapsManager (35)
14. WAN2MigrationManager (34)
15. SiteConfigManager (32)
16. FirmwareManager (32)
17. PromptUtils (28)
18. GlobalImportManager (27)
19. EnhancedSSHRunner (27)
20. SQLiteDatabaseWriter (26)
21. MSPInventoryExporter (26)
22. PacketCaptureManager (23)
23. GatewayTemplateConfigManager (23)
24. SiteExportUtils (22)
25. GatewayExportUtils (22)

## Clarifications

### Session 2026-03-03

- Q: How should the work be phased across all 25 classes? → A: One class at a time, sequential by method count descending. Validate with Pylance + py_compile + test suite between each class. No deployment until all 25 are complete.
- Q: How should user stories cover all 25 classes? → A: Individual user stories for each class (25 total).
- Q: How should extracted sub-classes access shared instance state (self.mist_session, self.org_id, etc.)? → A: Pass only required dependencies via constructor parameters. Each sub-class receives only what it needs.
- Q: How should decomposed sub-classes be wired into menu_actions? → A: Instantiate each sub-class directly in menu_actions at point of use. No coordinator, factory, or registry.
- Q: What is the target ceiling for the residual parent class after extraction? → A: Strict 5-method limit. The residual parent class MUST also comply — no exemptions. Keep extracting until compliant.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - OrgExportUtils Continues Decomposition (Priority: P1)

A NOC engineer runs any menu option from 1-60 that calls an `OrgExportUtils` method. After decomposition, every operation produces identical output — same CSV files, same console messages, same log entries. The engineer cannot distinguish between the old and new code structure.

OrgExportUtils currently has 51 methods after Feature 003 extracted 5. This story extracts ~10 groups of up to 5 methods each, following the proven `OrgAlarmEventExporter` pattern, until the residual OrgExportUtils has at most 5 public methods (per FR-013).

**Why this priority**: OrgExportUtils already has a proven extraction pattern from Feature 003 — lowest risk, highest confidence. Establishes the assembly line for the harder classes.

**Independent Test**: Run `python MistHelper.py --test` before and after changes. All 49 passing operations must still pass with 0 failures.

**Acceptance Scenarios**:

1. **Given** OrgExportUtils has 51 methods, **When** semantically related methods are extracted into ~10 focused classes, **Then** OrgExportUtils has at most 5 public methods and each new class has at most 5 public methods plus private helpers as needed
2. **Given** a NOC engineer runs any menu option that previously called OrgExportUtils, **When** the operation completes, **Then** the CSV output, console messages, and log entries are identical to the pre-refactoring behavior (excluding log entry timestamps and file generation timestamps; data field values including API timestamps must be identical)
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur and the success count remains at or above 49

---

### User Story 2 - BulkAPFirmwareUpgrader Decomposition (Priority: P2)

A network engineer performs an AP firmware upgrade using Menu 90. The upgrade workflow — device selection, version selection, confirmation prompt, upgrade execution, status monitoring, and result reporting — works identically after the class is decomposed into focused sub-classes.

BulkAPFirmwareUpgrader (72 methods) is the single largest class. It handles device discovery, filtering, firmware version management, upgrade orchestration, status tracking, and result reporting. These are distinct responsibilities that can be separated into focused classes.

**Why this priority**: Largest class in the codebase. Highly complex destructive operation where code clarity directly impacts safety.

**Independent Test**: Code compiles (`py_compile`), all menu references resolve correctly, and the class structure follows the 5-Item Rule. Full functional testing of Menu 90 requires a live Mist environment with test APs (destructive operation — included in skip list).

**Acceptance Scenarios**:

1. **Given** BulkAPFirmwareUpgrader has 72 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur and Menu 90 remains in the skip list (destructive)

---

### User Story 3 - OrgLevelAPFirmwareUpgrader Decomposition (Priority: P3)

A network engineer performs an org-level AP firmware upgrade using Menu 98 or 99. The workflow operates identically after decomposition. OrgLevelAPFirmwareUpgrader (66 methods) shares significant structural similarity with BulkAPFirmwareUpgrader — the decomposition strategy from US2 directly informs this extraction.

**Why this priority**: Second-largest class. Follows the same firmware domain as US2, so lessons learned apply directly.

**Independent Test**: Code compiles, all menu references resolve correctly. Menu 98-99 are destructive operations in the skip list.

**Acceptance Scenarios**:

1. **Given** OrgLevelAPFirmwareUpgrader has 66 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite includes skip list operations 90-100, **When** the test runs, **Then** 0 failures occur on all non-skipped operations

---

### User Story 4 - InventoryCSVComparator Decomposition (Priority: P3)

An engineer runs the inventory comparison workflow. The comparison logic — CSV loading, normalization, matching, delta computation, and reporting — works identically after the class is decomposed. InventoryCSVComparator (65 methods) handles file I/O, data normalization, address parsing, device matching, and report generation — distinct responsibilities.

**Why this priority**: Third-largest class but different domain (inventory vs firmware), so it exercises the decomposition pattern in a new context.

**Independent Test**: Code compiles, all menu references resolve. Run inventory comparison operations to verify functional equivalence.

**Acceptance Scenarios**:

1. **Given** InventoryCSVComparator has 65 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 5 - FirmwareUpgradeStatusChecker Decomposition (Priority: P3)

An engineer monitors firmware upgrade progress. The status checking workflow — polling, progress display, result aggregation, and timeout handling — works identically after decomposition. FirmwareUpgradeStatusChecker (53 methods) is tightly coupled to the firmware upgrade classes but has its own distinct monitoring responsibility.

**Why this priority**: Completes the firmware domain decomposition (with US2 and US3), ensuring the entire firmware subsystem is constitutionally compliant.

**Independent Test**: Code compiles, all references resolve. Firmware status checking is part of the destructive operations skip list.

**Acceptance Scenarios**:

1. **Given** FirmwareUpgradeStatusChecker has 53 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 6 - ServicePingManager Decomposition (Priority: P4)

A NOC engineer runs service reachability/ping operations. ServicePingManager (51 methods) handles service discovery, ping execution, result collection, timeout management, and reporting. After decomposition, all ping operations produce identical results.

**Why this priority**: Tied for 5th-largest class. Non-destructive operations — fully testable via `--test` suite.

**Independent Test**: `py_compile` + Pylance + `--test` between decomposition steps. All service ping menu operations must pass.

**Acceptance Scenarios**:

1. **Given** ServicePingManager has 51 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 7 - MapReplacementWizard Decomposition (Priority: P4)

A NOC engineer replaces map images for sites. MapReplacementWizard (50 methods) handles map file selection, image processing, upload coordination, validation, and status reporting. After decomposition, map replacement workflows produce identical results.

**Why this priority**: Large class (50 methods) in the maps/visualization domain. Exercises the pattern in a different domain than firmware or exports.

**Independent Test**: `py_compile` + Pylance + `--test`. Map operations produce identical output.

**Acceptance Scenarios**:

1. **Given** MapReplacementWizard has 50 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 8 - WLANRadiusTimerManager Decomposition (Priority: P4)

A NOC engineer manages WLAN RADIUS timer configurations. WLANRadiusTimerManager (47 methods) handles WLAN discovery, timer parameter management, bulk configuration, validation, and result reporting. After decomposition, all RADIUS timer operations produce identical results.

**Why this priority**: Large class in the WLAN/RADIUS domain. Feature 002 added this class — decomposition ensures it follows constitutional standards.

**Independent Test**: `py_compile` + Pylance + `--test`. RADIUS timer menu operations must pass.

**Acceptance Scenarios**:

1. **Given** WLANRadiusTimerManager has 47 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 9 - BulkSwitchFirmwareUpgrader Decomposition (Priority: P4)

A network engineer performs bulk switch firmware upgrades. BulkSwitchFirmwareUpgrader (46 methods) handles switch discovery, firmware version management, upgrade orchestration, status tracking, and result reporting. After decomposition, switch upgrade workflows work identically.

**Why this priority**: Firmware domain class — destructive operations in skip list. Follows patterns established by US2 (BulkAPFirmwareUpgrader).

**Independent Test**: `py_compile` + Pylance + `--test`. Switch firmware menus are in the destructive skip list; validated via syntax and structure only.

**Acceptance Scenarios**:

1. **Given** BulkSwitchFirmwareUpgrader has 46 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 10 - RoutingUtils Decomposition (Priority: P4)

A NOC engineer exports or manages routing configurations. RoutingUtils (40 methods) handles route table exports, routing policy management, BGP/OSPF data extraction, and routing report generation. After decomposition, all routing operations produce identical output.

**Why this priority**: Medium-large class in the routing/WAN domain. Non-destructive data export operations.

**Independent Test**: `py_compile` + Pylance + `--test`. Routing export operations must produce identical CSV output.

**Acceptance Scenarios**:

1. **Given** RoutingUtils has 40 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 11 - SiteAutoUpgradeConfigurator Decomposition (Priority: P4)

A network engineer configures site auto-upgrade settings. SiteAutoUpgradeConfigurator (38 methods) handles site selection, upgrade schedule configuration, version management, validation, and bulk application. After decomposition, auto-upgrade configuration works identically.

**Why this priority**: Firmware-adjacent class handling upgrade scheduling. Destructive operations in skip list.

**Independent Test**: `py_compile` + Pylance + `--test`. Auto-upgrade menus are in the destructive skip list.

**Acceptance Scenarios**:

1. **Given** SiteAutoUpgradeConfigurator has 38 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 12 - ConstDefinitionsExporter Decomposition (Priority: P5)

A NOC engineer exports constant definitions (alarm definitions, event types, etc.). ConstDefinitionsExporter (36 methods) handles API endpoint mapping, data flattening, categorization, and output formatting. After decomposition, all constant definition exports produce identical output.

**Why this priority**: Data export class — non-destructive, fully testable. Follows OrgExportUtils decomposition patterns.

**Independent Test**: `py_compile` + Pylance + `--test`. All constant definition export menus must pass.

**Acceptance Scenarios**:

1. **Given** ConstDefinitionsExporter has 36 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 13 - MapsManager Decomposition (Priority: P5)

A NOC engineer manages site maps (floor plans, campus maps). MapsManager (35 methods) handles map listing, image upload, coordinate management, map metadata, and visualization. After decomposition, all map management operations work identically.

**Why this priority**: Visualization domain class. Non-destructive operations are testable.

**Independent Test**: `py_compile` + Pylance + `--test`. Map management menu operations must pass.

**Acceptance Scenarios**:

1. **Given** MapsManager has 35 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 14 - WAN2MigrationManager Decomposition (Priority: P5)

A network engineer performs WAN edge migrations. WAN2MigrationManager (34 methods) handles device inventory, migration planning, configuration conversion, execution, and result validation. After decomposition, migration workflows work identically.

**Why this priority**: Migration domain class. Complex operations that benefit from clear code structure.

**Independent Test**: `py_compile` + Pylance + `--test`. Migration operations produce identical results.

**Acceptance Scenarios**:

1. **Given** WAN2MigrationManager has 34 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 15 - SiteConfigManager Decomposition (Priority: P5)

A NOC engineer manages site configurations. SiteConfigManager (32 methods) handles site settings retrieval, configuration comparison, bulk updates, validation, and reporting. After decomposition, all site configuration operations produce identical results.

**Why this priority**: Core configuration management class. Non-destructive read operations are testable.

**Independent Test**: `py_compile` + Pylance + `--test`. Site configuration menu operations must pass.

**Acceptance Scenarios**:

1. **Given** SiteConfigManager has 32 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 16 - FirmwareManager Decomposition (Priority: P5)

A network engineer accesses firmware version information and management. FirmwareManager (32 methods) handles firmware version listing, compatibility checking, download management, and version comparison. After decomposition, firmware information operations work identically.

**Why this priority**: Firmware domain base class. Supports the higher-priority firmware upgrader classes.

**Independent Test**: `py_compile` + Pylance + `--test`. Firmware information menus must pass.

**Acceptance Scenarios**:

1. **Given** FirmwareManager has 32 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 17 - PromptUtils Decomposition (Priority: P5)

A NOC engineer interacts with menu prompts and selections. PromptUtils (28 methods) handles user input prompting, selection validation, multi-select management, confirmation dialogs, and input formatting. After decomposition, all prompt interactions behave identically.

**Why this priority**: Core utility class used by many operations. Changes here have high blast radius — careful decomposition required.

**Independent Test**: `py_compile` + Pylance + `--test`. All menu-driven operations rely on PromptUtils — full test suite validates.

**Acceptance Scenarios**:

1. **Given** PromptUtils has 28 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 18 - GlobalImportManager Decomposition (Priority: P5)

When a NOC engineer launches MistHelper, GlobalImportManager (27 methods) ensures all required Python packages are installed and modules are imported. It handles package detection, UV-based installation, pip fallback installation, dynamic module importing, and global variable assignment. After decomposition, the startup import sequence works identically — the application launches and all dependencies resolve correctly.

**Why this priority**: Startup infrastructure — failure prevents app launch. Careful decomposition preserves the package detection and import orchestration sequence.

**Independent Test**: `py_compile` + Pylance + `--test`. Application must launch successfully — GlobalImportManager runs at startup before any menu operations.

**Acceptance Scenarios**:

1. **Given** GlobalImportManager has 27 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 19 - EnhancedSSHRunner Decomposition (Priority: P5)

A NOC engineer runs SSH commands against network devices. EnhancedSSHRunner (27 methods) handles connection management, command execution, output collection, session logging, and result formatting. After decomposition, SSH command workflows work identically.

**Why this priority**: SSH operations are safety-critical. Clear code structure directly impacts operational reliability.

**Independent Test**: `py_compile` + Pylance + `--test`. SSH runner menus (97-98) are in the skip list; validated via syntax and structure.

**Acceptance Scenarios**:

1. **Given** EnhancedSSHRunner has 27 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 20 - SQLiteDatabaseWriter Decomposition (Priority: P5)

A NOC engineer uses SQLite output mode for data persistence. SQLiteDatabaseWriter (26 methods) handles table creation, schema management, upsert logic, index management, and query execution. After decomposition, all SQLite operations produce identical database output.

**Why this priority**: Core infrastructure class. All data export operations depend on this when SQLite mode is enabled.

**Independent Test**: `py_compile` + Pylance + `--test`. All export operations with SQLite output must produce identical database records.

**Acceptance Scenarios**:

1. **Given** SQLiteDatabaseWriter has 26 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 21 - MSPInventoryExporter Decomposition (Priority: P5)

A NOC engineer exports MSP (Managed Service Provider) inventory data. MSPInventoryExporter (26 methods) handles multi-org inventory collection, data aggregation, filtering, and CSV/SQLite output. After decomposition, MSP inventory exports produce identical output.

**Why this priority**: MSP-specific export class. Non-destructive, follows OrgExportUtils patterns.

**Independent Test**: `py_compile` + Pylance + `--test`. MSP inventory export operations must produce identical CSV output.

**Acceptance Scenarios**:

1. **Given** MSPInventoryExporter has 26 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 22 - PacketCaptureManager Decomposition (Priority: P5)

A NOC engineer performs packet captures on wireless clients, wired ports, or switches. PacketCaptureManager (23 methods) handles capture target selection, parameter configuration, capture execution, file retrieval, and result display. After decomposition, all packet capture workflows work identically.

**Why this priority**: Operational troubleshooting class. Menus 9-10 — interactive operations.

**Independent Test**: `py_compile` + Pylance + `--test`. Packet capture operations must compile and pass structural validation.

**Acceptance Scenarios**:

1. **Given** PacketCaptureManager has 23 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 23 - GatewayTemplateConfigManager Decomposition (Priority: P5)

A NOC engineer manages gateway template configurations. GatewayTemplateConfigManager (23 methods) handles template listing, configuration comparison, bulk updates, and export. After decomposition, all gateway template operations produce identical results.

**Why this priority**: Configuration management class. Non-destructive read operations are testable.

**Independent Test**: `py_compile` + Pylance + `--test`. Gateway template menu operations must pass.

**Acceptance Scenarios**:

1. **Given** GatewayTemplateConfigManager has 23 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 24 - SiteExportUtils Decomposition (Priority: P5)

A NOC engineer exports site-level data (device stats, client stats, site settings). SiteExportUtils (22 methods) handles site data retrieval, flattening, and CSV/SQLite output. After decomposition, all site export operations produce identical output.

**Why this priority**: Data export class — follows OrgExportUtils patterns. Non-destructive and fully testable.

**Independent Test**: `py_compile` + Pylance + `--test`. All site export menu operations must produce identical CSV output.

**Acceptance Scenarios**:

1. **Given** SiteExportUtils has 22 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### User Story 25 - GatewayExportUtils Decomposition (Priority: P5)

A NOC engineer exports gateway-level data (gateway configs, routing tables, WAN metrics). GatewayExportUtils (22 methods) handles gateway data retrieval, flattening, and CSV/SQLite output. After decomposition, all gateway export operations produce identical output.

**Why this priority**: Final data export class — follows the established OrgExportUtils/SiteExportUtils patterns. Smallest violator — lowest risk.

**Independent Test**: `py_compile` + Pylance + `--test`. All gateway export menu operations must produce identical CSV output.

**Acceptance Scenarios**:

1. **Given** GatewayExportUtils has 22 methods, **When** methods are extracted into focused sub-classes, **Then** no resulting class exceeds 5 public methods (excluding private helpers)
2. **Given** the decomposed classes exist, **When** `python -m py_compile MistHelper.py` runs, **Then** zero syntax errors occur
3. **Given** the `--test` suite runs, **When** all non-skipped operations execute, **Then** 0 failures occur

---

### Edge Cases

- What happens when two extracted classes need to share a helper method (e.g., `_export_data`)? Each class gets its own private copy, per the R3 pattern from Feature 003.
- What happens when a method in one class calls a method in the class being decomposed? All cross-references must be updated to point to the new class.
- What happens when a method is only called internally (dead code with no menu entry or cross-reference)? Dead code is still moved to maintain semantic grouping, per the R4 pattern from Feature 003.
- What happens when extracted classes have circular dependencies? This indicates the grouping is wrong — re-evaluate the semantic groups to ensure each class is self-contained.
- What happens when a private helper method is used by methods that end up in different extracted classes? Duplicate the helper into each class that needs it. Prefer duplication over coupling.
- What happens when a sub-class needs shared instance state (e.g., `self.mist_session`, `self.org_id`)? Pass only the required dependencies as constructor parameters. Each sub-class stores only what it needs — no bloated constructors copying the full parent `__init__`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each god class MUST be decomposed into focused sub-classes where no sub-class exceeds 5 public methods
- **FR-002**: All `menu_actions` dictionary entries MUST be updated to reference new class names after extraction
- **FR-003**: All cross-references (e.g., `_refresh_support_data()` tuples, internal calls) MUST be updated to reference new class names
- **FR-004**: Each extracted method MUST preserve identical behavior — same parameters, same return values, same API calls, same error handling, same logging output
- **FR-005**: Private helper methods (e.g., `_export_data()`) MUST be duplicated into each new class that needs them, not shared via inheritance or imports
- **FR-011**: For classes using instance state (`self`), each extracted sub-class MUST receive only its required dependencies via constructor parameters — not a copy of the full parent `__init__`
- **FR-012**: Each extracted sub-class MUST be instantiated directly in `menu_actions` at point of use — no coordinator, factory, or registry patterns
- **FR-013**: The residual parent class MUST also have at most 5 public methods after extraction — no class gets an exemption from the 5-Item Rule. If the residual exceeds 5, continue extracting sub-classes until compliant
- **FR-006**: Dead code methods (methods with no callers) MUST be moved to their semantically appropriate new class rather than deleted
- **FR-007**: Each new class MUST include a docstring documenting the extraction pattern (the 6-step process from Feature 003's `OrgAlarmEventExporter`)
- **FR-008**: Naming for new classes MUST follow the `{Scope}{Domain}{Action}` convention (e.g., `OrgAlarmEventExporter`, `APFirmwareDeviceSelector`)
- **FR-009**: The decomposition MUST NOT change any user-visible behavior — CSV output, console messages, and operational results MUST be identical
- **FR-010**: Each decomposition phase MUST pass `python -m py_compile MistHelper.py` before proceeding to the next phase

### Key Entities

- **God Class**: A class with more than 5 public methods, violating the Constitution's 5-Item Rule
- **Focused Sub-Class**: A new class extracted from a god class, containing at most 5 semantically related public methods plus private helpers
- **Extraction Group**: A set of up to 5 semantically related methods identified for extraction into a single focused sub-class
- **Cross-Reference**: Any code location outside the class that references one of its methods (menu entries, support data tuples, direct calls)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After completing all user stories, all 25 target god classes are decomposed such that no resulting class — including the residual parent — has more than 5 public methods
- **SC-002**: The `--test` suite produces 0 failures across all non-skipped operations after each user story is completed
- **SC-003**: Total class count in MistHelper.py increases (new focused classes), while the method count per class decreases to at most 5 public methods per class for all newly created and modified classes
- **SC-004**: Every new class includes a docstring documenting the 6-step extraction pattern, enabling any developer to follow the documented process for future maintenance
- **SC-005**: Zero user-visible behavior changes — a NOC engineer operating any menu option cannot distinguish between pre- and post-refactoring operation (excluding log entry timestamps and file generation timestamps)

## Assumptions

- The proven extraction pattern from Feature 003 (`OrgAlarmEventExporter`) applies to all god classes, though firmware classes may require more nuanced grouping due to complex internal dependencies
- Methods within each god class can be grouped into semantically coherent clusters of at most 5 without breaking internal call chains
- The `@staticmethod` pattern used in `OrgExportUtils` applies only to stateless export classes. For classes using instance state (`self`), extracted sub-classes receive required dependencies via constructor parameters — each sub-class gets only what it needs
- All 25 god classes are in scope; no classes are deferred to future features
- Destructive operations (Menu 90-100) cannot be functionally tested in the automated test suite and are validated only via syntax checks and code review
