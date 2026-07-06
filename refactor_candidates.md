# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 193 first-party files
- Definitions analyzed: 89
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=9, hot=79, skipped=1

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
| `InputUtils` | class | 74 | 254 | hot |  | oversize_25_lines,raw_input_call |
| `InteractiveDisplayUtils` | class | 72 | 8 | hot |  | oversize_25_lines,missing_inline_comments |
| `DisplayUtils` | class | 70 | 8 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `ConfigUtils` | class | 70 | 182 | hot |  | oversize_25_lines |
| `OrgDeviceInventorySummary` | class | 69 | 22 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `AuditAnalysisOps` | class | 66 | 8 | hot |  | oversize_25_lines,missing_inline_comments,raw_input_call |
| `GatewayTemplateConfigManager` | class | 56 | 6 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `APICoreFetchUtils` | class | 47 | 55 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 97 | hot |  | oversize_25_lines,missing_inline_comments |
| `SiteConfigManager` | class | 43 | 16 | hot |  | oversize_25_lines,missing_action_logging |
| `SelfExportUtils` | class | 40 | 4 | hot |  | oversize_25_lines,non_ascii_logs |
| `TimeUtils` | class | 29 | 51 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
| `SSHRunnerManager` | class | 26 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 3 | low-use | DetectMspPrivilegesManager | missing_action_logging |
| `RoutingUtils` | class | 22 | 12 | hot |  | missing_inline_comments,missing_action_logging |
| `FirmwareManager` | class | 22 | 8 | hot |  |  |
| `SiteAutoUpgradeConfigurator` | class | 22 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `execute_with_connection_pool_management` | function | 21 | 7 | hot |  |  |
| `BulkSwitchFirmwareUpgrader` | class | 19 | 2 | low-use | FirmwareManager | missing_inline_comments,missing_action_logging |
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
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Low-Use (9)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2116-2140
- References: 3
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2246, 17707, 20658

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 18099-18117
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1880, 1881

### `main` (function, 12 lines)

- Def site: line 21045-21056
- References: 2
- Suggested class: `MapsManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`
- Rationale: 97 caller files detected; group callers under a shared class in `maps_manager.py` and rewrite references per file cluster
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 21159
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 2794

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6513-6516
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6513, 15655
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1988-1990
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1988, 9899, 15328

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1991-1993
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1991, 7389

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1996-1998
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1996, 15468

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2003-2005
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2003, 7379

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2011-2013
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2011, 15557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (79)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2854-5180
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2854, 6559, 6560, 6569, 6733

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13914-14672
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14391, 14391, 14403, 14403, 14431, 14431, 14443, 14443, 14504, 14504, 14541, 14541, 14698, 19098

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9060-9745
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5566, 5566, 9183, 9183, 9234, 9234, 9237, 9237, 9278, 9278, 9317, 9317, 9335, 9335, 9413, 9413, 9420, 9420, 9430, 9430, 9433, 9433, 9446, 9446, 9447, 9447, 9448, 9448, 9449, 9449, 9457, 9457, 9459, 9459, 9460, 9460, 9461, 9461, 9462, 9462, 9465, 9465, 9468, 9468, 9471, 9471, 9474, 9474, 9520, 9520, 9543, 9543, 9544, 9544, 9545, 9545, 9547, 9547, 9583, 9583, 9599, 9599, 9653, 9653, 9654, 9654, 9655, 9655, 9658, 9658, 9659, 9659, 9678, 9678, 9680, 9680, 9681, 9681, 9716, 9716, 15067, 15067, 15120, 15120, 15551, 17043, 17043, 17067, 17067, 17091, 17091, 17234, 17234, 18873, 18873, 18880, 18880, 18889, 18889, 18893, 18893, 18902, 18902
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16342-17016
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16730, 16730, 19344, 19350

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11793-12445
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10570, 10570, 10579, 10579, 10667, 10667, 10674, 10674, 11348, 11348, 11634, 11634, 11639, 11639, 11646, 11646, 11651, 11651, 11865, 11865, 11887, 11887, 11890, 11890, 11916, 11916, 11925, 11925, 11926, 11926, 11947, 11947, 11990, 11990, 12036, 12036, 12047, 12047, 12074, 12074, 12079, 12079, 12080, 12080, 12081, 12081, 12113, 12113, 12119, 12119, 12144, 12144, 12164, 12164, 12199, 12199, 12214, 12214, 12220, 12220, 12222, 12222, 12225, 12225, 12227, 12227, 12231, 12231, 12235, 12235, 12240, 12240, 12247, 12247, 12254, 12254, 12261, 12261, 12270, 12270, 12280, 12280, 12287, 12287, 12294, 12294, 12301, 12301, 12308, 12308, 12315, 12315, 12325, 12325, 12334, 12334, 12343, 12343, 12352, 12352, 12361, 12361, 12390, 12390, 18834, 18834, 19015, 19015, 19092, 19092, 19093, 19093, 19101, 19101, 19306, 19306, 19307, 19307, 19326, 19326, 19333, 19333, 19334, 19334, 19335, 19335, 19336, 19336

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 18130-18716
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18407, 18407, 18408, 18408, 18411, 18411, 18413, 18413, 18415, 18415, 18431, 18431, 19251

### `menu_actions` (assignment, 572 lines)

- Def site: line 18815-19386
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18815, 20100, 20101, 20110, 20230, 20230, 20272, 20330, 20375, 20866, 20870, 20915, 20915, 20942, 20942, 20945
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8344-8806
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8385, 8385, 8390, 8390, 8400, 8400, 8408, 8408, 8413, 8413, 8418, 8418, 8428, 8428, 8433, 8433, 8438, 8438, 8458, 8458, 8468, 8468, 8469, 8469, 8472, 8472, 8502, 8502, 8588, 8588, 8590, 8590, 8614, 8614, 8620, 8620, 8625, 8625, 8634, 8634, 8638, 8638, 8657, 8657, 8660, 8660, 8671, 8671, 8672, 8672, 8767, 8767, 8788, 8788, 19374, 19374, 19375, 19375, 19376, 19376, 19377, 19377, 19378, 19378, 19379, 19379

### `OperationRegistry` (class, 461 lines)

- Def site: line 19611-20071
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20078, 20078, 20082, 20082, 20102, 20102, 20107, 20107, 20331

### `PromptUtils` (class, 441 lines)

- Def site: line 7791-8231
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7736, 7736, 7752, 7752, 7756, 7756, 7757, 7757, 7758, 7758, 7773, 7773, 7779, 7779, 7806, 7806, 7809, 7809, 7817, 7817, 7835, 7835, 7885, 7885, 7893, 7893, 7898, 7898, 7944, 7944, 7955, 7955, 7980, 7980, 7999, 7999, 8000, 8000, 8003, 8003, 8004, 8004, 8094, 8094, 8096, 8096, 8100, 8100, 8128, 8128, 8129, 8129, 8130, 8130, 8131, 8131, 8132, 8132, 8141, 8141, 8185, 8185, 8209, 8209, 12525, 12525, 12575, 12575, 12580, 12580, 12723, 12806, 12806, 12860, 12860, 12881, 12881, 12886, 12886, 13150, 13150, 13353, 13555, 13555, 13642, 13642, 13647, 13647, 13697, 13697, 13698, 13698, 15194, 15194, 15653, 17050, 17050, 17572, 17572, 18739, 18739, 18740, 18740, 19026, 19026
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9748-10161
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5560, 5560, 9781, 9781, 9865, 9865, 9871, 9871, 9874, 9874, 9918, 9918, 9932, 9932, 9959, 9959, 9965, 9965, 9979, 9979, 10062, 10062, 10064, 10064, 10068, 10068, 10070, 10070, 10073, 10073, 10077, 10077, 10080, 10080, 10090, 10090, 10096, 10096, 10134, 10134, 15068, 15068, 15069, 15069, 15070, 15070, 15121, 15121, 15122, 15122, 18874, 18874, 18875, 18875, 18876, 18876, 18900, 18900

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17153-17550
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17174, 17174, 17179, 17179, 17183, 17183, 17186, 17186, 17193, 17193, 17195, 17195, 17196, 17196, 17199, 17199, 17202, 17202, 17205, 17205, 17247, 17247, 17279, 17279, 17346, 17346, 17359, 17359, 17364, 17364, 17416, 17416, 17449, 17449, 17450, 17450, 17451, 17451, 17481, 17481, 17510, 17510, 17511, 17511, 19057, 19057

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 17604-17991
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17631, 17775, 17775, 19197, 19197

### `DataExporter` (class, 345 lines)

- Def site: line 6700-7044
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5656, 5656, 6746, 6746, 6762, 6762, 6763, 6763, 6786, 6786, 6788, 6788, 6791, 6791, 6805, 6805, 6807, 6807, 6816, 6816, 6818, 6818, 6819, 6819, 6825, 6825, 6826, 6826, 6826, 6843, 6843, 6847, 6847, 6889, 6889, 6920, 6920, 6923, 6923, 6925, 6925, 6971, 6971, 6981, 6981, 7014, 7014, 7019, 7019, 7026, 7026, 7248, 7248, 7280, 7280, 7291, 7291, 7316, 7316, 7336, 7336, 7848, 7848, 8641, 8641, 8920, 8920, 8935, 8999, 8999, 9016, 9016, 9034, 9034, 9055, 9055, 9614, 9614, 9689, 9689, 10019, 10019, 10370, 10370, 10455, 10471, 10591, 10591, 10595, 10595, 10615, 10615, 10628, 10628, 10632, 10632, 10650, 10650, 10812, 10812, 11159, 11159, 11306, 11306, 11383, 11383, 11387, 11387, 11392, 11392, 11525, 11525, 11544, 11544, 11595, 11595, 11598, 11598, 11749, 11749, 11752, 11752, 11851, 11851, 11857, 11857, 12154, 12154, 12171, 12171, 12186, 12186, 12400, 12400, 12428, 12428, 12444, 12444, 12481, 12481, 12519, 12519, 12608, 12608, 12637, 12637, 12675, 12675, 12726, 12791, 12791, 12797, 12797, 12839, 12839, 13008, 13008, 13014, 13014, 13133, 13133, 13141, 13141, 13305, 13305, 13356, 13529, 13529, 13700, 13700, 14213, 14213, 14574, 14574, 14580, 14580, 15488, 15488, 15547, 15654, 15790, 15790, 15808, 15808, 15826, 15826, 17097, 17097, 17118, 17957, 17957, 18042, 18042, 18063, 18063, 18565, 18565, 19226, 19226, 19242, 19242
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12847-13187
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12864, 12864, 12866, 12866, 12870, 12870, 12871, 12871, 12885, 12885, 12891, 12891, 12894, 12894, 12897, 12897, 12955, 12955, 12961, 12961, 12966, 12966, 12980, 12980, 12998, 12998, 13108, 13108, 13112, 13112, 13114, 13114, 13117, 13117, 13154, 13154, 13159, 13159, 13173, 13173, 13177, 13177, 13179, 13179, 13182, 13182, 13187, 13187, 19103, 19103, 19107, 19107, 19111, 19111

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7047-7374
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7149, 7149, 8365, 8846, 8865, 8966, 9095, 9118, 9790, 10098, 10143, 10557, 11327, 11338, 11401, 11818

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14678-15005
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12135, 12135, 12194, 12194, 12195, 12195, 13359, 14719, 14719, 14721, 14721, 14727, 14727, 14741, 14741, 14780, 14780, 14783, 14783, 14785, 14785, 14786, 14786, 14787, 14787, 14841, 14841, 14842, 14842, 14853, 14853, 14862, 14862, 14881, 14881, 14933, 14933, 14937, 14937, 14945, 14945, 14946, 14946, 14970, 14970, 14974, 14974
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16038-16326
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16066, 16066, 16069, 16069, 16074, 16074, 16077, 16077, 16121, 16121, 16127, 16127, 16158, 16158, 16161, 16161, 16165, 16165, 16191, 16191, 16208, 16208, 16214, 16214, 16228, 16228, 16229, 16229, 16231, 16231, 16237, 16237, 16244, 16244, 16253, 16253, 16300, 16300, 16322, 16322, 16323, 16323, 16324, 16324, 19048, 19048

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10164-10436
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10187, 10187, 10188, 10188, 10201, 10201, 10202, 10202, 10204, 10204, 10205, 10205, 10208, 10208, 10211, 10211, 10215, 10215, 10216, 10216, 10292, 10292, 10296, 10296, 10299, 10299, 10312, 10312, 10349, 10349, 10366, 10366, 10379, 10379, 10381, 10381, 10388, 10388, 10397, 10397, 10406, 10406, 10407, 10407, 10418, 10418, 10422, 10422, 10431, 10431, 10436, 10436, 19305, 19305

### `CacheUtils` (class, 264 lines)

- Def site: line 5186-5449
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5226, 5226, 5228, 5228, 5310, 5310, 5316, 5316, 5353, 5353, 5355, 5355, 5364, 5364, 5374, 5374, 5384, 5384, 5420, 5420, 7884, 7884, 9542, 9542, 9543, 9543, 9854, 9854, 10700, 10700, 10720, 10720, 12721, 15127, 15127, 15133, 15133, 15134, 15134, 15135, 15135, 15136, 15136, 15137, 15137, 15138, 15138, 15145, 15145, 15173, 15173, 15545, 15791, 15791, 15809, 15809, 15827, 15827, 15853, 17042, 17042, 17066, 17066, 17090, 17090, 17234, 17234, 17235, 17235, 17236, 17236, 17237, 17237, 17573, 17573, 18790, 18790, 19342, 19342
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10931-11181
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10938, 10938, 10941, 10941, 10946, 10946, 10947, 10947, 10955, 10955, 10958, 10958, 10966, 10966, 11006, 11006, 11014, 11014, 11062, 11062, 11079, 11079, 11082, 11082, 11084, 11084, 11148, 11148, 11149, 11149, 19308, 19308

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15257-15501
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15123, 15123, 15283, 15283, 15285, 15285, 15286, 15286, 15287, 15287, 15315, 15315, 15320, 15320, 15342, 15342, 15343, 15343, 15385, 15385, 15393, 15393, 15419, 15419, 15428, 15428, 15436, 15436, 15467, 15467, 18879, 18879, 18883, 18883

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6119-6339
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6142, 6142, 6193, 6193, 6263, 6263, 6287, 6287, 6299, 6299, 6301, 6301, 6311, 6311, 6326, 6326, 6330, 6330, 6331, 6331, 6334, 6334, 6336, 6336, 12834, 12834, 15549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19392-19605
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20248, 20248, 20251, 20332, 20683

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7575-7784
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7588, 7588, 7594, 7594, 7595, 7595, 7598, 7598, 7621, 7621, 7624, 7624, 7627, 7627, 7628, 7628, 7630, 7630, 7697, 7697, 7741, 7741, 8206, 8206, 13155, 13155, 15652, 15891, 15891, 16051, 16051

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12453-12655
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12474, 12474, 12483, 12483, 12545, 12545, 12552, 12552, 12584, 12584, 12586, 12586, 12610, 12610, 12645, 12645, 12652, 12652, 12683, 12683, 15197, 15197, 18915, 18915, 18917, 18917, 18918, 18918, 18920, 18920

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13706-13893
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19265, 19265, 19266, 19266, 19267, 19267, 19268, 19268, 19269, 19269, 19270, 19270, 19271, 19271, 19272, 19272, 19274, 19274, 19275, 19275, 19276, 19276, 19277, 19277, 19278, 19278, 19279, 19279, 19280, 19280, 19282, 19282, 19283, 19283, 19284, 19284, 19285, 19285, 19286, 19286, 19287, 19287, 19288, 19288, 19289, 19289, 19290, 19290, 19292, 19292, 19293, 19293, 19294, 19294, 19295, 19295, 19296, 19296, 19297, 19297, 19298, 19298, 19299, 19299, 19300, 19300, 19302, 19302, 19303, 19303

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5531-5710
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5619, 5619, 5656, 5656, 5658, 5658, 5661, 5661, 5669, 5669, 5671, 5671, 5673, 5673, 5676, 5676, 5705, 5705, 5708, 5708, 19042, 19042

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6519-6697
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6564, 6564, 6602, 6602, 6613, 6613, 6639, 6639, 6640, 6640, 6642, 6642, 6648, 6648, 6649, 6649, 6652, 6652, 6658, 6658, 6659, 6659, 6662, 6662, 6664, 6664, 6674, 6674, 6676, 6676, 6677, 6677, 6679, 6679

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11411-11578
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11518, 11518, 11537, 11537, 11555, 11555, 11564, 11564, 11567, 11567, 11568, 11568, 11571, 11571, 11576, 11576, 11578, 11578, 18943, 18943

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11623-11790
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11660, 11660, 11662, 11662, 11665, 11665, 11736, 11736, 11738, 11738, 11751, 11751, 11755, 11755, 18946, 18946, 18947, 18947, 18948, 18948, 18986, 18986, 18991, 18991

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10656-10817
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10694, 10694, 10701, 10701, 10708, 10708, 10714, 10714, 10721, 10721, 10728, 10728, 10789, 10789, 10800, 10800, 18934, 18934, 18935, 18935, 18937, 18937, 18938, 18938, 18939, 18939

### `CLIShellManager` (class, 161 lines)

- Def site: line 15872-16032
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15895, 15895, 15897, 15897, 15966, 15966, 15968, 15968, 15987, 15987, 15989, 15989, 15989, 16005, 16005, 16021, 16021, 16022, 16022, 16028, 16028, 19047, 19047

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6347-6504
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5484, 5484, 6363, 6363, 6376, 6376, 6379, 6379, 6403, 6403, 6411, 6411, 6412, 6412, 6434, 6434, 6439, 6439, 6441, 6441, 6514, 6514, 6515, 6515, 6922, 6922, 6947, 6947, 7016, 7016, 7017, 7017, 7346, 7346, 7360, 7360, 7361, 7361, 7846, 7846, 7847, 7847, 8769, 8769, 8934, 8994, 8994, 8996, 8996, 8997, 8997, 9014, 9014, 9015, 9015, 9032, 9032, 9033, 9033, 9053, 9053, 9054, 9054, 9611, 9611, 9612, 9612, 9686, 9686, 9687, 9687, 10015, 10015, 10018, 10018, 10593, 10593, 10594, 10594, 10630, 10630, 10631, 10631, 10810, 10810, 10811, 10811, 11155, 11155, 11156, 11156, 11302, 11302, 11303, 11303, 11385, 11385, 11386, 11386, 11597, 11597, 11772, 11772, 11773, 11773, 11849, 11849, 11850, 11850, 12153, 12153, 12169, 12169, 12170, 12170, 12398, 12398, 12399, 12399, 12478, 12478, 12479, 12479, 12480, 12480, 12516, 12516, 12517, 12517, 12605, 12605, 12606, 12606, 12634, 12634, 12635, 12635, 12672, 12672, 12673, 12673, 12725, 12794, 12794, 12795, 12795, 12837, 12837, 12838, 12838, 13006, 13006, 13007, 13007, 13131, 13131, 13132, 13132, 13355, 13527, 13527, 14579, 14579, 15486, 15486, 15487, 15487, 15548, 15656, 17095, 17095, 17096, 17096, 17947, 17947
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15019-15174
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15041, 15041, 15047, 15047, 15049, 15049, 15077, 15077, 15103, 15103, 15106, 15106, 15109, 15109, 19033, 19033, 19037, 19037, 19045, 19045

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13190-13335
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13229, 13229, 13236, 13236, 13261, 13261, 13264, 13264, 13277, 13277, 13321, 13321, 13325, 13325, 13330, 13330, 13331, 13331, 13335, 13335, 19340, 19340

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13343-13487
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12564, 12564, 12740, 12740, 12818, 12818, 12823, 12823, 13372, 13372, 13378, 13378, 13384, 13384, 13390, 13390, 13396, 13396, 13402, 13402, 13408, 13408, 13414, 13414, 13420, 13420, 13426, 13426, 13432, 13432, 13438, 13438, 13444, 13444, 13450, 13450, 13456, 13456, 13462, 13462, 13468, 13468, 13474, 13474, 13480, 13480, 13486, 13486, 18953, 18953, 19094, 19094, 19096, 19096, 19211, 19211, 19337, 19337, 19338, 19338, 19339, 19339, 19358, 19358, 19359, 19359, 19360, 19360, 19361, 19361, 19362, 19362, 19363, 19363, 19364, 19364
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10510-10653
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10524, 10524, 10525, 10525, 10611, 10611, 10646, 10646, 18928, 18928, 18929, 18929, 18930, 18930, 18931, 18931, 18932, 18932

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13490-13628
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13559, 13559, 13562, 13562, 13563, 13563, 13564, 13564, 13584, 13584, 13587, 13587, 13595, 13595, 13600, 13600, 19366, 19366

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8812-8940
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8883, 8883, 8894, 8894, 15117, 15117, 15118, 15118, 18831, 18831, 18832, 18832, 19011, 19011

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11184-11312
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11191, 11191, 11196, 11196, 11197, 11197, 11198, 11198, 11201, 11201, 11202, 11202, 11265, 11265, 11272, 11272, 11299, 11299, 19310, 19310

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15642-15768
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15662, 15662, 15667, 15667, 15672, 15672, 15709, 15709, 15715, 15715, 15721, 15721, 15727, 15727, 15733, 15733, 15734, 15734, 15735, 15735, 15736, 15736, 15737, 15737, 15741, 15741, 15750, 15750, 15754, 15754, 15757, 15757, 15763, 15763, 19006, 19006

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5764-5888
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5785, 5785, 5787, 5787, 5803, 5803, 5815, 5815, 5854, 5854, 5855, 5855, 5856, 5856, 5857, 5857, 5858, 5858, 5869, 5869, 5872, 5872, 6804, 6804, 20345, 20345, 20928, 20928

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8946-9057
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7884, 7884, 9542, 9542, 9854, 9854, 10700, 10700, 10720, 10720, 12722, 15066, 15066, 15119, 15119, 15552, 15792, 15792, 15810, 15810, 15828, 15828, 17044, 17044, 17068, 17068, 17092, 17092, 17235, 17235, 17576, 17576, 18872, 18872, 18887, 18887, 18897, 18897, 18897, 18897, 18907, 18907
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10820-10928
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10875, 10875, 10878, 10878, 10879, 10879, 10884, 10884, 10902, 10902, 10902, 10911, 10911, 10911, 10911, 10912, 10912, 10912, 10912, 10970, 10970, 10973, 10973, 10985, 10985, 10986, 10986, 10999, 10999, 11038, 11038, 11046, 11046, 11100, 11100, 11108, 11108

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12745-12844
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12810, 12810, 12812, 12812, 12813, 12813, 18881, 18881, 18949, 18949, 18951, 18951, 18952, 18952

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15534-15631
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15277, 15277, 15512, 15512, 15570, 15570, 15576, 15576, 15582, 15582, 15588, 15588, 15594, 15594, 15600, 15600, 15606, 15606, 15612, 15612, 15618, 15618, 15624, 15624, 15630, 15630, 15854, 17236, 17236, 17239, 17239, 17575, 17575, 18838, 18838, 18905, 18905, 18911, 18911, 18962, 18962, 19019, 19019
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8242-8338
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8298, 8298, 8334, 8334

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11315-11408
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11367, 11367, 11380, 11380, 18941, 18941, 18983, 18983, 18984, 18984, 18989, 18989, 18990, 18990

### `ValidationUtils` (class, 90 lines)

- Def site: line 5894-5983
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5976, 5976, 15340, 15340, 15341, 15341, 15555, 18741, 18741
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12658-12742
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12692, 12692, 18916, 18916, 18924, 18924, 18950, 18950, 19095, 19095

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 18018-18096
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18013, 18013, 18014, 18014, 19190, 19190
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17022-17099
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19061, 19061, 19065, 19065, 19069, 19069
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1888-1961
- References: 254
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1901, 1901, 1933, 1933, 2282, 2282, 2309, 2309, 7596, 7596, 7682, 7682, 7812, 7812, 7889, 7889, 7972, 7972, 8202, 8202, 8391, 8391, 8447, 8447, 8460, 8460, 8477, 8477, 8522, 8522, 8553, 8553, 8559, 8559, 8662, 8662, 10203, 10203, 10470, 10972, 10972, 11001, 11001, 11266, 11266, 11472, 11472, 11711, 11711, 12427, 12427, 12443, 12443, 13230, 13230, 13649, 13649, 13699, 13699, 15553, 15755, 15755, 15788, 15788, 15806, 15806, 15824, 15824, 15852, 17049, 17049, 17074, 17074, 17117, 17216, 17216, 17428, 17428, 17571, 17571, 17678, 17678, 18008, 18008, 18038, 18038, 18059, 18059, 18078, 18078, 18094, 18094, 18111, 18111, 18688, 18688, 18708, 18708, 18743, 18743, 18756, 18756, 19224, 19224, 19315, 19315, 19320, 19320, 19326, 19326, 19345, 19345, 19351, 19351, 20951, 20951, 21049, 21049
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

- Def site: line 15180-15251
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19027, 19027, 19028, 19028, 19029, 19029, 19030, 19030

### `DisplayUtils` (class, 70 lines)

- Def site: line 5455-5524
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5487, 5487, 5488, 5488, 5503, 5503, 5505, 5505

### `ConfigUtils` (class, 70 lines)

- Def site: line 5989-6058
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6031, 6031, 6036, 6036, 6133, 6133, 6191, 6191, 7082, 7082, 7739, 7739, 8384, 8384, 8407, 8407, 8427, 8427, 8612, 8612, 8633, 8633, 8908, 8908, 8933, 8933, 8988, 8988, 9010, 9010, 9027, 9027, 9044, 9044, 9429, 9429, 9652, 9652, 9669, 9669, 10061, 10061, 10393, 10393, 10604, 10604, 10641, 10641, 10794, 10794, 10937, 10937, 11190, 11190, 11378, 11378, 11562, 11562, 11881, 11881, 12217, 12217, 12389, 12389, 12429, 12429, 12435, 12435, 12529, 12529, 12759, 12759, 12832, 12832, 13319, 13319, 13354, 13553, 13553, 15060, 15060, 15276, 15276, 15544, 15651, 15751, 15751, 15786, 15786, 15804, 15804, 15822, 15822, 17115, 18009, 18009, 18011, 18011, 18035, 18035, 18039, 18039, 18040, 18040, 18060, 18060, 18061, 18061, 18222, 18222, 18792, 18792, 18824, 18824, 18861, 18861, 18867, 18867, 18995, 18995, 19052, 19052, 19135, 19135, 19144, 19144, 19222, 19222, 19223, 19223, 19240, 19240, 19315, 19315, 19320, 19320, 19326, 19326, 19345, 19345, 19351, 19351, 20262, 20262, 20333, 20815, 20815, 20903, 20903
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10439-10507
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10479, 10479, 10484, 10484, 10489, 10489, 10490, 10490, 10496, 10496, 10497, 10497, 10503, 10503, 10504, 10504, 10505, 10505, 10506, 10506, 19368, 19368

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18747-18812
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18795, 18795, 18803, 18803, 18812, 18812, 19341, 19341

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15775-15830
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18966, 18966, 18970, 18970, 19175, 19175

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6064-6110
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6188, 6188, 8074, 8074, 8989, 8989, 9012, 9012, 9499, 9499, 9534, 9534, 9548, 9548, 9671, 9671, 9675, 9675, 10223, 10223, 12533, 12533, 13203, 13203, 13329, 13329, 13361, 13539, 13539, 13575, 13575, 15550, 17899, 17899, 18010, 18010, 18041, 18041, 18062, 18062, 19225, 19225, 19241, 19241, 20834, 20834
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5713-5758
- References: 97
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5225, 5225, 5267, 5267, 5312, 5312, 5418, 5418, 5433, 5433, 5703, 5703, 5704, 5704, 5748, 5748, 6214, 6214, 7908, 7908, 9199, 9199, 9510, 9510, 9526, 9526, 9855, 9855, 10736, 10736, 10755, 10755, 12724, 15143, 15143, 15546, 15789, 15789, 15807, 15807, 15825, 15825, 15855, 16277, 16277, 16317, 16317, 16318, 16318, 16319, 16319, 17041, 17041, 17065, 17065, 17069, 17069, 17089, 17089, 17116, 17191, 17191, 17225, 17225, 17246, 17246, 17278, 17278, 17340, 17340, 17379, 17379, 17529, 17529, 17574, 17574
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17105-17147
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17128, 17128, 17134, 17134, 17140, 17140, 17146, 17146, 19159, 19159, 19163, 19163, 19167, 19167, 19171, 19171

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11581-11620
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11618, 11618, 19365, 19365

### `TimeUtils` (class, 29 lines)

- Def site: line 1852-1880
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8862, 8862, 8863, 8863, 8892, 8892, 8893, 8893, 8909, 8909, 8910, 8910, 9788, 9788, 9789, 9789, 10093, 10093, 10094, 10094, 10141, 10141, 10142, 10142, 10697, 10697, 10699, 10699, 10717, 10717, 10719, 10719, 11607, 11607, 11608, 11608, 12268, 12268, 12269, 12269, 12374, 12374, 12375, 12375, 13357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15504-15531
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15518, 15518, 15524, 15524, 15530, 15530, 19073, 19073, 19077, 19077
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15841-15866
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15861, 15861, 15866, 15866, 19081, 19081, 19086, 19086
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13656-13677
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18847, 18847, 18851, 18851, 18855, 18855
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17557-17578
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18994, 18994, 19051, 19051, 19134, 19134, 19143, 19143

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 17994-18015
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19204, 19204
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7546-7566
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6297, 10066, 15389, 15554
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13902-13911
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13938, 14074, 14151, 14170, 14182, 14203, 14216, 14227, 14233, 14246, 14339, 14474, 14569

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 315-323
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

- Def site: line 342-350
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15212, 15229, 15245
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 327-334
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

- Def site: line 302-304
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13362, 13651, 18043, 18064, 18209, 18240, 18272, 18507, 18522
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 619-621
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1229, 1898, 1898, 1898, 1910, 1916, 6190, 6310, 7370, 7430, 9598, 9709, 9963, 10793, 13364, 15422, 15464, 15562, 19227
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

- Def site: line 2000-2002
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2000, 7380, 7387, 7388, 9974, 15411

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2018-2020
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2018, 15558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 735-1739
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1784

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
