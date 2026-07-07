# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 201 first-party files
- Definitions analyzed: 80
- LOC saveable (unused + single-use): 3
- Category counts: unused=0, single-use=1, low-use=2, hot=76, skipped=1

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
| `OrgTicketManager` | class | 475 | 66 | hot |  | oversize_25_lines |
| `OperationRegistry` | class | 461 | 9 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `PromptUtils` | class | 441 | 117 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 58 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 396 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `MSPInventoryExporter` | class | 386 | 5 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
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
| `DataProcessingUtils` | class | 158 | 197 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `DataCollectionManager` | class | 156 | 20 | hot |  | oversize_25_lines,missing_inline_comments |
| `SitesByAPModelExporter` | class | 146 | 22 | hot |  | oversize_25_lines |
| `SiteExportUtils` | class | 145 | 94 | hot |  | oversize_25_lines,missing_action_logging |
| `OrgTemplateExporter` | class | 144 | 18 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayHaExporter` | class | 139 | 18 | hot |  | oversize_25_lines |
| `OrgAlarmEventExporter` | class | 129 | 14 | hot |  | oversize_25_lines,missing_inline_comments |
| `WiredClientManufacturerReportGenerator` | class | 129 | 20 | hot |  | oversize_25_lines,non_ascii_logs |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `EnvironmentUtils` | class | 114 | 28 | hot |  | oversize_25_lines,hardcoded_separator |
| `OrgSiteExporter` | class | 112 | 52 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 110 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteConfigExporter` | class | 100 | 14 | hot |  | oversize_25_lines,non_ascii_logs |
| `GatewayExportUtils` | class | 98 | 78 | hot |  | oversize_25_lines,missing_action_logging |
| `DeviceUtils` | class | 97 | 4 | hot |  | oversize_25_lines |
| `OrgAdminExporter` | class | 94 | 14 | hot |  | oversize_25_lines,hardcoded_separator |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `SiteClientExporter` | class | 85 | 10 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 250 | hot |  | oversize_25_lines,raw_input_call |
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
| `EndpointConfig` | class | 10 | 13 | hot |  | missing_action_logging |
| `SSHConnectionConfig` | class | 9 | 6 | hot |  | missing_action_logging |
| `DeviceFetchConfig` | class | 9 | 4 | hot |  | missing_action_logging |
| `SSHExecutionConfig` | class | 8 | 5 | hot |  | missing_inline_comments,missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 3 | low-use | FastModeMaxConcurrentConnectionsManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 1 | single-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Single-Use (1)

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2018-2020
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2018

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2127-2151
- References: 3
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2257, 17526, 20459

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2015-2017
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2015, 9794, 15232

## Hot (76)

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2865, 6555, 6556, 6565, 6729

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13735-14493
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14212, 14212, 14224, 14224, 14252, 14252, 14264, 14264, 14325, 14325, 14362, 14362, 14519, 18899

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8880-9565
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5577, 5577, 9003, 9003, 9054, 9054, 9057, 9057, 9098, 9098, 9137, 9137, 9155, 9155, 9233, 9233, 9240, 9240, 9250, 9250, 9253, 9253, 9266, 9266, 9267, 9267, 9268, 9268, 9269, 9269, 9277, 9277, 9279, 9279, 9280, 9280, 9281, 9281, 9282, 9282, 9285, 9285, 9288, 9288, 9291, 9291, 9294, 9294, 9340, 9340, 9363, 9363, 9364, 9364, 9365, 9365, 9367, 9367, 9403, 9403, 9419, 9419, 9473, 9473, 9474, 9474, 9475, 9475, 9478, 9478, 9479, 9479, 9498, 9498, 9500, 9500, 9501, 9501, 9536, 9536, 14888, 14888, 14941, 14941, 15372, 16864, 16864, 16888, 16888, 16912, 16912, 17055, 17055, 18674, 18674, 18681, 18681, 18690, 18690, 18694, 18694, 18703, 18703
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16163-16837
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16551, 16551, 19145, 19151

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11614-12266
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10390, 10390, 10399, 10399, 10487, 10487, 10494, 10494, 11169, 11169, 11455, 11455, 11460, 11460, 11467, 11467, 11472, 11472, 11686, 11686, 11708, 11708, 11711, 11711, 11737, 11737, 11746, 11746, 11747, 11747, 11768, 11768, 11811, 11811, 11857, 11857, 11868, 11868, 11895, 11895, 11900, 11900, 11901, 11901, 11902, 11902, 11934, 11934, 11940, 11940, 11965, 11965, 11985, 11985, 12020, 12020, 12035, 12035, 12041, 12041, 12043, 12043, 12046, 12046, 12048, 12048, 12052, 12052, 12056, 12056, 12061, 12061, 12068, 12068, 12075, 12075, 12082, 12082, 12091, 12091, 12101, 12101, 12108, 12108, 12115, 12115, 12122, 12122, 12129, 12129, 12136, 12136, 12146, 12146, 12155, 12155, 12164, 12164, 12173, 12173, 12182, 12182, 12211, 12211, 18635, 18635, 18816, 18816, 18893, 18893, 18894, 18894, 18902, 18902, 19107, 19107, 19108, 19108, 19127, 19127, 19134, 19134, 19135, 19135, 19136, 19136, 19137, 19137

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 17931-18517
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18208, 18208, 18209, 18209, 18212, 18212, 18214, 18214, 18216, 18216, 18232, 18232, 19052

### `menu_actions` (assignment, 572 lines)

- Def site: line 18616-19187
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18616, 19901, 19902, 19911, 20031, 20031, 20073, 20131, 20176, 20667, 20671, 20716, 20716, 20743, 20743, 20746
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 475 lines)

- Def site: line 8152-8626
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8193, 8193, 8198, 8198, 8208, 8208, 8216, 8216, 8221, 8221, 8226, 8226, 8239, 8239, 8244, 8244, 8249, 8249, 8269, 8269, 8279, 8279, 8280, 8280, 8283, 8283, 8313, 8313, 8402, 8402, 8404, 8404, 8431, 8431, 8437, 8437, 8442, 8442, 8451, 8451, 8455, 8455, 8474, 8474, 8477, 8477, 8488, 8488, 8489, 8489, 8587, 8587, 8608, 8608, 19175, 19175, 19176, 19176, 19177, 19177, 19178, 19178, 19179, 19179, 19180, 19180

### `OperationRegistry` (class, 461 lines)

- Def site: line 19412-19872
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19879, 19879, 19883, 19883, 19903, 19903, 19908, 19908, 20132

### `PromptUtils` (class, 441 lines)

- Def site: line 7599-8039
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7544, 7544, 7560, 7560, 7564, 7564, 7565, 7565, 7566, 7566, 7581, 7581, 7587, 7587, 7614, 7614, 7617, 7617, 7625, 7625, 7643, 7643, 7693, 7693, 7701, 7701, 7706, 7706, 7752, 7752, 7763, 7763, 7788, 7788, 7807, 7807, 7808, 7808, 7811, 7811, 7812, 7812, 7902, 7902, 7904, 7904, 7908, 7908, 7936, 7936, 7937, 7937, 7938, 7938, 7939, 7939, 7940, 7940, 7949, 7949, 7993, 7993, 8017, 8017, 12346, 12346, 12396, 12396, 12401, 12401, 12544, 12627, 12627, 12681, 12681, 12702, 12702, 12707, 12707, 12971, 12971, 13174, 13376, 13376, 13463, 13463, 13468, 13468, 13518, 13518, 13519, 13519, 15015, 15015, 15474, 16871, 16871, 17391, 17391, 18540, 18540, 18541, 18541, 18827, 18827
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9568-9981
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5571, 5571, 9601, 9601, 9685, 9685, 9691, 9691, 9694, 9694, 9738, 9738, 9752, 9752, 9779, 9779, 9785, 9785, 9799, 9799, 9882, 9882, 9884, 9884, 9888, 9888, 9890, 9890, 9893, 9893, 9897, 9897, 9900, 9900, 9910, 9910, 9916, 9916, 9954, 9954, 14889, 14889, 14890, 14890, 14891, 14891, 14942, 14942, 14943, 14943, 18675, 18675, 18676, 18676, 18677, 18677, 18701, 18701

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 16974-17369
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16995, 16995, 17000, 17000, 17004, 17004, 17007, 17007, 17014, 17014, 17016, 17016, 17017, 17017, 17020, 17020, 17023, 17023, 17026, 17026, 17068, 17068, 17100, 17100, 17167, 17167, 17180, 17180, 17185, 17185, 17235, 17235, 17268, 17268, 17269, 17269, 17270, 17270, 17300, 17300, 17329, 17329, 17330, 17330, 18858, 18858

### `MSPInventoryExporter` (class, 386 lines)

- Def site: line 17423-17808
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17450, 17594, 17594, 18998, 18998

### `DataExporter` (class, 345 lines)

- Def site: line 6696-7040
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5667, 5667, 6742, 6742, 6758, 6758, 6759, 6759, 6782, 6782, 6784, 6784, 6787, 6787, 6801, 6801, 6803, 6803, 6812, 6812, 6814, 6814, 6815, 6815, 6821, 6821, 6822, 6822, 6822, 6839, 6839, 6843, 6843, 6885, 6885, 6916, 6916, 6919, 6919, 6921, 6921, 6967, 6967, 6977, 6977, 7010, 7010, 7015, 7015, 7022, 7022, 7244, 7244, 7276, 7276, 7287, 7287, 7312, 7312, 7332, 7332, 7656, 7656, 8458, 8458, 8740, 8740, 8755, 8819, 8819, 8836, 8836, 8854, 8854, 8875, 8875, 9434, 9434, 9509, 9509, 9839, 9839, 10190, 10190, 10275, 10291, 10411, 10411, 10415, 10415, 10435, 10435, 10448, 10448, 10452, 10452, 10470, 10470, 10632, 10632, 10980, 10980, 11127, 11127, 11204, 11204, 11208, 11208, 11213, 11213, 11346, 11346, 11365, 11365, 11416, 11416, 11419, 11419, 11570, 11570, 11573, 11573, 11672, 11672, 11678, 11678, 11975, 11975, 11992, 11992, 12007, 12007, 12221, 12221, 12249, 12249, 12265, 12265, 12302, 12302, 12340, 12340, 12429, 12429, 12458, 12458, 12496, 12496, 12547, 12612, 12612, 12618, 12618, 12660, 12660, 12829, 12829, 12835, 12835, 12954, 12954, 12962, 12962, 13126, 13126, 13177, 13350, 13350, 13521, 13521, 14034, 14034, 14395, 14395, 14401, 14401, 15309, 15309, 15368, 15475, 15611, 15611, 15629, 15629, 15647, 15647, 16918, 16918, 16939, 17774, 17774, 17859, 17859, 17880, 17880, 18366, 18366, 19027, 19027, 19043, 19043
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12668-13008
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12685, 12685, 12687, 12687, 12691, 12691, 12692, 12692, 12706, 12706, 12712, 12712, 12715, 12715, 12718, 12718, 12776, 12776, 12782, 12782, 12787, 12787, 12801, 12801, 12819, 12819, 12929, 12929, 12933, 12933, 12935, 12935, 12938, 12938, 12975, 12975, 12980, 12980, 12994, 12994, 12998, 12998, 13000, 13000, 13003, 13003, 13008, 13008, 18904, 18904, 18908, 18908, 18912, 18912

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7043-7370
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7145, 7145, 8173, 8666, 8685, 8786, 8915, 8938, 9610, 9918, 9963, 10377, 11148, 11159, 11222, 11639

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14499-14826
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11956, 11956, 12015, 12015, 12016, 12016, 13180, 14540, 14540, 14542, 14542, 14548, 14548, 14562, 14562, 14601, 14601, 14604, 14604, 14606, 14606, 14607, 14607, 14608, 14608, 14662, 14662, 14663, 14663, 14674, 14674, 14683, 14683, 14702, 14702, 14754, 14754, 14758, 14758, 14766, 14766, 14767, 14767, 14791, 14791, 14795, 14795
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 15859-16147
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15887, 15887, 15890, 15890, 15895, 15895, 15898, 15898, 15942, 15942, 15948, 15948, 15979, 15979, 15982, 15982, 15986, 15986, 16012, 16012, 16029, 16029, 16035, 16035, 16049, 16049, 16050, 16050, 16052, 16052, 16058, 16058, 16065, 16065, 16074, 16074, 16121, 16121, 16143, 16143, 16144, 16144, 16145, 16145, 18849, 18849

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9984-10256
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10007, 10007, 10008, 10008, 10021, 10021, 10022, 10022, 10024, 10024, 10025, 10025, 10028, 10028, 10031, 10031, 10035, 10035, 10036, 10036, 10112, 10112, 10116, 10116, 10119, 10119, 10132, 10132, 10169, 10169, 10186, 10186, 10199, 10199, 10201, 10201, 10208, 10208, 10217, 10217, 10226, 10226, 10227, 10227, 10238, 10238, 10242, 10242, 10251, 10251, 10256, 10256, 19106, 19106

### `CacheUtils` (class, 264 lines)

- Def site: line 5197-5460
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5237, 5237, 5239, 5239, 5321, 5321, 5327, 5327, 5364, 5364, 5366, 5366, 5375, 5375, 5385, 5385, 5395, 5395, 5431, 5431, 7692, 7692, 9362, 9362, 9363, 9363, 9674, 9674, 10520, 10520, 10540, 10540, 12542, 14948, 14948, 14954, 14954, 14955, 14955, 14956, 14956, 14957, 14957, 14958, 14958, 14959, 14959, 14966, 14966, 14994, 14994, 15366, 15612, 15612, 15630, 15630, 15648, 15648, 15674, 16863, 16863, 16887, 16887, 16911, 16911, 17055, 17055, 17056, 17056, 17057, 17057, 17058, 17058, 17392, 17392, 18591, 18591, 19143, 19143
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10752-11002
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10759, 10759, 10762, 10762, 10767, 10767, 10768, 10768, 10776, 10776, 10779, 10779, 10787, 10787, 10827, 10827, 10835, 10835, 10883, 10883, 10900, 10900, 10903, 10903, 10905, 10905, 10969, 10969, 10970, 10970, 19109, 19109

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15078-15322
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14944, 14944, 15104, 15104, 15106, 15106, 15107, 15107, 15108, 15108, 15136, 15136, 15141, 15141, 15163, 15163, 15164, 15164, 15206, 15206, 15214, 15214, 15240, 15240, 15249, 15249, 15257, 15257, 15288, 15288, 18680, 18680, 18684, 18684

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6119-6339
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6142, 6142, 6193, 6193, 6263, 6263, 6287, 6287, 6299, 6299, 6301, 6301, 6311, 6311, 6326, 6326, 6330, 6330, 6331, 6331, 6334, 6334, 6336, 6336, 12655, 12655, 15370
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19193-19406
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20049, 20049, 20052, 20133, 20484

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7383-7592
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7396, 7396, 7402, 7402, 7403, 7403, 7406, 7406, 7429, 7429, 7432, 7432, 7435, 7435, 7436, 7436, 7438, 7438, 7505, 7505, 7549, 7549, 8014, 8014, 12976, 12976, 15473, 15712, 15712, 15872, 15872

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12274-12476
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12295, 12295, 12304, 12304, 12366, 12366, 12373, 12373, 12405, 12405, 12407, 12407, 12431, 12431, 12466, 12466, 12473, 12473, 12504, 12504, 15018, 15018, 18716, 18716, 18718, 18718, 18719, 18719, 18721, 18721

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13527-13714
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19066, 19066, 19067, 19067, 19068, 19068, 19069, 19069, 19070, 19070, 19071, 19071, 19072, 19072, 19073, 19073, 19075, 19075, 19076, 19076, 19077, 19077, 19078, 19078, 19079, 19079, 19080, 19080, 19081, 19081, 19083, 19083, 19084, 19084, 19085, 19085, 19086, 19086, 19087, 19087, 19088, 19088, 19089, 19089, 19090, 19090, 19091, 19091, 19093, 19093, 19094, 19094, 19095, 19095, 19096, 19096, 19097, 19097, 19098, 19098, 19099, 19099, 19100, 19100, 19101, 19101, 19103, 19103, 19104, 19104

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5542-5721
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5630, 5630, 5667, 5667, 5669, 5669, 5672, 5672, 5680, 5680, 5682, 5682, 5684, 5684, 5687, 5687, 5716, 5716, 5719, 5719, 18843, 18843

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6515-6693
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6560, 6560, 6598, 6598, 6609, 6609, 6635, 6635, 6636, 6636, 6638, 6638, 6644, 6644, 6645, 6645, 6648, 6648, 6654, 6654, 6655, 6655, 6658, 6658, 6660, 6660, 6670, 6670, 6672, 6672, 6673, 6673, 6675, 6675

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11232-11399
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11339, 11339, 11358, 11358, 11376, 11376, 11385, 11385, 11388, 11388, 11389, 11389, 11392, 11392, 11397, 11397, 11399, 11399, 18744, 18744

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11444-11611
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11481, 11481, 11483, 11483, 11486, 11486, 11557, 11557, 11559, 11559, 11572, 11572, 11576, 11576, 18747, 18747, 18748, 18748, 18749, 18749, 18787, 18787, 18792, 18792

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10476-10637
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10514, 10514, 10521, 10521, 10528, 10528, 10534, 10534, 10541, 10541, 10548, 10548, 10609, 10609, 10620, 10620, 18735, 18735, 18736, 18736, 18738, 18738, 18739, 18739, 18740, 18740

### `CLIShellManager` (class, 161 lines)

- Def site: line 15693-15853
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15716, 15716, 15718, 15718, 15787, 15787, 15789, 15789, 15808, 15808, 15810, 15810, 15810, 15826, 15826, 15842, 15842, 15843, 15843, 15849, 15849, 18848, 18848

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6347-6504
- References: 197
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5495, 5495, 6363, 6363, 6376, 6376, 6379, 6379, 6403, 6403, 6411, 6411, 6412, 6412, 6434, 6434, 6439, 6439, 6441, 6441, 6918, 6918, 6943, 6943, 7012, 7012, 7013, 7013, 7342, 7342, 7356, 7356, 7357, 7357, 7654, 7654, 7655, 7655, 8589, 8589, 8754, 8814, 8814, 8816, 8816, 8817, 8817, 8834, 8834, 8835, 8835, 8852, 8852, 8853, 8853, 8873, 8873, 8874, 8874, 9431, 9431, 9432, 9432, 9506, 9506, 9507, 9507, 9835, 9835, 9838, 9838, 10413, 10413, 10414, 10414, 10450, 10450, 10451, 10451, 10630, 10630, 10631, 10631, 10976, 10976, 10977, 10977, 11123, 11123, 11124, 11124, 11206, 11206, 11207, 11207, 11418, 11418, 11593, 11593, 11594, 11594, 11670, 11670, 11671, 11671, 11974, 11974, 11990, 11990, 11991, 11991, 12219, 12219, 12220, 12220, 12299, 12299, 12300, 12300, 12301, 12301, 12337, 12337, 12338, 12338, 12426, 12426, 12427, 12427, 12455, 12455, 12456, 12456, 12493, 12493, 12494, 12494, 12546, 12615, 12615, 12616, 12616, 12658, 12658, 12659, 12659, 12827, 12827, 12828, 12828, 12952, 12952, 12953, 12953, 13176, 13348, 13348, 14400, 14400, 15307, 15307, 15308, 15308, 15369, 15477, 16916, 16916, 16917, 16917, 17764, 17764
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `DataCollectionManager` (class, 156 lines)

- Def site: line 14840-14995
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14862, 14862, 14868, 14868, 14870, 14870, 14898, 14898, 14924, 14924, 14927, 14927, 14930, 14930, 18834, 18834, 18838, 18838, 18846, 18846

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13011-13156
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13050, 13050, 13057, 13057, 13082, 13082, 13085, 13085, 13098, 13098, 13142, 13142, 13146, 13146, 13151, 13151, 13152, 13152, 13156, 13156, 19141, 19141

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13164-13308
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12385, 12385, 12561, 12561, 12639, 12639, 12644, 12644, 13193, 13193, 13199, 13199, 13205, 13205, 13211, 13211, 13217, 13217, 13223, 13223, 13229, 13229, 13235, 13235, 13241, 13241, 13247, 13247, 13253, 13253, 13259, 13259, 13265, 13265, 13271, 13271, 13277, 13277, 13283, 13283, 13289, 13289, 13295, 13295, 13301, 13301, 13307, 13307, 18754, 18754, 18895, 18895, 18897, 18897, 19012, 19012, 19138, 19138, 19139, 19139, 19140, 19140, 19159, 19159, 19160, 19160, 19161, 19161, 19162, 19162, 19163, 19163, 19164, 19164, 19165, 19165
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10330-10473
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10344, 10344, 10345, 10345, 10431, 10431, 10466, 10466, 18729, 18729, 18730, 18730, 18731, 18731, 18732, 18732, 18733, 18733

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13311-13449
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13380, 13380, 13383, 13383, 13384, 13384, 13385, 13385, 13405, 13405, 13408, 13408, 13416, 13416, 13421, 13421, 19167, 19167

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8632-8760
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8703, 8703, 8714, 8714, 14938, 14938, 14939, 14939, 18632, 18632, 18633, 18633, 18812, 18812

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11005-11133
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11012, 11012, 11017, 11017, 11018, 11018, 11019, 11019, 11022, 11022, 11023, 11023, 11086, 11086, 11093, 11093, 11120, 11120, 19111, 19111

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15463-15589
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15483, 15483, 15488, 15488, 15493, 15493, 15530, 15530, 15536, 15536, 15542, 15542, 15548, 15548, 15554, 15554, 15555, 15555, 15556, 15556, 15557, 15557, 15558, 15558, 15562, 15562, 15571, 15571, 15575, 15575, 15578, 15578, 15584, 15584, 18807, 18807

### `EnvironmentUtils` (class, 114 lines)

- Def site: line 5775-5888
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5796, 5796, 5798, 5798, 5814, 5814, 5826, 5826, 5865, 5865, 5866, 5866, 5867, 5867, 5868, 5868, 5869, 5869, 5880, 5880, 5883, 5883, 6800, 6800, 20146, 20146, 20729, 20729

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8766-8877
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7692, 7692, 9362, 9362, 9674, 9674, 10520, 10520, 10540, 10540, 12543, 14887, 14887, 14940, 14940, 15373, 15613, 15613, 15631, 15631, 15649, 15649, 16865, 16865, 16889, 16889, 16913, 16913, 17056, 17056, 17395, 17395, 18673, 18673, 18688, 18688, 18698, 18698, 18698, 18698, 18708, 18708
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 10640-10749
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10695, 10695, 10698, 10698, 10699, 10699, 10704, 10704, 10723, 10723, 10723, 10732, 10732, 10732, 10732, 10733, 10733, 10733, 10733, 10791, 10791, 10794, 10794, 10806, 10806, 10807, 10807, 10820, 10820, 10859, 10859, 10867, 10867, 10921, 10921, 10929, 10929

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12566-12665
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12631, 12631, 12633, 12633, 12634, 12634, 18682, 18682, 18750, 18750, 18752, 18752, 18753, 18753

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15355-15452
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15098, 15098, 15333, 15333, 15391, 15391, 15397, 15397, 15403, 15403, 15409, 15409, 15415, 15415, 15421, 15421, 15427, 15427, 15433, 15433, 15439, 15439, 15445, 15445, 15451, 15451, 15675, 17057, 17057, 17060, 17060, 17394, 17394, 18639, 18639, 18706, 18706, 18712, 18712, 18763, 18763, 18820, 18820
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8050-8146
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8106, 8106, 8142, 8142

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11136-11229
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11188, 11188, 11201, 11201, 18742, 18742, 18784, 18784, 18785, 18785, 18790, 18790, 18791, 18791

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5976, 5976, 15161, 15161, 15162, 15162, 15376, 18542, 18542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12479-12563
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12513, 12513, 18717, 18717, 18725, 18725, 18751, 18751, 18896, 18896

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 17835-17913
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17830, 17830, 17831, 17831, 18991, 18991
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 16843-16920
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18862, 18862, 18866, 18866, 18870, 18870
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1903-1976
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1916, 1916, 1948, 1948, 2293, 2293, 2320, 2320, 7404, 7404, 7490, 7490, 7620, 7620, 7697, 7697, 7780, 7780, 8010, 8010, 8199, 8199, 8258, 8258, 8271, 8271, 8288, 8288, 8333, 8333, 8367, 8367, 8373, 8373, 8479, 8479, 10023, 10023, 10290, 10793, 10793, 10822, 10822, 11087, 11087, 11293, 11293, 11532, 11532, 12248, 12248, 12264, 12264, 13051, 13051, 13470, 13470, 13520, 13520, 15374, 15576, 15576, 15609, 15609, 15627, 15627, 15645, 15645, 15673, 16870, 16870, 16895, 16895, 16938, 17037, 17037, 17247, 17247, 17390, 17390, 17497, 17497, 17825, 17825, 17855, 17855, 17876, 17876, 17895, 17895, 17911, 17911, 18489, 18489, 18509, 18509, 18544, 18544, 18557, 18557, 19025, 19025, 19116, 19116, 19121, 19121, 19127, 19127, 19146, 19146, 19152, 19152, 20752, 20752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550, 550
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 18, 66, 197, 197

### `InteractiveDisplayUtils` (class, 72 lines)

- Def site: line 15001-15072
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18828, 18828, 18829, 18829, 18830, 18830, 18831, 18831

### `DisplayUtils` (class, 70 lines)

- Def site: line 5466-5535
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5498, 5498, 5499, 5499, 5514, 5514, 5516, 5516

### `ConfigUtils` (class, 70 lines)

- Def site: line 5989-6058
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6031, 6031, 6036, 6036, 6133, 6133, 6191, 6191, 7078, 7078, 7547, 7547, 8192, 8192, 8215, 8215, 8238, 8238, 8429, 8429, 8450, 8450, 8728, 8728, 8753, 8753, 8808, 8808, 8830, 8830, 8847, 8847, 8864, 8864, 9249, 9249, 9472, 9472, 9489, 9489, 9881, 9881, 10213, 10213, 10424, 10424, 10461, 10461, 10614, 10614, 10758, 10758, 11011, 11011, 11199, 11199, 11383, 11383, 11702, 11702, 12038, 12038, 12210, 12210, 12250, 12250, 12256, 12256, 12350, 12350, 12580, 12580, 12653, 12653, 13140, 13140, 13175, 13374, 13374, 14881, 14881, 15097, 15097, 15365, 15472, 15572, 15572, 15607, 15607, 15625, 15625, 15643, 15643, 16936, 17826, 17826, 17828, 17828, 17852, 17852, 17856, 17856, 17857, 17857, 17877, 17877, 17878, 17878, 18023, 18023, 18593, 18593, 18625, 18625, 18662, 18662, 18668, 18668, 18796, 18796, 18853, 18853, 18936, 18936, 18945, 18945, 19023, 19023, 19024, 19024, 19041, 19041, 19116, 19116, 19121, 19121, 19127, 19127, 19146, 19146, 19152, 19152, 20063, 20063, 20134, 20616, 20616, 20704, 20704
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10259-10327
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10299, 10299, 10304, 10304, 10309, 10309, 10310, 10310, 10316, 10316, 10317, 10317, 10323, 10323, 10324, 10324, 10325, 10325, 10326, 10326, 19169, 19169

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18548-18613
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18596, 18596, 18604, 18604, 18613, 18613, 19142, 19142

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15596-15651
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18767, 18767, 18771, 18771, 18976, 18976

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6188, 6188, 7882, 7882, 8809, 8809, 8832, 8832, 9319, 9319, 9354, 9354, 9368, 9368, 9491, 9491, 9495, 9495, 10043, 10043, 12354, 12354, 13024, 13024, 13150, 13150, 13182, 13360, 13360, 13396, 13396, 15371, 17716, 17716, 17827, 17827, 17858, 17858, 17879, 17879, 19026, 19026, 19042, 19042, 20635, 20635
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5724-5769
- References: 97
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5236, 5236, 5278, 5278, 5323, 5323, 5429, 5429, 5444, 5444, 5714, 5714, 5715, 5715, 5759, 5759, 6214, 6214, 7716, 7716, 9019, 9019, 9330, 9330, 9346, 9346, 9675, 9675, 10556, 10556, 10575, 10575, 12545, 14964, 14964, 15367, 15610, 15610, 15628, 15628, 15646, 15646, 15676, 16098, 16098, 16138, 16138, 16139, 16139, 16140, 16140, 16862, 16862, 16886, 16886, 16890, 16890, 16910, 16910, 16937, 17012, 17012, 17046, 17046, 17067, 17067, 17099, 17099, 17161, 17161, 17200, 17200, 17348, 17348, 17393, 17393
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 16926-16968
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16949, 16949, 16955, 16955, 16961, 16961, 16967, 16967, 18960, 18960, 18964, 18964, 18968, 18968, 18972, 18972

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11402-11441
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11439, 11439, 19166, 19166

### `TimeUtils` (class, 29 lines)

- Def site: line 1867-1895
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8682, 8682, 8683, 8683, 8712, 8712, 8713, 8713, 8729, 8729, 8730, 8730, 9608, 9608, 9609, 9609, 9913, 9913, 9914, 9914, 9961, 9961, 9962, 9962, 10517, 10517, 10519, 10519, 10537, 10537, 10539, 10539, 11428, 11428, 11429, 11429, 12089, 12089, 12090, 12090, 12195, 12195, 12196, 12196, 13178
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15325-15352
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15339, 15339, 15345, 15345, 15351, 15351, 18874, 18874, 18878, 18878
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15662-15687
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15682, 15682, 15687, 15687, 18882, 18882, 18887, 18887
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13477-13498
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18648, 18648, 18652, 18652, 18656, 18656
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17376-17397
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18795, 18795, 18852, 18852, 18935, 18935, 18944, 18944

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 17811-17832
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19005, 19005
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `EndpointConfig` (class, 10 lines)

- Def site: line 13723-13732
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13759, 13895, 13972, 13991, 14003, 14024, 14037, 14048, 14054, 14067, 14160, 14295, 14390

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 327-335
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

- Def site: line 354-362
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15033, 15050, 15066
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 339-346
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

### `tqdm` (function, 3 lines)

- Def site: line 634-636
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1244, 1913, 1913, 1913, 1925, 1931, 6190, 6310, 7366, 9418, 9529, 9783, 10613, 13185, 15243, 15285, 15383, 19028
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 35, 79, 163
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 58
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 41, 217, 260
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\connection_pool_executor.py`: lines 137
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\wanprobe_config_manager.py`: lines 243, 363
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 903, 905

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2029-2031
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2029, 15379
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 750-1754
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1799

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
