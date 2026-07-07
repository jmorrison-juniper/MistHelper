# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 199 first-party files
- Definitions analyzed: 82
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=2, hot=79, skipped=1

## How to read this report

Work the report **top-down inside each category**, then move to the next category:

1. **Unused** -- zero references. Delete outright; no move, no callsite rewrite. Highest ROI per PR.
2. **Single-use** -- exactly one caller. Move alongside that caller (or into a new `/src` module when the Refactor report written to refactor_candidates.md
Entrypoint: C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py
Module graph: 199 first-party files
Definitions analyzed: 82
  unused=0  single-use=0  low-use=2  hot=79  skipped=1
LOC saveable (unused + single-use): 0
 -- pinned by bootstrap/module-load ordering (e.g. `GlobalImportManager`). DO NOT extract; the tool cannot detect load-order dependencies, so these are curated by hand via the `--skip NAME` CLI flag.

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
| `DataProcessingUtils` | class | 158 | 197 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
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
| `execute_with_connection_pool_management` | function | 21 | 7 | hot |  |  |
| `EndpointConfig` | class | 10 | 13 | hot |  | missing_action_logging |
| `SSHConnectionConfig` | class | 9 | 6 | hot |  | missing_action_logging |
| `DeviceFetchConfig` | class | 9 | 4 | hot |  | missing_action_logging |
| `SSHExecutionConfig` | class | 8 | 5 | hot |  | missing_inline_comments,missing_action_logging |
| `is_debug_mode` | function | 3 | 12 | hot |  | missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 2 | low-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2128-2152
- References: 3
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2258, 17717, 20652

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2019-2021
- References: 2
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_pool_configure()`; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2019, 7387

## Hot (79)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2866-5192
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2866, 6567, 6568, 6577, 6741

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13924-14682
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14401, 14401, 14413, 14413, 14441, 14441, 14453, 14453, 14514, 14514, 14551, 14551, 14708, 19092

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 9070-9755
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5578, 5578, 9193, 9193, 9244, 9244, 9247, 9247, 9288, 9288, 9327, 9327, 9345, 9345, 9423, 9423, 9430, 9430, 9440, 9440, 9443, 9443, 9456, 9456, 9457, 9457, 9458, 9458, 9459, 9459, 9467, 9467, 9469, 9469, 9470, 9470, 9471, 9471, 9472, 9472, 9475, 9475, 9478, 9478, 9481, 9481, 9484, 9484, 9530, 9530, 9553, 9553, 9554, 9554, 9555, 9555, 9557, 9557, 9593, 9593, 9609, 9609, 9663, 9663, 9664, 9664, 9665, 9665, 9668, 9668, 9669, 9669, 9688, 9688, 9690, 9690, 9691, 9691, 9726, 9726, 15077, 15077, 15130, 15130, 15561, 17053, 17053, 17077, 17077, 17101, 17101, 17244, 17244, 18867, 18867, 18874, 18874, 18883, 18883, 18887, 18887, 18896, 18896
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 294, 294, 342, 342, 498, 498

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16352-17026
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16740, 16740, 19338, 19344

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11803-12455
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10580, 10580, 10589, 10589, 10677, 10677, 10684, 10684, 11358, 11358, 11644, 11644, 11649, 11649, 11656, 11656, 11661, 11661, 11875, 11875, 11897, 11897, 11900, 11900, 11926, 11926, 11935, 11935, 11936, 11936, 11957, 11957, 12000, 12000, 12046, 12046, 12057, 12057, 12084, 12084, 12089, 12089, 12090, 12090, 12091, 12091, 12123, 12123, 12129, 12129, 12154, 12154, 12174, 12174, 12209, 12209, 12224, 12224, 12230, 12230, 12232, 12232, 12235, 12235, 12237, 12237, 12241, 12241, 12245, 12245, 12250, 12250, 12257, 12257, 12264, 12264, 12271, 12271, 12280, 12280, 12290, 12290, 12297, 12297, 12304, 12304, 12311, 12311, 12318, 12318, 12325, 12325, 12335, 12335, 12344, 12344, 12353, 12353, 12362, 12362, 12371, 12371, 12400, 12400, 18828, 18828, 19009, 19009, 19086, 19086, 19087, 19087, 19095, 19095, 19300, 19300, 19301, 19301, 19320, 19320, 19327, 19327, 19328, 19328, 19329, 19329, 19330, 19330

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 18124-18710
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18401, 18401, 18402, 18402, 18405, 18405, 18407, 18407, 18409, 18409, 18425, 18425, 19245

### `menu_actions` (assignment, 572 lines)

- Def site: line 18809-19380
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18809, 20094, 20095, 20104, 20224, 20224, 20266, 20324, 20369, 20860, 20864, 20909, 20909, 20936, 20936, 20939
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 463 lines)

- Def site: line 8354-8816
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8395, 8395, 8400, 8400, 8410, 8410, 8418, 8418, 8423, 8423, 8428, 8428, 8438, 8438, 8443, 8443, 8448, 8448, 8468, 8468, 8478, 8478, 8479, 8479, 8482, 8482, 8512, 8512, 8598, 8598, 8600, 8600, 8624, 8624, 8630, 8630, 8635, 8635, 8644, 8644, 8648, 8648, 8667, 8667, 8670, 8670, 8681, 8681, 8682, 8682, 8777, 8777, 8798, 8798, 19368, 19368, 19369, 19369, 19370, 19370, 19371, 19371, 19372, 19372, 19373, 19373

### `OperationRegistry` (class, 461 lines)

- Def site: line 19605-20065
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20072, 20072, 20076, 20076, 20096, 20096, 20101, 20101, 20325

### `PromptUtils` (class, 441 lines)

- Def site: line 7801-8241
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7746, 7746, 7762, 7762, 7766, 7766, 7767, 7767, 7768, 7768, 7783, 7783, 7789, 7789, 7816, 7816, 7819, 7819, 7827, 7827, 7845, 7845, 7895, 7895, 7903, 7903, 7908, 7908, 7954, 7954, 7965, 7965, 7990, 7990, 8009, 8009, 8010, 8010, 8013, 8013, 8014, 8014, 8104, 8104, 8106, 8106, 8110, 8110, 8138, 8138, 8139, 8139, 8140, 8140, 8141, 8141, 8142, 8142, 8151, 8151, 8195, 8195, 8219, 8219, 12535, 12535, 12585, 12585, 12590, 12590, 12733, 12816, 12816, 12870, 12870, 12891, 12891, 12896, 12896, 13160, 13160, 13363, 13565, 13565, 13652, 13652, 13657, 13657, 13707, 13707, 13708, 13708, 15204, 15204, 15663, 17060, 17060, 17582, 17582, 18733, 18733, 18734, 18734, 19020, 19020
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 67, 195, 195
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 62, 122, 122, 127, 127

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9758-10171
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5572, 5572, 9791, 9791, 9875, 9875, 9881, 9881, 9884, 9884, 9928, 9928, 9942, 9942, 9969, 9969, 9975, 9975, 9989, 9989, 10072, 10072, 10074, 10074, 10078, 10078, 10080, 10080, 10083, 10083, 10087, 10087, 10090, 10090, 10100, 10100, 10106, 10106, 10144, 10144, 15078, 15078, 15079, 15079, 15080, 15080, 15131, 15131, 15132, 15132, 18868, 18868, 18869, 18869, 18870, 18870, 18894, 18894

### `DeviceRebootManager` (class, 398 lines)

- Def site: line 17163-17560
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17184, 17184, 17189, 17189, 17193, 17193, 17196, 17196, 17203, 17203, 17205, 17205, 17206, 17206, 17209, 17209, 17212, 17212, 17215, 17215, 17257, 17257, 17289, 17289, 17356, 17356, 17369, 17369, 17374, 17374, 17426, 17426, 17459, 17459, 17460, 17460, 17461, 17461, 17491, 17491, 17520, 17520, 17521, 17521, 19051, 19051

### `MSPInventoryExporter` (class, 388 lines)

- Def site: line 17614-18001
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17641, 17785, 17785, 19191, 19191

### `DataExporter` (class, 345 lines)

- Def site: line 6708-7052
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5668, 5668, 6754, 6754, 6770, 6770, 6771, 6771, 6794, 6794, 6796, 6796, 6799, 6799, 6813, 6813, 6815, 6815, 6824, 6824, 6826, 6826, 6827, 6827, 6833, 6833, 6834, 6834, 6834, 6851, 6851, 6855, 6855, 6897, 6897, 6928, 6928, 6931, 6931, 6933, 6933, 6979, 6979, 6989, 6989, 7022, 7022, 7027, 7027, 7034, 7034, 7256, 7256, 7288, 7288, 7299, 7299, 7324, 7324, 7344, 7344, 7858, 7858, 8651, 8651, 8930, 8930, 8945, 9009, 9009, 9026, 9026, 9044, 9044, 9065, 9065, 9624, 9624, 9699, 9699, 10029, 10029, 10380, 10380, 10465, 10481, 10601, 10601, 10605, 10605, 10625, 10625, 10638, 10638, 10642, 10642, 10660, 10660, 10822, 10822, 11169, 11169, 11316, 11316, 11393, 11393, 11397, 11397, 11402, 11402, 11535, 11535, 11554, 11554, 11605, 11605, 11608, 11608, 11759, 11759, 11762, 11762, 11861, 11861, 11867, 11867, 12164, 12164, 12181, 12181, 12196, 12196, 12410, 12410, 12438, 12438, 12454, 12454, 12491, 12491, 12529, 12529, 12618, 12618, 12647, 12647, 12685, 12685, 12736, 12801, 12801, 12807, 12807, 12849, 12849, 13018, 13018, 13024, 13024, 13143, 13143, 13151, 13151, 13315, 13315, 13366, 13539, 13539, 13710, 13710, 14223, 14223, 14584, 14584, 14590, 14590, 15498, 15498, 15557, 15664, 15800, 15800, 15818, 15818, 15836, 15836, 17107, 17107, 17128, 17967, 17967, 18052, 18052, 18073, 18073, 18559, 18559, 19220, 19220, 19236, 19236
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 70, 187, 187, 285, 285, 293, 293, 362, 362, 391, 391, 543, 543, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 379, 379, 439, 439, 456, 456, 475, 475, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 305, 305, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12857-13197
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12874, 12874, 12876, 12876, 12880, 12880, 12881, 12881, 12895, 12895, 12901, 12901, 12904, 12904, 12907, 12907, 12965, 12965, 12971, 12971, 12976, 12976, 12990, 12990, 13008, 13008, 13118, 13118, 13122, 13122, 13124, 13124, 13127, 13127, 13164, 13164, 13169, 13169, 13183, 13183, 13187, 13187, 13189, 13189, 13192, 13192, 13197, 13197, 19097, 19097, 19101, 19101, 19105, 19105

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7055-7382
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7157, 7157, 8375, 8856, 8875, 8976, 9105, 9128, 9800, 10108, 10153, 10567, 11337, 11348, 11411, 11828

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14688-15015
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12145, 12145, 12204, 12204, 12205, 12205, 13369, 14729, 14729, 14731, 14731, 14737, 14737, 14751, 14751, 14790, 14790, 14793, 14793, 14795, 14795, 14796, 14796, 14797, 14797, 14851, 14851, 14852, 14852, 14863, 14863, 14872, 14872, 14891, 14891, 14943, 14943, 14947, 14947, 14955, 14955, 14956, 14956, 14980, 14980, 14984, 14984
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 73
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 16048-16336
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16076, 16076, 16079, 16079, 16084, 16084, 16087, 16087, 16131, 16131, 16137, 16137, 16168, 16168, 16171, 16171, 16175, 16175, 16201, 16201, 16218, 16218, 16224, 16224, 16238, 16238, 16239, 16239, 16241, 16241, 16247, 16247, 16254, 16254, 16263, 16263, 16310, 16310, 16332, 16332, 16333, 16333, 16334, 16334, 19042, 19042

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 10174-10446
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10197, 10197, 10198, 10198, 10211, 10211, 10212, 10212, 10214, 10214, 10215, 10215, 10218, 10218, 10221, 10221, 10225, 10225, 10226, 10226, 10302, 10302, 10306, 10306, 10309, 10309, 10322, 10322, 10359, 10359, 10376, 10376, 10389, 10389, 10391, 10391, 10398, 10398, 10407, 10407, 10416, 10416, 10417, 10417, 10428, 10428, 10432, 10432, 10441, 10441, 10446, 10446, 19299, 19299

### `CacheUtils` (class, 264 lines)

- Def site: line 5198-5461
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5238, 5238, 5240, 5240, 5322, 5322, 5328, 5328, 5365, 5365, 5367, 5367, 5376, 5376, 5386, 5386, 5396, 5396, 5432, 5432, 7894, 7894, 9552, 9552, 9553, 9553, 9864, 9864, 10710, 10710, 10730, 10730, 12731, 15137, 15137, 15143, 15143, 15144, 15144, 15145, 15145, 15146, 15146, 15147, 15147, 15148, 15148, 15155, 15155, 15183, 15183, 15555, 15801, 15801, 15819, 15819, 15837, 15837, 15863, 17052, 17052, 17076, 17076, 17100, 17100, 17244, 17244, 17245, 17245, 17246, 17246, 17247, 17247, 17583, 17583, 18784, 18784, 19336, 19336
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 338, 338, 340, 340, 342, 342, 344, 344, 498, 498, 499, 499, 544, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 331, 331, 352, 352
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10941-11191
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10948, 10948, 10951, 10951, 10956, 10956, 10957, 10957, 10965, 10965, 10968, 10968, 10976, 10976, 11016, 11016, 11024, 11024, 11072, 11072, 11089, 11089, 11092, 11092, 11094, 11094, 11158, 11158, 11159, 11159, 19302, 19302

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15267-15511
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15133, 15133, 15293, 15293, 15295, 15295, 15296, 15296, 15297, 15297, 15325, 15325, 15330, 15330, 15352, 15352, 15353, 15353, 15395, 15395, 15403, 15403, 15429, 15429, 15438, 15438, 15446, 15446, 15477, 15477, 18873, 18873, 18877, 18877

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6131-6351
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6154, 6154, 6205, 6205, 6275, 6275, 6299, 6299, 6311, 6311, 6313, 6313, 6323, 6323, 6338, 6338, 6342, 6342, 6343, 6343, 6346, 6346, 6348, 6348, 12844, 12844, 15559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 449, 449
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 23, 68

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19386-19599
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20242, 20242, 20245, 20326, 20677

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7585-7794
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7598, 7598, 7604, 7604, 7605, 7605, 7608, 7608, 7631, 7631, 7634, 7634, 7637, 7637, 7638, 7638, 7640, 7640, 7707, 7707, 7751, 7751, 8216, 8216, 13165, 13165, 15662, 15901, 15901, 16061, 16061

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12463-12665
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12484, 12484, 12493, 12493, 12555, 12555, 12562, 12562, 12594, 12594, 12596, 12596, 12620, 12620, 12655, 12655, 12662, 12662, 12693, 12693, 15207, 15207, 18909, 18909, 18911, 18911, 18912, 18912, 18914, 18914

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13716-13903
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19259, 19259, 19260, 19260, 19261, 19261, 19262, 19262, 19263, 19263, 19264, 19264, 19265, 19265, 19266, 19266, 19268, 19268, 19269, 19269, 19270, 19270, 19271, 19271, 19272, 19272, 19273, 19273, 19274, 19274, 19276, 19276, 19277, 19277, 19278, 19278, 19279, 19279, 19280, 19280, 19281, 19281, 19282, 19282, 19283, 19283, 19284, 19284, 19286, 19286, 19287, 19287, 19288, 19288, 19289, 19289, 19290, 19290, 19291, 19291, 19292, 19292, 19293, 19293, 19294, 19294, 19296, 19296, 19297, 19297

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5543-5722
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5631, 5631, 5668, 5668, 5670, 5670, 5673, 5673, 5681, 5681, 5683, 5683, 5685, 5685, 5688, 5688, 5717, 5717, 5720, 5720, 19036, 19036

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6527-6705
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6572, 6572, 6610, 6610, 6621, 6621, 6647, 6647, 6648, 6648, 6650, 6650, 6656, 6656, 6657, 6657, 6660, 6660, 6666, 6666, 6667, 6667, 6670, 6670, 6672, 6672, 6682, 6682, 6684, 6684, 6685, 6685, 6687, 6687

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11421-11588
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11528, 11528, 11547, 11547, 11565, 11565, 11574, 11574, 11577, 11577, 11578, 11578, 11581, 11581, 11586, 11586, 11588, 11588, 18937, 18937

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11633-11800
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11670, 11670, 11672, 11672, 11675, 11675, 11746, 11746, 11748, 11748, 11761, 11761, 11765, 11765, 18940, 18940, 18941, 18941, 18942, 18942, 18980, 18980, 18985, 18985

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10666-10827
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10704, 10704, 10711, 10711, 10718, 10718, 10724, 10724, 10731, 10731, 10738, 10738, 10799, 10799, 10810, 10810, 18928, 18928, 18929, 18929, 18931, 18931, 18932, 18932, 18933, 18933

### `CLIShellManager` (class, 161 lines)

- Def site: line 15882-16042
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15905, 15905, 15907, 15907, 15976, 15976, 15978, 15978, 15997, 15997, 15999, 15999, 15999, 16015, 16015, 16031, 16031, 16032, 16032, 16038, 16038, 19041, 19041

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6359-6516
- References: 197
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5496, 5496, 6375, 6375, 6388, 6388, 6391, 6391, 6415, 6415, 6423, 6423, 6424, 6424, 6446, 6446, 6451, 6451, 6453, 6453, 6930, 6930, 6955, 6955, 7024, 7024, 7025, 7025, 7354, 7354, 7368, 7368, 7369, 7369, 7856, 7856, 7857, 7857, 8779, 8779, 8944, 9004, 9004, 9006, 9006, 9007, 9007, 9024, 9024, 9025, 9025, 9042, 9042, 9043, 9043, 9063, 9063, 9064, 9064, 9621, 9621, 9622, 9622, 9696, 9696, 9697, 9697, 10025, 10025, 10028, 10028, 10603, 10603, 10604, 10604, 10640, 10640, 10641, 10641, 10820, 10820, 10821, 10821, 11165, 11165, 11166, 11166, 11312, 11312, 11313, 11313, 11395, 11395, 11396, 11396, 11607, 11607, 11782, 11782, 11783, 11783, 11859, 11859, 11860, 11860, 12163, 12163, 12179, 12179, 12180, 12180, 12408, 12408, 12409, 12409, 12488, 12488, 12489, 12489, 12490, 12490, 12526, 12526, 12527, 12527, 12615, 12615, 12616, 12616, 12644, 12644, 12645, 12645, 12682, 12682, 12683, 12683, 12735, 12804, 12804, 12805, 12805, 12847, 12847, 12848, 12848, 13016, 13016, 13017, 13017, 13141, 13141, 13142, 13142, 13365, 13537, 13537, 14589, 14589, 15496, 15496, 15497, 15497, 15558, 15666, 17105, 17105, 17106, 17106, 17957, 17957
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 69, 152, 152, 153, 153, 158, 158, 186, 186, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 453, 453, 454, 454, 473, 473, 474, 474
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 269, 269

### `DataCollectionManager` (class, 156 lines)

- Def site: line 15029-15184
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15051, 15051, 15057, 15057, 15059, 15059, 15087, 15087, 15113, 15113, 15116, 15116, 15119, 15119, 19027, 19027, 19031, 19031, 19039, 19039

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13200-13345
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13239, 13239, 13246, 13246, 13271, 13271, 13274, 13274, 13287, 13287, 13331, 13331, 13335, 13335, 13340, 13340, 13341, 13341, 13345, 13345, 19334, 19334

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13353-13497
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12574, 12574, 12750, 12750, 12828, 12828, 12833, 12833, 13382, 13382, 13388, 13388, 13394, 13394, 13400, 13400, 13406, 13406, 13412, 13412, 13418, 13418, 13424, 13424, 13430, 13430, 13436, 13436, 13442, 13442, 13448, 13448, 13454, 13454, 13460, 13460, 13466, 13466, 13472, 13472, 13478, 13478, 13484, 13484, 13490, 13490, 13496, 13496, 18947, 18947, 19088, 19088, 19090, 19090, 19205, 19205, 19331, 19331, 19332, 19332, 19333, 19333, 19352, 19352, 19353, 19353, 19354, 19354, 19355, 19355, 19356, 19356, 19357, 19357, 19358, 19358
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 208, 208, 351, 351, 355, 355, 365, 365, 414, 414, 423, 423, 432, 432, 496, 496, 524, 524

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10520-10663
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10534, 10534, 10535, 10535, 10621, 10621, 10656, 10656, 18922, 18922, 18923, 18923, 18924, 18924, 18925, 18925, 18926, 18926

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13500-13638
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13569, 13569, 13572, 13572, 13573, 13573, 13574, 13574, 13594, 13594, 13597, 13597, 13605, 13605, 13610, 13610, 19360, 19360

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8822-8950
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8893, 8893, 8904, 8904, 15127, 15127, 15128, 15128, 18825, 18825, 18826, 18826, 19005, 19005

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11194-11322
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11201, 11201, 11206, 11206, 11207, 11207, 11208, 11208, 11211, 11211, 11212, 11212, 11275, 11275, 11282, 11282, 11309, 11309, 19304, 19304

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15652-15778
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15672, 15672, 15677, 15677, 15682, 15682, 15719, 15719, 15725, 15725, 15731, 15731, 15737, 15737, 15743, 15743, 15744, 15744, 15745, 15745, 15746, 15746, 15747, 15747, 15751, 15751, 15760, 15760, 15764, 15764, 15767, 15767, 15773, 15773, 19000, 19000

### `EnvironmentUtils` (class, 125 lines)

- Def site: line 5776-5900
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5797, 5797, 5799, 5799, 5815, 5815, 5827, 5827, 5866, 5866, 5867, 5867, 5868, 5868, 5869, 5869, 5870, 5870, 5881, 5881, 5884, 5884, 6812, 6812, 20339, 20339, 20922, 20922

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8956-9067
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7894, 7894, 9552, 9552, 9864, 9864, 10710, 10710, 10730, 10730, 12732, 15076, 15076, 15129, 15129, 15562, 15802, 15802, 15820, 15820, 15838, 15838, 17054, 17054, 17078, 17078, 17102, 17102, 17245, 17245, 17586, 17586, 18866, 18866, 18881, 18881, 18891, 18891, 18891, 18891, 18901, 18901
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 338, 338, 499, 499, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 109 lines)

- Def site: line 10830-10938
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10885, 10885, 10888, 10888, 10889, 10889, 10894, 10894, 10912, 10912, 10912, 10921, 10921, 10921, 10921, 10922, 10922, 10922, 10922, 10980, 10980, 10983, 10983, 10995, 10995, 10996, 10996, 11009, 11009, 11048, 11048, 11056, 11056, 11110, 11110, 11118, 11118

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12755-12854
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12820, 12820, 12822, 12822, 12823, 12823, 18875, 18875, 18943, 18943, 18945, 18945, 18946, 18946

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15544-15641
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15287, 15287, 15522, 15522, 15580, 15580, 15586, 15586, 15592, 15592, 15598, 15598, 15604, 15604, 15610, 15610, 15616, 15616, 15622, 15622, 15628, 15628, 15634, 15634, 15640, 15640, 15864, 17246, 17246, 17249, 17249, 17585, 17585, 18832, 18832, 18899, 18899, 18905, 18905, 18956, 18956, 19013, 19013
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 76, 92, 340, 340, 346, 346, 402, 402, 404, 404, 408, 408, 411, 411, 414, 414, 415, 415, 458, 458, 459, 459, 491, 491, 492, 492, 508, 508, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8252-8348
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8308, 8308, 8344, 8344

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11325-11418
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11377, 11377, 11390, 11390, 18935, 18935, 18977, 18977, 18978, 18978, 18983, 18983, 18984, 18984

### `ValidationUtils` (class, 90 lines)

- Def site: line 5906-5995
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5988, 5988, 15350, 15350, 15351, 15351, 15565, 18735, 18735
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 49
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 26, 138, 138, 139, 139

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12668-12752
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12702, 12702, 18910, 18910, 18918, 18918, 18944, 18944, 19089, 19089

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 18028-18106
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18023, 18023, 18024, 18024, 19184, 19184
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 17032-17109
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19055, 19055, 19059, 19059, 19063, 19063
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1904-1977
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1917, 1917, 1949, 1949, 2294, 2294, 2321, 2321, 7606, 7606, 7692, 7692, 7822, 7822, 7899, 7899, 7982, 7982, 8212, 8212, 8401, 8401, 8457, 8457, 8470, 8470, 8487, 8487, 8532, 8532, 8563, 8563, 8569, 8569, 8672, 8672, 10213, 10213, 10480, 10982, 10982, 11011, 11011, 11276, 11276, 11482, 11482, 11721, 11721, 12437, 12437, 12453, 12453, 13240, 13240, 13659, 13659, 13709, 13709, 15563, 15765, 15765, 15798, 15798, 15816, 15816, 15834, 15834, 15862, 17059, 17059, 17084, 17084, 17127, 17226, 17226, 17438, 17438, 17581, 17581, 17688, 17688, 18018, 18018, 18048, 18048, 18069, 18069, 18088, 18088, 18104, 18104, 18682, 18682, 18702, 18702, 18737, 18737, 18750, 18750, 19218, 19218, 19309, 19309, 19314, 19314, 19320, 19320, 19339, 19339, 19345, 19345, 20945, 20945
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

- Def site: line 15190-15261
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19021, 19021, 19022, 19022, 19023, 19023, 19024, 19024

### `DisplayUtils` (class, 70 lines)

- Def site: line 5467-5536
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5499, 5499, 5500, 5500, 5515, 5515, 5517, 5517

### `ConfigUtils` (class, 70 lines)

- Def site: line 6001-6070
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6043, 6043, 6048, 6048, 6145, 6145, 6203, 6203, 7090, 7090, 7749, 7749, 8394, 8394, 8417, 8417, 8437, 8437, 8622, 8622, 8643, 8643, 8918, 8918, 8943, 8943, 8998, 8998, 9020, 9020, 9037, 9037, 9054, 9054, 9439, 9439, 9662, 9662, 9679, 9679, 10071, 10071, 10403, 10403, 10614, 10614, 10651, 10651, 10804, 10804, 10947, 10947, 11200, 11200, 11388, 11388, 11572, 11572, 11891, 11891, 12227, 12227, 12399, 12399, 12439, 12439, 12445, 12445, 12539, 12539, 12769, 12769, 12842, 12842, 13329, 13329, 13364, 13563, 13563, 15070, 15070, 15286, 15286, 15554, 15661, 15761, 15761, 15796, 15796, 15814, 15814, 15832, 15832, 17125, 18019, 18019, 18021, 18021, 18045, 18045, 18049, 18049, 18050, 18050, 18070, 18070, 18071, 18071, 18216, 18216, 18786, 18786, 18818, 18818, 18855, 18855, 18861, 18861, 18989, 18989, 19046, 19046, 19129, 19129, 19138, 19138, 19216, 19216, 19217, 19217, 19234, 19234, 19309, 19309, 19314, 19314, 19320, 19320, 19339, 19339, 19345, 19345, 20256, 20256, 20327, 20809, 20809, 20897, 20897
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 68, 245, 245, 555, 555, 556, 556
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 38, 401, 401, 448, 448, 466, 466, 507, 507, 541, 541
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 25, 316, 316
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 22, 67

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10449-10517
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10489, 10489, 10494, 10494, 10499, 10499, 10500, 10500, 10506, 10506, 10507, 10507, 10513, 10513, 10514, 10514, 10515, 10515, 10516, 10516, 19362, 19362

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18741-18806
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18789, 18789, 18797, 18797, 18806, 18806, 19335, 19335

### `GatewayTemplateConfigManager` (class, 56 lines)

- Def site: line 15785-15840
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18960, 18960, 18964, 18964, 19169, 19169

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6076-6122
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6200, 6200, 8084, 8084, 8999, 8999, 9022, 9022, 9509, 9509, 9544, 9544, 9558, 9558, 9681, 9681, 9685, 9685, 10233, 10233, 12543, 12543, 13213, 13213, 13339, 13339, 13371, 13549, 13549, 13585, 13585, 15560, 17909, 17909, 18020, 18020, 18051, 18051, 18072, 18072, 19219, 19219, 19235, 19235, 20828, 20828
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 75, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 514, 514, 525, 525

### `FilePathUtils` (class, 46 lines)

- Def site: line 5725-5770
- References: 97
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5237, 5237, 5279, 5279, 5324, 5324, 5430, 5430, 5445, 5445, 5715, 5715, 5716, 5716, 5760, 5760, 6226, 6226, 7918, 7918, 9209, 9209, 9520, 9520, 9536, 9536, 9865, 9865, 10746, 10746, 10765, 10765, 12734, 15153, 15153, 15556, 15799, 15799, 15817, 15817, 15835, 15835, 15865, 16287, 16287, 16327, 16327, 16328, 16328, 16329, 16329, 17051, 17051, 17075, 17075, 17079, 17079, 17099, 17099, 17126, 17201, 17201, 17235, 17235, 17256, 17256, 17288, 17288, 17350, 17350, 17389, 17389, 17539, 17539, 17584, 17584
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 148, 148, 226, 226, 234, 234, 242, 242, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 31, 355, 355
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 17115-17157
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17138, 17138, 17144, 17144, 17150, 17150, 17156, 17156, 19153, 19153, 19157, 19157, 19161, 19161, 19165, 19165

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11591-11630
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11628, 11628, 19359, 19359

### `TimeUtils` (class, 29 lines)

- Def site: line 1868-1896
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8872, 8872, 8873, 8873, 8902, 8902, 8903, 8903, 8919, 8919, 8920, 8920, 9798, 9798, 9799, 9799, 10103, 10103, 10104, 10104, 10151, 10151, 10152, 10152, 10707, 10707, 10709, 10709, 10727, 10727, 10729, 10729, 11617, 11617, 11618, 11618, 12278, 12278, 12279, 12279, 12384, 12384, 12385, 12385, 13367
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 71, 206, 206, 207, 207

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15514-15541
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15528, 15528, 15534, 15534, 15540, 15540, 19067, 19067, 19071, 19071
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 198, 198, 242, 242, 245, 245, 261, 261, 303, 303, 306, 306, 322, 322, 324, 324, 325, 325, 332, 332, 342, 342, 345, 345, 346, 346, 353, 353, 372, 372, 381, 381, 382, 382, 383, 383, 400, 400, 401, 401, 454, 454

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15851-15876
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15871, 15871, 15876, 15876, 19075, 19075, 19080, 19080
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13666-13687
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18841, 18841, 18845, 18845, 18849, 18849
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17567-17588
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18988, 18988, 19045, 19045, 19128, 19128, 19137, 19137

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 18004-18025
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19198, 19198
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `execute_with_connection_pool_management` (function, 21 lines)

- Def site: line 7556-7576
- References: 7
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6309, 10076, 15399, 15564
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32

### `EndpointConfig` (class, 10 lines)

- Def site: line 13912-13921
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13948, 14084, 14161, 14180, 14192, 14213, 14226, 14237, 14243, 14256, 14349, 14484, 14579

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 331-339
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

- Def site: line 358-366
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15222, 15239, 15255
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 343-350
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

- Def site: line 318-320
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13372, 13661, 18053, 18074, 18203, 18234, 18266, 18501, 18516
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 32, 76, 337

### `tqdm` (function, 3 lines)

- Def site: line 635-637
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1245, 1914, 1914, 1914, 1926, 1932, 6202, 6322, 7378, 7440, 9608, 9719, 9973, 10803, 13374, 15432, 15474, 15572, 19221
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

- Def site: line 2016-2018
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2016, 7388, 7395, 7396, 9984, 15421

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2030-2032
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2030, 15568
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 52, 543
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 751-1755
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1800

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
