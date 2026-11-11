# Tasks: EX Hardware XML Collection

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/0/3/4/4769-ex-hardware-xml/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), `design/research.md`, `design/data-model.md`, `design/contracts/ex-hardware-xml.md`, and `design/quickstart.md`.

**Organization**: Tasks follow the three user stories in the specification. Tests precede each story's implementation.

## Phase 1: Setup

**Purpose**: Prepare the isolated worktree and verify its required project configuration.

- [X] T001 Create and activate the worktree virtual environment with Python 3.15.2 by running `scripts/bootstrap_worktree.py`.
- [X] T002 Verify and update only required ignore patterns in `.gitignore`, `.dockerignore`, `ops-portal/eslint.config.*`, and `ops-portal/package.json` when the detected project setup requires them.

## Phase 2: Foundational

**Purpose**: Verify shared shell-session contracts before feature changes.

- [X] T003 Run `tests/contract/websocket_streams/test_ws_sdk_contract.py` and `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py` in the Python 3.15.2 environment.

## Phase 3: User Story 1 - Collect Hardware Inventory Across an Organization (Priority: P1)

**Goal**: Give operators a dedicated preset that previews and runs all EX targets across all sites in the configured organization.

**Independent Test**: Use mocked services and a fake browser to confirm that the preset previews every eligible EX target, fixes the server command, defaults to XML, and starts the batch through existing session safeguards.

### Tests for User Story 1

- [X] T004 [P] [US1] Add failing service tests for the `ex-hardware-xml` preset, its fixed commands, all-organization scope, XML default, and format enum in `tests/unit/websocket_streams/web/test_ws_web_services.py`.
- [X] T005 [P] [US1] Add a failing browser test for the dedicated action, XML default, JSON and BOTH choices, preview, and start request in `tests/e2e/websockets_tab/test_websockets_page.py`.

### Implementation for User Story 1

- [X] T006 [P] [US1] Implement the server-owned preset, fixed preview commands, and format snapshot in `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` and `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`.
- [X] T007 [P] [US1] Add the dedicated preset and format controls to `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` and `src/mist/realtime/websocket_streams/web/static/websockets.js`.
- [X] T008 [US1] Run the focused service and browser tests for `tests/unit/websocket_streams/web/test_ws_web_services.py` and `tests/e2e/websockets_tab/test_websockets_page.py`.

## Phase 4: User Story 2 - Review Safe Targeting and Run Outcomes (Priority: P1)

**Goal**: Restrict the action to unique EX devices and retain explicit outcomes for unavailable, failed, and cancelled targets.

**Independent Test**: Mock paginated sites and devices, virtual-chassis records, non-EX devices, setup failures, and cancellation. Confirm the preview and manifest contain every required target outcome.

### Tests for User Story 2

- [X] T009 [US2] Add failing tests for complete pagination, EX-only selection, virtual-chassis deduplication, offline or unavailable targets, setup 4xx and 5xx failures, and cancellation in `tests/unit/websocket_streams/web/test_ws_web_services.py` and `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.

### Implementation for User Story 2

- [X] T010 [US2] Enforce complete organization-site discovery, EX eligibility, stable target deduplication, and explicit per-target failure or cancellation outcomes in `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py`, `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`, and `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py`.
- [X] T011 [US2] Run the focused targeting, setup-failure, and cancellation tests in `tests/unit/websocket_streams/web/test_ws_web_services.py`.

## Phase 5: User Story 3 - Reliably Save and Download XML and JSON (Priority: P2)

**Goal**: Validate separate native XML and JSON replies and save distinct selected files with safe names.

**Independent Test**: Feed representative nested and repeated XML through mocked shell output. Confirm XML, JSON, and BOTH output, UTF-8 handling, namespace and attribute preservation, safe names, atomic failures, quotas, and archive contents.

### Tests for User Story 3

- [X] T012 [US3] Add failing tests for chunked UTF-8 XML, repeated elements, namespaces, attributes and tails, malformed or truncated XML, DTD and entity rejection, secret detection, oversized output, unsafe or duplicate hostnames, missing identifiers, quotas, atomic per-format writes, and archive contents in `tests/unit/websocket_streams/web/test_ws_web_services.py` and `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.

### Implementation for User Story 3

- [X] T013 [P] [US3] Capture the finite shell command's complete raw output and route the hardware preset away from terminal transcript messages in `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` and `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py`.
- [X] T014 [P] [US3] Add safe hostname and device-ID filenames, staged XML and JSON writes, per-file quota accounting, and selected-format ZIP entries in `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` and `src/mist/realtime/websocket_streams/intake/start_request/models.py`.
- [X] T015 [US3] Run the focused XML parser, format, secret, quota, and archive tests in `tests/unit/websocket_streams/web/test_ws_web_services.py`.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Document the operator workflow, validate the full change, and preserve the separate live-test handoff.

- [X] T016 [P] Update `documentation/operator-guide.md` with the preset, output choices, scope, and safe use notes. Keep `README.md` unchanged because other open pull requests own it.
- [X] T017 [P] Add the unique release note `changelog.d/issue-4769-ex-hardware-xml.md`.
- [X] T018 Run all affected WebSockets unit, contract, integration, and end-to-end tests, plus applicable lint, type, complexity, security, documentation, and syntax gates in the Python 3.15.2 environment.
- [X] T019 Run `speckit.analyze` on `spec.md`, `plan.md`, `tasks.md`, and the implementation evidence. Resolve all actionable inconsistencies in the feature-owned files.
- [X] T020 Commit explicit feature paths with a Conventional Commit subject, `Closes #4769`, and `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`. Do not push or open a pull request.
- [X] T021 After the commit, run the documented test-quality preflight and `test-quality-analyzer --gate --changed-from origin/main` without hiding baseline findings.
- [X] T022 After deployment, validate native XML and JSON files, partial outcomes, offline exclusions, and durable storage. Record anonymized aggregate acceptance results.

### Live Portal Acceptance

The parent verified the deployed portal with 15 online EX targets, 2 offline exclusions, and 60 other-family exclusions.
The batch sent two native commands per target and completed all 15 targets with zero failures.
The independently downloaded ZIP contained 15 XML files and 15 native JSON files.
Every document parsed, and each format pair contained matching hardware serial sets.
The manifest reported `durable=true`, `partial=false`, and 30 files.
The parent found no configured token, password, or secret bytes in the verified output.
Six XML files from a previous run survived container recreation.
The parent retained a host copy of the verified files, manifest, and ZIP.

The feature README row was removed because open pull requests #4619 and #4208 own that file.
The operator guide retains the complete feature documentation.

## Issue #4770 Acceptance Correction

- [X] T023 Replace XML-derived JSON with distinct fixed native commands. BOTH runs XML, then JSON, once each.
- [X] T024 Require current running statistics at preview and dispatch. Explain offline and unknown exclusions and skip changed-status targets.
- [X] T025 Require stable initial CLI readiness and separate per-command captures. Accept only verified Junos routing-engine framing.
- [X] T026 Retain successful format files after another format fails. Record separate format outcomes without false success.
- [X] T027 Preserve native hardware files and partial manifests after session expiry, deletion, and process restart.
- [X] T028 Display the exact confirmation phrase and selected commands. Add regression tests for native format choices and partial failures.
- [X] T029 Complete applicable local gates, commit the explicit paths, and run the test-quality ratchet.
- [X] T030 Reproduce the deployed artifact validation failure through the production collector and anonymized native document fixtures.
- [X] T031 Distinguish credential fields and values from native namespace URLs and hardware descriptions. Keep generic log redaction unchanged.
- [X] T032 Verify real native XML and JSON file bytes through the production collector and artifact writer in a separate diagnostic process.
- [X] T033 Complete repair gates, commit the correction, and repeat the committed-tree test-quality ratchet.

The corrected diagnostic run saved 6,079 XML bytes and 13,584 JSON bytes for one currently connected target.
The saved files matched their native captures. Both parsed successfully, and the durable manifest reported complete outcomes.
Container files and portal workers remained unchanged during this diagnostic process.
These results preceded the complete live portal acceptance above.
Repair validation reported 630 passed and 5 skipped across the WebSockets unit, contract, and page suites.
Ruff, Black, mypy, Bandit, complexity, compilation, and all seven changed Markdown score checks passed.
Symbol comparison reported only the intentional removal of the imported generic `SecretRedactor` name.
An independent process verified both persisted file hashes and parsed both native documents after the collector process ended.
The committed-tree quality preflight passed. The ratchet checked six files and reported zero new findings.

Runtime evidence: The authorized online-target probe returned both native formats with `| no-more`.
The XML parser failure came from the trailing `{master:0}` marker.
Native JSON contained `chassis-inventory`. A later current running-statistics read reported two targets as `connected`.
These initial diagnostic results preceded the complete live portal acceptance above.

Correction validation: The final WebSockets unit, contract, and page suite reported 611 passed and 5 skipped.
The native acceptance suite includes independent quota and collision failures.
Ruff, Black, mypy, Bandit, complexity, and compilation completed successfully.
Mypy examined 146 source files. Symbol comparison examined eight changed runtime modules and found no lost names.
Symbol comparison returned 1 because three required imports added names: `Mapping`, `json`, and `cast`.
The operator guide, correction release note, plan, and quickstart passed the STE score requirement.
Added empty-body and malformed native JSON regressions passed with their affected suites: 71 passed and 1 skipped.
The committed-tree quality preflight passed. The ratchet checked six files and reported zero new findings.

Validation evidence: Focused feature tests passed (85 passed, 1 skipped); the complete WebSockets unit/contract/E2E run collected 778 and reported 772 passed, 5 skipped, and 1 unrelated Windows-only failure in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py::TestReports::test_real_restricted_writer_keeps_distinct_modes_and_permissions` because `os.O_NOFOLLOW` is unavailable. Ruff, Black, mypy, Bandit, complexity, source compilation, and citation checks passed. Test-quality preflight and the changed-from ratchet each found zero new findings. `speckit.analyze` identified JSON/BOTH result and archive details that needed alignment; the feature spec was updated. The repository constitution’s mandatory full deployment pipeline and all-lines-comments expectations conflict with the user’s no-push/no-PR and non-obvious-comments instructions; shared governance was left unchanged.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 and T002 have no feature-code dependencies.
- **Foundational**: T003 depends on T001 and must pass before shell-flow changes.
- **User Story 1**: T004 and T005 depend on T003. T006 and T007 depend on their tests and edit separate files. T008 depends on T006 and T007.
- **User Story 2**: T009 depends on T008. T010 depends on T009. T011 depends on T010.
- **User Story 3**: T012 depends on T011. T013 and T014 depend on T012 and edit separate files. T015 depends on T013 and T014.
- **Polish**: T016 and T017 depend on T015. T018 depends on T008, T011, T015, T016, and T017. T019 depends on T018. T020 depends on T019. T021 depends on T020. T022 depends on deployment and the completed local validation work. Parent live validation does not block this implementation report.

### User Story Dependencies

- **US1 (P1)**: Independent after setup and the existing contract check.
- **US2 (P1)**: Extends the US1 preset and uses its server-owned target plan.
- **US3 (P2)**: Extends the US1 run and US2 target outcome flow with validated files.

## Parallel Opportunities

- T001 and T002 can run in parallel because they inspect separate setup concerns.
- T004 and T005 can run in parallel because the unit and browser tests use different files.
- T006 and T007 can run in parallel after the request contract is fixed by T004 and T005.
- T013 and T014 can run in parallel after T012 because shell capture and artifact persistence use separate files.
- T016 and T017 can run in parallel after feature behavior is stable.

## Parallel Example: User Story 1

```text
Task: T004 Add service contract tests in tests/unit/websocket_streams/web/test_ws_web_services.py
Task: T005 Add preset browser tests in tests/e2e/websockets_tab/test_websockets_page.py
```

## Implementation Strategy

1. Complete setup and verify the existing Mist shell contracts.
2. Deliver US1 as the MVP with a dedicated preset, organization preview, and format selection.
3. Add US2 targeting and failure guarantees before saving device output.
4. Add native XML and JSON parsing, safe filenames, and archive behavior.
5. Run feature and regression gates, analyze the artifacts, commit explicit files, then run the test-quality ratchet.
6. Leave live testing to the parent after local deployment. Never treat mocked output as live proof.
