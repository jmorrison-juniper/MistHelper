# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 190 first-party files
- Definitions analyzed: 93
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=12, hot=80, skipped=1

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
| `ConstDefinitionsExporter` | class | 759 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgInventoryExporter` | class | 686 | 110 | hot |  | oversize_25_lines,missing_inline_comments |
| `OrgConfigMigrationManager` | class | 675 | 4 | hot |  | oversize_25_lines |
| `OrgExportUtils` | class | 653 | 128 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `BulkRadiusWLANConfigManager` | class | 587 | 13 | hot |  | oversize_25_lines |
| `menu_actions` | assignment | 572 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgTicketManager` | class | 463 | 66 | hot |  | oversize_25_lines |
| `OperationRegistry` | class | 461 | 9 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `PromptUtils` | class | 441 | 117 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 58 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 398 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `MSPInventoryExporter` | class | 388 | 5 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `DataExporter` | class | 345 | 250 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `APIDataFetcher` | class | 328 | 16 | hot |  | oversize_25_lines |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 106 | hot |  | oversize_25_lines |
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
| `OrgSiteExporter` | class | 112 | 52 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 109 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteConfigExporter` | class | 100 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `GatewayExportUtils` | class | 98 | 78 | hot |  | oversize_25_lines,missing_action_logging |
| `DeviceUtils` | class | 97 | 4 | hot |  | oversize_25_lines |
| `OrgAdminExporter` | class | 94 | 14 | hot |  | oversize_25_lines,hardcoded_separator |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteClientExporter` | class | 85 | 10 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 258 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 8 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 188 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 57 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 99 | hot |  | oversize_25_lines,missing_inline_comments |
| `SiteConfigManager` | class | 43 | 16 | hot |  | oversize_25_lines,missing_action_logging |
| `SelfExportUtils` | class | 40 | 4 | hot |  | oversize_25_lines,non_ascii_logs |
| `BulkAPFirmwareUpgrader` | class | 32 | 2 | low-use | FirmwareManager | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `TimeUtils` | class | 29 | 51 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
| `SSHRunnerManager` | class | 26 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 4 | hot |  | missing_action_logging |
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
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Low-Use (12)

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 17628-17659
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1755, 1758

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 18160-18178
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1850, 1851

### `initialize_mist_session_interactive` (function, 18 lines)

- Def site: line 2198-2215
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2258, 17763, 20710

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2824-2841
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20715, 20778

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 375-387
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 375, 559

### `main` (function, 12 lines)

- Def site: line 21106-21117
- References: 2
- Suggested class: `MainManager`
- Suggested module: `src/refactors/main.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `main` OUT of the entrypoint into a new `src/refactors/main.py` module and rewrite the callsite(s) to import from there
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21220
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6545-6548
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6545, 15687
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1990-1992
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1990, 9931, 15360

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1993-1995
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1993, 7421

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1998-2000
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1998, 15500

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2005-2007
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2005, 7411

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2013-2015
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2013, 15589
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2886-5212
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2886, 6591, 6592, 6601, 6765

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13946-14704
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14423, 14423, 14435, 14435, 14463, 14463, 14475, 14475, 14536, 14536, 14573, 14573, 14730, 19159

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9092-9777
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5598, 5598, 9215, 9215, 9266, 9266, 9269, 9269, 9310, 9310, 9349, 9349, 9367, 9367, 9445, 9445, 9452, 9452, 9462, 9462, 9465, 9465, 9478, 9478, 9479, 9479, 9480, 9480, 9481, 9481, 9489, 9489, 9491, 9491, 9492, 9492, 9493, 9493, 9494, 9494, 9497, 9497, 9500, 9500, 9503, 9503, 9506, 9506, 9552, 9552, 9575, 9575, 9576, 9576, 9577, 9577, 9579, 9579, 9615, 9615, 9631, 9631, 9685, 9685, 9686, 9686, 9687, 9687, 9690, 9690, 9691, 9691, 9710, 9710, 9712, 9712, 9713, 9713, 9748, 9748, 15099, 15099, 15152, 15152, 15583, 17075, 17075, 17099, 17099, 17123, 17123, 17266, 17266, 18934, 18934, 18941, 18941, 18950, 18950, 18954, 18954, 18963, 18963
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16374-17048
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16762, 16762, 19405, 19411

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11825-12477
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10602, 10602, 10611, 10611, 10699, 10699, 10706, 10706, 11380, 11380, 11666, 11666, 11671, 11671, 11678, 11678, 11683, 11683, 11897, 11897, 11919, 11919, 11922, 11922, 11948, 11948, 11957, 11957, 11958, 11958, 11979, 11979, 12022, 12022, 12068, 12068, 12079, 12079, 12106, 12106, 12111, 12111, 12112, 12112, 12113, 12113, 12145, 12145, 12151, 12151, 12176, 12176, 12196, 12196, 12231, 12231, 12246, 12246, 12252, 12252, 12254, 12254, 12257, 12257, 12259, 12259, 12263, 12263, 12267, 12267, 12272, 12272, 12279, 12279, 12286, 12286, 12293, 12293, 12302, 12302, 12312, 12312, 12319, 12319, 12326, 12326, 12333, 12333, 12340, 12340, 12347, 12347, 12357, 12357, 12366, 12366, 12375, 12375, 12384, 12384, 12393, 12393, 12422, 12422, 18895, 18895, 19076, 19076, 19153, 19153, 19154, 19154, 19162, 19162, 19367, 19367, 19368, 19368, 19387, 19387, 19394, 19394, 19395, 19395, 19396, 19396, 19397, 19397

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 18191-18777
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18468, 18468, 18469, 18469, 18472, 18472, 18474, 18474, 18476, 18476, 18492, 18492, 19312

### `menu_actions` (assignment, 572 lines)

- Def site: line 18876-19447
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18876, 20161, 20162, 20171, 20291, 20291, 20333, 20391, 20436, 20927, 20931, 20976, 20976, 21003, 21003, 21006
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8376-8838
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8417, 8417, 8422, 8422, 8432, 8432, 8440, 8440, 8445, 8445, 8450, 8450, 8460, 8460, 8465, 8465, 8470, 8470, 8490, 8490, 8500, 8500, 8501, 8501, 8504, 8504, 8534, 8534, 8620, 8620, 8622, 8622, 8646, 8646, 8652, 8652, 8657, 8657, 8666, 8666, 8670, 8670, 8689, 8689, 8692, 8692, 8703, 8703, 8704, 8704, 8799, 8799, 8820, 8820, 19435, 19435, 19436, 19436, 19437, 19437, 19438, 19438, 19439, 19439, 19440, 19440

### `OperationRegistry` (class, 461 lines)

- Def site: line 19672-20132
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20139, 20139, 20143, 20143, 20163, 20163, 20168, 20168, 20392

### `PromptUtils` (class, 441 lines)

- Def site: line 7823-8263
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7768, 7768, 7784, 7784, 7788, 7788, 7789, 7789, 7790, 7790, 7805, 7805, 7811, 7811, 7838, 7838, 7841, 7841, 7849, 7849, 7867, 7867, 7917, 7917, 7925, 7925, 7930, 7930, 7976, 7976, 7987, 7987, 8012, 8012, 8031, 8031, 8032, 8032, 8035, 8035, 8036, 8036, 8126, 8126, 8128, 8128, 8132, 8132, 8160, 8160, 8161, 8161, 8162, 8162, 8163, 8163, 8164, 8164, 8173, 8173, 8217, 8217, 8241, 8241, 12557, 12557, 12607, 12607, 12612, 12612, 12755, 12838, 12838, 12892, 12892, 12913, 12913, 12918, 12918, 13182, 13182, 13385, 13587, 13587, 13674, 13674, 13679, 13679, 13729, 13729, 13730, 13730, 15226, 15226, 15685, 17082, 17082, 17604, 17604, 18800, 18800, 18801, 18801, 19087, 19087
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9780-10193
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5592, 5592, 9813, 9813, 9897, 9897, 9903, 9903, 9906, 9906, 9950, 9950, 9964, 9964, 9991, 9991, 9997, 9997, 10011, 10011, 10094, 10094, 10096, 10096, 10100, 10100, 10102, 10102, 10105, 10105, 10109, 10109, 10112, 10112, 10122, 10122, 10128, 10128, 10166, 10166, 15100, 15100, 15101, 15101, 15102, 15102, 15153, 15153, 15154, 15154, 18935, 18935, 18936, 18936, 18937, 18937, 18961, 18961

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17185-17582
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17206, 17206, 17211, 17211, 17215, 17215, 17218, 17218, 17225, 17225, 17227, 17227, 17228, 17228, 17231, 17231, 17234, 17234, 17237, 17237, 17279, 17279, 17311, 17311, 17378, 17378, 17391, 17391, 17396, 17396, 17448, 17448, 17481, 17481, 17482, 17482, 17483, 17483, 17513, 17513, 17542, 17542, 17543, 17543, 19118, 19118

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 17665-18052
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17692, 17836, 17836, 19258, 19258

### `DataExporter` (class, 345 lines)

- Def site: line 6732-7076
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5688, 5688, 6778, 6778, 6794, 6794, 6795, 6795, 6818, 6818, 6820, 6820, 6823, 6823, 6837, 6837, 6839, 6839, 6848, 6848, 6850, 6850, 6851, 6851, 6857, 6857, 6858, 6858, 6858, 6875, 6875, 6879, 6879, 6921, 6921, 6952, 6952, 6955, 6955, 6957, 6957, 7003, 7003, 7013, 7013, 7046, 7046, 7051, 7051, 7058, 7058, 7280, 7280, 7312, 7312, 7323, 7323, 7348, 7348, 7368, 7368, 7880, 7880, 8673, 8673, 8952, 8952, 8967, 9031, 9031, 9048, 9048, 9066, 9066, 9087, 9087, 9646, 9646, 9721, 9721, 10051, 10051, 10402, 10402, 10487, 10503, 10623, 10623, 10627, 10627, 10647, 10647, 10660, 10660, 10664, 10664, 10682, 10682, 10844, 10844, 11191, 11191, 11338, 11338, 11415, 11415, 11419, 11419, 11424, 11424, 11557, 11557, 11576, 11576, 11627, 11627, 11630, 11630, 11781, 11781, 11784, 11784, 11883, 11883, 11889, 11889, 12186, 12186, 12203, 12203, 12218, 12218, 12432, 12432, 12460, 12460, 12476, 12476, 12513, 12513, 12551, 12551, 12640, 12640, 12669, 12669, 12707, 12707, 12758, 12823, 12823, 12829, 12829, 12871, 12871, 13040, 13040, 13046, 13046, 13165, 13165, 13173, 13173, 13337, 13337, 13388, 13561, 13561, 13732, 13732, 14245, 14245, 14606, 14606, 14612, 14612, 15520, 15520, 15579, 15686, 15822, 15822, 15840, 15840, 15858, 15858, 17129, 17129, 17150, 18018, 18018, 18103, 18103, 18124, 18124, 18626, 18626, 19287, 19287, 19303, 19303
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12879-13219
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12896, 12896, 12898, 12898, 12902, 12902, 12903, 12903, 12917, 12917, 12923, 12923, 12926, 12926, 12929, 12929, 12987, 12987, 12993, 12993, 12998, 12998, 13012, 13012, 13030, 13030, 13140, 13140, 13144, 13144, 13146, 13146, 13149, 13149, 13186, 13186, 13191, 13191, 13205, 13205, 13209, 13209, 13211, 13211, 13214, 13214, 13219, 13219, 19164, 19164, 19168, 19168, 19172, 19172

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7079-7406
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7181, 7181, 8397, 8878, 8897, 8998, 9127, 9150, 9822, 10130, 10175, 10589, 11359, 11370, 11433, 11850

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14710-15037
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12167, 12167, 12226, 12226, 12227, 12227, 13391, 14751, 14751, 14753, 14753, 14759, 14759, 14773, 14773, 14812, 14812, 14815, 14815, 14817, 14817, 14818, 14818, 14819, 14819, 14873, 14873, 14874, 14874, 14885, 14885, 14894, 14894, 14913, 14913, 14965, 14965, 14969, 14969, 14977, 14977, 14978, 14978, 15002, 15002, 15006, 15006
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16070-16358
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16098, 16098, 16101, 16101, 16106, 16106, 16109, 16109, 16153, 16153, 16159, 16159, 16190, 16190, 16193, 16193, 16197, 16197, 16223, 16223, 16240, 16240, 16246, 16246, 16260, 16260, 16261, 16261, 16263, 16263, 16269, 16269, 16276, 16276, 16285, 16285, 16332, 16332, 16354, 16354, 16355, 16355, 16356, 16356, 19109, 19109

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10196-10468
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10219, 10219, 10220, 10220, 10233, 10233, 10234, 10234, 10236, 10236, 10237, 10237, 10240, 10240, 10243, 10243, 10247, 10247, 10248, 10248, 10324, 10324, 10328, 10328, 10331, 10331, 10344, 10344, 10381, 10381, 10398, 10398, 10411, 10411, 10413, 10413, 10420, 10420, 10429, 10429, 10438, 10438, 10439, 10439, 10450, 10450, 10454, 10454, 10463, 10463, 10468, 10468, 19366, 19366

### `CacheUtils` (class, 264 lines)

- Def site: line 5218-5481
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5258, 5258, 5260, 5260, 5342, 5342, 5348, 5348, 5385, 5385, 5387, 5387, 5396, 5396, 5406, 5406, 5416, 5416, 5452, 5452, 7916, 7916, 9574, 9574, 9575, 9575, 9886, 9886, 10732, 10732, 10752, 10752, 12753, 15159, 15159, 15165, 15165, 15166, 15166, 15167, 15167, 15168, 15168, 15169, 15169, 15170, 15170, 15177, 15177, 15205, 15205, 15577, 15823, 15823, 15841, 15841, 15859, 15859, 15885, 17074, 17074, 17098, 17098, 17122, 17122, 17266, 17266, 17267, 17267, 17268, 17268, 17269, 17269, 17605, 17605, 18851, 18851, 19403, 19403
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10963-11213
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10970, 10970, 10973, 10973, 10978, 10978, 10979, 10979, 10987, 10987, 10990, 10990, 10998, 10998, 11038, 11038, 11046, 11046, 11094, 11094, 11111, 11111, 11114, 11114, 11116, 11116, 11180, 11180, 11181, 11181, 19369, 19369

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15289-15533
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15155, 15155, 15315, 15315, 15317, 15317, 15318, 15318, 15319, 15319, 15347, 15347, 15352, 15352, 15374, 15374, 15375, 15375, 15417, 15417, 15425, 15425, 15451, 15451, 15460, 15460, 15468, 15468, 15499, 15499, 18940, 18940, 18944, 18944

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6151-6371
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6174, 6174, 6225, 6225, 6295, 6295, 6319, 6319, 6331, 6331, 6333, 6333, 6343, 6343, 6358, 6358, 6362, 6362, 6363, 6363, 6366, 6366, 6368, 6368, 12866, 12866, 15581
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19453-19666
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20309, 20309, 20312, 20393, 20744

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7607-7816
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7620, 7620, 7626, 7626, 7627, 7627, 7630, 7630, 7653, 7653, 7656, 7656, 7659, 7659, 7660, 7660, 7662, 7662, 7729, 7729, 7773, 7773, 8238, 8238, 13187, 13187, 15684, 15923, 15923, 16083, 16083

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12485-12687
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12506, 12506, 12515, 12515, 12577, 12577, 12584, 12584, 12616, 12616, 12618, 12618, 12642, 12642, 12677, 12677, 12684, 12684, 12715, 12715, 15229, 15229, 18976, 18976, 18978, 18978, 18979, 18979, 18981, 18981

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13738-13925
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19326, 19326, 19327, 19327, 19328, 19328, 19329, 19329, 19330, 19330, 19331, 19331, 19332, 19332, 19333, 19333, 19335, 19335, 19336, 19336, 19337, 19337, 19338, 19338, 19339, 19339, 19340, 19340, 19341, 19341, 19343, 19343, 19344, 19344, 19345, 19345, 19346, 19346, 19347, 19347, 19348, 19348, 19349, 19349, 19350, 19350, 19351, 19351, 19353, 19353, 19354, 19354, 19355, 19355, 19356, 19356, 19357, 19357, 19358, 19358, 19359, 19359, 19360, 19360, 19361, 19361, 19363, 19363, 19364, 19364

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5563-5742
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5651, 5651, 5688, 5688, 5690, 5690, 5693, 5693, 5701, 5701, 5703, 5703, 5705, 5705, 5708, 5708, 5737, 5737, 5740, 5740, 19103, 19103

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6551-6729
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6596, 6596, 6634, 6634, 6645, 6645, 6671, 6671, 6672, 6672, 6674, 6674, 6680, 6680, 6681, 6681, 6684, 6684, 6690, 6690, 6691, 6691, 6694, 6694, 6696, 6696, 6706, 6706, 6708, 6708, 6709, 6709, 6711, 6711

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11443-11610
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11550, 11550, 11569, 11569, 11587, 11587, 11596, 11596, 11599, 11599, 11600, 11600, 11603, 11603, 11608, 11608, 11610, 11610, 19004, 19004

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11655-11822
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11692, 11692, 11694, 11694, 11697, 11697, 11768, 11768, 11770, 11770, 11783, 11783, 11787, 11787, 19007, 19007, 19008, 19008, 19009, 19009, 19047, 19047, 19052, 19052

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10688-10849
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10726, 10726, 10733, 10733, 10740, 10740, 10746, 10746, 10753, 10753, 10760, 10760, 10821, 10821, 10832, 10832, 18995, 18995, 18996, 18996, 18998, 18998, 18999, 18999, 19000, 19000

### `CLIShellManager` (class, 161 lines)

- Def site: line 15904-16064
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15927, 15927, 15929, 15929, 15998, 15998, 16000, 16000, 16019, 16019, 16021, 16021, 16021, 16037, 16037, 16053, 16053, 16054, 16054, 16060, 16060, 19108, 19108

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6379-6536
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5516, 5516, 6395, 6395, 6408, 6408, 6411, 6411, 6435, 6435, 6443, 6443, 6444, 6444, 6466, 6466, 6471, 6471, 6473, 6473, 6546, 6546, 6547, 6547, 6954, 6954, 6979, 6979, 7048, 7048, 7049, 7049, 7378, 7378, 7392, 7392, 7393, 7393, 7878, 7878, 7879, 7879, 8801, 8801, 8966, 9026, 9026, 9028, 9028, 9029, 9029, 9046, 9046, 9047, 9047, 9064, 9064, 9065, 9065, 9085, 9085, 9086, 9086, 9643, 9643, 9644, 9644, 9718, 9718, 9719, 9719, 10047, 10047, 10050, 10050, 10625, 10625, 10626, 10626, 10662, 10662, 10663, 10663, 10842, 10842, 10843, 10843, 11187, 11187, 11188, 11188, 11334, 11334, 11335, 11335, 11417, 11417, 11418, 11418, 11629, 11629, 11804, 11804, 11805, 11805, 11881, 11881, 11882, 11882, 12185, 12185, 12201, 12201, 12202, 12202, 12430, 12430, 12431, 12431, 12510, 12510, 12511, 12511, 12512, 12512, 12548, 12548, 12549, 12549, 12637, 12637, 12638, 12638, 12666, 12666, 12667, 12667, 12704, 12704, 12705, 12705, 12757, 12826, 12826, 12827, 12827, 12869, 12869, 12870, 12870, 13038, 13038, 13039, 13039, 13163, 13163, 13164, 13164, 13387, 13559, 13559, 14611, 14611, 15518, 15518, 15519, 15519, 15580, 15688, 17127, 17127, 17128, 17128, 18008, 18008
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15051-15206
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15073, 15073, 15079, 15079, 15081, 15081, 15109, 15109, 15135, 15135, 15138, 15138, 15141, 15141, 19094, 19094, 19098, 19098, 19106, 19106

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13222-13367
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13261, 13261, 13268, 13268, 13293, 13293, 13296, 13296, 13309, 13309, 13353, 13353, 13357, 13357, 13362, 13362, 13363, 13363, 13367, 13367, 19401, 19401

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13375-13519
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12596, 12596, 12772, 12772, 12850, 12850, 12855, 12855, 13404, 13404, 13410, 13410, 13416, 13416, 13422, 13422, 13428, 13428, 13434, 13434, 13440, 13440, 13446, 13446, 13452, 13452, 13458, 13458, 13464, 13464, 13470, 13470, 13476, 13476, 13482, 13482, 13488, 13488, 13494, 13494, 13500, 13500, 13506, 13506, 13512, 13512, 13518, 13518, 19014, 19014, 19155, 19155, 19157, 19157, 19272, 19272, 19398, 19398, 19399, 19399, 19400, 19400, 19419, 19419, 19420, 19420, 19421, 19421, 19422, 19422, 19423, 19423, 19424, 19424, 19425, 19425
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10542-10685
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10556, 10556, 10557, 10557, 10643, 10643, 10678, 10678, 18989, 18989, 18990, 18990, 18991, 18991, 18992, 18992, 18993, 18993

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13522-13660
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13591, 13591, 13594, 13594, 13595, 13595, 13596, 13596, 13616, 13616, 13619, 13619, 13627, 13627, 13632, 13632, 19427, 19427

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8844-8972
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8915, 8915, 8926, 8926, 15149, 15149, 15150, 15150, 18892, 18892, 18893, 18893, 19072, 19072

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11216-11344
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11223, 11223, 11228, 11228, 11229, 11229, 11230, 11230, 11233, 11233, 11234, 11234, 11297, 11297, 11304, 11304, 11331, 11331, 19371, 19371

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15674-15800
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15694, 15694, 15699, 15699, 15704, 15704, 15741, 15741, 15747, 15747, 15753, 15753, 15759, 15759, 15765, 15765, 15766, 15766, 15767, 15767, 15768, 15768, 15769, 15769, 15773, 15773, 15782, 15782, 15786, 15786, 15789, 15789, 15795, 15795, 19067, 19067

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5796-5920
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5817, 5817, 5819, 5819, 5835, 5835, 5847, 5847, 5886, 5886, 5887, 5887, 5888, 5888, 5889, 5889, 5890, 5890, 5901, 5901, 5904, 5904, 6836, 6836, 20406, 20406, 20989, 20989

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8978-9089
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7916, 7916, 9574, 9574, 9886, 9886, 10732, 10732, 10752, 10752, 12754, 15098, 15098, 15151, 15151, 15584, 15824, 15824, 15842, 15842, 15860, 15860, 17076, 17076, 17100, 17100, 17124, 17124, 17267, 17267, 17608, 17608, 18933, 18933, 18948, 18948, 18958, 18958, 18958, 18958, 18968, 18968
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10852-10960
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10907, 10907, 10910, 10910, 10911, 10911, 10916, 10916, 10934, 10934, 10934, 10943, 10943, 10943, 10943, 10944, 10944, 10944, 10944, 11002, 11002, 11005, 11005, 11017, 11017, 11018, 11018, 11031, 11031, 11070, 11070, 11078, 11078, 11132, 11132, 11140, 11140

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12777-12876
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12842, 12842, 12844, 12844, 12845, 12845, 18942, 18942, 19010, 19010, 19012, 19012, 19013, 19013

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15566-15663
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15309, 15309, 15544, 15544, 15602, 15602, 15608, 15608, 15614, 15614, 15620, 15620, 15626, 15626, 15632, 15632, 15638, 15638, 15644, 15644, 15650, 15650, 15656, 15656, 15662, 15662, 15886, 17268, 17268, 17271, 17271, 17607, 17607, 18899, 18899, 18966, 18966, 18972, 18972, 19023, 19023, 19080, 19080
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8274-8370
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8330, 8330, 8366, 8366

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11347-11440
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11399, 11399, 11412, 11412, 19002, 19002, 19044, 19044, 19045, 19045, 19050, 19050, 19051, 19051

### `ValidationUtils` (class, 90 lines)

- Def site: line 5926-6015
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6008, 6008, 15372, 15372, 15373, 15373, 15587, 18802, 18802
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12690-12774
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12724, 12724, 18977, 18977, 18985, 18985, 19011, 19011, 19156, 19156

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 18079-18157
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18074, 18074, 18075, 18075, 19251, 19251
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17054-17131
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19122, 19122, 19126, 19126, 19130, 19130
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1890-1963
- References: 258
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1903, 1903, 1935, 1935, 2210, 2210, 2299, 2299, 2326, 2326, 7628, 7628, 7714, 7714, 7844, 7844, 7921, 7921, 8004, 8004, 8234, 8234, 8423, 8423, 8479, 8479, 8492, 8492, 8509, 8509, 8554, 8554, 8585, 8585, 8591, 8591, 8694, 8694, 10235, 10235, 10502, 11004, 11004, 11033, 11033, 11298, 11298, 11504, 11504, 11743, 11743, 12459, 12459, 12475, 12475, 13262, 13262, 13681, 13681, 13731, 13731, 15585, 15787, 15787, 15820, 15820, 15838, 15838, 15856, 15856, 15884, 17081, 17081, 17106, 17106, 17149, 17248, 17248, 17460, 17460, 17603, 17603, 17649, 17649, 17739, 17739, 18069, 18069, 18099, 18099, 18120, 18120, 18139, 18139, 18155, 18155, 18172, 18172, 18749, 18749, 18769, 18769, 18804, 18804, 18817, 18817, 19285, 19285, 19376, 19376, 19381, 19381, 19387, 19387, 19406, 19406, 19412, 19412, 21012, 21012, 21110, 21110
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

- Def site: line 15212-15283
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19088, 19088, 19089, 19089, 19090, 19090, 19091, 19091

### `DisplayUtils` (class, 70 lines)

- Def site: line 5487-5556
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5519, 5519, 5520, 5520, 5535, 5535, 5537, 5537

### `ConfigUtils` (class, 70 lines)

- Def site: line 6021-6090
- References: 188
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6063, 6063, 6068, 6068, 6165, 6165, 6223, 6223, 7114, 7114, 7771, 7771, 8416, 8416, 8439, 8439, 8459, 8459, 8644, 8644, 8665, 8665, 8940, 8940, 8965, 8965, 9020, 9020, 9042, 9042, 9059, 9059, 9076, 9076, 9461, 9461, 9684, 9684, 9701, 9701, 10093, 10093, 10425, 10425, 10636, 10636, 10673, 10673, 10826, 10826, 10969, 10969, 11222, 11222, 11410, 11410, 11594, 11594, 11913, 11913, 12249, 12249, 12421, 12421, 12461, 12461, 12467, 12467, 12561, 12561, 12791, 12791, 12864, 12864, 13351, 13351, 13386, 13585, 13585, 15092, 15092, 15308, 15308, 15576, 15683, 15783, 15783, 15818, 15818, 15836, 15836, 15854, 15854, 17147, 17650, 17650, 17655, 17655, 17657, 17657, 18070, 18070, 18072, 18072, 18096, 18096, 18100, 18100, 18101, 18101, 18121, 18121, 18122, 18122, 18283, 18283, 18853, 18853, 18885, 18885, 18922, 18922, 18928, 18928, 19056, 19056, 19113, 19113, 19196, 19196, 19205, 19205, 19283, 19283, 19284, 19284, 19301, 19301, 19376, 19376, 19381, 19381, 19387, 19387, 19406, 19406, 19412, 19412, 20323, 20323, 20394, 20876, 20876, 20964, 20964
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10471-10539
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10511, 10511, 10516, 10516, 10521, 10521, 10522, 10522, 10528, 10528, 10529, 10529, 10535, 10535, 10536, 10536, 10537, 10537, 10538, 10538, 19429, 19429

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18808-18873
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18856, 18856, 18864, 18864, 18873, 18873, 19402, 19402

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15807-15862
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19027, 19027, 19031, 19031, 19236, 19236

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6096-6142
- References: 57
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6220, 6220, 8106, 8106, 9021, 9021, 9044, 9044, 9531, 9531, 9566, 9566, 9580, 9580, 9703, 9703, 9707, 9707, 10255, 10255, 12565, 12565, 13235, 13235, 13361, 13361, 13393, 13571, 13571, 13607, 13607, 15582, 17651, 17651, 17960, 17960, 18071, 18071, 18102, 18102, 18123, 18123, 19286, 19286, 19302, 19302, 20895, 20895
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5745-5790
- References: 99
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5257, 5257, 5299, 5299, 5344, 5344, 5450, 5450, 5465, 5465, 5735, 5735, 5736, 5736, 5780, 5780, 6246, 6246, 7940, 7940, 9231, 9231, 9542, 9542, 9558, 9558, 9887, 9887, 10768, 10768, 10787, 10787, 12756, 15175, 15175, 15578, 15821, 15821, 15839, 15839, 15857, 15857, 15887, 16309, 16309, 16349, 16349, 16350, 16350, 16351, 16351, 17073, 17073, 17097, 17097, 17101, 17101, 17121, 17121, 17148, 17223, 17223, 17257, 17257, 17278, 17278, 17310, 17310, 17372, 17372, 17411, 17411, 17561, 17561, 17606, 17606, 17652, 17652
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17137-17179
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17160, 17160, 17166, 17166, 17172, 17172, 17178, 17178, 19220, 19220, 19224, 19224, 19228, 19228, 19232, 19232

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11613-11652
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11650, 11650, 19426, 19426

### `TimeUtils` (class, 29 lines)

- Def site: line 1854-1882
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8894, 8894, 8895, 8895, 8924, 8924, 8925, 8925, 8941, 8941, 8942, 8942, 9820, 9820, 9821, 9821, 10125, 10125, 10126, 10126, 10173, 10173, 10174, 10174, 10729, 10729, 10731, 10731, 10749, 10749, 10751, 10751, 11639, 11639, 11640, 11640, 12300, 12300, 12301, 12301, 12406, 12406, 12407, 12407, 13389
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15536-15563
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15550, 15550, 15556, 15556, 15562, 15562, 19134, 19134, 19138, 19138
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15873-15898
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15893, 15893, 15898, 15898, 19142, 19142, 19147, 19147
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2118-2142
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2204, 2263, 17768, 20719

### `RoutingUtils` (class, 22 lines)

- Def site: line 13688-13709
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18908, 18908, 18912, 18912, 18916, 18916
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17589-17610
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17654, 17654, 19055, 19055, 19112, 19112, 19195, 19195, 19204, 19204

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 18055-18076
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19265, 19265
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7578-7598
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6329, 10098, 15421, 15586
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13934-13943
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13970, 14106, 14183, 14202, 14214, 14235, 14248, 14259, 14265, 14278, 14371, 14506, 14601

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 306-314
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

- Def site: line 333-341
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15244, 15261, 15277
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 318-325
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

- Def site: line 293-295
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13394, 13683, 18104, 18125, 18270, 18301, 18333, 18568, 18583
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 621-623
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1231, 1900, 1900, 1900, 1912, 1918, 6222, 6342, 7402, 7462, 9630, 9741, 9995, 10825, 13396, 15454, 15496, 15594, 19288
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

- Def site: line 2002-2004
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2002, 7412, 7419, 7420, 10006, 15443

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2020-2022
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2020, 15590
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 737-1741
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1786

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
