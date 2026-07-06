# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 189 first-party files
- Definitions analyzed: 94
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=13, hot=80, skipped=1

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
| `DataExporter` | class | 345 | 251 | hot |  | oversize_25_lines,non_ascii_logs |
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
| `InputUtils` | class | 74 | 259 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 8 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 189 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 57 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 100 | hot |  | oversize_25_lines,missing_inline_comments |
| `SiteConfigManager` | class | 43 | 16 | hot |  | oversize_25_lines,missing_action_logging |
| `SelfExportUtils` | class | 40 | 4 | hot |  | oversize_25_lines,non_ascii_logs |
| `BulkAPFirmwareUpgrader` | class | 32 | 2 | low-use | FirmwareManager | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `TimeUtils` | class | 29 | 51 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
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
| `main` | function | 12 | 2 | low-use | MapsManager |  |
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

## Low-Use (13)

### `BulkAPFirmwareUpgrader` (class, 32 lines)

- Def site: line 17655-17686
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

### `WANProbeDeviceOverrideManager` (class, 23 lines)

- Def site: line 17053-17075
- References: 2
- Suggested class: `WANProbeDeviceOverrideManager`
- Suggested module: `src/refactors/wanprobe_device_override_manager.py`
- Rationale: low-use: sole caller lives inside MistHelper.py; extract `WANProbeDeviceOverrideManager` OUT of the entrypoint into a new `src/refactors/wanprobe_device_override_manager.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19271, 19271

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 18187-18205
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

- Def site: line 2195-2212
- References: 3
- Suggested class: `InitializeMistSessionInteractiveManager`
- Suggested module: `src/refactors/initialize_mist_session_interactive.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `initialize_mist_session_interactive` OUT of the entrypoint into a new `src/refactors/initialize_mist_session_interactive.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2255, 17790, 20737

### `initialize_mist_session` (function, 18 lines)

- Def site: line 2821-2838
- References: 2
- Suggested class: `InitializeMistSessionManager`
- Suggested module: `src/refactors/initialize_mist_session.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_establish_mist_session()`; extract `initialize_mist_session` OUT of the entrypoint into a new `src/refactors/initialize_mist_session.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20742, 20805

### `PACKAGE_IMPORT_MAP` (assignment, 13 lines)

- Def site: line 372-384
- References: 2
- Suggested class: `PackageImportMapManager`
- Suggested module: `src/refactors/package__import__map.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_early_dependency_check()`; extract `PACKAGE_IMPORT_MAP` OUT of the entrypoint into a new `src/refactors/package__import__map.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 372, 556

### `main` (function, 12 lines)

- Def site: line 21133-21144
- References: 2
- Suggested class: `MapsManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`
- Rationale: 97 caller files detected; group callers under a shared class in `maps_manager.py` and rewrite references per file cluster
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21247
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6542-6545
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6542, 15684
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1987-1989
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1987, 9928, 15357

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1990-1992
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1990, 7418

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1995-1997
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1995, 15497

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2002-2004
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2002, 7408

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2010-2012
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2010, 15586
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (80)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2883-5209
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2883, 6588, 6589, 6598, 6762

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13943-14701
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14420, 14420, 14432, 14432, 14460, 14460, 14472, 14472, 14533, 14533, 14570, 14570, 14727, 19186

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9089-9774
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5595, 5595, 9212, 9212, 9263, 9263, 9266, 9266, 9307, 9307, 9346, 9346, 9364, 9364, 9442, 9442, 9449, 9449, 9459, 9459, 9462, 9462, 9475, 9475, 9476, 9476, 9477, 9477, 9478, 9478, 9486, 9486, 9488, 9488, 9489, 9489, 9490, 9490, 9491, 9491, 9494, 9494, 9497, 9497, 9500, 9500, 9503, 9503, 9549, 9549, 9572, 9572, 9573, 9573, 9574, 9574, 9576, 9576, 9612, 9612, 9628, 9628, 9682, 9682, 9683, 9683, 9684, 9684, 9687, 9687, 9688, 9688, 9707, 9707, 9709, 9709, 9710, 9710, 9745, 9745, 15096, 15096, 15149, 15149, 15580, 17102, 17102, 17126, 17126, 17150, 17150, 17293, 17293, 18961, 18961, 18968, 18968, 18977, 18977, 18981, 18981, 18990, 18990
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16371-17045
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16759, 16759, 19432, 19438

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11822-12474
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10599, 10599, 10608, 10608, 10696, 10696, 10703, 10703, 11377, 11377, 11663, 11663, 11668, 11668, 11675, 11675, 11680, 11680, 11894, 11894, 11916, 11916, 11919, 11919, 11945, 11945, 11954, 11954, 11955, 11955, 11976, 11976, 12019, 12019, 12065, 12065, 12076, 12076, 12103, 12103, 12108, 12108, 12109, 12109, 12110, 12110, 12142, 12142, 12148, 12148, 12173, 12173, 12193, 12193, 12228, 12228, 12243, 12243, 12249, 12249, 12251, 12251, 12254, 12254, 12256, 12256, 12260, 12260, 12264, 12264, 12269, 12269, 12276, 12276, 12283, 12283, 12290, 12290, 12299, 12299, 12309, 12309, 12316, 12316, 12323, 12323, 12330, 12330, 12337, 12337, 12344, 12344, 12354, 12354, 12363, 12363, 12372, 12372, 12381, 12381, 12390, 12390, 12419, 12419, 18922, 18922, 19103, 19103, 19180, 19180, 19181, 19181, 19189, 19189, 19394, 19394, 19395, 19395, 19414, 19414, 19421, 19421, 19422, 19422, 19423, 19423, 19424, 19424

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 18218-18804
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18495, 18495, 18496, 18496, 18499, 18499, 18501, 18501, 18503, 18503, 18519, 18519, 19339

### `menu_actions` (assignment, 572 lines)

- Def site: line 18903-19474
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18903, 20188, 20189, 20198, 20318, 20318, 20360, 20418, 20463, 20954, 20958, 21003, 21003, 21030, 21030, 21033
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8373-8835
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8414, 8414, 8419, 8419, 8429, 8429, 8437, 8437, 8442, 8442, 8447, 8447, 8457, 8457, 8462, 8462, 8467, 8467, 8487, 8487, 8497, 8497, 8498, 8498, 8501, 8501, 8531, 8531, 8617, 8617, 8619, 8619, 8643, 8643, 8649, 8649, 8654, 8654, 8663, 8663, 8667, 8667, 8686, 8686, 8689, 8689, 8700, 8700, 8701, 8701, 8796, 8796, 8817, 8817, 19462, 19462, 19463, 19463, 19464, 19464, 19465, 19465, 19466, 19466, 19467, 19467

### `OperationRegistry` (class, 461 lines)

- Def site: line 19699-20159
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20166, 20166, 20170, 20170, 20190, 20190, 20195, 20195, 20419

### `PromptUtils` (class, 441 lines)

- Def site: line 7820-8260
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7765, 7765, 7781, 7781, 7785, 7785, 7786, 7786, 7787, 7787, 7802, 7802, 7808, 7808, 7835, 7835, 7838, 7838, 7846, 7846, 7864, 7864, 7914, 7914, 7922, 7922, 7927, 7927, 7973, 7973, 7984, 7984, 8009, 8009, 8028, 8028, 8029, 8029, 8032, 8032, 8033, 8033, 8123, 8123, 8125, 8125, 8129, 8129, 8157, 8157, 8158, 8158, 8159, 8159, 8160, 8160, 8161, 8161, 8170, 8170, 8214, 8214, 8238, 8238, 12554, 12554, 12604, 12604, 12609, 12609, 12752, 12835, 12835, 12889, 12889, 12910, 12910, 12915, 12915, 13179, 13179, 13382, 13584, 13584, 13671, 13671, 13676, 13676, 13726, 13726, 13727, 13727, 15223, 15223, 15682, 17109, 17109, 17631, 17631, 18827, 18827, 18828, 18828, 19114, 19114
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9777-10190
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5589, 5589, 9810, 9810, 9894, 9894, 9900, 9900, 9903, 9903, 9947, 9947, 9961, 9961, 9988, 9988, 9994, 9994, 10008, 10008, 10091, 10091, 10093, 10093, 10097, 10097, 10099, 10099, 10102, 10102, 10106, 10106, 10109, 10109, 10119, 10119, 10125, 10125, 10163, 10163, 15097, 15097, 15098, 15098, 15099, 15099, 15150, 15150, 15151, 15151, 18962, 18962, 18963, 18963, 18964, 18964, 18988, 18988

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17212-17609
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17233, 17233, 17238, 17238, 17242, 17242, 17245, 17245, 17252, 17252, 17254, 17254, 17255, 17255, 17258, 17258, 17261, 17261, 17264, 17264, 17306, 17306, 17338, 17338, 17405, 17405, 17418, 17418, 17423, 17423, 17475, 17475, 17508, 17508, 17509, 17509, 17510, 17510, 17540, 17540, 17569, 17569, 17570, 17570, 19145, 19145

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 17692-18079
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17719, 17863, 17863, 19285, 19285

### `DataExporter` (class, 345 lines)

- Def site: line 6729-7073
- References: 251
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5685, 5685, 6775, 6775, 6791, 6791, 6792, 6792, 6815, 6815, 6817, 6817, 6820, 6820, 6834, 6834, 6836, 6836, 6845, 6845, 6847, 6847, 6848, 6848, 6854, 6854, 6855, 6855, 6855, 6872, 6872, 6876, 6876, 6918, 6918, 6949, 6949, 6952, 6952, 6954, 6954, 7000, 7000, 7010, 7010, 7043, 7043, 7048, 7048, 7055, 7055, 7277, 7277, 7309, 7309, 7320, 7320, 7345, 7345, 7365, 7365, 7877, 7877, 8670, 8670, 8949, 8949, 8964, 9028, 9028, 9045, 9045, 9063, 9063, 9084, 9084, 9643, 9643, 9718, 9718, 10048, 10048, 10399, 10399, 10484, 10500, 10620, 10620, 10624, 10624, 10644, 10644, 10657, 10657, 10661, 10661, 10679, 10679, 10841, 10841, 11188, 11188, 11335, 11335, 11412, 11412, 11416, 11416, 11421, 11421, 11554, 11554, 11573, 11573, 11624, 11624, 11627, 11627, 11778, 11778, 11781, 11781, 11880, 11880, 11886, 11886, 12183, 12183, 12200, 12200, 12215, 12215, 12429, 12429, 12457, 12457, 12473, 12473, 12510, 12510, 12548, 12548, 12637, 12637, 12666, 12666, 12704, 12704, 12755, 12820, 12820, 12826, 12826, 12868, 12868, 13037, 13037, 13043, 13043, 13162, 13162, 13170, 13170, 13334, 13334, 13385, 13558, 13558, 13729, 13729, 14242, 14242, 14603, 14603, 14609, 14609, 15517, 15517, 15576, 15683, 15819, 15819, 15837, 15837, 15855, 15855, 17070, 17156, 17156, 17177, 18045, 18045, 18130, 18130, 18151, 18151, 18653, 18653, 19314, 19314, 19330, 19330
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12876-13216
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12893, 12893, 12895, 12895, 12899, 12899, 12900, 12900, 12914, 12914, 12920, 12920, 12923, 12923, 12926, 12926, 12984, 12984, 12990, 12990, 12995, 12995, 13009, 13009, 13027, 13027, 13137, 13137, 13141, 13141, 13143, 13143, 13146, 13146, 13183, 13183, 13188, 13188, 13202, 13202, 13206, 13206, 13208, 13208, 13211, 13211, 13216, 13216, 19191, 19191, 19195, 19195, 19199, 19199

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7076-7403
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7178, 7178, 8394, 8875, 8894, 8995, 9124, 9147, 9819, 10127, 10172, 10586, 11356, 11367, 11430, 11847

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14707-15034
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12164, 12164, 12223, 12223, 12224, 12224, 13388, 14748, 14748, 14750, 14750, 14756, 14756, 14770, 14770, 14809, 14809, 14812, 14812, 14814, 14814, 14815, 14815, 14816, 14816, 14870, 14870, 14871, 14871, 14882, 14882, 14891, 14891, 14910, 14910, 14962, 14962, 14966, 14966, 14974, 14974, 14975, 14975, 14999, 14999, 15003, 15003
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16067-16355
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16095, 16095, 16098, 16098, 16103, 16103, 16106, 16106, 16150, 16150, 16156, 16156, 16187, 16187, 16190, 16190, 16194, 16194, 16220, 16220, 16237, 16237, 16243, 16243, 16257, 16257, 16258, 16258, 16260, 16260, 16266, 16266, 16273, 16273, 16282, 16282, 16329, 16329, 16351, 16351, 16352, 16352, 16353, 16353, 19136, 19136

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10193-10465
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10216, 10216, 10217, 10217, 10230, 10230, 10231, 10231, 10233, 10233, 10234, 10234, 10237, 10237, 10240, 10240, 10244, 10244, 10245, 10245, 10321, 10321, 10325, 10325, 10328, 10328, 10341, 10341, 10378, 10378, 10395, 10395, 10408, 10408, 10410, 10410, 10417, 10417, 10426, 10426, 10435, 10435, 10436, 10436, 10447, 10447, 10451, 10451, 10460, 10460, 10465, 10465, 19393, 19393

### `CacheUtils` (class, 264 lines)

- Def site: line 5215-5478
- References: 107
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5255, 5255, 5257, 5257, 5339, 5339, 5345, 5345, 5382, 5382, 5384, 5384, 5393, 5393, 5403, 5403, 5413, 5413, 5449, 5449, 7913, 7913, 9571, 9571, 9572, 9572, 9883, 9883, 10729, 10729, 10749, 10749, 12750, 15156, 15156, 15162, 15162, 15163, 15163, 15164, 15164, 15165, 15165, 15166, 15166, 15167, 15167, 15174, 15174, 15202, 15202, 15574, 15820, 15820, 15838, 15838, 15856, 15856, 15882, 17065, 17101, 17101, 17125, 17125, 17149, 17149, 17293, 17293, 17294, 17294, 17295, 17295, 17296, 17296, 17632, 17632, 18878, 18878, 19430, 19430
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10960-11210
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10967, 10967, 10970, 10970, 10975, 10975, 10976, 10976, 10984, 10984, 10987, 10987, 10995, 10995, 11035, 11035, 11043, 11043, 11091, 11091, 11108, 11108, 11111, 11111, 11113, 11113, 11177, 11177, 11178, 11178, 19396, 19396

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15286-15530
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15152, 15152, 15312, 15312, 15314, 15314, 15315, 15315, 15316, 15316, 15344, 15344, 15349, 15349, 15371, 15371, 15372, 15372, 15414, 15414, 15422, 15422, 15448, 15448, 15457, 15457, 15465, 15465, 15496, 15496, 18967, 18967, 18971, 18971

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6148-6368
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6171, 6171, 6222, 6222, 6292, 6292, 6316, 6316, 6328, 6328, 6330, 6330, 6340, 6340, 6355, 6355, 6359, 6359, 6360, 6360, 6363, 6363, 6365, 6365, 12863, 12863, 15578
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19480-19693
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20336, 20336, 20339, 20420, 20771

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7604-7813
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7617, 7617, 7623, 7623, 7624, 7624, 7627, 7627, 7650, 7650, 7653, 7653, 7656, 7656, 7657, 7657, 7659, 7659, 7726, 7726, 7770, 7770, 8235, 8235, 13184, 13184, 15681, 15920, 15920, 16080, 16080

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12482-12684
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12503, 12503, 12512, 12512, 12574, 12574, 12581, 12581, 12613, 12613, 12615, 12615, 12639, 12639, 12674, 12674, 12681, 12681, 12712, 12712, 15226, 15226, 19003, 19003, 19005, 19005, 19006, 19006, 19008, 19008

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13735-13922
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19353, 19353, 19354, 19354, 19355, 19355, 19356, 19356, 19357, 19357, 19358, 19358, 19359, 19359, 19360, 19360, 19362, 19362, 19363, 19363, 19364, 19364, 19365, 19365, 19366, 19366, 19367, 19367, 19368, 19368, 19370, 19370, 19371, 19371, 19372, 19372, 19373, 19373, 19374, 19374, 19375, 19375, 19376, 19376, 19377, 19377, 19378, 19378, 19380, 19380, 19381, 19381, 19382, 19382, 19383, 19383, 19384, 19384, 19385, 19385, 19386, 19386, 19387, 19387, 19388, 19388, 19390, 19390, 19391, 19391

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5560-5739
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5648, 5648, 5685, 5685, 5687, 5687, 5690, 5690, 5698, 5698, 5700, 5700, 5702, 5702, 5705, 5705, 5734, 5734, 5737, 5737, 19130, 19130

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6548-6726
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6593, 6593, 6631, 6631, 6642, 6642, 6668, 6668, 6669, 6669, 6671, 6671, 6677, 6677, 6678, 6678, 6681, 6681, 6687, 6687, 6688, 6688, 6691, 6691, 6693, 6693, 6703, 6703, 6705, 6705, 6706, 6706, 6708, 6708

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11440-11607
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11547, 11547, 11566, 11566, 11584, 11584, 11593, 11593, 11596, 11596, 11597, 11597, 11600, 11600, 11605, 11605, 11607, 11607, 19031, 19031

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11652-11819
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11689, 11689, 11691, 11691, 11694, 11694, 11765, 11765, 11767, 11767, 11780, 11780, 11784, 11784, 19034, 19034, 19035, 19035, 19036, 19036, 19074, 19074, 19079, 19079

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10685-10846
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10723, 10723, 10730, 10730, 10737, 10737, 10743, 10743, 10750, 10750, 10757, 10757, 10818, 10818, 10829, 10829, 19022, 19022, 19023, 19023, 19025, 19025, 19026, 19026, 19027, 19027

### `CLIShellManager` (class, 161 lines)

- Def site: line 15901-16061
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15924, 15924, 15926, 15926, 15995, 15995, 15997, 15997, 16016, 16016, 16018, 16018, 16018, 16034, 16034, 16050, 16050, 16051, 16051, 16057, 16057, 19135, 19135

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6376-6533
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5513, 5513, 6392, 6392, 6405, 6405, 6408, 6408, 6432, 6432, 6440, 6440, 6441, 6441, 6463, 6463, 6468, 6468, 6470, 6470, 6543, 6543, 6544, 6544, 6951, 6951, 6976, 6976, 7045, 7045, 7046, 7046, 7375, 7375, 7389, 7389, 7390, 7390, 7875, 7875, 7876, 7876, 8798, 8798, 8963, 9023, 9023, 9025, 9025, 9026, 9026, 9043, 9043, 9044, 9044, 9061, 9061, 9062, 9062, 9082, 9082, 9083, 9083, 9640, 9640, 9641, 9641, 9715, 9715, 9716, 9716, 10044, 10044, 10047, 10047, 10622, 10622, 10623, 10623, 10659, 10659, 10660, 10660, 10839, 10839, 10840, 10840, 11184, 11184, 11185, 11185, 11331, 11331, 11332, 11332, 11414, 11414, 11415, 11415, 11626, 11626, 11801, 11801, 11802, 11802, 11878, 11878, 11879, 11879, 12182, 12182, 12198, 12198, 12199, 12199, 12427, 12427, 12428, 12428, 12507, 12507, 12508, 12508, 12509, 12509, 12545, 12545, 12546, 12546, 12634, 12634, 12635, 12635, 12663, 12663, 12664, 12664, 12701, 12701, 12702, 12702, 12754, 12823, 12823, 12824, 12824, 12866, 12866, 12867, 12867, 13035, 13035, 13036, 13036, 13160, 13160, 13161, 13161, 13384, 13556, 13556, 14608, 14608, 15515, 15515, 15516, 15516, 15577, 15685, 17154, 17154, 17155, 17155, 18035, 18035
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15048-15203
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15070, 15070, 15076, 15076, 15078, 15078, 15106, 15106, 15132, 15132, 15135, 15135, 15138, 15138, 19121, 19121, 19125, 19125, 19133, 19133

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13219-13364
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13258, 13258, 13265, 13265, 13290, 13290, 13293, 13293, 13306, 13306, 13350, 13350, 13354, 13354, 13359, 13359, 13360, 13360, 13364, 13364, 19428, 19428

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13372-13516
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12593, 12593, 12769, 12769, 12847, 12847, 12852, 12852, 13401, 13401, 13407, 13407, 13413, 13413, 13419, 13419, 13425, 13425, 13431, 13431, 13437, 13437, 13443, 13443, 13449, 13449, 13455, 13455, 13461, 13461, 13467, 13467, 13473, 13473, 13479, 13479, 13485, 13485, 13491, 13491, 13497, 13497, 13503, 13503, 13509, 13509, 13515, 13515, 19041, 19041, 19182, 19182, 19184, 19184, 19299, 19299, 19425, 19425, 19426, 19426, 19427, 19427, 19446, 19446, 19447, 19447, 19448, 19448, 19449, 19449, 19450, 19450, 19451, 19451, 19452, 19452
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10539-10682
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10553, 10553, 10554, 10554, 10640, 10640, 10675, 10675, 19016, 19016, 19017, 19017, 19018, 19018, 19019, 19019, 19020, 19020

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13519-13657
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13588, 13588, 13591, 13591, 13592, 13592, 13593, 13593, 13613, 13613, 13616, 13616, 13624, 13624, 13629, 13629, 19454, 19454

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8841-8969
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8912, 8912, 8923, 8923, 15146, 15146, 15147, 15147, 18919, 18919, 18920, 18920, 19099, 19099

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11213-11341
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11220, 11220, 11225, 11225, 11226, 11226, 11227, 11227, 11230, 11230, 11231, 11231, 11294, 11294, 11301, 11301, 11328, 11328, 19398, 19398

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15671-15797
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15691, 15691, 15696, 15696, 15701, 15701, 15738, 15738, 15744, 15744, 15750, 15750, 15756, 15756, 15762, 15762, 15763, 15763, 15764, 15764, 15765, 15765, 15766, 15766, 15770, 15770, 15779, 15779, 15783, 15783, 15786, 15786, 15792, 15792, 19094, 19094

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5793-5917
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5814, 5814, 5816, 5816, 5832, 5832, 5844, 5844, 5883, 5883, 5884, 5884, 5885, 5885, 5886, 5886, 5887, 5887, 5898, 5898, 5901, 5901, 6833, 6833, 20433, 20433, 21016, 21016

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8975-9086
- References: 53
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7913, 7913, 9571, 9571, 9883, 9883, 10729, 10729, 10749, 10749, 12751, 15095, 15095, 15148, 15148, 15581, 15821, 15821, 15839, 15839, 15857, 15857, 17066, 17103, 17103, 17127, 17127, 17151, 17151, 17294, 17294, 17635, 17635, 18960, 18960, 18975, 18975, 18985, 18985, 18985, 18985, 18995, 18995
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10849-10957
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10904, 10904, 10907, 10907, 10908, 10908, 10913, 10913, 10931, 10931, 10931, 10940, 10940, 10940, 10940, 10941, 10941, 10941, 10941, 10999, 10999, 11002, 11002, 11014, 11014, 11015, 11015, 11028, 11028, 11067, 11067, 11075, 11075, 11129, 11129, 11137, 11137

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12774-12873
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12839, 12839, 12841, 12841, 12842, 12842, 18969, 18969, 19037, 19037, 19039, 19039, 19040, 19040

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15563-15660
- References: 79
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15306, 15306, 15541, 15541, 15599, 15599, 15605, 15605, 15611, 15611, 15617, 15617, 15623, 15623, 15629, 15629, 15635, 15635, 15641, 15641, 15647, 15647, 15653, 15653, 15659, 15659, 15883, 17067, 17295, 17295, 17298, 17298, 17634, 17634, 18926, 18926, 18993, 18993, 18999, 18999, 19050, 19050, 19107, 19107
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8271-8367
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8327, 8327, 8363, 8363

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11344-11437
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11396, 11396, 11409, 11409, 19029, 19029, 19071, 19071, 19072, 19072, 19077, 19077, 19078, 19078

### `ValidationUtils` (class, 90 lines)

- Def site: line 5923-6012
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6005, 6005, 15369, 15369, 15370, 15370, 15584, 18829, 18829
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12687-12771
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12721, 12721, 19004, 19004, 19012, 19012, 19038, 19038, 19183, 19183

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 18106-18184
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18101, 18101, 18102, 18102, 19278, 19278
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17081-17158
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19149, 19149, 19153, 19153, 19157, 19157
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1887-1960
- References: 259
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1900, 1900, 1932, 1932, 2207, 2207, 2296, 2296, 2323, 2323, 7625, 7625, 7711, 7711, 7841, 7841, 7918, 7918, 8001, 8001, 8231, 8231, 8420, 8420, 8476, 8476, 8489, 8489, 8506, 8506, 8551, 8551, 8582, 8582, 8588, 8588, 8691, 8691, 10232, 10232, 10499, 11001, 11001, 11030, 11030, 11295, 11295, 11501, 11501, 11740, 11740, 12456, 12456, 12472, 12472, 13259, 13259, 13678, 13678, 13728, 13728, 15582, 15784, 15784, 15817, 15817, 15835, 15835, 15853, 15853, 15881, 17069, 17108, 17108, 17133, 17133, 17176, 17275, 17275, 17487, 17487, 17630, 17630, 17676, 17676, 17766, 17766, 18096, 18096, 18126, 18126, 18147, 18147, 18166, 18166, 18182, 18182, 18199, 18199, 18776, 18776, 18796, 18796, 18831, 18831, 18844, 18844, 19312, 19312, 19403, 19403, 19408, 19408, 19414, 19414, 19433, 19433, 19439, 19439, 21039, 21039, 21137, 21137
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

- Def site: line 15209-15280
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19115, 19115, 19116, 19116, 19117, 19117, 19118, 19118

### `DisplayUtils` (class, 70 lines)

- Def site: line 5484-5553
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5516, 5516, 5517, 5517, 5532, 5532, 5534, 5534

### `ConfigUtils` (class, 70 lines)

- Def site: line 6018-6087
- References: 189
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6060, 6060, 6065, 6065, 6162, 6162, 6220, 6220, 7111, 7111, 7768, 7768, 8413, 8413, 8436, 8436, 8456, 8456, 8641, 8641, 8662, 8662, 8937, 8937, 8962, 8962, 9017, 9017, 9039, 9039, 9056, 9056, 9073, 9073, 9458, 9458, 9681, 9681, 9698, 9698, 10090, 10090, 10422, 10422, 10633, 10633, 10670, 10670, 10823, 10823, 10966, 10966, 11219, 11219, 11407, 11407, 11591, 11591, 11910, 11910, 12246, 12246, 12418, 12418, 12458, 12458, 12464, 12464, 12558, 12558, 12788, 12788, 12861, 12861, 13348, 13348, 13383, 13582, 13582, 15089, 15089, 15305, 15305, 15573, 15680, 15780, 15780, 15815, 15815, 15833, 15833, 15851, 15851, 17064, 17174, 17677, 17677, 17682, 17682, 17684, 17684, 18097, 18097, 18099, 18099, 18123, 18123, 18127, 18127, 18128, 18128, 18148, 18148, 18149, 18149, 18310, 18310, 18880, 18880, 18912, 18912, 18949, 18949, 18955, 18955, 19083, 19083, 19140, 19140, 19223, 19223, 19232, 19232, 19310, 19310, 19311, 19311, 19328, 19328, 19403, 19403, 19408, 19408, 19414, 19414, 19433, 19433, 19439, 19439, 20350, 20350, 20421, 20903, 20903, 20991, 20991
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10468-10536
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10508, 10508, 10513, 10513, 10518, 10518, 10519, 10519, 10525, 10525, 10526, 10526, 10532, 10532, 10533, 10533, 10534, 10534, 10535, 10535, 19456, 19456

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18835-18900
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18883, 18883, 18891, 18891, 18900, 18900, 19429, 19429

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15804-15859
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19054, 19054, 19058, 19058, 19263, 19263

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6093-6139
- References: 57
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6217, 6217, 8103, 8103, 9018, 9018, 9041, 9041, 9528, 9528, 9563, 9563, 9577, 9577, 9700, 9700, 9704, 9704, 10252, 10252, 12562, 12562, 13232, 13232, 13358, 13358, 13390, 13568, 13568, 13604, 13604, 15579, 17678, 17678, 17987, 17987, 18098, 18098, 18129, 18129, 18150, 18150, 19313, 19313, 19329, 19329, 20922, 20922
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5742-5787
- References: 100
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5254, 5254, 5296, 5296, 5341, 5341, 5447, 5447, 5462, 5462, 5732, 5732, 5733, 5733, 5777, 5777, 6243, 6243, 7937, 7937, 9228, 9228, 9539, 9539, 9555, 9555, 9884, 9884, 10765, 10765, 10784, 10784, 12753, 15172, 15172, 15575, 15818, 15818, 15836, 15836, 15854, 15854, 15884, 16306, 16306, 16346, 16346, 16347, 16347, 16348, 16348, 17068, 17100, 17100, 17124, 17124, 17128, 17128, 17148, 17148, 17175, 17250, 17250, 17284, 17284, 17305, 17305, 17337, 17337, 17399, 17399, 17438, 17438, 17588, 17588, 17633, 17633, 17679, 17679
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17164-17206
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17187, 17187, 17193, 17193, 17199, 17199, 17205, 17205, 19247, 19247, 19251, 19251, 19255, 19255, 19259, 19259

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11610-11649
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11647, 11647, 19453, 19453

### `TimeUtils` (class, 29 lines)

- Def site: line 1851-1879
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8891, 8891, 8892, 8892, 8921, 8921, 8922, 8922, 8938, 8938, 8939, 8939, 9817, 9817, 9818, 9818, 10122, 10122, 10123, 10123, 10170, 10170, 10171, 10171, 10726, 10726, 10728, 10728, 10746, 10746, 10748, 10748, 11636, 11636, 11637, 11637, 12297, 12297, 12298, 12298, 12403, 12403, 12404, 12404, 13386
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15533-15560
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15547, 15547, 15553, 15553, 15559, 15559, 19161, 19161, 19165, 19165
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15870-15895
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15890, 15890, 15895, 15895, 19169, 19169, 19174, 19174
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2115-2139
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2201, 2260, 17795, 20746

### `RoutingUtils` (class, 22 lines)

- Def site: line 13685-13706
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18935, 18935, 18939, 18939, 18943, 18943
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17616-17637
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17681, 17681, 19082, 19082, 19139, 19139, 19222, 19222, 19231, 19231

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 18082-18103
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19292, 19292
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7575-7595
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6326, 10095, 15418, 15583
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13931-13940
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13967, 14103, 14180, 14199, 14211, 14232, 14245, 14256, 14262, 14275, 14368, 14503, 14598

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 303-311
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

- Def site: line 330-338
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15241, 15258, 15274
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 315-322
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

- Def site: line 290-292
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13391, 13680, 18131, 18152, 18297, 18328, 18360, 18595, 18610
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 618-620
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1228, 1897, 1897, 1897, 1909, 1915, 6219, 6339, 7399, 7459, 9627, 9738, 9992, 10822, 13393, 15451, 15493, 15591, 19315
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

- Def site: line 1999-2001
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1999, 7409, 7416, 7417, 10003, 15440

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2017-2019
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2017, 15587, 17072
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 734-1738
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1783

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
