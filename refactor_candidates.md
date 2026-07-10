# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 257 first-party files
- Definitions analyzed: 8
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=0, hot=7, skipped=1

## How to read this report

Work the report **top-down inside each category**, then move to the next category:

1. **Unused** -- zero references. Delete outright; no move, no callsite rewrite. Highest ROI per PR.
2. **Single-use** -- exactly one caller. Move alongside that caller (or into a new `/src` module when the eRefactor report written to refactor_candidates.md
Entrypoint: C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py
Module graph: 257 first-party files
Definitions analyzed: 8
  unused=0  single-use=0  low-use=0  hot=7  skipped=1
LOC saveable (unused + single-use): 0
* -- pinned by bootstrap/module-load ordering (e.g. `GlobalImportManager`). DO NOT extract; the tool cannot detect load-order dependencies, so these are curated by hand via the `--skip NAME` CLI flag.

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

## Hot (7)

### `menu_actions` (assignment, 887 lines)

- Def site: line 5161-6047
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5161, 6082, 6083, 6092, 6212, 6212, 6254, 6310, 6355, 6849, 6853, 6898, 6898, 6925, 6925, 6928
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 3944-4629
- References: 102
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 4067, 4067, 4118, 4118, 4121, 4121, 4162, 4162, 4201, 4201, 4219, 4219, 4297, 4297, 4304, 4304, 4314, 4314, 4317, 4317, 4330, 4330, 4331, 4331, 4332, 4332, 4333, 4333, 4341, 4341, 4343, 4343, 4344, 4344, 4345, 4345, 4346, 4346, 4349, 4349, 4352, 4352, 4355, 4355, 4358, 4358, 4404, 4404, 4427, 4427, 4428, 4428, 4429, 4429, 4431, 4431, 4467, 4467, 4483, 4483, 4537, 4537, 4538, 4538, 4539, 4539, 4542, 4542, 4543, 4543, 4562, 4562, 4564, 4564, 4565, 4565, 4600, 4600, 4801, 4956, 4956, 4980, 4980, 5004, 5004, 5252, 5252, 5259, 5259, 5268, 5268, 5272, 5272, 5281, 5281
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `PromptUtils` (class, 441 lines)

- Def site: line 3482-3922
- References: 96
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3497, 3497, 3500, 3500, 3508, 3508, 3526, 3526, 3576, 3576, 3584, 3584, 3589, 3589, 3635, 3635, 3646, 3646, 3671, 3671, 3690, 3690, 3691, 3691, 3694, 3694, 3695, 3695, 3785, 3785, 3787, 3787, 3791, 3791, 3819, 3819, 3820, 3820, 3821, 3821, 3822, 3822, 3823, 3823, 3832, 3832, 3876, 3876, 3900, 3900, 4732, 4732, 4733, 4733, 4963, 4963, 5057, 5057, 5146, 5146, 5147, 5147, 5196, 5196, 5197, 5197, 5211, 5211, 5212, 5212, 5226, 5226, 5227, 5227, 5335, 5441, 5441, 5512, 5525, 5670, 5821, 5840, 5859, 5896, 5915, 5934, 5953, 5972, 5991, 6010
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `DataExporter` (class, 345 lines)

- Def site: line 3119-3463
- References: 118
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3165, 3165, 3181, 3181, 3182, 3182, 3205, 3205, 3207, 3207, 3210, 3210, 3224, 3224, 3226, 3226, 3235, 3235, 3237, 3237, 3238, 3238, 3244, 3244, 3245, 3245, 3245, 3262, 3262, 3266, 3266, 3308, 3308, 3339, 3339, 3342, 3342, 3344, 3344, 3390, 3390, 3400, 3400, 3433, 3433, 3438, 3438, 3445, 3445, 3539, 3539, 4498, 4498, 4573, 4573, 4735, 4735, 4797, 5010, 5010, 5030, 5118, 5118, 5338, 5368, 5368, 5381, 5381, 5514, 5527, 5618, 5618, 5673, 5698, 5698, 5714, 5714, 5824, 5843, 5862, 5899, 5918, 5937, 5956, 5975, 5994, 6013
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 2948-3105
- References: 69
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2964, 2964, 2977, 2977, 2980, 2980, 3004, 3004, 3012, 3012, 3013, 3013, 3035, 3035, 3040, 3040, 3042, 3042, 3341, 3341, 3366, 3366, 3435, 3435, 3436, 3436, 3537, 3537, 3538, 3538, 4495, 4495, 4496, 4496, 4570, 4570, 4571, 4571, 4798, 5008, 5008, 5009, 5009, 5337, 5513, 5526, 5672, 5823, 5842, 5861, 5898, 5917, 5936, 5955, 5974, 5993, 6012
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 4935-5012
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5476, 5476, 5480, 5480, 5484, 5484
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 2015-2088
- References: 195
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2028, 2028, 2060, 2060, 2295, 2295, 2322, 2322, 3503, 3503, 3580, 3580, 3663, 3663, 3893, 3893, 4734, 4734, 4803, 4903, 4962, 4962, 4987, 4987, 5029, 5056, 5056, 5114, 5114, 5150, 5150, 5200, 5200, 5215, 5215, 5230, 5230, 5366, 5366, 5379, 5379, 5616, 5616, 5654, 5654, 5696, 5696, 5796, 5796, 5801, 5801, 5807, 5807, 5880, 5880, 5886, 5886, 6934, 6934
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

## Skipped (1)

### `GlobalImportManager` (class, 1003 lines)

- Def site: line 891-1893
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1938

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
