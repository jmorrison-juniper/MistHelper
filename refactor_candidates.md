# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 230 first-party files
- Definitions analyzed: 47
- LOC saveable (unused + single-use): 12
- Category counts: unused=0, single-use=2, low-use=2, hot=42, skipped=1

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
| `PromptUtils` | class | 441 | 110 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 396 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DataExporter` | class | 345 | 176 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 81 | hot |  | oversize_25_lines |
| `GlobalWiredClientReportGenerator` | class | 251 | 32 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `GatewayTestExporter` | class | 245 | 32 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `APIFetchUtils` | class | 221 | 34 | hot |  | oversize_25_lines |
| `PromptClientUtils` | class | 210 | 29 | hot |  | oversize_25_lines,raw_input_call |
| `SiteDeviceExporter` | class | 203 | 26 | hot |  | oversize_25_lines,non_ascii_logs |
| `DatabaseSchemaUtils` | class | 179 | 34 | hot |  | oversize_25_lines |
| `DataProcessingUtils` | class | 158 | 143 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `SiteExportUtils` | class | 145 | 88 | hot |  | oversize_25_lines,missing_action_logging |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `OrgSiteExporter` | class | 112 | 43 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 110 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `GatewayExportUtils` | class | 98 | 78 | hot |  | oversize_25_lines,missing_action_logging |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 233 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 150 | hot |  | oversize_25_lines |
| `APICoreFetchUtils` | class | 47 | 45 | hot |  | oversize_25_lines,missing_inline_comments |
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

- Def site: line 445-453
- References: 1
- Suggested class: `DeviceDataFetcherManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`
- Rationale: Sole caller lives in `device_data_fetcher.py` inside `__init__()`; move `DeviceFetchConfig` into that module's semantic class so callers rewrite in one PR
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2108-2110
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2108

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2217-2241
- References: 2
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2347, 14404

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2105-2107
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2105, 8966, 11794

## Hot (42)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2955-5281
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2955, 6286, 6287, 6296, 6460

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8052-8737
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8175, 8175, 8226, 8226, 8229, 8229, 8270, 8270, 8309, 8309, 8327, 8327, 8405, 8405, 8412, 8412, 8422, 8422, 8425, 8425, 8438, 8438, 8439, 8439, 8440, 8440, 8441, 8441, 8449, 8449, 8451, 8451, 8452, 8452, 8453, 8453, 8454, 8454, 8457, 8457, 8460, 8460, 8463, 8463, 8466, 8466, 8512, 8512, 8535, 8535, 8536, 8536, 8537, 8537, 8539, 8539, 8575, 8575, 8591, 8591, 8645, 8645, 8646, 8646, 8647, 8647, 8650, 8650, 8651, 8651, 8670, 8670, 8672, 8672, 8673, 8673, 8708, 8708, 11934, 12534, 12534, 12558, 12558, 12582, 12582, 12700, 12700, 13264, 13264, 13271, 13271, 13280, 13280, 13284, 13284, 13293, 13293
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgExportUtils` (class, 653 lines)

- Def site: line 9822-10474
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9894, 9894, 9916, 9916, 9919, 9919, 9945, 9945, 9954, 9954, 9955, 9955, 9976, 9976, 10019, 10019, 10065, 10065, 10076, 10076, 10103, 10103, 10108, 10108, 10109, 10109, 10110, 10110, 10142, 10142, 10148, 10148, 10173, 10173, 10193, 10193, 10228, 10228, 10243, 10243, 10249, 10249, 10251, 10251, 10254, 10254, 10256, 10256, 10260, 10260, 10264, 10264, 10269, 10269, 10276, 10276, 10283, 10283, 10290, 10290, 10299, 10299, 10309, 10309, 10316, 10316, 10323, 10323, 10330, 10330, 10337, 10337, 10344, 10344, 10354, 10354, 10363, 10363, 10372, 10372, 10381, 10381, 10390, 10390, 10419, 10419, 13225, 13225, 13424, 13424, 13501, 13501, 13502, 13502, 13510, 13510, 13733, 13733, 13734, 13734, 13753, 13753, 13760, 13760, 13761, 13761, 13762, 13762, 13763, 13763

### `menu_actions` (assignment, 608 lines)

- Def site: line 13206-13813
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13206, 13848, 13849, 13858, 13978, 13978, 14020, 14076, 14121, 14612, 14616, 14661, 14661, 14688, 14688, 14691
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 475 lines)

- Def site: line 7455-7929
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7496, 7496, 7501, 7501, 7511, 7511, 7519, 7519, 7524, 7524, 7529, 7529, 7542, 7542, 7547, 7547, 7552, 7552, 7572, 7572, 7582, 7582, 7583, 7583, 7586, 7586, 7616, 7616, 7705, 7705, 7707, 7707, 7734, 7734, 7740, 7740, 7745, 7745, 7754, 7754, 7758, 7758, 7777, 7777, 7780, 7780, 7791, 7791, 7792, 7792, 7890, 7890, 7911, 7911, 13801, 13801, 13802, 13802, 13803, 13803, 13804, 13804, 13805, 13805, 13806, 13806

### `PromptUtils` (class, 441 lines)

- Def site: line 7003-7443
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6948, 6948, 6964, 6964, 6968, 6968, 6969, 6969, 6970, 6970, 6985, 6985, 6991, 6991, 7018, 7018, 7021, 7021, 7029, 7029, 7047, 7047, 7097, 7097, 7105, 7105, 7110, 7110, 7156, 7156, 7167, 7167, 7192, 7192, 7211, 7211, 7212, 7212, 7215, 7215, 7216, 7216, 7306, 7306, 7308, 7308, 7312, 7312, 7340, 7340, 7341, 7341, 7342, 7342, 7343, 7343, 7344, 7344, 7353, 7353, 7397, 7397, 7421, 7421, 10554, 10554, 10604, 10604, 10609, 10609, 10706, 10706, 10727, 10727, 10732, 10732, 10996, 10996, 11054, 11205, 11205, 11210, 11210, 11260, 11260, 11261, 11261, 12036, 12541, 12541, 13032, 13032, 13191, 13191, 13192, 13192, 13435, 13435
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 8740-9153
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8773, 8773, 8857, 8857, 8863, 8863, 8866, 8866, 8910, 8910, 8924, 8924, 8951, 8951, 8957, 8957, 8971, 8971, 9054, 9054, 9056, 9056, 9060, 9060, 9062, 9062, 9065, 9065, 9069, 9069, 9072, 9072, 9082, 9082, 9088, 9088, 9126, 9126, 13265, 13265, 13266, 13266, 13267, 13267, 13291, 13291

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 12619-13014
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12640, 12640, 12645, 12645, 12649, 12649, 12652, 12652, 12659, 12659, 12661, 12661, 12662, 12662, 12665, 12665, 12668, 12668, 12671, 12671, 12713, 12713, 12745, 12745, 12812, 12812, 12825, 12825, 12830, 12830, 12880, 12880, 12913, 12913, 12914, 12914, 12915, 12915, 12945, 12945, 12974, 12974, 12975, 12975, 13466, 13466

### `DataExporter` (class, 345 lines)

- Def site: line 6427-6771
- References: 176
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6473, 6473, 6489, 6489, 6490, 6490, 6513, 6513, 6515, 6515, 6518, 6518, 6532, 6532, 6534, 6534, 6543, 6543, 6545, 6545, 6546, 6546, 6552, 6552, 6553, 6553, 6553, 6570, 6570, 6574, 6574, 6616, 6616, 6647, 6647, 6650, 6650, 6652, 6652, 6698, 6698, 6708, 6708, 6741, 6741, 6746, 6746, 6753, 6753, 7060, 7060, 7761, 7761, 7991, 7991, 8008, 8008, 8026, 8026, 8047, 8047, 8606, 8606, 8681, 8681, 9011, 9011, 9362, 9362, 9781, 9781, 9880, 9880, 9886, 9886, 10183, 10183, 10200, 10200, 10215, 10215, 10429, 10429, 10457, 10457, 10473, 10473, 10510, 10510, 10548, 10548, 10637, 10637, 10666, 10666, 10854, 10854, 10860, 10860, 10979, 10979, 10987, 10987, 11057, 11263, 11263, 11871, 11871, 11930, 12037, 12588, 12588, 12608, 13115, 13115, 13136, 13136, 13362, 13362, 13375, 13375, 13589, 13589, 13644, 13644, 13660, 13660
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 10693-11033
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10710, 10710, 10712, 10712, 10716, 10716, 10717, 10717, 10731, 10731, 10737, 10737, 10740, 10740, 10743, 10743, 10801, 10801, 10807, 10807, 10812, 10812, 10826, 10826, 10844, 10844, 10954, 10954, 10958, 10958, 10960, 10960, 10963, 10963, 11000, 11000, 11005, 11005, 11019, 11019, 11023, 11023, 11025, 11025, 11028, 11028, 11033, 11033, 13512, 13512, 13516, 13516, 13520, 13520

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 11289-11616
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10164, 10164, 10223, 10223, 10224, 10224, 11060, 11330, 11330, 11332, 11332, 11338, 11338, 11352, 11352, 11391, 11391, 11394, 11394, 11396, 11396, 11397, 11397, 11398, 11398, 11452, 11452, 11453, 11453, 11464, 11464, 11473, 11473, 11492, 11492, 11544, 11544, 11548, 11548, 11556, 11556, 11557, 11557, 11581, 11581, 11585, 11585
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 12202-12490
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12230, 12230, 12233, 12233, 12238, 12238, 12241, 12241, 12285, 12285, 12291, 12291, 12322, 12322, 12325, 12325, 12329, 12329, 12355, 12355, 12372, 12372, 12378, 12378, 12392, 12392, 12393, 12393, 12395, 12395, 12401, 12401, 12408, 12408, 12417, 12417, 12464, 12464, 12486, 12486, 12487, 12487, 12488, 12488, 13457, 13457

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9156-9428
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9179, 9179, 9180, 9180, 9193, 9193, 9194, 9194, 9196, 9196, 9197, 9197, 9200, 9200, 9203, 9203, 9207, 9207, 9208, 9208, 9284, 9284, 9288, 9288, 9291, 9291, 9304, 9304, 9341, 9341, 9358, 9358, 9371, 9371, 9373, 9373, 9380, 9380, 9389, 9389, 9398, 9398, 9399, 9399, 9410, 9410, 9414, 9414, 9423, 9423, 9428, 9428, 13732, 13732

### `CacheUtils` (class, 264 lines)

- Def site: line 5287-5550
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5327, 5327, 5329, 5329, 5411, 5411, 5417, 5417, 5454, 5454, 5456, 5456, 5465, 5465, 5475, 5475, 5485, 5485, 5521, 5521, 7096, 7096, 8534, 8534, 8535, 8535, 8846, 8846, 11928, 12179, 12533, 12533, 12557, 12557, 12581, 12581, 12700, 12700, 12701, 12701, 12702, 12702, 12703, 12703, 13033, 13033, 13363, 13363, 13376, 13376, 13590, 13590, 13769, 13769
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 9553-9803
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9560, 9560, 9563, 9563, 9568, 9568, 9569, 9569, 9577, 9577, 9580, 9580, 9588, 9588, 9628, 9628, 9636, 9636, 9684, 9684, 9701, 9701, 9704, 9704, 9706, 9706, 9770, 9770, 9771, 9771, 13735, 13735

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 11640-11884
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11666, 11666, 11668, 11668, 11669, 11669, 11670, 11670, 11698, 11698, 11703, 11703, 11725, 11725, 11726, 11726, 11768, 11768, 11776, 11776, 11802, 11802, 11811, 11811, 11819, 11819, 11850, 11850, 13270, 13270, 13274, 13274

### `APIFetchUtils` (class, 221 lines)

- Def site: line 5850-6070
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5873, 5873, 5924, 5924, 5994, 5994, 6018, 6018, 6030, 6030, 6032, 6032, 6042, 6042, 6057, 6057, 6061, 6061, 6062, 6062, 6065, 6065, 6067, 6067, 11932
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `PromptClientUtils` (class, 210 lines)

- Def site: line 6787-6996
- References: 29
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6800, 6800, 6806, 6806, 6807, 6807, 6810, 6810, 6833, 6833, 6836, 6836, 6839, 6839, 6840, 6840, 6842, 6842, 6909, 6909, 6953, 6953, 7418, 7418, 11001, 11001, 12035, 12215, 12215

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 10482-10684
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10503, 10503, 10512, 10512, 10574, 10574, 10581, 10581, 10613, 10613, 10615, 10615, 10639, 10639, 10674, 10674, 10681, 10681, 13306, 13306, 13308, 13308, 13309, 13309, 13311, 13311

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6246-6424
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6291, 6291, 6329, 6329, 6340, 6340, 6366, 6366, 6367, 6367, 6369, 6369, 6375, 6375, 6376, 6376, 6379, 6379, 6385, 6385, 6386, 6386, 6389, 6389, 6391, 6391, 6401, 6401, 6403, 6403, 6404, 6404, 6406, 6406

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6078-6235
- References: 143
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6094, 6094, 6107, 6107, 6110, 6110, 6134, 6134, 6142, 6142, 6143, 6143, 6165, 6165, 6170, 6170, 6172, 6172, 6649, 6649, 6674, 6674, 6743, 6743, 6744, 6744, 7058, 7058, 7059, 7059, 7892, 7892, 7986, 7986, 7988, 7988, 7989, 7989, 8006, 8006, 8007, 8007, 8024, 8024, 8025, 8025, 8045, 8045, 8046, 8046, 8603, 8603, 8604, 8604, 8678, 8678, 8679, 8679, 9007, 9007, 9010, 9010, 9777, 9777, 9778, 9778, 9878, 9878, 9879, 9879, 10182, 10182, 10198, 10198, 10199, 10199, 10427, 10427, 10428, 10428, 10507, 10507, 10508, 10508, 10509, 10509, 10545, 10545, 10546, 10546, 10634, 10634, 10635, 10635, 10663, 10663, 10664, 10664, 10852, 10852, 10853, 10853, 10977, 10977, 10978, 10978, 11056, 11869, 11869, 11870, 11870, 11931, 12039, 12586, 12586, 12587, 12587
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `SiteExportUtils` (class, 145 lines)

- Def site: line 11044-11188
- References: 88
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10593, 10593, 11073, 11073, 11079, 11079, 11085, 11085, 11091, 11091, 11097, 11097, 11103, 11103, 11109, 11109, 11115, 11115, 11121, 11121, 11127, 11127, 11133, 11133, 11139, 11139, 11145, 11145, 11151, 11151, 11157, 11157, 11163, 11163, 11169, 11169, 11175, 11175, 11181, 11181, 11187, 11187, 13344, 13344, 13503, 13503, 13505, 13505, 13629, 13629, 13764, 13764, 13765, 13765, 13766, 13766, 13785, 13785, 13786, 13786, 13787, 13787, 13788, 13788, 13789, 13789, 13790, 13790, 13791, 13791
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 12025-12151
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12045, 12045, 12050, 12050, 12055, 12055, 12092, 12092, 12098, 12098, 12104, 12104, 12110, 12110, 12116, 12116, 12117, 12117, 12118, 12118, 12119, 12119, 12120, 12120, 12124, 12124, 12133, 12133, 12137, 12137, 12140, 12140, 12146, 12146, 13415, 13415

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 7938-8049
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7096, 7096, 8534, 8534, 8846, 8846, 11935, 12535, 12535, 12559, 12559, 12583, 12583, 12701, 12701, 13036, 13036, 13263, 13263, 13278, 13278, 13288, 13288, 13288, 13288, 13298, 13298, 13364, 13364, 13377, 13377, 13591, 13591
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 9441-9550
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9496, 9496, 9499, 9499, 9500, 9500, 9505, 9505, 9524, 9524, 9524, 9533, 9533, 9533, 9533, 9534, 9534, 9534, 9534, 9592, 9592, 9595, 9595, 9607, 9607, 9608, 9608, 9621, 9621, 9660, 9660, 9668, 9668, 9722, 9722, 9730, 9730

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 11917-12014
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11660, 11660, 11895, 11895, 11953, 11953, 11959, 11959, 11965, 11965, 11971, 11971, 11977, 11977, 11983, 11983, 11989, 11989, 11995, 11995, 12001, 12001, 12007, 12007, 12013, 12013, 12180, 12702, 12702, 12705, 12705, 13035, 13035, 13229, 13229, 13296, 13296, 13302, 13302, 13353, 13353, 13428, 13428
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `ValidationUtils` (class, 90 lines)

- Def site: line 5625-5714
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5707, 5707, 11723, 11723, 11724, 11724, 11938, 13193, 13193
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 13091-13169
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13086, 13086, 13087, 13087, 13608, 13608
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 12513-12590
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13470, 13470, 13474, 13474, 13478, 13478
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1993-2066
- References: 233
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2006, 2006, 2038, 2038, 2383, 2383, 2410, 2410, 6808, 6808, 6894, 6894, 7024, 7024, 7101, 7101, 7184, 7184, 7414, 7414, 7502, 7502, 7561, 7561, 7574, 7574, 7591, 7591, 7636, 7636, 7670, 7670, 7676, 7676, 7782, 7782, 9195, 9195, 9594, 9594, 9623, 9623, 10456, 10456, 10472, 10472, 11212, 11212, 11262, 11262, 11936, 12138, 12138, 12178, 12540, 12540, 12565, 12565, 12607, 12682, 12682, 12892, 12892, 13031, 13031, 13081, 13081, 13111, 13111, 13132, 13132, 13151, 13151, 13167, 13167, 13195, 13195, 13360, 13360, 13373, 13373, 13587, 13587, 13642, 13642, 13742, 13742, 13747, 13747, 13753, 13753, 13772, 13772, 13778, 13778, 14697, 14697
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

- Def site: line 5720-5789
- References: 150
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5762, 5762, 5767, 5767, 5864, 5864, 5922, 5922, 6951, 6951, 7495, 7495, 7518, 7518, 7541, 7541, 7732, 7732, 7753, 7753, 7980, 7980, 8002, 8002, 8019, 8019, 8036, 8036, 8421, 8421, 8644, 8644, 8661, 8661, 9053, 9053, 9385, 9385, 9559, 9559, 9910, 9910, 10246, 10246, 10418, 10418, 10458, 10458, 10464, 10464, 10558, 10558, 11055, 11659, 11659, 11927, 12034, 12134, 12134, 12605, 13082, 13082, 13084, 13084, 13108, 13108, 13112, 13112, 13113, 13113, 13133, 13133, 13134, 13134, 13215, 13215, 13252, 13252, 13258, 13258, 13358, 13358, 13371, 13371, 13404, 13404, 13461, 13461, 13544, 13544, 13553, 13553, 13585, 13585, 13640, 13640, 13641, 13641, 13658, 13658, 13742, 13742, 13747, 13747, 13753, 13753, 13772, 13772, 13778, 13778, 14010, 14010, 14079, 14561, 14561, 14649, 14649
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 5795-5841
- References: 45
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5919, 5919, 7286, 7286, 7981, 7981, 8004, 8004, 8491, 8491, 8526, 8526, 8540, 8540, 8663, 8663, 8667, 8667, 9215, 9215, 10562, 10562, 11062, 11933, 13083, 13083, 13114, 13114, 13135, 13135, 13643, 13643, 13659, 13659, 14580, 14580
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5568-5613
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5326, 5326, 5368, 5368, 5413, 5413, 5519, 5519, 5534, 5534, 5603, 5603, 5945, 5945, 7120, 7120, 8191, 8191, 8502, 8502, 8518, 8518, 8847, 8847, 11929, 12181, 12441, 12441, 12481, 12481, 12482, 12482, 12483, 12483, 12532, 12532, 12556, 12556, 12560, 12560, 12580, 12580, 12606, 12657, 12657, 12691, 12691, 12712, 12712, 12744, 12744, 12806, 12806, 12845, 12845, 12993, 12993, 13034, 13034, 13361, 13361, 13374, 13374, 13588, 13588
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `TimeUtils` (class, 29 lines)

- Def site: line 1957-1985
- References: 27
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8780, 8780, 8781, 8781, 9085, 9085, 9086, 9086, 9133, 9133, 9134, 9134, 10297, 10297, 10298, 10298, 10403, 10403, 10404, 10404, 11058
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 11887-11914
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11901, 11901, 11907, 11907, 11913, 11913, 13482, 13482, 13486, 13486
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 12167-12192
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12187, 12187, 12192, 12192, 13490, 13490, 13495, 13495
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 11219-11240
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13238, 13238, 13242, 13242, 13246, 13246
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 13067-13088
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13622, 13622
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 418-426
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

- Def site: line 430-437
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

- Def site: line 724-726
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1334, 2003, 2003, 2003, 2015, 2021, 5921, 6041, 8590, 8701, 8955, 11065, 11805, 11847, 11945, 13645
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

- Def site: line 2119-2121
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2119, 11941
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 840-1844
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1889

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
