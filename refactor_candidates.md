# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 201 first-party files
- Definitions analyzed: 79
- LOC saveable (unused + single-use): 3
- Category counts: unused=0, single-use=1, low-use=2, hot=75, skipped=1

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
| `menu_actions` | assignment | 599 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |
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

- Def site: line 2019-2021
- References: 1
- Suggested class: `FastModeUseConnectionAwareThreadingManager`
- Suggested module: `src/refactors/fast__mode__use__connection__aware__threading.py`
- Rationale: single-use: sole caller lives inside MistHelper.py; extract `FAST_MODE_USE_CONNECTION_AWARE_THREADING` OUT of the entrypoint into a new `src/refactors/fast__mode__use__connection__aware__threading.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2019

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2258, 17470, 20419

### `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` (assignment, 3 lines)

- Def site: line 2016-2018
- References: 3
- Suggested class: `FastModeMaxConcurrentConnectionsManager`
- Suggested module: `src/refactors/fast__mode__max__concurrent__connections.py`
- Rationale: low-use: sole caller lives inside MistHelper.py from `_retry_failed_site_port_stats()`; extract `FAST_MODE_MAX_CONCURRENT_CONNECTIONS` OUT of the entrypoint into a new `src/refactors/fast__mode__max__concurrent__connections.py` module and rewrite the callsite(s) to import from there
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2016, 9795, 15233

## Hot (75)

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2866, 6556, 6557, 6566, 6730

### `ConstDefinitionsExporter` (class, 759 lines)

- Def site: line 13736-14494
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14213, 14213, 14225, 14225, 14253, 14253, 14265, 14265, 14326, 14326, 14363, 14363, 14520, 18852

### `OrgInventoryExporter` (class, 686 lines)

- Def site: line 8881-9566
- References: 110
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5578, 5578, 9004, 9004, 9055, 9055, 9058, 9058, 9099, 9099, 9138, 9138, 9156, 9156, 9234, 9234, 9241, 9241, 9251, 9251, 9254, 9254, 9267, 9267, 9268, 9268, 9269, 9269, 9270, 9270, 9278, 9278, 9280, 9280, 9281, 9281, 9282, 9282, 9283, 9283, 9286, 9286, 9289, 9289, 9292, 9292, 9295, 9295, 9341, 9341, 9364, 9364, 9365, 9365, 9366, 9366, 9368, 9368, 9404, 9404, 9420, 9420, 9474, 9474, 9475, 9475, 9476, 9476, 9479, 9479, 9480, 9480, 9499, 9499, 9501, 9501, 9502, 9502, 9537, 9537, 14889, 14889, 14942, 14942, 15373, 16808, 16808, 16832, 16832, 16856, 16856, 16999, 16999, 18609, 18609, 18616, 18616, 18625, 18625, 18629, 18629, 18638, 18638
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 46, 295, 295, 343, 343, 499, 499

### `OrgConfigMigrationManager` (class, 675 lines)

- Def site: line 16107-16781
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16495, 16495, 19107, 19113

### `OrgExportUtils` (class, 653 lines)

- Def site: line 11615-12267
- References: 128
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10391, 10391, 10400, 10400, 10488, 10488, 10495, 10495, 11170, 11170, 11456, 11456, 11461, 11461, 11468, 11468, 11473, 11473, 11687, 11687, 11709, 11709, 11712, 11712, 11738, 11738, 11747, 11747, 11748, 11748, 11769, 11769, 11812, 11812, 11858, 11858, 11869, 11869, 11896, 11896, 11901, 11901, 11902, 11902, 11903, 11903, 11935, 11935, 11941, 11941, 11966, 11966, 11986, 11986, 12021, 12021, 12036, 12036, 12042, 12042, 12044, 12044, 12047, 12047, 12049, 12049, 12053, 12053, 12057, 12057, 12062, 12062, 12069, 12069, 12076, 12076, 12083, 12083, 12092, 12092, 12102, 12102, 12109, 12109, 12116, 12116, 12123, 12123, 12130, 12130, 12137, 12137, 12147, 12147, 12156, 12156, 12165, 12165, 12174, 12174, 12183, 12183, 12212, 12212, 18570, 18570, 18769, 18769, 18846, 18846, 18847, 18847, 18855, 18855, 19069, 19069, 19070, 19070, 19089, 19089, 19096, 19096, 19097, 19097, 19098, 19098, 19099, 19099

### `menu_actions` (assignment, 599 lines)

- Def site: line 18551-19149
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18551, 19863, 19864, 19873, 19993, 19993, 20035, 20091, 20136, 20627, 20631, 20676, 20676, 20703, 20703, 20706
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

### `BulkRadiusWLANConfigManager` (class, 587 lines)

- Def site: line 17875-18461
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18152, 18152, 18153, 18153, 18156, 18156, 18158, 18158, 18160, 18160, 18176, 18176, 19014

### `OrgTicketManager` (class, 475 lines)

- Def site: line 8153-8627
- References: 66
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8194, 8194, 8199, 8199, 8209, 8209, 8217, 8217, 8222, 8222, 8227, 8227, 8240, 8240, 8245, 8245, 8250, 8250, 8270, 8270, 8280, 8280, 8281, 8281, 8284, 8284, 8314, 8314, 8403, 8403, 8405, 8405, 8432, 8432, 8438, 8438, 8443, 8443, 8452, 8452, 8456, 8456, 8475, 8475, 8478, 8478, 8489, 8489, 8490, 8490, 8588, 8588, 8609, 8609, 19137, 19137, 19138, 19138, 19139, 19139, 19140, 19140, 19141, 19141, 19142, 19142

### `OperationRegistry` (class, 461 lines)

- Def site: line 19374-19834
- References: 9
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19841, 19841, 19845, 19845, 19865, 19865, 19870, 19870, 20092

### `PromptUtils` (class, 441 lines)

- Def site: line 7600-8040
- References: 117
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7545, 7545, 7561, 7561, 7565, 7565, 7566, 7566, 7567, 7567, 7582, 7582, 7588, 7588, 7615, 7615, 7618, 7618, 7626, 7626, 7644, 7644, 7694, 7694, 7702, 7702, 7707, 7707, 7753, 7753, 7764, 7764, 7789, 7789, 7808, 7808, 7809, 7809, 7812, 7812, 7813, 7813, 7903, 7903, 7905, 7905, 7909, 7909, 7937, 7937, 7938, 7938, 7939, 7939, 7940, 7940, 7941, 7941, 7950, 7950, 7994, 7994, 8018, 8018, 12347, 12347, 12397, 12397, 12402, 12402, 12545, 12628, 12628, 12682, 12682, 12703, 12703, 12708, 12708, 12972, 12972, 13175, 13377, 13377, 13464, 13464, 13469, 13469, 13519, 13519, 13520, 13520, 15016, 15016, 15475, 16815, 16815, 17335, 17335, 18475, 18475, 18476, 18476, 18780, 18780
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 23, 68, 196, 196
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 37, 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 17, 65, 127, 127, 132, 132

### `OrgDeviceStatsExporter` (class, 414 lines)

- Def site: line 9569-9982
- References: 58
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5572, 5572, 9602, 9602, 9686, 9686, 9692, 9692, 9695, 9695, 9739, 9739, 9753, 9753, 9780, 9780, 9786, 9786, 9800, 9800, 9883, 9883, 9885, 9885, 9889, 9889, 9891, 9891, 9894, 9894, 9898, 9898, 9901, 9901, 9911, 9911, 9917, 9917, 9955, 9955, 14890, 14890, 14891, 14891, 14892, 14892, 14943, 14943, 14944, 14944, 18610, 18610, 18611, 18611, 18612, 18612, 18636, 18636

### `DeviceRebootManager` (class, 396 lines)

- Def site: line 16918-17313
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16939, 16939, 16944, 16944, 16948, 16948, 16951, 16951, 16958, 16958, 16960, 16960, 16961, 16961, 16964, 16964, 16967, 16967, 16970, 16970, 17012, 17012, 17044, 17044, 17111, 17111, 17124, 17124, 17129, 17129, 17179, 17179, 17212, 17212, 17213, 17213, 17214, 17214, 17244, 17244, 17273, 17273, 17274, 17274, 18811, 18811

### `MSPInventoryExporter` (class, 386 lines)

- Def site: line 17367-17752
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17394, 17538, 17538, 18960, 18960

### `DataExporter` (class, 345 lines)

- Def site: line 6697-7041
- References: 250
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5668, 5668, 6743, 6743, 6759, 6759, 6760, 6760, 6783, 6783, 6785, 6785, 6788, 6788, 6802, 6802, 6804, 6804, 6813, 6813, 6815, 6815, 6816, 6816, 6822, 6822, 6823, 6823, 6823, 6840, 6840, 6844, 6844, 6886, 6886, 6917, 6917, 6920, 6920, 6922, 6922, 6968, 6968, 6978, 6978, 7011, 7011, 7016, 7016, 7023, 7023, 7245, 7245, 7277, 7277, 7288, 7288, 7313, 7313, 7333, 7333, 7657, 7657, 8459, 8459, 8741, 8741, 8756, 8820, 8820, 8837, 8837, 8855, 8855, 8876, 8876, 9435, 9435, 9510, 9510, 9840, 9840, 10191, 10191, 10276, 10292, 10412, 10412, 10416, 10416, 10436, 10436, 10449, 10449, 10453, 10453, 10471, 10471, 10633, 10633, 10981, 10981, 11128, 11128, 11205, 11205, 11209, 11209, 11214, 11214, 11347, 11347, 11366, 11366, 11417, 11417, 11420, 11420, 11571, 11571, 11574, 11574, 11673, 11673, 11679, 11679, 11976, 11976, 11993, 11993, 12008, 12008, 12222, 12222, 12250, 12250, 12266, 12266, 12303, 12303, 12341, 12341, 12430, 12430, 12459, 12459, 12497, 12497, 12548, 12613, 12613, 12619, 12619, 12661, 12661, 12830, 12830, 12836, 12836, 12955, 12955, 12963, 12963, 13127, 13127, 13178, 13351, 13351, 13522, 13522, 14035, 14035, 14396, 14396, 14402, 14402, 15310, 15310, 15369, 15476, 16862, 16862, 16883, 17718, 17718, 17803, 17803, 17824, 17824, 18310, 18310, 18707, 18707, 18720, 18720, 18934, 18934, 18989, 18989, 19005, 19005
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 26, 71, 188, 188, 286, 286, 294, 294, 363, 363, 392, 392, 544, 544, 559, 559
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 39, 53
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 42, 380, 380, 440, 440, 457, 457, 476, 476, 549, 549
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 30, 310, 310, 454, 454
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 21, 639, 639
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_msp.py`: lines 28, 67, 380, 380, 413, 413, 424, 424
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\inventory\org_device_inventory_summary.py`: lines 15, 39, 338, 338

### `SiteAnomalyExporter` (class, 341 lines)

- Def site: line 12669-13009
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12686, 12686, 12688, 12688, 12692, 12692, 12693, 12693, 12707, 12707, 12713, 12713, 12716, 12716, 12719, 12719, 12777, 12777, 12783, 12783, 12788, 12788, 12802, 12802, 12820, 12820, 12930, 12930, 12934, 12934, 12936, 12936, 12939, 12939, 12976, 12976, 12981, 12981, 12995, 12995, 12999, 12999, 13001, 13001, 13004, 13004, 13009, 13009, 18857, 18857, 18861, 18861, 18865, 18865

### `APIDataFetcher` (class, 328 lines)

- Def site: line 7044-7371
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7146, 7146, 8174, 8667, 8686, 8787, 8916, 8939, 9611, 9919, 9964, 10378, 11149, 11160, 11223, 11640

### `InsightMetricsUtils` (class, 328 lines)

- Def site: line 14500-14827
- References: 51
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11957, 11957, 12016, 12016, 12017, 12017, 13181, 14541, 14541, 14543, 14543, 14549, 14549, 14563, 14563, 14602, 14602, 14605, 14605, 14607, 14607, 14608, 14608, 14609, 14609, 14663, 14663, 14664, 14664, 14675, 14675, 14684, 14684, 14703, 14703, 14755, 14755, 14759, 14759, 14767, 14767, 14768, 14768, 14792, 14792, 14796, 14796
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 29, 74
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 41, 55

### `ARPCommandManager` (class, 289 lines)

- Def site: line 15803-16091
- References: 46
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15831, 15831, 15834, 15834, 15839, 15839, 15842, 15842, 15886, 15886, 15892, 15892, 15923, 15923, 15926, 15926, 15930, 15930, 15956, 15956, 15973, 15973, 15979, 15979, 15993, 15993, 15994, 15994, 15996, 15996, 16002, 16002, 16009, 16009, 16018, 16018, 16065, 16065, 16087, 16087, 16088, 16088, 16089, 16089, 18802, 18802

### `OfflineDeviceReporter` (class, 273 lines)

- Def site: line 9985-10257
- References: 54
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10008, 10008, 10009, 10009, 10022, 10022, 10023, 10023, 10025, 10025, 10026, 10026, 10029, 10029, 10032, 10032, 10036, 10036, 10037, 10037, 10113, 10113, 10117, 10117, 10120, 10120, 10133, 10133, 10170, 10170, 10187, 10187, 10200, 10200, 10202, 10202, 10209, 10209, 10218, 10218, 10227, 10227, 10228, 10228, 10239, 10239, 10243, 10243, 10252, 10252, 10257, 10257, 19068, 19068

### `CacheUtils` (class, 264 lines)

- Def site: line 5198-5461
- References: 106
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5238, 5238, 5240, 5240, 5322, 5322, 5328, 5328, 5365, 5365, 5367, 5367, 5376, 5376, 5386, 5386, 5396, 5396, 5432, 5432, 7693, 7693, 9363, 9363, 9364, 9364, 9675, 9675, 10521, 10521, 10541, 10541, 12543, 14949, 14949, 14955, 14955, 14956, 14956, 14957, 14957, 14958, 14958, 14959, 14959, 14960, 14960, 14967, 14967, 14995, 14995, 15367, 15618, 16807, 16807, 16831, 16831, 16855, 16855, 16999, 16999, 17000, 17000, 17001, 17001, 17002, 17002, 17336, 17336, 18526, 18526, 18708, 18708, 18721, 18721, 18935, 18935, 19105, 19105
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 40, 339, 339, 341, 341, 343, 343, 345, 345, 499, 499, 500, 500, 545, 545
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 32, 336, 336, 357, 357
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 16, 191, 191, 192, 192, 195, 195

### `GlobalWiredClientReportGenerator` (class, 251 lines)

- Def site: line 10753-11003
- References: 32
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10760, 10760, 10763, 10763, 10768, 10768, 10769, 10769, 10777, 10777, 10780, 10780, 10788, 10788, 10828, 10828, 10836, 10836, 10884, 10884, 10901, 10901, 10904, 10904, 10906, 10906, 10970, 10970, 10971, 10971, 19071, 19071

### `GatewayTestExporter` (class, 245 lines)

- Def site: line 15079-15323
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14945, 14945, 15105, 15105, 15107, 15107, 15108, 15108, 15109, 15109, 15137, 15137, 15142, 15142, 15164, 15164, 15165, 15165, 15207, 15207, 15215, 15215, 15241, 15241, 15250, 15250, 15258, 15258, 15289, 15289, 18615, 18615, 18619, 18619

### `APIFetchUtils` (class, 221 lines)

- Def site: line 6120-6340
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6143, 6143, 6194, 6194, 6264, 6264, 6288, 6288, 6300, 6300, 6302, 6302, 6312, 6312, 6327, 6327, 6331, 6331, 6332, 6332, 6335, 6335, 6337, 6337, 12656, 12656, 15371
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 44, 450, 450
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 13, 43, 108, 108
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 25, 71

### `TelemetryEmitter` (class, 214 lines)

- Def site: line 19155-19368
- References: 5
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 20011, 20011, 20014, 20093, 20444

### `PromptClientUtils` (class, 210 lines)

- Def site: line 7384-7593
- References: 31
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7397, 7397, 7403, 7403, 7404, 7404, 7407, 7407, 7430, 7430, 7433, 7433, 7436, 7436, 7437, 7437, 7439, 7439, 7506, 7506, 7550, 7550, 8015, 8015, 12977, 12977, 15474, 15656, 15656, 15816, 15816

### `SiteDeviceExporter` (class, 203 lines)

- Def site: line 12275-12477
- References: 30
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12296, 12296, 12305, 12305, 12367, 12367, 12374, 12374, 12406, 12406, 12408, 12408, 12432, 12432, 12467, 12467, 12474, 12474, 12505, 12505, 15019, 15019, 18651, 18651, 18653, 18653, 18654, 18654, 18656, 18656

### `DeviceUtilityCommands` (class, 188 lines)

- Def site: line 13528-13715
- References: 70
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 19028, 19028, 19029, 19029, 19030, 19030, 19031, 19031, 19032, 19032, 19033, 19033, 19034, 19034, 19035, 19035, 19037, 19037, 19038, 19038, 19039, 19039, 19040, 19040, 19041, 19041, 19042, 19042, 19043, 19043, 19045, 19045, 19046, 19046, 19047, 19047, 19048, 19048, 19049, 19049, 19050, 19050, 19051, 19051, 19052, 19052, 19053, 19053, 19055, 19055, 19056, 19056, 19057, 19057, 19058, 19058, 19059, 19059, 19060, 19060, 19061, 19061, 19062, 19062, 19063, 19063, 19065, 19065, 19066, 19066

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5631, 5631, 5668, 5668, 5670, 5670, 5673, 5673, 5681, 5681, 5683, 5683, 5685, 5685, 5688, 5688, 5717, 5717, 5720, 5720, 18796, 18796

### `DatabaseSchemaUtils` (class, 179 lines)

- Def site: line 6516-6694
- References: 34
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6561, 6561, 6599, 6599, 6610, 6610, 6636, 6636, 6637, 6637, 6639, 6639, 6645, 6645, 6646, 6646, 6649, 6649, 6655, 6655, 6656, 6656, 6659, 6659, 6661, 6661, 6671, 6671, 6673, 6673, 6674, 6674, 6676, 6676

### `LicenseExportUtils` (class, 168 lines)

- Def site: line 11233-11400
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11340, 11340, 11359, 11359, 11377, 11377, 11386, 11386, 11389, 11389, 11390, 11390, 11393, 11393, 11398, 11398, 11400, 11400, 18679, 18679

### `OrgConfigExporter` (class, 168 lines)

- Def site: line 11445-11612
- References: 24
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11482, 11482, 11484, 11484, 11487, 11487, 11558, 11558, 11560, 11560, 11573, 11573, 11577, 11577, 18682, 18682, 18683, 18683, 18684, 18684, 18740, 18740, 18745, 18745

### `OrgClientSecurityExporter` (class, 162 lines)

- Def site: line 10477-10638
- References: 26
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10515, 10515, 10522, 10522, 10529, 10529, 10535, 10535, 10542, 10542, 10549, 10549, 10610, 10610, 10621, 10621, 18670, 18670, 18671, 18671, 18673, 18673, 18674, 18674, 18675, 18675

### `CLIShellManager` (class, 161 lines)

- Def site: line 15637-15797
- References: 23
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15660, 15660, 15662, 15662, 15731, 15731, 15733, 15733, 15752, 15752, 15754, 15754, 15754, 15770, 15770, 15786, 15786, 15787, 15787, 15793, 15793, 18801, 18801

### `DataProcessingUtils` (class, 158 lines)

- Def site: line 6348-6505
- References: 197
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5496, 5496, 6364, 6364, 6377, 6377, 6380, 6380, 6404, 6404, 6412, 6412, 6413, 6413, 6435, 6435, 6440, 6440, 6442, 6442, 6919, 6919, 6944, 6944, 7013, 7013, 7014, 7014, 7343, 7343, 7357, 7357, 7358, 7358, 7655, 7655, 7656, 7656, 8590, 8590, 8755, 8815, 8815, 8817, 8817, 8818, 8818, 8835, 8835, 8836, 8836, 8853, 8853, 8854, 8854, 8874, 8874, 8875, 8875, 9432, 9432, 9433, 9433, 9507, 9507, 9508, 9508, 9836, 9836, 9839, 9839, 10414, 10414, 10415, 10415, 10451, 10451, 10452, 10452, 10631, 10631, 10632, 10632, 10977, 10977, 10978, 10978, 11124, 11124, 11125, 11125, 11207, 11207, 11208, 11208, 11419, 11419, 11594, 11594, 11595, 11595, 11671, 11671, 11672, 11672, 11975, 11975, 11991, 11991, 11992, 11992, 12220, 12220, 12221, 12221, 12300, 12300, 12301, 12301, 12302, 12302, 12338, 12338, 12339, 12339, 12427, 12427, 12428, 12428, 12456, 12456, 12457, 12457, 12494, 12494, 12495, 12495, 12547, 12616, 12616, 12617, 12617, 12659, 12659, 12660, 12660, 12828, 12828, 12829, 12829, 12953, 12953, 12954, 12954, 13177, 13349, 13349, 14401, 14401, 15308, 15308, 15309, 15309, 15370, 15478, 16860, 16860, 16861, 16861, 17708, 17708
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 25, 70, 153, 153, 154, 154, 159, 159, 187, 187, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_insights_exporter.py`: lines 38, 52
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 43, 454, 454, 455, 455, 474, 474, 475, 475
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 29, 274, 274

### `DataCollectionManager` (class, 156 lines)

- Def site: line 14841-14996
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 14863, 14863, 14869, 14869, 14871, 14871, 14899, 14899, 14925, 14925, 14928, 14928, 14931, 14931, 18787, 18787, 18791, 18791, 18799, 18799

### `SitesByAPModelExporter` (class, 146 lines)

- Def site: line 13012-13157
- References: 22
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13051, 13051, 13058, 13058, 13083, 13083, 13086, 13086, 13099, 13099, 13143, 13143, 13147, 13147, 13152, 13152, 13153, 13153, 13157, 13157, 19103, 19103

### `SiteExportUtils` (class, 145 lines)

- Def site: line 13165-13309
- References: 94
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12386, 12386, 12562, 12562, 12640, 12640, 12645, 12645, 13194, 13194, 13200, 13200, 13206, 13206, 13212, 13212, 13218, 13218, 13224, 13224, 13230, 13230, 13236, 13236, 13242, 13242, 13248, 13248, 13254, 13254, 13260, 13260, 13266, 13266, 13272, 13272, 13278, 13278, 13284, 13284, 13290, 13290, 13296, 13296, 13302, 13302, 13308, 13308, 18689, 18689, 18848, 18848, 18850, 18850, 18974, 18974, 19100, 19100, 19101, 19101, 19102, 19102, 19121, 19121, 19122, 19122, 19123, 19123, 19124, 19124, 19125, 19125, 19126, 19126, 19127, 19127
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 209, 209, 352, 352, 356, 356, 366, 366, 415, 415, 424, 424, 433, 433, 497, 497, 525, 525

### `OrgTemplateExporter` (class, 144 lines)

- Def site: line 10331-10474
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10345, 10345, 10346, 10346, 10432, 10432, 10467, 10467, 18664, 18664, 18665, 18665, 18666, 18666, 18667, 18667, 18668, 18668

### `GatewayHaExporter` (class, 139 lines)

- Def site: line 13312-13450
- References: 18
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13381, 13381, 13384, 13384, 13385, 13385, 13386, 13386, 13406, 13406, 13409, 13409, 13417, 13417, 13422, 13422, 19129, 19129

### `OrgAlarmEventExporter` (class, 129 lines)

- Def site: line 8633-8761
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8704, 8704, 8715, 8715, 14939, 14939, 14940, 14940, 18567, 18567, 18568, 18568, 18765, 18765

### `WiredClientManufacturerReportGenerator` (class, 129 lines)

- Def site: line 11006-11134
- References: 20
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11013, 11013, 11018, 11018, 11019, 11019, 11020, 11020, 11023, 11023, 11024, 11024, 11087, 11087, 11094, 11094, 11121, 11121, 19073, 19073

### `TroubleshootUtils` (class, 127 lines)

- Def site: line 15464-15590
- References: 36
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15484, 15484, 15489, 15489, 15494, 15494, 15531, 15531, 15537, 15537, 15543, 15543, 15549, 15549, 15555, 15555, 15556, 15556, 15557, 15557, 15558, 15558, 15559, 15559, 15563, 15563, 15572, 15572, 15576, 15576, 15579, 15579, 15585, 15585, 18760, 18760

### `EnvironmentUtils` (class, 114 lines)

- Def site: line 5776-5889
- References: 28
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5797, 5797, 5799, 5799, 5815, 5815, 5827, 5827, 5866, 5866, 5867, 5867, 5868, 5868, 5869, 5869, 5870, 5870, 5881, 5881, 5884, 5884, 6801, 6801, 20106, 20106, 20689, 20689

### `OrgSiteExporter` (class, 112 lines)

- Def site: line 8767-8878
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 7693, 7693, 9363, 9363, 9675, 9675, 10521, 10521, 10541, 10541, 12544, 14888, 14888, 14941, 14941, 15374, 16809, 16809, 16833, 16833, 16857, 16857, 17000, 17000, 17339, 17339, 18608, 18608, 18623, 18623, 18633, 18633, 18633, 18633, 18643, 18643, 18709, 18709, 18722, 18722, 18936, 18936
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 47, 339, 339, 500, 500, 547, 547
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 17, 191, 191

### `FilterOperatorEngine` (class, 110 lines)

- Def site: line 10641-10750
- References: 37
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10696, 10696, 10699, 10699, 10700, 10700, 10705, 10705, 10724, 10724, 10724, 10733, 10733, 10733, 10733, 10734, 10734, 10734, 10734, 10792, 10792, 10795, 10795, 10807, 10807, 10808, 10808, 10821, 10821, 10860, 10860, 10868, 10868, 10922, 10922, 10930, 10930

### `SiteConfigExporter` (class, 100 lines)

- Def site: line 12567-12666
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12632, 12632, 12634, 12634, 12635, 12635, 18617, 18617, 18685, 18685, 18687, 18687, 18688, 18688

### `GatewayExportUtils` (class, 98 lines)

- Def site: line 15356-15453
- References: 78
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15099, 15099, 15334, 15334, 15392, 15392, 15398, 15398, 15404, 15404, 15410, 15410, 15416, 15416, 15422, 15422, 15428, 15428, 15434, 15434, 15440, 15440, 15446, 15446, 15452, 15452, 15619, 17001, 17001, 17004, 17004, 17338, 17338, 18574, 18574, 18641, 18641, 18647, 18647, 18698, 18698, 18773, 18773
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 78, 94, 341, 341, 347, 347, 403, 403, 405, 405, 409, 409, 412, 412, 415, 415, 416, 416, 459, 459, 460, 460, 492, 492, 493, 493, 509, 509, 546, 546
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 18, 193, 193, 196, 196

### `DeviceUtils` (class, 97 lines)

- Def site: line 8051-8147
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8107, 8107, 8143, 8143

### `OrgAdminExporter` (class, 94 lines)

- Def site: line 11137-11230
- References: 14
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] hardcoded_separator
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11189, 11189, 11202, 11202, 18677, 18677, 18737, 18737, 18738, 18738, 18743, 18743, 18744, 18744

### `ValidationUtils` (class, 90 lines)

- Def site: line 5895-5984
- References: 15
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5977, 5977, 15162, 15162, 15163, 15163, 15377, 18477, 18477
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 51
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 28, 143, 143, 144, 144

### `SiteClientExporter` (class, 85 lines)

- Def site: line 12480-12564
- References: 10
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 12514, 12514, 18652, 18652, 18660, 18660, 18686, 18686, 18849, 18849

### `OrgLevelAPFirmwareUpgrader` (class, 79 lines)

- Def site: line 17779-17857
- References: 33
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 17774, 17774, 17775, 17775, 18953, 18953
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\org_ap_upgrader.py`: lines 412, 409, 425, 770, 770, 772, 772, 781, 781, 786, 786, 790, 790, 846, 846, 847, 847, 848, 848, 849, 849, 883, 883, 2223, 2223, 2226, 2226

### `VirtualChassisManager` (class, 78 lines)

- Def site: line 16787-16864
- References: 104
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18815, 18815, 18819, 18819, 18823, 18823
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1917, 1917, 1949, 1949, 2294, 2294, 2321, 2321, 7405, 7405, 7491, 7491, 7621, 7621, 7698, 7698, 7781, 7781, 8011, 8011, 8200, 8200, 8259, 8259, 8272, 8272, 8289, 8289, 8334, 8334, 8368, 8368, 8374, 8374, 8480, 8480, 10024, 10024, 10291, 10794, 10794, 10823, 10823, 11088, 11088, 11294, 11294, 11533, 11533, 12249, 12249, 12265, 12265, 13052, 13052, 13471, 13471, 13521, 13521, 15375, 15577, 15577, 15617, 16814, 16814, 16839, 16839, 16882, 16981, 16981, 17191, 17191, 17334, 17334, 17441, 17441, 17769, 17769, 17799, 17799, 17820, 17820, 17839, 17839, 17855, 17855, 18433, 18433, 18453, 18453, 18479, 18479, 18492, 18492, 18705, 18705, 18718, 18718, 18932, 18932, 18987, 18987, 19078, 19078, 19083, 19083, 19089, 19089, 19108, 19108, 19114, 19114, 20712, 20712
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

- Def site: line 15002-15073
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18781, 18781, 18782, 18782, 18783, 18783, 18784, 18784

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

- Def site: line 5990-6059
- References: 182
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6032, 6032, 6037, 6037, 6134, 6134, 6192, 6192, 7079, 7079, 7548, 7548, 8193, 8193, 8216, 8216, 8239, 8239, 8430, 8430, 8451, 8451, 8729, 8729, 8754, 8754, 8809, 8809, 8831, 8831, 8848, 8848, 8865, 8865, 9250, 9250, 9473, 9473, 9490, 9490, 9882, 9882, 10214, 10214, 10425, 10425, 10462, 10462, 10615, 10615, 10759, 10759, 11012, 11012, 11200, 11200, 11384, 11384, 11703, 11703, 12039, 12039, 12211, 12211, 12251, 12251, 12257, 12257, 12351, 12351, 12581, 12581, 12654, 12654, 13141, 13141, 13176, 13375, 13375, 14882, 14882, 15098, 15098, 15366, 15473, 15573, 15573, 16880, 17770, 17770, 17772, 17772, 17796, 17796, 17800, 17800, 17801, 17801, 17821, 17821, 17822, 17822, 17967, 17967, 18528, 18528, 18560, 18560, 18597, 18597, 18603, 18603, 18703, 18703, 18716, 18716, 18749, 18749, 18806, 18806, 18889, 18889, 18898, 18898, 18930, 18930, 18985, 18985, 18986, 18986, 19003, 19003, 19078, 19078, 19083, 19083, 19089, 19089, 19108, 19108, 19114, 19114, 20025, 20025, 20094, 20576, 20576, 20664, 20664
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 24, 69, 246, 246, 556, 556, 557, 557
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 39, 402, 402, 449, 449, 467, 467, 508, 508, 542, 542
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 27, 321, 321
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 15, 150, 150, 510, 510
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_discovery.py`: lines 12, 42, 86, 86
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\websocket\service_ping_manager.py`: lines 24, 70

### `OrgDeviceInventorySummary` (class, 69 lines)

- Def site: line 10260-10328
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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 10300, 10300, 10305, 10305, 10310, 10310, 10311, 10311, 10317, 10317, 10318, 10318, 10324, 10324, 10325, 10325, 10326, 10326, 10327, 10327, 19131, 19131

### `AuditAnalysisOps` (class, 66 lines)

- Def site: line 18483-18548
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] raw_input_call
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18531, 18531, 18539, 18539, 18548, 18548, 19104, 19104

### `APICoreFetchUtils` (class, 47 lines)

- Def site: line 6065-6111
- References: 55
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 6189, 6189, 7883, 7883, 8810, 8810, 8833, 8833, 9320, 9320, 9355, 9355, 9369, 9369, 9492, 9492, 9496, 9496, 10044, 10044, 12355, 12355, 13025, 13025, 13151, 13151, 13183, 13361, 13361, 13397, 13397, 15372, 17660, 17660, 17771, 17771, 17802, 17802, 17823, 17823, 18988, 18988, 19004, 19004, 20595, 20595
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 31, 76, 558, 558
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 45, 515, 515, 526, 526

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 5237, 5237, 5279, 5279, 5324, 5324, 5430, 5430, 5445, 5445, 5715, 5715, 5716, 5716, 5760, 5760, 6215, 6215, 7717, 7717, 9020, 9020, 9331, 9331, 9347, 9347, 9676, 9676, 10557, 10557, 10576, 10576, 12546, 14965, 14965, 15368, 15620, 16042, 16042, 16082, 16082, 16083, 16083, 16084, 16084, 16806, 16806, 16830, 16830, 16834, 16834, 16854, 16854, 16881, 16956, 16956, 16990, 16990, 17011, 17011, 17043, 17043, 17105, 17105, 17144, 17144, 17292, 17292, 17337, 17337, 18706, 18706, 18719, 18719, 18933, 18933
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 41, 149, 149, 227, 227, 235, 235, 243, 243, 548, 548
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 33, 360, 360
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\wan2_migration_manager.py`: lines 19, 198, 198, 341, 341, 347, 347

### `SiteConfigManager` (class, 43 lines)

- Def site: line 16870-16912
- References: 16
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 16893, 16893, 16899, 16899, 16905, 16905, 16911, 16911, 18913, 18913, 18917, 18917, 18921, 18921, 18925, 18925

### `SelfExportUtils` (class, 40 lines)

- Def site: line 11403-11442
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] non_ascii_logs
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 11440, 11440, 19128, 19128

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
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 8683, 8683, 8684, 8684, 8713, 8713, 8714, 8714, 8730, 8730, 8731, 8731, 9609, 9609, 9610, 9610, 9914, 9914, 9915, 9915, 9962, 9962, 9963, 9963, 10518, 10518, 10520, 10520, 10538, 10538, 10540, 10540, 11429, 11429, 11430, 11430, 12090, 12090, 12091, 12091, 12196, 12196, 12197, 12197, 13179
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\export\site_export_utils.py`: lines 27, 72, 207, 207, 208, 208

### `GatewayStatsExporter` (class, 28 lines)

- Def site: line 15326-15353
- References: 52
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15340, 15340, 15346, 15346, 15352, 15352, 18827, 18827, 18831, 18831
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_stats_exporter.py`: lines 203, 203, 247, 247, 250, 250, 266, 266, 308, 308, 311, 311, 327, 327, 329, 329, 330, 330, 337, 337, 347, 347, 350, 350, 351, 351, 358, 358, 377, 377, 386, 386, 387, 387, 388, 388, 405, 405, 406, 406, 459, 459

### `SSHRunnerManager` (class, 26 lines)

- Def site: line 15606-15631
- References: 82
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15626, 15626, 15631, 15631, 18835, 18835, 18840, 18840
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\ssh\ssh_runner_manager.py`: lines 61, 61, 62, 62, 64, 64, 68, 68, 73, 73, 86, 86, 87, 87, 96, 96, 97, 97, 129, 129, 130, 130, 131, 131, 136, 136, 137, 137, 139, 139, 162, 162, 165, 165, 168, 168, 189, 189, 193, 193, 209, 209, 210, 210, 211, 211, 278, 278, 280, 280, 281, 281, 327, 327, 369, 369, 373, 373, 382, 382, 400, 400, 416, 416, 438, 438, 495, 495, 499, 499, 500, 500, 503, 503

### `RoutingUtils` (class, 22 lines)

- Def site: line 13478-13499
- References: 12
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18583, 18583, 18587, 18587, 18591, 18591
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_display.py`: lines 106
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_forwarding.py`: lines 46
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_parsing.py`: lines 67
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_payload.py`: lines 85
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_routing.py`: lines 50
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\network\_routing_utils_ssr.py`: lines 36

### `FirmwareManager` (class, 22 lines)

- Def site: line 17320-17341
- References: 8
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18748, 18748, 18805, 18805, 18888, 18888, 18897, 18897

### `SiteAutoUpgradeConfigurator` (class, 22 lines)

- Def site: line 17755-17776
- References: 6
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 18967, 18967
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\firmware\site_auto_upgrade.py`: lines 177, 177, 742, 964

### `EndpointConfig` (class, 10 lines)

- Def site: line 13724-13733
- References: 13
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 13760, 13896, 13973, 13992, 14004, 14025, 14038, 14049, 14055, 14068, 14161, 14296, 14391

### `SSHConnectionConfig` (class, 9 lines)

- Def site: line 328-336
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

- Def site: line 355-363
- References: 4
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 15034, 15051, 15067
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\refactors\device_data_fetcher.py`: lines 49

### `SSHExecutionConfig` (class, 8 lines)

- Def site: line 340-347
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

- Def site: line 635-637
- References: 43
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1245, 1914, 1914, 1914, 1926, 1932, 6191, 6311, 7367, 9419, 9530, 9784, 10614, 13186, 15244, 15286, 15384, 18990
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

- Def site: line 2030-2032
- References: 11
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 2030, 15380
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\gateway\gateway_export_utils.py`: lines 54, 544
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
