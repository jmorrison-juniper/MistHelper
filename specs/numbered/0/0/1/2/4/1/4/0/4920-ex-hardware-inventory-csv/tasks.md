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
- [X] T029 [US1] Run the Story 1 tests and the menu guards. Commit and push.

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
- [X] T036 [US2] Run the Story 2 tests. Commit and push.

## Phase 5: User Story 3 - Run the same action from the Multi Site tab (Priority: P1)

**Goal**: The portal action offers **One combined CSV report**, publishes it, and offers the download. MSP scope works in the portal.

**Independent Test**: With fake services and a fake browser, choose the CSV output, preview, start, and download. XML, JSON, and both outputs still behave as before.

### Tests for User Story 3

- [X] T037 [P] [US3] Write `tests/unit/websocket_streams/web/test_ws_hardware_csv.py`: the preset accepts `csv`, the fixed command list holds only the XML command, the finish step publishes `hardware/inventory.csv`, the manifest lists it, a compile failure sets the artifact status to failed and keeps the XML files, the download route, and the quota refusal. Add a regression case: the XML, JSON, and both runs write the same files as before this change.
- [X] T038 [P] [US3] Write `tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py`: `ReportHook` with fake read and publish callables, including every error converted to the output failure.
- [X] T039 [P] [US3] Write `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py`: the scope-aware picker returns the sites of all organizations, routes reads by site, and delegates in organization scope. The scope-aware checker builds each request for the right organization.
- [X] T040 [P] [US3] Add a browser test in `tests/e2e/websockets_tab/test_websockets_page.py`: the output choice, the scope line, the preview, the start request, and the download link.

### Implementation for User Story 3

- [X] T041 [US3] Implement `ReportHook` in `src/operations/exporting/ex_hardware_inventory/run/publisher.py`, per data-model.md `ReportFile.name`, `ReportFile.size_bytes`, and `ReportFile.partial`. It takes callables, so it imports no artifact internals.
- [X] T042 [US3] Add the `csv` format to `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py`: the format set and the command list in `batch_request`.
- [X] T043 [US3] Call the hook from the finish step in `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`. The storage class holds five methods, so the publication lives in a new nested class `Reports`, and the saved files are read through the new `Files.read_bytes`. A failure marks the artifact failed, keeps the XML files, and the finish step raises `StreamRequestError("output_failed", ...)`. `SessionArtifactService.csv_download` serves the report.
- [X] T044 [US3] Add the `format=csv` branch to `src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py` and `src/mist/realtime/websocket_streams/web/blueprint/responses/download.py`.
- [X] T045 [US3] Store the scope with the run in `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` (the report names the organizations from it), and add the `scope` counts to the preview in the route `src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py` (class `PreviewScope`), because the preview function is at its complexity limit. The page reads the concurrency default from the catalog limit `hardware_concurrency`, so no change of the preview limits is needed. The report takes the organization name from the stored scope, so no `org_name` target field exists.
- [X] T046 [US3] Implement `ScopeAwarePicker` and `ScopeAwareChecker` in `src/operations/exporting/ex_hardware_inventory/run/routing.py`. Wire them with the smallest edit in `src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py`.
- [X] T047 [US3] Add the output choice, the scope line, the download link, and the default concurrency to `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` and `src/mist/realtime/websocket_streams/web/static/websockets.js`. Use the `data-testid` values of the portal contract.
- [X] T048 [US3] Run the Story 3 tests and the WebSocket structure guard. Update the pinned counts only if an edit changes them. Commit and push.

## Phase 6: User Story 4 - Limit concurrency with an environment variable (Priority: P2)

**Goal**: One variable limits the open shells in both front ends.

**Independent Test**: With a fake shell that records the open shells, 12 targets never exceed a limit of 1, 3, or 5.

### Tests for User Story 4

- [X] T049 [P] [US4] Write `tests/integration/ex_hardware_inventory/test_hardware_concurrency.py` (it needs the shared world of the integration tests): the peak number of open shells for limits 1, 3, and 5 with 12 targets, the default, and the warning for a bad value. Check that the CLI and the preview show the value in use.

### Implementation for User Story 4

- [X] T050 [US4] Pass `StreamSettings.hardware_concurrency` to the batch start in `src/operations/exporting/ex_hardware_inventory/run/batch.py`, and print it in the confirmation step of `src/operations/exporting/ex_hardware_inventory/operation.py`.
- [X] T051 [US4] Run the Story 4 tests. Commit and push.

## Phase 7: User Story 5 - Trust the report (Priority: P2)

**Goal**: The report shows every attempted switch, holds no credential, and runs no formula.

**Independent Test**: A failing switch, a cancelled run, a reply with a credential, and a cell that starts with `=` give the outcome rows, the partial marker, the rejection, and the neutralized cell.

### Tests for User Story 5

- [X] T052 [P] [US5] Write `tests/integration/ex_hardware_inventory/test_hardware_report_trust.py` (it needs the shared world of the integration tests): the outcome rows for each status, the partial marker in the summary and the manifest, a reply with a credential that adds no row, the spreadsheet guard end to end, a write failure that leaves no file, and the size refusal.

### Implementation for User Story 5

- [X] T053 [US5] Close the gaps that T052 finds in `src/operations/exporting/ex_hardware_inventory/report/builder.py`, `report/export.py`, and `run/publisher.py`.
- [X] T054 [US5] Run the Story 5 tests. Commit and push.

## Phase 8: Polish and Cross-Cutting Concerns

- [X] T055 [P] Document the feature in `documentation/operator-guide.md`: a paragraph for menu 309 and a section for the new output choice. Document the variable in `deploy/.env.example` and in the settings table of `documentation/wiki/Web-Portal.md`. `documentation/sample.env` holds no WebSocket setting, so it stays unchanged.
- [X] T056 [P] Add the release note `changelog.d/issue-4920-ex-hardware-inventory-csv.md`.
- [X] T057 Regenerate the menu pages with `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Run the second command with `--check`.
- [X] T058 Run the repository guards and compare with the baseline: the nested package guard, the domain structure guard, the endpoint catalog, the registry coverage, the destructive menu docs, the portal operation coverage, the WebSocket structure guard, and the full `tests/guardrails` folder. Result: 23 failed, 1193 passed, 9 skipped on the baseline, and the same 23 failures after the change. The first run after the change found one new failure, the symbol preservation guard, which counted the removed `BatchTargetPickerService` import of the service factory. A reviewed removal entry repaired it.
- [X] T059 Run the local gates on every changed file: `python -m py_compile MistHelper.py`, Ruff, Black, mypy with `MYPY_PATHS`, Bandit, the complexity gate at 10, Vulture, Pylint at 9.5, pydocstyle, Interrogate at 90, `symbol-diff`, the STE gate, and the link check. Result: every gate passes. Pylint scores 9.73 on the changed source, with `too-few-public-methods` notes and four `protected-access` notes in `run/routing.py`.
- [X] T060 Run the full WebSocket unit, contract, and integration tests and the new tests. Run the test quality preflight and the `test-quality-analyzer` gate on the committed tree. Result: 1142 passed and 6 skipped in the feature, WebSocket, and guard tests. The ratchet for the changed files prints `gate: 0 new findings vs baseline`.
- [X] T061 Audit every new and changed line for its inline comment, and every meaningful action for its before and after log lines (Constitution VI and VII).
- [X] T062 File the follow-up issues: shared admission rejects site-level requests when the ledger holds no organization (#4921, links #4713), the stale README step in the constitution (#4922), and the repeated site list read of the batch resolver (#4923).

## Phase 9: Live Validation

- [X] T063 Run menu 309 live and read-only on the one organization of the configured token. Run one switch first. Check the scope line. Check that the report serial numbers equal the saved XML serial numbers. Search the output for the token. Record aggregate counts only in the tracking issue. Result: the live run reached every step up to the shell. The token is an organization token with the read-only role, and Mist refused each of the 15 shell sessions with HTTP 403 and the detail `shell access not allowed for this user`. The menu has no switch limit, so the run used all 15 connected switches. The report holds 15 `failed` outcome rows and no hardware row. The serial number check has no data, because no shell opened. The search for the token found it in none of the 3 files. The success path needs a credential with a role that can open a shell, so it stays open for the owner. T070 closed it after the owner changed the role of the token.
- [X] T064 Run the portal path with the real services and no browser, if the structure of the services allows it. Compare its report with the CLI report. Result: the integration tests in `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` run the real Flask routes and the real batch services with fake Mist calls and fake shells. Both front ends build the report with the same `ReportBuilder`, so they hold the same columns. No test compares the two files byte for byte.
- [X] T068 [US1] Add the read-only role note that the live test showed to be useful: `ProfileReader` sets `read_only`, the scope decision adds one note, and a refused switch gets the detail `The shell could not collect this switch. See the log for the cause.` Tests, the operator guide, the CLI contract, FR-043, and the release note cover it.
- [X] T069 [US5] Repair the fault that the second live run showed (issue #4926, FR-044). One manifest replace in a OneDrive folder got a Windows permission error, the batch record became `failed`, and the last switch was refused. `BatchArtifactStorage.Metadata.replace` now tries up to five times, with waits of 50, 100, 200, and 400 milliseconds, and both the manifest write and the publish step use it. The report now says that the reply could not be saved when the XML entry of the target says so. Ten tests in `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` cover the retry. The tests of the report builder, the report hook, and the CLI batch cover the exact reason. A mutation run, with the old `os.replace` call back in both places, failed four of the ten retry tests.
- [X] T070 Run menu 309 live again with the admin-role token that the owner set, on the one test organization. The first run with that token, before the fix, collected 14 of 15 switches (T069). The run after the fix collected 15 of 15: 297 rows, all `hardware_item`, run status `complete`, manifest status `ready`. The set of serial numbers in the report equals the set in the 15 saved replies (114 distinct values, none missing in either direction), and each switch has as many rows as its reply has chassis elements. The search for the token found it in none of 34 files. SC-005 is met live.
- [X] T071 Run the portal path live, in a real browser, on the one test organization (the owner asked for it). The WebSockets page showed `The portal has no Mist session or organization.` for `python MistHelper.py --web-portal`, because that mode never resolved the organization (issue #4929, FR-047). The fix resolves it in the launcher, with three unit tests, and a live start gave a ready catalog (16 channels, 54 utilities). With the production wiring, the browser run of Multi Site, the hardware action, and the CSV output previewed 15 targets, typed `RUN 15 TARGETS`, and finished 15 of 15. The downloaded CSV has 297 rows and 28 columns, and its size is the same as the CLI report (101182 bytes). The rows equal the rows of the CLI report, in the same order, and the 114 serial numbers equal the serial numbers of the 15 saved replies. The token is in none of 112 files.
- [X] T072 [US3] Keep the Targets card for the hardware action (issue #4927, FR-045). The owner found that the checkbox emptied the card. `HardwareXmlSelection.parse_sites` validates the optional `sites` field, `batch_request` passes it to the existing site resolver, and the preview gives `site_selection` with a count. The page loads the sites with the catalog shell, sends a subset only when chosen, and gives the sites of the catalog operation back when the action is off. Nineteen unit cases and four browser tests cover it. Live: one site of 48 gave 4 targets, `RUN 4 TARGETS`, 4 of 4 completed, and 71 rows that equal the 71 rows of the full report for that site.
- [X] T073 [US3] Name the confirmation word and the preview step on the page (issue #4928, FR-046). The review card lists four steps, the label and the placeholder show the word, a line above **Start batch** gives the next action, and a changed choice clears the preview. Four browser tests cover it.
- [X] T074 Audit each Mist list call of the feature for `limit=1000` (FR-048). The portal run made 177 Mist requests. Each list call carried `limit=1000`: 49 organization site lists, 48 device lists, and 63 device statistics lists. The other requests were 15 shell sessions and 2 profile reads. `listMspOrgs` has no limit in the SDK or in the OpenAPI file.
- [X] T075 [US3] Add `CsvPreviewer.page` to `report/csv_file.py` (issue #4931, FR-050 through FR-052). It reads the bytes of the report, applies the plain text filter, cuts long cells, and gives one page with the columns, the totals, and the number of cut cells. Twenty-nine unit tests in `tests/unit/ex_hardware_inventory/report/test_hardware_csv_preview.py` cover the paging, the filter, the cut, a damaged file, and an empty file.
- [X] T076 [US3] Add `SessionArtifactService.Preview` and bind it as `csv_preview` (FR-050, FR-052). It reuses `csv_download`, refuses a report over 16 MiB, and writes the log lines of the action with counts only. The 44 tests in `tests/unit/websocket_streams/web/test_ws_csv_preview.py` use the real artifact service and the real portal app. A fault injection run applied 17 small faults to the three new source files, and the tests caught all 17.
- [X] T077 [US3] Add the route module `responses/csv_preview.py` and register `GET /api/websockets/batches/<id>/csv-preview` (FR-050). Route tests use the real portal app. Two integration tests run the real services: the table equals the parsed download, and a bad query gets HTTP 400 before any read.
- [X] T078 [US3] Add the table to the page: the template, the script, and the style (FR-049, FR-053). Thirteen browser tests cover the table, the filter, the page buttons, the refusal text, a cell with markup, a cut cell, the screen reader names, and a page reload.
- [X] T079 Document the table in `documentation/operator-guide.md`, in the portal contract, and in the release note. Move the pin of the WebSocket structure test from (148, 292, 913) to (149, 295, 917) with a comment that names issue #4931.
- [X] T080 Run the table live in a real browser on the one test organization, with the report of the full run. Result: the portal on the final code, with a Playwright browser, ran the hardware action with the CSV output on the 15 connected EX switches. All 15 completed, and the output was `ready`. The table showed `Rows 1 to 297 of 297.` with 28 columns. A comparison in the page found the table equal to the downloaded file: the same 28 column names, the same 297 rows, and every cell equal. The file has 101182 bytes, as before. The filter `FPC`, typed one key at a time, sent one filter request and showed 151 rows. An independent filter of the downloaded file gives the same 151 rows in the same order. The page made one preview read for the run. The token is in none of 65 files. The run of one site is not repeated, because the table reads the published report and has no site logic, and the full report holds the rows of each site.
- [X] T081 [US3] Repair the second fault that the live check showed (issue #4932, FR-054). The page opened the batch parent of the hardware action as a terminal, because the parent keeps the output name `terminal`. The portal answered HTTP 409 `not_terminal` on the terminal read and on the resize, and the output panel showed `State: Connecting` for ever on the first tab. `isTerminalSession` now returns false for a `multi_site` parent. One browser test, which failed before the change with six terminal reads in 1.5 seconds, proves it. Live: the run after the change made no terminal request, and the first tab showed `State: Finished` with the 30 messages of the parent.

## Phase 10: Delivery

- [X] T065 Run `speckit.analyze` and write `analysis.md`. Run `speckit.converge`. Fix every actionable finding. Result: the first pass found nine findings before the code, and the second pass in `analysis.md` found five after the implementation. F1 through F3 are fixed, F4 is accepted, and F5 is out of scope.
- [ ] T066 Open the pull request with the template, the gate results, and the file list. Wait for every check and for CodeQL with `gh pr checks <number> --watch`. Do not add `auto-merge`. Leave the merge to the owner.
- [ ] T067 After the owner merges, verify the merge commit on `main`, the issue state, and the container build.

## Phase 11: User Story 6 - One master XML file (Priority: P1)

The customer added this requirement on 2026-11-25 (issue #4933, FR-055 through FR-069, SC-009 through SC-012). One pull request holds this phase and the earlier phases, so T066 and T067 cover it too.

- [X] T082 [US6] Add `RowFactory.classify` to `report/builder.py` and refactor `RowFactory.build` to call it (FR-059). One place decides the status and the plain detail of a target, so the CSV report and the master XML never disagree. `ReportBuilder.results` keeps each result for the XML. A test builds both files from the same results and compares the statuses.
- [X] T083 [US6] Add `run/master_xml.py` with `XmlText` (the character rules and the escapers), `XmlWriter` (a strict namespace-aware expat copy of each reply that keeps elements, attributes, text, namespace addresses, and prefixes, and replaces only formatting white space with the indent of the file), and `MasterXmlBuilder` (the wrapper elements, the order, and the counts). FR-056 through FR-060, FR-062, and FR-064.
- [X] T084 [US6] Add `MasterXmlVerifier` (FR-061). A second pass that writes no XML checks the exact declaration, strict UTF-8, the character rules, a strict parse that refuses a DTD, the structure, the counts of the root against the document and the run, the event digest of each embedded reply against its source, and the standard canonicalizer. A document that fails any check is never handed out.
- [X] T085 [US6] Add `MasterXmlExporter` for the CLI (FR-063): a unique UTC-stamped name that takes the stem of the CSV report, exclusive creation, a read-back of the disk, a second check of the bytes that were read, and removal of the file on any failure.
- [X] T086 [US6] Add `documentation/schemas/ex-hardware-inventory.xsd` (FR-067) and the contract tests that pin its namespace, its attributes, and its enumerations to the constants of the code. The reply sits under a lax wildcard, because no public schema covers each Junos release.
- [X] T087 [US6] Write the file from menu 309 (FR-055, FR-069): `MasterXmlStep` in `operation.py`, the `Master XML:` line in the console, the new title in `MistHelper.py`, and one sentence for each refusal (the size limit and a failed check). The CSV report stays when the XML fails, and the XML stays when the CSV fails. The menu identity pin of `tests/guardrails/test_endpoint_catalog.py` moved with a comment that names issue #4933.
- [X] T088 [US6] Publish the file from the portal (FR-055, FR-063, FR-065, FR-068). `HardwareXmlPreset` gets the formats `master-xml` and `csv-master-xml` and the table `REPORT_KINDS`. `Reports.publish` compiles each report within the quota that is left and publishes all of them in one atomic step. `ReportDownload` serves `csv_download` and `xml_download` with the same pin, checked path, and size limit. The route accepts `format=xml` and answers `application/xml`. A failed report sets the output to `failed` and publishes none.
- [X] T089 [US6] Add the controls to the page (FR-066): two output options, the **Download combined XML** link, and `setReportLinks`, which also restores the links after a reload. The table stays for the outputs that hold the CSV. Ten browser tests cover the options, the link, the failed output, the other outputs, the pair, and a reload. The WebSocket structure pin moved from (149, 295, 917) to (149, 296, 920) with a comment that names issue #4933.
- [X] T090 [US6] Bring every function of the new module to a cyclomatic complexity of 10 or less. The first run of the complexity gate found three functions at 16, 14, and 11. `XmlWriter.Space`, `MasterXmlBuilder.Entry.of`, and `MasterXmlBuilder._counts` took the branches. The event log keeps tuples, so the verifier has no JSON round trip.
- [X] T091 [US6] Test the file. The unit and property tests (`test_hardware_master_xml.py` with 169 cases, `test_hardware_master_xml_properties.py` with 12 tests that generate hostile text, and `test_ws_hardware_master_xml.py` with 49 cases) cover the exact form of the document, each refusal, the character rules, namespaces, size, the exporter on the disk, the finish step, the quota to the byte, the download, and a restart. The integration tests run the real CLI flow and the real portal routes with fake Mist calls and fake shells, and they compare each embedded reply with its saved file. The log of a failed report carries a sentence that holds no data of a reply.
- [X] T092 [US6] Prove that the tests can fail. A run of 52 small faults in a copy of the tree (the character escapers, the DTD refusal, the depth limit, the white space rules, the sort, the verifier checks, the exporter, the CLI step, the finish step, the route, the page, and the template) was caught by the tests for 45 faults at the first run. Seven faults were not caught: the `xml:space` rule in two places, the case folding at the three sort levels, the byte limit for multi-byte text, and the numbered name of the XML file. Each now has a test that fails without the code, and a second run caught all seven.
- [X] T093 [US6] Check live, read-only, on the one test organization. Result: menu 309 collected 15 of 15 switches and wrote a 105370-byte XML file with 1830 elements, 114 serial numbers, and the same 297 rows in the CSV report. The Multi Site action, with the choice **Combined CSV and XML** in a Playwright browser, published both files and the table showed 297 rows. The download of the XML equals the saved file byte for byte. A second portal run with the choice **One combined XML file** published the XML only, with no CSV link and no table, and the link came back after a reload. The files of the two front ends are canonically equal apart from the run time. Readers that the tool does not use accepted each file: ElementTree (expat), SAX with namespaces, minidom, the standard canonicalizer, libxml2 through `lxml` 6.1.3 with recovery off, `xmlschema` 4.3.2, the .NET `XmlReader` with the schema (0 errors), `XmlDocument`, and LINQ to XML. The canonical form of libxml2 equals the canonical form of the standard library. Each embedded reply equals its saved reply apart from formatting, and the 114 serial numbers equal those of the 15 saved replies. A control run of nine corrupted copies (a control character, a wrong count, a changed serial number, an undeclared prefix, a missing attribute, two roots, no declaration, a truncated file, and a DTD) failed at least one check each, and the two that the .NET reader should catch failed there too. A file that was built offline from the 15 real replies of an older run passes the same checks. The token is in none of 54 files and no log.
- [X] T094 [US6] Document the format and the choices (FR-067): `documentation/ex-hardware-master-xml.md`, the operator guide, the contracts, the quickstart, the research notes, the data model, the plan, the release note, and the generated menu pages.

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
- **Story 6 (Phase 11)**: needs Stories 1, 3, and 5, because it reuses the results, the finish step, and the page. It was added after the first delivery steps, so T066 and T067 cover it.

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
5. Story 6: the master XML (T082 through T094).
6. Polish, live validation, and the pull request.

### Guard Rules

- Run the WebSocket structure guard after every edit of a WebSocket file.
- Add each new file by explicit path before any guard run.
- Commit after each story phase and update the tracking issue.
