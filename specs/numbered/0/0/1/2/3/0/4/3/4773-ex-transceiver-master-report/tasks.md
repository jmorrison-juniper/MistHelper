# Tasks: EX Transceiver Master Report

**Input**: Design documents in `specs/numbered/0/0/1/2/3/0/4/3/4773-ex-transceiver-master-report/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`.

**Tests**: The specification and the constitution require tests. Write each test case before its implementation. Watch it fail first. Use synthetic replies and fake shells for every automated check. The live check is read-only and runs on one organization.

**Ownership**: Do not modify `.specify/feature.json`, `CHANGELOG.md`, or any file in `specs/` on the feature branch. Add files by explicit path.

**Environment**: Run Python from the `.venv` of the feature worktree. Use the gate commands from `.github/copilot-instructions.md`.

## Status Legend

- `absent`: `main` does not hold the change. The task is not started.
- `verified-present`: `main` already holds the behavior. The task checks it.
- `partial`: `main` holds part of the change.
- `open`: a human or a live system must act. The agent cannot finish the task alone.

## Format

- **[P]**: The task can run in parallel with other [P] tasks of its phase, because it edits different files.
- **Requirements**: The requirement IDs from `spec.md` that the task serves.
- **Paths**: The exact repository paths that the task edits or reads.
- **Acceptance**: The observable result that ends the task.
- **Verification**: One command from the local gates table.

## Phase 1: Setup and Baseline

- [ ] T001 Create a dedicated worktree for the branch `feat/4773-ex-transceiver-master-report` from `origin/main`.
  - **Requirements**: All.
  - **Paths**: The new worktree folder outside the shared checkout. The shared checkout stays unchanged.
  - **Acceptance**: The worktree is clean, and its head commit equals `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
  - **Verification**: `python -m pytest tests/guardrails`
  - **Status**: absent

- [ ] T002 Record the baseline of the affected tests on the untouched worktree.
  - **Requirements**: FR-029.
  - **Paths**: `tests/unit/ex_hardware_inventory/test_hardware_operation.py`, `tests/unit/websocket_streams/web/test_ws_web_services.py`.
  - **Acceptance**: The pass and fail counts of each file are stored outside the repository.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - **Status**: absent

## Phase 2: Shared Readers and Natural Key

- [ ] T003 [P] Add the primary key strategy `ExTransceiverMaster`.
  - **Requirements**: FR-028.
  - **Paths**: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` (insert after the `ExHardwareInventory` entry at line 3506). `tests/unit/export/test_pk_strategies.py` (append one case).
  - **Acceptance**: The entry has type `composite_pk` and key `org_id`, `device_id`, and `item_path`. The test asserts the type and the key list.
  - **Verification**: `python -m pytest tests/unit/export/test_pk_strategies.py`
  - **Status**: absent

- [ ] T004 [P] Extend the existing builder types for a JSON reply.
  - **Requirements**: FR-011, FR-012, FR-014, FR-029.
  - **Paths**: `src/operations/exporting/ex_hardware_inventory/report/builder.py` (`TargetResult` at line 26, `FailureReasons.exact` with its `formats.get("xml")` line at 79, `RowFactory.classify` at line 91). `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` (append cases).
  - **Acceptance**: `TargetResult` has `json_text` with default `None`. `classify` accepts a completed target with a JSON reply. `exact` reads the entry of each requested format. Menu 309 results do not change.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py`
  - **Status**: absent

- [ ] T005 Create the native JSON reader.
  - **Requirements**: FR-012, FR-010.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/__init__.py` and `src/operations/exporting/ex_transceiver_master/json_reply.py` (class `NativeJsonFlattener`). `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` (append cases).
  - **Acceptance**: The reader follows `design/contracts/native-json.md`. It reuses `HardwareXmlFlattener.Names.field` and the `FlattenedItem` and `FlattenedDevice` types. Parity with the XML walker holds for identity fields.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py`
  - **Status**: absent

- [ ] T006 Create the transceiver row builder.
  - **Requirements**: FR-007, FR-008, FR-009, FR-010, FR-011, FR-013, FR-014, FR-015, FR-017.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/rows.py` (class `TransceiverRowBuilder`). `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` (append cases).
  - **Acceptance**: The builder keeps `add`, `counts`, `results`, `rows`, and `fieldnames`. It uses XML first and JSON only when XML is absent for a completed target. It applies `CellGuard.clean` to text columns.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py`
  - **Status**: absent

- [ ] T007 Create the transceiver report compiler.
  - **Requirements**: FR-017, FR-018.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/report.py` (class `TransceiverReportCompiler`). `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py` (append cases).
  - **Acceptance**: The compiler renders with `CsvRenderer.render`, checks with `CsvVerifier.verify`, and refuses a file above 64 MiB.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py`
  - **Status**: absent

- [ ] T008 Create the CLI report exporter.
  - **Requirements**: FR-019, FR-024, FR-025.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/report.py` (class `TransceiverReportExporter`). `tests/unit/ex_hardware_inventory/report/test_hardware_export.py` (append cases).
  - **Acceptance**: The exporter calls `write_with_format_selection` with `api_function_name` set to `ExTransceiverMaster` and the CSV format forced. It writes under `data/` with a UTC name. It never overwrites an earlier file. It removes a file that fails the read-back check.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/report/test_hardware_export.py`
  - **Status**: absent

## Phase 3: Existing CLI Collection Path

- [ ] T009 Read each requested native file in the run folder.
  - **Requirements**: FR-006, FR-011, FR-012.
  - **Paths**: `src/operations/exporting/ex_hardware_inventory/run/watch.py` (`RunFolder._xml` at line 139, and `RunFolder._result`). `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` (append cases).
  - **Acceptance**: `RunFolder` returns the XML text and the JSON text for each requested format. It keeps the run-folder path check and the size limit. The XML read for menu 309 does not change.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_batch.py`
  - **Status**: absent

- [ ] T010 Pass the output format into the batch request.
  - **Requirements**: FR-005.
  - **Paths**: `src/operations/exporting/ex_hardware_inventory/run/batch.py` (`OrganizationBatchRun` at line 173, request at line 176, preview at line 188). `src/operations/exporting/ex_hardware_inventory/operation.py` (`OrganizationPlan.build`). `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` (append cases).
  - **Acceptance**: `OrganizationBatchRun` takes `output_format` with the default `xml`. Each instance builds its own request. The preview posts `json` or `both` when the operator chose it.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_batch.py`
  - **Status**: absent

- [ ] T011 Print the commands that the confirmation runs.
  - **Requirements**: FR-003, FR-004, FR-005, FR-029.
  - **Paths**: `src/operations/exporting/ex_hardware_inventory/console.py` (`HardwareConsole.confirm` at line 71). `tests/unit/ex_hardware_inventory/test_hardware_operation.py` (append cases).
  - **Acceptance**: `confirm` accepts a list of commands and prints each one. Menu 309 passes its one command, and its output does not change.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - **Status**: absent

- [ ] T012 Share the menu steps and accept a result sink.
  - **Requirements**: FR-029.
  - **Paths**: `src/operations/exporting/ex_hardware_inventory/operation.py` (`ExHardwareInventoryReport.run` at line 225, `_confirmed` at line 287, `_collect` at line 296, `RunCollector` at line 101). Extract the steps into a public class `HardwareRunSteps`.
  - **Acceptance**: `RunCollector` takes a sink with `add`, `counts`, and `results`. Menu 309 passes the default sink. The existing tests pass unchanged.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - **Status**: absent

## Phase 4: Menu 310 in the CLI

- [ ] T013 Create the menu 310 flow.
  - **Requirements**: FR-001, FR-005, FR-016, FR-024, FR-026.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/operation.py` (classes `TransceiverFormatPrompt` and `ExTransceiverMasterReport`). `tests/unit/ex_hardware_inventory/test_hardware_operation.py` (append cases).
  - **Acceptance**: The format prompt accepts `XML`, `JSON`, or `BOTH`. Enter selects XML. Any other answer cancels. End of input and an interrupt cancel. The summary lines follow `design/contracts/cli-menu-310.md`. Log lines are ASCII and hold no secret.
  - **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - **Status**: absent

- [ ] T014 Register menu 310 in the entry point.
  - **Requirements**: FR-001, FR-027.
  - **Paths**: `MistHelper.py` (import after line 580, entry after the `"309"` entry that ends at line 4843).
  - **Acceptance**: The entry has title `Collect EX switch transceivers into one master CSV report`, category `OperationRegistry.skip_category("310")`, `destructive=False`, and `supports_fast=False`.
  - **Verification**: `python -m py_compile MistHelper.py`
  - **Status**: absent

- [ ] T015 Add the registry entry for menu 310.
  - **Requirements**: FR-027.
  - **Paths**: `src/foundation/support/utils/operation_registry.py` (add `"310"` after the `"309"` entry at line 537).
  - **Acceptance**: The category is `resource_intensive`. The skip reason names the EX switch shells and the typed confirmation.
  - **Verification**: `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py`
  - **Status**: absent

- [ ] T016 Update the menu count and the identity pins.
  - **Requirements**: FR-027, FR-029.
  - **Paths**: `tests/unit/test_menu_entry_metadata.py` (expected count at line 10, add `("310", False)` after line 45). `tests/guardrails/test_endpoint_catalog.py` (re-pin the `MistHelper.py` count and hash near line 547).
  - **Acceptance**: The count is 310. The new pin matches the value that the guard computes for the edited file.
  - **Verification**: `python -m pytest tests/unit/test_menu_entry_metadata.py`
  - **Status**: absent

- [ ] T017 Test the full CLI flow for each format.
  - **Requirements**: FR-005, FR-009, FR-011, FR-012, FR-016.
  - **Paths**: `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` (append cases).
  - **Acceptance**: The flow uses a fake shell with synthetic replies. XML, JSON, and both give one set of rows. A partial run keeps the rows of each collected switch.
  - **Verification**: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py`
  - **Status**: absent

## Phase 5: Portal Checkbox and Publication

- [ ] T018 Add the portal selection field.
  - **Requirements**: FR-021, FR-030.
  - **Paths**: `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` (`HardwareXmlSelection` at line 33, `preview_values` at line 64, `HardwareXmlPreset.parse` at line 342). `tests/unit/websocket_streams/web/test_ws_web_services.py` (update the exact dict at line 662, append parser cases).
  - **Acceptance**: `transceiver_csv` is a boolean with default `False`. The parser refuses a value that is not a boolean. The preview values include the field.
  - **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py`
  - **Status**: absent

- [ ] T019 Store the field with the preview and the run.
  - **Requirements**: FR-020, FR-021.
  - **Paths**: `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` (`BatchPreviewRecord` at line 50, field after line 68, `preview` at line 891, start output at line 925, summary payloads at lines 629 and 804). `tests/unit/websocket_streams/web/test_ws_web_services.py` (append cases).
  - **Acceptance**: The preview record keeps the field. The start output keeps the field. The summary payloads report it beside `format`.
  - **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py`
  - **Status**: absent

- [ ] T020 Publish the transceiver file in the run folder.
  - **Requirements**: FR-006, FR-020, FR-023, FR-030.
  - **Paths**: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (`TRANSCEIVER_NAME` after line 52, finish gate at line 260, `_compile` at line 702, `ReportDownload` at line 846 with the file-name line at line 871, `transceiver_download` after line 793). `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` (append cases).
  - **Acceptance**: The file `hardware/transceiver-master.csv` is published with the other outputs in one step. The manifest lists it. The ZIP archive holds it. With the checkbox off, every other output is unchanged.
  - **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_csv.py`
  - **Status**: absent

- [ ] T021 Serve the transceiver file through the download route.
  - **Requirements**: FR-023.
  - **Paths**: `src/mist/realtime/websocket_streams/web/blueprint/responses/download.py` (`BATCH_OUTPUTS` at line 24, error text at line 51). `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` (update the exact text at line 410, append a download case for `transceiver-csv`).
  - **Acceptance**: `format=transceiver-csv` returns `text/csv` with a name that starts with `ExTransceiverMaster_`. The error text lists the new value.
  - **Verification**: `python -m pytest tests/unit/websocket_streams/web/test_ws_hardware_csv.py`
  - **Status**: absent

- [ ] T022 Add the checkbox and the download link to the page.
  - **Requirements**: FR-002, FR-022.
  - **Paths**: `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` (checkbox inside `wsBatchHardwareFormatGroup` after the closing select tag at line 197, download link after the CSV download link at line 305). `tests/e2e/websockets_tab/test_websockets_page.py` (append cases).
  - **Acceptance**: The checkbox `wsBatchHardwareTransceiverCsv` is unchecked by default. It carries `data-testid="ws-batch-hardware-transceiver-csv"`. The link carries `data-testid="ws-batch-transceiver-csv-download"`.
  - **Verification**: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`
  - **Status**: absent

- [ ] T023 Bind the checkbox in the page script.
  - **Requirements**: FR-021, FR-022, FR-025.
  - **Paths**: `src/mist/realtime/websocket_streams/web/static/websockets.js` (change listener near line 183, request body at line 648, summary at line 713, report names at line 960, link visibility near line 952). `tests/e2e/websockets_tab/test_websockets_page.py` (append cases).
  - **Acceptance**: A change to the checkbox makes the preview invalid. The request carries `transceiver_csv`. The link appears only after the file is published. A failed browser check saves its screenshot under `test-artifacts/`.
  - **Verification**: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`
  - **Status**: absent

## Phase 6: Documents and Counts

- [ ] T024 Document the portal checkbox and menu 310.
  - **Requirements**: FR-001, FR-002, FR-005.
  - **Paths**: `documentation/operator-guide.md` (one new section after the heading at line 398). Keep the heading at line 338 and the sentence at line 425 unchanged.
  - **Acceptance**: The section gives the steps of the checkbox and of menu 310. It names the output files. It states that the checkbox is off by default.
  - **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - **Status**: absent

- [ ] T025 Regenerate the generated menu reference.
  - **Requirements**: FR-027.
  - **Paths**: `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md`, written by `scripts/generate_menu_wiki.py`.
  - **Acceptance**: After the two generator commands run, no file changes. The reference shows menu 310 in the resource intensive list.
  - **Verification**: `python -m scripts.menu_api_map`
  - **Status**: absent

- [ ] T026 Update the operation counts and the README row.
  - **Requirements**: FR-001, FR-027.
  - **Paths**: `.github/copilot-instructions.md` (count at line 11, `resource_intensive` row at line 224). `README.md` (one row after line 40).
  - **Acceptance**: The counts show 309 registered operations, numbered 1 through 310, with the gap at 152. The `resource_intensive` count is 12 and includes 310. The README row links to the operator guide.
  - **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`
  - **Status**: absent

- [ ] T027 Add the changelog fragment.
  - **Requirements**: Release note under the constitution.
  - **Paths**: `changelog.d/issue-4773-ex-transceiver-master-report.md` (new file).
  - **Acceptance**: The fragment has one `### Added` heading and one bullet that names issue #4773.
  - **Verification**: `python -m pytest tests/guardrails`
  - **Status**: absent

## Phase 7: Contracts and Audits

- [ ] T028 Confirm that the owned transport contracts stay green.
  - **Requirements**: FR-003.
  - **Paths**: `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py` and `tests/guardrails/test_websocket_transport_constitution.py` (read only).
  - **Acceptance**: Both files pass without an edit.
  - **Verification**: `python -m pytest tests/guardrails/test_websocket_transport_constitution.py`
  - **Status**: verified-present

- [ ] T029 Audit the inline comments and the action logging (T-COMMENTS).
  - **Requirements**: FR-024.
  - **Paths**: Each new and touched file listed in `plan.md`.
  - **Acceptance**: Each executable line has an inline comment. Each action has an info line before it and a debug line after it.
  - **Verification**: `python -m ruff check .`
  - **Status**: absent

- [ ] T030 Audit complexity and function limits.
  - **Requirements**: FR-029.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/`, `src/operations/exporting/ex_hardware_inventory/`.
  - **Acceptance**: No block has cyclomatic complexity above 10. Each function has five parameters or fewer.
  - **Verification**: `radon cc src/operations/exporting/ex_transceiver_master -j | complexity-gate --max 10`
  - **Status**: absent

- [ ] T031 Audit security (T-SECURITY).
  - **Requirements**: FR-017, FR-031.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/`.
  - **Acceptance**: Bandit reports no finding. Any finding is fixed, not suppressed.
  - **Verification**: `bandit -c pyproject.toml -r src/operations/exporting/ex_transceiver_master -q`
  - **Status**: absent

- [ ] T032 Check the test-quality ratchet on the changed tests.
  - **Requirements**: All test requirements.
  - **Paths**: The changed test files listed in `plan.md`. `.github/test-quality-baseline.json` stays unchanged.
  - **Acceptance**: The gate reports zero new findings. Issue #4783 tracks the two existing findings.
  - **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - **Status**: absent

- [ ] T033 Audit docstrings and dead code for the new package.
  - **Requirements**: FR-029.
  - **Paths**: `src/operations/exporting/ex_transceiver_master/`.
  - **Acceptance**: Interrogate reports at least 90 percent coverage. Vulture reports no finding at 70 percent confidence for the new package.
  - **Verification**: `interrogate src/operations/exporting/ex_transceiver_master --fail-under 90`
  - **Status**: absent

- [ ] T034 Run the authorized read-only live check.
  - **Requirements**: FR-031, SC-007.
  - **Paths**: `data/ExTransceiverMaster_<UTC time>.csv` and `data/websocket-streams/<run id>/hardware/` (outputs, ignored by git).
  - **Acceptance**: Run menu 310 with XML, JSON, and both on the configured lab organization. Compare the serial numbers in the CSV with the saved replies. Record counts only in the pull request.
  - Warning: Do not commit the `data/` folder. It holds device identifiers and serial numbers.
  - **Verification**: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py`
  - **Status**: open

## Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - **Requirements**: All.
  - **Paths**: Every path listed in `plan.md`.
  - **Gates and expected results**:
    - Compile: `python -m py_compile MistHelper.py`. Expected: no output.
    - Lint: `python -m ruff check .`. Expected: `All checks passed`.
    - Format: `python -m black --check .`. Expected: no file needs a change.
    - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`. Read `MYPY_PATHS` from `.github/workflows/ci.yml`. Expected: `Success`.
    - Tests: `python -m pytest tests/unit/ex_hardware_inventory tests/integration/ex_hardware_inventory tests/unit/websocket_streams/web tests/unit/export/test_pk_strategies.py tests/unit/test_menu_entry_metadata.py tests/e2e/websockets_tab/test_websockets_page.py`. Expected: all pass.
    - Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`. Expected: one summary line for each shard.
    - Safe sweep: `python MistHelper.py --test`. Expected: each safe operation completes. Mist checks skip without a token.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected: 80 percent or above.
    - Test quality: the ratchet in T032. Expected: `gate: 0 new findings vs baseline`.
    - Complexity: the command in T030. Expected: no block above 10.
    - Security lint: the command in T031. Expected: no finding.
    - Dependency audit: not applicable, because `requirements.txt` does not change.
    - Code quality: `pylint src/ --fail-under=9.5`. Expected: score 9.5 or above.
    - Dead code: `vulture $VULTURE_PATHS --min-confidence 70`. Read `VULTURE_PATHS` from `ci.yml`. Expected: no finding.
    - Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`. Expected: no violation and at least 90 percent coverage.
    - Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Expected: no changed file after the run.
    - Symbols: `symbol-diff --base origin/main <file>` for each changed Python file. Expected: `no module-level name changed`.
    - STE: the two `ste-linter` commands in T024 and T026. Expected: each file scores 80 or above.
    - Guardrails: `python -m pytest tests/guardrails`. Expected: all pass.
    - Container and ops portal gates: not applicable, because no container file, `ops-portal/` file, or `mist-ops-platform/` file changes.
  - **Acceptance**: Every applicable gate prints its expected result. The task records the actual output of each command.
  - **Verification**: `python -m pytest tests/guardrails`
  - **Status**: absent

- [ ] T-PR Commit, push, and open the pull request.
  - **Requirements**: All.
  - **Paths**: The feature branch and its pull request.
  - **Acceptance**: The commit subject is `feat(web-portal): add EX transceiver master report and CLI collection`. The commit body holds `Closes #4773` and the `Co-authored-by` trailer. The pull request body holds `Closes #4773`, the changed-file list, and the gate results.
  - **Verification**: `python -m pytest tests/guardrails`
  - **Status**: absent

- [ ] T-REMOTE-CI Watch the remote checks.
  - **Requirements**: All.
  - **Paths**: The pull request checks.
  - **Acceptance**: Run `gh pr checks <number> --watch` until each required check and CodeQL report success. Do not add the `auto-merge` label in this task.
  - **Verification**: `python -m pytest tests/guardrails`
  - **Status**: open

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - **Requirements**: All.
  - **Paths**: The pull request labels.
  - **Acceptance**: After remote checks pass and the orchestrator authorizes the merge, add the `auto-merge` label. After the merge, confirm the merge commit on `main`, the issue state, and the `container-build.yml` run for the merged revision. The image revision label must equal the merged commit SHA.
  - **Verification**: `python -m py_compile MistHelper.py`
  - **Status**: open
