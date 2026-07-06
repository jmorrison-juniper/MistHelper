# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 181 first-party files
- Definitions analyzed: 103
- LOC saveable (unused + single-use): 22
- Category counts: unused=0, single-use=2, low-use=20, hot=80, skipped=1

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
| `run_interactive_test` | function | 18 | 1 | single-use | RunInteractiveTestManager |  |
| `PACKAGE_IMPORT_MAP` | assignment | 13 | 2 | low-use | PackageImportMapManager | missing_action_logging |
| `main` | function | 12 | 2 | low-use | MapsManager |  |
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

## Single-Use (2)

### `run_interactive_test` (function, 18 lines)

- Def site: line 22884-22901
- References: 1
- Suggested class: `RunInteractiveTestManager`
- Suggested module: `src/refactors/run_interactive_test.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_interactive_test_mode()`; extract `run_interactive_test` OUT of the entrypoint into a new `src/refactors/run_interactive_test.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23633

### `listen_keyboard` (function, 4 lines)

- Def site: line 644-647
- References: 1
- Suggested class: `ListenKeyboardManager`
- Suggested module: `src/refactors/listen_keyboard.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_interactive()`; extract `listen_keyboard` OUT of the entrypoint into a new `src/refactors/listen_keyboard.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16132

## Low-Use (20)

### `FirmwareUpgradeStatusChecker` (class, 958 lines)

- Def site: line 18251-19208
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

- Def site: line 19877-20663
- References: 3
- Suggested class: `WLANRadiusTimerManager`
- Suggested module: `src/refactors/wlanradius_timer_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_apply_site_template_response()`; extract `WLANRadiusTimerManager` OUT of the entrypoint into a new `src/refactors/wlanradius_timer_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20044, 20044, 21515

### `WANProbeConfigManager` (class, 473 lines)

- Def site: line 17181-17653
- References: 2
- Suggested class: `WANProbeConfigManager`
- Suggested module: `src/refactors/wanprobe_config_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeConfigManager` OUT of the entrypoint into a new `src/refactors/wanprobe_config_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21720, 21720

### `AnomalyMetricsDiscovery` (class, 91 lines)

- Def site: line 19779-19869
- References: 2
- Suggested class: `AnomalyMetricsDiscovery`
- Suggested module: `src/refactors/anomaly_metrics_discovery.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_discover_site_anomaly_metrics()`; extract `AnomalyMetricsDiscovery` OUT of the entrypoint into a new `src/refactors/anomaly_metrics_discovery.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12994, 12994

### `DeviceDataFetcher` (class, 68 lines)

- Def site: line 5538-5605
- References: 3
- Suggested class: `DeviceDataFetcher`
- Suggested module: `src/refactors/device_data_fetcher.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `device_stats()`; extract `DeviceDataFetcher` OUT of the entrypoint into a new `src/refactors/device_data_fetcher.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15292, 15309, 15325

### `InventoryCSVComparator` (class, 47 lines)

- Def site: line 16449-16495
- References: 3
- Suggested class: `InventoryCSVComparator`
- Suggested module: `src/refactors/inventory_csvcomparator.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `__init__()`; extract `InventoryCSVComparator` OUT of the entrypoint into a new `src/refactors/inventory_csvcomparator.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16488, 16488, 21541

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 19221-19252
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

- Def site: line 15914-15940
- References: 2
- Suggested class: `DeviceConfigTemplateClonerManager`
- Suggested module: `src/refactors/device_config_template_cloner_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `DeviceConfigTemplateClonerManager` OUT of the entrypoint into a new `src/refactors/device_config_template_cloner_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21922, 21922

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17661-17683
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21724, 21724

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 19753-19771
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

- Def site: line 2177-2194
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2237, 19356, 23210

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2803-2820
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23215, 23278

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 350-362
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 350, 534

### `main` (function, 12 lines)

- Def site: line 23606-23617
- References: 2
- Suggested class: `MapsManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`
- Rationale: 97 caller files detected; group callers under a shared class in `maps_manager.py` and rewrite references per file cluster
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23720
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6594-6597
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6594, 15736
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1969-1971
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1969, 9980, 15409

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1972-1974
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1972, 7470

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1977-1979
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1977, 15549

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 1984-1986
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1984, 7460

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 1992-1994
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1992, 15638
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2865-5191
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2865, 6640, 6641, 6650, 6814

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13995-14753
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14472, 14472, 14484, 14484, 14512, 14512, 14524, 14524, 14585, 14585, 14622, 14622, 14779, 21639

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9141-9826
- References: 112
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5647, 5647, 9264, 9264, 9315, 9315, 9318, 9318, 9359, 9359, 9398, 9398, 9416, 9416, 9494, 9494, 9501, 9501, 9511, 9511, 9514, 9514, 9527, 9527, 9528, 9528, 9529, 9529, 9530, 9530, 9538, 9538, 9540, 9540, 9541, 9541, 9542, 9542, 9543, 9543, 9546, 9546, 9549, 9549, 9552, 9552, 9555, 9555, 9601, 9601, 9624, 9624, 9625, 9625, 9626, 9626, 9628, 9628, 9664, 9664, 9680, 9680, 9734, 9734, 9735, 9735, 9736, 9736, 9739, 9739, 9740, 9740, 9759, 9759, 9761, 9761, 9762, 9762, 9797, 9797, 15148, 15148, 15201, 15201, 15632, 16471, 16471, 17710, 17710, 17734, 17734, 17758, 17758, 17901, 17901, 21414, 21414, 21421, 21421, 21430, 21430, 21434, 21434, 21443, 21443
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16501-17175
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16889, 16889, 21885, 21891

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11874-12526
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10651, 10651, 10660, 10660, 10748, 10748, 10755, 10755, 11429, 11429, 11715, 11715, 11720, 11720, 11727, 11727, 11732, 11732, 11946, 11946, 11968, 11968, 11971, 11971, 11997, 11997, 12006, 12006, 12007, 12007, 12028, 12028, 12071, 12071, 12117, 12117, 12128, 12128, 12155, 12155, 12160, 12160, 12161, 12161, 12162, 12162, 12194, 12194, 12200, 12200, 12225, 12225, 12245, 12245, 12280, 12280, 12295, 12295, 12301, 12301, 12303, 12303, 12306, 12306, 12308, 12308, 12312, 12312, 12316, 12316, 12321, 12321, 12328, 12328, 12335, 12335, 12342, 12342, 12351, 12351, 12361, 12361, 12368, 12368, 12375, 12375, 12382, 12382, 12389, 12389, 12396, 12396, 12406, 12406, 12415, 12415, 12424, 12424, 12433, 12433, 12442, 12442, 12471, 12471, 21375, 21375, 21556, 21556, 21633, 21633, 21634, 21634, 21642, 21642, 21847, 21847, 21848, 21848, 21867, 21867, 21874, 21874, 21875, 21875, 21876, 21876, 21877, 21877

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 20671-21257
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20948, 20948, 20949, 20949, 20952, 20952, 20954, 20954, 20956, 20956, 20972, 20972, 21792

### `menu_actions` (assignment, 572 lines)

- Def site: line 21356-21927
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21356, 22641, 22642, 22651, 22771, 22771, 22813, 22871, 22936, 23427, 23431, 23476, 23476, 23503, 23503, 23506
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8425-8887
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8466, 8466, 8471, 8471, 8481, 8481, 8489, 8489, 8494, 8494, 8499, 8499, 8509, 8509, 8514, 8514, 8519, 8519, 8539, 8539, 8549, 8549, 8550, 8550, 8553, 8553, 8583, 8583, 8669, 8669, 8671, 8671, 8695, 8695, 8701, 8701, 8706, 8706, 8715, 8715, 8719, 8719, 8738, 8738, 8741, 8741, 8752, 8752, 8753, 8753, 8848, 8848, 8869, 8869, 21915, 21915, 21916, 21916, 21917, 21917, 21918, 21918, 21919, 21919, 21920, 21920

### `OperationRegistry` (class, 461 lines)

- Def site: line 22152-22612
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22619, 22619, 22623, 22623, 22643, 22643, 22648, 22648, 22872

### `PromptUtils` (class, 441 lines)

- Def site: line 7872-8312
- References: 125
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5576, 5576, 5584, 5584, 7817, 7817, 7833, 7833, 7837, 7837, 7838, 7838, 7839, 7839, 7854, 7854, 7860, 7860, 7887, 7887, 7890, 7890, 7898, 7898, 7916, 7916, 7966, 7966, 7974, 7974, 7979, 7979, 8025, 8025, 8036, 8036, 8061, 8061, 8080, 8080, 8081, 8081, 8084, 8084, 8085, 8085, 8175, 8175, 8177, 8177, 8181, 8181, 8209, 8209, 8210, 8210, 8211, 8211, 8212, 8212, 8213, 8213, 8222, 8222, 8266, 8266, 8290, 8290, 12606, 12606, 12656, 12656, 12661, 12661, 12804, 12887, 12887, 12941, 12941, 12962, 12962, 12967, 12967, 13231, 13231, 13434, 13636, 13636, 13723, 13723, 13728, 13728, 13778, 13778, 13779, 13779, 15275, 15275, 15734, 17717, 17717, 18239, 18239, 18340, 18340, 19968, 19968, 21280, 21280, 21281, 21281, 21567, 21567
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9829-10242
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5641, 5641, 9862, 9862, 9946, 9946, 9952, 9952, 9955, 9955, 9999, 9999, 10013, 10013, 10040, 10040, 10046, 10046, 10060, 10060, 10143, 10143, 10145, 10145, 10149, 10149, 10151, 10151, 10154, 10154, 10158, 10158, 10161, 10161, 10171, 10171, 10177, 10177, 10215, 10215, 15149, 15149, 15150, 15150, 15151, 15151, 15202, 15202, 15203, 15203, 21415, 21415, 21416, 21416, 21417, 21417, 21441, 21441

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17820-18217
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17841, 17841, 17846, 17846, 17850, 17850, 17853, 17853, 17860, 17860, 17862, 17862, 17863, 17863, 17866, 17866, 17869, 17869, 17872, 17872, 17914, 17914, 17946, 17946, 18013, 18013, 18026, 18026, 18031, 18031, 18083, 18083, 18116, 18116, 18117, 18117, 18118, 18118, 18148, 18148, 18177, 18177, 18178, 18178, 21598, 21598

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 19258-19645
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19285, 19429, 19429, 21738, 21738

### `DataExporter` (class, 345 lines)

- Def site: line 6781-7125
- References: 261
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5604, 5604, 5737, 5737, 6827, 6827, 6843, 6843, 6844, 6844, 6867, 6867, 6869, 6869, 6872, 6872, 6886, 6886, 6888, 6888, 6897, 6897, 6899, 6899, 6900, 6900, 6906, 6906, 6907, 6907, 6907, 6924, 6924, 6928, 6928, 6970, 6970, 7001, 7001, 7004, 7004, 7006, 7006, 7052, 7052, 7062, 7062, 7095, 7095, 7100, 7100, 7107, 7107, 7329, 7329, 7361, 7361, 7372, 7372, 7397, 7397, 7417, 7417, 7929, 7929, 8722, 8722, 9001, 9001, 9016, 9080, 9080, 9097, 9097, 9115, 9115, 9136, 9136, 9695, 9695, 9770, 9770, 10100, 10100, 10451, 10451, 10536, 10552, 10672, 10672, 10676, 10676, 10696, 10696, 10709, 10709, 10713, 10713, 10731, 10731, 10893, 10893, 11240, 11240, 11387, 11387, 11464, 11464, 11468, 11468, 11473, 11473, 11606, 11606, 11625, 11625, 11676, 11676, 11679, 11679, 11830, 11830, 11833, 11833, 11932, 11932, 11938, 11938, 12235, 12235, 12252, 12252, 12267, 12267, 12481, 12481, 12509, 12509, 12525, 12525, 12562, 12562, 12600, 12600, 12689, 12689, 12718, 12718, 12756, 12756, 12807, 12872, 12872, 12878, 12878, 12920, 12920, 13089, 13089, 13095, 13095, 13214, 13214, 13222, 13222, 13386, 13386, 13437, 13610, 13610, 13781, 13781, 14294, 14294, 14655, 14655, 14661, 14661, 15569, 15569, 15628, 15735, 15871, 15871, 15889, 15889, 15907, 15907, 15934, 15934, 15935, 15935, 17585, 17585, 17678, 17764, 17764, 17785, 19093, 19093, 19611, 19611, 19696, 19696, 19717, 19717, 21106, 21106, 21767, 21767, 21783, 21783
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12928-13268
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12945, 12945, 12947, 12947, 12951, 12951, 12952, 12952, 12966, 12966, 12972, 12972, 12975, 12975, 12978, 12978, 13036, 13036, 13042, 13042, 13047, 13047, 13061, 13061, 13079, 13079, 13189, 13189, 13193, 13193, 13195, 13195, 13198, 13198, 13235, 13235, 13240, 13240, 13254, 13254, 13258, 13258, 13260, 13260, 13263, 13263, 13268, 13268, 21644, 21644, 21648, 21648, 21652, 21652

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7128-7455
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7230, 7230, 8446, 8927, 8946, 9047, 9176, 9199, 9871, 10179, 10224, 10638, 11408, 11419, 11482, 11899

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14759-15086
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12216, 12216, 12275, 12275, 12276, 12276, 13440, 14800, 14800, 14802, 14802, 14808, 14808, 14822, 14822, 14861, 14861, 14864, 14864, 14866, 14866, 14867, 14867, 14868, 14868, 14922, 14922, 14923, 14923, 14934, 14934, 14943, 14943, 14962, 14962, 15014, 15014, 15018, 15018, 15026, 15026, 15027, 15027, 15051, 15051, 15055, 15055
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16143-16431
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16171, 16171, 16174, 16174, 16179, 16179, 16182, 16182, 16226, 16226, 16232, 16232, 16263, 16263, 16266, 16266, 16270, 16270, 16296, 16296, 16313, 16313, 16319, 16319, 16333, 16333, 16334, 16334, 16336, 16336, 16342, 16342, 16349, 16349, 16358, 16358, 16405, 16405, 16427, 16427, 16428, 16428, 16429, 16429, 21589, 21589

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10245-10517
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10268, 10268, 10269, 10269, 10282, 10282, 10283, 10283, 10285, 10285, 10286, 10286, 10289, 10289, 10292, 10292, 10296, 10296, 10297, 10297, 10373, 10373, 10377, 10377, 10380, 10380, 10393, 10393, 10430, 10430, 10447, 10447, 10460, 10460, 10462, 10462, 10469, 10469, 10478, 10478, 10487, 10487, 10488, 10488, 10499, 10499, 10503, 10503, 10512, 10512, 10517, 10517, 21846, 21846

### `CacheUtils` (class, 264 lines)

- Def site: line 5197-5460
- References: 115
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5237, 5237, 5239, 5239, 5321, 5321, 5327, 5327, 5364, 5364, 5366, 5366, 5375, 5375, 5385, 5385, 5395, 5395, 5431, 5431, 7965, 7965, 9623, 9623, 9624, 9624, 9935, 9935, 10781, 10781, 10801, 10801, 12802, 15208, 15208, 15214, 15214, 15215, 15215, 15216, 15216, 15217, 15217, 15218, 15218, 15219, 15219, 15226, 15226, 15254, 15254, 15626, 15872, 15872, 15890, 15890, 15908, 15908, 15958, 16469, 16469, 16470, 16470, 17298, 17298, 17299, 17299, 17673, 17709, 17709, 17733, 17733, 17757, 17757, 17901, 17901, 17902, 17902, 17903, 17903, 17904, 17904, 18240, 18240, 21331, 21331, 21883, 21883
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 11012-11262
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11019, 11019, 11022, 11022, 11027, 11027, 11028, 11028, 11036, 11036, 11039, 11039, 11047, 11047, 11087, 11087, 11095, 11095, 11143, 11143, 11160, 11160, 11163, 11163, 11165, 11165, 11229, 11229, 11230, 11230, 21849, 21849

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15338-15582
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15204, 15204, 15364, 15364, 15366, 15366, 15367, 15367, 15368, 15368, 15396, 15396, 15401, 15401, 15423, 15423, 15424, 15424, 15466, 15466, 15474, 15474, 15500, 15500, 15509, 15509, 15517, 15517, 15548, 15548, 21420, 21420, 21424, 21424

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6200-6420
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6223, 6223, 6274, 6274, 6344, 6344, 6368, 6368, 6380, 6380, 6382, 6382, 6392, 6392, 6407, 6407, 6411, 6411, 6412, 6412, 6415, 6415, 6417, 6417, 12915, 12915, 15630
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 21933-22146
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22789, 22789, 22792, 22873, 23244

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7656-7865
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7669, 7669, 7675, 7675, 7676, 7676, 7679, 7679, 7702, 7702, 7705, 7705, 7708, 7708, 7709, 7709, 7711, 7711, 7778, 7778, 7822, 7822, 8287, 8287, 13236, 13236, 15733, 15996, 15996, 16156, 16156

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12534-12736
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12555, 12555, 12564, 12564, 12626, 12626, 12633, 12633, 12665, 12665, 12667, 12667, 12691, 12691, 12726, 12726, 12733, 12733, 12764, 12764, 15278, 15278, 21456, 21456, 21458, 21458, 21459, 21459, 21461, 21461

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13787-13974
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21806, 21806, 21807, 21807, 21808, 21808, 21809, 21809, 21810, 21810, 21811, 21811, 21812, 21812, 21813, 21813, 21815, 21815, 21816, 21816, 21817, 21817, 21818, 21818, 21819, 21819, 21820, 21820, 21821, 21821, 21823, 21823, 21824, 21824, 21825, 21825, 21826, 21826, 21827, 21827, 21828, 21828, 21829, 21829, 21830, 21830, 21831, 21831, 21833, 21833, 21834, 21834, 21835, 21835, 21836, 21836, 21837, 21837, 21838, 21838, 21839, 21839, 21840, 21840, 21841, 21841, 21843, 21843, 21844, 21844

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5612-5791
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5700, 5700, 5737, 5737, 5739, 5739, 5742, 5742, 5750, 5750, 5752, 5752, 5754, 5754, 5757, 5757, 5786, 5786, 5789, 5789, 21583, 21583

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6600-6778
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6645, 6645, 6683, 6683, 6694, 6694, 6720, 6720, 6721, 6721, 6723, 6723, 6729, 6729, 6730, 6730, 6733, 6733, 6739, 6739, 6740, 6740, 6743, 6743, 6745, 6745, 6755, 6755, 6757, 6757, 6758, 6758, 6760, 6760

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11492-11659
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11599, 11599, 11618, 11618, 11636, 11636, 11645, 11645, 11648, 11648, 11649, 11649, 11652, 11652, 11657, 11657, 11659, 11659, 21484, 21484

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11704-11871
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11741, 11741, 11743, 11743, 11746, 11746, 11817, 11817, 11819, 11819, 11832, 11832, 11836, 11836, 21487, 21487, 21488, 21488, 21489, 21489, 21527, 21527, 21532, 21532

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10737-10898
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10775, 10775, 10782, 10782, 10789, 10789, 10795, 10795, 10802, 10802, 10809, 10809, 10870, 10870, 10881, 10881, 21475, 21475, 21476, 21476, 21478, 21478, 21479, 21479, 21480, 21480

### `CLIShellManager` (class, 161 lines)

- Def site: line 15977-16137
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16000, 16000, 16002, 16002, 16071, 16071, 16073, 16073, 16092, 16092, 16094, 16094, 16094, 16110, 16110, 16126, 16126, 16127, 16127, 16133, 16133, 21588, 21588

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6428-6585
- References: 205
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5495, 5495, 5602, 5602, 5603, 5603, 6444, 6444, 6457, 6457, 6460, 6460, 6484, 6484, 6492, 6492, 6493, 6493, 6515, 6515, 6520, 6520, 6522, 6522, 6595, 6595, 6596, 6596, 7003, 7003, 7028, 7028, 7097, 7097, 7098, 7098, 7427, 7427, 7441, 7441, 7442, 7442, 7927, 7927, 7928, 7928, 8850, 8850, 9015, 9075, 9075, 9077, 9077, 9078, 9078, 9095, 9095, 9096, 9096, 9113, 9113, 9114, 9114, 9134, 9134, 9135, 9135, 9692, 9692, 9693, 9693, 9767, 9767, 9768, 9768, 10096, 10096, 10099, 10099, 10674, 10674, 10675, 10675, 10711, 10711, 10712, 10712, 10891, 10891, 10892, 10892, 11236, 11236, 11237, 11237, 11383, 11383, 11384, 11384, 11466, 11466, 11467, 11467, 11678, 11678, 11853, 11853, 11854, 11854, 11930, 11930, 11931, 11931, 12234, 12234, 12250, 12250, 12251, 12251, 12479, 12479, 12480, 12480, 12559, 12559, 12560, 12560, 12561, 12561, 12597, 12597, 12598, 12598, 12686, 12686, 12687, 12687, 12715, 12715, 12716, 12716, 12753, 12753, 12754, 12754, 12806, 12875, 12875, 12876, 12876, 12918, 12918, 12919, 12919, 13087, 13087, 13088, 13088, 13212, 13212, 13213, 13213, 13436, 13608, 13608, 14660, 14660, 15567, 15567, 15568, 15568, 15629, 15737, 17762, 17762, 17763, 17763, 19601, 19601
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15100-15255
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15122, 15122, 15128, 15128, 15130, 15130, 15158, 15158, 15184, 15184, 15187, 15187, 15190, 15190, 21574, 21574, 21578, 21578, 21586, 21586

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13271-13416
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13310, 13310, 13317, 13317, 13342, 13342, 13345, 13345, 13358, 13358, 13402, 13402, 13406, 13406, 13411, 13411, 13412, 13412, 13416, 13416, 21881, 21881

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13424-13568
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12645, 12645, 12821, 12821, 12899, 12899, 12904, 12904, 13453, 13453, 13459, 13459, 13465, 13465, 13471, 13471, 13477, 13477, 13483, 13483, 13489, 13489, 13495, 13495, 13501, 13501, 13507, 13507, 13513, 13513, 13519, 13519, 13525, 13525, 13531, 13531, 13537, 13537, 13543, 13543, 13549, 13549, 13555, 13555, 13561, 13561, 13567, 13567, 21494, 21494, 21635, 21635, 21637, 21637, 21752, 21752, 21878, 21878, 21879, 21879, 21880, 21880, 21899, 21899, 21900, 21900, 21901, 21901, 21902, 21902, 21903, 21903, 21904, 21904, 21905, 21905
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10591-10734
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10605, 10605, 10606, 10606, 10692, 10692, 10727, 10727, 21469, 21469, 21470, 21470, 21471, 21471, 21472, 21472, 21473, 21473

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13571-13709
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13640, 13640, 13643, 13643, 13644, 13644, 13645, 13645, 13665, 13665, 13668, 13668, 13676, 13676, 13681, 13681, 21907, 21907

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8893-9021
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8964, 8964, 8975, 8975, 15198, 15198, 15199, 15199, 21372, 21372, 21373, 21373, 21552, 21552

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11265-11393
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11272, 11272, 11277, 11277, 11278, 11278, 11279, 11279, 11282, 11282, 11283, 11283, 11346, 11346, 11353, 11353, 11380, 11380, 21851, 21851

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15723-15849
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15743, 15743, 15748, 15748, 15753, 15753, 15790, 15790, 15796, 15796, 15802, 15802, 15808, 15808, 15814, 15814, 15815, 15815, 15816, 15816, 15817, 15817, 15818, 15818, 15822, 15822, 15831, 15831, 15835, 15835, 15838, 15838, 15844, 15844, 21547, 21547

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5845-5969
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5866, 5866, 5868, 5868, 5884, 5884, 5896, 5896, 5935, 5935, 5936, 5936, 5937, 5937, 5938, 5938, 5939, 5939, 5950, 5950, 5953, 5953, 6885, 6885, 22906, 22906, 23489, 23489

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 9027-9138
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7965, 7965, 9623, 9623, 9935, 9935, 10781, 10781, 10801, 10801, 12803, 15147, 15147, 15200, 15200, 15633, 15873, 15873, 15891, 15891, 15909, 15909, 17299, 17299, 17674, 17711, 17711, 17735, 17735, 17759, 17759, 17902, 17902, 18243, 18243, 21413, 21413, 21428, 21428, 21438, 21438, 21438, 21438, 21448, 21448
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10901-11009
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10956, 10956, 10959, 10959, 10960, 10960, 10965, 10965, 10983, 10983, 10983, 10992, 10992, 10992, 10992, 10993, 10993, 10993, 10993, 11051, 11051, 11054, 11054, 11066, 11066, 11067, 11067, 11080, 11080, 11119, 11119, 11127, 11127, 11181, 11181, 11189, 11189

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12826-12925
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12891, 12891, 12893, 12893, 12894, 12894, 21422, 21422, 21490, 21490, 21492, 21492, 21493, 21493

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15615-15712
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15358, 15358, 15593, 15593, 15651, 15651, 15657, 15657, 15663, 15663, 15669, 15669, 15675, 15675, 15681, 15681, 15687, 15687, 15693, 15693, 15699, 15699, 15705, 15705, 15711, 15711, 15959, 17298, 17298, 17675, 17903, 17903, 17906, 17906, 18242, 18242, 21379, 21379, 21446, 21446, 21452, 21452, 21503, 21503, 21560, 21560
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8323-8419
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8379, 8379, 8415, 8415, 16473, 16473

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11396-11489
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11448, 11448, 11461, 11461, 21482, 21482, 21524, 21524, 21525, 21525, 21530, 21530, 21531, 21531

### `ValidationUtils` (class, 90 lines)

- Def site: line 5975-6064
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6057, 6057, 15421, 15421, 15422, 15422, 15636, 21282, 21282
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12739-12823
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12773, 12773, 21457, 21457, 21465, 21465, 21491, 21491, 21636, 21636

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 19672-19750
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19667, 19667, 19668, 19668, 21731, 21731
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17689-17766
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21602, 21602, 21606, 21606, 21610, 21610
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1869-1942
- References: 277
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1882, 1882, 1914, 1914, 2189, 2189, 2278, 2278, 2305, 2305, 7677, 7677, 7763, 7763, 7893, 7893, 7970, 7970, 8053, 8053, 8283, 8283, 8472, 8472, 8528, 8528, 8541, 8541, 8558, 8558, 8603, 8603, 8634, 8634, 8640, 8640, 8743, 8743, 10284, 10284, 10551, 11053, 11053, 11082, 11082, 11347, 11347, 11553, 11553, 11792, 11792, 12508, 12508, 12524, 12524, 13311, 13311, 13730, 13730, 13780, 13780, 15634, 15836, 15836, 15869, 15869, 15887, 15887, 15905, 15905, 15932, 15932, 15957, 17359, 17359, 17486, 17486, 17677, 17716, 17716, 17741, 17741, 17784, 17883, 17883, 18095, 18095, 18238, 18238, 19242, 19242, 19332, 19332, 19662, 19662, 19692, 19692, 19713, 19713, 19732, 19732, 19748, 19748, 19765, 19765, 20256, 20256, 20313, 20313, 20325, 20325, 20338, 20338, 20355, 20355, 20518, 20518, 21229, 21229, 21249, 21249, 21284, 21284, 21297, 21297, 21765, 21765, 21856, 21856, 21861, 21861, 21867, 21867, 21886, 21886, 21892, 21892, 23512, 23512, 23610, 23610
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

- Def site: line 15261-15332
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21568, 21568, 21569, 21569, 21570, 21570, 21571, 21571

### `DisplayUtils` (class, 70 lines)

- Def site: line 5466-5535
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5498, 5498, 5499, 5499, 5514, 5514, 5516, 5516, 5605, 5605, 18611, 18611, 18650, 18650, 18709, 18709

### `ConfigUtils` (class, 70 lines)

- Def site: line 6070-6139
- References: 199
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6112, 6112, 6117, 6117, 6214, 6214, 6272, 6272, 7163, 7163, 7820, 7820, 8465, 8465, 8488, 8488, 8508, 8508, 8693, 8693, 8714, 8714, 8989, 8989, 9014, 9014, 9069, 9069, 9091, 9091, 9108, 9108, 9125, 9125, 9510, 9510, 9733, 9733, 9750, 9750, 10142, 10142, 10474, 10474, 10685, 10685, 10722, 10722, 10875, 10875, 11018, 11018, 11271, 11271, 11459, 11459, 11643, 11643, 11962, 11962, 12298, 12298, 12470, 12470, 12510, 12510, 12516, 12516, 12610, 12610, 12840, 12840, 12913, 12913, 13400, 13400, 13435, 13634, 13634, 15141, 15141, 15357, 15357, 15625, 15732, 15832, 15832, 15867, 15867, 15885, 15885, 15903, 15903, 15938, 15938, 16472, 16472, 17279, 17279, 17672, 17782, 18290, 18290, 19243, 19243, 19248, 19248, 19250, 19250, 19663, 19663, 19665, 19665, 19689, 19689, 19693, 19693, 19694, 19694, 19714, 19714, 19715, 19715, 19977, 19977, 20763, 20763, 21333, 21333, 21365, 21365, 21402, 21402, 21408, 21408, 21536, 21536, 21593, 21593, 21676, 21676, 21685, 21685, 21763, 21763, 21764, 21764, 21781, 21781, 21856, 21856, 21861, 21861, 21867, 21867, 21886, 21886, 21892, 21892, 22803, 22803, 22874, 23376, 23376, 23464, 23464
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10520-10588
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10560, 10560, 10565, 10565, 10570, 10570, 10571, 10571, 10577, 10577, 10578, 10578, 10584, 10584, 10585, 10585, 10586, 10586, 10587, 10587, 21909, 21909

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 21288-21353
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21336, 21336, 21344, 21344, 21353, 21353, 21882, 21882

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15856-15911
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21507, 21507, 21511, 21511, 21716, 21716

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6145-6191
- References: 59
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6269, 6269, 8155, 8155, 9070, 9070, 9093, 9093, 9580, 9580, 9615, 9615, 9629, 9629, 9752, 9752, 9756, 9756, 10304, 10304, 12614, 12614, 13284, 13284, 13410, 13410, 13442, 13620, 13620, 13656, 13656, 15631, 18398, 18398, 19244, 19244, 19553, 19553, 19664, 19664, 19695, 19695, 19716, 19716, 21766, 21766, 21782, 21782, 23395, 23395
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5794-5839
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5236, 5236, 5278, 5278, 5323, 5323, 5429, 5429, 5444, 5444, 5784, 5784, 5785, 5785, 5829, 5829, 6295, 6295, 7989, 7989, 9280, 9280, 9591, 9591, 9607, 9607, 9936, 9936, 10817, 10817, 10836, 10836, 12805, 15224, 15224, 15627, 15870, 15870, 15888, 15888, 15906, 15906, 15933, 15933, 15960, 16382, 16382, 16422, 16422, 16423, 16423, 16424, 16424, 16468, 16468, 17300, 17300, 17307, 17307, 17676, 17708, 17708, 17732, 17732, 17736, 17736, 17756, 17756, 17783, 17858, 17858, 17892, 17892, 17913, 17913, 17945, 17945, 18007, 18007, 18046, 18046, 18196, 18196, 18241, 18241, 19245, 19245, 19816, 19816
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17772-17814
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17795, 17795, 17801, 17801, 17807, 17807, 17813, 17813, 21700, 21700, 21704, 21704, 21708, 21708, 21712, 21712

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11662-11701
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11699, 11699, 21906, 21906

### `TimeUtils` (class, 29 lines)

- Def site: line 1833-1861
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8943, 8943, 8944, 8944, 8973, 8973, 8974, 8974, 8990, 8990, 8991, 8991, 9869, 9869, 9870, 9870, 10174, 10174, 10175, 10175, 10222, 10222, 10223, 10223, 10778, 10778, 10780, 10780, 10798, 10798, 10800, 10800, 11688, 11688, 11689, 11689, 12349, 12349, 12350, 12350, 12455, 12455, 12456, 12456, 13438
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15585-15612
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15599, 15599, 15605, 15605, 15611, 15611, 21614, 21614, 21618, 21618
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15946-15971
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15966, 15966, 15971, 15971, 21622, 21622, 21627, 21627
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2097-2121
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2183, 2242, 19361, 23219

### `RoutingUtils` (class, 22 lines)

- Def site: line 13737-13758
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21388, 21388, 21392, 21392, 21396, 21396
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 18224-18245
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19247, 19247, 21535, 21535, 21592, 21592, 21675, 21675, 21684, 21684

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 19648-19669
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21745, 21745
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7627-7647
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6378, 10147, 15470, 15635
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13983-13992
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14019, 14155, 14232, 14251, 14263, 14284, 14297, 14308, 14314, 14327, 14420, 14555, 14650

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 281-289
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

- Def site: line 308-316
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5552, 15293, 15310, 15326

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 293-300
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

- Def site: line 268-270
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13443, 13732, 19697, 19718, 20750, 20781, 20813, 21048, 21063
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 596-598
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1210, 1879, 1879, 1879, 1891, 1897, 6271, 6391, 7451, 7511, 9679, 9790, 10044, 10874, 13445, 15503, 15545, 15643, 17381, 17501, 21768
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 34, 78, 162
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 56
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 36, 212, 255
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 903, 905

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 1981-1983
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1981, 7461, 7468, 7469, 10055, 15492

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 1999-2001
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1999, 15639, 17289, 17289, 17680
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 716-1720
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1765

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
