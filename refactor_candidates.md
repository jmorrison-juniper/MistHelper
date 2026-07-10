# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 253 first-party files
- Definitions analyzed: 12
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=0, hot=11, skipped=1

## How to read this report

Work the report **top-down inside each category**, then move to the next category:

1. **Unused** -- zero references. Delete outright; no move, no callsite rewrite. Highest ROI per PR.
2. **Single-use** -- exactly one caller. Move alongside that caller (or into a new `/src` module when the Refactor report written to refactor_candidates.md
Entrypoint: C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py
Module graph: 253 first-party files
Definitions analyzed: 12
  unused=0  single-use=0  low-use=0  hot=11  skipped=1
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
| `GlobalImportManager` | class | 1003 | 1 | skipped |  | oversize_25_lines |
| `menu_actions` | assignment | 887 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgInventoryExporter` | class | 686 | 102 | hot |  | oversize_25_lines,missing_inline_comments |
| `PromptUtils` | class | 441 | 96 | hot |  | oversize_25_lines |
| `DataExporter` | class | 345 | 118 | hot |  | oversize_25_lines,non_ascii_logs |
| `DataProcessingUtils` | class | 158 | 69 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 195 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 102 | hot |  | oversize_25_lines |
| `FilePathUtils` | class | 46 | 50 | hot |  | oversize_25_lines,missing_inline_comments |
| `tqdm` | function | 3 | 51 | hot |  | missing_action_logging |
| `MIST_SITE_EXCLUDE_PREFIX` | assignment | 3 | 11 | hot |  | missing_inline_comments,missing_action_logging |

## Hot (11)

### `menu_actions` (assignment, 887 lines)

- Def site: line 5350-6236
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5350, 6271, 6272, 6281, 6401, 6401, 6443, 6499, 6544, 7035, 7039, 7084, 7084, 7111, 7111, 7114
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 4133-4818
- References: 102
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 4256, 4256, 4307, 4307, 4310, 4310, 4351, 4351, 4390, 4390, 4408, 4408, 4486, 4486, 4493, 4493, 4503, 4503, 4506, 4506, 4519, 4519, 4520, 4520, 4521, 4521, 4522, 4522, 4530, 4530, 4532, 4532, 4533, 4533, 4534, 4534, 4535, 4535, 4538, 4538, 4541, 4541, 4544, 4544, 4547, 4547, 4593, 4593, 4616, 4616, 4617, 4617, 4618, 4618, 4620, 4620, 4656, 4656, 4672, 4672, 4726, 4726, 4727, 4727, 4728, 4728, 4731, 4731, 4732, 4732, 4751, 4751, 4753, 4753, 4754, 4754, 4789, 4789, 4990, 5145, 5145, 5169, 5169, 5193, 5193, 5441, 5441, 5448, 5448, 5457, 5457, 5461, 5461, 5470, 5470
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `PromptUtils` (class, 441 lines)

- Def site: line 3671-4111
- References: 96
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3686, 3686, 3689, 3689, 3697, 3697, 3715, 3715, 3765, 3765, 3773, 3773, 3778, 3778, 3824, 3824, 3835, 3835, 3860, 3860, 3879, 3879, 3880, 3880, 3883, 3883, 3884, 3884, 3974, 3974, 3976, 3976, 3980, 3980, 4008, 4008, 4009, 4009, 4010, 4010, 4011, 4011, 4012, 4012, 4021, 4021, 4065, 4065, 4089, 4089, 4921, 4921, 4922, 4922, 5152, 5152, 5246, 5246, 5335, 5335, 5336, 5336, 5385, 5385, 5386, 5386, 5400, 5400, 5401, 5401, 5415, 5415, 5416, 5416, 5524, 5630, 5630, 5701, 5714, 5859, 6010, 6029, 6048, 6085, 6104, 6123, 6142, 6161, 6180, 6199
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `DataExporter` (class, 345 lines)

- Def site: line 3308-3652
- References: 118
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3354, 3354, 3370, 3370, 3371, 3371, 3394, 3394, 3396, 3396, 3399, 3399, 3413, 3413, 3415, 3415, 3424, 3424, 3426, 3426, 3427, 3427, 3433, 3433, 3434, 3434, 3434, 3451, 3451, 3455, 3455, 3497, 3497, 3528, 3528, 3531, 3531, 3533, 3533, 3579, 3579, 3589, 3589, 3622, 3622, 3627, 3627, 3634, 3634, 3728, 3728, 4687, 4687, 4762, 4762, 4924, 4924, 4986, 5199, 5199, 5219, 5307, 5307, 5527, 5557, 5557, 5570, 5570, 5703, 5716, 5807, 5807, 5862, 5887, 5887, 5903, 5903, 6013, 6032, 6051, 6088, 6107, 6126, 6145, 6164, 6183, 6202
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 3137-3294
- References: 69
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3153, 3153, 3166, 3166, 3169, 3169, 3193, 3193, 3201, 3201, 3202, 3202, 3224, 3224, 3229, 3229, 3231, 3231, 3530, 3530, 3555, 3555, 3624, 3624, 3625, 3625, 3726, 3726, 3727, 3727, 4684, 4684, 4685, 4685, 4759, 4759, 4760, 4760, 4987, 5197, 5197, 5198, 5198, 5526, 5702, 5715, 5861, 6012, 6031, 6050, 6087, 6106, 6125, 6144, 6163, 6182, 6201
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 5124-5201
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5665, 5665, 5669, 5669, 5673, 5673
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 2011-2084
- References: 195
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2024, 2024, 2056, 2056, 2378, 2378, 2405, 2405, 3692, 3692, 3769, 3769, 3852, 3852, 4082, 4082, 4923, 4923, 4992, 5092, 5151, 5151, 5176, 5176, 5218, 5245, 5245, 5303, 5303, 5339, 5339, 5389, 5389, 5404, 5404, 5419, 5419, 5555, 5555, 5568, 5568, 5805, 5805, 5843, 5843, 5885, 5885, 5985, 5985, 5990, 5990, 5996, 5996, 6069, 6069, 6075, 6075, 7120, 7120
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

- Def site: line 3047-3116
- References: 102
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3089, 3089, 3094, 3094, 4502, 4502, 4725, 4725, 4742, 4742, 4983, 5216, 5300, 5300, 5304, 5304, 5305, 5305, 5359, 5359, 5429, 5429, 5435, 5435, 5525, 5553, 5553, 5566, 5566, 5599, 5599, 5656, 5656, 5762, 5762, 5771, 5771, 5803, 5803, 5844, 5844, 5846, 5846, 5860, 5883, 5883, 5884, 5884, 5901, 5901, 5985, 5985, 5990, 5990, 5996, 5996, 6011, 6030, 6049, 6069, 6069, 6075, 6075, 6086, 6105, 6124, 6143, 6162, 6181, 6200, 6433, 6433, 6502, 6984, 6984, 7072, 7072
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `FilePathUtils` (class, 46 lines)

- Def site: line 2981-3026
- References: 50
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3016, 3016, 3788, 3788, 4272, 4272, 4583, 4583, 4599, 4599, 4985, 5095, 5143, 5143, 5167, 5167, 5171, 5171, 5191, 5191, 5217, 5248, 5248, 5556, 5556, 5569, 5569, 5806, 5806
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `tqdm` (function, 3 lines)

- Def site: line 771-773
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1381, 2021, 2021, 2021, 2033, 2039, 4671, 4782, 5001, 5535, 5870, 5888, 6021, 6040, 6059, 6096, 6115, 6134, 6153, 6172, 6191, 6210
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_data_fetcher.py`: lines 359
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_fetch_utils.py`: lines 104, 227
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\gateway_test_exporter.py`: lines 220, 270
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\org_client_security_exporter.py`: lines 179
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\org_device_stats_exporter.py`: lines 259
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 58
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 41, 217, 260
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\template_config.py`: lines 401, 601, 640
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 509
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\csv_comparator.py`: lines 727, 1068
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\maps\maps_manager.py`: lines 579, 699, 707, 866, 1152, 1752
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\connection_pool_executor.py`: lines 148
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\wanprobe_config_manager.py`: lines 243, 363
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\site\address_audit\audit_engine.py`: lines 56, 916, 918

### `MIST_SITE_EXCLUDE_PREFIX` (assignment, 3 lines)

- Def site: line 2137-2139
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2137, 4997
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1003 lines)

- Def site: line 887-1889
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1934

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
