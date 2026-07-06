# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 179 first-party files
- Definitions analyzed: 105
- LOC saveable (unused + single-use): 64
- Category counts: unused=0, single-use=4, low-use=20, hot=80, skipped=1

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
| `run_systematic_test` | function | 22 | 1 | single-use | RunSystematicTestManager | missing_action_logging |
| `execute_with_connection_pool_management` | function | 21 | 7 | hot |  |  |
| `switch_to_interactive_login` | function | 20 | 1 | single-use | SwitchToInteractiveLoginManager |  |
| `BulkSwitchFirmwareUpgrader` | class | 19 | 2 | low-use | FirmwareManager | missing_inline_comments,missing_action_logging |
| `initialize_mist_session_interactive` | function | 18 | 3 | low-use | InitializeMistSessionInteractiveManager | missing_action_logging |
| `initialize_mist_session` | function | 18 | 2 | low-use | InitializeMistSessionManager | missing_action_logging |
| `run_interactive_test` | function | 18 | 1 | single-use | RunInteractiveTestManager |  |
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

## Single-Use (4)

### `run_systematic_test` (function, 22 lines)

- Def site: line 22756-22777
- References: 1
- Suggested class: `RunSystematicTestManager`
- Suggested module: `src/refactors/run_systematic_test.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_systematic_test_mode()`; extract `run_systematic_test` OUT of the entrypoint into a new `src/refactors/run_systematic_test.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23666

### `switch_to_interactive_login` (function, 20 lines)

- Def site: line 2288-2307
- References: 1
- Suggested class: `SwitchToInteractiveLoginManager`
- Suggested module: `src/refactors/switch_to_interactive_login.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `switch_to_interactive_login` OUT of the entrypoint into a new `src/refactors/switch_to_interactive_login.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21539

### `run_interactive_test` (function, 18 lines)

- Def site: line 22927-22944
- References: 1
- Suggested class: `RunInteractiveTestManager`
- Suggested module: `src/refactors/run_interactive_test.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_interactive_test_mode()`; extract `run_interactive_test` OUT of the entrypoint into a new `src/refactors/run_interactive_test.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23672

### `listen_keyboard` (function, 4 lines)

- Def site: line 641-644
- References: 1
- Suggested class: `ListenKeyboardManager`
- Suggested module: `src/refactors/listen_keyboard.py`
- Rationale: single-use: sole caller lives inside MistHelper.py from `_run_interactive()`; extract `listen_keyboard` OUT of the entrypoint into a new `src/refactors/listen_keyboard.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16151

## Low-Use (20)

### `FirmwareUpgradeStatusChecker` (class, 958 lines)

- Def site: line 18270-19227
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

- Def site: line 19896-20682
- References: 3
- Suggested class: `WLANRadiusTimerManager`
- Suggested module: `src/refactors/wlanradius_timer_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_apply_site_template_response()`; extract `WLANRadiusTimerManager` OUT of the entrypoint into a new `src/refactors/wlanradius_timer_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20063, 20063, 21534

### `WANProbeConfigManager` (class, 473 lines)

- Def site: line 17200-17672
- References: 2
- Suggested class: `WANProbeConfigManager`
- Suggested module: `src/refactors/wanprobe_config_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeConfigManager` OUT of the entrypoint into a new `src/refactors/wanprobe_config_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21739, 21739

### `AnomalyMetricsDiscovery` (class, 91 lines)

- Def site: line 19798-19888
- References: 2
- Suggested class: `AnomalyMetricsDiscovery`
- Suggested module: `src/refactors/anomaly_metrics_discovery.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_discover_site_anomaly_metrics()`; extract `AnomalyMetricsDiscovery` OUT of the entrypoint into a new `src/refactors/anomaly_metrics_discovery.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13013, 13013

### `DeviceDataFetcher` (class, 68 lines)

- Def site: line 5557-5624
- References: 3
- Suggested class: `DeviceDataFetcher`
- Suggested module: `src/refactors/device_data_fetcher.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `device_stats()`; extract `DeviceDataFetcher` OUT of the entrypoint into a new `src/refactors/device_data_fetcher.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15311, 15328, 15344

### `InventoryCSVComparator` (class, 47 lines)

- Def site: line 16468-16514
- References: 3
- Suggested class: `InventoryCSVComparator`
- Suggested module: `src/refactors/inventory_csvcomparator.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `__init__()`; extract `InventoryCSVComparator` OUT of the entrypoint into a new `src/refactors/inventory_csvcomparator.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16507, 16507, 21560

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 19240-19271
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

- Def site: line 15933-15959
- References: 2
- Suggested class: `DeviceConfigTemplateClonerManager`
- Suggested module: `src/refactors/device_config_template_cloner_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `DeviceConfigTemplateClonerManager` OUT of the entrypoint into a new `src/refactors/device_config_template_cloner_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21941, 21941

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17680-17702
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21743, 21743

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 19772-19790
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

- Def site: line 2174-2191
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2234, 19375, 23253

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2822-2839
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23258, 23321

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 347-359
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 347, 531

### `main` (function, 12 lines)

- Def site: line 23649-23660
- References: 2
- Suggested class: `MainManager`
- Suggested module: `src/refactors/main.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `main` OUT of the entrypoint into a new `src/refactors/main.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 23759
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6613-6616
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6613, 15755
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1966-1968
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1966, 9999, 15428

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1969-1971
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1969, 7489

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1974-1976
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1974, 15568

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 1981-1983
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1981, 7479

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 1989-1991
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1989, 15657
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2884-5210
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2884, 6659, 6660, 6669, 6833

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 14014-14772
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14491, 14491, 14503, 14503, 14531, 14531, 14543, 14543, 14604, 14604, 14641, 14641, 14798, 21658

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9160-9845
- References: 112
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5666, 5666, 9283, 9283, 9334, 9334, 9337, 9337, 9378, 9378, 9417, 9417, 9435, 9435, 9513, 9513, 9520, 9520, 9530, 9530, 9533, 9533, 9546, 9546, 9547, 9547, 9548, 9548, 9549, 9549, 9557, 9557, 9559, 9559, 9560, 9560, 9561, 9561, 9562, 9562, 9565, 9565, 9568, 9568, 9571, 9571, 9574, 9574, 9620, 9620, 9643, 9643, 9644, 9644, 9645, 9645, 9647, 9647, 9683, 9683, 9699, 9699, 9753, 9753, 9754, 9754, 9755, 9755, 9758, 9758, 9759, 9759, 9778, 9778, 9780, 9780, 9781, 9781, 9816, 9816, 15167, 15167, 15220, 15220, 15651, 16490, 16490, 17729, 17729, 17753, 17753, 17777, 17777, 17920, 17920, 21433, 21433, 21440, 21440, 21449, 21449, 21453, 21453, 21462, 21462
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16520-17194
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16908, 16908, 21904, 21910

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11893-12545
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10670, 10670, 10679, 10679, 10767, 10767, 10774, 10774, 11448, 11448, 11734, 11734, 11739, 11739, 11746, 11746, 11751, 11751, 11965, 11965, 11987, 11987, 11990, 11990, 12016, 12016, 12025, 12025, 12026, 12026, 12047, 12047, 12090, 12090, 12136, 12136, 12147, 12147, 12174, 12174, 12179, 12179, 12180, 12180, 12181, 12181, 12213, 12213, 12219, 12219, 12244, 12244, 12264, 12264, 12299, 12299, 12314, 12314, 12320, 12320, 12322, 12322, 12325, 12325, 12327, 12327, 12331, 12331, 12335, 12335, 12340, 12340, 12347, 12347, 12354, 12354, 12361, 12361, 12370, 12370, 12380, 12380, 12387, 12387, 12394, 12394, 12401, 12401, 12408, 12408, 12415, 12415, 12425, 12425, 12434, 12434, 12443, 12443, 12452, 12452, 12461, 12461, 12490, 12490, 21394, 21394, 21575, 21575, 21652, 21652, 21653, 21653, 21661, 21661, 21866, 21866, 21867, 21867, 21886, 21886, 21893, 21893, 21894, 21894, 21895, 21895, 21896, 21896

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 20690-21276
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20967, 20967, 20968, 20968, 20971, 20971, 20973, 20973, 20975, 20975, 20991, 20991, 21811

### `menu_actions` (assignment, 572 lines)

- Def site: line 21375-21946
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21375, 22660, 22661, 22670, 22814, 22814, 22856, 22914, 22979, 23470, 23474, 23519, 23519, 23546, 23546, 23549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8444-8906
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8485, 8485, 8490, 8490, 8500, 8500, 8508, 8508, 8513, 8513, 8518, 8518, 8528, 8528, 8533, 8533, 8538, 8538, 8558, 8558, 8568, 8568, 8569, 8569, 8572, 8572, 8602, 8602, 8688, 8688, 8690, 8690, 8714, 8714, 8720, 8720, 8725, 8725, 8734, 8734, 8738, 8738, 8757, 8757, 8760, 8760, 8771, 8771, 8772, 8772, 8867, 8867, 8888, 8888, 21934, 21934, 21935, 21935, 21936, 21936, 21937, 21937, 21938, 21938, 21939, 21939

### `OperationRegistry` (class, 461 lines)

- Def site: line 22171-22631
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22638, 22638, 22642, 22642, 22662, 22662, 22667, 22667, 22915

### `PromptUtils` (class, 441 lines)

- Def site: line 7891-8331
- References: 125
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5595, 5595, 5603, 5603, 7836, 7836, 7852, 7852, 7856, 7856, 7857, 7857, 7858, 7858, 7873, 7873, 7879, 7879, 7906, 7906, 7909, 7909, 7917, 7917, 7935, 7935, 7985, 7985, 7993, 7993, 7998, 7998, 8044, 8044, 8055, 8055, 8080, 8080, 8099, 8099, 8100, 8100, 8103, 8103, 8104, 8104, 8194, 8194, 8196, 8196, 8200, 8200, 8228, 8228, 8229, 8229, 8230, 8230, 8231, 8231, 8232, 8232, 8241, 8241, 8285, 8285, 8309, 8309, 12625, 12625, 12675, 12675, 12680, 12680, 12823, 12906, 12906, 12960, 12960, 12981, 12981, 12986, 12986, 13250, 13250, 13453, 13655, 13655, 13742, 13742, 13747, 13747, 13797, 13797, 13798, 13798, 15294, 15294, 15753, 17736, 17736, 18258, 18258, 18359, 18359, 19987, 19987, 21299, 21299, 21300, 21300, 21586, 21586
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9848-10261
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5660, 5660, 9881, 9881, 9965, 9965, 9971, 9971, 9974, 9974, 10018, 10018, 10032, 10032, 10059, 10059, 10065, 10065, 10079, 10079, 10162, 10162, 10164, 10164, 10168, 10168, 10170, 10170, 10173, 10173, 10177, 10177, 10180, 10180, 10190, 10190, 10196, 10196, 10234, 10234, 15168, 15168, 15169, 15169, 15170, 15170, 15221, 15221, 15222, 15222, 21434, 21434, 21435, 21435, 21436, 21436, 21460, 21460

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17839-18236
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17860, 17860, 17865, 17865, 17869, 17869, 17872, 17872, 17879, 17879, 17881, 17881, 17882, 17882, 17885, 17885, 17888, 17888, 17891, 17891, 17933, 17933, 17965, 17965, 18032, 18032, 18045, 18045, 18050, 18050, 18102, 18102, 18135, 18135, 18136, 18136, 18137, 18137, 18167, 18167, 18196, 18196, 18197, 18197, 21617, 21617

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 19277-19664
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19304, 19448, 19448, 21757, 21757

### `DataExporter` (class, 345 lines)

- Def site: line 6800-7144
- References: 261
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5623, 5623, 5756, 5756, 6846, 6846, 6862, 6862, 6863, 6863, 6886, 6886, 6888, 6888, 6891, 6891, 6905, 6905, 6907, 6907, 6916, 6916, 6918, 6918, 6919, 6919, 6925, 6925, 6926, 6926, 6926, 6943, 6943, 6947, 6947, 6989, 6989, 7020, 7020, 7023, 7023, 7025, 7025, 7071, 7071, 7081, 7081, 7114, 7114, 7119, 7119, 7126, 7126, 7348, 7348, 7380, 7380, 7391, 7391, 7416, 7416, 7436, 7436, 7948, 7948, 8741, 8741, 9020, 9020, 9035, 9099, 9099, 9116, 9116, 9134, 9134, 9155, 9155, 9714, 9714, 9789, 9789, 10119, 10119, 10470, 10470, 10555, 10571, 10691, 10691, 10695, 10695, 10715, 10715, 10728, 10728, 10732, 10732, 10750, 10750, 10912, 10912, 11259, 11259, 11406, 11406, 11483, 11483, 11487, 11487, 11492, 11492, 11625, 11625, 11644, 11644, 11695, 11695, 11698, 11698, 11849, 11849, 11852, 11852, 11951, 11951, 11957, 11957, 12254, 12254, 12271, 12271, 12286, 12286, 12500, 12500, 12528, 12528, 12544, 12544, 12581, 12581, 12619, 12619, 12708, 12708, 12737, 12737, 12775, 12775, 12826, 12891, 12891, 12897, 12897, 12939, 12939, 13108, 13108, 13114, 13114, 13233, 13233, 13241, 13241, 13405, 13405, 13456, 13629, 13629, 13800, 13800, 14313, 14313, 14674, 14674, 14680, 14680, 15588, 15588, 15647, 15754, 15890, 15890, 15908, 15908, 15926, 15926, 15953, 15953, 15954, 15954, 17604, 17604, 17697, 17783, 17783, 17804, 19112, 19112, 19630, 19630, 19715, 19715, 19736, 19736, 21125, 21125, 21786, 21786, 21802, 21802
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12947-13287
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12964, 12964, 12966, 12966, 12970, 12970, 12971, 12971, 12985, 12985, 12991, 12991, 12994, 12994, 12997, 12997, 13055, 13055, 13061, 13061, 13066, 13066, 13080, 13080, 13098, 13098, 13208, 13208, 13212, 13212, 13214, 13214, 13217, 13217, 13254, 13254, 13259, 13259, 13273, 13273, 13277, 13277, 13279, 13279, 13282, 13282, 13287, 13287, 21663, 21663, 21667, 21667, 21671, 21671

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7147-7474
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7249, 7249, 8465, 8946, 8965, 9066, 9195, 9218, 9890, 10198, 10243, 10657, 11427, 11438, 11501, 11918

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14778-15105
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12235, 12235, 12294, 12294, 12295, 12295, 13459, 14819, 14819, 14821, 14821, 14827, 14827, 14841, 14841, 14880, 14880, 14883, 14883, 14885, 14885, 14886, 14886, 14887, 14887, 14941, 14941, 14942, 14942, 14953, 14953, 14962, 14962, 14981, 14981, 15033, 15033, 15037, 15037, 15045, 15045, 15046, 15046, 15070, 15070, 15074, 15074
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16162-16450
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16190, 16190, 16193, 16193, 16198, 16198, 16201, 16201, 16245, 16245, 16251, 16251, 16282, 16282, 16285, 16285, 16289, 16289, 16315, 16315, 16332, 16332, 16338, 16338, 16352, 16352, 16353, 16353, 16355, 16355, 16361, 16361, 16368, 16368, 16377, 16377, 16424, 16424, 16446, 16446, 16447, 16447, 16448, 16448, 21608, 21608

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10264-10536
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10287, 10287, 10288, 10288, 10301, 10301, 10302, 10302, 10304, 10304, 10305, 10305, 10308, 10308, 10311, 10311, 10315, 10315, 10316, 10316, 10392, 10392, 10396, 10396, 10399, 10399, 10412, 10412, 10449, 10449, 10466, 10466, 10479, 10479, 10481, 10481, 10488, 10488, 10497, 10497, 10506, 10506, 10507, 10507, 10518, 10518, 10522, 10522, 10531, 10531, 10536, 10536, 21865, 21865

### `CacheUtils` (class, 264 lines)

- Def site: line 5216-5479
- References: 115
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5256, 5256, 5258, 5258, 5340, 5340, 5346, 5346, 5383, 5383, 5385, 5385, 5394, 5394, 5404, 5404, 5414, 5414, 5450, 5450, 7984, 7984, 9642, 9642, 9643, 9643, 9954, 9954, 10800, 10800, 10820, 10820, 12821, 15227, 15227, 15233, 15233, 15234, 15234, 15235, 15235, 15236, 15236, 15237, 15237, 15238, 15238, 15245, 15245, 15273, 15273, 15645, 15891, 15891, 15909, 15909, 15927, 15927, 15977, 16488, 16488, 16489, 16489, 17317, 17317, 17318, 17318, 17692, 17728, 17728, 17752, 17752, 17776, 17776, 17920, 17920, 17921, 17921, 17922, 17922, 17923, 17923, 18259, 18259, 21350, 21350, 21902, 21902
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 11031-11281
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11038, 11038, 11041, 11041, 11046, 11046, 11047, 11047, 11055, 11055, 11058, 11058, 11066, 11066, 11106, 11106, 11114, 11114, 11162, 11162, 11179, 11179, 11182, 11182, 11184, 11184, 11248, 11248, 11249, 11249, 21868, 21868

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15357-15601
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15223, 15223, 15383, 15383, 15385, 15385, 15386, 15386, 15387, 15387, 15415, 15415, 15420, 15420, 15442, 15442, 15443, 15443, 15485, 15485, 15493, 15493, 15519, 15519, 15528, 15528, 15536, 15536, 15567, 15567, 21439, 21439, 21443, 21443

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6219-6439
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6242, 6242, 6293, 6293, 6363, 6363, 6387, 6387, 6399, 6399, 6401, 6401, 6411, 6411, 6426, 6426, 6430, 6430, 6431, 6431, 6434, 6434, 6436, 6436, 12934, 12934, 15649
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 21952-22165
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22832, 22832, 22835, 22916, 23287

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7675-7884
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7688, 7688, 7694, 7694, 7695, 7695, 7698, 7698, 7721, 7721, 7724, 7724, 7727, 7727, 7728, 7728, 7730, 7730, 7797, 7797, 7841, 7841, 8306, 8306, 13255, 13255, 15752, 16015, 16015, 16175, 16175

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12553-12755
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12574, 12574, 12583, 12583, 12645, 12645, 12652, 12652, 12684, 12684, 12686, 12686, 12710, 12710, 12745, 12745, 12752, 12752, 12783, 12783, 15297, 15297, 21475, 21475, 21477, 21477, 21478, 21478, 21480, 21480

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13806-13993
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21825, 21825, 21826, 21826, 21827, 21827, 21828, 21828, 21829, 21829, 21830, 21830, 21831, 21831, 21832, 21832, 21834, 21834, 21835, 21835, 21836, 21836, 21837, 21837, 21838, 21838, 21839, 21839, 21840, 21840, 21842, 21842, 21843, 21843, 21844, 21844, 21845, 21845, 21846, 21846, 21847, 21847, 21848, 21848, 21849, 21849, 21850, 21850, 21852, 21852, 21853, 21853, 21854, 21854, 21855, 21855, 21856, 21856, 21857, 21857, 21858, 21858, 21859, 21859, 21860, 21860, 21862, 21862, 21863, 21863

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5631-5810
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5719, 5719, 5756, 5756, 5758, 5758, 5761, 5761, 5769, 5769, 5771, 5771, 5773, 5773, 5776, 5776, 5805, 5805, 5808, 5808, 21602, 21602

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6619-6797
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6664, 6664, 6702, 6702, 6713, 6713, 6739, 6739, 6740, 6740, 6742, 6742, 6748, 6748, 6749, 6749, 6752, 6752, 6758, 6758, 6759, 6759, 6762, 6762, 6764, 6764, 6774, 6774, 6776, 6776, 6777, 6777, 6779, 6779

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11511-11678
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11618, 11618, 11637, 11637, 11655, 11655, 11664, 11664, 11667, 11667, 11668, 11668, 11671, 11671, 11676, 11676, 11678, 11678, 21503, 21503

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11723-11890
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11760, 11760, 11762, 11762, 11765, 11765, 11836, 11836, 11838, 11838, 11851, 11851, 11855, 11855, 21506, 21506, 21507, 21507, 21508, 21508, 21546, 21546, 21551, 21551

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10756-10917
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10794, 10794, 10801, 10801, 10808, 10808, 10814, 10814, 10821, 10821, 10828, 10828, 10889, 10889, 10900, 10900, 21494, 21494, 21495, 21495, 21497, 21497, 21498, 21498, 21499, 21499

### `CLIShellManager` (class, 161 lines)

- Def site: line 15996-16156
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16019, 16019, 16021, 16021, 16090, 16090, 16092, 16092, 16111, 16111, 16113, 16113, 16113, 16129, 16129, 16145, 16145, 16146, 16146, 16152, 16152, 21607, 21607

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6447-6604
- References: 205
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5514, 5514, 5621, 5621, 5622, 5622, 6463, 6463, 6476, 6476, 6479, 6479, 6503, 6503, 6511, 6511, 6512, 6512, 6534, 6534, 6539, 6539, 6541, 6541, 6614, 6614, 6615, 6615, 7022, 7022, 7047, 7047, 7116, 7116, 7117, 7117, 7446, 7446, 7460, 7460, 7461, 7461, 7946, 7946, 7947, 7947, 8869, 8869, 9034, 9094, 9094, 9096, 9096, 9097, 9097, 9114, 9114, 9115, 9115, 9132, 9132, 9133, 9133, 9153, 9153, 9154, 9154, 9711, 9711, 9712, 9712, 9786, 9786, 9787, 9787, 10115, 10115, 10118, 10118, 10693, 10693, 10694, 10694, 10730, 10730, 10731, 10731, 10910, 10910, 10911, 10911, 11255, 11255, 11256, 11256, 11402, 11402, 11403, 11403, 11485, 11485, 11486, 11486, 11697, 11697, 11872, 11872, 11873, 11873, 11949, 11949, 11950, 11950, 12253, 12253, 12269, 12269, 12270, 12270, 12498, 12498, 12499, 12499, 12578, 12578, 12579, 12579, 12580, 12580, 12616, 12616, 12617, 12617, 12705, 12705, 12706, 12706, 12734, 12734, 12735, 12735, 12772, 12772, 12773, 12773, 12825, 12894, 12894, 12895, 12895, 12937, 12937, 12938, 12938, 13106, 13106, 13107, 13107, 13231, 13231, 13232, 13232, 13455, 13627, 13627, 14679, 14679, 15586, 15586, 15587, 15587, 15648, 15756, 17781, 17781, 17782, 17782, 19620, 19620
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15119-15274
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15141, 15141, 15147, 15147, 15149, 15149, 15177, 15177, 15203, 15203, 15206, 15206, 15209, 15209, 21593, 21593, 21597, 21597, 21605, 21605

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13290-13435
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13329, 13329, 13336, 13336, 13361, 13361, 13364, 13364, 13377, 13377, 13421, 13421, 13425, 13425, 13430, 13430, 13431, 13431, 13435, 13435, 21900, 21900

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13443-13587
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12664, 12664, 12840, 12840, 12918, 12918, 12923, 12923, 13472, 13472, 13478, 13478, 13484, 13484, 13490, 13490, 13496, 13496, 13502, 13502, 13508, 13508, 13514, 13514, 13520, 13520, 13526, 13526, 13532, 13532, 13538, 13538, 13544, 13544, 13550, 13550, 13556, 13556, 13562, 13562, 13568, 13568, 13574, 13574, 13580, 13580, 13586, 13586, 21513, 21513, 21654, 21654, 21656, 21656, 21771, 21771, 21897, 21897, 21898, 21898, 21899, 21899, 21918, 21918, 21919, 21919, 21920, 21920, 21921, 21921, 21922, 21922, 21923, 21923, 21924, 21924
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10610-10753
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10624, 10624, 10625, 10625, 10711, 10711, 10746, 10746, 21488, 21488, 21489, 21489, 21490, 21490, 21491, 21491, 21492, 21492

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13590-13728
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13659, 13659, 13662, 13662, 13663, 13663, 13664, 13664, 13684, 13684, 13687, 13687, 13695, 13695, 13700, 13700, 21926, 21926

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8912-9040
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8983, 8983, 8994, 8994, 15217, 15217, 15218, 15218, 21391, 21391, 21392, 21392, 21571, 21571

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11284-11412
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11291, 11291, 11296, 11296, 11297, 11297, 11298, 11298, 11301, 11301, 11302, 11302, 11365, 11365, 11372, 11372, 11399, 11399, 21870, 21870

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15742-15868
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15762, 15762, 15767, 15767, 15772, 15772, 15809, 15809, 15815, 15815, 15821, 15821, 15827, 15827, 15833, 15833, 15834, 15834, 15835, 15835, 15836, 15836, 15837, 15837, 15841, 15841, 15850, 15850, 15854, 15854, 15857, 15857, 15863, 15863, 21566, 21566

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5864-5988
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5885, 5885, 5887, 5887, 5903, 5903, 5915, 5915, 5954, 5954, 5955, 5955, 5956, 5956, 5957, 5957, 5958, 5958, 5969, 5969, 5972, 5972, 6904, 6904, 22949, 22949, 23532, 23532

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 9046-9157
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7984, 7984, 9642, 9642, 9954, 9954, 10800, 10800, 10820, 10820, 12822, 15166, 15166, 15219, 15219, 15652, 15892, 15892, 15910, 15910, 15928, 15928, 17318, 17318, 17693, 17730, 17730, 17754, 17754, 17778, 17778, 17921, 17921, 18262, 18262, 21432, 21432, 21447, 21447, 21457, 21457, 21457, 21457, 21467, 21467
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10920-11028
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10975, 10975, 10978, 10978, 10979, 10979, 10984, 10984, 11002, 11002, 11002, 11011, 11011, 11011, 11011, 11012, 11012, 11012, 11012, 11070, 11070, 11073, 11073, 11085, 11085, 11086, 11086, 11099, 11099, 11138, 11138, 11146, 11146, 11200, 11200, 11208, 11208

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12845-12944
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12910, 12910, 12912, 12912, 12913, 12913, 21441, 21441, 21509, 21509, 21511, 21511, 21512, 21512

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15634-15731
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15377, 15377, 15612, 15612, 15670, 15670, 15676, 15676, 15682, 15682, 15688, 15688, 15694, 15694, 15700, 15700, 15706, 15706, 15712, 15712, 15718, 15718, 15724, 15724, 15730, 15730, 15978, 17317, 17317, 17694, 17922, 17922, 17925, 17925, 18261, 18261, 21398, 21398, 21465, 21465, 21471, 21471, 21522, 21522, 21579, 21579
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8342-8438
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8398, 8398, 8434, 8434, 16492, 16492

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11415-11508
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11467, 11467, 11480, 11480, 21501, 21501, 21543, 21543, 21544, 21544, 21549, 21549, 21550, 21550

### `ValidationUtils` (class, 90 lines)

- Def site: line 5994-6083
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6076, 6076, 15440, 15440, 15441, 15441, 15655, 21301, 21301
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12758-12842
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12792, 12792, 21476, 21476, 21484, 21484, 21510, 21510, 21655, 21655

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 19691-19769
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19686, 19686, 19687, 19687, 21750, 21750
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17708-17785
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21621, 21621, 21625, 21625, 21629, 21629
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1866-1939
- References: 277
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1879, 1879, 1911, 1911, 2186, 2186, 2275, 2275, 2324, 2324, 7696, 7696, 7782, 7782, 7912, 7912, 7989, 7989, 8072, 8072, 8302, 8302, 8491, 8491, 8547, 8547, 8560, 8560, 8577, 8577, 8622, 8622, 8653, 8653, 8659, 8659, 8762, 8762, 10303, 10303, 10570, 11072, 11072, 11101, 11101, 11366, 11366, 11572, 11572, 11811, 11811, 12527, 12527, 12543, 12543, 13330, 13330, 13749, 13749, 13799, 13799, 15653, 15855, 15855, 15888, 15888, 15906, 15906, 15924, 15924, 15951, 15951, 15976, 17378, 17378, 17505, 17505, 17696, 17735, 17735, 17760, 17760, 17803, 17902, 17902, 18114, 18114, 18257, 18257, 19261, 19261, 19351, 19351, 19681, 19681, 19711, 19711, 19732, 19732, 19751, 19751, 19767, 19767, 19784, 19784, 20275, 20275, 20332, 20332, 20344, 20344, 20357, 20357, 20374, 20374, 20537, 20537, 21248, 21248, 21268, 21268, 21303, 21303, 21316, 21316, 21784, 21784, 21875, 21875, 21880, 21880, 21886, 21886, 21905, 21905, 21911, 21911, 23555, 23555, 23653, 23653
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

- Def site: line 15280-15351
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21587, 21587, 21588, 21588, 21589, 21589, 21590, 21590

### `DisplayUtils` (class, 70 lines)

- Def site: line 5485-5554
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5517, 5517, 5518, 5518, 5533, 5533, 5535, 5535, 5624, 5624, 18630, 18630, 18669, 18669, 18728, 18728

### `ConfigUtils` (class, 70 lines)

- Def site: line 6089-6158
- References: 199
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6131, 6131, 6136, 6136, 6233, 6233, 6291, 6291, 7182, 7182, 7839, 7839, 8484, 8484, 8507, 8507, 8527, 8527, 8712, 8712, 8733, 8733, 9008, 9008, 9033, 9033, 9088, 9088, 9110, 9110, 9127, 9127, 9144, 9144, 9529, 9529, 9752, 9752, 9769, 9769, 10161, 10161, 10493, 10493, 10704, 10704, 10741, 10741, 10894, 10894, 11037, 11037, 11290, 11290, 11478, 11478, 11662, 11662, 11981, 11981, 12317, 12317, 12489, 12489, 12529, 12529, 12535, 12535, 12629, 12629, 12859, 12859, 12932, 12932, 13419, 13419, 13454, 13653, 13653, 15160, 15160, 15376, 15376, 15644, 15751, 15851, 15851, 15886, 15886, 15904, 15904, 15922, 15922, 15957, 15957, 16491, 16491, 17298, 17298, 17691, 17801, 18309, 18309, 19262, 19262, 19267, 19267, 19269, 19269, 19682, 19682, 19684, 19684, 19708, 19708, 19712, 19712, 19713, 19713, 19733, 19733, 19734, 19734, 19996, 19996, 20782, 20782, 21352, 21352, 21384, 21384, 21421, 21421, 21427, 21427, 21555, 21555, 21612, 21612, 21695, 21695, 21704, 21704, 21782, 21782, 21783, 21783, 21800, 21800, 21875, 21875, 21880, 21880, 21886, 21886, 21905, 21905, 21911, 21911, 22846, 22846, 22917, 23419, 23419, 23507, 23507
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10539-10607
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10579, 10579, 10584, 10584, 10589, 10589, 10590, 10590, 10596, 10596, 10597, 10597, 10603, 10603, 10604, 10604, 10605, 10605, 10606, 10606, 21928, 21928

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 21307-21372
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21355, 21355, 21363, 21363, 21372, 21372, 21901, 21901

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15875-15930
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21526, 21526, 21530, 21530, 21735, 21735

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6164-6210
- References: 59
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6288, 6288, 8174, 8174, 9089, 9089, 9112, 9112, 9599, 9599, 9634, 9634, 9648, 9648, 9771, 9771, 9775, 9775, 10323, 10323, 12633, 12633, 13303, 13303, 13429, 13429, 13461, 13639, 13639, 13675, 13675, 15650, 18417, 18417, 19263, 19263, 19572, 19572, 19683, 19683, 19714, 19714, 19735, 19735, 21785, 21785, 21801, 21801, 23438, 23438
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5813-5858
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5255, 5255, 5297, 5297, 5342, 5342, 5448, 5448, 5463, 5463, 5803, 5803, 5804, 5804, 5848, 5848, 6314, 6314, 8008, 8008, 9299, 9299, 9610, 9610, 9626, 9626, 9955, 9955, 10836, 10836, 10855, 10855, 12824, 15243, 15243, 15646, 15889, 15889, 15907, 15907, 15925, 15925, 15952, 15952, 15979, 16401, 16401, 16441, 16441, 16442, 16442, 16443, 16443, 16487, 16487, 17319, 17319, 17326, 17326, 17695, 17727, 17727, 17751, 17751, 17755, 17755, 17775, 17775, 17802, 17877, 17877, 17911, 17911, 17932, 17932, 17964, 17964, 18026, 18026, 18065, 18065, 18215, 18215, 18260, 18260, 19264, 19264, 19835, 19835
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17791-17833
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17814, 17814, 17820, 17820, 17826, 17826, 17832, 17832, 21719, 21719, 21723, 21723, 21727, 21727, 21731, 21731

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11681-11720
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11718, 11718, 21925, 21925

### `TimeUtils` (class, 29 lines)

- Def site: line 1830-1858
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8962, 8962, 8963, 8963, 8992, 8992, 8993, 8993, 9009, 9009, 9010, 9010, 9888, 9888, 9889, 9889, 10193, 10193, 10194, 10194, 10241, 10241, 10242, 10242, 10797, 10797, 10799, 10799, 10817, 10817, 10819, 10819, 11707, 11707, 11708, 11708, 12368, 12368, 12369, 12369, 12474, 12474, 12475, 12475, 13457
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15604-15631
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15618, 15618, 15624, 15624, 15630, 15630, 21633, 21633, 21637, 21637
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15965-15990
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15985, 15985, 15990, 15990, 21641, 21641, 21646, 21646
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2094-2118
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2180, 2239, 19380, 23262

### `RoutingUtils` (class, 22 lines)

- Def site: line 13756-13777
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21407, 21407, 21411, 21411, 21415, 21415
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 18243-18264
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19266, 19266, 21554, 21554, 21611, 21611, 21694, 21694, 21703, 21703

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 19667-19688
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21764, 21764
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7646-7666
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6397, 10166, 15489, 15654
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 14002-14011
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14038, 14174, 14251, 14270, 14282, 14303, 14316, 14327, 14333, 14346, 14439, 14574, 14669

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 278-286
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

- Def site: line 305-313
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5571, 15312, 15329, 15345

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 290-297
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

- Def site: line 265-267
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13462, 13751, 19716, 19737, 20769, 20800, 20832, 21067, 21082
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 593-595
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1207, 1876, 1876, 1876, 1888, 1894, 6290, 6410, 7470, 7530, 9698, 9809, 10063, 10893, 13464, 15522, 15564, 15662, 17400, 17520, 21787
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 34, 78, 162
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 56
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 36, 212, 255
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 903, 905

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 1978-1980
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1978, 7480, 7487, 7488, 10074, 15511

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 1996-1998
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1996, 15658, 17308, 17308, 17699
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 713-1717
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1762

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
