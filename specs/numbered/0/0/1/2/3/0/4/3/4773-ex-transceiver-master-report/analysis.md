# Specification Analysis Report: EX Transceiver Master Report

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the design files under `design/`, and the code, tests, and documents on GitHub `main` (commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`).

## Findings

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| A-01 | High | The CLI reads only XML. `OrganizationBatchRun.REQUEST` fixes the format to `xml` (`run/batch.py` line 176). `RunFolder._xml` reads only `.xml` files (`run/watch.py` line 141). A JSON-only run would show every switch as a missing reply. | Fixed by T009 and T010. |
| A-02 | High | `FailureReasons.exact` reads only the `xml` entry (`report/builder.py` line 79). A JSON failure would lose its exact reason. | Fixed by T004. |
| A-03 | High | Two existing tests assert exact values that the change alters. `test_ws_web_services.py` line 662 compares the exact preview dict. `test_ws_hardware_csv.py` line 410 compares the exact download error text. | Updated by T018 and T021. |
| A-04 | High | Menu count pins fail after a new menu row. `test_menu_entry_metadata.py` line 10 expects 309. `test_endpoint_catalog.py` line 547 pins the file identity. | Updated by T016. |
| A-05 | Medium | The format choices of `HardwareXmlPreset.COMMAND_FORMATS` (line 310) include `json` and `both`, but `HardwareConsole.confirm` prints only the XML command (`console.py` line 87). The confirmation would hide the JSON command. | Fixed by T011. |
| A-06 | Medium | `ReportDownload` builds every file name with the prefix `ExHardwareInventory_` (`artifacts.py` line 871). A transceiver download under that prefix would mislead the operator. | Fixed by T020 with a prefix argument. |
| A-07 | Medium | The portal summary sets report names from `reportsOfFormat` (`websockets.js` line 960), and that list has no transceiver name. The link would never appear. | Fixed by T023. |
| A-08 | Medium | `MistHelper.py` is a hot file. The issue asks for coordination before a change. The blocker in the issue body names PR #4607. PR #4607 merged on 2026-11-13 at 07:14:03 UTC. No open pull request changes `MistHelper.py` on 2026-11-26. | The blocker is resolved. T014 proceeds, and T-MERGE checks the merge. |
| A-09 | Medium | The four worktree commits in the issue comment do not exist on GitHub. The REST lookups return HTTP 422 for `8140bb3`, `58ab484`, `07cf3ee`, and `edc12d5`. | The evidence is local only. D-17 reimplements the feature on a new branch. The worktree stays unchanged. |
| A-10 | Low | `README.md` has no operation count and no menu table. `.github/copilot-instructions.md` tells the agent to update both in `README.md`. | D-15 adds one row to the task table. The instruction file wording stays unchanged in this change. |
| A-11 | Low | The local checkout differs from `main` for `.gitignore` and for `.specify/scripts/powershell/spec-route.ps1`. The blob hashes do not match. | This record uses the remote line numbers for both files. The local copy stays unchanged. |
| A-12 | Low | The module note in `src/mist/intelligence/reports/sfp_transceiver_data_processor.py` line 1 names menu 77. `MistHelper.py` registers the same class at menu 100 (line 5313). | Out of scope. The change does not edit the SFP processor. |
| A-13 | Low | Open draft pull request #4813 changes `src/operations/exporting/export/data_exporter.py` and CSV carriage-return handling. The transceiver CSV uses that path. | Risk R-4 in `plan.md`. The branch rebases after #4813 lands, and the CSV tests run again. |
| A-14 | Low | The test-quality baseline reports two existing findings that issue #4783 tracks. The new tests might add findings. | T032 requires zero new findings. The baseline does not change. |
| A-15 | Low | The `ste-linter` gate names `CLAUDE.md`. The file exists on `main` (remote row R94). | No action. |

## Consistency Review

### Spec to Plan

- Each of the 31 requirements appears in the plan change map or in the constitution check. The coverage table below proves it.
- The plan names the same menu number (310), the same key (`ExTransceiverMaster`), and the same file name (`hardware/transceiver-master.csv`) as the spec.
- The plan names the same four user-story paths and the same portal test identifier as the spec.

### Plan to Tasks

- Each file in the plan change map appears in at least one task. The tasks T003 to T034 cover the whole map.
- Each task names one verification command from the local gates table. The final task T-LOCAL-GATES lists each gate.
- The plan's implementation outline names T003 to T027, then T028 to T034 and the four final tasks. The tasks file uses the same ranges.

### Spec and Plan to Remote Code

- The remote tree confirms every existing path that the spec, plan, or tasks cite. Remote rows R01 through R149 in `design/research.md` record each check.
- Each symbol line cited in the plan matches the remote line. Two files differ locally (A-11), and the plan uses the remote line for each.
- The Mist claims cite the local OpenAPI file, as the brief requires. The SDK claims cite the installed `mistapi` 0.64.1 source file under `.venv`.

### Consistency Gaps Closed in This Review

- The plan first named an unverified line 9 for the Python requirement. The line reference is removed, and the plan names the section instead.
- The plan first used the words "Warning" for a recoverable effect. That line is now a Caution.
- The plan first used placeholder task names (T-COMMENTS, T-SECURITY, T-DOCS). Those names are replaced by T029, T031, and T024 to T027.
- The task list first cited a line for a method that starts on a different line. The task now cites the line of the reference it changes.

## Coverage Summary

Each requirement maps to at least one task and at least one test case (TC numbers below).

| Requirement | Tasks | Test cases |
|-------------|-------|------------|
| FR-001 | T013, T014, T024 | TC-20, TC-23 |
| FR-002 | T022, T024 | TC-32 |
| FR-003 | T011, T028 | TC-19 |
| FR-004 | T011, T012 | TC-19, TC-21 |
| FR-005 | T010, T011, T013, T017 | TC-17, TC-19, TC-20 |
| FR-006 | T009, T020 | TC-18, TC-30 |
| FR-007 | T006 | TC-07 |
| FR-008 | T006 | TC-07 |
| FR-009 | T006, T017 | TC-08, TC-24 |
| FR-010 | T005, T006 | TC-05, TC-06, TC-37 |
| FR-011 | T004, T006, T009, T017 | TC-02, TC-11, TC-24 |
| FR-012 | T005, T017 | TC-04, TC-24 |
| FR-013 | T006 | TC-09 |
| FR-014 | T004, T006 | TC-03, TC-10 |
| FR-015 | T006 | TC-10 |
| FR-016 | T013, T017 | TC-25 |
| FR-017 | T006, T007, T031 | TC-13 |
| FR-018 | T007 | TC-12, TC-14 |
| FR-019 | T008 | TC-15, TC-16 |
| FR-020 | T019, T020, T023 | TC-28, TC-29, TC-34 |
| FR-021 | T018, T019, T023 | TC-26, TC-27, TC-28, TC-33 |
| FR-022 | T022, T023 | TC-32 |
| FR-023 | T020, T021 | TC-31 |
| FR-024 | T013, T029 | TC-22 |
| FR-025 | T008, T023 | TC-15, TC-35 |
| FR-026 | T013 | TC-20, TC-21 |
| FR-027 | T014, T015, T016, T025, T026 | TC-23 |
| FR-028 | T003 | TC-01 |
| FR-029 | T002, T011, T012, T016, T030 | TC-19, TC-36 |
| FR-030 | T018, T020 | TC-26, TC-30 |
| FR-031 | T031, T034 | TC-37 |

Each success criterion maps to at least one test or to a task.

| Success criterion | Evidence |
|-------------------|----------|
| SC-001 | TC-24 |
| SC-002 | TC-08 |
| SC-003 | TC-10, TC-25 |
| SC-004 | TC-13 |
| SC-005 | TC-30 |
| SC-006 | TC-32, TC-33 |
| SC-007 | T034 (operator-run live check, not an automated test) |
| SC-008 | T-LOCAL-GATES |

## Planned Test Cases

The planned test cases total 37. Each case appends to an existing test module. No new test module or test folder is created.

| TC | Module (appended) | Case | Task | Requirement |
|----|-------------------|------|------|-------------|
| TC-01 | `tests/unit/export/test_pk_strategies.py` | `ExTransceiverMaster` is a composite key on org_id, device_id, and item_path | T003 | FR-028 |
| TC-02 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | A completed target with a JSON reply only classifies as collected | T004 | FR-011, FR-012 |
| TC-03 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | `FailureReasons.exact` names the JSON failure, and the menu 309 XML path is unchanged | T004 | FR-014, FR-029 |
| TC-04 | `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` | The JSON reader and the XML walker give equal identity fields for one synthetic switch | T005 | FR-012 |
| TC-05 | `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` | The JSON reader refuses malformed JSON and non-finite numbers with one documented error | T005 | FR-010 |
| TC-06 | `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` | Empty leaves stay empty for both the `data` form and the empty-object form | T005 | FR-010 |
| TC-07 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | One transceiver row per transceiver item, with its module location | T006 | FR-007, FR-008 |
| TC-08 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | Duplicate hostnames and virtual-chassis members keep separate rows | T006 | FR-009 |
| TC-09 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | A collected switch with no transceiver item gets one no-transceiver row | T006 | FR-013 |
| TC-10 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | Failed, skipped, canceled, and unread-organization outcomes carry a plain reason | T006 | FR-014, FR-015 |
| TC-11 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | A both-format target uses the XML rows and adds no JSON rows | T006 | FR-011 |
| TC-12 | `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py` | The transceiver CSV renders UTF-8 with one header and passes the file check | T007 | FR-018 |
| TC-13 | `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py` | A text cell that starts with a formula character gains an apostrophe | T007 | FR-017 |
| TC-14 | `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py` | A report above 64 MiB is refused and returns no file | T007 | FR-018 |
| TC-15 | `tests/unit/ex_hardware_inventory/report/test_hardware_export.py` | The CLI exporter forces the CSV format and writes a UTC name under the data folder | T008 | FR-019, FR-025 |
| TC-16 | `tests/unit/ex_hardware_inventory/report/test_hardware_export.py` | The exporter never overwrites a file and removes a file that fails the read-back | T008 | FR-019 |
| TC-17 | `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` | The batch request carries `json` or `both` when the operator chose it | T010 | FR-005 |
| TC-18 | `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` | The native reader returns JSON text inside the run folder and refuses a path outside it | T009 | FR-006 |
| TC-19 | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | The confirmation prints one command for menu 309 and two for both formats | T011 | FR-003, FR-005, FR-029 |
| TC-20 | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | The menu 310 format prompt defaults to XML and cancels on any other answer | T013 | FR-001, FR-005, FR-026 |
| TC-21 | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | End of input and an interrupt cancel before any shell opens and write no file | T013 | FR-004, FR-026 |
| TC-22 | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | The new log lines are ASCII and carry no secret | T013 | FR-024 |
| TC-23 | `tests/unit/test_menu_entry_metadata.py` | Menu 310 is registered as non-destructive, and the expected count is 310 | T016 | FR-027 |
| TC-24 | `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` | XML, JSON, and both runs write equal transceiver rows and no duplicates | T017 | FR-009, FR-011, FR-012 |
| TC-25 | `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` | A partial run keeps the rows of collected switches and marks the others | T017 | FR-016 |
| TC-26 | `tests/unit/websocket_streams/web/test_ws_web_services.py` | The preview values include `transceiver_csv`, and the exact dict matches | T018 | FR-021, FR-030 |
| TC-27 | `tests/unit/websocket_streams/web/test_ws_web_services.py` | The parser refuses a non-boolean `transceiver_csv` and defaults it to false | T018 | FR-021 |
| TC-28 | `tests/unit/websocket_streams/web/test_ws_web_services.py` | The start output and the summary payload carry `transceiver_csv` beside `format` | T019 | FR-020, FR-021 |
| TC-29 | `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` | A completed run with the checkbox on publishes the file, lists it, and zips it | T020 | FR-020 |
| TC-30 | `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` | A run with the checkbox off publishes no transceiver file and keeps the other outputs | T020 | FR-006, FR-030 |
| TC-31 | `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` | `format=transceiver-csv` returns `text/csv` with the `ExTransceiverMaster_` name | T021 | FR-023 |
| TC-32 | `tests/e2e/websockets_tab/test_websockets_page.py` | The checkbox carries the stable identifier and is unchecked by default | T022 | FR-002, FR-022 |
| TC-33 | `tests/e2e/websockets_tab/test_websockets_page.py` | A checkbox change invalidates the preview and disables start | T023 | FR-021 |
| TC-34 | `tests/e2e/websockets_tab/test_websockets_page.py` | The transceiver download link appears only after publication | T023 | FR-020 |
| TC-35 | `tests/e2e/websockets_tab/test_websockets_page.py` | Failure screenshots and traces save under `test-artifacts/` | T023 | FR-025 |
| TC-36 | `tests/guardrails/test_endpoint_catalog.py` | The `MistHelper.py` identity pin matches the edited file | T016 | FR-029 |
| TC-37 | `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | The fixture replies use only synthetic serial numbers and names | T031 | FR-031 |

## Unresolved Items

These items need evidence that the repository cannot provide. Each item stays open until its named task supplies the evidence. Detail appears in `design/research.md` under Unverified.

- U-1: The live element type and name of a transceiver item. Task T034 captures them.
- U-2: Whether a live transceiver reply holds `model-number`. Task T034 captures it.
- U-3: Whether every target release accepts the `detail` option. Task T034 records the release of the lab switch.
- U-4: The JSON form of an empty leaf in live output. Task T034 captures one example.
- U-5: The content of the four worktree commits. These commits are absent on GitHub, and this review does not inspect the local worktree.
- U-6: The counts in the issue comment, which name 63 rows from 15 switches. Task T034 gives new counts.

## Metrics

| Metric | Value |
|--------|-------|
| Functional requirements | 31 |
| Success criteria | 8 |
| Tasks, including final tasks | 38 |
| Planned test cases | 37 |
| Remote verification rows | 149 |
| Decisions | 18 |
| Decisions that need a human | 0 |
| Findings with High severity | 4 |
