# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 187 first-party files
- Definitions analyzed: 97
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=16, hot=80, skipped=1

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
| `ConstDefinitionsExporter` | class | 759 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgInventoryExporter` | class | 686 | 112 | hot |  | oversize_25_lines,missing_inline_comments |
| `OrgConfigMigrationManager` | class | 675 | 4 | hot |  | oversize_25_lines |
| `OrgExportUtils` | class | 653 | 128 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `BulkRadiusWLANConfigManager` | class | 587 | 13 | hot |  | oversize_25_lines |
| `menu_actions` | assignment | 572 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgTicketManager` | class | 463 | 66 | hot |  | oversize_25_lines |
| `OperationRegistry` | class | 461 | 9 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `PromptUtils` | class | 441 | 119 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 58 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 398 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `MSPInventoryExporter` | class | 388 | 5 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `DataExporter` | class | 345 | 257 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `APIDataFetcher` | class | 328 | 16 | hot |  | oversize_25_lines |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 111 | hot |  | oversize_25_lines |
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
| `DataProcessingUtils` | class | 158 | 201 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `DataCollectionManager` | class | 156 | 20 | hot |  | oversize_25_lines,missing_inline_comments |
| `SitesByAPModelExporter` | class | 146 | 22 | hot |  | oversize_25_lines |
| `SiteExportUtils` | class | 145 | 94 | hot |  | oversize_25_lines,missing_action_logging |
| `OrgTemplateExporter` | class | 144 | 18 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayHaExporter` | class | 139 | 18 | hot |  | oversize_25_lines |
| `OrgAlarmEventExporter` | class | 129 | 14 | hot |  | oversize_25_lines,missing_inline_comments |
| `WiredClientManufacturerReportGenerator` | class | 129 | 20 | hot |  | oversize_25_lines,non_ascii_logs |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `EnvironmentUtils` | class | 125 | 28 | hot |  | oversize_25_lines,hardcoded_separator |
| `OrgSiteExporter` | class | 112 | 53 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 109 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteConfigExporter` | class | 100 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `GatewayExportUtils` | class | 98 | 79 | hot |  | oversize_25_lines,missing_action_logging |
| `DeviceUtils` | class | 97 | 6 | hot |  | oversize_25_lines |
| `OrgAdminExporter` | class | 94 | 14 | hot |  | oversize_25_lines,hardcoded_separator |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteClientExporter` | class | 85 | 10 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 261 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 14 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 195 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 59 | hot |  | oversize_25_lines,missing_inline_comments |
| `InventoryCSVComparator` | class | 47 | 3 | low-use | InventoryCSVComparator | oversize_25_lines,missing_action_logging |
| `FilePathUtils` | class | 46 | 104 | hot |  | oversize_25_lines,missing_inline_comments |
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
| `marvis_data_utils` | assignment | 4 | 3 | low-use | MarvisDataUtils | missing_action_logging |
| `is_debug_mode` | function | 3 | 12 | hot |  | missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_BACKOFF_MULTIPLIER` | assignment | 3 | 3 | low-use | FastModeBackoffMultiplierManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_DEVICES_PER_THREAD` | assignment | 3 | 2 | low-use | FastModeDevicesPerThreadManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_SEQUENTIAL_MAX_RETRIES` | assignment | 3 | 2 | low-use | FastModeSequentialMaxRetriesManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 2 | low-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_WAN_TARGET_PORTS` | assignment | 3 | 3 | low-use | MistWanTargetPortsManager | missing_inline_comments,missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 12 | hot |  | missing_inline_comments,missing_action_logging |

## Low-Use (16)

### `FirmwareUpgradeStatusChecker` (class, 958 lines)

- Def site: line 17715-18672
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

### `InventoryCSVComparator` (class, 47 lines)

- Def site: line 16391-16437
- References: 3
- Suggested class: `InventoryCSVComparator`
- Suggested module: `src/refactors/inventory_csvcomparator.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `__init__()`; extract `InventoryCSVComparator` OUT of the entrypoint into a new `src/refactors/inventory_csvcomparator.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16430, 16430, 20118

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 18685-18716
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

- Def site: line 15856-15882
- References: 2
- Suggested class: `DeviceConfigTemplateClonerManager`
- Suggested module: `src/refactors/device_config_template_cloner_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `DeviceConfigTemplateClonerManager` OUT of the entrypoint into a new `src/refactors/device_config_template_cloner_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20499, 20499

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17125-17147
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20301, 20301

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 19217-19235
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

- Def site: line 2189-2206
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2249, 18820, 21767

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2815-2832
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21772, 21835

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 366-378
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 366, 550

### `main` (function, 12 lines)

- Def site: line 22163-22174
- References: 2
- Suggested class: `MainManager`
- Suggested module: `src/refactors/main.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `main` OUT of the entrypoint into a new `src/refactors/main.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22277
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6536-6539
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6536, 15678
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1981-1983
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1981, 9922, 15351

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1984-1986
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1984, 7412

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1989-1991
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1989, 15491

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 1996-1998
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1996, 7402

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2004-2006
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2004, 15580
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2877-5203
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2877, 6582, 6583, 6592, 6756

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13937-14695
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14414, 14414, 14426, 14426, 14454, 14454, 14466, 14466, 14527, 14527, 14564, 14564, 14721, 20216

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9083-9768
- References: 112
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5589, 5589, 9206, 9206, 9257, 9257, 9260, 9260, 9301, 9301, 9340, 9340, 9358, 9358, 9436, 9436, 9443, 9443, 9453, 9453, 9456, 9456, 9469, 9469, 9470, 9470, 9471, 9471, 9472, 9472, 9480, 9480, 9482, 9482, 9483, 9483, 9484, 9484, 9485, 9485, 9488, 9488, 9491, 9491, 9494, 9494, 9497, 9497, 9543, 9543, 9566, 9566, 9567, 9567, 9568, 9568, 9570, 9570, 9606, 9606, 9622, 9622, 9676, 9676, 9677, 9677, 9678, 9678, 9681, 9681, 9682, 9682, 9701, 9701, 9703, 9703, 9704, 9704, 9739, 9739, 15090, 15090, 15143, 15143, 15574, 16413, 16413, 17174, 17174, 17198, 17198, 17222, 17222, 17365, 17365, 19991, 19991, 19998, 19998, 20007, 20007, 20011, 20011, 20020, 20020
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16443-17117
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16831, 16831, 20462, 20468

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11816-12468
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10593, 10593, 10602, 10602, 10690, 10690, 10697, 10697, 11371, 11371, 11657, 11657, 11662, 11662, 11669, 11669, 11674, 11674, 11888, 11888, 11910, 11910, 11913, 11913, 11939, 11939, 11948, 11948, 11949, 11949, 11970, 11970, 12013, 12013, 12059, 12059, 12070, 12070, 12097, 12097, 12102, 12102, 12103, 12103, 12104, 12104, 12136, 12136, 12142, 12142, 12167, 12167, 12187, 12187, 12222, 12222, 12237, 12237, 12243, 12243, 12245, 12245, 12248, 12248, 12250, 12250, 12254, 12254, 12258, 12258, 12263, 12263, 12270, 12270, 12277, 12277, 12284, 12284, 12293, 12293, 12303, 12303, 12310, 12310, 12317, 12317, 12324, 12324, 12331, 12331, 12338, 12338, 12348, 12348, 12357, 12357, 12366, 12366, 12375, 12375, 12384, 12384, 12413, 12413, 19952, 19952, 20133, 20133, 20210, 20210, 20211, 20211, 20219, 20219, 20424, 20424, 20425, 20425, 20444, 20444, 20451, 20451, 20452, 20452, 20453, 20453, 20454, 20454

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 19248-19834
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19525, 19525, 19526, 19526, 19529, 19529, 19531, 19531, 19533, 19533, 19549, 19549, 20369

### `menu_actions` (assignment, 572 lines)

- Def site: line 19933-20504
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19933, 21218, 21219, 21228, 21348, 21348, 21390, 21448, 21493, 21984, 21988, 22033, 22033, 22060, 22060, 22063
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8367-8829
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8408, 8408, 8413, 8413, 8423, 8423, 8431, 8431, 8436, 8436, 8441, 8441, 8451, 8451, 8456, 8456, 8461, 8461, 8481, 8481, 8491, 8491, 8492, 8492, 8495, 8495, 8525, 8525, 8611, 8611, 8613, 8613, 8637, 8637, 8643, 8643, 8648, 8648, 8657, 8657, 8661, 8661, 8680, 8680, 8683, 8683, 8694, 8694, 8695, 8695, 8790, 8790, 8811, 8811, 20492, 20492, 20493, 20493, 20494, 20494, 20495, 20495, 20496, 20496, 20497, 20497

### `OperationRegistry` (class, 461 lines)

- Def site: line 20729-21189
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21196, 21196, 21200, 21200, 21220, 21220, 21225, 21225, 21449

### `PromptUtils` (class, 441 lines)

- Def site: line 7814-8254
- References: 119
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7759, 7759, 7775, 7775, 7779, 7779, 7780, 7780, 7781, 7781, 7796, 7796, 7802, 7802, 7829, 7829, 7832, 7832, 7840, 7840, 7858, 7858, 7908, 7908, 7916, 7916, 7921, 7921, 7967, 7967, 7978, 7978, 8003, 8003, 8022, 8022, 8023, 8023, 8026, 8026, 8027, 8027, 8117, 8117, 8119, 8119, 8123, 8123, 8151, 8151, 8152, 8152, 8153, 8153, 8154, 8154, 8155, 8155, 8164, 8164, 8208, 8208, 8232, 8232, 12548, 12548, 12598, 12598, 12603, 12603, 12746, 12829, 12829, 12883, 12883, 12904, 12904, 12909, 12909, 13173, 13173, 13376, 13578, 13578, 13665, 13665, 13670, 13670, 13720, 13720, 13721, 13721, 15217, 15217, 15676, 17181, 17181, 17703, 17703, 17804, 17804, 19857, 19857, 19858, 19858, 20144, 20144
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9771-10184
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5583, 5583, 9804, 9804, 9888, 9888, 9894, 9894, 9897, 9897, 9941, 9941, 9955, 9955, 9982, 9982, 9988, 9988, 10002, 10002, 10085, 10085, 10087, 10087, 10091, 10091, 10093, 10093, 10096, 10096, 10100, 10100, 10103, 10103, 10113, 10113, 10119, 10119, 10157, 10157, 15091, 15091, 15092, 15092, 15093, 15093, 15144, 15144, 15145, 15145, 19992, 19992, 19993, 19993, 19994, 19994, 20018, 20018

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17284-17681
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17305, 17305, 17310, 17310, 17314, 17314, 17317, 17317, 17324, 17324, 17326, 17326, 17327, 17327, 17330, 17330, 17333, 17333, 17336, 17336, 17378, 17378, 17410, 17410, 17477, 17477, 17490, 17490, 17495, 17495, 17547, 17547, 17580, 17580, 17581, 17581, 17582, 17582, 17612, 17612, 17641, 17641, 17642, 17642, 20175, 20175

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 18722-19109
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18749, 18893, 18893, 20315, 20315

### `DataExporter` (class, 345 lines)

- Def site: line 6723-7067
- References: 257
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5679, 5679, 6769, 6769, 6785, 6785, 6786, 6786, 6809, 6809, 6811, 6811, 6814, 6814, 6828, 6828, 6830, 6830, 6839, 6839, 6841, 6841, 6842, 6842, 6848, 6848, 6849, 6849, 6849, 6866, 6866, 6870, 6870, 6912, 6912, 6943, 6943, 6946, 6946, 6948, 6948, 6994, 6994, 7004, 7004, 7037, 7037, 7042, 7042, 7049, 7049, 7271, 7271, 7303, 7303, 7314, 7314, 7339, 7339, 7359, 7359, 7871, 7871, 8664, 8664, 8943, 8943, 8958, 9022, 9022, 9039, 9039, 9057, 9057, 9078, 9078, 9637, 9637, 9712, 9712, 10042, 10042, 10393, 10393, 10478, 10494, 10614, 10614, 10618, 10618, 10638, 10638, 10651, 10651, 10655, 10655, 10673, 10673, 10835, 10835, 11182, 11182, 11329, 11329, 11406, 11406, 11410, 11410, 11415, 11415, 11548, 11548, 11567, 11567, 11618, 11618, 11621, 11621, 11772, 11772, 11775, 11775, 11874, 11874, 11880, 11880, 12177, 12177, 12194, 12194, 12209, 12209, 12423, 12423, 12451, 12451, 12467, 12467, 12504, 12504, 12542, 12542, 12631, 12631, 12660, 12660, 12698, 12698, 12749, 12814, 12814, 12820, 12820, 12862, 12862, 13031, 13031, 13037, 13037, 13156, 13156, 13164, 13164, 13328, 13328, 13379, 13552, 13552, 13723, 13723, 14236, 14236, 14597, 14597, 14603, 14603, 15511, 15511, 15570, 15677, 15813, 15813, 15831, 15831, 15849, 15849, 15876, 15876, 15877, 15877, 17142, 17228, 17228, 17249, 18557, 18557, 19075, 19075, 19160, 19160, 19181, 19181, 19683, 19683, 20344, 20344, 20360, 20360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12870-13210
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12887, 12887, 12889, 12889, 12893, 12893, 12894, 12894, 12908, 12908, 12914, 12914, 12917, 12917, 12920, 12920, 12978, 12978, 12984, 12984, 12989, 12989, 13003, 13003, 13021, 13021, 13131, 13131, 13135, 13135, 13137, 13137, 13140, 13140, 13177, 13177, 13182, 13182, 13196, 13196, 13200, 13200, 13202, 13202, 13205, 13205, 13210, 13210, 20221, 20221, 20225, 20225, 20229, 20229

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7070-7397
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7172, 7172, 8388, 8869, 8888, 8989, 9118, 9141, 9813, 10121, 10166, 10580, 11350, 11361, 11424, 11841

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14701-15028
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12158, 12158, 12217, 12217, 12218, 12218, 13382, 14742, 14742, 14744, 14744, 14750, 14750, 14764, 14764, 14803, 14803, 14806, 14806, 14808, 14808, 14809, 14809, 14810, 14810, 14864, 14864, 14865, 14865, 14876, 14876, 14885, 14885, 14904, 14904, 14956, 14956, 14960, 14960, 14968, 14968, 14969, 14969, 14993, 14993, 14997, 14997
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16085-16373
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16113, 16113, 16116, 16116, 16121, 16121, 16124, 16124, 16168, 16168, 16174, 16174, 16205, 16205, 16208, 16208, 16212, 16212, 16238, 16238, 16255, 16255, 16261, 16261, 16275, 16275, 16276, 16276, 16278, 16278, 16284, 16284, 16291, 16291, 16300, 16300, 16347, 16347, 16369, 16369, 16370, 16370, 16371, 16371, 20166, 20166

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10187-10459
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10210, 10210, 10211, 10211, 10224, 10224, 10225, 10225, 10227, 10227, 10228, 10228, 10231, 10231, 10234, 10234, 10238, 10238, 10239, 10239, 10315, 10315, 10319, 10319, 10322, 10322, 10335, 10335, 10372, 10372, 10389, 10389, 10402, 10402, 10404, 10404, 10411, 10411, 10420, 10420, 10429, 10429, 10430, 10430, 10441, 10441, 10445, 10445, 10454, 10454, 10459, 10459, 20423, 20423

### `CacheUtils` (class, 264 lines)

- Def site: line 5209-5472
- References: 111
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5249, 5249, 5251, 5251, 5333, 5333, 5339, 5339, 5376, 5376, 5378, 5378, 5387, 5387, 5397, 5397, 5407, 5407, 5443, 5443, 7907, 7907, 9565, 9565, 9566, 9566, 9877, 9877, 10723, 10723, 10743, 10743, 12744, 15150, 15150, 15156, 15156, 15157, 15157, 15158, 15158, 15159, 15159, 15160, 15160, 15161, 15161, 15168, 15168, 15196, 15196, 15568, 15814, 15814, 15832, 15832, 15850, 15850, 15900, 16411, 16411, 16412, 16412, 17137, 17173, 17173, 17197, 17197, 17221, 17221, 17365, 17365, 17366, 17366, 17367, 17367, 17368, 17368, 17704, 17704, 19908, 19908, 20460, 20460
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10954-11204
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10961, 10961, 10964, 10964, 10969, 10969, 10970, 10970, 10978, 10978, 10981, 10981, 10989, 10989, 11029, 11029, 11037, 11037, 11085, 11085, 11102, 11102, 11105, 11105, 11107, 11107, 11171, 11171, 11172, 11172, 20426, 20426

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15280-15524
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15146, 15146, 15306, 15306, 15308, 15308, 15309, 15309, 15310, 15310, 15338, 15338, 15343, 15343, 15365, 15365, 15366, 15366, 15408, 15408, 15416, 15416, 15442, 15442, 15451, 15451, 15459, 15459, 15490, 15490, 19997, 19997, 20001, 20001

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6142-6362
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6165, 6165, 6216, 6216, 6286, 6286, 6310, 6310, 6322, 6322, 6324, 6324, 6334, 6334, 6349, 6349, 6353, 6353, 6354, 6354, 6357, 6357, 6359, 6359, 12857, 12857, 15572
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 20510-20723
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21366, 21366, 21369, 21450, 21801

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7598-7807
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7611, 7611, 7617, 7617, 7618, 7618, 7621, 7621, 7644, 7644, 7647, 7647, 7650, 7650, 7651, 7651, 7653, 7653, 7720, 7720, 7764, 7764, 8229, 8229, 13178, 13178, 15675, 15938, 15938, 16098, 16098

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12476-12678
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12497, 12497, 12506, 12506, 12568, 12568, 12575, 12575, 12607, 12607, 12609, 12609, 12633, 12633, 12668, 12668, 12675, 12675, 12706, 12706, 15220, 15220, 20033, 20033, 20035, 20035, 20036, 20036, 20038, 20038

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13729-13916
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20383, 20383, 20384, 20384, 20385, 20385, 20386, 20386, 20387, 20387, 20388, 20388, 20389, 20389, 20390, 20390, 20392, 20392, 20393, 20393, 20394, 20394, 20395, 20395, 20396, 20396, 20397, 20397, 20398, 20398, 20400, 20400, 20401, 20401, 20402, 20402, 20403, 20403, 20404, 20404, 20405, 20405, 20406, 20406, 20407, 20407, 20408, 20408, 20410, 20410, 20411, 20411, 20412, 20412, 20413, 20413, 20414, 20414, 20415, 20415, 20416, 20416, 20417, 20417, 20418, 20418, 20420, 20420, 20421, 20421

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5554-5733
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5642, 5642, 5679, 5679, 5681, 5681, 5684, 5684, 5692, 5692, 5694, 5694, 5696, 5696, 5699, 5699, 5728, 5728, 5731, 5731, 20160, 20160

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6542-6720
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6587, 6587, 6625, 6625, 6636, 6636, 6662, 6662, 6663, 6663, 6665, 6665, 6671, 6671, 6672, 6672, 6675, 6675, 6681, 6681, 6682, 6682, 6685, 6685, 6687, 6687, 6697, 6697, 6699, 6699, 6700, 6700, 6702, 6702

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11434-11601
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11541, 11541, 11560, 11560, 11578, 11578, 11587, 11587, 11590, 11590, 11591, 11591, 11594, 11594, 11599, 11599, 11601, 11601, 20061, 20061

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11646-11813
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11683, 11683, 11685, 11685, 11688, 11688, 11759, 11759, 11761, 11761, 11774, 11774, 11778, 11778, 20064, 20064, 20065, 20065, 20066, 20066, 20104, 20104, 20109, 20109

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10679-10840
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10717, 10717, 10724, 10724, 10731, 10731, 10737, 10737, 10744, 10744, 10751, 10751, 10812, 10812, 10823, 10823, 20052, 20052, 20053, 20053, 20055, 20055, 20056, 20056, 20057, 20057

### `CLIShellManager` (class, 161 lines)

- Def site: line 15919-16079
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15942, 15942, 15944, 15944, 16013, 16013, 16015, 16015, 16034, 16034, 16036, 16036, 16036, 16052, 16052, 16068, 16068, 16069, 16069, 16075, 16075, 20165, 20165

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6370-6527
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5507, 5507, 6386, 6386, 6399, 6399, 6402, 6402, 6426, 6426, 6434, 6434, 6435, 6435, 6457, 6457, 6462, 6462, 6464, 6464, 6537, 6537, 6538, 6538, 6945, 6945, 6970, 6970, 7039, 7039, 7040, 7040, 7369, 7369, 7383, 7383, 7384, 7384, 7869, 7869, 7870, 7870, 8792, 8792, 8957, 9017, 9017, 9019, 9019, 9020, 9020, 9037, 9037, 9038, 9038, 9055, 9055, 9056, 9056, 9076, 9076, 9077, 9077, 9634, 9634, 9635, 9635, 9709, 9709, 9710, 9710, 10038, 10038, 10041, 10041, 10616, 10616, 10617, 10617, 10653, 10653, 10654, 10654, 10833, 10833, 10834, 10834, 11178, 11178, 11179, 11179, 11325, 11325, 11326, 11326, 11408, 11408, 11409, 11409, 11620, 11620, 11795, 11795, 11796, 11796, 11872, 11872, 11873, 11873, 12176, 12176, 12192, 12192, 12193, 12193, 12421, 12421, 12422, 12422, 12501, 12501, 12502, 12502, 12503, 12503, 12539, 12539, 12540, 12540, 12628, 12628, 12629, 12629, 12657, 12657, 12658, 12658, 12695, 12695, 12696, 12696, 12748, 12817, 12817, 12818, 12818, 12860, 12860, 12861, 12861, 13029, 13029, 13030, 13030, 13154, 13154, 13155, 13155, 13378, 13550, 13550, 14602, 14602, 15509, 15509, 15510, 15510, 15571, 15679, 17226, 17226, 17227, 17227, 19065, 19065
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15042-15197
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15064, 15064, 15070, 15070, 15072, 15072, 15100, 15100, 15126, 15126, 15129, 15129, 15132, 15132, 20151, 20151, 20155, 20155, 20163, 20163

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13213-13358
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13252, 13252, 13259, 13259, 13284, 13284, 13287, 13287, 13300, 13300, 13344, 13344, 13348, 13348, 13353, 13353, 13354, 13354, 13358, 13358, 20458, 20458

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13366-13510
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12587, 12587, 12763, 12763, 12841, 12841, 12846, 12846, 13395, 13395, 13401, 13401, 13407, 13407, 13413, 13413, 13419, 13419, 13425, 13425, 13431, 13431, 13437, 13437, 13443, 13443, 13449, 13449, 13455, 13455, 13461, 13461, 13467, 13467, 13473, 13473, 13479, 13479, 13485, 13485, 13491, 13491, 13497, 13497, 13503, 13503, 13509, 13509, 20071, 20071, 20212, 20212, 20214, 20214, 20329, 20329, 20455, 20455, 20456, 20456, 20457, 20457, 20476, 20476, 20477, 20477, 20478, 20478, 20479, 20479, 20480, 20480, 20481, 20481, 20482, 20482
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10533-10676
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10547, 10547, 10548, 10548, 10634, 10634, 10669, 10669, 20046, 20046, 20047, 20047, 20048, 20048, 20049, 20049, 20050, 20050

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13513-13651
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13582, 13582, 13585, 13585, 13586, 13586, 13587, 13587, 13607, 13607, 13610, 13610, 13618, 13618, 13623, 13623, 20484, 20484

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8835-8963
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8906, 8906, 8917, 8917, 15140, 15140, 15141, 15141, 19949, 19949, 19950, 19950, 20129, 20129

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11207-11335
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11214, 11214, 11219, 11219, 11220, 11220, 11221, 11221, 11224, 11224, 11225, 11225, 11288, 11288, 11295, 11295, 11322, 11322, 20428, 20428

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15665-15791
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15685, 15685, 15690, 15690, 15695, 15695, 15732, 15732, 15738, 15738, 15744, 15744, 15750, 15750, 15756, 15756, 15757, 15757, 15758, 15758, 15759, 15759, 15760, 15760, 15764, 15764, 15773, 15773, 15777, 15777, 15780, 15780, 15786, 15786, 20124, 20124

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5787-5911
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5808, 5808, 5810, 5810, 5826, 5826, 5838, 5838, 5877, 5877, 5878, 5878, 5879, 5879, 5880, 5880, 5881, 5881, 5892, 5892, 5895, 5895, 6827, 6827, 21463, 21463, 22046, 22046

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8969-9080
- References: 53
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7907, 7907, 9565, 9565, 9877, 9877, 10723, 10723, 10743, 10743, 12745, 15089, 15089, 15142, 15142, 15575, 15815, 15815, 15833, 15833, 15851, 15851, 17138, 17175, 17175, 17199, 17199, 17223, 17223, 17366, 17366, 17707, 17707, 19990, 19990, 20005, 20005, 20015, 20015, 20015, 20015, 20025, 20025
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10843-10951
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10898, 10898, 10901, 10901, 10902, 10902, 10907, 10907, 10925, 10925, 10925, 10934, 10934, 10934, 10934, 10935, 10935, 10935, 10935, 10993, 10993, 10996, 10996, 11008, 11008, 11009, 11009, 11022, 11022, 11061, 11061, 11069, 11069, 11123, 11123, 11131, 11131

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12768-12867
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12833, 12833, 12835, 12835, 12836, 12836, 19999, 19999, 20067, 20067, 20069, 20069, 20070, 20070

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15557-15654
- References: 79
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15300, 15300, 15535, 15535, 15593, 15593, 15599, 15599, 15605, 15605, 15611, 15611, 15617, 15617, 15623, 15623, 15629, 15629, 15635, 15635, 15641, 15641, 15647, 15647, 15653, 15653, 15901, 17139, 17367, 17367, 17370, 17370, 17706, 17706, 19956, 19956, 20023, 20023, 20029, 20029, 20080, 20080, 20137, 20137
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8265-8361
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8321, 8321, 8357, 8357, 16415, 16415

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11338-11431
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11390, 11390, 11403, 11403, 20059, 20059, 20101, 20101, 20102, 20102, 20107, 20107, 20108, 20108

### `ValidationUtils` (class, 90 lines)

- Def site: line 5917-6006
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5999, 5999, 15363, 15363, 15364, 15364, 15578, 19859, 19859
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12681-12765
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12715, 12715, 20034, 20034, 20042, 20042, 20068, 20068, 20213, 20213

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 19136-19214
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19131, 19131, 19132, 19132, 20308, 20308
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17153-17230
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20179, 20179, 20183, 20183, 20187, 20187
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1881-1954
- References: 261
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1894, 1894, 1926, 1926, 2201, 2201, 2290, 2290, 2317, 2317, 7619, 7619, 7705, 7705, 7835, 7835, 7912, 7912, 7995, 7995, 8225, 8225, 8414, 8414, 8470, 8470, 8483, 8483, 8500, 8500, 8545, 8545, 8576, 8576, 8582, 8582, 8685, 8685, 10226, 10226, 10493, 10995, 10995, 11024, 11024, 11289, 11289, 11495, 11495, 11734, 11734, 12450, 12450, 12466, 12466, 13253, 13253, 13672, 13672, 13722, 13722, 15576, 15778, 15778, 15811, 15811, 15829, 15829, 15847, 15847, 15874, 15874, 15899, 17141, 17180, 17180, 17205, 17205, 17248, 17347, 17347, 17559, 17559, 17702, 17702, 18706, 18706, 18796, 18796, 19126, 19126, 19156, 19156, 19177, 19177, 19196, 19196, 19212, 19212, 19229, 19229, 19806, 19806, 19826, 19826, 19861, 19861, 19874, 19874, 20342, 20342, 20433, 20433, 20438, 20438, 20444, 20444, 20463, 20463, 20469, 20469, 22069, 22069, 22167, 22167
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

- Def site: line 15203-15274
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20145, 20145, 20146, 20146, 20147, 20147, 20148, 20148

### `DisplayUtils` (class, 70 lines)

- Def site: line 5478-5547
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5510, 5510, 5511, 5511, 5526, 5526, 5528, 5528, 18075, 18075, 18114, 18114, 18173, 18173

### `ConfigUtils` (class, 70 lines)

- Def site: line 6012-6081
- References: 195
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6054, 6054, 6059, 6059, 6156, 6156, 6214, 6214, 7105, 7105, 7762, 7762, 8407, 8407, 8430, 8430, 8450, 8450, 8635, 8635, 8656, 8656, 8931, 8931, 8956, 8956, 9011, 9011, 9033, 9033, 9050, 9050, 9067, 9067, 9452, 9452, 9675, 9675, 9692, 9692, 10084, 10084, 10416, 10416, 10627, 10627, 10664, 10664, 10817, 10817, 10960, 10960, 11213, 11213, 11401, 11401, 11585, 11585, 11904, 11904, 12240, 12240, 12412, 12412, 12452, 12452, 12458, 12458, 12552, 12552, 12782, 12782, 12855, 12855, 13342, 13342, 13377, 13576, 13576, 15083, 15083, 15299, 15299, 15567, 15674, 15774, 15774, 15809, 15809, 15827, 15827, 15845, 15845, 15880, 15880, 16414, 16414, 17136, 17246, 17754, 17754, 18707, 18707, 18712, 18712, 18714, 18714, 19127, 19127, 19129, 19129, 19153, 19153, 19157, 19157, 19158, 19158, 19178, 19178, 19179, 19179, 19340, 19340, 19910, 19910, 19942, 19942, 19979, 19979, 19985, 19985, 20113, 20113, 20170, 20170, 20253, 20253, 20262, 20262, 20340, 20340, 20341, 20341, 20358, 20358, 20433, 20433, 20438, 20438, 20444, 20444, 20463, 20463, 20469, 20469, 21380, 21380, 21451, 21933, 21933, 22021, 22021
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10462-10530
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10502, 10502, 10507, 10507, 10512, 10512, 10513, 10513, 10519, 10519, 10520, 10520, 10526, 10526, 10527, 10527, 10528, 10528, 10529, 10529, 20486, 20486

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 19865-19930
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19913, 19913, 19921, 19921, 19930, 19930, 20459, 20459

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15798-15853
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20084, 20084, 20088, 20088, 20293, 20293

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6087-6133
- References: 59
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6211, 6211, 8097, 8097, 9012, 9012, 9035, 9035, 9522, 9522, 9557, 9557, 9571, 9571, 9694, 9694, 9698, 9698, 10246, 10246, 12556, 12556, 13226, 13226, 13352, 13352, 13384, 13562, 13562, 13598, 13598, 15573, 17862, 17862, 18708, 18708, 19017, 19017, 19128, 19128, 19159, 19159, 19180, 19180, 20343, 20343, 20359, 20359, 21952, 21952
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5736-5781
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5248, 5248, 5290, 5290, 5335, 5335, 5441, 5441, 5456, 5456, 5726, 5726, 5727, 5727, 5771, 5771, 6237, 6237, 7931, 7931, 9222, 9222, 9533, 9533, 9549, 9549, 9878, 9878, 10759, 10759, 10778, 10778, 12747, 15166, 15166, 15569, 15812, 15812, 15830, 15830, 15848, 15848, 15875, 15875, 15902, 16324, 16324, 16364, 16364, 16365, 16365, 16366, 16366, 16410, 16410, 17140, 17172, 17172, 17196, 17196, 17200, 17200, 17220, 17220, 17247, 17322, 17322, 17356, 17356, 17377, 17377, 17409, 17409, 17471, 17471, 17510, 17510, 17660, 17660, 17705, 17705, 18709, 18709
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17236-17278
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17259, 17259, 17265, 17265, 17271, 17271, 17277, 17277, 20277, 20277, 20281, 20281, 20285, 20285, 20289, 20289

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11604-11643
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11641, 11641, 20483, 20483

### `TimeUtils` (class, 29 lines)

- Def site: line 1845-1873
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8885, 8885, 8886, 8886, 8915, 8915, 8916, 8916, 8932, 8932, 8933, 8933, 9811, 9811, 9812, 9812, 10116, 10116, 10117, 10117, 10164, 10164, 10165, 10165, 10720, 10720, 10722, 10722, 10740, 10740, 10742, 10742, 11630, 11630, 11631, 11631, 12291, 12291, 12292, 12292, 12397, 12397, 12398, 12398, 13380
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15527-15554
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15541, 15541, 15547, 15547, 15553, 15553, 20191, 20191, 20195, 20195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15888-15913
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15908, 15908, 15913, 15913, 20199, 20199, 20204, 20204
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2109-2133
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2195, 2254, 18825, 21776

### `RoutingUtils` (class, 22 lines)

- Def site: line 13679-13700
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19965, 19965, 19969, 19969, 19973, 19973
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17688-17709
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18711, 18711, 20112, 20112, 20169, 20169, 20252, 20252, 20261, 20261

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 19112-19133
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20322, 20322
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7569-7589
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6320, 10089, 15412, 15577
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13925-13934
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13961, 14097, 14174, 14193, 14205, 14226, 14239, 14250, 14256, 14269, 14362, 14497, 14592

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 297-305
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

- Def site: line 324-332
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15235, 15252, 15268
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 309-316
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

- Def site: line 284-286
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13385, 13674, 19161, 19182, 19327, 19358, 19390, 19625, 19640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 612-614
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1222, 1891, 1891, 1891, 1903, 1909, 6213, 6333, 7393, 7453, 9621, 9732, 9986, 10816, 13387, 15445, 15487, 15585, 20345
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 34, 78, 162
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 56
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 36, 212, 255
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\wanprobe_config_manager.py`: lines 243, 363
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 903, 905

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 1993-1995
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1993, 7403, 7410, 7411, 9997, 15434

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2011-2013
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2011, 15581, 17144
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 728-1732
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1777

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
