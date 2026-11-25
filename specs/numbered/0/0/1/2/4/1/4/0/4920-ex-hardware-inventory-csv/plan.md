# Implementation Plan: EX Hardware Inventory CSV

**Branch**: `feat/4920-ex-hardware-inventory-csv` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Add one command that finds the scope of the Mist credential, runs the fixed command `show chassis hardware detail | display xml | no-more` on every connected EX switch, and writes one CSV report. The command runs as menu 309 and as an output choice of the existing **Collect EX hardware inventory** action on the Multi Site tab.

The plan reuses the working collector of issue #4769. The CLI drives the portal batch service layer, which needs no Flask object. That layer already owns discovery, the status re-check, the typed confirmation, bounded concurrency, and durable artifacts. A new report compiler reads the saved per-switch XML files and builds the CSV. The portal publishes it from the artifact finish step. The CLI writes it through the standard exporter. A scope resolver reads the profile, names the credential type, and chooses organization scope or MSP scope. One setting, `PORTAL_WS_HARDWARE_CONCURRENCY`, limits the open shells for both front ends. All new code lives in one new package, `src/operations/exporting/ex_hardware_inventory/`, plus narrow edits to existing files.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`)

**Primary Dependencies**: `mistapi` 0.64.x for REST, the owned WebSocket transport that issues #4259 and #4769 already use (no new transport), Flask for the portal only, and the standard `xml.etree.ElementTree` and `csv` modules. No new dependency.

**Storage**: Files under `data/`. The CLI report goes through `DataExporter.write_with_format_selection` with the CSV format forced, so the SQLite and ArangoDB and Redis backends also receive the rows. The portal keeps its durable run folder under `data/websocket-streams/<run id>/`.

**Testing**: pytest with mocked Mist responses and a fake shell: unit tests, integration tests, contract tests for the reused path, Playwright for the tab, and the repository guards. A live read-only smoke test runs on one organization.

**Target Platform**: Windows 11, macOS, and Linux, and the Podman container.

**Project Type**: A menu operation and a portal feature in an existing repository.

**Performance Goals**: The open shells stay at or below the limit of 1 through 5. The report compile step is linear in the number of hardware items. A report of 1000 switches stays under the 64 MiB output limit.

**Constraints**: At most 1000 targets in one batch. At most 1 MiB for one saved reply. At most 64 MiB of saved output for one portal run. Shared admission allows 5000 requests an hour for each credential. Functions stay at 25 lines or fewer, take 5 parameters or fewer, and have 5 blocks or fewer. A class has 5 methods or fewer. A module has 5 top-level definitions or fewer.

**Scale/Scope**: One organization with up to 1000 connected EX switches in one batch. An MSP with many organizations in the CLI.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Evidence in this plan |
|-------------------|------|-----------------------|
| I. Five-item rule | No directory passes five children. No method is added to a class at its limit. | The new package is the fourth child of `src/operations/exporting` (now three). Its root holds one module and three subpackages. Each subpackage holds five modules or fewer. `websocket_streams` stays at four children. `web/services/operations` stays at five modules, and only existing files change. The WebSocket structure guard runs after each edit. |
| II. Class-based, no wrappers | Behavior lives in named classes. | Each unit is a class with a subject name: `ScopeResolver`, `HardwareXmlFlattener`, `ReportBuilder`, `CsvRenderer`, `OrganizationBatchRun`, `ReportHook`, and the others in the layout below. |
| III. Safety first | Typed confirmation, safe input, early validation, no secret in output. | Menu 309 reads `RUN <count> TARGETS` through `InputUtils.safe_input`. End of input and an interrupt cancel. The command is fixed and read-only. The decoder of issue #4769 rejects a reply that holds a credential. |
| IV. Full deployment pipeline | Local gates, explicit paths, rebase, push, pull request, CI. | The tasks run each gate and commit explicit paths. The agent does not merge. The owner merges and deploys. |
| V. Logging | ASCII only, structured, no secret. | New modules use standard logging with `%s` values, which the structured front end formats. No log line holds the token or an address. |
| VI. Inline comments | Every executable line carries a comment. | A task audits each new file. |
| VII. Action logging | `info` before and `debug` after each action. | Each client call, file read, write, and transform logs both lines. |
| Mist transport | Every REST call uses a working `mistapi` method. | See the Mist Cloud gate below. |
| Output backends | Collected data goes through `DataExporter`. | The CLI uses it. The portal keeps its existing durable artifact writer for run folders, as issue #4769 does. |
| Database keys | Define the natural key before the operation. | `ENDPOINT_PRIMARY_KEY_STRATEGIES` gets `ExHardwareInventory` as `composite_pk` on `org_id`, `device_id`, and `item_path`. |
| Data directory | Product output goes to `data/`. | The CLI report and the run folders go under `data/`. |
| Adding menu operations | Follow the seven steps. | Steps 1 to 4, 6, and 7 apply. Step 5 (README table) does not. See Complexity Tracking. |

For repository structure and generated files:

- The commit subjects and the pull request title use the Conventional Commit form.
- The change adds only its own record under `specs/numbered/` and one fragment under `changelog.d/`.
- The plan records existing folder debt and a separate remediation action in Complexity Tracking.
- Product output stays under `data/`. Test output uses `tmp_path`.

For a feature that uses Juniper Mist Cloud:

- REST methods, all through `mistapi`: `getSelf` (`mistapi.api.v1.self.self.getSelf`), `listMspOrgs` (`mistapi.api.v1.msps.orgs.listMspOrgs`), and, through the existing pickers, `listOrgSites`, `listSiteDevices`, and `listSiteDevicesStats`.
- The shell session trigger is the existing `UtilityTriggerTable.shell_request` path. The contract test `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py` proves that it equals the SDK `createShellSession` request. This plan does not change it.
- The feature adds no owned WebSocket transport. It reuses the transport that the constitution already allows. The contract tests `test_ws_sdk_contract.py` and `test_websocket_transport_constitution.py` stay unchanged and must pass.
- New tests cover the scope resolver against the failure paths (HTTP 401, 403, 429, 5xx, and a transport fault), the report compiler against a reply with a credential, and the redaction of every new log line.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      cli-menu.md
      report-csv.md
      portal.md
    checklists/
      requirements.md
      security.md
      report.md
```

### Source Code (repository root)

```text
src/operations/exporting/ex_hardware_inventory/
  __init__.py
  operation.py              # ExHardwareInventoryReport, OrganizationPlan, RunCollector: menu 309 flow
  console.py                # HardwareConsole: the console lines and the typed phrase
  scope/
    __init__.py
    profile.py              # CredentialProfile, ProfileReader (getSelf, status checked)
    resolver.py             # OrganizationRef, ScopeDecision, ScopeError, ScopeResolver
    session.py              # AdmissionBinding, SdkErrorMute
  report/
    __init__.py
    flatten.py              # HardwareXmlFlattener, FlattenedDevice
    columns.py              # ReportColumns, CellGuard
    builder.py              # TargetResult, ReportBuilder
    csv_file.py             # CsvRenderer, CsvVerifier
    export.py               # ReportExporter (DataExporter, file check)
  run/
    __init__.py
    batch.py                # BatchPreview, BatchRunResult, BatchStack, OrganizationBatchRun
    watch.py                # BatchWatcher (poll and stop), RunFolder (read outcomes and replies)
    publisher.py            # ReportHook (portal finish step)
    routing.py              # ScopeRouter, ScopeAwareTargets, ScopeAwareChecker (portal MSP)
```

Existing files with narrow edits (no new method in a class at its limit, no new module in a full directory):

```text
MistHelper.py                                                     # import and MenuEntry 309
src/foundation/support/utils/operation_registry.py                # entry 309
src/foundation/support/refactors/endpoint_primary_key_strategies.py   # ExHardwareInventory
src/mist/realtime/websocket_streams/live/sessions/settings.py     # hardware_concurrency
src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py   # csv format
src/mist/realtime/websocket_streams/web/services/operations/artifacts.py     # finish step hook
src/mist/realtime/websocket_streams/web/services/operations/sessions.py       # limits, scope in preview
src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py    # scope-aware collaborators
src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py          # csv download branch
src/mist/realtime/websocket_streams/web/blueprint/responses/download.py       # csv response
src/mist/realtime/websocket_streams/web/templates/websockets_page.html        # output choice, link
src/mist/realtime/websocket_streams/web/static/websockets.js                  # choice, download, default
```

Tests:

```text
tests/unit/ex_hardware_inventory/
  support/                  # synthetic reply builders and fake sessions
  report/                   # flatten, builder, csv file, export
  scope/                    # profile, resolver, session helpers
  run/                      # batch run, publisher, routing
  test_hardware_operation.py
tests/integration/ex_hardware_inventory/   # CLI flow with a fake batch service
tests/unit/websocket_streams/web/          # csv preset, finish step, download
tests/unit/websocket_streams/live/sessions/   # the new setting in test_ws_stream_settings.py
tests/e2e/websockets_tab/                  # the new output choice
```

Updated expectations: `tests/guardrails/test_endpoint_catalog.py` (count and digest), `tests/unit/test_menu_entry_metadata.py` (count and entry), `tests/unit/ap_warning_report/test_menu.py` (last menu), and `tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py` (pinned counts, only if an edit changes them).

Documentation and release: `documentation/operator-guide.md`, `deploy/.env.example`, `documentation/sample.env`, `.github/copilot-instructions.md` (two count lines), the generated menu pages, and `changelog.d/issue-4920-ex-hardware-inventory-csv.md`.

**Structure Decision**: One new package under `src/operations/exporting/`, the same parent that menu 307 used. The `report` subpackage has no WebSocket dependency, so the portal finish step can import it without a cycle. The `run` subpackage depends on the WebSocket service layer. Every `__init__.py` stays empty. The portal changes stay inside existing files and add no new method to a class at its limit.

## Implementation Outline

1. **Foundation**: the setting, the registry entry, the natural-key strategy, the synthetic reply builders, and the report compiler.
2. **Story 1**: the CLI run for one organization.
3. **Story 2**: scope detection and the MSP loop in the CLI.
4. **Story 3**: the Multi Site output choice, the finish step, the download, and MSP scope in the portal.
5. **Story 4**: the concurrency setting in the page and the preview.
6. **Story 5**: outcome rows, cancellation, spreadsheet safety, and the file check.
7. **Polish**: documentation, generators, guards, the full local gates, and the live smoke test.

## Complexity Tracking

Existing debt that the change touches or avoids. None of it is new debt.

| Item | Kind | Why it stays | Remediation |
|------|------|--------------|-------------|
| WebSocket files at their structure limits (`artifacts.py`, `sessions.py`, `hardware_xml.py`) | Grandfathered | The portal finish step and the preset live there. A parallel preset would copy the collector. | Edits add no method and no module. The capacity work of issue #4259 (task T039) stays separate. |
| `src/mist/intelligence/reports` holds 18 children, and `src/operations` holds 5 | Grandfathered | The change adds no child there. | Issues #3824 and #4168 track the baseline. |

New design that needs a reason.

| Item | Why it is needed | Simpler alternative rejected because |
|------|------------------|--------------------------------------|
| The CLI binds the organization to the shared request ledger through the session adapter | Shared admission rejects a site request when the ledger has no organization. Nothing sets one. | A context variable does not reach the batch worker threads. Editing the admission module is a separate issue with its own owner. A follow-up issue records the gap. |
| The portal finish step imports the `report` subpackage from `operations` | It keeps the `websocket_streams` package at four children. | Placing the package under `websocket_streams` uses its last free slot. |
| No README menu table for menu 309 | Issue #4916 removed menu text from the README at the owner request. The constitution step is stale. | Adding the table undoes the owner decision. A follow-up can amend the constitution. |
| A second preview for each organization in a long CLI run | A preview expires after 300 seconds. | Reusing the first preview fails for a long MSP run. |

## Risks and Mitigations

- **Guard limits on edited WebSocket files**: run the structure guard after each edit. If an edit does not fit, move the logic into the new package and keep the edit to one call.
- **MSP scope in the portal**: it needs scope-aware collaborators. If the structure limits block the wiring, the plan delivers the CLI MSP run and the portal CSV for organization scope, and it reports the gap in the pull request.
- **Real replies differ from the tracked fixtures**: tests use synthetic replies with the real shape. A local check runs the flattener on retained real files and prints counts only.
- **Request volume**: each site costs at least three reads. The pull request notes the cost for large MSPs.
