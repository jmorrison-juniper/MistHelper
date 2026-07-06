# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 194 first-party files
- Definitions analyzed: 88
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=8, hot=79, skipped=1

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
| `InputUtils` | class | 74 | 252 | hot |  | oversize_25_lines,raw_input_call |
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

## Low-Use (8)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2117-2141
- References: 3
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2247, 17708, 20659

### `BulkSwitchFirmwareUpgrader` (class, 19 lines)

- Def site: line 18100-18118
- References: 2
- Suggested class: `FirmwareManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`
- Rationale: 105 caller files detected; group callers under a shared class in `firmware_manager.py` and rewrite references per file cluster
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\firmware_manager.py`: lines 1880, 1881

### `marvis_data_utils` (assignment, 4 lines)

- Def site: line 6514-6517
- References: 3
- Suggested class: `MarvisDataUtils`
- Suggested module: `src/refactors/marvis_data_utils.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_deps()`; extract `marvis_data_utils` OUT of the entrypoint into a new `src/refactors/marvis_data_utils.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6514, 15656
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\marvis_troubleshoot_utils.py`: lines 21

### `FAST_MODE_BACKOFF_MULTIPLIER` (assignment, 3 lines)

- Def site: line 1989-1991
- References: 3
- Suggested class: `FastModeBackoffMultiplierManager`
- Suggested module: `src/refactors/fast__mode__backoff__multiplier.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_handle_site_port_stats_retry()`; extract `FAST_MODE_BACKOFF_MULTIPLIER` OUT of the entrypoint into a new `src/refactors/fast__mode__backoff__multiplier.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1989, 9900, 15329

### `FAST_MODE_DEVICES_PER_THREAD` (assignment, 3 lines)

- Def site: line 1992-1994
- References: 2
- Suggested class: `FastModeDevicesPerThreadManager`
- Suggested module: `src/refactors/fast__mode__devices__per__thread.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_DEVICES_PER_THREAD` OUT of the entrypoint into a new `src/refactors/fast__mode__devices__per__thread.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1992, 7390

### `FAST_MODE_SEQUENTIAL_MAX_RETRIES` (assignment, 3 lines)

- Def site: line 1997-1999
- References: 2
- Suggested class: `FastModeSequentialMaxRetriesManager`
- Suggested module: `src/refactors/fast__mode__sequential__max__retries.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_run_synthetic_sequential_path()`; extract `FAST_MODE_SEQUENTIAL_MAX_RETRIES` OUT of the entrypoint into a new `src/refactors/fast__mode__sequential__max__retries.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1997, 15469

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2004-2006
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2004, 7380

### `MIST_WAN_TARGET_PORTS` (assignment, 3 lines)

- Def site: line 2012-2014
- References: 3
- Suggested class: `MistWanTargetPortsManager`
- Suggested module: `src/refactors/mist__wan__target__ports.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_gateway_export_dependency_kwargs()`; extract `MIST_WAN_TARGET_PORTS` OUT of the entrypoint into a new `src/refactors/mist__wan__target__ports.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2012, 15558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51

## Hot (79)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2855-5181
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2855, 6560, 6561, 6570, 6734

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13915-14673
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14392, 14392, 14404, 14404, 14432, 14432, 14444, 14444, 14505, 14505, 14542, 14542, 14699, 19099

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9061-9746
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5567, 5567, 9184, 9184, 9235, 9235, 9238, 9238, 9279, 9279, 9318, 9318, 9336, 9336, 9414, 9414, 9421, 9421, 9431, 9431, 9434, 9434, 9447, 9447, 9448, 9448, 9449, 9449, 9450, 9450, 9458, 9458, 9460, 9460, 9461, 9461, 9462, 9462, 9463, 9463, 9466, 9466, 9469, 9469, 9472, 9472, 9475, 9475, 9521, 9521, 9544, 9544, 9545, 9545, 9546, 9546, 9548, 9548, 9584, 9584, 9600, 9600, 9654, 9654, 9655, 9655, 9656, 9656, 9659, 9659, 9660, 9660, 9679, 9679, 9681, 9681, 9682, 9682, 9717, 9717, 15068, 15068, 15121, 15121, 15552, 17044, 17044, 17068, 17068, 17092, 17092, 17235, 17235, 18874, 18874, 18881, 18881, 18890, 18890, 18894, 18894, 18903, 18903
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16343-17017
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16731, 16731, 19345, 19351

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11794-12446
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10571, 10571, 10580, 10580, 10668, 10668, 10675, 10675, 11349, 11349, 11635, 11635, 11640, 11640, 11647, 11647, 11652, 11652, 11866, 11866, 11888, 11888, 11891, 11891, 11917, 11917, 11926, 11926, 11927, 11927, 11948, 11948, 11991, 11991, 12037, 12037, 12048, 12048, 12075, 12075, 12080, 12080, 12081, 12081, 12082, 12082, 12114, 12114, 12120, 12120, 12145, 12145, 12165, 12165, 12200, 12200, 12215, 12215, 12221, 12221, 12223, 12223, 12226, 12226, 12228, 12228, 12232, 12232, 12236, 12236, 12241, 12241, 12248, 12248, 12255, 12255, 12262, 12262, 12271, 12271, 12281, 12281, 12288, 12288, 12295, 12295, 12302, 12302, 12309, 12309, 12316, 12316, 12326, 12326, 12335, 12335, 12344, 12344, 12353, 12353, 12362, 12362, 12391, 12391, 18835, 18835, 19016, 19016, 19093, 19093, 19094, 19094, 19102, 19102, 19307, 19307, 19308, 19308, 19327, 19327, 19334, 19334, 19335, 19335, 19336, 19336, 19337, 19337

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 18131-18717
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18408, 18408, 18409, 18409, 18412, 18412, 18414, 18414, 18416, 18416, 18432, 18432, 19252

### `menu_actions` (assignment, 572 lines)

- Def site: line 18816-19387
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18816, 20101, 20102, 20111, 20231, 20231, 20273, 20331, 20376, 20867, 20871, 20916, 20916, 20943, 20943, 20946
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8345-8807
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8386, 8386, 8391, 8391, 8401, 8401, 8409, 8409, 8414, 8414, 8419, 8419, 8429, 8429, 8434, 8434, 8439, 8439, 8459, 8459, 8469, 8469, 8470, 8470, 8473, 8473, 8503, 8503, 8589, 8589, 8591, 8591, 8615, 8615, 8621, 8621, 8626, 8626, 8635, 8635, 8639, 8639, 8658, 8658, 8661, 8661, 8672, 8672, 8673, 8673, 8768, 8768, 8789, 8789, 19375, 19375, 19376, 19376, 19377, 19377, 19378, 19378, 19379, 19379, 19380, 19380

### `OperationRegistry` (class, 461 lines)

- Def site: line 19612-20072
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20079, 20079, 20083, 20083, 20103, 20103, 20108, 20108, 20332

### `PromptUtils` (class, 441 lines)

- Def site: line 7792-8232
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7737, 7737, 7753, 7753, 7757, 7757, 7758, 7758, 7759, 7759, 7774, 7774, 7780, 7780, 7807, 7807, 7810, 7810, 7818, 7818, 7836, 7836, 7886, 7886, 7894, 7894, 7899, 7899, 7945, 7945, 7956, 7956, 7981, 7981, 8000, 8000, 8001, 8001, 8004, 8004, 8005, 8005, 8095, 8095, 8097, 8097, 8101, 8101, 8129, 8129, 8130, 8130, 8131, 8131, 8132, 8132, 8133, 8133, 8142, 8142, 8186, 8186, 8210, 8210, 12526, 12526, 12576, 12576, 12581, 12581, 12724, 12807, 12807, 12861, 12861, 12882, 12882, 12887, 12887, 13151, 13151, 13354, 13556, 13556, 13643, 13643, 13648, 13648, 13698, 13698, 13699, 13699, 15195, 15195, 15654, 17051, 17051, 17573, 17573, 18740, 18740, 18741, 18741, 19027, 19027
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9749-10162
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5561, 5561, 9782, 9782, 9866, 9866, 9872, 9872, 9875, 9875, 9919, 9919, 9933, 9933, 9960, 9960, 9966, 9966, 9980, 9980, 10063, 10063, 10065, 10065, 10069, 10069, 10071, 10071, 10074, 10074, 10078, 10078, 10081, 10081, 10091, 10091, 10097, 10097, 10135, 10135, 15069, 15069, 15070, 15070, 15071, 15071, 15122, 15122, 15123, 15123, 18875, 18875, 18876, 18876, 18877, 18877, 18901, 18901

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17154-17551
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17175, 17175, 17180, 17180, 17184, 17184, 17187, 17187, 17194, 17194, 17196, 17196, 17197, 17197, 17200, 17200, 17203, 17203, 17206, 17206, 17248, 17248, 17280, 17280, 17347, 17347, 17360, 17360, 17365, 17365, 17417, 17417, 17450, 17450, 17451, 17451, 17452, 17452, 17482, 17482, 17511, 17511, 17512, 17512, 19058, 19058

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 17605-17992
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17632, 17776, 17776, 19198, 19198

### `DataExporter` (class, 345 lines)

- Def site: line 6701-7045
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5657, 5657, 6747, 6747, 6763, 6763, 6764, 6764, 6787, 6787, 6789, 6789, 6792, 6792, 6806, 6806, 6808, 6808, 6817, 6817, 6819, 6819, 6820, 6820, 6826, 6826, 6827, 6827, 6827, 6844, 6844, 6848, 6848, 6890, 6890, 6921, 6921, 6924, 6924, 6926, 6926, 6972, 6972, 6982, 6982, 7015, 7015, 7020, 7020, 7027, 7027, 7249, 7249, 7281, 7281, 7292, 7292, 7317, 7317, 7337, 7337, 7849, 7849, 8642, 8642, 8921, 8921, 8936, 9000, 9000, 9017, 9017, 9035, 9035, 9056, 9056, 9615, 9615, 9690, 9690, 10020, 10020, 10371, 10371, 10456, 10472, 10592, 10592, 10596, 10596, 10616, 10616, 10629, 10629, 10633, 10633, 10651, 10651, 10813, 10813, 11160, 11160, 11307, 11307, 11384, 11384, 11388, 11388, 11393, 11393, 11526, 11526, 11545, 11545, 11596, 11596, 11599, 11599, 11750, 11750, 11753, 11753, 11852, 11852, 11858, 11858, 12155, 12155, 12172, 12172, 12187, 12187, 12401, 12401, 12429, 12429, 12445, 12445, 12482, 12482, 12520, 12520, 12609, 12609, 12638, 12638, 12676, 12676, 12727, 12792, 12792, 12798, 12798, 12840, 12840, 13009, 13009, 13015, 13015, 13134, 13134, 13142, 13142, 13306, 13306, 13357, 13530, 13530, 13701, 13701, 14214, 14214, 14575, 14575, 14581, 14581, 15489, 15489, 15548, 15655, 15791, 15791, 15809, 15809, 15827, 15827, 17098, 17098, 17119, 17958, 17958, 18043, 18043, 18064, 18064, 18566, 18566, 19227, 19227, 19243, 19243
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12848-13188
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12865, 12865, 12867, 12867, 12871, 12871, 12872, 12872, 12886, 12886, 12892, 12892, 12895, 12895, 12898, 12898, 12956, 12956, 12962, 12962, 12967, 12967, 12981, 12981, 12999, 12999, 13109, 13109, 13113, 13113, 13115, 13115, 13118, 13118, 13155, 13155, 13160, 13160, 13174, 13174, 13178, 13178, 13180, 13180, 13183, 13183, 13188, 13188, 19104, 19104, 19108, 19108, 19112, 19112

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7048-7375
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7150, 7150, 8366, 8847, 8866, 8967, 9096, 9119, 9791, 10099, 10144, 10558, 11328, 11339, 11402, 11819

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14679-15006
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12136, 12136, 12195, 12195, 12196, 12196, 13360, 14720, 14720, 14722, 14722, 14728, 14728, 14742, 14742, 14781, 14781, 14784, 14784, 14786, 14786, 14787, 14787, 14788, 14788, 14842, 14842, 14843, 14843, 14854, 14854, 14863, 14863, 14882, 14882, 14934, 14934, 14938, 14938, 14946, 14946, 14947, 14947, 14971, 14971, 14975, 14975
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16039-16327
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16067, 16067, 16070, 16070, 16075, 16075, 16078, 16078, 16122, 16122, 16128, 16128, 16159, 16159, 16162, 16162, 16166, 16166, 16192, 16192, 16209, 16209, 16215, 16215, 16229, 16229, 16230, 16230, 16232, 16232, 16238, 16238, 16245, 16245, 16254, 16254, 16301, 16301, 16323, 16323, 16324, 16324, 16325, 16325, 19049, 19049

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10165-10437
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10188, 10188, 10189, 10189, 10202, 10202, 10203, 10203, 10205, 10205, 10206, 10206, 10209, 10209, 10212, 10212, 10216, 10216, 10217, 10217, 10293, 10293, 10297, 10297, 10300, 10300, 10313, 10313, 10350, 10350, 10367, 10367, 10380, 10380, 10382, 10382, 10389, 10389, 10398, 10398, 10407, 10407, 10408, 10408, 10419, 10419, 10423, 10423, 10432, 10432, 10437, 10437, 19306, 19306

### `CacheUtils` (class, 264 lines)

- Def site: line 5187-5450
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5227, 5227, 5229, 5229, 5311, 5311, 5317, 5317, 5354, 5354, 5356, 5356, 5365, 5365, 5375, 5375, 5385, 5385, 5421, 5421, 7885, 7885, 9543, 9543, 9544, 9544, 9855, 9855, 10701, 10701, 10721, 10721, 12722, 15128, 15128, 15134, 15134, 15135, 15135, 15136, 15136, 15137, 15137, 15138, 15138, 15139, 15139, 15146, 15146, 15174, 15174, 15546, 15792, 15792, 15810, 15810, 15828, 15828, 15854, 17043, 17043, 17067, 17067, 17091, 17091, 17235, 17235, 17236, 17236, 17237, 17237, 17238, 17238, 17574, 17574, 18791, 18791, 19343, 19343
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10932-11182
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10939, 10939, 10942, 10942, 10947, 10947, 10948, 10948, 10956, 10956, 10959, 10959, 10967, 10967, 11007, 11007, 11015, 11015, 11063, 11063, 11080, 11080, 11083, 11083, 11085, 11085, 11149, 11149, 11150, 11150, 19309, 19309

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15258-15502
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15124, 15124, 15284, 15284, 15286, 15286, 15287, 15287, 15288, 15288, 15316, 15316, 15321, 15321, 15343, 15343, 15344, 15344, 15386, 15386, 15394, 15394, 15420, 15420, 15429, 15429, 15437, 15437, 15468, 15468, 18880, 18880, 18884, 18884

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6120-6340
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6143, 6143, 6194, 6194, 6264, 6264, 6288, 6288, 6300, 6300, 6302, 6302, 6312, 6312, 6327, 6327, 6331, 6331, 6332, 6332, 6335, 6335, 6337, 6337, 12835, 12835, 15550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19393-19606
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20249, 20249, 20252, 20333, 20684

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7576-7785
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7589, 7589, 7595, 7595, 7596, 7596, 7599, 7599, 7622, 7622, 7625, 7625, 7628, 7628, 7629, 7629, 7631, 7631, 7698, 7698, 7742, 7742, 8207, 8207, 13156, 13156, 15653, 15892, 15892, 16052, 16052

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12454-12656
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12475, 12475, 12484, 12484, 12546, 12546, 12553, 12553, 12585, 12585, 12587, 12587, 12611, 12611, 12646, 12646, 12653, 12653, 12684, 12684, 15198, 15198, 18916, 18916, 18918, 18918, 18919, 18919, 18921, 18921

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13707-13894
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19266, 19266, 19267, 19267, 19268, 19268, 19269, 19269, 19270, 19270, 19271, 19271, 19272, 19272, 19273, 19273, 19275, 19275, 19276, 19276, 19277, 19277, 19278, 19278, 19279, 19279, 19280, 19280, 19281, 19281, 19283, 19283, 19284, 19284, 19285, 19285, 19286, 19286, 19287, 19287, 19288, 19288, 19289, 19289, 19290, 19290, 19291, 19291, 19293, 19293, 19294, 19294, 19295, 19295, 19296, 19296, 19297, 19297, 19298, 19298, 19299, 19299, 19300, 19300, 19301, 19301, 19303, 19303, 19304, 19304

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5532-5711
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5620, 5620, 5657, 5657, 5659, 5659, 5662, 5662, 5670, 5670, 5672, 5672, 5674, 5674, 5677, 5677, 5706, 5706, 5709, 5709, 19043, 19043

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6520-6698
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6565, 6565, 6603, 6603, 6614, 6614, 6640, 6640, 6641, 6641, 6643, 6643, 6649, 6649, 6650, 6650, 6653, 6653, 6659, 6659, 6660, 6660, 6663, 6663, 6665, 6665, 6675, 6675, 6677, 6677, 6678, 6678, 6680, 6680

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11412-11579
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11519, 11519, 11538, 11538, 11556, 11556, 11565, 11565, 11568, 11568, 11569, 11569, 11572, 11572, 11577, 11577, 11579, 11579, 18944, 18944

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11624-11791
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11661, 11661, 11663, 11663, 11666, 11666, 11737, 11737, 11739, 11739, 11752, 11752, 11756, 11756, 18947, 18947, 18948, 18948, 18949, 18949, 18987, 18987, 18992, 18992

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10657-10818
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10695, 10695, 10702, 10702, 10709, 10709, 10715, 10715, 10722, 10722, 10729, 10729, 10790, 10790, 10801, 10801, 18935, 18935, 18936, 18936, 18938, 18938, 18939, 18939, 18940, 18940

### `CLIShellManager` (class, 161 lines)

- Def site: line 15873-16033
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15896, 15896, 15898, 15898, 15967, 15967, 15969, 15969, 15988, 15988, 15990, 15990, 15990, 16006, 16006, 16022, 16022, 16023, 16023, 16029, 16029, 19048, 19048

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6348-6505
- References: 201
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5485, 5485, 6364, 6364, 6377, 6377, 6380, 6380, 6404, 6404, 6412, 6412, 6413, 6413, 6435, 6435, 6440, 6440, 6442, 6442, 6515, 6515, 6516, 6516, 6923, 6923, 6948, 6948, 7017, 7017, 7018, 7018, 7347, 7347, 7361, 7361, 7362, 7362, 7847, 7847, 7848, 7848, 8770, 8770, 8935, 8995, 8995, 8997, 8997, 8998, 8998, 9015, 9015, 9016, 9016, 9033, 9033, 9034, 9034, 9054, 9054, 9055, 9055, 9612, 9612, 9613, 9613, 9687, 9687, 9688, 9688, 10016, 10016, 10019, 10019, 10594, 10594, 10595, 10595, 10631, 10631, 10632, 10632, 10811, 10811, 10812, 10812, 11156, 11156, 11157, 11157, 11303, 11303, 11304, 11304, 11386, 11386, 11387, 11387, 11598, 11598, 11773, 11773, 11774, 11774, 11850, 11850, 11851, 11851, 12154, 12154, 12170, 12170, 12171, 12171, 12399, 12399, 12400, 12400, 12479, 12479, 12480, 12480, 12481, 12481, 12517, 12517, 12518, 12518, 12606, 12606, 12607, 12607, 12635, 12635, 12636, 12636, 12673, 12673, 12674, 12674, 12726, 12795, 12795, 12796, 12796, 12838, 12838, 12839, 12839, 13007, 13007, 13008, 13008, 13132, 13132, 13133, 13133, 13356, 13528, 13528, 14580, 14580, 15487, 15487, 15488, 15488, 15549, 15657, 17096, 17096, 17097, 17097, 17948, 17948
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15020-15175
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15042, 15042, 15048, 15048, 15050, 15050, 15078, 15078, 15104, 15104, 15107, 15107, 15110, 15110, 19034, 19034, 19038, 19038, 19046, 19046

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13191-13336
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13230, 13230, 13237, 13237, 13262, 13262, 13265, 13265, 13278, 13278, 13322, 13322, 13326, 13326, 13331, 13331, 13332, 13332, 13336, 13336, 19341, 19341

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13344-13488
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12565, 12565, 12741, 12741, 12819, 12819, 12824, 12824, 13373, 13373, 13379, 13379, 13385, 13385, 13391, 13391, 13397, 13397, 13403, 13403, 13409, 13409, 13415, 13415, 13421, 13421, 13427, 13427, 13433, 13433, 13439, 13439, 13445, 13445, 13451, 13451, 13457, 13457, 13463, 13463, 13469, 13469, 13475, 13475, 13481, 13481, 13487, 13487, 18954, 18954, 19095, 19095, 19097, 19097, 19212, 19212, 19338, 19338, 19339, 19339, 19340, 19340, 19359, 19359, 19360, 19360, 19361, 19361, 19362, 19362, 19363, 19363, 19364, 19364, 19365, 19365
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10511-10654
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10525, 10525, 10526, 10526, 10612, 10612, 10647, 10647, 18929, 18929, 18930, 18930, 18931, 18931, 18932, 18932, 18933, 18933

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13491-13629
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13560, 13560, 13563, 13563, 13564, 13564, 13565, 13565, 13585, 13585, 13588, 13588, 13596, 13596, 13601, 13601, 19367, 19367

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8813-8941
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8884, 8884, 8895, 8895, 15118, 15118, 15119, 15119, 18832, 18832, 18833, 18833, 19012, 19012

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11185-11313
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11192, 11192, 11197, 11197, 11198, 11198, 11199, 11199, 11202, 11202, 11203, 11203, 11266, 11266, 11273, 11273, 11300, 11300, 19311, 19311

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15643-15769
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15663, 15663, 15668, 15668, 15673, 15673, 15710, 15710, 15716, 15716, 15722, 15722, 15728, 15728, 15734, 15734, 15735, 15735, 15736, 15736, 15737, 15737, 15738, 15738, 15742, 15742, 15751, 15751, 15755, 15755, 15758, 15758, 15764, 15764, 19007, 19007

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5765-5889
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5786, 5786, 5788, 5788, 5804, 5804, 5816, 5816, 5855, 5855, 5856, 5856, 5857, 5857, 5858, 5858, 5859, 5859, 5870, 5870, 5873, 5873, 6805, 6805, 20346, 20346, 20929, 20929

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8947-9058
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7885, 7885, 9543, 9543, 9855, 9855, 10701, 10701, 10721, 10721, 12723, 15067, 15067, 15120, 15120, 15553, 15793, 15793, 15811, 15811, 15829, 15829, 17045, 17045, 17069, 17069, 17093, 17093, 17236, 17236, 17577, 17577, 18873, 18873, 18888, 18888, 18898, 18898, 18898, 18898, 18908, 18908
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10821-10929
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10876, 10876, 10879, 10879, 10880, 10880, 10885, 10885, 10903, 10903, 10903, 10912, 10912, 10912, 10912, 10913, 10913, 10913, 10913, 10971, 10971, 10974, 10974, 10986, 10986, 10987, 10987, 11000, 11000, 11039, 11039, 11047, 11047, 11101, 11101, 11109, 11109

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12746-12845
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12811, 12811, 12813, 12813, 12814, 12814, 18882, 18882, 18950, 18950, 18952, 18952, 18953, 18953

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15535-15632
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15278, 15278, 15513, 15513, 15571, 15571, 15577, 15577, 15583, 15583, 15589, 15589, 15595, 15595, 15601, 15601, 15607, 15607, 15613, 15613, 15619, 15619, 15625, 15625, 15631, 15631, 15855, 17237, 17237, 17240, 17240, 17576, 17576, 18839, 18839, 18906, 18906, 18912, 18912, 18963, 18963, 19020, 19020
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8243-8339
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8299, 8299, 8335, 8335

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11316-11409
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11368, 11368, 11381, 11381, 18942, 18942, 18984, 18984, 18985, 18985, 18990, 18990, 18991, 18991

### `ValidationUtils` (class, 90 lines)

- Def site: line 5895-5984
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5977, 5977, 15341, 15341, 15342, 15342, 15556, 18742, 18742
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12659-12743
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12693, 12693, 18917, 18917, 18925, 18925, 18951, 18951, 19096, 19096

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 18019-18097
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18014, 18014, 18015, 18015, 19191, 19191
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17023-17100
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19062, 19062, 19066, 19066, 19070, 19070
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1889-1962
- References: 252
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1902, 1902, 1934, 1934, 2283, 2283, 2310, 2310, 7597, 7597, 7683, 7683, 7813, 7813, 7890, 7890, 7973, 7973, 8203, 8203, 8392, 8392, 8448, 8448, 8461, 8461, 8478, 8478, 8523, 8523, 8554, 8554, 8560, 8560, 8663, 8663, 10204, 10204, 10471, 10973, 10973, 11002, 11002, 11267, 11267, 11473, 11473, 11712, 11712, 12428, 12428, 12444, 12444, 13231, 13231, 13650, 13650, 13700, 13700, 15554, 15756, 15756, 15789, 15789, 15807, 15807, 15825, 15825, 15853, 17050, 17050, 17075, 17075, 17118, 17217, 17217, 17429, 17429, 17572, 17572, 17679, 17679, 18009, 18009, 18039, 18039, 18060, 18060, 18079, 18079, 18095, 18095, 18112, 18112, 18689, 18689, 18709, 18709, 18744, 18744, 18757, 18757, 19225, 19225, 19316, 19316, 19321, 19321, 19327, 19327, 19346, 19346, 19352, 19352, 20952, 20952
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

- Def site: line 15181-15252
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19028, 19028, 19029, 19029, 19030, 19030, 19031, 19031

### `DisplayUtils` (class, 70 lines)

- Def site: line 5456-5525
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5488, 5488, 5489, 5489, 5504, 5504, 5506, 5506

### `ConfigUtils` (class, 70 lines)

- Def site: line 5990-6059
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6032, 6032, 6037, 6037, 6134, 6134, 6192, 6192, 7083, 7083, 7740, 7740, 8385, 8385, 8408, 8408, 8428, 8428, 8613, 8613, 8634, 8634, 8909, 8909, 8934, 8934, 8989, 8989, 9011, 9011, 9028, 9028, 9045, 9045, 9430, 9430, 9653, 9653, 9670, 9670, 10062, 10062, 10394, 10394, 10605, 10605, 10642, 10642, 10795, 10795, 10938, 10938, 11191, 11191, 11379, 11379, 11563, 11563, 11882, 11882, 12218, 12218, 12390, 12390, 12430, 12430, 12436, 12436, 12530, 12530, 12760, 12760, 12833, 12833, 13320, 13320, 13355, 13554, 13554, 15061, 15061, 15277, 15277, 15545, 15652, 15752, 15752, 15787, 15787, 15805, 15805, 15823, 15823, 17116, 18010, 18010, 18012, 18012, 18036, 18036, 18040, 18040, 18041, 18041, 18061, 18061, 18062, 18062, 18223, 18223, 18793, 18793, 18825, 18825, 18862, 18862, 18868, 18868, 18996, 18996, 19053, 19053, 19136, 19136, 19145, 19145, 19223, 19223, 19224, 19224, 19241, 19241, 19316, 19316, 19321, 19321, 19327, 19327, 19346, 19346, 19352, 19352, 20263, 20263, 20334, 20816, 20816, 20904, 20904
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10440-10508
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10480, 10480, 10485, 10485, 10490, 10490, 10491, 10491, 10497, 10497, 10498, 10498, 10504, 10504, 10505, 10505, 10506, 10506, 10507, 10507, 19369, 19369

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18748-18813
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18796, 18796, 18804, 18804, 18813, 18813, 19342, 19342

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15776-15831
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18967, 18967, 18971, 18971, 19176, 19176

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6065-6111
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6189, 6189, 8075, 8075, 8990, 8990, 9013, 9013, 9500, 9500, 9535, 9535, 9549, 9549, 9672, 9672, 9676, 9676, 10224, 10224, 12534, 12534, 13204, 13204, 13330, 13330, 13362, 13540, 13540, 13576, 13576, 15551, 17900, 17900, 18011, 18011, 18042, 18042, 18063, 18063, 19226, 19226, 19242, 19242, 20835, 20835
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5714-5759
- References: 97
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5226, 5226, 5268, 5268, 5313, 5313, 5419, 5419, 5434, 5434, 5704, 5704, 5705, 5705, 5749, 5749, 6215, 6215, 7909, 7909, 9200, 9200, 9511, 9511, 9527, 9527, 9856, 9856, 10737, 10737, 10756, 10756, 12725, 15144, 15144, 15547, 15790, 15790, 15808, 15808, 15826, 15826, 15856, 16278, 16278, 16318, 16318, 16319, 16319, 16320, 16320, 17042, 17042, 17066, 17066, 17070, 17070, 17090, 17090, 17117, 17192, 17192, 17226, 17226, 17247, 17247, 17279, 17279, 17341, 17341, 17380, 17380, 17530, 17530, 17575, 17575
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17106-17148
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17129, 17129, 17135, 17135, 17141, 17141, 17147, 17147, 19160, 19160, 19164, 19164, 19168, 19168, 19172, 19172

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11582-11621
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11619, 11619, 19366, 19366

### `TimeUtils` (class, 29 lines)

- Def site: line 1853-1881
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8863, 8863, 8864, 8864, 8893, 8893, 8894, 8894, 8910, 8910, 8911, 8911, 9789, 9789, 9790, 9790, 10094, 10094, 10095, 10095, 10142, 10142, 10143, 10143, 10698, 10698, 10700, 10700, 10718, 10718, 10720, 10720, 11608, 11608, 11609, 11609, 12269, 12269, 12270, 12270, 12375, 12375, 12376, 12376, 13358
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15505-15532
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15519, 15519, 15525, 15525, 15531, 15531, 19074, 19074, 19078, 19078
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15842-15867
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15862, 15862, 15867, 15867, 19082, 19082, 19087, 19087
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13657-13678
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18848, 18848, 18852, 18852, 18856, 18856
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17558-17579
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18995, 18995, 19052, 19052, 19135, 19135, 19144, 19144

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 17995-18016
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19205, 19205
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7547-7567
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6298, 10067, 15390, 15555
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13903-13912
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13939, 14075, 14152, 14171, 14183, 14204, 14217, 14228, 14234, 14247, 14340, 14475, 14570

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 316-324
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

- Def site: line 343-351
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15213, 15230, 15246
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 328-335
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

- Def site: line 303-305
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13363, 13652, 18044, 18065, 18210, 18241, 18273, 18508, 18523
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 620-622
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1230, 1899, 1899, 1899, 1911, 1917, 6191, 6311, 7371, 7431, 9599, 9710, 9964, 10794, 13365, 15423, 15465, 15563, 19228
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

- Def site: line 2001-2003
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2001, 7381, 7388, 7389, 9975, 15412

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2019-2021
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2019, 15559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 736-1740
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1785

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
