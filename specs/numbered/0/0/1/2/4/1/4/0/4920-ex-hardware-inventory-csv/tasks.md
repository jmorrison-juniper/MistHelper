# Tasks: EX Hardware Inventory CSV

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: The specification, the constitution, and the request require tests. Write each test task before its implementation task, and see it fail first. Use mocked Mist responses and a fake shell for every automated check. The live check is read-only and runs on one organization only.

**Ownership**: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Do not add a module to `src/mist/realtime/websocket_streams/web/services/operations/`, because it holds five. Do not add a method to a class that already holds five. Add files by explicit path, because the structure guard reads tracked files only.

**Environment**: Run Python with the `.venv` of the main checkout from the worktree root. Set `SPECIFY_FEATURE_DIRECTORY` for Spec Kit scripts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other [P] tasks of its phase, because it edits a different file.
- **[Story]**: The user story that the task serves.
- A constrained field is cited as `data-model.md` `Entity.field`.

## Phase 1: Setup

- [X] T001 Create the worktree and the branch `feat/4920-ex-hardware-inventory-csv` from `origin/main`.
- [X] T002 Record the guardrail baseline on the untouched worktree: 1193 pass and 23 fail. Keep the failing test identifiers outside the repository for the final comparison.
- [X] T003 Create the empty package files `src/operations/exporting/ex_hardware_inventory/__init__.py`, `src/operations/exporting/ex_hardware_inventory/scope/__init__.py`, `src/operations/exporting/ex_hardware_inventory/report/__init__.py`, and `src/operations/exporting/ex_hardware_inventory/run/__init__.py`.
- [X] T004 [P] Add the synthetic reply builders in `tests/unit/ex_hardware_inventory/support/hardware_replies.py`. Cover a single switch, a two-member virtual chassis, disk and USB modules, a default namespace on `chassis-inventory`, `junos:style` on `chassis`, `cli/banner`, one-space version fields, and empty serial fields. Invent every value.
- [X] T005 [P] Add the fake Mist session, the fake ledger adapter, and the fake batch service in `tests/unit/ex_hardware_inventory/support/hardware_fakes.py`.

## Phase 2: Foundational

**Purpose**: The setting, the natural key, and the report compiler. Every story needs them.

- [X] T006 [P] Extend `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py` with cases for `PORTAL_WS_HARDWARE_CONCURRENCY`: unset, 1, 5, 0, 6, text, and the new `limits_payload` key.
- [X] T007 Add `hardware_concurrency` to `StreamSettings`, to `from_environment`, and to `limits_payload` in `src/mist/realtime/websocket_streams/live/sessions/settings.py`, per data-model.md `StreamSettings.hardware_concurrency`.
- [X] T008 [P] Add the strategy `ExHardwareInventory` as `composite_pk` in `src/foundation/support/refactors/endpoint_primary_key_strategies.py` and a case in `tests/unit/export/test_pk_strategies.py`, per data-model.md `ReportRow.org_id`, `ReportRow.device_id`, and `ReportRow.item_path`.
- [X] T009 [P] Write `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py`: levels, the `#2` path suffix, local-name matching across namespace versions, attributes, trimmed and empty values, the banner, a virtual chassis, disk and USB modules, and a malformed reply.
- [X] T010 [P] Write `tests/unit/ex_hardware_inventory/report/test_hardware_columns.py`: the fixed column order, the preferred item field order, the sorted extras, and the spreadsheet guard for each leading character and for the exempt columns.
- [X] T011 [P] Write `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py`: the state mapping, collected and outcome rows, the stable row order, the run time on every row, and unique natural keys.
- [X] T012 [P] Write `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py`: UTF-8 text, the header row, standard quoting, the file check, and the size limit.
- [X] T013 Implement `HardwareXmlFlattener` and `FlattenedDevice` in `src/operations/exporting/ex_hardware_inventory/report/flatten.py`, per data-model.md `FlattenedItem.level`, `FlattenedItem.path`, `FlattenedItem.item_type`, and `FlattenedItem.fields`. Match local names only. Parse with the same DTD and entity rule as `hardware_xml.py`.
- [X] T014 Implement `ReportColumns` and `CellGuard` in `src/operations/exporting/ex_hardware_inventory/report/columns.py`, per data-model.md `ReportRow.item_level`, `ReportRow.item_type`, `ReportRow.record_type`, `ReportRow.collection_status`, `ReportRow.scope`, and `ReportRow.item_<field>`.
- [X] T015 Implement `TargetResult` and `ReportBuilder` in `src/operations/exporting/ex_hardware_inventory/report/builder.py`, per data-model.md `TargetResult.identity`, `TargetResult.org_name`, `TargetResult.state`, `TargetResult.reason`, `TargetResult.xml_text`, `ReportRow.report_run_utc`, `ReportRow.org_id`, `ReportRow.org_name`, `ReportRow.site_id`, `ReportRow.site_name`, `ReportRow.device_id`, `ReportRow.device_name`, `ReportRow.collection_detail`, `ReportRow.device_cli_banner`, and `ReportRow.item_path`.
- [X] T016 Implement `CsvRenderer` and `CsvVerifier` in `src/operations/exporting/ex_hardware_inventory/report/csv_file.py`, per data-model.md `ReportFile.row_count` and `ReportFile.size_bytes`. The renderer takes the byte limit as a parameter. Both front ends pass 64 MiB, and a report over the limit raises an error and returns no file.
- [X] T017 Run the flattener on the retained real replies of issue #4769 with a temporary script outside the repository. Print only counts: files, items, columns, and errors. Record the aggregate result in the tracking issue.

## Phase 3: User Story 1 - Collect one CSV for an organization from the CLI (Priority: P1) MVP

**Goal**: Menu 309 runs one organization from the CLI and writes one CSV.

**Independent Test**: Run menu 309 against a mocked organization with connected EX switches, an offline switch, a non-EX device, and a virtual chassis. One CSV holds the rows of the connected switches.

### Tests for User Story 1

- [X] T018 [P] [US1] Write `tests/unit/ex_hardware_inventory/scope/test_hardware_session.py`: `AdmissionBinding` sets and restores the ledger organization, reaches the ledger through the mounted adapter, and does nothing when no ledger exists. `SdkErrorMute` hides SDK error records only inside its block.
- [X] T019 [P] [US1] Write `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py`: preview, confirmation phrase, start, polling, the subset rule, an expired preview that previews again, and a new target that stops the organization.
- [X] T020 [P] [US1] Write `tests/unit/ex_hardware_inventory/report/test_hardware_export.py`: the exporter call with the CSV format forced and explicit field names, the UTC-stamped name, the file check, and the removal of a file that fails the check.
- [X] T021 [P] [US1] Write `tests/unit/ex_hardware_inventory/test_hardware_operation.py`: a wrong phrase, end of input, an interrupt, the right phrase, no target, the summary lines, the return value, and the registry and menu entry facts.
- [X] T022 [P] [US1] Write `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py`: the whole CLI flow against the real `WebSocketBatchService` with fake collaborators and a fake shell that returns synthetic replies.

### Implementation for User Story 1

- [X] T023 [US1] Implement `AdmissionBinding` and `SdkErrorMute` in `src/operations/exporting/ex_hardware_inventory/scope/session.py`.
- [X] T024 [US1] Implement `BatchPreview`, `BatchRunResult`, `BatchStack`, and `OrganizationBatchRun` in `src/operations/exporting/ex_hardware_inventory/run/batch.py`, and `BatchWatcher` and `RunFolder` in `src/operations/exporting/ex_hardware_inventory/run/watch.py`. Build the service stack with the shell flag on and the concurrency from `StreamSettings.hardware_concurrency`. Read each run folder through its manifest.
- [X] T025 [US1] Implement `ReportExporter` in `src/operations/exporting/ex_hardware_inventory/report/export.py`, per data-model.md `ReportFile.name`, `ReportFile.row_count`, and `ReportFile.partial`. When the name already exists, add a numeric suffix so no earlier report is overwritten.
- [X] T026 [US1] Implement `ExHardwareInventoryReport` in `src/operations/exporting/ex_hardware_inventory/operation.py` and `HardwareConsole` in `src/operations/exporting/ex_hardware_inventory/console.py`: the console steps of the menu contract, the typed phrase through `InputUtils.safe_input`, and the summary, per data-model.md `RunSummary.organizations`, `RunSummary.targets`, `RunSummary.counts`, and `RunSummary.report_path`.
- [X] T027 [US1] Register menu 309: import the class and add the `MenuEntry` in `MistHelper.py`, and add the entry `309` with the category `resource_intensive` in `src/foundation/support/utils/operation_registry.py`.
- [X] T028 [US1] Update the menu expectations: `tests/unit/test_menu_entry_metadata.py`, `tests/unit/ap_warning_report/test_menu.py`, and the two count lines in `.github/copilot-instructions.md`. Re-pin `tests/guardrails/test_endpoint_catalog.py` after the last edit of `MistHelper.py`.
- [ ] T029 [US1] Run the Story 1 tests and the menu guards. Commit and push.

## Phase 4: User Story 2 - Find the scope and run for an MSP (Priority: P1)

**Goal**: The tool detects the credential scope and runs every organization of an MSP.

**Independent Test**: Mocked profiles give the right scope for an organization token, an MSP login, an MSP list that returns HTTP 403, and an unreadable profile. A mocked MSP run finishes the other organizations when one fails.

### Tests for User Story 2

- [X] T030 [P] [US2] Write `tests/unit/ex_hardware_inventory/scope/test_hardware_profile.py`: `getSelf` answers 200, 401, 403, 429, 5xx, and a transport fault. The account kind follows `email`. The credential type follows the session.
- [X] T031 [P] [US2] Write `tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py`: an organization token, an MSP login with a good list, HTTP 403 and other failures of the list, a failed later page, several grants with and without `org_id`, an `org_id` outside the grants, and the union of direct and MSP organizations without repeats.
- [X] T032 [P] [US2] Write the MSP loop tests in `tests/unit/ex_hardware_inventory/test_hardware_operation.py` (class `TestMspScope`) and in the integration test (class `TestMspEndToEnd`), not in a separate `run/test_hardware_batch_msp.py`: the organization loop, a failing organization, a discovery error such as HTTP 429 that is reported and does not stop the loop, the per-organization subset rule, the total phrase, and a cancel in the middle.

### Implementation for User Story 2

- [X] T033 [US2] Implement `CredentialProfile` and `ProfileReader` in `src/operations/exporting/ex_hardware_inventory/scope/profile.py`, per data-model.md `ScopeDecision.credential_type` and `ScopeDecision.account_kind`. Require status 200.
- [X] T034 [US2] Implement `OrganizationRef`, `ScopeDecision`, `ScopeError`, and `ScopeResolver` in `src/operations/exporting/ex_hardware_inventory/scope/resolver.py`, per data-model.md `OrganizationRef.org_id`, `OrganizationRef.org_name`, `OrganizationRef.msp_id`, `OrganizationRef.source`, `ScopeDecision.mode`, `ScopeDecision.organizations`, and `ScopeDecision.notes`. Mute the SDK error lines for the MSP list and log one warning.
- [X] T035 [US2] Wire the scope and the organization loop into `src/operations/exporting/ex_hardware_inventory/operation.py` and `src/operations/exporting/ex_hardware_inventory/run/batch.py`. Preview every organization first, ask once, preview each organization again just before it starts, and bind the ledger organization for each run. A discovery error of one organization, such as HTTP 429, is reported for that organization and the loop goes on.
- [ ] T036 [US2] Run the Story 2 tests. Commit and push.

## Phase 5: User Story 3 - Run the same action from the Multi Site tab (Priority: P1)

**Goal**: The portal action offers **One combined CSV report**, publishes it, and offers the download. MSP scope works in the portal.

**Independent Test**: With fake services and a fake browser, choose the CSV output, preview, start, and download. XML, JSON, and both outputs still behave as before.

### Tests for User Story 3

- [ ] T037 [P] [US3] Write `tests/unit/websocket_streams/web/test_ws_hardware_csv.py`: the preset accepts `csv`, the fixed command list holds only the XML command, the finish step publishes `hardware/inventory.csv`, the manifest lists it, a compile failure sets the artifact status to failed and keeps the XML files, the download route, and the quota refusal. Add a regression case: the XML, JSON, and both runs write the same files as before this change.
- [ ] T038 [P] [US3] Write `tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py`: `ReportHook` with fake read and publish callables, including every error converted to the output failure.
- [ ] T039 [P] [US3] Write `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py`: the scope-aware picker returns the sites of all organizations, routes reads by site, and delegates in organization scope. The scope-aware checker builds each request for the right organization.
- [ ] T040 [P] [US3] Add a browser test in `tests/e2e/websockets_tab/test_websockets_page.py`: the output choice, the scope line, the preview, the start request, and the download link.

### Implementation for User Story 3

- [ ] T041 [US3] Implement `ReportHook` in `src/operations/exporting/ex_hardware_inventory/run/publisher.py`, per data-model.md `ReportFile.name`, `ReportFile.size_bytes`, and `ReportFile.partial`. It takes callables, so it imports no artifact internals.
- [ ] T042 [US3] Add the `csv` format to `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py`: the format set and the command list in `batch_request`.
- [ ] T043 [US3] Call the hook from the finish step in `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`, with no new method. Convert every error to `StreamRequestError("output_failed", ...)`.
- [ ] T044 [US3] Add the `format=csv` branch to `src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py` and `src/mist/realtime/websocket_streams/web/blueprint/responses/download.py`.
- [ ] T045 [US3] Add the `scope` object, the `org_name` target field, and the settings-based concurrency limit to the preview in `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`.
- [ ] T046 [US3] Implement `ScopeAwarePicker` and `ScopeAwareChecker` in `src/operations/exporting/ex_hardware_inventory/run/routing.py`. Wire them with the smallest edit in `src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py`.
- [ ] T047 [US3] Add the output choice, the scope line, the download link, and the default concurrency to `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` and `src/mist/realtime/websocket_streams/web/static/websockets.js`. Use the `data-testid` values of the portal contract.
- [ ] T048 [US3] Run the Story 3 tests and the WebSocket structure guard. Update the pinned counts only if an edit changes them. Commit and push.

## Phase 6: User Story 4 - Limit concurrency with an environment variable (Priority: P2)

**Goal**: One variable limits the open shells in both front ends.

**Independent Test**: With a fake shell that records the open shells, 12 targets never exceed a limit of 1, 3, or 5.

### Tests for User Story 4

- [ ] T049 [P] [US4] Write `tests/unit/ex_hardware_inventory/run/test_hardware_concurrency.py`: the peak number of open shells for limits 1, 3, and 5 with 12 targets, the default, and the warning for a bad value. Check that the CLI and the preview show the value in use.

### Implementation for User Story 4

- [ ] T050 [US4] Pass `StreamSettings.hardware_concurrency` to the batch start in `src/operations/exporting/ex_hardware_inventory/run/batch.py`, and print it in the confirmation step of `src/operations/exporting/ex_hardware_inventory/operation.py`.
- [ ] T051 [US4] Run the Story 4 tests. Commit and push.

## Phase 7: User Story 5 - Trust the report (Priority: P2)

**Goal**: The report shows every attempted switch, holds no credential, and runs no formula.

**Independent Test**: A failing switch, a cancelled run, a reply with a credential, and a cell that starts with `=` give the outcome rows, the partial marker, the rejection, and the neutralized cell.

### Tests for User Story 5

- [ ] T052 [P] [US5] Write `tests/unit/ex_hardware_inventory/report/test_hardware_report_trust.py`: the outcome rows for each status, the partial marker in the summary and the manifest, a reply with a credential that adds no row, the spreadsheet guard end to end, a write failure that leaves no file, and the size refusal.

### Implementation for User Story 5

- [ ] T053 [US5] Close the gaps that T052 finds in `src/operations/exporting/ex_hardware_inventory/report/builder.py`, `report/export.py`, and `run/publisher.py`.
- [ ] T054 [US5] Run the Story 5 tests. Commit and push.

## Phase 8: Polish and Cross-Cutting Concerns

- [ ] T055 [P] Document the feature in `documentation/operator-guide.md`: a paragraph for menu 309 and a section for the new output choice. Document the variable in `deploy/.env.example` and `documentation/sample.env`.
- [ ] T056 [P] Add the release note `changelog.d/issue-4920-ex-hardware-inventory-csv.md`.
- [ ] T057 Regenerate the menu pages with `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Run the second command with `--check`.
- [ ] T058 Run the repository guards and compare with the baseline: the nested package guard, the domain structure guard, the endpoint catalog, the registry coverage, the destructive menu docs, the portal operation coverage, the WebSocket structure guard, and the full `tests/guardrails` folder.
- [ ] T059 Run the local gates on every changed file: `python -m py_compile MistHelper.py`, Ruff, Black, mypy with `MYPY_PATHS`, Bandit, the complexity gate at 10, Vulture, Pylint at 9.5, pydocstyle, Interrogate at 90, `symbol-diff`, the STE gate, and the link check.
- [ ] T060 Run the full WebSocket unit, contract, and integration tests and the new tests. Run the test quality preflight and the `test-quality-analyzer` gate on the committed tree.
- [ ] T061 Audit every new and changed line for its inline comment, and every meaningful action for its before and after log lines (Constitution VI and VII).
- [ ] T062 File the follow-up issues: shared admission rejects site-level requests when the ledger holds no organization, and the stale README step in the constitution. Link issue #4713.

## Phase 9: Live Validation

- [ ] T063 Run menu 309 live and read-only on the one organization of the configured token. Run one switch first. Check the scope line. Check that the report serial numbers equal the saved XML serial numbers. Search the output for the token. Record aggregate counts only in the tracking issue.
- [ ] T064 Run the portal path with the real services and no browser, if the structure of the services allows it. Compare its report with the CLI report.

## Phase 10: Delivery

- [ ] T065 Run `speckit.analyze` and write `analysis.md`. Run `speckit.converge`. Fix every actionable finding.
- [ ] T066 Open the pull request with the template, the gate results, and the file list. Wait for every check and for CodeQL with `gh pr checks <number> --watch`. Do not add `auto-merge`. Leave the merge to the owner.
- [ ] T067 After the owner merges, verify the merge commit on `main`, the issue state, and the container build.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: starts at once.
- **Foundational (Phase 2)**: needs Setup. It blocks every story.
- **Story 1 (Phase 3)**: needs Phase 2. It is the MVP.
- **Story 2 (Phase 4)**: needs Story 1, because it wires the scope into the same run.
- **Story 3 (Phase 5)**: needs Phase 2. Its MSP part needs Story 2.
- **Story 4 (Phase 6)**: needs Phase 2 and Story 1. It touches the page that Story 3 changes.
- **Story 5 (Phase 7)**: needs Stories 1 and 3.
- **Polish (Phase 8)**: needs the stories that ship.
- **Live validation (Phase 9)**: needs Phase 8.
- **Delivery (Phase 10)**: needs Phase 9. T067 needs the owner.

### Parallel Opportunities

- T004 and T005 run together.
- T006, T008, and T009 through T012 run together, because each edits a different test file.
- T013 through T016 split by file after their tests exist.
- T018 through T022 run together.
- T030 through T032 run together.
- T037 through T040 run together.
- T055 and T056 run together.

### Parallel Example: Foundational Tests

```text
Task T009: Flattener tests in tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py
Task T010: Column tests in tests/unit/ex_hardware_inventory/report/test_hardware_columns.py
Task T011: Builder tests in tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py
Task T012: File tests in tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete Story 1. Run menu 309 on mocks, then validate live on one organization.
3. Stop and check the report against the saved XML before more work.

### Incremental Delivery

1. Story 1: the CLI for one organization.
2. Story 2: scope detection and the MSP loop.
3. Story 3: the portal output and MSP scope.
4. Stories 4 and 5: the concurrency page default and the trust rules.
5. Polish, live validation, and the pull request.

### Guard Rules

- Run the WebSocket structure guard after every edit of a WebSocket file.
- Add each new file by explicit path before any guard run.
- Commit after each story phase and update the tracking issue.
