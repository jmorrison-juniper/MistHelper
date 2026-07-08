# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 231 first-party files
- Definitions analyzed: 46
- LOC saveable (unused + single-use): 12
- Category counts: unused=0, single-use=2, low-use=2, hot=41, skipped=1

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
| `OrgInventoryExporter` | class | 686 | 104 | hot |  | oversize_25_lines,missing_inline_comments |
| `OrgExportUtils` | class | 653 | 110 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `menu_actions` | assignment | 608 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgTicketManager` | class | 475 | 66 | hot |  | oversize_25_lines |
| `PromptUtils` | class | 441 | 104 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 396 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DataExporter` | class | 345 | 168 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 81 | hot |  | oversize_25_lines |
| `GlobalWiredClientReportGenerator` | class | 251 | 32 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `GatewayTestExporter` | class | 245 | 32 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `APIFetchUtils` | class | 221 | 34 | hot |  | oversize_25_lines |
| `PromptClientUtils` | class | 210 | 29 | hot |  | oversize_25_lines,raw_input_call |
| `DatabaseSchemaUtils` | class | 179 | 34 | hot |  | oversize_25_lines |
| `DataProcessingUtils` | class | 158 | 125 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `SiteExportUtils` | class | 145 | 86 | hot |  | oversize_25_lines,missing_action_logging |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgSiteExporter` | class | 112 | 43 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 110 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `GatewayExportUtils` | class | 98 | 78 | hot |  | oversize_25_lines,missing_action_logging |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 233 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 148 | hot |  | oversize_25_lines |
| `APICoreFetchUtils` | class | 47 | 43 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 86 | hot |  | oversize_25_lines,missing_inline_comments |
| `TimeUtils` | class | 29 | 27 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
| `SSHRunnerManager` | class | 26 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 2 | low-use | DetectMspPrivilegesManager | missing_action_logging |
| `RoutingUtils` | class | 22 | 12 | hot |  | missing_inline_comments,missing_action_logging |
| `SiteAutoUpgradeConfigurator` | class | 22 | 6 | hot |  | missing_inline_comments,missing_action_logging |
| `SSHConnectionConfig` | class | 9 | 6 | hot |  | missing_action_logging |
| `DeviceFetchConfig` | class | 9 | 1 | single-use | DeviceDataFetcherManager | missing_action_logging |
| `SSHExecutionConfig` | class | 8 | 5 | hot |  | missing_inline_comments,missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 3 | low-use | FastModeMaxConcurrentConnectionsManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 1 | single-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Single-Use (2)

### `DeviceFetchConfig` (class, 9 lines)

- Def site: line 448-456
- References: 1
- Suggested class: `DeviceDataFetcherManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`
- Rationale: Sole caller lives in `device_data_fetcher.py` inside `__init__()`; move `DeviceFetchConfig` into that module's semantic class so callers rewrite in one PR
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2111-2113
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2111

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2220-2244
- References: 2
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2350, 14205

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2108-2110
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2108, 8969, 11595

## Hot (41)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2958-5284
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2958, 6289, 6290, 6299, 6463

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8055-8740
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8178, 8178, 8229, 8229, 8232, 8232, 8273, 8273, 8312, 8312, 8330, 8330, 8408, 8408, 8415, 8415, 8425, 8425, 8428, 8428, 8441, 8441, 8442, 8442, 8443, 8443, 8444, 8444, 8452, 8452, 8454, 8454, 8455, 8455, 8456, 8456, 8457, 8457, 8460, 8460, 8463, 8463, 8466, 8466, 8469, 8469, 8515, 8515, 8538, 8538, 8539, 8539, 8540, 8540, 8542, 8542, 8578, 8578, 8594, 8594, 8648, 8648, 8649, 8649, 8650, 8650, 8653, 8653, 8654, 8654, 8673, 8673, 8675, 8675, 8676, 8676, 8711, 8711, 11735, 12335, 12335, 12359, 12359, 12383, 12383, 12501, 12501, 13065, 13065, 13072, 13072, 13081, 13081, 13085, 13085, 13094, 13094
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgExportUtils` (class, 653 lines)

- Def site: line 9825-10477
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9897, 9897, 9919, 9919, 9922, 9922, 9948, 9948, 9957, 9957, 9958, 9958, 9979, 9979, 10022, 10022, 10068, 10068, 10079, 10079, 10106, 10106, 10111, 10111, 10112, 10112, 10113, 10113, 10145, 10145, 10151, 10151, 10176, 10176, 10196, 10196, 10231, 10231, 10246, 10246, 10252, 10252, 10254, 10254, 10257, 10257, 10259, 10259, 10263, 10263, 10267, 10267, 10272, 10272, 10279, 10279, 10286, 10286, 10293, 10293, 10302, 10302, 10312, 10312, 10319, 10319, 10326, 10326, 10333, 10333, 10340, 10340, 10347, 10347, 10357, 10357, 10366, 10366, 10375, 10375, 10384, 10384, 10393, 10393, 10422, 10422, 13026, 13026, 13225, 13225, 13302, 13302, 13303, 13303, 13311, 13311, 13534, 13534, 13535, 13535, 13554, 13554, 13561, 13561, 13562, 13562, 13563, 13563, 13564, 13564

### `menu_actions` (assignment, 608 lines)

- Def site: line 13007-13614
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13007, 13649, 13650, 13659, 13779, 13779, 13821, 13877, 13922, 14413, 14417, 14462, 14462, 14489, 14489, 14492
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 475 lines)

- Def site: line 7458-7932
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7499, 7499, 7504, 7504, 7514, 7514, 7522, 7522, 7527, 7527, 7532, 7532, 7545, 7545, 7550, 7550, 7555, 7555, 7575, 7575, 7585, 7585, 7586, 7586, 7589, 7589, 7619, 7619, 7708, 7708, 7710, 7710, 7737, 7737, 7743, 7743, 7748, 7748, 7757, 7757, 7761, 7761, 7780, 7780, 7783, 7783, 7794, 7794, 7795, 7795, 7893, 7893, 7914, 7914, 13602, 13602, 13603, 13603, 13604, 13604, 13605, 13605, 13606, 13606, 13607, 13607

### `PromptUtils` (class, 441 lines)

- Def site: line 7006-7446
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6951, 6951, 6967, 6967, 6971, 6971, 6972, 6972, 6973, 6973, 6988, 6988, 6994, 6994, 7021, 7021, 7024, 7024, 7032, 7032, 7050, 7050, 7100, 7100, 7108, 7108, 7113, 7113, 7159, 7159, 7170, 7170, 7195, 7195, 7214, 7214, 7215, 7215, 7218, 7218, 7219, 7219, 7309, 7309, 7311, 7311, 7315, 7315, 7343, 7343, 7344, 7344, 7345, 7345, 7346, 7346, 7347, 7347, 7356, 7356, 7400, 7400, 7424, 7424, 10507, 10507, 10528, 10528, 10533, 10533, 10797, 10797, 10855, 11006, 11006, 11011, 11011, 11061, 11061, 11062, 11062, 11837, 12342, 12342, 12833, 12833, 12992, 12992, 12993, 12993, 13236, 13236
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 8743-9156
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8776, 8776, 8860, 8860, 8866, 8866, 8869, 8869, 8913, 8913, 8927, 8927, 8954, 8954, 8960, 8960, 8974, 8974, 9057, 9057, 9059, 9059, 9063, 9063, 9065, 9065, 9068, 9068, 9072, 9072, 9075, 9075, 9085, 9085, 9091, 9091, 9129, 9129, 13066, 13066, 13067, 13067, 13068, 13068, 13092, 13092

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 12420-12815
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12441, 12441, 12446, 12446, 12450, 12450, 12453, 12453, 12460, 12460, 12462, 12462, 12463, 12463, 12466, 12466, 12469, 12469, 12472, 12472, 12514, 12514, 12546, 12546, 12613, 12613, 12626, 12626, 12631, 12631, 12681, 12681, 12714, 12714, 12715, 12715, 12716, 12716, 12746, 12746, 12775, 12775, 12776, 12776, 13267, 13267

### `DataExporter` (class, 345 lines)

- Def site: line 6430-6774
- References: 168
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6476, 6476, 6492, 6492, 6493, 6493, 6516, 6516, 6518, 6518, 6521, 6521, 6535, 6535, 6537, 6537, 6546, 6546, 6548, 6548, 6549, 6549, 6555, 6555, 6556, 6556, 6556, 6573, 6573, 6577, 6577, 6619, 6619, 6650, 6650, 6653, 6653, 6655, 6655, 6701, 6701, 6711, 6711, 6744, 6744, 6749, 6749, 6756, 6756, 7063, 7063, 7764, 7764, 7994, 7994, 8011, 8011, 8029, 8029, 8050, 8050, 8609, 8609, 8684, 8684, 9014, 9014, 9365, 9365, 9784, 9784, 9883, 9883, 9889, 9889, 10186, 10186, 10203, 10203, 10218, 10218, 10432, 10432, 10460, 10460, 10476, 10476, 10655, 10655, 10661, 10661, 10780, 10780, 10788, 10788, 10858, 11064, 11064, 11672, 11672, 11731, 11838, 12389, 12389, 12409, 12916, 12916, 12937, 12937, 13163, 13163, 13176, 13176, 13390, 13390, 13445, 13445, 13461, 13461
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 10494-10834
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10511, 10511, 10513, 10513, 10517, 10517, 10518, 10518, 10532, 10532, 10538, 10538, 10541, 10541, 10544, 10544, 10602, 10602, 10608, 10608, 10613, 10613, 10627, 10627, 10645, 10645, 10755, 10755, 10759, 10759, 10761, 10761, 10764, 10764, 10801, 10801, 10806, 10806, 10820, 10820, 10824, 10824, 10826, 10826, 10829, 10829, 10834, 10834, 13313, 13313, 13317, 13317, 13321, 13321

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 11090-11417
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10167, 10167, 10226, 10226, 10227, 10227, 10861, 11131, 11131, 11133, 11133, 11139, 11139, 11153, 11153, 11192, 11192, 11195, 11195, 11197, 11197, 11198, 11198, 11199, 11199, 11253, 11253, 11254, 11254, 11265, 11265, 11274, 11274, 11293, 11293, 11345, 11345, 11349, 11349, 11357, 11357, 11358, 11358, 11382, 11382, 11386, 11386
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 12003-12291
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12031, 12031, 12034, 12034, 12039, 12039, 12042, 12042, 12086, 12086, 12092, 12092, 12123, 12123, 12126, 12126, 12130, 12130, 12156, 12156, 12173, 12173, 12179, 12179, 12193, 12193, 12194, 12194, 12196, 12196, 12202, 12202, 12209, 12209, 12218, 12218, 12265, 12265, 12287, 12287, 12288, 12288, 12289, 12289, 13258, 13258

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9159-9431
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9182, 9182, 9183, 9183, 9196, 9196, 9197, 9197, 9199, 9199, 9200, 9200, 9203, 9203, 9206, 9206, 9210, 9210, 9211, 9211, 9287, 9287, 9291, 9291, 9294, 9294, 9307, 9307, 9344, 9344, 9361, 9361, 9374, 9374, 9376, 9376, 9383, 9383, 9392, 9392, 9401, 9401, 9402, 9402, 9413, 9413, 9417, 9417, 9426, 9426, 9431, 9431, 13533, 13533

### `CacheUtils` (class, 264 lines)

- Def site: line 5290-5553
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5330, 5330, 5332, 5332, 5414, 5414, 5420, 5420, 5457, 5457, 5459, 5459, 5468, 5468, 5478, 5478, 5488, 5488, 5524, 5524, 7099, 7099, 8537, 8537, 8538, 8538, 8849, 8849, 11729, 11980, 12334, 12334, 12358, 12358, 12382, 12382, 12501, 12501, 12502, 12502, 12503, 12503, 12504, 12504, 12834, 12834, 13164, 13164, 13177, 13177, 13391, 13391, 13570, 13570
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 9556-9806
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9563, 9563, 9566, 9566, 9571, 9571, 9572, 9572, 9580, 9580, 9583, 9583, 9591, 9591, 9631, 9631, 9639, 9639, 9687, 9687, 9704, 9704, 9707, 9707, 9709, 9709, 9773, 9773, 9774, 9774, 13536, 13536

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 11441-11685
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11467, 11467, 11469, 11469, 11470, 11470, 11471, 11471, 11499, 11499, 11504, 11504, 11526, 11526, 11527, 11527, 11569, 11569, 11577, 11577, 11603, 11603, 11612, 11612, 11620, 11620, 11651, 11651, 13071, 13071, 13075, 13075

### `APIFetchUtils` (class, 221 lines)

- Def site: line 5853-6073
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5876, 5876, 5927, 5927, 5997, 5997, 6021, 6021, 6033, 6033, 6035, 6035, 6045, 6045, 6060, 6060, 6064, 6064, 6065, 6065, 6068, 6068, 6070, 6070, 11733
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `PromptClientUtils` (class, 210 lines)

- Def site: line 6790-6999
- References: 29
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6803, 6803, 6809, 6809, 6810, 6810, 6813, 6813, 6836, 6836, 6839, 6839, 6842, 6842, 6843, 6843, 6845, 6845, 6912, 6912, 6956, 6956, 7421, 7421, 10802, 10802, 11836, 12016, 12016

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6249-6427
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6294, 6294, 6332, 6332, 6343, 6343, 6369, 6369, 6370, 6370, 6372, 6372, 6378, 6378, 6379, 6379, 6382, 6382, 6388, 6388, 6389, 6389, 6392, 6392, 6394, 6394, 6404, 6404, 6406, 6406, 6407, 6407, 6409, 6409

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6081-6238
- References: 125
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6097, 6097, 6110, 6110, 6113, 6113, 6137, 6137, 6145, 6145, 6146, 6146, 6168, 6168, 6173, 6173, 6175, 6175, 6652, 6652, 6677, 6677, 6746, 6746, 6747, 6747, 7061, 7061, 7062, 7062, 7895, 7895, 7989, 7989, 7991, 7991, 7992, 7992, 8009, 8009, 8010, 8010, 8027, 8027, 8028, 8028, 8048, 8048, 8049, 8049, 8606, 8606, 8607, 8607, 8681, 8681, 8682, 8682, 9010, 9010, 9013, 9013, 9780, 9780, 9781, 9781, 9881, 9881, 9882, 9882, 10185, 10185, 10201, 10201, 10202, 10202, 10430, 10430, 10431, 10431, 10653, 10653, 10654, 10654, 10778, 10778, 10779, 10779, 10857, 11670, 11670, 11671, 11671, 11732, 11840, 12387, 12387, 12388, 12388
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `SiteExportUtils` (class, 145 lines)

- Def site: line 10845-10989
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10874, 10874, 10880, 10880, 10886, 10886, 10892, 10892, 10898, 10898, 10904, 10904, 10910, 10910, 10916, 10916, 10922, 10922, 10928, 10928, 10934, 10934, 10940, 10940, 10946, 10946, 10952, 10952, 10958, 10958, 10964, 10964, 10970, 10970, 10976, 10976, 10982, 10982, 10988, 10988, 13145, 13145, 13304, 13304, 13306, 13306, 13430, 13430, 13565, 13565, 13566, 13566, 13567, 13567, 13586, 13586, 13587, 13587, 13588, 13588, 13589, 13589, 13590, 13590, 13591, 13591, 13592, 13592
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 11826-11952
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11846, 11846, 11851, 11851, 11856, 11856, 11893, 11893, 11899, 11899, 11905, 11905, 11911, 11911, 11917, 11917, 11918, 11918, 11919, 11919, 11920, 11920, 11921, 11921, 11925, 11925, 11934, 11934, 11938, 11938, 11941, 11941, 11947, 11947, 13216, 13216

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 7941-8052
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7099, 7099, 8537, 8537, 8849, 8849, 11736, 12336, 12336, 12360, 12360, 12384, 12384, 12502, 12502, 12837, 12837, 13064, 13064, 13079, 13079, 13089, 13089, 13089, 13089, 13099, 13099, 13165, 13165, 13178, 13178, 13392, 13392
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 9444-9553
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9499, 9499, 9502, 9502, 9503, 9503, 9508, 9508, 9527, 9527, 9527, 9536, 9536, 9536, 9536, 9537, 9537, 9537, 9537, 9595, 9595, 9598, 9598, 9610, 9610, 9611, 9611, 9624, 9624, 9663, 9663, 9671, 9671, 9725, 9725, 9733, 9733

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 11718-11815
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11461, 11461, 11696, 11696, 11754, 11754, 11760, 11760, 11766, 11766, 11772, 11772, 11778, 11778, 11784, 11784, 11790, 11790, 11796, 11796, 11802, 11802, 11808, 11808, 11814, 11814, 11981, 12503, 12503, 12506, 12506, 12836, 12836, 13030, 13030, 13097, 13097, 13103, 13103, 13154, 13154, 13229, 13229
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `ValidationUtils` (class, 90 lines)

- Def site: line 5628-5717
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5710, 5710, 11524, 11524, 11525, 11525, 11739, 12994, 12994
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 12892-12970
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12887, 12887, 12888, 12888, 13409, 13409
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 12314-12391
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13271, 13271, 13275, 13275, 13279, 13279
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1996-2069
- References: 233
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2009, 2009, 2041, 2041, 2386, 2386, 2413, 2413, 6811, 6811, 6897, 6897, 7027, 7027, 7104, 7104, 7187, 7187, 7417, 7417, 7505, 7505, 7564, 7564, 7577, 7577, 7594, 7594, 7639, 7639, 7673, 7673, 7679, 7679, 7785, 7785, 9198, 9198, 9597, 9597, 9626, 9626, 10459, 10459, 10475, 10475, 11013, 11013, 11063, 11063, 11737, 11939, 11939, 11979, 12341, 12341, 12366, 12366, 12408, 12483, 12483, 12693, 12693, 12832, 12832, 12882, 12882, 12912, 12912, 12933, 12933, 12952, 12952, 12968, 12968, 12996, 12996, 13161, 13161, 13174, 13174, 13388, 13388, 13443, 13443, 13543, 13543, 13548, 13548, 13554, 13554, 13573, 13573, 13579, 13579, 14498, 14498
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 48, 550, 550
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 20, 226, 226, 244, 244, 313, 313
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 411, 411
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 27, 66, 82, 82, 107, 107, 220, 220
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\_maps_clone.py`: lines 123, 123, 164, 164
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\_maps_wizard.py`: lines 179, 179, 295, 295, 333, 333, 688, 688, 761, 761
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 227, 227, 280, 280, 462, 462, 994, 994, 1012, 1012, 1021, 1021, 1024, 1024, 1027, 1027, 1213, 1213, 1277, 1277, 1383, 1383, 1451, 1451, 1488, 1488, 1668, 1668, 1838, 1838, 2659, 2659, 2662, 2662, 2677, 2677, 2764, 2764
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\address_corrector.py`: lines 79, 79
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 246, 246, 282, 282, 342, 342, 885, 885, 897, 897
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\comparison_display.py`: lines 82, 82
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\ui_geocoder.py`: lines 173, 173, 207, 207, 227, 227
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\runtime\app_runner.py`: lines 257, 257
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\runtime\interactive_mode.py`: lines 33, 33, 50, 50, 74, 74, 104, 104, 127, 127, 140, 140
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ui\execution\item_executor.py`: lines 224, 224
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\utils\input_utils.py`: lines 42, 42, 44, 44, 46, 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 14, 44, 452, 452, 512, 512, 609, 609, 690, 690, 706, 706, 717, 717, 729, 729, 742, 742
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 18, 66, 197, 197

### `ConfigUtils` (class, 70 lines)

- Def site: line 5723-5792
- References: 148
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5765, 5765, 5770, 5770, 5867, 5867, 5925, 5925, 6954, 6954, 7498, 7498, 7521, 7521, 7544, 7544, 7735, 7735, 7756, 7756, 7983, 7983, 8005, 8005, 8022, 8022, 8039, 8039, 8424, 8424, 8647, 8647, 8664, 8664, 9056, 9056, 9388, 9388, 9562, 9562, 9913, 9913, 10249, 10249, 10421, 10421, 10461, 10461, 10467, 10467, 10856, 11460, 11460, 11728, 11835, 11935, 11935, 12406, 12883, 12883, 12885, 12885, 12909, 12909, 12913, 12913, 12914, 12914, 12934, 12934, 12935, 12935, 13016, 13016, 13053, 13053, 13059, 13059, 13159, 13159, 13172, 13172, 13205, 13205, 13262, 13262, 13345, 13345, 13354, 13354, 13386, 13386, 13441, 13441, 13442, 13442, 13459, 13459, 13543, 13543, 13548, 13548, 13554, 13554, 13573, 13573, 13579, 13579, 13811, 13811, 13880, 14362, 14362, 14450, 14450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 5798-5844
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5922, 5922, 7289, 7289, 7984, 7984, 8007, 8007, 8494, 8494, 8529, 8529, 8543, 8543, 8666, 8666, 8670, 8670, 9218, 9218, 10863, 11734, 12884, 12884, 12915, 12915, 12936, 12936, 13444, 13444, 13460, 13460, 14381, 14381
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5571-5616
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5329, 5329, 5371, 5371, 5416, 5416, 5522, 5522, 5537, 5537, 5606, 5606, 5948, 5948, 7123, 7123, 8194, 8194, 8505, 8505, 8521, 8521, 8850, 8850, 11730, 11982, 12242, 12242, 12282, 12282, 12283, 12283, 12284, 12284, 12333, 12333, 12357, 12357, 12361, 12361, 12381, 12381, 12407, 12458, 12458, 12492, 12492, 12513, 12513, 12545, 12545, 12607, 12607, 12646, 12646, 12794, 12794, 12835, 12835, 13162, 13162, 13175, 13175, 13389, 13389
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `TimeUtils` (class, 29 lines)

- Def site: line 1960-1988
- References: 27
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8783, 8783, 8784, 8784, 9088, 9088, 9089, 9089, 9136, 9136, 9137, 9137, 10300, 10300, 10301, 10301, 10406, 10406, 10407, 10407, 10859
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 11688-11715
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11702, 11702, 11708, 11708, 11714, 11714, 13283, 13283, 13287, 13287
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 11968-11993
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11988, 11988, 11993, 11993, 13291, 13291, 13296, 13296
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 11020-11041
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13039, 13039, 13043, 13043, 13047, 13047
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 12868-12889
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13423, 13423
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 421-429
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

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 433-440
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

- Def site: line 727-729
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1337, 2006, 2006, 2006, 2018, 2024, 5924, 6044, 8593, 8704, 8958, 10866, 11606, 11648, 11746, 13446
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_data_fetcher.py`: lines 359
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\org_client_security_exporter.py`: lines 177
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 35, 79, 163
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 58
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 41, 217, 260
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\connection_pool_executor.py`: lines 137
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\wanprobe_config_manager.py`: lines 243, 363
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 916, 918

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2122-2124
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2122, 11742
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 843-1847
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1892

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
