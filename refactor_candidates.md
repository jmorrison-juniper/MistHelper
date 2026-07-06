# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 182 first-party files
- Definitions analyzed: 102
- LOC saveable (unused + single-use): 4
- Category counts: unused=0, single-use=1, low-use=20, hot=80, skipped=1

## How to read this report

Work the report **top-down inside each category**, then move to the next category:

1. **Unused** -- zero references. Delete outright; no move, no callsite rewrite. Highest ROI per PR.
2. **Single-use** -- exactly one caller. Move alongside that caller (or into a new `/src` module when the entrypoint is the sole caller). One PR covers move + rewrite.
3. **Low-use** -- 2-3 callers. Evaluate before moving: worth it only when all callers can be rewritten in one bounded PR cluster.
4. **Hot** -- 4+ callers. Leave in place until dependencies decouple. Listed for completeness only.
5. **Skipped** -- pinned by bootstrap/module-load ordering (e.g. `GlobalImportManager`). DO NOT extract; the tool cannot detect load-order dependencies, so these are curated by hand via the `--skip NAME` CLI flag.

Within each bucket, candidates are sorted by **line_count descending** so the biggest LOC wins surface first. The `LOC saveable` headline in the metadata block sums unused + single-use lines only -- that number is your extraction budget for this pass.

Reference sites are grouped **per file** so each candidate maps cleanly to one PR per reference-holding file (move + rewrite in the same PR). When multiple single-use candidates share the same dominant caller (see `Suggested class`), bundle them into one PR that lands them in the same class body.

## SpecKit non-negotiables

1. **No wrapper shims**: do NOT create `def old(...): return NewClass().new(...)` or thin re-export modules. Move the code into a semantic class body and delete the old symbol.
2. **Rewrite every callsite**: for each candidate below, produce one PR per reference-holding file cluster. Every listed `file:lineno` must be updated in the same PR as the move.
3. **Decompose while moving**: if a candidate lists `guideline_flags`, do NOT lift-and-shift. Split into <=25-line methods with <=5 params, add inline comments on every executable line, and add `logging.info/debug` before/after every operation.
4. **Landing target is a class body**: `Suggested class` names the destination. Prefer an existing class (`WebSocketManager`, `FirmwareManager`, `SFPTransceiverDataProcessor`, `EnhancedSSHRunner`, etc.) when one already lives in the target module; otherwise create the proposed new class rather than adding a bare module-level function.
5. **ASCII-only logs, `safe_input()`, `pathlib.Path`**: any candidate flagged for non-ASCII literals, raw `input()`, or hardcoded separators must be cleaned up during the move.

## Summary

| Name | Kind | Lines | Refs | Category | Suggested class | Flags |
|---|---|---:|---:|---|---|---|
| `ENDPOINT_PRIMARY_KEY_STRATEGIES` | assignment | 2327 | 5 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `GlobalImportManager` | class | 1005 | 1 | skipped |  | oversize_25_lines |
| `FirmwareUpgradeStatusChecker` | class | 958 | 2 | low-use | FirmwareManager | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `WLANRadiusTimerManager` | class | 787 | 3 | low-use | WLANRadiusTimerManager | oversize_25_lines,non_ascii_logs,raw_input_call |
| `ConstDefinitionsExporter` | class | 759 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgInventoryExporter` | class | 686 | 112 | hot |  | oversize_25_lines,missing_inline_comments |
| `OrgConfigMigrationManager` | class | 675 | 4 | hot |  | oversize_25_lines |
| `OrgExportUtils` | class | 653 | 128 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `BulkRadiusWLANConfigManager` | class | 587 | 13 | hot |  | oversize_25_lines |
| `menu_actions` | assignment | 572 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `WANProbeConfigManager` | class | 473 | 2 | low-use | WANProbeConfigManager | oversize_25_lines,non_ascii_logs |
| `OrgTicketManager` | class | 463 | 66 | hot |  | oversize_25_lines |
| `OperationRegistry` | class | 461 | 9 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `PromptUtils` | class | 441 | 125 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 58 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 398 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `MSPInventoryExporter` | class | 388 | 5 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `DataExporter` | class | 345 | 261 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `APIDataFetcher` | class | 328 | 16 | hot |  | oversize_25_lines |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 115 | hot |  | oversize_25_lines |
| `GlobalWiredClientReportGenerator` | class | 251 | 32 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `GatewayTestExporter` | class | 245 | 34 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `APIFetchUtils` | class | 221 | 36 | hot |  | oversize_25_lines |
| `TelemetryEmitter` | class | 214 | 5 | hot |  | oversize_25_lines,missing_inline_comments |
| `PromptClientUtils` | class | 210 | 31 | hot |  | oversize_25_lines,raw_input_call |
| `SiteDeviceExporter` | class | 203 | 30 | hot |  | oversize_25_lines,non_ascii_logs |
| `DeviceUtilityCommands` | class | 188 | 70 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SFPTransceiverDataProcessor` | class | 180 | 22 | hot |  | oversize_25_lines,missing_inline_comments |
| `DatabaseSchemaUtils` | class | 179 | 34 | hot |  | oversize_25_lines |
| `LicenseExportUtils` | class | 168 | 20 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgConfigExporter` | class | 168 | 24 | hot |  | oversize_25_lines |
| `OrgClientSecurityExporter` | class | 162 | 26 | hot |  | oversize_25_lines |
| `CLIShellManager` | class | 161 | 23 | hot |  | oversize_25_lines,missing_action_logging |
| `DataProcessingUtils` | class | 158 | 205 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `DataCollectionManager` | class | 156 | 20 | hot |  | oversize_25_lines,missing_inline_comments |
| `SitesByAPModelExporter` | class | 146 | 22 | hot |  | oversize_25_lines |
| `SiteExportUtils` | class | 145 | 94 | hot |  | oversize_25_lines,missing_action_logging |
| `OrgTemplateExporter` | class | 144 | 18 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayHaExporter` | class | 139 | 18 | hot |  | oversize_25_lines |
| `OrgAlarmEventExporter` | class | 129 | 14 | hot |  | oversize_25_lines,missing_inline_comments |
| `WiredClientManufacturerReportGenerator` | class | 129 | 20 | hot |  | oversize_25_lines,non_ascii_logs |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `EnvironmentUtils` | class | 125 | 28 | hot |  | oversize_25_lines,hardcoded_separator |
| `OrgSiteExporter` | class | 112 | 55 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 109 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteConfigExporter` | class | 100 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `GatewayExportUtils` | class | 98 | 81 | hot |  | oversize_25_lines,missing_action_logging |
| `DeviceUtils` | class | 97 | 6 | hot |  | oversize_25_lines |
| `OrgAdminExporter` | class | 94 | 14 | hot |  | oversize_25_lines,hardcoded_separator |
| `AnomalyMetricsDiscovery` | class | 91 | 2 | low-use | AnomalyMetricsDiscovery | oversize_25_lines,missing_inline_comments |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteClientExporter` | class | 85 | 10 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 277 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 16 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 199 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `DeviceDataFetcher` | class | 68 | 3 | low-use | DeviceDataFetcher | oversize_25_lines,missing_inline_comments |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 59 | hot |  | oversize_25_lines,missing_inline_comments |
| `InventoryCSVComparator` | class | 47 | 3 | low-use | InventoryCSVComparator | oversize_25_lines,missing_action_logging |
| `FilePathUtils` | class | 46 | 110 | hot |  | oversize_25_lines,missing_inline_comments |
| `SiteConfigManager` | class | 43 | 16 | hot |  | oversize_25_lines,missing_action_logging |
| `SelfExportUtils` | class | 40 | 4 | hot |  | oversize_25_lines,non_ascii_logs |
| `BulkAPFirmwareUpgrader` | class | 32 | 2 | low-use | FirmwareManager | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `TimeUtils` | class | 29 | 51 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
| `DeviceConfigTemplateClonerManager` | class | 27 | 2 | low-use | DeviceConfigTemplateClonerManager | oversize_25_lines,missing_action_logging |
| `SSHRunnerManager` | class | 26 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 4 | hot |  | missing_action_logging |
| `WANProbeDeviceOverrideManager` | class | 23 | 2 | low-use | WANProbeDeviceOverrideManager | missing_inline_comments,missing_action_logging |
| `RoutingUtils` | class | 22 | 12 | hot |  | missing_inline_comments,missing_action_logging |
| `FirmwareManager` | class | 22 | 10 | hot |  |  |
| `SiteAutoUpgradeConfigurator` | class | 22 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `execute_with_connection_pool_management` | function | 21 | 7 | hot |  |  |
| `BulkSwitchFirmwareUpgrader` | class | 19 | 2 | low-use | FirmwareManager | missing_inline_comments,missing_action_logging |
| `initialize_mist_session_interactive` | function | 18 | 3 | low-use | InitializeMistSessionInteractiveManager | missing_action_logging |
| `initialize_mist_session` | function | 18 | 2 | low-use | InitializeMistSessionManager | missing_action_logging |
| `PACKAGE_IMPORT_MAP` | assignment | 13 | 2 | low-use | PackageImportMapManager | missing_action_logging |
| `main` | function | 12 | 2 | low-use | MainManager |  |
| `EndpointConfig` | class | 10 | 13 | hot |  | missing_action_logging |
| `SSHConnectionConfig` | class | 9 | 6 | hot |  | missing_action_logging |
| `DeviceFetchConfig` | class | 9 | 4 | hot |  | missing_action_logging |
| `SSHExecutionConfig` | class | 8 | 5 | hot |  | missing_inline_comments,missing_action_logging |
| `listen_keyboard` | function | 4 | 1 | single-use | ListenKeyboardManager |  |
| `marvis_data_utils` | assignment | 4 | 3 | low-use | MarvisDataUtils | missing_action_logging |
| `is_debug_mode` | function | 3 | 12 | hot |  | missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_BACKOFF_MULTIPLIER` | assignment | 3 | 3 | low-use | FastModeBackoffMultiplierManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_DEVICES_PER_THREAD` | assignment | 3 | 2 | low-use | FastModeDevicesPerThreadManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_SEQUENTIAL_MAX_RETRIES` | assignment | 3 | 2 | low-use | FastModeSequentialMaxRetriesManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 2 | low-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_WAN_TARGET_PORTS` | assignment | 3 | 3 | low-use | MistWanTargetPortsManager | missing_inline_comments,missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 14 | hot |  | missing_inline_comments,missing_action_logging |

## Single-Use (1)

### `listen_keyboard` (function, 4 lines)

- Def site: line 647-650
- References: 1
- Suggested class: `ListenKeyboardManager`
- Suggested module: `src/refactors/listen_keyboard.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_interactive()`; extract `listen_keyboard` OUT of the entrypoint into a new `src/refactors/listen_keyboard.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16135

## Low-Use (20)

### `FirmwareUpgradeStatusChecker` (class, 958 lines)

- Def site: line 18254-19211
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1746, 1753

### `WLANRadiusTimerManager` (class, 787 lines)

- Def site: line 19880-20666
- References: 3
- Suggested class: `WLANRadiusTimerManager`
- Suggested module: `src/refactors/wlanradius_timer_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_apply_site_template_response()`; extract `WLANRadiusTimerManager` OUT of the entrypoint into a new `src/refactors/wlanradius_timer_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20047, 20047, 21518

### `WANProbeConfigManager` (class, 473 lines)

- Def site: line 17184-17656
- References: 2
- Suggested class: `WANProbeConfigManager`
- Suggested module: `src/refactors/wanprobe_config_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeConfigManager` OUT of the entrypoint into a new `src/refactors/wanprobe_config_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21723, 21723

### `AnomalyMetricsDiscovery` (class, 91 lines)

- Def site: line 19782-19872
- References: 2
- Suggested class: `AnomalyMetricsDiscovery`
- Suggested module: `src/refactors/anomaly_metrics_discovery.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_discover_site_anomaly_metrics()`; extract `AnomalyMetricsDiscovery` OUT of the entrypoint into a new `src/refactors/anomaly_metrics_discovery.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12997, 12997

### `DeviceDataFetcher` (class, 68 lines)

- Def site: line 5541-5608
- References: 3
- Suggested class: `DeviceDataFetcher`
- Suggested module: `src/refactors/device_data_fetcher.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `device_stats()`; extract `DeviceDataFetcher` OUT of the entrypoint into a new `src/refactors/device_data_fetcher.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15295, 15312, 15328

### `InventoryCSVComparator` (class, 47 lines)

- Def site: line 16452-16498
- References: 3
- Suggested class: `InventoryCSVComparator`
- Suggested module: `src/refactors/inventory_csvcomparator.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `__init__()`; extract `InventoryCSVComparator` OUT of the entrypoint into a new `src/refactors/inventory_csvcomparator.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16491, 16491, 21544

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 19224-19255
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1733, 1736

### `DeviceConfigTemplateClonerManager` (class, 27 lines)

- Def site: line 15917-15943
- References: 2
- Suggested class: `DeviceConfigTemplateClonerManager`
- Suggested module: `src/refactors/device_config_template_cloner_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `DeviceConfigTemplateClonerManager` OUT of the entrypoint into a new `src/refactors/device_config_template_cloner_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21925, 21925

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17664-17686
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21727, 21727

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 19756-19774
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1832, 1833

### `initialize_mist_session_interactive` (function, 18 lines)

- Def site: line 2180-2197
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2240, 19359, 23193

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2806-2823
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23198, 23261

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 353-365
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 353, 537

### `main` (function, 12 lines)

- Def site: line 23589-23600
- References: 2
- Suggested class: `MainManager`
- Suggested module: `src/refactors/main.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `main` OUT of the entrypoint into a new `src/refactors/main.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23703
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6597-6600
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6597, 15739
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1972-1974
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1972, 9983, 15412

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1975-1977
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1975, 7473

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1980-1982
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1980, 15552

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 1987-1989
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1987, 7463

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 1995-1997
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1995, 15641
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2868-5194
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2868, 6643, 6644, 6653, 6817

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13998-14756
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14475, 14475, 14487, 14487, 14515, 14515, 14527, 14527, 14588, 14588, 14625, 14625, 14782, 21642

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9144-9829
- References: 112
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5650, 5650, 9267, 9267, 9318, 9318, 9321, 9321, 9362, 9362, 9401, 9401, 9419, 9419, 9497, 9497, 9504, 9504, 9514, 9514, 9517, 9517, 9530, 9530, 9531, 9531, 9532, 9532, 9533, 9533, 9541, 9541, 9543, 9543, 9544, 9544, 9545, 9545, 9546, 9546, 9549, 9549, 9552, 9552, 9555, 9555, 9558, 9558, 9604, 9604, 9627, 9627, 9628, 9628, 9629, 9629, 9631, 9631, 9667, 9667, 9683, 9683, 9737, 9737, 9738, 9738, 9739, 9739, 9742, 9742, 9743, 9743, 9762, 9762, 9764, 9764, 9765, 9765, 9800, 9800, 15151, 15151, 15204, 15204, 15635, 16474, 16474, 17713, 17713, 17737, 17737, 17761, 17761, 17904, 17904, 21417, 21417, 21424, 21424, 21433, 21433, 21437, 21437, 21446, 21446
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16504-17178
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16892, 16892, 21888, 21894

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11877-12529
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10654, 10654, 10663, 10663, 10751, 10751, 10758, 10758, 11432, 11432, 11718, 11718, 11723, 11723, 11730, 11730, 11735, 11735, 11949, 11949, 11971, 11971, 11974, 11974, 12000, 12000, 12009, 12009, 12010, 12010, 12031, 12031, 12074, 12074, 12120, 12120, 12131, 12131, 12158, 12158, 12163, 12163, 12164, 12164, 12165, 12165, 12197, 12197, 12203, 12203, 12228, 12228, 12248, 12248, 12283, 12283, 12298, 12298, 12304, 12304, 12306, 12306, 12309, 12309, 12311, 12311, 12315, 12315, 12319, 12319, 12324, 12324, 12331, 12331, 12338, 12338, 12345, 12345, 12354, 12354, 12364, 12364, 12371, 12371, 12378, 12378, 12385, 12385, 12392, 12392, 12399, 12399, 12409, 12409, 12418, 12418, 12427, 12427, 12436, 12436, 12445, 12445, 12474, 12474, 21378, 21378, 21559, 21559, 21636, 21636, 21637, 21637, 21645, 21645, 21850, 21850, 21851, 21851, 21870, 21870, 21877, 21877, 21878, 21878, 21879, 21879, 21880, 21880

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 20674-21260
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20951, 20951, 20952, 20952, 20955, 20955, 20957, 20957, 20959, 20959, 20975, 20975, 21795

### `menu_actions` (assignment, 572 lines)

- Def site: line 21359-21930
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21359, 22644, 22645, 22654, 22774, 22774, 22816, 22874, 22919, 23410, 23414, 23459, 23459, 23486, 23486, 23489
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8428-8890
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8469, 8469, 8474, 8474, 8484, 8484, 8492, 8492, 8497, 8497, 8502, 8502, 8512, 8512, 8517, 8517, 8522, 8522, 8542, 8542, 8552, 8552, 8553, 8553, 8556, 8556, 8586, 8586, 8672, 8672, 8674, 8674, 8698, 8698, 8704, 8704, 8709, 8709, 8718, 8718, 8722, 8722, 8741, 8741, 8744, 8744, 8755, 8755, 8756, 8756, 8851, 8851, 8872, 8872, 21918, 21918, 21919, 21919, 21920, 21920, 21921, 21921, 21922, 21922, 21923, 21923

### `OperationRegistry` (class, 461 lines)

- Def site: line 22155-22615
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22622, 22622, 22626, 22626, 22646, 22646, 22651, 22651, 22875

### `PromptUtils` (class, 441 lines)

- Def site: line 7875-8315
- References: 125
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5579, 5579, 5587, 5587, 7820, 7820, 7836, 7836, 7840, 7840, 7841, 7841, 7842, 7842, 7857, 7857, 7863, 7863, 7890, 7890, 7893, 7893, 7901, 7901, 7919, 7919, 7969, 7969, 7977, 7977, 7982, 7982, 8028, 8028, 8039, 8039, 8064, 8064, 8083, 8083, 8084, 8084, 8087, 8087, 8088, 8088, 8178, 8178, 8180, 8180, 8184, 8184, 8212, 8212, 8213, 8213, 8214, 8214, 8215, 8215, 8216, 8216, 8225, 8225, 8269, 8269, 8293, 8293, 12609, 12609, 12659, 12659, 12664, 12664, 12807, 12890, 12890, 12944, 12944, 12965, 12965, 12970, 12970, 13234, 13234, 13437, 13639, 13639, 13726, 13726, 13731, 13731, 13781, 13781, 13782, 13782, 15278, 15278, 15737, 17720, 17720, 18242, 18242, 18343, 18343, 19971, 19971, 21283, 21283, 21284, 21284, 21570, 21570
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9832-10245
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5644, 5644, 9865, 9865, 9949, 9949, 9955, 9955, 9958, 9958, 10002, 10002, 10016, 10016, 10043, 10043, 10049, 10049, 10063, 10063, 10146, 10146, 10148, 10148, 10152, 10152, 10154, 10154, 10157, 10157, 10161, 10161, 10164, 10164, 10174, 10174, 10180, 10180, 10218, 10218, 15152, 15152, 15153, 15153, 15154, 15154, 15205, 15205, 15206, 15206, 21418, 21418, 21419, 21419, 21420, 21420, 21444, 21444

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17823-18220
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17844, 17844, 17849, 17849, 17853, 17853, 17856, 17856, 17863, 17863, 17865, 17865, 17866, 17866, 17869, 17869, 17872, 17872, 17875, 17875, 17917, 17917, 17949, 17949, 18016, 18016, 18029, 18029, 18034, 18034, 18086, 18086, 18119, 18119, 18120, 18120, 18121, 18121, 18151, 18151, 18180, 18180, 18181, 18181, 21601, 21601

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 19261-19648
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19288, 19432, 19432, 21741, 21741

### `DataExporter` (class, 345 lines)

- Def site: line 6784-7128
- References: 261
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5607, 5607, 5740, 5740, 6830, 6830, 6846, 6846, 6847, 6847, 6870, 6870, 6872, 6872, 6875, 6875, 6889, 6889, 6891, 6891, 6900, 6900, 6902, 6902, 6903, 6903, 6909, 6909, 6910, 6910, 6910, 6927, 6927, 6931, 6931, 6973, 6973, 7004, 7004, 7007, 7007, 7009, 7009, 7055, 7055, 7065, 7065, 7098, 7098, 7103, 7103, 7110, 7110, 7332, 7332, 7364, 7364, 7375, 7375, 7400, 7400, 7420, 7420, 7932, 7932, 8725, 8725, 9004, 9004, 9019, 9083, 9083, 9100, 9100, 9118, 9118, 9139, 9139, 9698, 9698, 9773, 9773, 10103, 10103, 10454, 10454, 10539, 10555, 10675, 10675, 10679, 10679, 10699, 10699, 10712, 10712, 10716, 10716, 10734, 10734, 10896, 10896, 11243, 11243, 11390, 11390, 11467, 11467, 11471, 11471, 11476, 11476, 11609, 11609, 11628, 11628, 11679, 11679, 11682, 11682, 11833, 11833, 11836, 11836, 11935, 11935, 11941, 11941, 12238, 12238, 12255, 12255, 12270, 12270, 12484, 12484, 12512, 12512, 12528, 12528, 12565, 12565, 12603, 12603, 12692, 12692, 12721, 12721, 12759, 12759, 12810, 12875, 12875, 12881, 12881, 12923, 12923, 13092, 13092, 13098, 13098, 13217, 13217, 13225, 13225, 13389, 13389, 13440, 13613, 13613, 13784, 13784, 14297, 14297, 14658, 14658, 14664, 14664, 15572, 15572, 15631, 15738, 15874, 15874, 15892, 15892, 15910, 15910, 15937, 15937, 15938, 15938, 17588, 17588, 17681, 17767, 17767, 17788, 19096, 19096, 19614, 19614, 19699, 19699, 19720, 19720, 21109, 21109, 21770, 21770, 21786, 21786
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12931-13271
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12948, 12948, 12950, 12950, 12954, 12954, 12955, 12955, 12969, 12969, 12975, 12975, 12978, 12978, 12981, 12981, 13039, 13039, 13045, 13045, 13050, 13050, 13064, 13064, 13082, 13082, 13192, 13192, 13196, 13196, 13198, 13198, 13201, 13201, 13238, 13238, 13243, 13243, 13257, 13257, 13261, 13261, 13263, 13263, 13266, 13266, 13271, 13271, 21647, 21647, 21651, 21651, 21655, 21655

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7131-7458
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7233, 7233, 8449, 8930, 8949, 9050, 9179, 9202, 9874, 10182, 10227, 10641, 11411, 11422, 11485, 11902

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14762-15089
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12219, 12219, 12278, 12278, 12279, 12279, 13443, 14803, 14803, 14805, 14805, 14811, 14811, 14825, 14825, 14864, 14864, 14867, 14867, 14869, 14869, 14870, 14870, 14871, 14871, 14925, 14925, 14926, 14926, 14937, 14937, 14946, 14946, 14965, 14965, 15017, 15017, 15021, 15021, 15029, 15029, 15030, 15030, 15054, 15054, 15058, 15058
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16146-16434
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16174, 16174, 16177, 16177, 16182, 16182, 16185, 16185, 16229, 16229, 16235, 16235, 16266, 16266, 16269, 16269, 16273, 16273, 16299, 16299, 16316, 16316, 16322, 16322, 16336, 16336, 16337, 16337, 16339, 16339, 16345, 16345, 16352, 16352, 16361, 16361, 16408, 16408, 16430, 16430, 16431, 16431, 16432, 16432, 21592, 21592

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10248-10520
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10271, 10271, 10272, 10272, 10285, 10285, 10286, 10286, 10288, 10288, 10289, 10289, 10292, 10292, 10295, 10295, 10299, 10299, 10300, 10300, 10376, 10376, 10380, 10380, 10383, 10383, 10396, 10396, 10433, 10433, 10450, 10450, 10463, 10463, 10465, 10465, 10472, 10472, 10481, 10481, 10490, 10490, 10491, 10491, 10502, 10502, 10506, 10506, 10515, 10515, 10520, 10520, 21849, 21849

### `CacheUtils` (class, 264 lines)

- Def site: line 5200-5463
- References: 115
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5240, 5240, 5242, 5242, 5324, 5324, 5330, 5330, 5367, 5367, 5369, 5369, 5378, 5378, 5388, 5388, 5398, 5398, 5434, 5434, 7968, 7968, 9626, 9626, 9627, 9627, 9938, 9938, 10784, 10784, 10804, 10804, 12805, 15211, 15211, 15217, 15217, 15218, 15218, 15219, 15219, 15220, 15220, 15221, 15221, 15222, 15222, 15229, 15229, 15257, 15257, 15629, 15875, 15875, 15893, 15893, 15911, 15911, 15961, 16472, 16472, 16473, 16473, 17301, 17301, 17302, 17302, 17676, 17712, 17712, 17736, 17736, 17760, 17760, 17904, 17904, 17905, 17905, 17906, 17906, 17907, 17907, 18243, 18243, 21334, 21334, 21886, 21886
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 11015-11265
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11022, 11022, 11025, 11025, 11030, 11030, 11031, 11031, 11039, 11039, 11042, 11042, 11050, 11050, 11090, 11090, 11098, 11098, 11146, 11146, 11163, 11163, 11166, 11166, 11168, 11168, 11232, 11232, 11233, 11233, 21852, 21852

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15341-15585
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15207, 15207, 15367, 15367, 15369, 15369, 15370, 15370, 15371, 15371, 15399, 15399, 15404, 15404, 15426, 15426, 15427, 15427, 15469, 15469, 15477, 15477, 15503, 15503, 15512, 15512, 15520, 15520, 15551, 15551, 21423, 21423, 21427, 21427

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6203-6423
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6226, 6226, 6277, 6277, 6347, 6347, 6371, 6371, 6383, 6383, 6385, 6385, 6395, 6395, 6410, 6410, 6414, 6414, 6415, 6415, 6418, 6418, 6420, 6420, 12918, 12918, 15633
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 21936-22149
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22792, 22792, 22795, 22876, 23227

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7659-7868
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7672, 7672, 7678, 7678, 7679, 7679, 7682, 7682, 7705, 7705, 7708, 7708, 7711, 7711, 7712, 7712, 7714, 7714, 7781, 7781, 7825, 7825, 8290, 8290, 13239, 13239, 15736, 15999, 15999, 16159, 16159

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12537-12739
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12558, 12558, 12567, 12567, 12629, 12629, 12636, 12636, 12668, 12668, 12670, 12670, 12694, 12694, 12729, 12729, 12736, 12736, 12767, 12767, 15281, 15281, 21459, 21459, 21461, 21461, 21462, 21462, 21464, 21464

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13790-13977
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21809, 21809, 21810, 21810, 21811, 21811, 21812, 21812, 21813, 21813, 21814, 21814, 21815, 21815, 21816, 21816, 21818, 21818, 21819, 21819, 21820, 21820, 21821, 21821, 21822, 21822, 21823, 21823, 21824, 21824, 21826, 21826, 21827, 21827, 21828, 21828, 21829, 21829, 21830, 21830, 21831, 21831, 21832, 21832, 21833, 21833, 21834, 21834, 21836, 21836, 21837, 21837, 21838, 21838, 21839, 21839, 21840, 21840, 21841, 21841, 21842, 21842, 21843, 21843, 21844, 21844, 21846, 21846, 21847, 21847

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5615-5794
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5703, 5703, 5740, 5740, 5742, 5742, 5745, 5745, 5753, 5753, 5755, 5755, 5757, 5757, 5760, 5760, 5789, 5789, 5792, 5792, 21586, 21586

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6603-6781
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6648, 6648, 6686, 6686, 6697, 6697, 6723, 6723, 6724, 6724, 6726, 6726, 6732, 6732, 6733, 6733, 6736, 6736, 6742, 6742, 6743, 6743, 6746, 6746, 6748, 6748, 6758, 6758, 6760, 6760, 6761, 6761, 6763, 6763

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11495-11662
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11602, 11602, 11621, 11621, 11639, 11639, 11648, 11648, 11651, 11651, 11652, 11652, 11655, 11655, 11660, 11660, 11662, 11662, 21487, 21487

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11707-11874
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11744, 11744, 11746, 11746, 11749, 11749, 11820, 11820, 11822, 11822, 11835, 11835, 11839, 11839, 21490, 21490, 21491, 21491, 21492, 21492, 21530, 21530, 21535, 21535

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10740-10901
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10778, 10778, 10785, 10785, 10792, 10792, 10798, 10798, 10805, 10805, 10812, 10812, 10873, 10873, 10884, 10884, 21478, 21478, 21479, 21479, 21481, 21481, 21482, 21482, 21483, 21483

### `CLIShellManager` (class, 161 lines)

- Def site: line 15980-16140
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16003, 16003, 16005, 16005, 16074, 16074, 16076, 16076, 16095, 16095, 16097, 16097, 16097, 16113, 16113, 16129, 16129, 16130, 16130, 16136, 16136, 21591, 21591

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6431-6588
- References: 205
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5498, 5498, 5605, 5605, 5606, 5606, 6447, 6447, 6460, 6460, 6463, 6463, 6487, 6487, 6495, 6495, 6496, 6496, 6518, 6518, 6523, 6523, 6525, 6525, 6598, 6598, 6599, 6599, 7006, 7006, 7031, 7031, 7100, 7100, 7101, 7101, 7430, 7430, 7444, 7444, 7445, 7445, 7930, 7930, 7931, 7931, 8853, 8853, 9018, 9078, 9078, 9080, 9080, 9081, 9081, 9098, 9098, 9099, 9099, 9116, 9116, 9117, 9117, 9137, 9137, 9138, 9138, 9695, 9695, 9696, 9696, 9770, 9770, 9771, 9771, 10099, 10099, 10102, 10102, 10677, 10677, 10678, 10678, 10714, 10714, 10715, 10715, 10894, 10894, 10895, 10895, 11239, 11239, 11240, 11240, 11386, 11386, 11387, 11387, 11469, 11469, 11470, 11470, 11681, 11681, 11856, 11856, 11857, 11857, 11933, 11933, 11934, 11934, 12237, 12237, 12253, 12253, 12254, 12254, 12482, 12482, 12483, 12483, 12562, 12562, 12563, 12563, 12564, 12564, 12600, 12600, 12601, 12601, 12689, 12689, 12690, 12690, 12718, 12718, 12719, 12719, 12756, 12756, 12757, 12757, 12809, 12878, 12878, 12879, 12879, 12921, 12921, 12922, 12922, 13090, 13090, 13091, 13091, 13215, 13215, 13216, 13216, 13439, 13611, 13611, 14663, 14663, 15570, 15570, 15571, 15571, 15632, 15740, 17765, 17765, 17766, 17766, 19604, 19604
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15103-15258
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15125, 15125, 15131, 15131, 15133, 15133, 15161, 15161, 15187, 15187, 15190, 15190, 15193, 15193, 21577, 21577, 21581, 21581, 21589, 21589

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13274-13419
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13313, 13313, 13320, 13320, 13345, 13345, 13348, 13348, 13361, 13361, 13405, 13405, 13409, 13409, 13414, 13414, 13415, 13415, 13419, 13419, 21884, 21884

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13427-13571
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12648, 12648, 12824, 12824, 12902, 12902, 12907, 12907, 13456, 13456, 13462, 13462, 13468, 13468, 13474, 13474, 13480, 13480, 13486, 13486, 13492, 13492, 13498, 13498, 13504, 13504, 13510, 13510, 13516, 13516, 13522, 13522, 13528, 13528, 13534, 13534, 13540, 13540, 13546, 13546, 13552, 13552, 13558, 13558, 13564, 13564, 13570, 13570, 21497, 21497, 21638, 21638, 21640, 21640, 21755, 21755, 21881, 21881, 21882, 21882, 21883, 21883, 21902, 21902, 21903, 21903, 21904, 21904, 21905, 21905, 21906, 21906, 21907, 21907, 21908, 21908
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10594-10737
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10608, 10608, 10609, 10609, 10695, 10695, 10730, 10730, 21472, 21472, 21473, 21473, 21474, 21474, 21475, 21475, 21476, 21476

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13574-13712
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13643, 13643, 13646, 13646, 13647, 13647, 13648, 13648, 13668, 13668, 13671, 13671, 13679, 13679, 13684, 13684, 21910, 21910

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8896-9024
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8967, 8967, 8978, 8978, 15201, 15201, 15202, 15202, 21375, 21375, 21376, 21376, 21555, 21555

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11268-11396
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11275, 11275, 11280, 11280, 11281, 11281, 11282, 11282, 11285, 11285, 11286, 11286, 11349, 11349, 11356, 11356, 11383, 11383, 21854, 21854

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15726-15852
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15746, 15746, 15751, 15751, 15756, 15756, 15793, 15793, 15799, 15799, 15805, 15805, 15811, 15811, 15817, 15817, 15818, 15818, 15819, 15819, 15820, 15820, 15821, 15821, 15825, 15825, 15834, 15834, 15838, 15838, 15841, 15841, 15847, 15847, 21550, 21550

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5848-5972
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5869, 5869, 5871, 5871, 5887, 5887, 5899, 5899, 5938, 5938, 5939, 5939, 5940, 5940, 5941, 5941, 5942, 5942, 5953, 5953, 5956, 5956, 6888, 6888, 22889, 22889, 23472, 23472

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 9030-9141
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7968, 7968, 9626, 9626, 9938, 9938, 10784, 10784, 10804, 10804, 12806, 15150, 15150, 15203, 15203, 15636, 15876, 15876, 15894, 15894, 15912, 15912, 17302, 17302, 17677, 17714, 17714, 17738, 17738, 17762, 17762, 17905, 17905, 18246, 18246, 21416, 21416, 21431, 21431, 21441, 21441, 21441, 21441, 21451, 21451
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10904-11012
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10959, 10959, 10962, 10962, 10963, 10963, 10968, 10968, 10986, 10986, 10986, 10995, 10995, 10995, 10995, 10996, 10996, 10996, 10996, 11054, 11054, 11057, 11057, 11069, 11069, 11070, 11070, 11083, 11083, 11122, 11122, 11130, 11130, 11184, 11184, 11192, 11192

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12829-12928
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12894, 12894, 12896, 12896, 12897, 12897, 21425, 21425, 21493, 21493, 21495, 21495, 21496, 21496

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15618-15715
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15361, 15361, 15596, 15596, 15654, 15654, 15660, 15660, 15666, 15666, 15672, 15672, 15678, 15678, 15684, 15684, 15690, 15690, 15696, 15696, 15702, 15702, 15708, 15708, 15714, 15714, 15962, 17301, 17301, 17678, 17906, 17906, 17909, 17909, 18245, 18245, 21382, 21382, 21449, 21449, 21455, 21455, 21506, 21506, 21563, 21563
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8326-8422
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8382, 8382, 8418, 8418, 16476, 16476

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11399-11492
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11451, 11451, 11464, 11464, 21485, 21485, 21527, 21527, 21528, 21528, 21533, 21533, 21534, 21534

### `ValidationUtils` (class, 90 lines)

- Def site: line 5978-6067
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6060, 6060, 15424, 15424, 15425, 15425, 15639, 21285, 21285
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12742-12826
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12776, 12776, 21460, 21460, 21468, 21468, 21494, 21494, 21639, 21639

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 19675-19753
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19670, 19670, 19671, 19671, 21734, 21734
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17692-17769
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21605, 21605, 21609, 21609, 21613, 21613
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1872-1945
- References: 277
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1885, 1885, 1917, 1917, 2192, 2192, 2281, 2281, 2308, 2308, 7680, 7680, 7766, 7766, 7896, 7896, 7973, 7973, 8056, 8056, 8286, 8286, 8475, 8475, 8531, 8531, 8544, 8544, 8561, 8561, 8606, 8606, 8637, 8637, 8643, 8643, 8746, 8746, 10287, 10287, 10554, 11056, 11056, 11085, 11085, 11350, 11350, 11556, 11556, 11795, 11795, 12511, 12511, 12527, 12527, 13314, 13314, 13733, 13733, 13783, 13783, 15637, 15839, 15839, 15872, 15872, 15890, 15890, 15908, 15908, 15935, 15935, 15960, 17362, 17362, 17489, 17489, 17680, 17719, 17719, 17744, 17744, 17787, 17886, 17886, 18098, 18098, 18241, 18241, 19245, 19245, 19335, 19335, 19665, 19665, 19695, 19695, 19716, 19716, 19735, 19735, 19751, 19751, 19768, 19768, 20259, 20259, 20316, 20316, 20328, 20328, 20341, 20341, 20358, 20358, 20521, 20521, 21232, 21232, 21252, 21252, 21287, 21287, 21300, 21300, 21768, 21768, 21859, 21859, 21864, 21864, 21870, 21870, 21889, 21889, 21895, 21895, 23495, 23495, 23593, 23593
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 20, 226, 226, 244, 244, 313, 313
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 411, 411
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 27, 66, 82, 82, 107, 107, 220, 220
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\_maps_clone.py`: lines 123, 123, 164, 164
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\_maps_wizard.py`: lines 179, 179, 295, 295, 333, 333, 688, 688, 761, 761
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 227, 227, 280, 280, 462, 462, 994, 994, 1012, 1012, 1021, 1021, 1024, 1024, 1027, 1027, 1213, 1213, 1277, 1277, 1383, 1383, 1451, 1451, 1488, 1488, 1668, 1668, 1838, 1838, 2659, 2659, 2662, 2662, 2677, 2677, 2764, 2764
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\address_corrector.py`: lines 79, 79
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 246, 246, 276, 276, 329, 329, 872, 872, 884, 884
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\comparison_display.py`: lines 82, 82
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\ui_geocoder.py`: lines 173, 173, 207, 207, 227, 227
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\runtime\app_runner.py`: lines 257, 257
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\runtime\interactive_mode.py`: lines 33, 33, 50, 50, 74, 74, 104, 104, 127, 127, 140, 140
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ui\execution\item_executor.py`: lines 224, 224
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\utils\input_utils.py`: lines 42, 42, 44, 44, 46, 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 14, 44, 452, 452, 512, 512, 609, 609, 690, 690, 706, 706, 717, 717, 729, 729, 742, 742
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 18, 63, 192, 192

### `InteractiveDisplayUtils` (class, 72 lines)

- Def site: line 15264-15335
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21571, 21571, 21572, 21572, 21573, 21573, 21574, 21574

### `DisplayUtils` (class, 70 lines)

- Def site: line 5469-5538
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5501, 5501, 5502, 5502, 5517, 5517, 5519, 5519, 5608, 5608, 18614, 18614, 18653, 18653, 18712, 18712

### `ConfigUtils` (class, 70 lines)

- Def site: line 6073-6142
- References: 199
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6115, 6115, 6120, 6120, 6217, 6217, 6275, 6275, 7166, 7166, 7823, 7823, 8468, 8468, 8491, 8491, 8511, 8511, 8696, 8696, 8717, 8717, 8992, 8992, 9017, 9017, 9072, 9072, 9094, 9094, 9111, 9111, 9128, 9128, 9513, 9513, 9736, 9736, 9753, 9753, 10145, 10145, 10477, 10477, 10688, 10688, 10725, 10725, 10878, 10878, 11021, 11021, 11274, 11274, 11462, 11462, 11646, 11646, 11965, 11965, 12301, 12301, 12473, 12473, 12513, 12513, 12519, 12519, 12613, 12613, 12843, 12843, 12916, 12916, 13403, 13403, 13438, 13637, 13637, 15144, 15144, 15360, 15360, 15628, 15735, 15835, 15835, 15870, 15870, 15888, 15888, 15906, 15906, 15941, 15941, 16475, 16475, 17282, 17282, 17675, 17785, 18293, 18293, 19246, 19246, 19251, 19251, 19253, 19253, 19666, 19666, 19668, 19668, 19692, 19692, 19696, 19696, 19697, 19697, 19717, 19717, 19718, 19718, 19980, 19980, 20766, 20766, 21336, 21336, 21368, 21368, 21405, 21405, 21411, 21411, 21539, 21539, 21596, 21596, 21679, 21679, 21688, 21688, 21766, 21766, 21767, 21767, 21784, 21784, 21859, 21859, 21864, 21864, 21870, 21870, 21889, 21889, 21895, 21895, 22806, 22806, 22877, 23359, 23359, 23447, 23447
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10523-10591
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10563, 10563, 10568, 10568, 10573, 10573, 10574, 10574, 10580, 10580, 10581, 10581, 10587, 10587, 10588, 10588, 10589, 10589, 10590, 10590, 21912, 21912

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 21291-21356
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21339, 21339, 21347, 21347, 21356, 21356, 21885, 21885

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15859-15914
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21510, 21510, 21514, 21514, 21719, 21719

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6148-6194
- References: 59
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6272, 6272, 8158, 8158, 9073, 9073, 9096, 9096, 9583, 9583, 9618, 9618, 9632, 9632, 9755, 9755, 9759, 9759, 10307, 10307, 12617, 12617, 13287, 13287, 13413, 13413, 13445, 13623, 13623, 13659, 13659, 15634, 18401, 18401, 19247, 19247, 19556, 19556, 19667, 19667, 19698, 19698, 19719, 19719, 21769, 21769, 21785, 21785, 23378, 23378
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5797-5842
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5239, 5239, 5281, 5281, 5326, 5326, 5432, 5432, 5447, 5447, 5787, 5787, 5788, 5788, 5832, 5832, 6298, 6298, 7992, 7992, 9283, 9283, 9594, 9594, 9610, 9610, 9939, 9939, 10820, 10820, 10839, 10839, 12808, 15227, 15227, 15630, 15873, 15873, 15891, 15891, 15909, 15909, 15936, 15936, 15963, 16385, 16385, 16425, 16425, 16426, 16426, 16427, 16427, 16471, 16471, 17303, 17303, 17310, 17310, 17679, 17711, 17711, 17735, 17735, 17739, 17739, 17759, 17759, 17786, 17861, 17861, 17895, 17895, 17916, 17916, 17948, 17948, 18010, 18010, 18049, 18049, 18199, 18199, 18244, 18244, 19248, 19248, 19819, 19819
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17775-17817
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17798, 17798, 17804, 17804, 17810, 17810, 17816, 17816, 21703, 21703, 21707, 21707, 21711, 21711, 21715, 21715

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11665-11704
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11702, 11702, 21909, 21909

### `TimeUtils` (class, 29 lines)

- Def site: line 1836-1864
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8946, 8946, 8947, 8947, 8976, 8976, 8977, 8977, 8993, 8993, 8994, 8994, 9872, 9872, 9873, 9873, 10177, 10177, 10178, 10178, 10225, 10225, 10226, 10226, 10781, 10781, 10783, 10783, 10801, 10801, 10803, 10803, 11691, 11691, 11692, 11692, 12352, 12352, 12353, 12353, 12458, 12458, 12459, 12459, 13441
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15588-15615
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15602, 15602, 15608, 15608, 15614, 15614, 21617, 21617, 21621, 21621
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15949-15974
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15969, 15969, 15974, 15974, 21625, 21625, 21630, 21630
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2100-2124
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2186, 2245, 19364, 23202

### `RoutingUtils` (class, 22 lines)

- Def site: line 13740-13761
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21391, 21391, 21395, 21395, 21399, 21399
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 18227-18248
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19250, 19250, 21538, 21538, 21595, 21595, 21678, 21678, 21687, 21687

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 19651-19672
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21748, 21748
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7630-7650
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6381, 10150, 15473, 15638
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13986-13995
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14022, 14158, 14235, 14254, 14266, 14287, 14300, 14311, 14317, 14330, 14423, 14558, 14653

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 284-292
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\batch_executor.py`: lines 60
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\host_runner.py`: lines 66
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\interactive_batch_executor.py`: lines 103
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\multi_host_runner.py`: lines 60, 83
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\command\command_runner.py`: lines 64

### `DeviceFetchConfig` (class, 9 lines)

- Def site: line 311-319
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5555, 15296, 15313, 15329

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 296-303
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\batch_executor.py`: lines 61
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\host_runner.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\interactive_batch_executor.py`: lines 104
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\batch\multi_host_runner.py`: lines 61, 84

### `is_debug_mode` (function, 3 lines)

- Def site: line 271-273
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13446, 13735, 19700, 19721, 20753, 20784, 20816, 21051, 21066
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 599-601
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1213, 1882, 1882, 1882, 1894, 1900, 6274, 6394, 7454, 7514, 9682, 9793, 10047, 10877, 13448, 15506, 15548, 15646, 17384, 17504, 21771
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 34, 78, 162
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 56
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 36, 212, 255
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 903, 905

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 1984-1986
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1984, 7464, 7471, 7472, 10058, 15495

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2002-2004
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2002, 15642, 17292, 17292, 17683
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 719-1723
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1768

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
