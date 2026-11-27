# Tasks: Portal hardware inventory unlock without the free-form shell

Every task starts with status `open`. No task starts before the owner records decision D-1. Each task names one verification command from the Local gates table in `.github/copilot-instructions.md` (RC-003). The final tasks use read-only `gh` commands, see analysis.md finding A-03. Tasks marked [P] can run in parallel.

## Test tasks

### T001 [P] Test the settings flag (FR-008)
- Depends on: T009.
- Files: modify `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py` (line 32).
- Cases (3): (a) `true` enables the flag. (b) `maybe` reads false and logs one warning that names the variable. (c) A missing variable reads false.
- Acceptance: All three cases pass with the reader from T009.
- Verification: `python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`
- Status: open

### T002 [P] Test the catalog lock rule (FR-001, FR-002, FR-003, FR-004, FR-007)
- Depends on: T010.
- Files: modify `tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py` (lines 23, 37).
- Cases (5): (a) The hardware scope opens with the hardware flag. (b) No scope with only the hardware flag refuses the free-form shell and names `PORTAL_WS_ENABLE_SHELL`. (c) The hardware scope with both flags false refuses and names `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`. (d) The shell flag opens the hardware scope. (e) The payload keeps `changes` and `shell` and adds `hardware_inventory`.
- Verification: `python -m pytest tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py`
- Status: open

### T003 [P] Test the intake checker (FR-002, FR-005, FR-006)
- Depends on: T011, T012.
- Files: modify `tests/unit/websocket_streams/intake/test_ws_start_request.py` (line 194).
- Cases (3): (a) The checker forwards the scope and accepts a hardware-only batch. (b) Without scope, the free-form shell refuses and names `PORTAL_WS_ENABLE_SHELL`. (c) The hardware scope with both flags false refuses and names `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- Verification: `python -m pytest tests/unit/websocket_streams/intake/test_ws_start_request.py`
- Status: open

### T004 [P] Test the batch service (FR-002, FR-003, FR-005, FR-006)
- Depends on: T013.
- Files: modify `tests/unit/websocket_streams/web/test_ws_web_services.py` (line 489).
- Cases (4): (a) A hardware preview with both flags false returns 403 `locked` and names the hardware flag. (b) A generic shell batch with only the hardware flag returns 403 `locked`. (c) A flag change between preview and start refuses the start with 403 `locked`. (d) Browser commands with the hardware preset return 400 `bad_request`.
- Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py`
- Status: open

### T005 [P] Test the portal flow (FR-001, FR-003, FR-013, FR-014)
- Depends on: T013, T014, T015.
- Files: modify `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` (lines 34, 569).
- Cases (3): (a) Only the hardware flag gives a preview with the EX target list and HTTP 200. (b) Start sends only the fixed command on line 34 and writes the WARNING audit event. (c) Both flags false return 403 `locked` with the message on line 569.
- Verification: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`
- Status: open

### T006 [P] Test the routing checker (FR-005, FR-012)
- Depends on: T015.
- Files: modify `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py` (line 53).
- Cases (1): The fake checker forwards `lock_scope`. The CLI route keeps the shell unlock from `batch.py` lines 144 and 147 without a setting.
- Verification: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py`
- Status: open

### T007 [P] Test the page hint (FR-007, FR-009)
- Depends on: T016, T017.
- Files: modify `tests/e2e/websockets_tab/test_websockets_page.py` (lines 159, 998).
- Cases (1): With both flags false, the Multi Site tab shows the hardware flag name in `ws-batch-hardware-lock`. The page loads when the `hardware_inventory` key is absent, as in the fixture on line 159.
- Verification: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`
- Status: open

### T008 [P] Test the documents (FR-010, FR-011, FR-015, FR-016)
- Depends on: T018, T019, T020, T021, T022.
- Files: modify `tests/guardrails/test_hardware_shell_lock_docs.py` (lines 112, 140).
- Cases (4): (1) The operator guide names both flags, the scope, the warning, and the steps. The documented refusal names the hardware flag. (2) The Web Portal row and `deploy/.env.example` name the hardware flag. (3) The 4920 amendment is dated and names the hardware flag. (4) The changelog fragment names issue 4939 and uses only change types from `changelog.d/README.md`.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

## Implementation and document tasks

### T009 [P] Add the hardware flag reader (FR-008)
- Depends on: none.
- Files: modify `src/mist/realtime/websocket_streams/live/sessions/settings.py`. Add field `hardware_inventory_enabled` after line 43. Add one reader line after line 59. The line calls `cls._read_flag` with `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- Acceptance: The reader uses the rules on lines 100 to 105. Method `from_environment` (lines 46 to 69) keeps 25 lines or fewer.
- Verification: `python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`
- Status: open

### T010 Add the lock scope to the catalog (FR-001, FR-002, FR-003, FR-004, FR-007)
- Depends on: T009.
- Files: modify `src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py`. Add `HARDWARE_FLAG` and `HARDWARE_SCOPE` after line 27. Add a constructor keyword near lines 29 to 35. Apply the scope in `lock_flag` (lines 52 to 63). Add `flags.hardware_inventory` after line 75.
- Acceptance: The hardware scope unlocks with either flag. Other shell requests unlock with the shell flag only.
- Verification: `python -m pytest tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py`
- Status: open

### T011 Pass the scope in the intake check (FR-005, FR-006)
- Depends on: T010.
- Files: modify `src/mist/realtime/websocket_streams/intake/start_request/validation.py` (lines 53 to 59). `check_lock` accepts `lock_scope` and passes it to `lock_flag`. The message on line 59 does not change.
- Verification: `python -m pytest tests/unit/websocket_streams/intake/test_ws_start_request.py`
- Status: open

### T012 Pass the scope in the checker (FR-005, FR-006)
- Depends on: T011.
- Files: modify `src/mist/realtime/websocket_streams/intake/start_request/checker.py` (lines 57 to 71). `check_batch` and `resolve_definition` accept `lock_scope` and pass it to `check_lock`.
- Verification: `python -m pytest tests/unit/websocket_streams/intake/test_ws_start_request.py`
- Status: open

### T013 Set the scope in the batch service (FR-001, FR-002, FR-003, FR-005, FR-006, FR-013)
- Depends on: T012.
- Files: modify `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`. Lines 94 to 96 and 113 pass `lock_scope`. Lines 138 to 149 pass it to `resolve_definition`. Line 447 passes it to the per-target check. Lines 614 to 619 pass the stored scope at admission. Lines 891 to 900 set `hardware_preset` in the hardware branch only.
- Acceptance: The browser cannot set the scope (FR-005). The start path keeps its WARNING audit event (FR-013).
- Verification: `python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py`
- Status: open

### T014 Wire the flag into the catalog factory (FR-001, FR-007)
- Depends on: T009, T010.
- Files: modify `src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py` (lines 48 to 63). `_catalog` passes `hardware_inventory_enabled` from the settings to `StreamCatalog`.
- Verification: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`
- Status: open

### T015 Forward the scope in the MSP checker (FR-005, FR-006, FR-012)
- Depends on: T012.
- Files: modify `src/operations/exporting/ex_hardware_inventory/run/routing.py` (lines 215 to 223). `ScopeAwareChecker.check_batch` accepts `lock_scope` and passes it to the checker. The CLI route in `batch.py` (lines 144 and 147) does not change.
- Verification: `python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py`
- Status: open

### T016 [P] Add the hidden lock element (FR-009)
- Depends on: none.
- Files: modify `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` (near lines 177 to 189). Add the hidden element `wsBatchHardwareLock` with `data-testid="ws-batch-hardware-lock"`.
- Verification: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`
- Status: open

### T017 Show the flag name in the page handler (FR-007, FR-009)
- Depends on: T010, T016.
- Files: modify `src/mist/realtime/websocket_streams/web/static/websockets.js` (lines 204 to 215). `changeBatchHardwarePreset` shows `wsBatchHardwareLock` when `flags.hardware_inventory` reports both flags false. The handler reads the key only when present.
- Verification: `python -m pytest tests/e2e/websockets_tab/test_websockets_page.py`
- Status: open

### T018 [P] Rewrite the operator guide section (FR-010, FR-011)
- Depends on: none.
- Files: modify `documentation/operator-guide.md` (lines 398 to 432). Name the hardware flag first. Keep the shell warning. Remove the sentence on line 432 that refers to issue 4939.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

### T019 [P] Update the Web Portal wiki (FR-010)
- Depends on: none.
- Files: modify `documentation/wiki/Web-Portal.md`. Add the hardware flag row after line 284. Update the shell row on line 284. Update the unlock steps that start on line 130.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

### T020 [P] Add the contract amendment (FR-016)
- Depends on: none.
- Files: modify `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/portal.md`. Add a dated amendment under "Locks and limits" after line 96. The amendment states the hardware flag rule.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

### T021 [P] Add the changelog fragment (FR-015)
- Depends on: none.
- Files: add `changelog.d/issue-4939-portal-hardware-inventory-unlock.md`. Write one `###` heading. Write one bullet for each change type used, Added and Changed. End each bullet with issue 4939.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

### T022 [P] Add the env example block (FR-010), blocked
- Depends on: none. Blocked until draft PR #4208 merges or its owner completes a handover of `deploy/.env.example`.
- Files: modify `deploy/.env.example` (after line 221). Add a commented `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` block.
- Verification: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py`
- Status: open

## Final tasks

### T-LOCAL-GATES Run the local gates
- Depends on: T001 to T022.
- Files: every changed file in the change map of plan.md.
- Runs: Compile (`python -m py_compile MistHelper.py`). Format (`python -m black --check .`). Types (`python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`). Tests for the eight test files in T001 to T008. Full tests (the two `pytest-chunks` commands below the table). Safe sweep (`python MistHelper.py --test`). Coverage (`python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`). Test quality. Complexity. Security lint. Code quality (`pylint src/ --fail-under=9.5`). Dead code. Docstrings. Symbols (`symbol-diff --base main <file>`).
- Skipped: Dependency audit (no dependency change). Menu reference (no menu change). STE (none of the five files changes). Ops portal and Ops platform (no change in those trees).
- Verification: `python -m ruff check .` (Lint gate, expected: All checks passed).
- Status: open

### T-PR Commit, push, and open the pull request
- Depends on: T-LOCAL-GATES.
- Work: Commit with a Conventional Commits message that names issue 4939. Push branch `feat/4939-portal-hardware-inventory-unlock`. Open a pull request whose body contains `Closes #4939`. Review the diff against FR-014: no transport, REST call, menu, or command change.
- Verification: `gh pr view --json title,body,headRefName` (read-only, see analysis.md A-03).
- Status: open

### T-REMOTE-CI Watch the CI run
- Depends on: T-PR.
- Verification: `gh pr checks --watch` (read-only wait, see analysis.md A-03).
- Status: open

### T-MERGE Enable auto-merge after authorization
- Depends on: T-REMOTE-CI and the orchestrator authorization.
- Work: Enable auto-merge only after every remote check passes. After the merge, constitution steps 10 to 12 run (constitution lines 166 to 171, RC-012, U-8).
- Verification: `gh pr view --json mergeStateStatus,autoMergeRequest` (read-only).
- Status: open
