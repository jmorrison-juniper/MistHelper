# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 202 first-party files
- Definitions analyzed: 75
- LOC saveable (unused + single-use): 3
- Category counts: unused=0, single-use=1, low-use=2, hot=71, skipped=1

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
| `OrgExportUtils` | class | 653 | 128 | hot |  | oversize_25_lines,non_ascii_logs,hardcoded_separator |
| `menu_actions` | assignment | 608 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `BulkRadiusWLANConfigManager` | class | 587 | 13 | hot |  | oversize_25_lines |
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
| `APICoreFetchUtils` | class | 47 | 55 | hot |  | oversize_25_lines,missing_inline_comments |
| `FilePathUtils` | class | 46 | 97 | hot |  | oversize_25_lines,missing_inline_comments |
| `SelfExportUtils` | class | 40 | 4 | hot |  | oversize_25_lines,non_ascii_logs |
| `TimeUtils` | class | 29 | 51 | hot |  | oversize_25_lines,missing_inline_comments |
| `GatewayStatsExporter` | class | 28 | 52 | hot |  | oversize_25_lines,missing_action_logging |
| `SSHRunnerManager` | class | 26 | 82 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
| `detect_msp_privileges` | function | 25 | 3 | low-use | DetectMspPrivilegesManager | missing_action_logging |
| `RoutingUtils` | class | 22 | 12 | hot |  | missing_inline_comments,missing_action_logging |
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

- Def site: line 2033-2035
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2033

## Low-Use (2)

### `detect_msp_privileges` (function, 25 lines)

- Def site: line 2142-2166
- References: 3
- Suggested class: `DetectMspPrivilegesManager`
- Suggested module: `src/refactors/detect_msp_privileges.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_attempt_interactive_login_with_rollback()`; extract `detect_msp_privileges` OUT of the entrypoint into a new `src/refactors/detect_msp_privileges.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2272, 16598, 19556

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2030-2032
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2030, 9809, 15063

## Hot (71)

### `ENDPOINT_PRIMARY_KEY_STRATEGIES` (assignment, 2327 lines)

- Def site: line 2880-5206
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2880, 6570, 6571, 6580, 6744

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13566-14324
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14043, 14043, 14055, 14055, 14083, 14083, 14095, 14095, 14156, 14156, 14193, 14193, 14350, 17980

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8895-9580
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5592, 5592, 9018, 9018, 9069, 9069, 9072, 9072, 9113, 9113, 9152, 9152, 9170, 9170, 9248, 9248, 9255, 9255, 9265, 9265, 9268, 9268, 9281, 9281, 9282, 9282, 9283, 9283, 9284, 9284, 9292, 9292, 9294, 9294, 9295, 9295, 9296, 9296, 9297, 9297, 9300, 9300, 9303, 9303, 9306, 9306, 9309, 9309, 9355, 9355, 9378, 9378, 9379, 9379, 9380, 9380, 9382, 9382, 9418, 9418, 9434, 9434, 9488, 9488, 9489, 9489, 9490, 9490, 9493, 9493, 9494, 9494, 9513, 9513, 9515, 9515, 9516, 9516, 9551, 9551, 14719, 14719, 14772, 14772, 15203, 15965, 15965, 15989, 15989, 16013, 16013, 16131, 16131, 17737, 17737, 17744, 17744, 17753, 17753, 17757, 17757, 17766, 17766
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11629-12281
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10405, 10405, 10414, 10414, 10502, 10502, 10509, 10509, 11184, 11184, 11470, 11470, 11475, 11475, 11482, 11482, 11487, 11487, 11701, 11701, 11723, 11723, 11726, 11726, 11752, 11752, 11761, 11761, 11762, 11762, 11783, 11783, 11826, 11826, 11872, 11872, 11883, 11883, 11910, 11910, 11915, 11915, 11916, 11916, 11917, 11917, 11949, 11949, 11955, 11955, 11980, 11980, 12000, 12000, 12035, 12035, 12050, 12050, 12056, 12056, 12058, 12058, 12061, 12061, 12063, 12063, 12067, 12067, 12071, 12071, 12076, 12076, 12083, 12083, 12090, 12090, 12097, 12097, 12106, 12106, 12116, 12116, 12123, 12123, 12130, 12130, 12137, 12137, 12144, 12144, 12151, 12151, 12161, 12161, 12170, 12170, 12179, 12179, 12188, 12188, 12197, 12197, 12226, 12226, 17698, 17698, 17897, 17897, 17974, 17974, 17975, 17975, 17983, 17983, 18206, 18206, 18207, 18207, 18226, 18226, 18233, 18233, 18234, 18234, 18235, 18235, 18236, 18236

### `menu_actions` (assignment, 608 lines)

- Def site: line 17679-18286
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17679, 19000, 19001, 19010, 19130, 19130, 19172, 19228, 19273, 19764, 19768, 19813, 19813, 19840, 19840, 19843
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 17003-17589
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17280, 17280, 17281, 17281, 17284, 17284, 17286, 17286, 17288, 17288, 17304, 17304, 18142

### `OrgTicketManager` (class, 475 lines)

- Def site: line 8167-8641
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8208, 8208, 8213, 8213, 8223, 8223, 8231, 8231, 8236, 8236, 8241, 8241, 8254, 8254, 8259, 8259, 8264, 8264, 8284, 8284, 8294, 8294, 8295, 8295, 8298, 8298, 8328, 8328, 8417, 8417, 8419, 8419, 8446, 8446, 8452, 8452, 8457, 8457, 8466, 8466, 8470, 8470, 8489, 8489, 8492, 8492, 8503, 8503, 8504, 8504, 8602, 8602, 8623, 8623, 18274, 18274, 18275, 18275, 18276, 18276, 18277, 18277, 18278, 18278, 18279, 18279

### `OperationRegistry` (class, 461 lines)

- Def site: line 18511-18971
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18978, 18978, 18982, 18982, 19002, 19002, 19007, 19007, 19229

### `PromptUtils` (class, 441 lines)

- Def site: line 7614-8054
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7559, 7559, 7575, 7575, 7579, 7579, 7580, 7580, 7581, 7581, 7596, 7596, 7602, 7602, 7629, 7629, 7632, 7632, 7640, 7640, 7658, 7658, 7708, 7708, 7716, 7716, 7721, 7721, 7767, 7767, 7778, 7778, 7803, 7803, 7822, 7822, 7823, 7823, 7826, 7826, 7827, 7827, 7917, 7917, 7919, 7919, 7923, 7923, 7951, 7951, 7952, 7952, 7953, 7953, 7954, 7954, 7955, 7955, 7964, 7964, 8008, 8008, 8032, 8032, 12361, 12361, 12411, 12411, 12416, 12416, 12559, 12642, 12642, 12696, 12696, 12717, 12717, 12722, 12722, 12986, 12986, 13189, 13391, 13391, 13478, 13478, 13483, 13483, 13533, 13533, 13534, 13534, 14846, 14846, 15305, 15972, 15972, 16463, 16463, 17603, 17603, 17604, 17604, 17908, 17908
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9583-9996
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5586, 5586, 9616, 9616, 9700, 9700, 9706, 9706, 9709, 9709, 9753, 9753, 9767, 9767, 9794, 9794, 9800, 9800, 9814, 9814, 9897, 9897, 9899, 9899, 9903, 9903, 9905, 9905, 9908, 9908, 9912, 9912, 9915, 9915, 9925, 9925, 9931, 9931, 9969, 9969, 14720, 14720, 14721, 14721, 14722, 14722, 14773, 14773, 14774, 14774, 17738, 17738, 17739, 17739, 17740, 17740, 17764, 17764

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 16050-16445
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16071, 16071, 16076, 16076, 16080, 16080, 16083, 16083, 16090, 16090, 16092, 16092, 16093, 16093, 16096, 16096, 16099, 16099, 16102, 16102, 16144, 16144, 16176, 16176, 16243, 16243, 16256, 16256, 16261, 16261, 16311, 16311, 16344, 16344, 16345, 16345, 16346, 16346, 16376, 16376, 16405, 16405, 16406, 16406, 17939, 17939

### `MSPInventoryExporter` (class, 386 lines)

- Def site: line 16495-16880
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16522, 16666, 16666, 18088, 18088

### `DataExporter` (class, 345 lines)

- Def site: line 6711-7055
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5682, 5682, 6757, 6757, 6773, 6773, 6774, 6774, 6797, 6797, 6799, 6799, 6802, 6802, 6816, 6816, 6818, 6818, 6827, 6827, 6829, 6829, 6830, 6830, 6836, 6836, 6837, 6837, 6837, 6854, 6854, 6858, 6858, 6900, 6900, 6931, 6931, 6934, 6934, 6936, 6936, 6982, 6982, 6992, 6992, 7025, 7025, 7030, 7030, 7037, 7037, 7259, 7259, 7291, 7291, 7302, 7302, 7327, 7327, 7347, 7347, 7671, 7671, 8473, 8473, 8755, 8755, 8770, 8834, 8834, 8851, 8851, 8869, 8869, 8890, 8890, 9449, 9449, 9524, 9524, 9854, 9854, 10205, 10205, 10290, 10306, 10426, 10426, 10430, 10430, 10450, 10450, 10463, 10463, 10467, 10467, 10485, 10485, 10647, 10647, 10995, 10995, 11142, 11142, 11219, 11219, 11223, 11223, 11228, 11228, 11361, 11361, 11380, 11380, 11431, 11431, 11434, 11434, 11585, 11585, 11588, 11588, 11687, 11687, 11693, 11693, 11990, 11990, 12007, 12007, 12022, 12022, 12236, 12236, 12264, 12264, 12280, 12280, 12317, 12317, 12355, 12355, 12444, 12444, 12473, 12473, 12511, 12511, 12562, 12627, 12627, 12633, 12633, 12675, 12675, 12844, 12844, 12850, 12850, 12969, 12969, 12977, 12977, 13141, 13141, 13192, 13365, 13365, 13536, 13536, 13865, 13865, 14226, 14226, 14232, 14232, 15140, 15140, 15199, 15306, 16019, 16019, 16039, 16846, 16846, 16931, 16931, 16952, 16952, 17438, 17438, 17835, 17835, 17848, 17848, 18062, 18062, 18117, 18117, 18133, 18133
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12683-13023
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12700, 12700, 12702, 12702, 12706, 12706, 12707, 12707, 12721, 12721, 12727, 12727, 12730, 12730, 12733, 12733, 12791, 12791, 12797, 12797, 12802, 12802, 12816, 12816, 12834, 12834, 12944, 12944, 12948, 12948, 12950, 12950, 12953, 12953, 12990, 12990, 12995, 12995, 13009, 13009, 13013, 13013, 13015, 13015, 13018, 13018, 13023, 13023, 17985, 17985, 17989, 17989, 17993, 17993

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7058-7385
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7160, 7160, 8188, 8681, 8700, 8801, 8930, 8953, 9625, 9933, 9978, 10392, 11163, 11174, 11237, 11654

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14330-14657
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11971, 11971, 12030, 12030, 12031, 12031, 13195, 14371, 14371, 14373, 14373, 14379, 14379, 14393, 14393, 14432, 14432, 14435, 14435, 14437, 14437, 14438, 14438, 14439, 14439, 14493, 14493, 14494, 14494, 14505, 14505, 14514, 14514, 14533, 14533, 14585, 14585, 14589, 14589, 14597, 14597, 14598, 14598, 14622, 14622, 14626, 14626
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 15633-15921
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15661, 15661, 15664, 15664, 15669, 15669, 15672, 15672, 15716, 15716, 15722, 15722, 15753, 15753, 15756, 15756, 15760, 15760, 15786, 15786, 15803, 15803, 15809, 15809, 15823, 15823, 15824, 15824, 15826, 15826, 15832, 15832, 15839, 15839, 15848, 15848, 15895, 15895, 15917, 15917, 15918, 15918, 15919, 15919, 17930, 17930

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9999-10271
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10022, 10022, 10023, 10023, 10036, 10036, 10037, 10037, 10039, 10039, 10040, 10040, 10043, 10043, 10046, 10046, 10050, 10050, 10051, 10051, 10127, 10127, 10131, 10131, 10134, 10134, 10147, 10147, 10184, 10184, 10201, 10201, 10214, 10214, 10216, 10216, 10223, 10223, 10232, 10232, 10241, 10241, 10242, 10242, 10253, 10253, 10257, 10257, 10266, 10266, 10271, 10271, 18205, 18205

### `CacheUtils` (class, 264 lines)

- Def site: line 5212-5475
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5252, 5252, 5254, 5254, 5336, 5336, 5342, 5342, 5379, 5379, 5381, 5381, 5390, 5390, 5400, 5400, 5410, 5410, 5446, 5446, 7707, 7707, 9377, 9377, 9378, 9378, 9689, 9689, 10535, 10535, 10555, 10555, 12557, 14779, 14779, 14785, 14785, 14786, 14786, 14787, 14787, 14788, 14788, 14789, 14789, 14790, 14790, 14797, 14797, 14825, 14825, 15197, 15448, 15964, 15964, 15988, 15988, 16012, 16012, 16131, 16131, 16132, 16132, 16133, 16133, 16134, 16134, 16464, 16464, 17654, 17654, 17836, 17836, 17849, 17849, 18063, 18063, 18242, 18242
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10767-11017
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10774, 10774, 10777, 10777, 10782, 10782, 10783, 10783, 10791, 10791, 10794, 10794, 10802, 10802, 10842, 10842, 10850, 10850, 10898, 10898, 10915, 10915, 10918, 10918, 10920, 10920, 10984, 10984, 10985, 10985, 18208, 18208

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 14909-15153
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14775, 14775, 14935, 14935, 14937, 14937, 14938, 14938, 14939, 14939, 14967, 14967, 14972, 14972, 14994, 14994, 14995, 14995, 15037, 15037, 15045, 15045, 15071, 15071, 15080, 15080, 15088, 15088, 15119, 15119, 17743, 17743, 17747, 17747

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6134-6354
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6157, 6157, 6208, 6208, 6278, 6278, 6302, 6302, 6314, 6314, 6316, 6316, 6326, 6326, 6341, 6341, 6345, 6345, 6346, 6346, 6349, 6349, 6351, 6351, 12670, 12670, 15201
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 18292-18505
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19148, 19148, 19151, 19230, 19581

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7398-7607
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7411, 7411, 7417, 7417, 7418, 7418, 7421, 7421, 7444, 7444, 7447, 7447, 7450, 7450, 7451, 7451, 7453, 7453, 7520, 7520, 7564, 7564, 8029, 8029, 12991, 12991, 15304, 15486, 15486, 15646, 15646

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12289-12491
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12310, 12310, 12319, 12319, 12381, 12381, 12388, 12388, 12420, 12420, 12422, 12422, 12446, 12446, 12481, 12481, 12488, 12488, 12519, 12519, 14849, 14849, 17779, 17779, 17781, 17781, 17782, 17782, 17784, 17784

### `SFPTransceiverDataProcessor` (class, 180 lines)

- Def site: line 5557-5736
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5645, 5645, 5682, 5682, 5684, 5684, 5687, 5687, 5695, 5695, 5697, 5697, 5699, 5699, 5702, 5702, 5731, 5731, 5734, 5734, 17924, 17924

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6530-6708
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6575, 6575, 6613, 6613, 6624, 6624, 6650, 6650, 6651, 6651, 6653, 6653, 6659, 6659, 6660, 6660, 6663, 6663, 6669, 6669, 6670, 6670, 6673, 6673, 6675, 6675, 6685, 6685, 6687, 6687, 6688, 6688, 6690, 6690

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11247-11414
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11354, 11354, 11373, 11373, 11391, 11391, 11400, 11400, 11403, 11403, 11404, 11404, 11407, 11407, 11412, 11412, 11414, 11414, 17807, 17807

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11459-11626
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11496, 11496, 11498, 11498, 11501, 11501, 11572, 11572, 11574, 11574, 11587, 11587, 11591, 11591, 17810, 17810, 17811, 17811, 17812, 17812, 17868, 17868, 17873, 17873

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10491-10652
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10529, 10529, 10536, 10536, 10543, 10543, 10549, 10549, 10556, 10556, 10563, 10563, 10624, 10624, 10635, 10635, 17798, 17798, 17799, 17799, 17801, 17801, 17802, 17802, 17803, 17803

### `CLIShellManager` (class, 161 lines)

- Def site: line 15467-15627
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15490, 15490, 15492, 15492, 15561, 15561, 15563, 15563, 15582, 15582, 15584, 15584, 15584, 15600, 15600, 15616, 15616, 15617, 15617, 15623, 15623, 17929, 17929

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6362-6519
- References: 197
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5510, 5510, 6378, 6378, 6391, 6391, 6394, 6394, 6418, 6418, 6426, 6426, 6427, 6427, 6449, 6449, 6454, 6454, 6456, 6456, 6933, 6933, 6958, 6958, 7027, 7027, 7028, 7028, 7357, 7357, 7371, 7371, 7372, 7372, 7669, 7669, 7670, 7670, 8604, 8604, 8769, 8829, 8829, 8831, 8831, 8832, 8832, 8849, 8849, 8850, 8850, 8867, 8867, 8868, 8868, 8888, 8888, 8889, 8889, 9446, 9446, 9447, 9447, 9521, 9521, 9522, 9522, 9850, 9850, 9853, 9853, 10428, 10428, 10429, 10429, 10465, 10465, 10466, 10466, 10645, 10645, 10646, 10646, 10991, 10991, 10992, 10992, 11138, 11138, 11139, 11139, 11221, 11221, 11222, 11222, 11433, 11433, 11608, 11608, 11609, 11609, 11685, 11685, 11686, 11686, 11989, 11989, 12005, 12005, 12006, 12006, 12234, 12234, 12235, 12235, 12314, 12314, 12315, 12315, 12316, 12316, 12352, 12352, 12353, 12353, 12441, 12441, 12442, 12442, 12470, 12470, 12471, 12471, 12508, 12508, 12509, 12509, 12561, 12630, 12630, 12631, 12631, 12673, 12673, 12674, 12674, 12842, 12842, 12843, 12843, 12967, 12967, 12968, 12968, 13191, 13363, 13363, 14231, 14231, 15138, 15138, 15139, 15139, 15200, 15308, 16017, 16017, 16018, 16018, 16836, 16836
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `DataCollectionManager` (class, 156 lines)

- Def site: line 14671-14826
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14693, 14693, 14699, 14699, 14701, 14701, 14729, 14729, 14755, 14755, 14758, 14758, 14761, 14761, 17915, 17915, 17919, 17919, 17927, 17927

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13026-13171
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13065, 13065, 13072, 13072, 13097, 13097, 13100, 13100, 13113, 13113, 13157, 13157, 13161, 13161, 13166, 13166, 13167, 13167, 13171, 13171, 18240, 18240

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13179-13323
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12400, 12400, 12576, 12576, 12654, 12654, 12659, 12659, 13208, 13208, 13214, 13214, 13220, 13220, 13226, 13226, 13232, 13232, 13238, 13238, 13244, 13244, 13250, 13250, 13256, 13256, 13262, 13262, 13268, 13268, 13274, 13274, 13280, 13280, 13286, 13286, 13292, 13292, 13298, 13298, 13304, 13304, 13310, 13310, 13316, 13316, 13322, 13322, 17817, 17817, 17976, 17976, 17978, 17978, 18102, 18102, 18237, 18237, 18238, 18238, 18239, 18239, 18258, 18258, 18259, 18259, 18260, 18260, 18261, 18261, 18262, 18262, 18263, 18263, 18264, 18264
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10345-10488
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10359, 10359, 10360, 10360, 10446, 10446, 10481, 10481, 17792, 17792, 17793, 17793, 17794, 17794, 17795, 17795, 17796, 17796

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13326-13464
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13395, 13395, 13398, 13398, 13399, 13399, 13400, 13400, 13420, 13420, 13423, 13423, 13431, 13431, 13436, 13436, 18266, 18266

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8647-8775
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8718, 8718, 8729, 8729, 14769, 14769, 14770, 14770, 17695, 17695, 17696, 17696, 17893, 17893

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11020-11148
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11027, 11027, 11032, 11032, 11033, 11033, 11034, 11034, 11037, 11037, 11038, 11038, 11101, 11101, 11108, 11108, 11135, 11135, 18210, 18210

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15294-15420
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15314, 15314, 15319, 15319, 15324, 15324, 15361, 15361, 15367, 15367, 15373, 15373, 15379, 15379, 15385, 15385, 15386, 15386, 15387, 15387, 15388, 15388, 15389, 15389, 15393, 15393, 15402, 15402, 15406, 15406, 15409, 15409, 15415, 15415, 17888, 17888

### `EnvironmentUtils` (class, 114 lines)

- Def site: line 5790-5903
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5811, 5811, 5813, 5813, 5829, 5829, 5841, 5841, 5880, 5880, 5881, 5881, 5882, 5882, 5883, 5883, 5884, 5884, 5895, 5895, 5898, 5898, 6815, 6815, 19243, 19243, 19826, 19826

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8781-8892
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7707, 7707, 9377, 9377, 9689, 9689, 10535, 10535, 10555, 10555, 12558, 14718, 14718, 14771, 14771, 15204, 15966, 15966, 15990, 15990, 16014, 16014, 16132, 16132, 16467, 16467, 17736, 17736, 17751, 17751, 17761, 17761, 17761, 17761, 17771, 17771, 17837, 17837, 17850, 17850, 18064, 18064
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 10655-10764
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10710, 10710, 10713, 10713, 10714, 10714, 10719, 10719, 10738, 10738, 10738, 10747, 10747, 10747, 10747, 10748, 10748, 10748, 10748, 10806, 10806, 10809, 10809, 10821, 10821, 10822, 10822, 10835, 10835, 10874, 10874, 10882, 10882, 10936, 10936, 10944, 10944

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12581-12680
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12646, 12646, 12648, 12648, 12649, 12649, 17745, 17745, 17813, 17813, 17815, 17815, 17816, 17816

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15186-15283
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14929, 14929, 15164, 15164, 15222, 15222, 15228, 15228, 15234, 15234, 15240, 15240, 15246, 15246, 15252, 15252, 15258, 15258, 15264, 15264, 15270, 15270, 15276, 15276, 15282, 15282, 15449, 16133, 16133, 16136, 16136, 16466, 16466, 17702, 17702, 17769, 17769, 17775, 17775, 17826, 17826, 17901, 17901
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8065-8161
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8121, 8121, 8157, 8157

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11151-11244
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11203, 11203, 11216, 11216, 17805, 17805, 17865, 17865, 17866, 17866, 17871, 17871, 17872, 17872

### `ValidationUtils` (class, 90 lines)

- Def site: line 5909-5998
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5991, 5991, 14992, 14992, 14993, 14993, 15207, 17605, 17605
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12494-12578
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12528, 12528, 17780, 17780, 17788, 17788, 17814, 17814, 17977, 17977

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 16907-16985
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16902, 16902, 16903, 16903, 18081, 18081
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 15944-16021
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17943, 17943, 17947, 17947, 17951, 17951
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\device\virtual_chassis.py`: lines 87, 87, 88, 88, 92, 92, 95, 95, 101, 101, 112, 112, 117, 117, 124, 124, 125, 125, 127, 127, 136, 136, 139, 139, 141, 141, 143, 143, 146, 146, 147, 147, 154, 154, 176, 176, 188, 188, 199, 199, 210, 210, 214, 214, 219, 219, 234, 234, 249, 249, 259, 259, 262, 262, 263, 263, 315, 315, 318, 318, 365, 365, 381, 381, 383, 383, 385, 385, 440, 440, 444, 444, 457, 457, 472, 472, 515, 515, 517, 517, 544, 544, 546, 546, 598, 598, 600, 600, 657, 657, 701, 701, 771, 771, 871, 871, 874, 874

### `InputUtils` (class, 74 lines)

- Def site: line 1918-1991
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1931, 1931, 1963, 1963, 2308, 2308, 2335, 2335, 7419, 7419, 7505, 7505, 7635, 7635, 7712, 7712, 7795, 7795, 8025, 8025, 8214, 8214, 8273, 8273, 8286, 8286, 8303, 8303, 8348, 8348, 8382, 8382, 8388, 8388, 8494, 8494, 10038, 10038, 10305, 10808, 10808, 10837, 10837, 11102, 11102, 11308, 11308, 11547, 11547, 12263, 12263, 12279, 12279, 13066, 13066, 13485, 13485, 13535, 13535, 15205, 15407, 15407, 15447, 15971, 15971, 15996, 15996, 16038, 16113, 16113, 16323, 16323, 16462, 16462, 16569, 16569, 16897, 16897, 16927, 16927, 16948, 16948, 16967, 16967, 16983, 16983, 17561, 17561, 17581, 17581, 17607, 17607, 17620, 17620, 17833, 17833, 17846, 17846, 18060, 18060, 18115, 18115, 18215, 18215, 18220, 18220, 18226, 18226, 18245, 18245, 18251, 18251, 19849, 19849
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

### `InteractiveDisplayUtils` (class, 72 lines)

- Def site: line 14832-14903
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17909, 17909, 17910, 17910, 17911, 17911, 17912, 17912

### `DisplayUtils` (class, 70 lines)

- Def site: line 5481-5550
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5513, 5513, 5514, 5514, 5529, 5529, 5531, 5531

### `ConfigUtils` (class, 70 lines)

- Def site: line 6004-6073
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6046, 6046, 6051, 6051, 6148, 6148, 6206, 6206, 7093, 7093, 7562, 7562, 8207, 8207, 8230, 8230, 8253, 8253, 8444, 8444, 8465, 8465, 8743, 8743, 8768, 8768, 8823, 8823, 8845, 8845, 8862, 8862, 8879, 8879, 9264, 9264, 9487, 9487, 9504, 9504, 9896, 9896, 10228, 10228, 10439, 10439, 10476, 10476, 10629, 10629, 10773, 10773, 11026, 11026, 11214, 11214, 11398, 11398, 11717, 11717, 12053, 12053, 12225, 12225, 12265, 12265, 12271, 12271, 12365, 12365, 12595, 12595, 12668, 12668, 13155, 13155, 13190, 13389, 13389, 14712, 14712, 14928, 14928, 15196, 15303, 15403, 15403, 16036, 16898, 16898, 16900, 16900, 16924, 16924, 16928, 16928, 16929, 16929, 16949, 16949, 16950, 16950, 17095, 17095, 17656, 17656, 17688, 17688, 17725, 17725, 17731, 17731, 17831, 17831, 17844, 17844, 17877, 17877, 17934, 17934, 18017, 18017, 18026, 18026, 18058, 18058, 18113, 18113, 18114, 18114, 18131, 18131, 18215, 18215, 18220, 18220, 18226, 18226, 18245, 18245, 18251, 18251, 19162, 19162, 19231, 19713, 19713, 19801, 19801
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10274-10342
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10314, 10314, 10319, 10319, 10324, 10324, 10325, 10325, 10331, 10331, 10332, 10332, 10338, 10338, 10339, 10339, 10340, 10340, 10341, 10341, 18268, 18268

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 17611-17676
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17659, 17659, 17667, 17667, 17676, 17676, 18241, 18241

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6079-6125
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6203, 6203, 7897, 7897, 8824, 8824, 8847, 8847, 9334, 9334, 9369, 9369, 9383, 9383, 9506, 9506, 9510, 9510, 10058, 10058, 12369, 12369, 13039, 13039, 13165, 13165, 13197, 13375, 13375, 13411, 13411, 15202, 16788, 16788, 16899, 16899, 16930, 16930, 16951, 16951, 18116, 18116, 18132, 18132, 19732, 19732
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

### `FilePathUtils` (class, 46 lines)

- Def site: line 5739-5784
- References: 97
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5251, 5251, 5293, 5293, 5338, 5338, 5444, 5444, 5459, 5459, 5729, 5729, 5730, 5730, 5774, 5774, 6229, 6229, 7731, 7731, 9034, 9034, 9345, 9345, 9361, 9361, 9690, 9690, 10571, 10571, 10590, 10590, 12560, 14795, 14795, 15198, 15450, 15872, 15872, 15912, 15912, 15913, 15913, 15914, 15914, 15963, 15963, 15987, 15987, 15991, 15991, 16011, 16011, 16037, 16088, 16088, 16122, 16122, 16143, 16143, 16175, 16175, 16237, 16237, 16276, 16276, 16424, 16424, 16465, 16465, 17834, 17834, 17847, 17847, 18061, 18061
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11417-11456
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11454, 11454, 18265, 18265

### `TimeUtils` (class, 29 lines)

- Def site: line 1882-1910
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8697, 8697, 8698, 8698, 8727, 8727, 8728, 8728, 8744, 8744, 8745, 8745, 9623, 9623, 9624, 9624, 9928, 9928, 9929, 9929, 9976, 9976, 9977, 9977, 10532, 10532, 10534, 10534, 10552, 10552, 10554, 10554, 11443, 11443, 11444, 11444, 12104, 12104, 12105, 12105, 12210, 12210, 12211, 12211, 13193
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15156-15183
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15170, 15170, 15176, 15176, 15182, 15182, 17955, 17955, 17959, 17959
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15436-15461
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15456, 15456, 15461, 15461, 17963, 17963, 17968, 17968
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13492-13513
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17711, 17711, 17715, 17715, 17719, 17719
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 16883-16904
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18095, 18095
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `EndpointConfig` (class, 10 lines)

- Def site: line 13554-13563
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13590, 13726, 13803, 13822, 13834, 13855, 13868, 13879, 13885, 13898, 13991, 14126, 14221

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 342-350
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

- Def site: line 369-377
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14864, 14881, 14897
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 354-361
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

- Def site: line 649-651
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1259, 1928, 1928, 1928, 1940, 1946, 6205, 6325, 7381, 9433, 9544, 9798, 10628, 13200, 15074, 15116, 15214, 18118
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

- Def site: line 2044-2046
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2044, 15210
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 23, 270, 272, 287, 290, 294, 297

## Skipped (1)

### `GlobalImportManager` (class, 1005 lines)

- Def site: line 765-1769
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1814

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
