# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 228 first-party files
- Definitions analyzed: 49
- LOC saveable (unused + single-use): 12
- Category counts: unused=0, single-use=2, low-use=2, hot=44, skipped=1

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
| `OrgExportUtils` | class | 653 | 114 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `menu_actions` | assignment | 608 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgTicketManager` | class | 475 | 66 | hot |  | oversize_25_lines |
| `PromptUtils` | class | 441 | 110 | hot |  | oversize_25_lines |
| `OrgDeviceStatsExporter` | class | 414 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DeviceRebootManager` | class | 396 | 46 | hot |  | oversize_25_lines,missing_inline_comments |
| `DataExporter` | class | 345 | 178 | hot |  | oversize_25_lines,non_ascii_logs |
| `SiteAnomalyExporter` | class | 341 | 54 | hot |  | oversize_25_lines,non_ascii_logs |
| `InsightMetricsUtils` | class | 328 | 51 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `ARPCommandManager` | class | 289 | 46 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `OfflineDeviceReporter` | class | 273 | 54 | hot |  | oversize_25_lines,missing_inline_comments |
| `CacheUtils` | class | 264 | 85 | hot |  | oversize_25_lines |
| `GlobalWiredClientReportGenerator` | class | 251 | 32 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `GatewayTestExporter` | class | 245 | 32 | hot |  | oversize_25_lines,missing_inline_comments,non_ascii_logs |
| `APIFetchUtils` | class | 221 | 34 | hot |  | oversize_25_lines |
| `PromptClientUtils` | class | 210 | 29 | hot |  | oversize_25_lines,raw_input_call |
| `SiteDeviceExporter` | class | 203 | 26 | hot |  | oversize_25_lines,non_ascii_logs |
| `DatabaseSchemaUtils` | class | 179 | 34 | hot |  | oversize_25_lines |
| `OrgClientSecurityExporter` | class | 162 | 26 | hot |  | oversize_25_lines |
| `DataProcessingUtils` | class | 158 | 147 | hot |  | oversize_25_lines,missing_inline_comments,hardcoded_separator |
| `SiteExportUtils` | class | 145 | 88 | hot |  | oversize_25_lines,missing_action_logging |
| `TroubleshootUtils` | class | 127 | 36 | hot |  | oversize_25_lines,non_ascii_logs |
| `EnvironmentUtils` | class | 114 | 28 | hot |  | oversize_25_lines,hardcoded_separator |
| `OrgSiteExporter` | class | 112 | 47 | hot |  | oversize_25_lines |
| `FilterOperatorEngine` | class | 110 | 37 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `GatewayExportUtils` | class | 98 | 78 | hot |  | oversize_25_lines,missing_action_logging |
| `ValidationUtils` | class | 90 | 15 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `OrgLevelAPFirmwareUpgrader` | class | 79 | 33 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `VirtualChassisManager` | class | 78 | 104 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `InputUtils` | class | 74 | 233 | hot |  | oversize_25_lines,raw_input_call |
| `ConfigUtils` | class | 70 | 152 | hot |  | oversize_25_lines |
| `APICoreFetchUtils` | class | 47 | 45 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 90 | hot |  | oversize_25_lines,missing_inline_comments |
| `TimeUtils` | class | 29 | 35 | hot |  | oversize_25_lines,missing_inline_comments |
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

- Def site: line 439-447
- References: 1
- Suggested class: `DeviceDataFetcherManager`
- Suggested module: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`
- Rationale: Sole caller lives in `device_data_fetcher.py` inside `__init__()`; move `DeviceFetchConfig` into that module's semantic class so callers rewrite in one PR
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `FAST_MODE_USE_CONNECTION_AWARE_THREADING` (assignment, 3 lines)

- Def site: line 2102-2104
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2102

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2211-2235
- References: 2
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2341, 14672

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2099-2101
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2099, 9073, 12062

## Hot (44)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2949-5275
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2949, 6393, 6394, 6403, 6567

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8159-8844
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8282, 8282, 8333, 8333, 8336, 8336, 8377, 8377, 8416, 8416, 8434, 8434, 8512, 8512, 8519, 8519, 8529, 8529, 8532, 8532, 8545, 8545, 8546, 8546, 8547, 8547, 8548, 8548, 8556, 8556, 8558, 8558, 8559, 8559, 8560, 8560, 8561, 8561, 8564, 8564, 8567, 8567, 8570, 8570, 8573, 8573, 8619, 8619, 8642, 8642, 8643, 8643, 8644, 8644, 8646, 8646, 8682, 8682, 8698, 8698, 8752, 8752, 8753, 8753, 8754, 8754, 8757, 8757, 8758, 8758, 8777, 8777, 8779, 8779, 8780, 8780, 8815, 8815, 12202, 12802, 12802, 12826, 12826, 12850, 12850, 12968, 12968, 13532, 13532, 13539, 13539, 13548, 13548, 13552, 13552, 13561, 13561
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgExportUtils` (class, 653 lines)

- Def site: line 10090-10742
- References: 114
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9556, 9556, 9563, 9563, 10162, 10162, 10184, 10184, 10187, 10187, 10213, 10213, 10222, 10222, 10223, 10223, 10244, 10244, 10287, 10287, 10333, 10333, 10344, 10344, 10371, 10371, 10376, 10376, 10377, 10377, 10378, 10378, 10410, 10410, 10416, 10416, 10441, 10441, 10461, 10461, 10496, 10496, 10511, 10511, 10517, 10517, 10519, 10519, 10522, 10522, 10524, 10524, 10528, 10528, 10532, 10532, 10537, 10537, 10544, 10544, 10551, 10551, 10558, 10558, 10567, 10567, 10577, 10577, 10584, 10584, 10591, 10591, 10598, 10598, 10605, 10605, 10612, 10612, 10622, 10622, 10631, 10631, 10640, 10640, 10649, 10649, 10658, 10658, 10687, 10687, 13493, 13493, 13692, 13692, 13769, 13769, 13770, 13770, 13778, 13778, 14001, 14001, 14002, 14002, 14021, 14021, 14028, 14028, 14029, 14029, 14030, 14030, 14031, 14031

### `menu_actions` (assignment, 608 lines)

- Def site: line 13474-14081
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13474, 14116, 14117, 14126, 14246, 14246, 14288, 14344, 14389, 14880, 14884, 14929, 14929, 14956, 14956, 14959
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `OrgTicketManager` (class, 475 lines)

- Def site: line 7562-8036
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7603, 7603, 7608, 7608, 7618, 7618, 7626, 7626, 7631, 7631, 7636, 7636, 7649, 7649, 7654, 7654, 7659, 7659, 7679, 7679, 7689, 7689, 7690, 7690, 7693, 7693, 7723, 7723, 7812, 7812, 7814, 7814, 7841, 7841, 7847, 7847, 7852, 7852, 7861, 7861, 7865, 7865, 7884, 7884, 7887, 7887, 7898, 7898, 7899, 7899, 7997, 7997, 8018, 8018, 14069, 14069, 14070, 14070, 14071, 14071, 14072, 14072, 14073, 14073, 14074, 14074

### `PromptUtils` (class, 441 lines)

- Def site: line 7110-7550
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7055, 7055, 7071, 7071, 7075, 7075, 7076, 7076, 7077, 7077, 7092, 7092, 7098, 7098, 7125, 7125, 7128, 7128, 7136, 7136, 7154, 7154, 7204, 7204, 7212, 7212, 7217, 7217, 7263, 7263, 7274, 7274, 7299, 7299, 7318, 7318, 7319, 7319, 7322, 7322, 7323, 7323, 7413, 7413, 7415, 7415, 7419, 7419, 7447, 7447, 7448, 7448, 7449, 7449, 7450, 7450, 7451, 7451, 7460, 7460, 7504, 7504, 7528, 7528, 10822, 10822, 10872, 10872, 10877, 10877, 10974, 10974, 10995, 10995, 11000, 11000, 11264, 11264, 11322, 11473, 11473, 11478, 11478, 11528, 11528, 11529, 11529, 12304, 12809, 12809, 13300, 13300, 13459, 13459, 13460, 13460, 13703, 13703
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 8847-9260
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8880, 8880, 8964, 8964, 8970, 8970, 8973, 8973, 9017, 9017, 9031, 9031, 9058, 9058, 9064, 9064, 9078, 9078, 9161, 9161, 9163, 9163, 9167, 9167, 9169, 9169, 9172, 9172, 9176, 9176, 9179, 9179, 9189, 9189, 9195, 9195, 9233, 9233, 13533, 13533, 13534, 13534, 13535, 13535, 13559, 13559

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 12887-13282
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12908, 12908, 12913, 12913, 12917, 12917, 12920, 12920, 12927, 12927, 12929, 12929, 12930, 12930, 12933, 12933, 12936, 12936, 12939, 12939, 12981, 12981, 13013, 13013, 13080, 13080, 13093, 13093, 13098, 13098, 13148, 13148, 13181, 13181, 13182, 13182, 13183, 13183, 13213, 13213, 13242, 13242, 13243, 13243, 13734, 13734

### `DataExporter` (class, 345 lines)

- Def site: line 6534-6878
- References: 178
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6580, 6580, 6596, 6596, 6597, 6597, 6620, 6620, 6622, 6622, 6625, 6625, 6639, 6639, 6641, 6641, 6650, 6650, 6652, 6652, 6653, 6653, 6659, 6659, 6660, 6660, 6660, 6677, 6677, 6681, 6681, 6723, 6723, 6754, 6754, 6757, 6757, 6759, 6759, 6805, 6805, 6815, 6815, 6848, 6848, 6853, 6853, 6860, 6860, 7167, 7167, 7868, 7868, 8098, 8098, 8115, 8115, 8133, 8133, 8154, 8154, 8713, 8713, 8788, 8788, 9118, 9118, 9469, 9469, 9701, 9701, 10049, 10049, 10148, 10148, 10154, 10154, 10451, 10451, 10468, 10468, 10483, 10483, 10697, 10697, 10725, 10725, 10741, 10741, 10778, 10778, 10816, 10816, 10905, 10905, 10934, 10934, 11122, 11122, 11128, 11128, 11247, 11247, 11255, 11255, 11325, 11531, 11531, 12139, 12139, 12198, 12305, 12856, 12856, 12876, 13383, 13383, 13404, 13404, 13630, 13630, 13643, 13643, 13857, 13857, 13912, 13912, 13928, 13928
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 10961-11301
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10978, 10978, 10980, 10980, 10984, 10984, 10985, 10985, 10999, 10999, 11005, 11005, 11008, 11008, 11011, 11011, 11069, 11069, 11075, 11075, 11080, 11080, 11094, 11094, 11112, 11112, 11222, 11222, 11226, 11226, 11228, 11228, 11231, 11231, 11268, 11268, 11273, 11273, 11287, 11287, 11291, 11291, 11293, 11293, 11296, 11296, 11301, 11301, 13780, 13780, 13784, 13784, 13788, 13788

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 11557-11884
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10432, 10432, 10491, 10491, 10492, 10492, 11328, 11598, 11598, 11600, 11600, 11606, 11606, 11620, 11620, 11659, 11659, 11662, 11662, 11664, 11664, 11665, 11665, 11666, 11666, 11720, 11720, 11721, 11721, 11732, 11732, 11741, 11741, 11760, 11760, 11812, 11812, 11816, 11816, 11824, 11824, 11825, 11825, 11849, 11849, 11853, 11853
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 12470-12758
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12498, 12498, 12501, 12501, 12506, 12506, 12509, 12509, 12553, 12553, 12559, 12559, 12590, 12590, 12593, 12593, 12597, 12597, 12623, 12623, 12640, 12640, 12646, 12646, 12660, 12660, 12661, 12661, 12663, 12663, 12669, 12669, 12676, 12676, 12685, 12685, 12732, 12732, 12754, 12754, 12755, 12755, 12756, 12756, 13725, 13725

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9263-9535
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9286, 9286, 9287, 9287, 9300, 9300, 9301, 9301, 9303, 9303, 9304, 9304, 9307, 9307, 9310, 9310, 9314, 9314, 9315, 9315, 9391, 9391, 9395, 9395, 9398, 9398, 9411, 9411, 9448, 9448, 9465, 9465, 9478, 9478, 9480, 9480, 9487, 9487, 9496, 9496, 9505, 9505, 9506, 9506, 9517, 9517, 9521, 9521, 9530, 9530, 9535, 9535, 14000, 14000

### `CacheUtils` (class, 264 lines)

- Def site: line 5281-5544
- References: 85
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5321, 5321, 5323, 5323, 5405, 5405, 5411, 5411, 5448, 5448, 5450, 5450, 5459, 5459, 5469, 5469, 5479, 5479, 5515, 5515, 7203, 7203, 8641, 8641, 8642, 8642, 8953, 8953, 9589, 9589, 9609, 9609, 12196, 12447, 12801, 12801, 12825, 12825, 12849, 12849, 12968, 12968, 12969, 12969, 12970, 12970, 12971, 12971, 13301, 13301, 13631, 13631, 13644, 13644, 13858, 13858, 14037, 14037
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 9821-10071
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9828, 9828, 9831, 9831, 9836, 9836, 9837, 9837, 9845, 9845, 9848, 9848, 9856, 9856, 9896, 9896, 9904, 9904, 9952, 9952, 9969, 9969, 9972, 9972, 9974, 9974, 10038, 10038, 10039, 10039, 14003, 14003

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 11908-12152
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11934, 11934, 11936, 11936, 11937, 11937, 11938, 11938, 11966, 11966, 11971, 11971, 11993, 11993, 11994, 11994, 12036, 12036, 12044, 12044, 12070, 12070, 12079, 12079, 12087, 12087, 12118, 12118, 13538, 13538, 13542, 13542

### `APIFetchUtils` (class, 221 lines)

- Def site: line 5957-6177
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5980, 5980, 6031, 6031, 6101, 6101, 6125, 6125, 6137, 6137, 6139, 6139, 6149, 6149, 6164, 6164, 6168, 6168, 6169, 6169, 6172, 6172, 6174, 6174, 12200
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `PromptClientUtils` (class, 210 lines)

- Def site: line 6894-7103
- References: 29
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6907, 6907, 6913, 6913, 6914, 6914, 6917, 6917, 6940, 6940, 6943, 6943, 6946, 6946, 6947, 6947, 6949, 6949, 7016, 7016, 7060, 7060, 7525, 7525, 11269, 11269, 12303, 12483, 12483

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 10750-10952
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10771, 10771, 10780, 10780, 10842, 10842, 10849, 10849, 10881, 10881, 10883, 10883, 10907, 10907, 10942, 10942, 10949, 10949, 13574, 13574, 13576, 13576, 13577, 13577, 13579, 13579

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6353-6531
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6398, 6398, 6436, 6436, 6447, 6447, 6473, 6473, 6474, 6474, 6476, 6476, 6482, 6482, 6483, 6483, 6486, 6486, 6492, 6492, 6493, 6493, 6496, 6496, 6498, 6498, 6508, 6508, 6510, 6510, 6511, 6511, 6513, 6513

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 9545-9706
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9583, 9583, 9590, 9590, 9597, 9597, 9603, 9603, 9610, 9610, 9617, 9617, 9678, 9678, 9689, 9689, 13593, 13593, 13594, 13594, 13596, 13596, 13597, 13597, 13598, 13598

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6185-6342
- References: 147
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6201, 6201, 6214, 6214, 6217, 6217, 6241, 6241, 6249, 6249, 6250, 6250, 6272, 6272, 6277, 6277, 6279, 6279, 6756, 6756, 6781, 6781, 6850, 6850, 6851, 6851, 7165, 7165, 7166, 7166, 7999, 7999, 8093, 8093, 8095, 8095, 8096, 8096, 8113, 8113, 8114, 8114, 8131, 8131, 8132, 8132, 8152, 8152, 8153, 8153, 8710, 8710, 8711, 8711, 8785, 8785, 8786, 8786, 9114, 9114, 9117, 9117, 9699, 9699, 9700, 9700, 10045, 10045, 10046, 10046, 10146, 10146, 10147, 10147, 10450, 10450, 10466, 10466, 10467, 10467, 10695, 10695, 10696, 10696, 10775, 10775, 10776, 10776, 10777, 10777, 10813, 10813, 10814, 10814, 10902, 10902, 10903, 10903, 10931, 10931, 10932, 10932, 11120, 11120, 11121, 11121, 11245, 11245, 11246, 11246, 11324, 12137, 12137, 12138, 12138, 12199, 12307, 12854, 12854, 12855, 12855
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `SiteExportUtils` (class, 145 lines)

- Def site: line 11312-11456
- References: 88
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10861, 10861, 11341, 11341, 11347, 11347, 11353, 11353, 11359, 11359, 11365, 11365, 11371, 11371, 11377, 11377, 11383, 11383, 11389, 11389, 11395, 11395, 11401, 11401, 11407, 11407, 11413, 11413, 11419, 11419, 11425, 11425, 11431, 11431, 11437, 11437, 11443, 11443, 11449, 11449, 11455, 11455, 13612, 13612, 13771, 13771, 13773, 13773, 13897, 13897, 14032, 14032, 14033, 14033, 14034, 14034, 14053, 14053, 14054, 14054, 14055, 14055, 14056, 14056, 14057, 14057, 14058, 14058, 14059, 14059
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 12293-12419
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12313, 12313, 12318, 12318, 12323, 12323, 12360, 12360, 12366, 12366, 12372, 12372, 12378, 12378, 12384, 12384, 12385, 12385, 12386, 12386, 12387, 12387, 12388, 12388, 12392, 12392, 12401, 12401, 12405, 12405, 12408, 12408, 12414, 12414, 13683, 13683

### `EnvironmentUtils` (class, 114 lines)

- Def site: line 5613-5726
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5634, 5634, 5636, 5636, 5652, 5652, 5664, 5664, 5703, 5703, 5704, 5704, 5705, 5705, 5706, 5706, 5707, 5707, 5718, 5718, 5721, 5721, 6638, 6638, 14359, 14359, 14942, 14942

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8045-8156
- References: 47
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7203, 7203, 8641, 8641, 8953, 8953, 9589, 9589, 9609, 9609, 12203, 12803, 12803, 12827, 12827, 12851, 12851, 12969, 12969, 13304, 13304, 13531, 13531, 13546, 13546, 13556, 13556, 13556, 13556, 13566, 13566, 13632, 13632, 13645, 13645, 13859, 13859
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 9709-9818
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 9764, 9764, 9767, 9767, 9768, 9768, 9773, 9773, 9792, 9792, 9792, 9801, 9801, 9801, 9801, 9802, 9802, 9802, 9802, 9860, 9860, 9863, 9863, 9875, 9875, 9876, 9876, 9889, 9889, 9928, 9928, 9936, 9936, 9990, 9990, 9998, 9998

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 12185-12282
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11928, 11928, 12163, 12163, 12221, 12221, 12227, 12227, 12233, 12233, 12239, 12239, 12245, 12245, 12251, 12251, 12257, 12257, 12263, 12263, 12269, 12269, 12275, 12275, 12281, 12281, 12448, 12970, 12970, 12973, 12973, 13303, 13303, 13497, 13497, 13564, 13564, 13570, 13570, 13621, 13621, 13696, 13696
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `ValidationUtils` (class, 90 lines)

- Def site: line 5732-5821
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5814, 5814, 11991, 11991, 11992, 11992, 12206, 13461, 13461
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 13359-13437
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13354, 13354, 13355, 13355, 13876, 13876
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 12781-12858
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13738, 13738, 13742, 13742, 13746, 13746
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1987-2060
- References: 233
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2000, 2000, 2032, 2032, 2377, 2377, 2404, 2404, 6915, 6915, 7001, 7001, 7131, 7131, 7208, 7208, 7291, 7291, 7521, 7521, 7609, 7609, 7668, 7668, 7681, 7681, 7698, 7698, 7743, 7743, 7777, 7777, 7783, 7783, 7889, 7889, 9302, 9302, 9862, 9862, 9891, 9891, 10724, 10724, 10740, 10740, 11480, 11480, 11530, 11530, 12204, 12406, 12406, 12446, 12808, 12808, 12833, 12833, 12875, 12950, 12950, 13160, 13160, 13299, 13299, 13349, 13349, 13379, 13379, 13400, 13400, 13419, 13419, 13435, 13435, 13463, 13463, 13628, 13628, 13641, 13641, 13855, 13855, 13910, 13910, 14010, 14010, 14015, 14015, 14021, 14021, 14040, 14040, 14046, 14046, 14965, 14965
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

- Def site: line 5827-5896
- References: 152
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5869, 5869, 5874, 5874, 5971, 5971, 6029, 6029, 7058, 7058, 7602, 7602, 7625, 7625, 7648, 7648, 7839, 7839, 7860, 7860, 8087, 8087, 8109, 8109, 8126, 8126, 8143, 8143, 8528, 8528, 8751, 8751, 8768, 8768, 9160, 9160, 9492, 9492, 9683, 9683, 9827, 9827, 10178, 10178, 10514, 10514, 10686, 10686, 10726, 10726, 10732, 10732, 10826, 10826, 11323, 11927, 11927, 12195, 12302, 12402, 12402, 12873, 13350, 13350, 13352, 13352, 13376, 13376, 13380, 13380, 13381, 13381, 13401, 13401, 13402, 13402, 13483, 13483, 13520, 13520, 13526, 13526, 13626, 13626, 13639, 13639, 13672, 13672, 13729, 13729, 13812, 13812, 13821, 13821, 13853, 13853, 13908, 13908, 13909, 13909, 13926, 13926, 14010, 14010, 14015, 14015, 14021, 14021, 14040, 14040, 14046, 14046, 14278, 14278, 14347, 14829, 14829, 14917, 14917
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 5902-5948
- References: 45
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6026, 6026, 7393, 7393, 8088, 8088, 8111, 8111, 8598, 8598, 8633, 8633, 8647, 8647, 8770, 8770, 8774, 8774, 9322, 9322, 10830, 10830, 11330, 12201, 13351, 13351, 13382, 13382, 13403, 13403, 13911, 13911, 13927, 13927, 14848, 14848
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5562-5607
- References: 90
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5320, 5320, 5362, 5362, 5407, 5407, 5513, 5513, 5528, 5528, 5597, 5597, 6052, 6052, 7227, 7227, 8298, 8298, 8609, 8609, 8625, 8625, 8954, 8954, 9625, 9625, 9644, 9644, 12197, 12449, 12709, 12709, 12749, 12749, 12750, 12750, 12751, 12751, 12800, 12800, 12824, 12824, 12828, 12828, 12848, 12848, 12874, 12925, 12925, 12959, 12959, 12980, 12980, 13012, 13012, 13074, 13074, 13113, 13113, 13261, 13261, 13302, 13302, 13629, 13629, 13642, 13642, 13856, 13856
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `TimeUtils` (class, 29 lines)

- Def site: line 1951-1979
- References: 35
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8887, 8887, 8888, 8888, 9192, 9192, 9193, 9193, 9240, 9240, 9241, 9241, 9586, 9586, 9588, 9588, 9606, 9606, 9608, 9608, 10565, 10565, 10566, 10566, 10671, 10671, 10672, 10672, 11326
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 12155-12182
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12169, 12169, 12175, 12175, 12181, 12181, 13750, 13750, 13754, 13754
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 12435-12460
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12455, 12455, 12460, 12460, 13758, 13758, 13763, 13763
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 11487-11508
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13506, 13506, 13510, 13510, 13514, 13514
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 13335-13356
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13890, 13890
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 412-420
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

- Def site: line 424-431
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

- Def site: line 718-720
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1328, 1997, 1997, 1997, 2009, 2015, 6028, 6148, 8697, 8808, 9062, 9682, 11333, 12073, 12115, 12213, 13913
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\api\api_data_fetcher.py`: lines 359
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

- Def site: line 2113-2115
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2113, 12209
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 834-1838
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1883

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
