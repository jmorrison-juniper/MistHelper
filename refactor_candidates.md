# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 188 first-party files
- Definitions analyzed: 96
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=15, hot=80, skipped=1

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
| `OrgInventoryExporter` | class | 686 | 110 | hot |  | oversize_25_lines,missing_inline_comments |
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
| `CacheUtils` | class | 264 | 107 | hot |  | oversize_25_lines |
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
| `DeviceUtils` | class | 97 | 4 | hot |  | oversize_25_lines |
| `OrgAdminExporter` | class | 94 | 14 | hot |  | oversize_25_lines,hardcoded_separator |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteClientExporter` | class | 85 | 10 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 261 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 14 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 193 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 59 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 102 | hot |  | oversize_25_lines,missing_inline_comments |
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

## Low-Use (15)

### `FirmwareUpgradeStatusChecker` (class, 958 lines)

- Def site: line 17664-18621
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

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 18634-18665
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

- Def site: line 15859-15885
- References: 2
- Suggested class: `DeviceConfigTemplateClonerManager`
- Suggested module: `src/refactors/device_config_template_cloner_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `DeviceConfigTemplateClonerManager` OUT of the entrypoint into a new `src/refactors/device_config_template_cloner_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20448, 20448

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17074-17096
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20250, 20250

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 19166-19184
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

- Def site: line 2192-2209
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2252, 18769, 21716

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2818-2835
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21721, 21784

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 369-381
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 369, 553

### `main` (function, 12 lines)

- Def site: line 22112-22123
- References: 2
- Suggested class: `MainManager`
- Suggested module: `src/refactors/main.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `main` OUT of the entrypoint into a new `src/refactors/main.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 22226
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6539-6542
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6539, 15681
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1984-1986
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1984, 9925, 15354

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1987-1989
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1987, 7415

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1992-1994
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1992, 15494

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 1999-2001
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1999, 7405

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2007-2009
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2007, 15583
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2880-5206
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2880, 6585, 6586, 6595, 6759

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13940-14698
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14417, 14417, 14429, 14429, 14457, 14457, 14469, 14469, 14530, 14530, 14567, 14567, 14724, 20165

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9086-9771
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5592, 5592, 9209, 9209, 9260, 9260, 9263, 9263, 9304, 9304, 9343, 9343, 9361, 9361, 9439, 9439, 9446, 9446, 9456, 9456, 9459, 9459, 9472, 9472, 9473, 9473, 9474, 9474, 9475, 9475, 9483, 9483, 9485, 9485, 9486, 9486, 9487, 9487, 9488, 9488, 9491, 9491, 9494, 9494, 9497, 9497, 9500, 9500, 9546, 9546, 9569, 9569, 9570, 9570, 9571, 9571, 9573, 9573, 9609, 9609, 9625, 9625, 9679, 9679, 9680, 9680, 9681, 9681, 9684, 9684, 9685, 9685, 9704, 9704, 9706, 9706, 9707, 9707, 9742, 9742, 15093, 15093, 15146, 15146, 15577, 17123, 17123, 17147, 17147, 17171, 17171, 17314, 17314, 19940, 19940, 19947, 19947, 19956, 19956, 19960, 19960, 19969, 19969
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16392-17066
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16780, 16780, 20411, 20417

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11819-12471
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10596, 10596, 10605, 10605, 10693, 10693, 10700, 10700, 11374, 11374, 11660, 11660, 11665, 11665, 11672, 11672, 11677, 11677, 11891, 11891, 11913, 11913, 11916, 11916, 11942, 11942, 11951, 11951, 11952, 11952, 11973, 11973, 12016, 12016, 12062, 12062, 12073, 12073, 12100, 12100, 12105, 12105, 12106, 12106, 12107, 12107, 12139, 12139, 12145, 12145, 12170, 12170, 12190, 12190, 12225, 12225, 12240, 12240, 12246, 12246, 12248, 12248, 12251, 12251, 12253, 12253, 12257, 12257, 12261, 12261, 12266, 12266, 12273, 12273, 12280, 12280, 12287, 12287, 12296, 12296, 12306, 12306, 12313, 12313, 12320, 12320, 12327, 12327, 12334, 12334, 12341, 12341, 12351, 12351, 12360, 12360, 12369, 12369, 12378, 12378, 12387, 12387, 12416, 12416, 19901, 19901, 20082, 20082, 20159, 20159, 20160, 20160, 20168, 20168, 20373, 20373, 20374, 20374, 20393, 20393, 20400, 20400, 20401, 20401, 20402, 20402, 20403, 20403

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 19197-19783
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19474, 19474, 19475, 19475, 19478, 19478, 19480, 19480, 19482, 19482, 19498, 19498, 20318

### `menu_actions` (assignment, 572 lines)

- Def site: line 19882-20453
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19882, 21167, 21168, 21177, 21297, 21297, 21339, 21397, 21442, 21933, 21937, 21982, 21982, 22009, 22009, 22012
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8370-8832
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8411, 8411, 8416, 8416, 8426, 8426, 8434, 8434, 8439, 8439, 8444, 8444, 8454, 8454, 8459, 8459, 8464, 8464, 8484, 8484, 8494, 8494, 8495, 8495, 8498, 8498, 8528, 8528, 8614, 8614, 8616, 8616, 8640, 8640, 8646, 8646, 8651, 8651, 8660, 8660, 8664, 8664, 8683, 8683, 8686, 8686, 8697, 8697, 8698, 8698, 8793, 8793, 8814, 8814, 20441, 20441, 20442, 20442, 20443, 20443, 20444, 20444, 20445, 20445, 20446, 20446

### `OperationRegistry` (class, 461 lines)

- Def site: line 20678-21138
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21145, 21145, 21149, 21149, 21169, 21169, 21174, 21174, 21398

### `PromptUtils` (class, 441 lines)

- Def site: line 7817-8257
- References: 119
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7762, 7762, 7778, 7778, 7782, 7782, 7783, 7783, 7784, 7784, 7799, 7799, 7805, 7805, 7832, 7832, 7835, 7835, 7843, 7843, 7861, 7861, 7911, 7911, 7919, 7919, 7924, 7924, 7970, 7970, 7981, 7981, 8006, 8006, 8025, 8025, 8026, 8026, 8029, 8029, 8030, 8030, 8120, 8120, 8122, 8122, 8126, 8126, 8154, 8154, 8155, 8155, 8156, 8156, 8157, 8157, 8158, 8158, 8167, 8167, 8211, 8211, 8235, 8235, 12551, 12551, 12601, 12601, 12606, 12606, 12749, 12832, 12832, 12886, 12886, 12907, 12907, 12912, 12912, 13176, 13176, 13379, 13581, 13581, 13668, 13668, 13673, 13673, 13723, 13723, 13724, 13724, 15220, 15220, 15679, 17130, 17130, 17652, 17652, 17753, 17753, 19806, 19806, 19807, 19807, 20093, 20093
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9774-10187
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5586, 5586, 9807, 9807, 9891, 9891, 9897, 9897, 9900, 9900, 9944, 9944, 9958, 9958, 9985, 9985, 9991, 9991, 10005, 10005, 10088, 10088, 10090, 10090, 10094, 10094, 10096, 10096, 10099, 10099, 10103, 10103, 10106, 10106, 10116, 10116, 10122, 10122, 10160, 10160, 15094, 15094, 15095, 15095, 15096, 15096, 15147, 15147, 15148, 15148, 19941, 19941, 19942, 19942, 19943, 19943, 19967, 19967

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17233-17630
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17254, 17254, 17259, 17259, 17263, 17263, 17266, 17266, 17273, 17273, 17275, 17275, 17276, 17276, 17279, 17279, 17282, 17282, 17285, 17285, 17327, 17327, 17359, 17359, 17426, 17426, 17439, 17439, 17444, 17444, 17496, 17496, 17529, 17529, 17530, 17530, 17531, 17531, 17561, 17561, 17590, 17590, 17591, 17591, 20124, 20124

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 18671-19058
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18698, 18842, 18842, 20264, 20264

### `DataExporter` (class, 345 lines)

- Def site: line 6726-7070
- References: 257
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5682, 5682, 6772, 6772, 6788, 6788, 6789, 6789, 6812, 6812, 6814, 6814, 6817, 6817, 6831, 6831, 6833, 6833, 6842, 6842, 6844, 6844, 6845, 6845, 6851, 6851, 6852, 6852, 6852, 6869, 6869, 6873, 6873, 6915, 6915, 6946, 6946, 6949, 6949, 6951, 6951, 6997, 6997, 7007, 7007, 7040, 7040, 7045, 7045, 7052, 7052, 7274, 7274, 7306, 7306, 7317, 7317, 7342, 7342, 7362, 7362, 7874, 7874, 8667, 8667, 8946, 8946, 8961, 9025, 9025, 9042, 9042, 9060, 9060, 9081, 9081, 9640, 9640, 9715, 9715, 10045, 10045, 10396, 10396, 10481, 10497, 10617, 10617, 10621, 10621, 10641, 10641, 10654, 10654, 10658, 10658, 10676, 10676, 10838, 10838, 11185, 11185, 11332, 11332, 11409, 11409, 11413, 11413, 11418, 11418, 11551, 11551, 11570, 11570, 11621, 11621, 11624, 11624, 11775, 11775, 11778, 11778, 11877, 11877, 11883, 11883, 12180, 12180, 12197, 12197, 12212, 12212, 12426, 12426, 12454, 12454, 12470, 12470, 12507, 12507, 12545, 12545, 12634, 12634, 12663, 12663, 12701, 12701, 12752, 12817, 12817, 12823, 12823, 12865, 12865, 13034, 13034, 13040, 13040, 13159, 13159, 13167, 13167, 13331, 13331, 13382, 13555, 13555, 13726, 13726, 14239, 14239, 14600, 14600, 14606, 14606, 15514, 15514, 15573, 15680, 15816, 15816, 15834, 15834, 15852, 15852, 15879, 15879, 15880, 15880, 17091, 17177, 17177, 17198, 18506, 18506, 19024, 19024, 19109, 19109, 19130, 19130, 19632, 19632, 20293, 20293, 20309, 20309
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12873-13213
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12890, 12890, 12892, 12892, 12896, 12896, 12897, 12897, 12911, 12911, 12917, 12917, 12920, 12920, 12923, 12923, 12981, 12981, 12987, 12987, 12992, 12992, 13006, 13006, 13024, 13024, 13134, 13134, 13138, 13138, 13140, 13140, 13143, 13143, 13180, 13180, 13185, 13185, 13199, 13199, 13203, 13203, 13205, 13205, 13208, 13208, 13213, 13213, 20170, 20170, 20174, 20174, 20178, 20178

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7073-7400
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7175, 7175, 8391, 8872, 8891, 8992, 9121, 9144, 9816, 10124, 10169, 10583, 11353, 11364, 11427, 11844

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14704-15031
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12161, 12161, 12220, 12220, 12221, 12221, 13385, 14745, 14745, 14747, 14747, 14753, 14753, 14767, 14767, 14806, 14806, 14809, 14809, 14811, 14811, 14812, 14812, 14813, 14813, 14867, 14867, 14868, 14868, 14879, 14879, 14888, 14888, 14907, 14907, 14959, 14959, 14963, 14963, 14971, 14971, 14972, 14972, 14996, 14996, 15000, 15000
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16088-16376
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16116, 16116, 16119, 16119, 16124, 16124, 16127, 16127, 16171, 16171, 16177, 16177, 16208, 16208, 16211, 16211, 16215, 16215, 16241, 16241, 16258, 16258, 16264, 16264, 16278, 16278, 16279, 16279, 16281, 16281, 16287, 16287, 16294, 16294, 16303, 16303, 16350, 16350, 16372, 16372, 16373, 16373, 16374, 16374, 20115, 20115

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10190-10462
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10213, 10213, 10214, 10214, 10227, 10227, 10228, 10228, 10230, 10230, 10231, 10231, 10234, 10234, 10237, 10237, 10241, 10241, 10242, 10242, 10318, 10318, 10322, 10322, 10325, 10325, 10338, 10338, 10375, 10375, 10392, 10392, 10405, 10405, 10407, 10407, 10414, 10414, 10423, 10423, 10432, 10432, 10433, 10433, 10444, 10444, 10448, 10448, 10457, 10457, 10462, 10462, 20372, 20372

### `CacheUtils` (class, 264 lines)

- Def site: line 5212-5475
- References: 107
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5252, 5252, 5254, 5254, 5336, 5336, 5342, 5342, 5379, 5379, 5381, 5381, 5390, 5390, 5400, 5400, 5410, 5410, 5446, 5446, 7910, 7910, 9568, 9568, 9569, 9569, 9880, 9880, 10726, 10726, 10746, 10746, 12747, 15153, 15153, 15159, 15159, 15160, 15160, 15161, 15161, 15162, 15162, 15163, 15163, 15164, 15164, 15171, 15171, 15199, 15199, 15571, 15817, 15817, 15835, 15835, 15853, 15853, 15903, 17086, 17122, 17122, 17146, 17146, 17170, 17170, 17314, 17314, 17315, 17315, 17316, 17316, 17317, 17317, 17653, 17653, 19857, 19857, 20409, 20409
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10957-11207
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10964, 10964, 10967, 10967, 10972, 10972, 10973, 10973, 10981, 10981, 10984, 10984, 10992, 10992, 11032, 11032, 11040, 11040, 11088, 11088, 11105, 11105, 11108, 11108, 11110, 11110, 11174, 11174, 11175, 11175, 20375, 20375

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15283-15527
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15149, 15149, 15309, 15309, 15311, 15311, 15312, 15312, 15313, 15313, 15341, 15341, 15346, 15346, 15368, 15368, 15369, 15369, 15411, 15411, 15419, 15419, 15445, 15445, 15454, 15454, 15462, 15462, 15493, 15493, 19946, 19946, 19950, 19950

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6145-6365
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6168, 6168, 6219, 6219, 6289, 6289, 6313, 6313, 6325, 6325, 6327, 6327, 6337, 6337, 6352, 6352, 6356, 6356, 6357, 6357, 6360, 6360, 6362, 6362, 12860, 12860, 15575
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 20459-20672
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21315, 21315, 21318, 21399, 21750

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7601-7810
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7614, 7614, 7620, 7620, 7621, 7621, 7624, 7624, 7647, 7647, 7650, 7650, 7653, 7653, 7654, 7654, 7656, 7656, 7723, 7723, 7767, 7767, 8232, 8232, 13181, 13181, 15678, 15941, 15941, 16101, 16101

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12479-12681
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12500, 12500, 12509, 12509, 12571, 12571, 12578, 12578, 12610, 12610, 12612, 12612, 12636, 12636, 12671, 12671, 12678, 12678, 12709, 12709, 15223, 15223, 19982, 19982, 19984, 19984, 19985, 19985, 19987, 19987

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13732-13919
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20332, 20332, 20333, 20333, 20334, 20334, 20335, 20335, 20336, 20336, 20337, 20337, 20338, 20338, 20339, 20339, 20341, 20341, 20342, 20342, 20343, 20343, 20344, 20344, 20345, 20345, 20346, 20346, 20347, 20347, 20349, 20349, 20350, 20350, 20351, 20351, 20352, 20352, 20353, 20353, 20354, 20354, 20355, 20355, 20356, 20356, 20357, 20357, 20359, 20359, 20360, 20360, 20361, 20361, 20362, 20362, 20363, 20363, 20364, 20364, 20365, 20365, 20366, 20366, 20367, 20367, 20369, 20369, 20370, 20370

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5557-5736
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5645, 5645, 5682, 5682, 5684, 5684, 5687, 5687, 5695, 5695, 5697, 5697, 5699, 5699, 5702, 5702, 5731, 5731, 5734, 5734, 20109, 20109

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6545-6723
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6590, 6590, 6628, 6628, 6639, 6639, 6665, 6665, 6666, 6666, 6668, 6668, 6674, 6674, 6675, 6675, 6678, 6678, 6684, 6684, 6685, 6685, 6688, 6688, 6690, 6690, 6700, 6700, 6702, 6702, 6703, 6703, 6705, 6705

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11437-11604
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11544, 11544, 11563, 11563, 11581, 11581, 11590, 11590, 11593, 11593, 11594, 11594, 11597, 11597, 11602, 11602, 11604, 11604, 20010, 20010

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11649-11816
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11686, 11686, 11688, 11688, 11691, 11691, 11762, 11762, 11764, 11764, 11777, 11777, 11781, 11781, 20013, 20013, 20014, 20014, 20015, 20015, 20053, 20053, 20058, 20058

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10682-10843
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10720, 10720, 10727, 10727, 10734, 10734, 10740, 10740, 10747, 10747, 10754, 10754, 10815, 10815, 10826, 10826, 20001, 20001, 20002, 20002, 20004, 20004, 20005, 20005, 20006, 20006

### `CLIShellManager` (class, 161 lines)

- Def site: line 15922-16082
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15945, 15945, 15947, 15947, 16016, 16016, 16018, 16018, 16037, 16037, 16039, 16039, 16039, 16055, 16055, 16071, 16071, 16072, 16072, 16078, 16078, 20114, 20114

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6373-6530
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5510, 5510, 6389, 6389, 6402, 6402, 6405, 6405, 6429, 6429, 6437, 6437, 6438, 6438, 6460, 6460, 6465, 6465, 6467, 6467, 6540, 6540, 6541, 6541, 6948, 6948, 6973, 6973, 7042, 7042, 7043, 7043, 7372, 7372, 7386, 7386, 7387, 7387, 7872, 7872, 7873, 7873, 8795, 8795, 8960, 9020, 9020, 9022, 9022, 9023, 9023, 9040, 9040, 9041, 9041, 9058, 9058, 9059, 9059, 9079, 9079, 9080, 9080, 9637, 9637, 9638, 9638, 9712, 9712, 9713, 9713, 10041, 10041, 10044, 10044, 10619, 10619, 10620, 10620, 10656, 10656, 10657, 10657, 10836, 10836, 10837, 10837, 11181, 11181, 11182, 11182, 11328, 11328, 11329, 11329, 11411, 11411, 11412, 11412, 11623, 11623, 11798, 11798, 11799, 11799, 11875, 11875, 11876, 11876, 12179, 12179, 12195, 12195, 12196, 12196, 12424, 12424, 12425, 12425, 12504, 12504, 12505, 12505, 12506, 12506, 12542, 12542, 12543, 12543, 12631, 12631, 12632, 12632, 12660, 12660, 12661, 12661, 12698, 12698, 12699, 12699, 12751, 12820, 12820, 12821, 12821, 12863, 12863, 12864, 12864, 13032, 13032, 13033, 13033, 13157, 13157, 13158, 13158, 13381, 13553, 13553, 14605, 14605, 15512, 15512, 15513, 15513, 15574, 15682, 17175, 17175, 17176, 17176, 19014, 19014
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15045-15200
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15067, 15067, 15073, 15073, 15075, 15075, 15103, 15103, 15129, 15129, 15132, 15132, 15135, 15135, 20100, 20100, 20104, 20104, 20112, 20112

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13216-13361
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13255, 13255, 13262, 13262, 13287, 13287, 13290, 13290, 13303, 13303, 13347, 13347, 13351, 13351, 13356, 13356, 13357, 13357, 13361, 13361, 20407, 20407

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13369-13513
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12590, 12590, 12766, 12766, 12844, 12844, 12849, 12849, 13398, 13398, 13404, 13404, 13410, 13410, 13416, 13416, 13422, 13422, 13428, 13428, 13434, 13434, 13440, 13440, 13446, 13446, 13452, 13452, 13458, 13458, 13464, 13464, 13470, 13470, 13476, 13476, 13482, 13482, 13488, 13488, 13494, 13494, 13500, 13500, 13506, 13506, 13512, 13512, 20020, 20020, 20161, 20161, 20163, 20163, 20278, 20278, 20404, 20404, 20405, 20405, 20406, 20406, 20425, 20425, 20426, 20426, 20427, 20427, 20428, 20428, 20429, 20429, 20430, 20430, 20431, 20431
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10536-10679
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10550, 10550, 10551, 10551, 10637, 10637, 10672, 10672, 19995, 19995, 19996, 19996, 19997, 19997, 19998, 19998, 19999, 19999

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13516-13654
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13585, 13585, 13588, 13588, 13589, 13589, 13590, 13590, 13610, 13610, 13613, 13613, 13621, 13621, 13626, 13626, 20433, 20433

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8838-8966
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8909, 8909, 8920, 8920, 15143, 15143, 15144, 15144, 19898, 19898, 19899, 19899, 20078, 20078

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11210-11338
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11217, 11217, 11222, 11222, 11223, 11223, 11224, 11224, 11227, 11227, 11228, 11228, 11291, 11291, 11298, 11298, 11325, 11325, 20377, 20377

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15668-15794
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15688, 15688, 15693, 15693, 15698, 15698, 15735, 15735, 15741, 15741, 15747, 15747, 15753, 15753, 15759, 15759, 15760, 15760, 15761, 15761, 15762, 15762, 15763, 15763, 15767, 15767, 15776, 15776, 15780, 15780, 15783, 15783, 15789, 15789, 20073, 20073

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5790-5914
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5811, 5811, 5813, 5813, 5829, 5829, 5841, 5841, 5880, 5880, 5881, 5881, 5882, 5882, 5883, 5883, 5884, 5884, 5895, 5895, 5898, 5898, 6830, 6830, 21412, 21412, 21995, 21995

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8972-9083
- References: 53
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7910, 7910, 9568, 9568, 9880, 9880, 10726, 10726, 10746, 10746, 12748, 15092, 15092, 15145, 15145, 15578, 15818, 15818, 15836, 15836, 15854, 15854, 17087, 17124, 17124, 17148, 17148, 17172, 17172, 17315, 17315, 17656, 17656, 19939, 19939, 19954, 19954, 19964, 19964, 19964, 19964, 19974, 19974
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10846-10954
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10901, 10901, 10904, 10904, 10905, 10905, 10910, 10910, 10928, 10928, 10928, 10937, 10937, 10937, 10937, 10938, 10938, 10938, 10938, 10996, 10996, 10999, 10999, 11011, 11011, 11012, 11012, 11025, 11025, 11064, 11064, 11072, 11072, 11126, 11126, 11134, 11134

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12771-12870
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12836, 12836, 12838, 12838, 12839, 12839, 19948, 19948, 20016, 20016, 20018, 20018, 20019, 20019

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15560-15657
- References: 79
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15303, 15303, 15538, 15538, 15596, 15596, 15602, 15602, 15608, 15608, 15614, 15614, 15620, 15620, 15626, 15626, 15632, 15632, 15638, 15638, 15644, 15644, 15650, 15650, 15656, 15656, 15904, 17088, 17316, 17316, 17319, 17319, 17655, 17655, 19905, 19905, 19972, 19972, 19978, 19978, 20029, 20029, 20086, 20086
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8268-8364
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8324, 8324, 8360, 8360

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11341-11434
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11393, 11393, 11406, 11406, 20008, 20008, 20050, 20050, 20051, 20051, 20056, 20056, 20057, 20057

### `ValidationUtils` (class, 90 lines)

- Def site: line 5920-6009
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6002, 6002, 15366, 15366, 15367, 15367, 15581, 19808, 19808
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12684-12768
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12718, 12718, 19983, 19983, 19991, 19991, 20017, 20017, 20162, 20162

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 19085-19163
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19080, 19080, 19081, 19081, 20257, 20257
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17102-17179
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20128, 20128, 20132, 20132, 20136, 20136
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1884-1957
- References: 261
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1897, 1897, 1929, 1929, 2204, 2204, 2293, 2293, 2320, 2320, 7622, 7622, 7708, 7708, 7838, 7838, 7915, 7915, 7998, 7998, 8228, 8228, 8417, 8417, 8473, 8473, 8486, 8486, 8503, 8503, 8548, 8548, 8579, 8579, 8585, 8585, 8688, 8688, 10229, 10229, 10496, 10998, 10998, 11027, 11027, 11292, 11292, 11498, 11498, 11737, 11737, 12453, 12453, 12469, 12469, 13256, 13256, 13675, 13675, 13725, 13725, 15579, 15781, 15781, 15814, 15814, 15832, 15832, 15850, 15850, 15877, 15877, 15902, 17090, 17129, 17129, 17154, 17154, 17197, 17296, 17296, 17508, 17508, 17651, 17651, 18655, 18655, 18745, 18745, 19075, 19075, 19105, 19105, 19126, 19126, 19145, 19145, 19161, 19161, 19178, 19178, 19755, 19755, 19775, 19775, 19810, 19810, 19823, 19823, 20291, 20291, 20382, 20382, 20387, 20387, 20393, 20393, 20412, 20412, 20418, 20418, 22018, 22018, 22116, 22116
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

- Def site: line 15206-15277
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20094, 20094, 20095, 20095, 20096, 20096, 20097, 20097

### `DisplayUtils` (class, 70 lines)

- Def site: line 5481-5550
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5513, 5513, 5514, 5514, 5529, 5529, 5531, 5531, 18024, 18024, 18063, 18063, 18122, 18122

### `ConfigUtils` (class, 70 lines)

- Def site: line 6015-6084
- References: 193
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6057, 6057, 6062, 6062, 6159, 6159, 6217, 6217, 7108, 7108, 7765, 7765, 8410, 8410, 8433, 8433, 8453, 8453, 8638, 8638, 8659, 8659, 8934, 8934, 8959, 8959, 9014, 9014, 9036, 9036, 9053, 9053, 9070, 9070, 9455, 9455, 9678, 9678, 9695, 9695, 10087, 10087, 10419, 10419, 10630, 10630, 10667, 10667, 10820, 10820, 10963, 10963, 11216, 11216, 11404, 11404, 11588, 11588, 11907, 11907, 12243, 12243, 12415, 12415, 12455, 12455, 12461, 12461, 12555, 12555, 12785, 12785, 12858, 12858, 13345, 13345, 13380, 13579, 13579, 15086, 15086, 15302, 15302, 15570, 15677, 15777, 15777, 15812, 15812, 15830, 15830, 15848, 15848, 15883, 15883, 17085, 17195, 17703, 17703, 18656, 18656, 18661, 18661, 18663, 18663, 19076, 19076, 19078, 19078, 19102, 19102, 19106, 19106, 19107, 19107, 19127, 19127, 19128, 19128, 19289, 19289, 19859, 19859, 19891, 19891, 19928, 19928, 19934, 19934, 20062, 20062, 20119, 20119, 20202, 20202, 20211, 20211, 20289, 20289, 20290, 20290, 20307, 20307, 20382, 20382, 20387, 20387, 20393, 20393, 20412, 20412, 20418, 20418, 21329, 21329, 21400, 21882, 21882, 21970, 21970
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10465-10533
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10505, 10505, 10510, 10510, 10515, 10515, 10516, 10516, 10522, 10522, 10523, 10523, 10529, 10529, 10530, 10530, 10531, 10531, 10532, 10532, 20435, 20435

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 19814-19879
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19862, 19862, 19870, 19870, 19879, 19879, 20408, 20408

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15801-15856
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20033, 20033, 20037, 20037, 20242, 20242

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6090-6136
- References: 59
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6214, 6214, 8100, 8100, 9015, 9015, 9038, 9038, 9525, 9525, 9560, 9560, 9574, 9574, 9697, 9697, 9701, 9701, 10249, 10249, 12559, 12559, 13229, 13229, 13355, 13355, 13387, 13565, 13565, 13601, 13601, 15576, 17811, 17811, 18657, 18657, 18966, 18966, 19077, 19077, 19108, 19108, 19129, 19129, 20292, 20292, 20308, 20308, 21901, 21901
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5739-5784
- References: 102
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5251, 5251, 5293, 5293, 5338, 5338, 5444, 5444, 5459, 5459, 5729, 5729, 5730, 5730, 5774, 5774, 6240, 6240, 7934, 7934, 9225, 9225, 9536, 9536, 9552, 9552, 9881, 9881, 10762, 10762, 10781, 10781, 12750, 15169, 15169, 15572, 15815, 15815, 15833, 15833, 15851, 15851, 15878, 15878, 15905, 16327, 16327, 16367, 16367, 16368, 16368, 16369, 16369, 17089, 17121, 17121, 17145, 17145, 17149, 17149, 17169, 17169, 17196, 17271, 17271, 17305, 17305, 17326, 17326, 17358, 17358, 17420, 17420, 17459, 17459, 17609, 17609, 17654, 17654, 18658, 18658
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17185-17227
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17208, 17208, 17214, 17214, 17220, 17220, 17226, 17226, 20226, 20226, 20230, 20230, 20234, 20234, 20238, 20238

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11607-11646
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11644, 11644, 20432, 20432

### `TimeUtils` (class, 29 lines)

- Def site: line 1848-1876
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8888, 8888, 8889, 8889, 8918, 8918, 8919, 8919, 8935, 8935, 8936, 8936, 9814, 9814, 9815, 9815, 10119, 10119, 10120, 10120, 10167, 10167, 10168, 10168, 10723, 10723, 10725, 10725, 10743, 10743, 10745, 10745, 11633, 11633, 11634, 11634, 12294, 12294, 12295, 12295, 12400, 12400, 12401, 12401, 13383
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15530-15557
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15544, 15544, 15550, 15550, 15556, 15556, 20140, 20140, 20144, 20144
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15891-15916
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15911, 15911, 15916, 15916, 20148, 20148, 20153, 20153
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2112-2136
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2198, 2257, 18774, 21725

### `RoutingUtils` (class, 22 lines)

- Def site: line 13682-13703
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19914, 19914, 19918, 19918, 19922, 19922
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17637-17658
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18660, 18660, 20061, 20061, 20118, 20118, 20201, 20201, 20210, 20210

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 19061-19082
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20271, 20271
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7572-7592
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6323, 10092, 15415, 15580
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13928-13937
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13964, 14100, 14177, 14196, 14208, 14229, 14242, 14253, 14259, 14272, 14365, 14500, 14595

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 300-308
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

- Def site: line 327-335
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15238, 15255, 15271
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 312-319
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

- Def site: line 287-289
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13388, 13677, 19110, 19131, 19276, 19307, 19339, 19574, 19589
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 615-617
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1225, 1894, 1894, 1894, 1906, 1912, 6216, 6336, 7396, 7456, 9624, 9735, 9989, 10819, 13390, 15448, 15490, 15588, 20294
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

- Def site: line 1996-1998
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1996, 7406, 7413, 7414, 10000, 15437

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2014-2016
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2014, 15584, 17093
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 731-1735
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1780

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
