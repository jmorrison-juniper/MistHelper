# Tasks: Hardware Manifest Finalization After a File Lock

**Input**: Numeric record `specs/numbered/0/0/1/2/3/1/1/0/4780-manifest-finalization/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/manifest-json.md`, `design/contracts/cli-status.md`, and `design/quickstart.md`.

**Tests**: The specification requires tests. Write each test task before its implementation task. Each new test case must fail on main before the fix.

**Organization**: Tasks are grouped by phase. Each task names its user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It edits a different file.
- **[Story]**: The user story in `spec.md` that the task serves.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.
- **Verification**: One command from the local gates table in `.github/copilot-instructions.md`.

## Phase 1: Baseline Checks

- **T001** [P] [US1] Confirm the in-run replace budget on main.
  - Requirements: FR-001
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 461-483)
  - Acceptance: The replace waits 0.05, 0.1, 0.2, and 0.4 seconds. A final try raises.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py`
  - Status: verified-present

- **T002** [P] [US1] Confirm that no finalization marker exists on main.
  - Requirements: FR-008
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`
  - Acceptance: No source file contains the text `finalization-failed`.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_output_boundaries.py`
  - Status: absent

- **T003** [P] [US1] Confirm the parent state rule on main.
  - Requirements: FR-012
  - Files: `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` (lines 345-355)
  - Acceptance: `finish_parent` ignores the boolean from `artifacts.finish()`. A completed target set gives FINISHED.
  - Verification: `python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`
  - Status: verified-present

## Phase 2: Tests First

- **T004** [P] [US1] Write TEST-01, TEST-02, TEST-03, TEST-04, and TEST-05, and revise TEST-10.
  - Requirements: FR-002, FR-003, FR-006 to FR-009, FR-011, FR-017
  - Files: `tests/unit/websocket_streams/web/test_ws_artifact_replace.py`
  - Acceptance: Each new case fails on main. TEST-10 replaces the assertion at line 169.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py`
  - Status: open

- **T005** [P] [US2] Write TEST-06 and TEST-07.
  - Requirements: FR-003, FR-004, FR-005, FR-010
  - Files: `tests/unit/websocket_streams/web/test_hardware_native_acceptance.py`
  - Acceptance: TEST-06 checks the deferred write, the single later try, and the final file list.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_hardware_native_acceptance.py`
  - Status: open

- **T006** [P] [US1] Write TEST-08.
  - Requirements: FR-012
  - Files: `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`
  - Acceptance: A failed finalization sets the parent state to FAILED.
  - Verification: `python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`
  - Status: open

- **T007** [P] [US1] Write TEST-09.
  - Requirements: FR-013
  - Files: `tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - Acceptance: An unfinished run prints one unfinished-run line. The run status line stays last and reads partial.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - Status: open

- **T008** [P] [US1] Revise TEST-11.
  - Requirements: FR-008, FR-009
  - Files: `tests/unit/websocket_streams/web/test_ws_output_boundaries.py`
  - Acceptance: A failed final manifest leaves the marker, removes the staged file, and keeps external files.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_output_boundaries.py`
  - Status: open

## Phase 3: Implementation

- **T009** [US1] Add the `manifest_stale` field to `BatchArtifactRecord`.
  - Requirements: FR-003
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 56-73)
  - Acceptance: The field defaults to False. The field has an inline comment.
  - Verification: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`
  - Status: open

- **T010** [US1] Change `Metadata.write` and `Metadata.replace`.
  - Requirements: FR-001, FR-002, FR-009, FR-011, FR-014
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 444-483)
  - Acceptance: `write` accepts a waits argument. A refused replace sets `manifest_stale` and leaves the status unchanged. The staged file is removed when removal succeeds. Error events carry the integer codes.
  - Verification: `symbol-diff --base origin/main src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`
  - Status: open

- **T011** [US1] Add `Metadata.write_marker` and the marker constants.
  - Requirements: FR-008
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 436-503)
  - Acceptance: The marker name is `finalization-failed.json`. The marker write uses the finalization budget. A refused marker write logs an error and returns False.
  - Verification: `radon cc src/mist/realtime/websocket_streams -j | complexity-gate --max 10`
  - Status: open

- **T012** [US1] Change `BatchArtifactStorage.finish`.
  - Requirements: FR-006, FR-007, FR-008
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 255-267)
  - Acceptance: Success sets ready and complete. A refusal sets failed and partial, writes the marker, and raises `output_failed`.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py`
  - Status: open

- **T013** [US2] Defer refused in-run writes.
  - Requirements: FR-003, FR-004, FR-005, FR-010
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (`Hardware._snapshot` at lines 127-140, and `BatchArtifactWriter.write_result` at lines 85-98)
  - Acceptance: A refused write defers only when the status stays writing. A quota or link refusal still raises.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_hardware_native_acceptance.py`
  - Status: open

- **T014** [US1] Set the parent state to FAILED.
  - Requirements: FR-012
  - Files: `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` (lines 345-355)
  - Acceptance: A False result from `artifacts.finish()` sets FAILED. The reason reads "The batch output could not be finalized."
  - Verification: `python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`
  - Status: open

- **T015** [US1] Add `artifact_ready` to `BatchRunResult`, and read it in `OrganizationBatchRun.run`.
  - Requirements: FR-013
  - Files: `src/operations/exporting/ex_hardware_inventory/run/batch.py` (lines 100-111 and 213-239)
  - Acceptance: The field defaults to True. Skipped runs keep the default.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_batch.py`
  - Status: open

- **T016** [US1] Collect unfinished runs and set partial.
  - Requirements: FR-013
  - Files: `src/operations/exporting/ex_hardware_inventory/operation.py` (lines 101-135 and 296-306)
  - Acceptance: `partial` is True when any run is unfinished.
  - Verification: `python -m pytest tests/unit/ex_hardware_inventory/test_hardware_operation.py`
  - Status: open

- **T017** [US1] Print one line for each unfinished run.
  - Requirements: FR-013
  - Files: `src/operations/exporting/ex_hardware_inventory/console.py` (lines 106-118)
  - Acceptance: Each unfinished run prints one line that names the run folder. The run status line stays last.
  - Verification: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py`
  - Status: open

## Phase 4: Documentation and Evidence

- **T018** [US3] Update the operator guide and add the changelog fragment.
  - Requirements: FR-008, FR-011, FR-013
  - Files: `documentation/operator-guide.md` (line 392), and `changelog.d/issue-4780-manifest-finalization.md` (new)
  - Acceptance: The guide names the marker, the partial status, and the wait. The guide gives one Caution statement about the wait. The fragment has one `### Fixed` heading and one bullet that names issue 4780.
  - Verification: `python -m pytest tests/guardrails`
  - Status: open

- **T019** [US3] Run the authorized read-only acceptance and record the evidence.
  - Requirements: FR-011, FR-016
  - Files: None in the repository. The run writes under `data\websocket-streams\` and `data\script.log`. Do not add either path to a commit.
  - Acceptance: The issue receives the `errno` value, the `winerror` value, the handle listing result, and the run folder name. The record names a lock holder only when the evidence shows one.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_artifact_replace.py`
  - Status: open
  - Depends on: T010

- **T020** [US3] Conditional. When T019 names an in-process reader, skip live run folders in `Retention.cleanup_orphans`.
  - Requirements: FR-010, FR-016
  - Files: `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` (lines 574-585), and `tests/unit/websocket_streams/web/test_ws_orphan_retention.py`
  - Acceptance: The orphan scan opens no manifest of a run that this process owns.
  - Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_orphan_retention.py`
  - Status: open
  - Depends on: T019

## Phase 5: Pipeline

- **T-LOCAL-GATES** [US1] Run each local gate that applies to the changed files.
  - Requirements: FR-015, and every other requirement through the full suite
  - Files: Each changed file
  - Gates: Lint, format, types, tests, full tests, coverage, test quality, complexity, security lint, code quality, dead code, docstrings, symbols, and the safe sweep.
  - Acceptance: Each applicable local gate passes. The menu reference and ops portal gates do not apply, because no menu and no ops portal file changes.
  - Verification: `python -m ruff check .`
  - Status: open
  - Depends on: T004 to T020

- **T-PR** [US1] Commit with a Conventional Commits message, push `fix/4780-manifest-finalization`, and open a pull request.
  - Requirements: All
  - Files: The changed files, added by explicit path
  - Acceptance: The title reads `fix(web-portal): finalize hardware manifest after a file lock`. The body contains `Closes #4780` and the gate results.
  - Verification: `python -m ruff check .`
  - Status: open
  - Depends on: T-LOCAL-GATES

- **T-REMOTE-CI** [US1] Wait for each required check.
  - Requirements: All
  - Files: None
  - Acceptance: `gh pr checks <number> --watch` shows green for each required check.
  - Verification: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open
  - Depends on: T-PR

- **T-MERGE** [US1] Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: All
  - Files: None
  - Acceptance: The `auto-merge` label is added once, after the checks pass. The squash merge creates one commit on `main`.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: open
  - Depends on: T-REMOTE-CI

## Dependencies and Execution Order

- Phase 1 runs first. Tasks T001 to T003 have no prerequisite.
- Phase 2 tasks T004 to T008 depend on Phase 1. They run in parallel.
- Phase 3 depends on Phase 2. Task T009 precedes T010. Tasks T010 precedes T011 and T012. Task T013 depends on T010. Tasks T014 and T015 run in parallel. Task T016 depends on T015. Task T017 depends on T016.
- Phase 4 depends on Phase 3. Task T019 depends on T010. Task T020 depends on T019.
- Phase 5 runs last, in this order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
