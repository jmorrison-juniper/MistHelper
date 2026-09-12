# Research: God Class Decomposition

**Feature**: 004-god-class-decomposition  
**Date**: 2026-03-04  
**Status**: Complete

## Research Questions

### RQ-1: What class patterns exist in MistHelper's god classes?

**Decision**: Three distinct patterns identified, requiring different extraction strategies.

**Pattern A — Stateless @staticmethod (10 classes)**:
- No `__init__`, all methods are `@staticmethod`
- Examples: OrgExportUtils, PromptUtils, RoutingUtils, SiteExportUtils, GatewayExportUtils, GatewayTemplateConfigManager, SiteConfigManager
- Strategy: Follow `OrgAlarmEventExporter` pattern exactly — create new class with `@staticmethod` methods, duplicate private helpers (`_export_data` etc.), wire directly in `menu_actions`

**Pattern B — Instance-based with constructor (8 classes)**:
- Has `__init__` with specific parameters, all methods use `self`
- Examples: BulkAPFirmwareUpgrader, InventoryCSVComparator, FirmwareUpgradeStatusChecker, ServicePingManager, WAN2MigrationManager, MapReplacementWizard, MapsManager, WLANRadiusTimerManager, BulkSwitchFirmwareUpgrader, ConstDefinitionsExporter, FirmwareManager
- Strategy: Pass only required dependencies via constructor parameters. Each sub-class gets only what it needs from the parent's `__init__`. Update lambda wrappers in `menu_actions`.

**Pattern C — Mixed static + instance (5 classes)**:
- Has `__init__` but also uses `@staticmethod` for some methods (typically entry points)
- Examples: PacketCaptureManager, MSPInventoryExporter, SiteAutoUpgradeConfigurator, OrgLevelAPFirmwareUpgrader, EnhancedSSHRunner
- Strategy: Split static utilities (validation, parsing) into their own class. Instance methods follow Pattern B extraction.

**Rationale**: A single extraction strategy cannot handle all three patterns. Pattern A is proven (Feature 003). Pattern B requires constructor dependency injection per FR-011. Pattern C needs a hybrid approach.

**Alternatives considered**: 
- Treating all classes as Pattern A (rejected: instance state cannot be ignored)
- Using inheritance instead of extraction (rejected: violates "no wrappers" principle)

---

### RQ-2: What menu_actions wiring patterns exist?

**Decision**: Three wiring patterns, each requiring different update approaches.

1. **Direct @staticmethod reference** (Pattern A classes):
   ```python
   "11": (OrgExportUtils.sites, "Export Org Sites")
   "1": (OrgAlarmEventExporter.alarms, "Export Org Alarms")
   ```
   Update: Change `OrgExportUtils.sites` → `OrgSiteExporter.sites`

2. **Lambda wrapper** (Pattern B/C classes):
   ```python
   "9": (lambda: PacketCaptureManager(apisession, org_id).start_site_packet_capture(), "...")
   "61": (lambda fast=False, ...: InventoryCSVComparator(fast=fast, ...).execute(), "...")
   ```
   Update: Change class name in lambda, pass additional params if sub-class needs them

3. **Classmethod/staticmethod entry point** (Pattern C classes):
   ```python
   "116": (OrgLevelAPFirmwareUpgrader.run, "...")
   "117": (SiteAutoUpgradeConfigurator.execute, "...")
   ```
   Update: Keep entry point on residual parent or move to orchestrator sub-class

**Rationale**: Understanding the wiring pattern for each class determines how `menu_actions` references must be updated.

---

### RQ-3: What is the proven extraction pattern from Feature 003?

**Decision**: The 6-step extraction pattern documented in `OrgAlarmEventExporter`:

1. **Identify semantic group**: Find 2-5 methods that share a domain concept
2. **Create new class**: Name follows `{Scope}{Domain}{Action}` convention
3. **Copy methods**: Move methods to new class, preserving exact signatures
4. **Duplicate helpers**: Copy private helpers (`_export_data`) into new class
5. **Update references**: Fix `menu_actions`, cross-references, support data tuples
6. **Validate**: `py_compile` + Pylance + `--test` suite

**Rationale**: Proven in production (Feature 003), validated by 49/49 test pass rate.

---

### RQ-4: How should the ~100-150 new sub-classes be named?

**Decision**: `{Scope}{Domain}{Action}` naming convention.

**For Pattern A (Stateless export classes)**:
| Parent | Sub-class Example | Semantic Group |
|--------|-------------------|----------------|
| OrgExportUtils | `OrgDeviceExporter` | Device-related exports |
| OrgExportUtils | `OrgNetworkExporter` | Network/WLAN exports |
| OrgExportUtils | `OrgTemplateExporter` | Template exports |
| SiteExportUtils | `SiteDeviceExporter` | Site device exports |
| SiteExportUtils | `SiteClientExporter` | Site client exports |
| GatewayExportUtils | `GatewayStatsExporter` | Gateway stats |
| GatewayExportUtils | `GatewayConflictAnalyzer` | WAN conflict analysis |
| PromptUtils | `DevicePromptHelper` | Device selection prompts |
| PromptUtils | `SitePromptHelper` | Site selection prompts |

**For Pattern B (Instance-based classes)**:
| Parent | Sub-class Example | Semantic Group |
|--------|-------------------|----------------|
| BulkAPFirmwareUpgrader | `APFirmwareSiteSelector` | Site selection step |
| BulkAPFirmwareUpgrader | `APFirmwareDeviceDiscovery` | AP discovery step |
| BulkAPFirmwareUpgrader | `APFirmwareVersionSelector` | Version selection |
| BulkAPFirmwareUpgrader | `APFirmwareUpgradeExecutor` | Execute upgrades |
| InventoryCSVComparator | `InventoryCSVLoader` | CSV loading/parsing |
| InventoryCSVComparator | `InventoryAddressParser` | Address normalization |
| InventoryCSVComparator | `InventoryDeviceMatcher` | Device matching |
| FirmwareUpgradeStatusChecker | `FirmwareStatusFetcher` | Data fetching |
| FirmwareUpgradeStatusChecker | `FirmwareStatusDisplay` | Display/formatting |
| ServicePingManager | `ServicePingSiteSelector` | Site/device selection |
| ServicePingManager | `ServicePingExecutor` | WebSocket execution |

**Rationale**: Consistent naming makes the codebase navigable. `{Scope}` identifies domain (Org, Site, AP, Gateway), `{Domain}` identifies the functional area, `{Action}` describes the responsibility.

---

### RQ-5: How should instance state be distributed to sub-classes?

**Decision**: Each sub-class receives only its required dependencies via constructor parameters.

**Example — BulkAPFirmwareUpgrader decomposition**:

Current `__init__` stores ~20 instance variables. Sub-classes receive only what they need:

```python
# APFirmwareSiteSelector only needs org_id and API session
class APFirmwareSiteSelector:
    def __init__(self, org_id, sites_override=None):
        self.org_id = org_id
        self.sites_override = sites_override

# APFirmwareVersionSelector needs model data from discovery step
class APFirmwareVersionSelector:
    def __init__(self, models_by_ap, available_versions):
        self.models_by_ap = models_by_ap
        self.available_versions = available_versions
```

**Data flow between sub-classes**: The orchestrator (residual parent) calls each sub-class in sequence, passing results forward:

```python
class BulkAPFirmwareUpgrader:
    def execute(self):
        sites = APFirmwareSiteSelector(self.org_id, self.sites_override).select()
        devices = APFirmwareDeviceDiscovery(self.org_id, sites).discover()
        versions = APFirmwareVersionSelector(devices.models, ...).select()
        # etc.
```

**Rationale**: Avoids bloated constructors that copy the full parent `__init__`. Each sub-class is self-contained and testable in isolation.

**Alternatives considered**:
- Passing the parent instance (`self`) to sub-classes (rejected: tight coupling, violates single responsibility)
- Using a shared context/config object (rejected: creates hidden dependencies, harder to reason about)

---

### RQ-6: What are the semantic groupings for each god class?

**Decision**: Full semantic groupings documented below. Each group becomes one sub-class with at most 5 public methods.

#### BulkAPFirmwareUpgrader (72 methods → ~14 sub-classes)
1. Site selection (13 methods → 3 sub-classes)
2. AP discovery (3 methods → 1 sub-class)
3. Firmware stats (5 methods → 1 sub-class)
4. Available firmware (3 methods → 1 sub-class)
5. Version selection (9 methods → 2 sub-classes)
6. Configure upgrade (10 methods → 2 sub-classes)
7. Confirm upgrade (7 methods → 2 sub-classes)
8. Execute upgrades (7 methods → 2 sub-classes)
9. Auto-upgrade config (8 methods → 2 sub-classes)
10. Status check offer (2 methods → merge)
11. Results (1 method → merge)

#### OrgLevelAPFirmwareUpgrader (66 methods → ~13 sub-classes)
Similar structure to BulkAPFirmwareUpgrader plus MSP entry points.

#### InventoryCSVComparator (65 methods → ~13 sub-classes)
1. CSV loading/field detection (5 methods)
2. Address parsing (5 methods)
3. Duplicate detection (5 methods)
4. Device processing (5 methods)
5. Conflict filtering (5 methods)
6. Validation (5 methods)
7. Results/reporting (5 methods)
8. CSV export (5 methods)

#### FirmwareUpgradeStatusChecker (53 methods → ~10 sub-classes)
1. Data fetching (5 methods)
2. Device processing (5 methods)
3. Status categorization (5 methods)
4. Display/formatting (5 methods)
5. SSR/stored/audit checks (5 methods)
6. Export (5 methods)
7. Recommendations (5 methods)

#### OrgExportUtils (51 methods → ~10 sub-classes)
1. Simple API exports - devices (5 methods)
2. Simple API exports - networks (5 methods)
3. Simple API exports - templates (5 methods)
4. Complex exports - inventory (5 methods)
5. Complex exports - configs (5 methods)
6. Complex exports - stats (5 methods)
7. Location-enriched exports (3 methods → merge)
8. Gateway-enriched exports (1 method → merge)
9. Port stats (2 methods → merge)
10. Core helper (`export_data` → replicated to each)

#### ServicePingManager (51 methods → ~10 sub-classes)
1. Site/device selection (5 methods)
2. Tenant fetching (5 methods)
3. Service fetching (5 methods)
4. Ping parameter prompting (5 methods)
5. WebSocket execution (5 methods)
6. Results display (5 methods)

#### MapReplacementWizard (50 methods → ~10 sub-classes)
1. Orchestration (4 methods)
2. Map selection & asset fetching (5+4 methods → 2 sub-classes)
3. Image selection (3 methods)
4. Scaling configuration (5+5 methods → 2 sub-classes)
5. Backup (2 methods → merge)
6. Preview (5+2 methods → 2 sub-classes)
7. Confirm & apply (5+3+5 methods → 3 sub-classes)
8. Summary (1 method → merge)

#### WLANRadiusTimerManager (47 methods → ~9 sub-classes)
1. Orchestration (4 methods)
2. Site selection (4 methods)
3. WLAN fetching (5 methods)
4. Template assignment (4 methods)
5. RADIUS filtering (5 methods)
6. WLAN display/selection (4 methods)
7. Value prompting (5 methods)
8. Behavior impact display (5 methods)
9. Confirm & apply (5+3 methods → 2 sub-classes)

#### BulkSwitchFirmwareUpgrader (46 methods → ~9 sub-classes)
1. Orchestration (2 methods)
2. Site selection (5 methods)
3. Upgrade configuration (5 methods)
4. Firmware discovery (5 methods)
5. Firmware data processing (4 methods)
6. Version selection (5 methods)
7. Confirmation (3 methods)
8. Execution (5 methods)
9. Results (5 methods)

#### RoutingUtils (40 methods → ~8 sub-classes)
1. Forwarding table parsing (3 methods)
2. Routing table parsing (5 methods)
3. Vendor-specific parsing (2 methods → merge)
4. Display utilities (3 methods)
5. Shared utilities (3 methods)
6. Forwarding table workflow (5+4 methods → 2 sub-classes)
7. Routing table workflow (5+2 methods → 2 sub-classes)
8. SSR route workflow (5+2 methods → 2 sub-classes)

#### SiteAutoUpgradeConfigurator (38 methods → ~8 sub-classes)
1. Entry points (2 methods)
2. MSP mode (5 methods)
3. Core workflow (3 methods)
4. Site selection (5+5 methods → 2 sub-classes)
5. Version selection (5+4 methods → 2 sub-classes)
6. Schedule config (4 methods)
7. Confirm & apply (4 methods)

#### ConstDefinitionsExporter (36 methods → ~7 sub-classes)
1. Entry point (1 method)
2. Endpoint discovery (5 methods)
3. Endpoint metadata (3 methods → merge)
4. Processing pipeline (4 methods)
5. Standard fetch (2 methods → merge)
6. Gateway model fetch (4 methods)
7. Country states fetch (4 methods)
8. Country channels fetch (4 methods)
9. Data export/conversion (5 methods)

#### MapsManager (35 methods → ~7 sub-classes)
1. Site navigation (3 methods)
2. Map selection/backup (2 methods → merge)
3. List/export operations (5 methods)
4. Download operations (2 methods → merge)
5. CRUD operations (5 methods)
6. Device placement (3 methods)
7. Reports/analytics (5 methods)
8. Interactive viewer (5 methods)

#### WAN2MigrationManager (34 methods → ~7 sub-classes)
1. Entry point & UI (3 methods)
2. Data loading (5 methods)
3. Template mapping (4 methods)
4. Override detection (5 methods)
5. IP config extraction (5 methods)
6. Site processing (5 methods)
7. Reporting (5 methods)

#### SiteConfigManager (32 methods → ~7 sub-classes)
1. Test site creation (5+2 methods → 2 sub-classes)
2. RF template management (5+3 methods → 2 sub-classes)
3. Device profile creation (5+3 methods → 2 sub-classes)
4. AP profile assignment (5+3 methods → 2 sub-classes)

#### FirmwareManager (32 methods → ~6 sub-classes)
1. Version utilities (1 method → merge)
2. Status monitoring (4 methods)
3. AP template-based upgrade (5 methods)
4. Mode selection entry points (3 methods)
5. MSP multi-org upgrade (5+4 methods → 2 sub-classes)
6. AP bulk upgrade (3 methods)
7. Switch firmware (3 methods)
8. SSR firmware (3 methods)

#### PromptUtils (28 methods → ~6 sub-classes)
1. Device selection (5 methods)
2. Site selection (5 methods)
3. AP selection (5 methods)
4. Client selection (5 methods)
5. Switch/gateway selection (5 methods)
6. Port selection (3 methods → merge)

#### GlobalImportManager (27 methods → ~5 sub-classes)
1. Package detection (5 methods)
2. UV install (5 methods)
3. Pip install (5 methods)
4. Import management (5 methods)
5. Global assignments (5 methods)

#### EnhancedSSHRunner (27 methods → ~5 sub-classes)
1. Input validation (5 methods)
2. Input parsing (4 methods)
3. File/config (3 methods → merge)
4. Connection lifecycle (4 methods)
5. High-level runners (5 methods)
6. Application entry (2 methods → merge)

#### SQLiteDatabaseWriter (26 methods → ~5 sub-classes)
1. Validation (5 methods)
2. Processing (5 methods)
3. Connection/table (5 methods)
4. Insert/upsert (5 methods)
5. Error handling/close (5 methods)

#### MSPInventoryExporter (26 methods → ~5 sub-classes)
1. Entry & auth (5 methods)
2. Login UI (3 methods → merge)
3. MSP processing (4 methods)
4. Org/device processing (5 methods)
5. Export/output (5 methods)
6. Summary (3 methods → merge)

#### PacketCaptureManager (23 methods → ~5 sub-classes)
1. Validation (2 methods → merge)
2. Configuration/selection (2 methods → merge)
3. Site capture starters (5+3 methods → 2 sub-classes)
4. Capture execution (3 methods)
5. Org capture (2 methods → merge)
6. WebSocket/streaming (2 methods → merge)
7. Download/export (3 methods)

#### GatewayTemplateConfigManager (23 methods → ~5 sub-classes)
1. Extract workflow (5 methods)
2. Apply workflow (5 methods)
3. Clone by location - data (4 methods)
4. Clone by location - planning (3 methods → merge)
5. Clone by location - execution (4 methods)

#### SiteExportUtils (22 methods → ~5 sub-classes)
1. Core export infrastructure (2 methods → kept in residual)
2. Device data exports (5 methods)
3. Client data exports (4 methods)
4. Site config/asset exports (5 methods)
5. Event exports (5 methods)

#### GatewayExportUtils (22 methods → ~5 sub-classes)
1. Test/synthetic exports (2 methods → merge)
2. Device stats exports (3 methods)
3. WAN conflict analysis (5+3 methods → 2 sub-classes)
4. Config/template exports (3 methods)
5. Device inventory helpers (4 methods)

---

### RQ-7: What is the estimated total sub-class count?

**Decision**: ~185 new sub-classes across all 25 parent classes.

| Class | Methods | Estimated Sub-classes |
|-------|---------|----------------------|
| BulkAPFirmwareUpgrader | 72 | 14 |
| OrgLevelAPFirmwareUpgrader | 66 | 13 |
| InventoryCSVComparator | 65 | 13 |
| FirmwareUpgradeStatusChecker | 53 | 10 |
| OrgExportUtils | 51 | 10 |
| ServicePingManager | 51 | 10 |
| MapReplacementWizard | 50 | 10 |
| WLANRadiusTimerManager | 47 | 9 |
| BulkSwitchFirmwareUpgrader | 46 | 9 |
| RoutingUtils | 40 | 8 |
| SiteAutoUpgradeConfigurator | 38 | 8 |
| ConstDefinitionsExporter | 36 | 7 |
| MapsManager | 35 | 7 |
| WAN2MigrationManager | 34 | 7 |
| SiteConfigManager | 32 | 7 |
| FirmwareManager | 32 | 6 |
| PromptUtils | 28 | 6 |
| GlobalImportManager | 27 | 5 |
| EnhancedSSHRunner | 27 | 5 |
| SQLiteDatabaseWriter | 26 | 5 |
| MSPInventoryExporter | 26 | 5 |
| PacketCaptureManager | 23 | 5 |
| GatewayTemplateConfigManager | 23 | 5 |
| SiteExportUtils | 22 | 5 |
| GatewayExportUtils | 22 | 5 |
| **TOTAL** | **1012** | **~187** |

**Note**: Final count will vary as semantic groups are refined during implementation. Some groups may merge (fewer sub-classes) or split (more sub-classes) to maintain the strict 5-method limit.

---

### RQ-8: What cross-references exist beyond menu_actions?

**Decision**: Three types of cross-references must be tracked:

1. **`menu_actions` dictionary**: Direct function references for menu operations
2. **`_refresh_support_data()` tuples**: Data refresh triggers in `DataCollectionManager`
3. **Internal class-to-class calls**: Methods in one class calling methods on another class (e.g., `FirmwareManager` calling `BulkAPFirmwareUpgrader`)

**Strategy**: For each class decomposition, grep for the class name and all its method names to find every reference. Update all references before marking the class as complete.

---

### RQ-9: What is the risk profile for each class?

**Decision**: Classes categorized by blast radius:

**Low Risk (Pattern A, non-destructive)**:
- OrgExportUtils, SiteExportUtils, GatewayExportUtils — proven pattern, read-only
- ConstDefinitionsExporter — read-only data export
- RoutingUtils — WebSocket queries, no writes

**Medium Risk (heavily referenced utilities)**:
- PromptUtils — used by ~20+ other classes; changes have wide blast radius
- SQLiteDatabaseWriter — used by all SQLite exports; changes affect all data persistence
- GlobalImportManager — startup infrastructure; failure prevents app launch

**High Risk (destructive operations)**:
- BulkAPFirmwareUpgrader, OrgLevelAPFirmwareUpgrader — firmware upgrades
- BulkSwitchFirmwareUpgrader — switch firmware
- SiteAutoUpgradeConfigurator — auto-upgrade scheduling
- Cannot be functionally tested via `--test` (skip list)

**Strategy**: Process in spec order (by method count descending), but apply extra validation for medium/high risk classes. For high risk: manual code review of every moved method, verify all destructive confirmation prompts are preserved.
