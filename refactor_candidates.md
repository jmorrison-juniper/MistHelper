# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 232 first-party files
- Definitions analyzed: 45
- LOC saveable (unused + single-use): 12
- Category counts: unused=0, single-use=2, low-use=2, hot=40, skipped=1

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
| `PromptUtils` | class | 441 | 90 | hot |  | oversize_25_lines |
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
| `InputUtils` | class | 74 | 229 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 146 | hot |  | oversize_25_lines |
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

- Def site: line 451-459
- References: 1
- Suggested class: `DeviceDataFetcherManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`
- Rationale: Sole caller lives in `device_data_fetcher.py` inside `__init__()`; move `DeviceFetchConfig` into that module's semantic class so callers rewrite in one PR
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2114-2116
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2114

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2223-2247
- References: 2
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2353, 13995

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2111-2113
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2111, 8759, 11385

## Hot (40)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2961-5287
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2961, 6292, 6293, 6302, 6466

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 7845-8530
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7968, 7968, 8019, 8019, 8022, 8022, 8063, 8063, 8102, 8102, 8120, 8120, 8198, 8198, 8205, 8205, 8215, 8215, 8218, 8218, 8231, 8231, 8232, 8232, 8233, 8233, 8234, 8234, 8242, 8242, 8244, 8244, 8245, 8245, 8246, 8246, 8247, 8247, 8250, 8250, 8253, 8253, 8256, 8256, 8259, 8259, 8305, 8305, 8328, 8328, 8329, 8329, 8330, 8330, 8332, 8332, 8368, 8368, 8384, 8384, 8438, 8438, 8439, 8439, 8440, 8440, 8443, 8443, 8444, 8444, 8463, 8463, 8465, 8465, 8466, 8466, 8501, 8501, 11525, 12125, 12125, 12149, 12149, 12173, 12173, 12291, 12291, 12855, 12855, 12862, 12862, 12871, 12871, 12875, 12875, 12884, 12884
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgExportUtils` (class, 653 lines)

- Def site: line 9615-10267
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9687, 9687, 9709, 9709, 9712, 9712, 9738, 9738, 9747, 9747, 9748, 9748, 9769, 9769, 9812, 9812, 9858, 9858, 9869, 9869, 9896, 9896, 9901, 9901, 9902, 9902, 9903, 9903, 9935, 9935, 9941, 9941, 9966, 9966, 9986, 9986, 10021, 10021, 10036, 10036, 10042, 10042, 10044, 10044, 10047, 10047, 10049, 10049, 10053, 10053, 10057, 10057, 10062, 10062, 10069, 10069, 10076, 10076, 10083, 10083, 10092, 10092, 10102, 10102, 10109, 10109, 10116, 10116, 10123, 10123, 10130, 10130, 10137, 10137, 10147, 10147, 10156, 10156, 10165, 10165, 10174, 10174, 10183, 10183, 10212, 10212, 12816, 12816, 13015, 13015, 13092, 13092, 13093, 13093, 13101, 13101, 13324, 13324, 13325, 13325, 13344, 13344, 13351, 13351, 13352, 13352, 13353, 13353, 13354, 13354

### `menu_actions` (assignment, 608 lines)

- Def site: line 12797-13404
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12797, 13439, 13440, 13449, 13569, 13569, 13611, 13667, 13712, 14203, 14207, 14252, 14252, 14279, 14279, 14282
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 475 lines)

- Def site: line 7248-7722
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7289, 7289, 7294, 7294, 7304, 7304, 7312, 7312, 7317, 7317, 7322, 7322, 7335, 7335, 7340, 7340, 7345, 7345, 7365, 7365, 7375, 7375, 7376, 7376, 7379, 7379, 7409, 7409, 7498, 7498, 7500, 7500, 7527, 7527, 7533, 7533, 7538, 7538, 7547, 7547, 7551, 7551, 7570, 7570, 7573, 7573, 7584, 7584, 7585, 7585, 7683, 7683, 7704, 7704, 13392, 13392, 13393, 13393, 13394, 13394, 13395, 13395, 13396, 13396, 13397, 13397

### `PromptUtils` (class, 441 lines)

- Def site: line 6796-7236
- References: 90
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6811, 6811, 6814, 6814, 6822, 6822, 6840, 6840, 6890, 6890, 6898, 6898, 6903, 6903, 6949, 6949, 6960, 6960, 6985, 6985, 7004, 7004, 7005, 7005, 7008, 7008, 7009, 7009, 7099, 7099, 7101, 7101, 7105, 7105, 7133, 7133, 7134, 7134, 7135, 7135, 7136, 7136, 7137, 7137, 7146, 7146, 7190, 7190, 7214, 7214, 10297, 10297, 10318, 10318, 10323, 10323, 10587, 10587, 10645, 10796, 10796, 10801, 10801, 10851, 10851, 10852, 10852, 11627, 12132, 12132, 12623, 12623, 12782, 12782, 12783, 12783, 13026, 13026
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 8533-8946
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8566, 8566, 8650, 8650, 8656, 8656, 8659, 8659, 8703, 8703, 8717, 8717, 8744, 8744, 8750, 8750, 8764, 8764, 8847, 8847, 8849, 8849, 8853, 8853, 8855, 8855, 8858, 8858, 8862, 8862, 8865, 8865, 8875, 8875, 8881, 8881, 8919, 8919, 12856, 12856, 12857, 12857, 12858, 12858, 12882, 12882

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 12210-12605
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12231, 12231, 12236, 12236, 12240, 12240, 12243, 12243, 12250, 12250, 12252, 12252, 12253, 12253, 12256, 12256, 12259, 12259, 12262, 12262, 12304, 12304, 12336, 12336, 12403, 12403, 12416, 12416, 12421, 12421, 12471, 12471, 12504, 12504, 12505, 12505, 12506, 12506, 12536, 12536, 12565, 12565, 12566, 12566, 13057, 13057

### `DataExporter` (class, 345 lines)

- Def site: line 6433-6777
- References: 168
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6479, 6479, 6495, 6495, 6496, 6496, 6519, 6519, 6521, 6521, 6524, 6524, 6538, 6538, 6540, 6540, 6549, 6549, 6551, 6551, 6552, 6552, 6558, 6558, 6559, 6559, 6559, 6576, 6576, 6580, 6580, 6622, 6622, 6653, 6653, 6656, 6656, 6658, 6658, 6704, 6704, 6714, 6714, 6747, 6747, 6752, 6752, 6759, 6759, 6853, 6853, 7554, 7554, 7784, 7784, 7801, 7801, 7819, 7819, 7840, 7840, 8399, 8399, 8474, 8474, 8804, 8804, 9155, 9155, 9574, 9574, 9673, 9673, 9679, 9679, 9976, 9976, 9993, 9993, 10008, 10008, 10222, 10222, 10250, 10250, 10266, 10266, 10445, 10445, 10451, 10451, 10570, 10570, 10578, 10578, 10648, 10854, 10854, 11462, 11462, 11521, 11628, 12179, 12179, 12199, 12706, 12706, 12727, 12727, 12953, 12953, 12966, 12966, 13180, 13180, 13235, 13235, 13251, 13251
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 10284-10624
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10301, 10301, 10303, 10303, 10307, 10307, 10308, 10308, 10322, 10322, 10328, 10328, 10331, 10331, 10334, 10334, 10392, 10392, 10398, 10398, 10403, 10403, 10417, 10417, 10435, 10435, 10545, 10545, 10549, 10549, 10551, 10551, 10554, 10554, 10591, 10591, 10596, 10596, 10610, 10610, 10614, 10614, 10616, 10616, 10619, 10619, 10624, 10624, 13103, 13103, 13107, 13107, 13111, 13111

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 10880-11207
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9957, 9957, 10016, 10016, 10017, 10017, 10651, 10921, 10921, 10923, 10923, 10929, 10929, 10943, 10943, 10982, 10982, 10985, 10985, 10987, 10987, 10988, 10988, 10989, 10989, 11043, 11043, 11044, 11044, 11055, 11055, 11064, 11064, 11083, 11083, 11135, 11135, 11139, 11139, 11147, 11147, 11148, 11148, 11172, 11172, 11176, 11176
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 11793-12081
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11821, 11821, 11824, 11824, 11829, 11829, 11832, 11832, 11876, 11876, 11882, 11882, 11913, 11913, 11916, 11916, 11920, 11920, 11946, 11946, 11963, 11963, 11969, 11969, 11983, 11983, 11984, 11984, 11986, 11986, 11992, 11992, 11999, 11999, 12008, 12008, 12055, 12055, 12077, 12077, 12078, 12078, 12079, 12079, 13048, 13048

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 8949-9221
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8972, 8972, 8973, 8973, 8986, 8986, 8987, 8987, 8989, 8989, 8990, 8990, 8993, 8993, 8996, 8996, 9000, 9000, 9001, 9001, 9077, 9077, 9081, 9081, 9084, 9084, 9097, 9097, 9134, 9134, 9151, 9151, 9164, 9164, 9166, 9166, 9173, 9173, 9182, 9182, 9191, 9191, 9192, 9192, 9203, 9203, 9207, 9207, 9216, 9216, 9221, 9221, 13323, 13323

### `CacheUtils` (class, 264 lines)

- Def site: line 5293-5556
- References: 81
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5333, 5333, 5335, 5335, 5417, 5417, 5423, 5423, 5460, 5460, 5462, 5462, 5471, 5471, 5481, 5481, 5491, 5491, 5527, 5527, 6889, 6889, 8327, 8327, 8328, 8328, 8639, 8639, 11519, 11770, 12124, 12124, 12148, 12148, 12172, 12172, 12291, 12291, 12292, 12292, 12293, 12293, 12294, 12294, 12624, 12624, 12954, 12954, 12967, 12967, 13181, 13181, 13360, 13360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 9346-9596
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9353, 9353, 9356, 9356, 9361, 9361, 9362, 9362, 9370, 9370, 9373, 9373, 9381, 9381, 9421, 9421, 9429, 9429, 9477, 9477, 9494, 9494, 9497, 9497, 9499, 9499, 9563, 9563, 9564, 9564, 13326, 13326

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 11231-11475
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11257, 11257, 11259, 11259, 11260, 11260, 11261, 11261, 11289, 11289, 11294, 11294, 11316, 11316, 11317, 11317, 11359, 11359, 11367, 11367, 11393, 11393, 11402, 11402, 11410, 11410, 11441, 11441, 12861, 12861, 12865, 12865

### `APIFetchUtils` (class, 221 lines)

- Def site: line 5856-6076
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5879, 5879, 5930, 5930, 6000, 6000, 6024, 6024, 6036, 6036, 6038, 6038, 6048, 6048, 6063, 6063, 6067, 6067, 6068, 6068, 6071, 6071, 6073, 6073, 11523
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6252-6430
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6297, 6297, 6335, 6335, 6346, 6346, 6372, 6372, 6373, 6373, 6375, 6375, 6381, 6381, 6382, 6382, 6385, 6385, 6391, 6391, 6392, 6392, 6395, 6395, 6397, 6397, 6407, 6407, 6409, 6409, 6410, 6410, 6412, 6412

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6084-6241
- References: 125
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6100, 6100, 6113, 6113, 6116, 6116, 6140, 6140, 6148, 6148, 6149, 6149, 6171, 6171, 6176, 6176, 6178, 6178, 6655, 6655, 6680, 6680, 6749, 6749, 6750, 6750, 6851, 6851, 6852, 6852, 7685, 7685, 7779, 7779, 7781, 7781, 7782, 7782, 7799, 7799, 7800, 7800, 7817, 7817, 7818, 7818, 7838, 7838, 7839, 7839, 8396, 8396, 8397, 8397, 8471, 8471, 8472, 8472, 8800, 8800, 8803, 8803, 9570, 9570, 9571, 9571, 9671, 9671, 9672, 9672, 9975, 9975, 9991, 9991, 9992, 9992, 10220, 10220, 10221, 10221, 10443, 10443, 10444, 10444, 10568, 10568, 10569, 10569, 10647, 11460, 11460, 11461, 11461, 11522, 11630, 12177, 12177, 12178, 12178
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `SiteExportUtils` (class, 145 lines)

- Def site: line 10635-10779
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10664, 10664, 10670, 10670, 10676, 10676, 10682, 10682, 10688, 10688, 10694, 10694, 10700, 10700, 10706, 10706, 10712, 10712, 10718, 10718, 10724, 10724, 10730, 10730, 10736, 10736, 10742, 10742, 10748, 10748, 10754, 10754, 10760, 10760, 10766, 10766, 10772, 10772, 10778, 10778, 12935, 12935, 13094, 13094, 13096, 13096, 13220, 13220, 13355, 13355, 13356, 13356, 13357, 13357, 13376, 13376, 13377, 13377, 13378, 13378, 13379, 13379, 13380, 13380, 13381, 13381, 13382, 13382
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 11616-11742
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11636, 11636, 11641, 11641, 11646, 11646, 11683, 11683, 11689, 11689, 11695, 11695, 11701, 11701, 11707, 11707, 11708, 11708, 11709, 11709, 11710, 11710, 11711, 11711, 11715, 11715, 11724, 11724, 11728, 11728, 11731, 11731, 11737, 11737, 13006, 13006

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 7731-7842
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6889, 6889, 8327, 8327, 8639, 8639, 11526, 12126, 12126, 12150, 12150, 12174, 12174, 12292, 12292, 12627, 12627, 12854, 12854, 12869, 12869, 12879, 12879, 12879, 12879, 12889, 12889, 12955, 12955, 12968, 12968, 13182, 13182
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 9234-9343
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9289, 9289, 9292, 9292, 9293, 9293, 9298, 9298, 9317, 9317, 9317, 9326, 9326, 9326, 9326, 9327, 9327, 9327, 9327, 9385, 9385, 9388, 9388, 9400, 9400, 9401, 9401, 9414, 9414, 9453, 9453, 9461, 9461, 9515, 9515, 9523, 9523

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 11508-11605
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11251, 11251, 11486, 11486, 11544, 11544, 11550, 11550, 11556, 11556, 11562, 11562, 11568, 11568, 11574, 11574, 11580, 11580, 11586, 11586, 11592, 11592, 11598, 11598, 11604, 11604, 11771, 12293, 12293, 12296, 12296, 12626, 12626, 12820, 12820, 12887, 12887, 12893, 12893, 12944, 12944, 13019, 13019
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `ValidationUtils` (class, 90 lines)

- Def site: line 5631-5720
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5713, 5713, 11314, 11314, 11315, 11315, 11529, 12784, 12784
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 12682-12760
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12677, 12677, 12678, 12678, 13199, 13199
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 12104-12181
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13061, 13061, 13065, 13065, 13069, 13069
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1999-2072
- References: 229
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2012, 2012, 2044, 2044, 2389, 2389, 2416, 2416, 6817, 6817, 6894, 6894, 6977, 6977, 7207, 7207, 7295, 7295, 7354, 7354, 7367, 7367, 7384, 7384, 7429, 7429, 7463, 7463, 7469, 7469, 7575, 7575, 8988, 8988, 9387, 9387, 9416, 9416, 10249, 10249, 10265, 10265, 10803, 10803, 10853, 10853, 11527, 11729, 11729, 11769, 12131, 12131, 12156, 12156, 12198, 12273, 12273, 12483, 12483, 12622, 12622, 12672, 12672, 12702, 12702, 12723, 12723, 12742, 12742, 12758, 12758, 12786, 12786, 12951, 12951, 12964, 12964, 13178, 13178, 13233, 13233, 13333, 13333, 13338, 13338, 13344, 13344, 13363, 13363, 13369, 13369, 14288, 14288
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

- Def site: line 5726-5795
- References: 146
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5768, 5768, 5773, 5773, 5870, 5870, 5928, 5928, 7288, 7288, 7311, 7311, 7334, 7334, 7525, 7525, 7546, 7546, 7773, 7773, 7795, 7795, 7812, 7812, 7829, 7829, 8214, 8214, 8437, 8437, 8454, 8454, 8846, 8846, 9178, 9178, 9352, 9352, 9703, 9703, 10039, 10039, 10211, 10211, 10251, 10251, 10257, 10257, 10646, 11250, 11250, 11518, 11625, 11725, 11725, 12196, 12673, 12673, 12675, 12675, 12699, 12699, 12703, 12703, 12704, 12704, 12724, 12724, 12725, 12725, 12806, 12806, 12843, 12843, 12849, 12849, 12949, 12949, 12962, 12962, 12995, 12995, 13052, 13052, 13135, 13135, 13144, 13144, 13176, 13176, 13231, 13231, 13232, 13232, 13249, 13249, 13333, 13333, 13338, 13338, 13344, 13344, 13363, 13363, 13369, 13369, 13601, 13601, 13670, 14152, 14152, 14240, 14240
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 5801-5847
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5925, 5925, 7079, 7079, 7774, 7774, 7797, 7797, 8284, 8284, 8319, 8319, 8333, 8333, 8456, 8456, 8460, 8460, 9008, 9008, 10653, 11524, 12674, 12674, 12705, 12705, 12726, 12726, 13234, 13234, 13250, 13250, 14171, 14171
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5574-5619
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5332, 5332, 5374, 5374, 5419, 5419, 5525, 5525, 5540, 5540, 5609, 5609, 5951, 5951, 6913, 6913, 7984, 7984, 8295, 8295, 8311, 8311, 8640, 8640, 11520, 11772, 12032, 12032, 12072, 12072, 12073, 12073, 12074, 12074, 12123, 12123, 12147, 12147, 12151, 12151, 12171, 12171, 12197, 12248, 12248, 12282, 12282, 12303, 12303, 12335, 12335, 12397, 12397, 12436, 12436, 12584, 12584, 12625, 12625, 12952, 12952, 12965, 12965, 13179, 13179
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `TimeUtils` (class, 29 lines)

- Def site: line 1963-1991
- References: 27
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8573, 8573, 8574, 8574, 8878, 8878, 8879, 8879, 8926, 8926, 8927, 8927, 10090, 10090, 10091, 10091, 10196, 10196, 10197, 10197, 10649
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 11478-11505
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11492, 11492, 11498, 11498, 11504, 11504, 13073, 13073, 13077, 13077
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 11758-11783
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11778, 11778, 11783, 11783, 13081, 13081, 13086, 13086
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 10810-10831
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12829, 12829, 12833, 12833, 12837, 12837
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 12658-12679
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13213, 13213
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 424-432
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

- Def site: line 436-443
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

- Def site: line 730-732
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1340, 2009, 2009, 2009, 2021, 2027, 5927, 6047, 8383, 8494, 8748, 10656, 11396, 11438, 11536, 13236
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

- Def site: line 2125-2127
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2125, 11532
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 846-1850
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1895

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
