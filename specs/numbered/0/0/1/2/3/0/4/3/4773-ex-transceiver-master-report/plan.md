# Implementation Plan: EX Transceiver Master Report

**Branch**: `feat/4773-ex-transceiver-master-report` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4773 and the numeric route `specs/numbered/0/0/1/2/3/0/4/3/4773-ex-transceiver-master-report/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Add CLI menu 310 and an optional portal checkbox. Both collect the EX switch hardware with the existing fixed read-only command. Both write one transceiver master CSV from the saved native replies. The collector, the shell confirmation, the connected-only filter, and the offline exclusion stay as they are in menu 309. The XML reply is the row source when it is valid. A JSON-only reply yields the same rows through a new JSON reader. The new code lives in one new package, `src/operations/exporting/ex_transceiver_master/`. Existing files change only where the new behavior needs a narrow edit.

## Technical Context

**Language/Version**: Python 3.15 or newer. The repository instruction file gives this requirement in its section Language and environment.

**Primary Dependencies**: `mistapi==0.64.1` as the only Mist REST interface (`requirements.txt`, line 129). Flask serves the portal. The standard `json`, `csv`, `xml.etree.ElementTree`, and `hashlib` modules are used. No new dependency.

**Storage**: CLI output goes under `data/`. The portal keeps each run folder under `data/websocket-streams/<run id>/`. The `.gitignore` file ignores `data/` (line 95) and `/test-artifacts/` (line 107).

**Testing**: pytest with mocked Mist responses, fake shells, and fake batch services. Playwright runs the browser checks in `tests/e2e/websockets_tab/`. The repository guard tests run in `tests/guardrails/`.

**Target Platform**: Windows 11, macOS, and Linux. The Podman container runs the same code. No container change is part of this feature.

**Project Type**: A new menu operation, a portal option, and a shared report package in an existing repository.

**Performance Goals**: The shell count stays at or below `PORTAL_WS_HARDWARE_CONCURRENCY`, which has a range of 1 through 5 (`src/mist/realtime/websocket_streams/live/sessions/settings.py`, line 66). Report compile time grows linearly with the number of items.

**Constraints**: At most 1000 targets in one batch. At most 1 MiB for one saved reply (`hardware_xml.py` `Rules.MAX_XML_BYTES`). At most 64 MiB of output for one run (`report/export.py` `LIMIT_BYTES`). Functions have five parameters or fewer and 25 lines or fewer, as `AGENTS.md` requires.

**Scale/Scope**: One organization with up to 1000 connected EX switches in one batch. The CLI runs each organization in turn, as menu 309 does.

## Constitution Check

*Gate: passes before research and passes after design. The Principle I entry records existing debt and a separate remediation action.*

| Principle or rule | Gate | Evidence in this plan |
|-------------------|------|-----------------------|
| I. Five-item rule | No new direct child under a noncompliant parent. New feature code enters a compliant nested package. | The new package `src/operations/exporting/ex_transceiver_master/` is the fifth directory child of `src/operations/exporting/`. Its guard count is 5, and it excludes `__init__.py`, as the repository guard does. It holds four modules. No new test folder is created. New test cases append to existing modules. Existing debt is recorded in Complexity Tracking. |
| II. Class-based architecture | Behavior lives in named classes. No wrapper function. | Classes: `NativeJsonFlattener`, `TransceiverRowBuilder`, `TransceiverReportCompiler`, `TransceiverReportExporter`, `TransceiverFormatPrompt`, `ExTransceiverMasterReport`, and `HardwareRunSteps` (existing file, extracted class). |
| III. Safety first | Typed confirmation, safe input, early validation, no secret in output. | The phrase `RUN <count> TARGETS` stays unchanged. Each new prompt uses `InputUtils.safe_input`. The JSON reader rejects non-finite numbers. The existing decoder rejects credential text before a reply is saved. |
| IV. Full deployment pipeline | Local gates, explicit paths, rebase, push, pull request, CI, squash merge, verified image. | `tasks.md` T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. The agent does not merge without authorization. |
| V. Observability | ASCII logs, structured logs for new services, no secret in logs. | The new modules use the standard logging module with `%s` values. No new service starts. Log lines carry counts and states, never reply text. |
| VI. Inline comments | Each executable line of generated code carries an inline comment. | `tasks.md` T029 audits each new and touched line. |
| VII. Action logging | An info line before each action and a debug line after it. | Each prompt, file read, file write, flatten call, and compile call has both lines. |
| Mist REST | Each REST call uses a working mistapi method. | The feature adds no REST call. Existing calls: `getSelf` (`scope/profile.py` line 97), `listMspOrgs` (`scope/resolver.py` line 118), `listOrgSites` (`intake/pickers/resources.py` line 77), `listSiteDevices` (`intake/pickers/devices.py` line 102), and `listSiteDevicesStats` (`intake/pickers/devices.py` line 43). |
| Owned WebSocket transport | Only an approved flow may own a transport. The contract tests pin the transport. | The shell path is the existing owned transport (`live/transport/endpoint.py` line 117). This feature does not change it. The existing contract tests stay unchanged. |
| Output backends | Collected data goes through `DataExporter.write_with_format_selection`. | The CLI report calls `write_with_format_selection` with the CSV format forced (`report/export.py` line 81). The portal keeps its atomic run-folder writer, as menu 309 does. Complexity Tracking records this pattern. |
| Database keys | The natural key is defined before the operation. | `ExTransceiverMaster` is a `composite_pk` on `org_id`, `device_id`, and `item_path`. The key is added before menu 310 runs (FR-028). |
| Data directory | Product output goes to `data/`. Test evidence goes to `test-artifacts/`. | The CLI writes `data/ExTransceiverMaster_<UTC time>.csv`. The portal writes under `data/websocket-streams/`. Failure screenshots go to `test-artifacts/` (FR-025). |
| Container security | No container change. A test container joins the compose group only when started. | No test container is started by this feature. |
| File paths | Paths use the path library. No hand-built separator. | New code uses `pathlib.Path`. The run folder code keeps its existing checked path logic. |
| Zscaler and proxy | Container builds and pushes run in GitHub Actions. | T-MERGE waits for `container-build.yml`. No local `podman push` occurs. |
| Adding a menu operation | The seven steps of the constitution. | Step 1: mistapi functions are reused, and no endpoint is added. Step 2: the key is added. Step 3: the native XML walker is reused, and the JSON reader is new (Complexity Tracking). Step 4: the CLI uses `write_with_format_selection`. Step 5: one README row is added (D-15). Step 6: one changelog fragment is added. Step 7: the full pipeline runs. |
| Testing skip list | Menu 310 is `resource_intensive`, so `--test` and `--testinteractive` skip it. | `OperationRegistry` decides the category (FR-027). |
| Security findings | Fix over suppress. No new suppression comment. | `tasks.md` T031 runs bandit on the new package. Any finding is fixed, not suppressed. |
| Documentation | README, the operator guide, and the generated menu reference change with behavior. | `tasks.md` T024 to T027 change each document. |
| Audience standard | Plain words for junior engineers. | Operator-facing text in the menu and the portal uses short sentences and no jargon. |
| Escalation to a spec | A change that touches three or more files or two or more classes needs a spec. | This record is the spec. |
| Multi-agent git | One pull request for `MistHelper.py`, label rules, file overlap check. | No open pull request changes `MistHelper.py` (checked 2026-11-26). The branch carries the label `feature`, the scope `web-portal`, and the status `in-progress`. Open draft pull request #4813 changes `data_exporter.py`, which this plan does not edit. |

For repository structure and generated files:

- The pull request title uses the Conventional Commits form `feat(web-portal): add EX transceiver master report and CLI collection`.
- The change adds only its own record under `specs/numbered/` and one fragment under `changelog.d/`.
- The new package adds no direct child to a noncompliant parent. Complexity Tracking records the existing folder debt.
- Product output stays under `data/`. Test output uses `tmp_path` or `test-artifacts/`.

For a feature that uses Juniper Mist Cloud:

- REST methods are existing mistapi functions listed above. No new REST method is added.
- The shell path uses the existing owned transport. The matching utility path is `/api/v1/sites/{site_id}/devices/{device_id}/shell` (`live/runners/utility/triggers/table.py` line 103). The OpenAPI file defines the operation `createSiteDeviceShellSession` at line 30503 of `documentation/mist-api-openapi31yaml.yaml`.
- The existing contract tests remain the proof for the owned transport. Their names appear in `spec.md`.
- New tests cover output rows, failure handling, formula safety, and redaction (FR-024, FR-017, FR-010).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/0/4/3/4773-ex-transceiver-master-report/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      cli-menu-310.md
      portal.md
      transceiver-csv.md
      native-json.md
    checklists/
      requirements.md
      report.md
      security.md
```

### Source Code (repository root)

```text
src/operations/exporting/ex_transceiver_master/
  __init__.py          # Package marker and one-line purpose
  json_reply.py        # NativeJsonFlattener: native JSON reply to item fields
  rows.py              # TransceiverRowBuilder: transceiver, no-transceiver, and outcome rows
  report.py            # TransceiverReportCompiler and TransceiverReportExporter
  operation.py         # TransceiverFormatPrompt and ExTransceiverMasterReport (menu 310)
```

The package adds one direct child to `src/operations/exporting/`. The package holds four modules and one `__init__.py` file.

## Architecture

```text
Menu 310 or portal checkbox
  -> scope and preview (existing: ScopeResolver, WebSocketBatchService.preview)
  -> confirmation (existing: typed phrase, format and commands shown)
  -> shell batch (existing: StreamSessionManager, one shell for each target)
  -> saved native files (existing: run folder, XML and JSON files)
  -> TransceiverRowBuilder (new: XML first, JSON only when XML is absent)
       -> HardwareXmlFlattener (existing) or NativeJsonFlattener (new)
  -> TransceiverReportCompiler (new: CsvRenderer and CsvVerifier, existing)
  -> CLI: TransceiverReportExporter -> DataExporter.write_with_format_selection (existing)
  -> Portal: artifact finish step publishes hardware/transceiver-master.csv (existing publisher)
```

Caution: the portal finish step publishes all reports in one step. A failed transceiver report blocks the other reports. The publisher must compile the new report before it commits any file.

## File-by-File Change Map

| Path | Action | Requirements | Purpose |
|------|--------|--------------|---------|
| `src/operations/exporting/ex_transceiver_master/__init__.py` | Add | FR-001 | Package marker. |
| `src/operations/exporting/ex_transceiver_master/json_reply.py` | Add | FR-012 | Read a native JSON reply into the same item fields as the XML walker. |
| `src/operations/exporting/ex_transceiver_master/rows.py` | Add | FR-007 to FR-017 | Build transceiver, no-transceiver, and outcome rows. Apply the formula guard. |
| `src/operations/exporting/ex_transceiver_master/report.py` | Add | FR-018, FR-019 | Compile CSV bytes, check them, and write the CLI file. |
| `src/operations/exporting/ex_transceiver_master/operation.py` | Add | FR-001, FR-005, FR-026 | Format prompt and menu 310 flow. |
| `changelog.d/issue-4773-ex-transceiver-master-report.md` | Add | Release note | One `Added` bullet for issue #4773. |
| `MistHelper.py` | Modify | FR-001, FR-027 | Import the new class after line 580. Add the `310` menu entry after the `309` entry at line 4836. |
| `src/foundation/support/utils/operation_registry.py` | Modify | FR-027 | Add `"310"` with category `resource_intensive` after `"309"` at line 537. |
| `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | Modify | FR-028 | Add `ExTransceiverMaster` after `ExHardwareInventory` at line 3506. |
| `src/operations/exporting/ex_hardware_inventory/operation.py` | Modify | FR-029 | Move the four step methods into a public `HardwareRunSteps` class. Pass the output format to `OrganizationPlan.build`. Let `RunCollector` accept any result sink. |
| `src/operations/exporting/ex_hardware_inventory/console.py` | Modify | FR-004, FR-005 | `confirm` prints the command list that its caller passes. |
| `src/operations/exporting/ex_hardware_inventory/run/batch.py` | Modify | FR-005 | `OrganizationBatchRun` takes the output format and builds its request per instance. |
| `src/operations/exporting/ex_hardware_inventory/run/watch.py` | Modify | FR-006, FR-011, FR-012 | `RunFolder` reads the native file of each requested format. |
| `src/operations/exporting/ex_hardware_inventory/report/builder.py` | Modify | FR-011, FR-012, FR-014 | `TargetResult.json_text`. `RowFactory.classify` accepts a JSON reply. `FailureReasons.exact` reads each requested format. |
| `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` | Modify | FR-021, FR-030 | Add the `transceiver_csv` boolean to the selection, the parser, and the preview values. |
| `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | Modify | FR-020, FR-021 | Add `transceiver_csv` to `BatchPreviewRecord`, the start output, and the summary payloads. |
| `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | Modify | FR-020, FR-023 | Add `TRANSCEIVER_NAME`. Extend the finish gate and the compile builders. Add a download reader with a file-name prefix. |
| `src/mist/realtime/websocket_streams/web/blueprint/responses/download.py` | Modify | FR-023 | Add the `transceiver-csv` output and list it in the error text. |
| `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` | Modify | FR-002, FR-022 | Add the checkbox and the download link, with stable test identifiers. |
| `src/mist/realtime/websocket_streams/web/static/websockets.js` | Modify | FR-021, FR-022 | Bind the checkbox, send the field, show the summary line, and show the download link. |
| `documentation/operator-guide.md` | Modify | FR-001, FR-002, FR-005 | Add one section for the portal checkbox and menu 310. Keep the sentence that starts "Menu 309 in the CLI needs no setting". |
| `documentation/menu_reference.md` | Regenerate | FR-027 | Run `python scripts/generate_menu_wiki.py`. |
| `documentation/wiki/Menu-Reference.md` | Regenerate | FR-027 | Run `python scripts/generate_menu_wiki.py`. |
| `.github/copilot-instructions.md` | Modify | FR-027 | Update the operation count at line 11 and the `resource_intensive` row at line 224. |
| `README.md` | Modify | FR-001 | Add one row to the task table after line 40. |
| `tests/unit/export/test_pk_strategies.py` | Modify | FR-028 | Add one case for `ExTransceiverMaster`. |
| `tests/unit/test_menu_entry_metadata.py` | Modify | FR-027 | Change the expected count at line 10 to 310. Add `("310", False)` after line 45. |
| `tests/guardrails/test_endpoint_catalog.py` | Modify | FR-029 | Re-pin the `MistHelper.py` identity after the edit. The pin spans lines 546 to 548. |
| `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` | Modify | FR-012 | Add parity and malformed-reply cases for the JSON reader. |
| `tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py` | Modify | FR-007 to FR-015 | Add rows, no-transceiver rows, outcome rows, and source precedence. |
| `tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py` | Modify | FR-017, FR-018 | Add the transceiver CSV check and the formula guard cases. |
| `tests/unit/ex_hardware_inventory/report/test_hardware_export.py` | Modify | FR-019 | Add the CLI write cases: forced CSV, unique name, and removal after a failed check. |
| `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` | Modify | FR-005, FR-006 | Add the requested format case and the native read cases. |
| `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | Modify | FR-001, FR-005, FR-024, FR-026, FR-029 | Add menu 310 prompt, cancel, command list, and log cases. |
| `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` | Modify | FR-005, FR-009, FR-011, FR-012, FR-016 | Add the full CLI flow for XML, JSON, and both. |
| `tests/unit/websocket_streams/web/test_ws_web_services.py` | Modify | FR-021, FR-030 | Update the exact preview values at line 662. Add parser cases. |
| `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` | Modify | FR-020, FR-023, FR-030 | Update the exact download error text at line 410. Add publication, manifest, ZIP, and download cases. |
| `tests/e2e/websockets_tab/test_websockets_page.py` | Modify | FR-002, FR-021, FR-022, FR-025 | Add checkbox, invalidation, download, and artifact path cases. |

## Dependencies

- Runtime: no new package. Python 3.15 and `mistapi==0.64.1` stay unchanged.
- Test: pytest, Flask test client, Playwright, and the existing guard tests.
- Quality: ruff, black, mypy, pylint, vulture, bandit, pydocstyle, interrogate, radon, and `misthelper-devtools` commands (`symbol-diff`, `ste-linter`, `complexity-gate`, and `test-quality-analyzer`).
- Coordination: open draft pull request #4813 changes `src/operations/exporting/export/data_exporter.py` and CSV carriage-return handling. Rebase after #4813 lands, then rerun the CSV tests.
- Coordination: open draft pull request #4208 changes `web_portal/app.py` and `web_portal/templates/base.html`. This plan does not edit those files.

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| Live transceiver item names differ from the synthetic fixtures. | Rows are missing on a live switch. | Stop the live run and report the switch. Add the observed name to the fixture set only after an authorized capture. Research U-1 records the gap. |
| The `detail` option is refused on an older software release. | The switch gets a failed outcome row. | The outcome row shows the failure. Research U-3 records the release risk. No command change occurs. |
| JSON empty leaves use a shape the fixtures do not show. | A JSON-only row has an empty cell where XML has a value. | The reader accepts both `[{"data": ""}]` and `[{}]`. Tests cover both. Research U-4 records the gap. |
| `MistHelper.py` edit conflicts with another pull request. | The rebase fails. | No open pull request changes the file on 2026-11-26. Merge the branch quickly. Use the symbol gate. |
| The JSON reader and the XML walker diverge over time. | JSON-only rows differ from XML rows. | Parity tests compare both readers on the same synthetic model (SC-001). |
| Existing exact-text tests fail after the edit. | The gate is red. | T-LOCAL-GATES runs them. The two known assertions are updated in the same change (`test_ws_web_services.py` line 662 and `test_ws_hardware_csv.py` line 410). |
| Menu count pins fail after the edit. | The gate is red. | The count pins in `test_menu_entry_metadata.py` and `test_endpoint_catalog.py` update in the same change. |
| The test-quality ratchet reports a new finding. | The gate is red. | Fix the test. Do not change `.github/test-quality-baseline.json`. Issue #4783 tracks the two existing findings. |
| The portal checkbox is hidden until the shell setting is on. | An operator cannot see the checkbox. | This is the existing lock. The operator guide states the setting (`PORTAL_WS_ENABLE_SHELL=true`). |
| A large run exceeds the 64 MiB limit. | No file is written. | The existing check refuses the file and prints one sentence. The operator uses the CLI with a smaller organization scope. |
| A shared checkout is changed by another agent. | Lost work. | Use a dedicated worktree. Do not run `git checkout` in a shared checkout. Do not run `git clean` or `git reset --hard`. |

Warning: a failed rebase or a force push can remove other agents' commits. Use `--force-with-lease` only on the feature branch, after the owner agrees.

## Rollback Steps

1. Revert the squash commit with a new pull request. Do not force-push `main`.
2. After the revert merges, pull `main` and check that `python MistHelper.py --menu 310` is no longer registered.
3. Redeploy the previous container image. Choose the image tag by its UTC version stamp in `YY.MM.DD.HH.MM` form.
4. Delete only the new files that a run created. The CLI files match `data/ExTransceiverMaster_*.csv`. The portal files match `hardware/transceiver-master.csv` in a run folder.

Caution: deleting a run folder removes its native replies. Delete only the transceiver file when the native replies still matter.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| The JSON reader does not use `DataProcessingUtils.flatten_dict`. | The native JSON keeps lists of leaf objects with a `data` key. The existing helper joins nested keys with an underscore and gives list items index keys (`data_processing_utils.py` lines 36 and 37). | The helper would produce different item paths and field names from the XML walker. The XML and JSON rows would not match (SC-001). |
| The portal publishes the new file through its artifact writer, not through `DataExporter`. | The portal publishes all reports in one atomic step. `DataExporter` does not write atomically (`report/csv_file.py` and `report/export.py` module notes). | A separate write would break the atomic step, and a failed write could leave a partial report. |
| The five-item rule is already broken in `tests/unit/ex_hardware_inventory/report/` (seven entries), `tests/unit/ex_hardware_inventory/run/` (six entries), and `src/operations/exporting/ex_hardware_inventory/report/` (six entries). | Existing debt. The repository guard counts these folders above five. | New tests append to the existing modules. No new folder is added to a noncompliant parent. The remediation action R-1 below tracks the existing debt separately. |
| Remediation action R-1 | Separate from this feature. | Move the support helpers and split the report folder in a later issue. This feature does not perform the move. |

## Implementation Outline

1. Create the package and the shared readers (T003 to T008).
2. Extend the existing CLI collection path (T009 to T012).
3. Add menu 310 and its registration (T013 to T017).
4. Extend the portal path (T018 to T023).
5. Update the docs, counts, and fragment (T024 to T027).
6. Run the audits and the live check (T028 to T034), then the final tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
