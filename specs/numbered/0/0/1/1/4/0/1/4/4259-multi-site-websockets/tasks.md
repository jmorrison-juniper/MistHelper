# Tasks: Multi-site WebSocket operations

**Input**: Design documents in `specs/numbered/0/0/1/1/4/0/1/4/4259-multi-site-websockets/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: Required by the specification and this request. Use mocked Mist and transport responses for automated checks.

**Ownership**: Do not modify `.specify/feature.json` (PR #4260) or `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py` (PR #4208). Extend existing package files; do not add package children to full directories.

## Phase 1: Setup

**Purpose**: Confirm existing boundaries and prepare safe local validation.

- [ ] T001 [P] Check the structure guard and direct-child counts for `src/mist/realtime/websocket_streams/` and `tests/unit/websocket_streams/` before choosing implementation files; do not add modules or package directories.
- [ ] T002 [P] Confirm that mocked Mist SDK and WebSocket fixtures use temporary output paths and do not write test output under `data/` in `tests/unit/websocket_streams/` and `tests/contract/websocket_streams/`.

## Phase 2: Foundational

**Purpose**: Prove transport and SDK behavior and establish shared batch invariants before story work.

- [ ] T003 Add contract coverage in `tests/contract/websocket_streams/test_ws_sdk_contract.py` for installed SDK 0.64.1 page traversal. `mistapi.get_next` follows the authenticated `response.next` URL. Validate every returned status and shape. Do not use `mistapi.get_all` where it cannot report a failed page.
- [ ] T004 [P] Run and preserve the first-output and split-control transport proofs in `tests/contract/websocket_streams/test_ws_sdk_contract.py`; confirm that the owned transport retains first output and split control sequences before implementation approval.
- [ ] T005 [P] Add unit coverage for target identity, terminal target states, and count invariants in `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py` and `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
- [ ] T006 Check the shared live-session and transport limits in `src/mist/realtime/websocket_streams/live/sessions/settings.py` and `src/mist/realtime/websocket_streams/live/sessions/manager/operations.py`; define how batch permits share capacity with Single Site sessions without changing existing limits.

## Phase 3: User Story 1 - Preserve the Single Site workflow (Priority: P1)

**Goal**: Add the new tab entry point without changing the existing Single Site form, channel selection, session controls, interactive shell, or downloads.

**Independent Test**: Use the Single Site tab to start a mocked operation, receive output, stop it, and download it. Confirm that channel selection still accepts 10 paths and rejects 11, and that the interactive shell still supports input and resize.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add regression checks for the current Single Site start payload, session controls, and downloads in `tests/unit/websocket_streams/web/test_ws_web_services.py`.
- [ ] T008 [P] [US1] Add browser checks for the initial Single Site tab, 10/11 channel paths, session continuity across tab changes, and interactive shell controls in `tests/e2e/websockets_tab/test_websockets_page.py` and `tests/e2e/websockets_tab/test_websockets_terminal.py`.

### Implementation for User Story 1

- [ ] T009 [US1] Add accessible Single Site and Multi Site tab panels while preserving the current Single Site markup and test IDs in `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`.
- [ ] T010 [US1] Keep separate tab state and add tab navigation without changing Single Site request construction, the 10-path limit, or terminal behavior in `src/mist/realtime/websocket_streams/web/static/websockets.js`.

## Phase 4: User Story 2 - Select organization targets (Priority: P1)

**Goal**: Discover complete, eligible target lists from catalog metadata and resolve all/selected choices to verified natural-key identities.

**Independent Test**: Mock multiple site, device, and wired-client pages. Verify configured page limits, family and parent association filters, empty versus failed discovery, and stale browser response rejection.

### Tests for User Story 2

- [ ] T011 [P] [US2] Add site, device, map, asset, and Mist Edge picker cases to `tests/unit/websocket_streams/intake/test_ws_start_request.py`. Add client association and natural-key deduplication cases to `tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py`. Use only these existing test files.
- [ ] T012 [P] [US2] Add SDK contract cases for authenticated requests, runtime limits 250 and 1000, all pages, `type="all"` device discovery, later-page failures, complete empty results, and verified wired-client traversal in `tests/contract/websocket_streams/test_ws_sdk_contract.py`. Cover paged site, device, map, asset, Mist Edge, SDK-client, and wired-client methods with maximum limits, identity retention, and failed-page handling. Base wired-client assertions on T003.
- [ ] T013 [P] [US2] Add Flask picker response tests for complete, empty, denied, incomplete, and stale-scope outcomes in `tests/unit/websocket_streams/web/test_ws_web_services.py`.

### Implementation for User Story 2

- [ ] T014 [US2] Extend SDK-backed discovery and response validation in `src/mist/realtime/websocket_streams/intake/pickers/devices.py`, `src/mist/realtime/websocket_streams/intake/pickers/resources.py`, and `src/mist/realtime/websocket_streams/intake/pickers/service.py`; fetch every supported page, retain verified associations, and report a failed page instead of an empty list.
- [ ] T015 [US2] Add the Multi Site sites and target picker routes through existing route files in `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py` and `src/mist/realtime/websocket_streams/web/blueprint/registry.py`.
- [ ] T016 [US2] Add catalog-derived target controls for all/selected sites and supported resources, with site and device identity, family filtering, revision checks, and distinct discovery errors in `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` and `src/mist/realtime/websocket_streams/web/static/websockets.js`.
- [ ] T017 [US2] Exercise target selection, stale-response rejection, and empty/error states in `tests/e2e/websockets_tab/test_websockets_page.py`.

## Phase 5: User Story 3 - Run and monitor a multi-target operation (Priority: P1)

**Goal**: Admit one parent session, freeze the confirmed target set, run bounded target work, and retain per-target state and results.

**Independent Test**: Start a mocked batch of at least six targets with concurrency two. Confirm one public session, mixed success and failure, accurate target identities and counts, cancellation of queued and active work, and no more than two active targets or the shared transport limit.

### Tests for User Story 3

- [ ] T018 [P] [US3] Add unit cases for preview expiry and consumption, exact fingerprint binding, typed confirmation, target limits 1-1000, channel concurrency exactly 1, utility and shell concurrency 1-5 with default 3, cancellation races, and terminal target outcomes in `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py` and `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`.
- [ ] T019 [P] [US3] Add channel contract cases for one owned connection, catalog paths, path-to-target demultiplexing, first-output retention, and batches that exceed the Single Site 10-path limit in `tests/contract/websocket_streams/test_ws_channel_parity.py`.
- [ ] T020 [P] [US3] Add utility and finite-shell runner unit cases for bounded target dispatch, one utility trigger per target, ordered shell commands, initial normalized prompt capture, same-prompt completion, two-second quiet, both 30-second deadlines, partial output, command skipping, and unavailable device exit status in `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py` and `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`.
- [ ] T021 [P] [US3] Add Flask integration cases for preview, atomic admission, target pagination, progress, partial failures, stop, repeated stop, invalid targets, and session capacity in `tests/unit/websocket_streams/web/test_ws_web_services.py`.

### Implementation for User Story 3

- [ ] T022 [US3] Add immutable preview validation for operation, parameters, exact targets, shell command order, and the `RUN <target_count> TARGETS` confirmation in existing intake files `src/mist/realtime/websocket_streams/intake/start_request/models.py`, `src/mist/realtime/websocket_streams/intake/start_request/targets.py`, and `src/mist/realtime/websocket_streams/intake/start_request/validation.py`.
- [ ] T023 [US3] Add bounded target scheduling, shared transport permits, batch cancellation, and parent lifetime handling in existing session files `src/mist/realtime/websocket_streams/live/sessions/manager/operations.py`, `src/mist/realtime/websocket_streams/live/sessions/manager/lifecycle.py`, and `src/mist/realtime/websocket_streams/live/sessions/record/session.py`.
- [ ] T024 [US3] Route all selected channel paths through one owned connection and demultiplex each event by its frozen target identity in `src/mist/realtime/websocket_streams/live/runners/channel/runner.py` and `src/mist/realtime/websocket_streams/live/runners/channel/routing.py`; do not apply the Single Site 10-path validation limit.
- [ ] T025 [US3] Run utility triggers as separate bounded per-target executions and retain target identity for each result in `src/mist/realtime/websocket_streams/live/runners/utility/runner/utility_runner.py` and `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`.
- [ ] T026 [US3] Run only the ordered finite command list accepted in the preview and bound to its confirmed snapshot; enforce 1-20 commands, 4096 UTF-8 bytes per command, 16384 bytes per list, 30-second initial-output and per-command deadlines, same normalized prompt, and two-second quiet completion in `src/mist/realtime/websocket_streams/live/runners/shell/runners.py`. Preserve partial output and skip later commands after a timeout. Keep Single Site interactive shell behavior unchanged.
- [ ] T027 [US3] Add batch preview, start, summary, target-page, and batch-shell rejection routes through existing files `src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py`, `src/mist/realtime/websocket_streams/web/blueprint/registry.py`, and `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`.
- [ ] T028 [US3] Add the Multi Site preview, confirmation, per-target progress, partial-failure, and parent-stop browser flow in `tests/e2e/websockets_tab/test_websockets_page.py`; verify that no live broadcast input is available.

## Phase 6: User Story 4 - Save batch results (Priority: P2)

**Goal**: Save redacted target results to server-owned files under `data/`, expose combined or grouped downloads, and remove files with the existing session retention policy.

**Independent Test**: Run mocked mixed-outcome batches in combined, grouped, and both modes. Verify record identity, path containment, redaction, partial status, download behavior, and cleanup at five ended sessions or 600 seconds.

### Tests for User Story 4

- [ ] T029 [P] [US4] Add unit cases for traversal, symlinks, unsafe labels, reserved names, split-secret redaction, output quotas, and failed writes in `tests/unit/websocket_streams/web/test_ws_output_boundaries.py` and `tests/unit/websocket_streams/web/test_ws_secret_guard.py`.
- [ ] T030 [P] [US4] Add Flask integration cases for manifests, combined and grouped downloads, ZIP entries, partial snapshots, download pins, deletion, expiry, and restart cleanup in `tests/unit/websocket_streams/web/test_ws_web_services.py`.

### Implementation for User Story 4

- [ ] T031 [US4] Persist redacted result envelopes through a bounded writer under `data/websocket-streams/{session_id}/`; enforce the 64 MiB total limit, reserve 1 MiB for metadata, and use safe server-created paths in `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` and `src/mist/realtime/websocket_streams/live/sessions/record/output.py`.
- [ ] T032 [US4] Remove session-owned artifact trees on deletion, retention expiry, and safe restart cleanup; preserve the existing five-ended-session and 600-second limits in `src/mist/realtime/websocket_streams/live/sessions/manager/lifecycle.py` and `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`.
- [ ] T033 [US4] Add artifact manifest, JSONL, and ZIP download handling through existing response and route files `src/mist/realtime/websocket_streams/web/blueprint/responses/download.py` and `src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py`.
- [ ] T034 [US4] Add browser checks for target-labeled results, partial progress, layout selection, and parent-session downloads in `tests/e2e/websockets_tab/test_websockets_page.py`.

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Document the feature and run safe local checks after implementation.

- [ ] T035 [P] Update operator guidance for target selection, preview confirmation, finite shell batches, output layouts, and retention in `./README.md`.
- [ ] T036 [P] Add the issue release note for Multi Site WebSocket operations in `changelog.d/issue-4259-multi-site-websockets.md`.
- [ ] T037 Run safe validation with mocked credentials: the transport contract tests, `python -m pytest tests/unit/websocket_streams -q`, `python -m pytest tests/contract/websocket_streams -q`, `python -m pytest tests/e2e/websockets_tab -q`, and `git diff --check`. If credentials are available, use Morrison House Oregon for read-only checks only. Never change cloud configuration or device state.
- [ ] T038 Run the repository structure guard and applicable lint, type, security, and documentation checks for changed files. Read each command from `.github/workflows/ci.yml` and repository instructions. Report unavailable checks instead of treating them as passed.
- [ ] T040 Audit every changed executable line for its required inline comment and every meaningful action for before/after/error logs; add focused tests where practical and do not commit until the audit passes.

## Phase 8: Delivery and Post-Merge

**Purpose**: Run required gates, prepare a complete pull request, and verify the merged result.

- [ ] T041 Run `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` and confirm every required input is present before the test-quality check.
- [ ] T042 After committing the intended tests, run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`; require zero new findings before push.
- [ ] T043 Inspect `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/` before preparing the PR body. Preserve the selected template and include exact local gate commands and results. Wait for required checks and CodeQL with `gh pr checks <number> --watch`, then wait for human review before merge.
- [ ] T044 After a maintainer merges the PR, verify the merge commit on `main`, the linked issue state, and the merged feature files. Do not merge or delete the branch without required approval and preservation evidence.

## Separate Capacity Remediation

This is a separately approved follow-up, not a package move in issue #4259. The feature implementation must extend existing children and stop if it needs a new child in a full directory.

- [ ] T039 Inventory and complete the plan's CAP-4259-1, CAP-4259-2, and CAP-4259-3 capacity remediation in a separate approved change for `src/mist/realtime/websocket_streams/live/`, `src/mist/realtime/websocket_streams/live/sessions/`, `tests/unit/websocket_streams/live/`, and `tests/unit/websocket_streams/live/sessions/`; add move/import tests there and do not move packages as part of this feature.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately. It checks existing guardrails and safe test fixtures.
- **Foundational (Phase 2)**: Depends on setup. T003 must finish before wired-client traversal is implemented; T004 must pass before implementation approval.
- **User Story 1 (Phase 3)**: Depends on the foundation. It can proceed separately from target discovery and batch execution.
- **User Story 2 (Phase 4)**: Depends on the foundation and provides the verified target snapshot required by User Story 3.
- **User Story 3 (Phase 5)**: Depends on User Story 2 for complete discovery and frozen target identities.
- **User Story 4 (Phase 6)**: Depends on User Story 3 for parent sessions and result envelopes.
- **Polish (Phase 7)**: Depends on the stories selected for delivery. Run automated checks with mocks; live validation needs separate approval.
- **Delivery (Phase 8)**: Depends on all implementation, documentation, and local validation tasks. Complete T041-T043 before push and T044 only after a maintainer merges the pull request.
- **Capacity remediation (T039)**: Separate follow-up. It is not a prerequisite while implementation stays within existing package files. If new children are required, stop and obtain approval for the separate capacity change.

### User Story Dependencies

- **US1 (P1)**: Independent after the foundation. Its Single Site behavior is a regression boundary for every later story.
- **US2 (P1)**: Can start after the foundation. US3 needs its complete, verified target snapshot.
- **US3 (P1)**: Starts after US2. It owns batch admission, target execution, and progress.
- **US4 (P2)**: Starts after US3. It uses the batch result envelope and session ownership.

### Parallel Opportunities

- T001 and T002 can run in parallel.
- In Phase 2, T004 and T005 can run in parallel with SDK verification T003; do not approve implementation until T003 and T004 are complete.
- US1 regression test tasks T007 and T008 can run in parallel; after they pass, template and JavaScript tasks T009 and T010 can be split by file.
- US2 unit, SDK contract, and Flask picker tests T011-T013 can run in parallel because they use different files. Discovery implementation must wait for T003 and those tests.
- US3 unit, channel contract, runner, and Flask integration test tasks T018-T021 can run in parallel. Runtime tasks T023-T026 can be split by file after the snapshot contract in T022 is fixed.
- US4 boundary/redaction tests and Flask integration tests T029-T030 can run in parallel. Artifact writing and retention tasks T031-T032 touch different files and can be split after the data model is fixed.
- Documentation tasks T035 and T036 can run in parallel after behavior is stable.
- T040 can run after source and test changes stabilize. T041-T043 are sequential because the quality analyzer reads committed tests and the PR requires completed local evidence.
- T044 is a post-merge check and cannot run before the maintainer merges the pull request.
- Do not run competing edits to the same existing test or source file at the same time.

### Parallel Example: User Story 2

```text
Task T011: Add target eligibility unit cases in tests/unit/websocket_streams/intake/test_ws_stream_pickers.py
Task T012: Add SDK pagination contract cases in tests/contract/websocket_streams/test_ws_sdk_contract.py
Task T013: Add Flask picker response cases in tests/unit/websocket_streams/web/test_ws_web_services.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks, including SDK cursor verification and both transport proofs.
2. Complete US1 to preserve the current Single Site workflow.
3. Complete US2 for catalog-driven, complete target discovery.
4. Complete US3 for one-parent bounded batch execution and per-target outcomes.
5. Validate US1-US3 with mocked SDK and transport fixtures before adding saved batch layouts.

### Incremental Delivery

1. Deliver tab separation while Single Site behavior remains unchanged.
2. Add target discovery and preview with exact target identities.
3. Add bounded channel, utility, and finite shell batches with cancellation.
4. Add safe artifacts, grouped downloads, retention cleanup, documentation, and the issue changelog.
5. Run the full safe local validation set. Do not use live commands without separate approval.

## Unresolved Cross-Artifact Check

The installed `mistapi` 0.64.1 source confirms that `get_next` follows the authenticated `response.next` URL and that the wired-client OpenAPI schema defines that field as the next-page URL. T003 must add failure-path contract coverage before implementation relies on this behavior.
