# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 250 first-party files
- Definitions analyzed: 20
- LOC saveable (unused + single-use): 15
- Category counts: unused=0, single-use=3, low-use=2, hot=14, skipped=1

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
| `ENDPOINT_PRIMARY_KEY_STRATEGIES` | assignment | 2327 | 2 | low-use | EndpointPrimaryKeyStrategiesManager | oversize_25_lines,missing_inline_comments,missing_action_logging,non_ascii_logs |
| `GlobalImportManager` | class | 1003 | 1 | skipped |  | oversize_25_lines |
| `OrgInventoryExporter` | class | 686 | 102 | hot |  | oversize_25_lines,missing_inline_comments |
| `menu_actions` | assignment | 651 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `PromptUtils` | class | 441 | 89 | hot |  | oversize_25_lines |
| `DataExporter` | class | 345 | 123 | hot |  | oversize_25_lines,non_ascii_logs |
| `CacheUtils` | class | 264 | 71 | hot |  | oversize_25_lines |
| `DataProcessingUtils` | class | 158 | 70 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `SiteExportUtils` | class | 145 | 86 | hot |  | oversize_25_lines,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 195 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 99 | hot |  | oversize_25_lines |
| `FilePathUtils` | class | 46 | 60 | hot |  | oversize_25_lines,missing_inline_comments |
| `SSHRunnerManager` | class | 27 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 2 | low-use | DetectMspPrivilegesManager | missing_action_logging |
| `DeviceFetchConfig` | class | 9 | 1 | single-use | DeviceDataFetcherManager | missing_action_logging |
| `tqdm` | function | 3 | 43 | hot |  | missing_action_logging |
| `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` | assignment | 3 | 1 | single-use | FastModeMaxConcurrentConnectionsManager | missing_inline_comments,missing_action_logging |
| `FAST_MODE_USE_CONNECTION_AWARE_THREADING` | assignment | 3 | 1 | single-use | FastModeUseConnectionAwareThreadingManager | missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Single-Use (3)

### `DeviceFetchConfig` (class, 9 lines)

- Def site: line 494-502
- References: 1
- Suggested class: `DeviceDataFetcherManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`
- Rationale: Sole caller lives in `device_data_fetcher.py` inside `__init__()`; move `DeviceFetchConfig` into that module's semantic class so callers rewrite in one PR
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2125-2127
- References: 1
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2125

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2128-2130
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2128

## Low-Use (2)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2975-5301
- References: 2
- Suggested class: `EndpointPrimaryKeyStrategiesManager`
- Suggested module: `src/refactors/endpoint__primary__key__strategies.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_build_polyglot_router()`; extract `ENDPOINT_PRIMARY_KEY_STRATEGIES` OUT of the entrypoint into a new `src/refactors/endpoint__primary__key__strategies.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2975, 5948

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2237-2261
- References: 2
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2367, 9356

## Hot (14)

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 6740-7425
- References: 102
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6863, 6863, 6914, 6914, 6917, 6917, 6958, 6958, 6997, 6997, 7015, 7015, 7093, 7093, 7100, 7100, 7110, 7110, 7113, 7113, 7126, 7126, 7127, 7127, 7128, 7128, 7129, 7129, 7137, 7137, 7139, 7139, 7140, 7140, 7141, 7141, 7142, 7142, 7145, 7145, 7148, 7148, 7151, 7151, 7154, 7154, 7200, 7200, 7223, 7223, 7224, 7224, 7225, 7225, 7227, 7227, 7263, 7263, 7279, 7279, 7333, 7333, 7334, 7334, 7335, 7335, 7338, 7338, 7339, 7339, 7358, 7358, 7360, 7360, 7361, 7361, 7396, 7396, 7743, 7910, 7910, 7934, 7934, 7958, 7958, 8206, 8206, 8213, 8213, 8222, 8222, 8226, 8226, 8235, 8235
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `menu_actions` (assignment, 651 lines)

- Def site: line 8115-8765
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8115, 8800, 8801, 8810, 8930, 8930, 8972, 9028, 9073, 9564, 9568, 9613, 9613, 9640, 9640, 9643
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `PromptUtils` (class, 441 lines)

- Def site: line 6278-6718
- References: 89
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6293, 6293, 6296, 6296, 6304, 6304, 6322, 6322, 6372, 6372, 6380, 6380, 6385, 6385, 6431, 6431, 6442, 6442, 6467, 6467, 6486, 6486, 6487, 6487, 6490, 6490, 6491, 6491, 6581, 6581, 6583, 6583, 6587, 6587, 6615, 6615, 6616, 6616, 6617, 6617, 6618, 6618, 6619, 6619, 6628, 6628, 6672, 6672, 6696, 6696, 7507, 7674, 7674, 7675, 7675, 7917, 7917, 8011, 8011, 8100, 8100, 8101, 8101, 8150, 8150, 8151, 8151, 8165, 8165, 8166, 8166, 8180, 8180, 8181, 8181, 8377, 8377
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `DataExporter` (class, 345 lines)

- Def site: line 5915-6259
- References: 123
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5961, 5961, 5977, 5977, 5978, 5978, 6001, 6001, 6003, 6003, 6006, 6006, 6020, 6020, 6022, 6022, 6031, 6031, 6033, 6033, 6034, 6034, 6040, 6040, 6041, 6041, 6041, 6058, 6058, 6062, 6062, 6104, 6104, 6135, 6135, 6138, 6138, 6140, 6140, 6186, 6186, 6196, 6196, 6229, 6229, 6234, 6234, 6241, 6241, 6335, 6335, 7294, 7294, 7369, 7369, 7510, 7677, 7677, 7739, 7964, 7964, 7984, 8072, 8072, 8304, 8304, 8317, 8317, 8531, 8531, 8596, 8596, 8612, 8612
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `CacheUtils` (class, 264 lines)

- Def site: line 5307-5570
- References: 71
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5347, 5347, 5349, 5349, 5431, 5431, 5437, 5437, 5474, 5474, 5476, 5476, 5485, 5485, 5495, 5495, 5505, 5505, 5541, 5541, 6371, 6371, 7222, 7222, 7223, 7223, 7737, 7848, 7909, 7909, 7933, 7933, 7957, 7957, 8012, 8012, 8305, 8305, 8318, 8318, 8532, 8532, 8721, 8721
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 5744-5901
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5760, 5760, 5773, 5773, 5776, 5776, 5800, 5800, 5808, 5808, 5809, 5809, 5831, 5831, 5836, 5836, 5838, 5838, 6137, 6137, 6162, 6162, 6231, 6231, 6232, 6232, 6333, 6333, 6334, 6334, 7291, 7291, 7292, 7292, 7366, 7366, 7367, 7367, 7509, 7740, 7962, 7962, 7963, 7963
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `SiteExportUtils` (class, 145 lines)

- Def site: line 7497-7641
- References: 86
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7526, 7526, 7532, 7532, 7538, 7538, 7544, 7544, 7550, 7550, 7556, 7556, 7562, 7562, 7568, 7568, 7574, 7574, 7580, 7580, 7586, 7586, 7592, 7592, 7598, 7598, 7604, 7604, 7610, 7610, 7616, 7616, 7622, 7622, 7628, 7628, 7634, 7634, 7640, 7640, 8286, 8286, 8445, 8445, 8447, 8447, 8581, 8581, 8716, 8716, 8717, 8717, 8718, 8718, 8737, 8737, 8738, 8738, 8739, 8739, 8740, 8740, 8741, 8741, 8742, 8742, 8743, 8743
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 7889-7966
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8412, 8412, 8416, 8416, 8420, 8420
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 2013-2086
- References: 195
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2026, 2026, 2058, 2058, 2403, 2403, 2430, 2430, 6299, 6299, 6376, 6376, 6459, 6459, 6689, 6689, 7676, 7676, 7745, 7847, 7916, 7916, 7941, 7941, 7983, 8010, 8010, 8068, 8068, 8104, 8104, 8154, 8154, 8169, 8169, 8184, 8184, 8302, 8302, 8315, 8315, 8529, 8529, 8567, 8567, 8594, 8594, 8694, 8694, 8699, 8699, 8705, 8705, 8724, 8724, 8730, 8730, 9649, 9649
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

- Def site: line 5654-5723
- References: 99
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5696, 5696, 5701, 5701, 7109, 7109, 7332, 7332, 7349, 7349, 7508, 7736, 7981, 8065, 8065, 8069, 8069, 8070, 8070, 8124, 8124, 8194, 8194, 8200, 8200, 8300, 8300, 8313, 8313, 8346, 8346, 8403, 8403, 8486, 8486, 8495, 8495, 8527, 8527, 8568, 8568, 8570, 8570, 8592, 8592, 8593, 8593, 8610, 8610, 8694, 8694, 8699, 8699, 8705, 8705, 8724, 8724, 8730, 8730, 8962, 8962, 9031, 9513, 9513, 9601, 9601
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `FilePathUtils` (class, 46 lines)

- Def site: line 5588-5633
- References: 60
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5346, 5346, 5388, 5388, 5433, 5433, 5539, 5539, 5554, 5554, 5623, 5623, 6395, 6395, 6879, 6879, 7190, 7190, 7206, 7206, 7738, 7850, 7908, 7908, 7932, 7932, 7936, 7936, 7956, 7956, 7982, 8013, 8013, 8303, 8303, 8316, 8316, 8530, 8530
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SSHRunnerManager` (class, 27 lines)

- Def site: line 7835-7861
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7856, 7856, 7861, 7861, 8432, 8432, 8437, 8437
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `tqdm` (function, 3 lines)

- Def site: line 773-775
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1383, 2023, 2023, 2023, 2035, 2041, 7278, 7389, 7518, 7754, 8597
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_data_fetcher.py`: lines 359
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_fetch_utils.py`: lines 104, 227
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\gateway_test_exporter.py`: lines 218, 268
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\org_client_security_exporter.py`: lines 179
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\org_device_stats_exporter.py`: lines 259
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

- Def site: line 2139-2141
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2139, 7750
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1003 lines)

- Def site: line 889-1891
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1936

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
