Feature: Audit Menu #5 — Show MAC Table via WebSocket
Repository path: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper
Spec directory: C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\092-audit-menu-5-show-mac-table-via

Overview
--------
This tasks.md implements the audit plan for Menu #5: WebSocketCommands.show_mac_table.
Tasks are organized by phase and by user story (US1..US5) and are dependency-ordered.
Each task follows the required checklist format and includes absolute file paths.

Phase 1 — Setup (project initialization)
---------------------------------------
- [ ] T001 [P] Create test scaffold for show MAC table: add file C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py with class TestShowMacTable and placeholder tests per quickstart.md
- [ ] T002 [P] Create test scaffold for WebSocketManager: add file C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_websocket_manager.py with class TestWebSocketManager and placeholder tests per quickstart.md
- [ ] T003 [P] Ensure top-of-file import 'traceback' exists in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (add "import traceback" at top if missing)

Phase 2 — Foundational (blocking prerequisites)
------------------------------------------------
- [ ] T004 Initialize 'websocket_manager' before try/except in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (set websocket_manager = None immediately before the try block in WebSocketCommands.show_mac_table)
- [ ] T005 Remove inline "import traceback" from exception handler in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (delete the runtime import inside except blocks)
- [ ] T006 Replace raw requests.post call with apisession.mist_post in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (change REST POST to use apisession.mist_post(uri, body=payload) and adapt response handling)
- [ ] T007 Replace hardcoded time.sleep(1) after subscribe with WebSocketManager.wait_for_subscription_confirmation in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (call wait_for_subscription_confirmation(command_channel, timeout_seconds=10) and handle False case with warning)
- [ ] T008 Pass activity_timeout_seconds=5 to wait_for_command_result in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (ensure wait_for_command_result(session_id, timeout_seconds=60, activity_timeout_seconds=5) is called)
- [ ] T009 Add explicit empty-table detection and user-facing message in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (when result has "ethernet switching table : 0 entries" print "MAC table is empty (0 entries learned)" instead of generic failure)
- [ ] T010 Ensure disconnect() is invoked using the explicit websocket_manager variable in finally in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (use if websocket_manager is not None: websocket_manager.disconnect())

Phase 3 — User Stories (priority order from spec.md)
----------------------------------------------------
Note: Each user-story phase is an independently testable increment. Story labels [US1]..[US5] are used.

Phase 3 — US1 (P1): Retrieve MAC Table from a Healthy Switch
- [ ] T011 [P] [US1] Extract helper _select_mac_table_target in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (implement private static method that encapsulates site/device selection and returns (site_id, device_id) or None)
- [ ] T012 [P] [US1] Extract helper _setup_websocket_for_command in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (implement private static method that builds WebSocketManager, calls connect(), subscribes to the command channel, and confirms subscription; return websocket_manager or None)
- [ ] T013 [P] [US1] Extract helper _trigger_mac_table_command in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (implement private static method that issues REST POST via apisession.mist_post, extracts session_id, and returns session_id or None)
- [ ] T014 [P] [US1] Extract helper _display_mac_table_result in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (implement private static method that formats and prints results, handles empty table and field enumeration)
- [ ] T015 [US1] [US1] Implement orchestration in WebSocketCommands.show_mac_table in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (call the four helpers in sequence, handle error return values, and ensure finally cleanup)
- [ ] T016 [US1] [US1] Implement happy-path unit test in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (mock PromptUtils selections, mock WebSocketManager behaviors, mock apisession.mist_post to return 200 + session, assert printed output contains MAC table header and entries)

Phase 4 — US2 (P1): Graceful Handling of Connection and Command Failures
- [ ] T017 [US2] Implement unit test for WebSocket connection failure in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (mock WebSocketManager.connect to return False; assert error message and no leaked connections)
- [ ] T018 [US2] Implement unit test for subscription failure in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (mock subscribe_to_channel to return False and wait_for_subscription_confirmation False; assert warning/error and disconnect called)
- [ ] T019 [US2] Implement unit test for REST POST failure in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (mock apisession.mist_post to return non-200 status; assert error message includes status and body and disconnect called)
- [ ] T020 [US2] Implement missing-session-id handling in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (detect when response.data lacks 'session' and print "No session ID returned" and disconnect)

Phase 5 — US5 (P1): Unit Test Coverage (create comprehensive tests)
- [ ] T021 [US5] [P] Implement unit test for empty MAC table in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (mock wait_for_command_result returning raw output containing "ethernet switching table : 0 entries" and assert the "MAC table is empty (0 entries learned)" message)
- [ ] T022 [US5] [P] Implement unit test for wait_for_command_result timeout in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_websocket_manager.py (mock wait_for_command_result to return None; assert timeout message and disconnect)
- [ ] T023 [US5] [P] Implement unit test to ensure disconnect called on exceptions and KeyboardInterrupt in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (raise exceptions at several points; assert websocket_manager.disconnect called once)
- [ ] T024 [US5] [P] Add coverage-driven tests for repeated-message completion heuristic in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_websocket_manager.py (simulate 5 identical messages → ensure completion returned)

Phase 6 — US3 (P2): Timeout and Large-Table Resilience
- [ ] T025 [US3] Implement unit test simulating large MAC table streaming with intermittent 5s pauses in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (simulate incremental messages with sleeps in mocks, assert collection to completion)
- [ ] T026 [US3] Verify wait_for_command_result parameterization in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (ensure activity_timeout_seconds flows from show_mac_table into the shared waiter)

Phase 7 — US4 (P2): Resource Cleanup on Any Exit Path
- [ ] T027 [US4] Implement unit tests for cleanup on success, error, and interrupt in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\tests\unit\test_show_mac_table.py (assert disconnect called exactly once for each path)
- [ ] T028 [US4] Ensure WebSocketManager.disconnect is idempotent or guarded in C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py (add guard or safe call so repeated disconnect calls are safe)

Final Phase — Polish & Cross-Cutting Concerns
---------------------------------------------
- [ ] T029 Update C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\specs\092-audit-menu-5-show-mac-table-via\quickstart.md with test run examples and developer notes reflecting new helper methods and test files
- [ ] T030 Run static checks and syntax validation: add documentation note to specs (manual step) — run "python -m py_compile C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py" and run "pytest tests/unit/ --maxfail=1 -q" as part of developer workflow

Dependencies (story completion order)
-------------------------------------
- US1 (Retrieve MAC table) -> US2 (Failure handling) -> US5 (Complete unit test coverage)
- US3 (Large-table resilience) and US4 (Cleanup) are P2 and can be worked in parallel after Foundational Phase

Parallel execution examples
---------------------------
- While T011..T015 (helper extraction and orchestration) are being implemented, a separate engineer can implement T016..T024 (unit tests) in parallel because tests mock external dependencies and operate on the public API of the methods [mark tasks with [P]].
- T006 (replace requests.post) and T013 (extract _trigger_mac_table_command) are parallelizable if T013's implementation references apisession; mark both [P].

Implementation strategy
-----------------------
- MVP: Deliver US1 happy-path only (T011..T016). This provides an executable feature with tests and enables incremental verification.
- Next: Implement US2 and US5 (error handling and full test coverage). Then address US3 and US4 (resilience & cleanup).
- Follow project conventions: keep each helper ≤25 lines, use full-word variable names, and avoid inline imports.

Validation checklist (format rules)
----------------------------------
- ALL tasks use the checklist format: "- [ ] T### [P?] [US?] Description with file path".
- Story tasks include [USx] label; Setup/Foundational/Polish tasks omit story label.

Notes for implementers
----------------------
- Tests must not perform real network calls; use unittest.mock.patch to mock WebSocketManager, apisession.mist_post, and PromptUtils selections.
- Use the existing pytest fixtures in tests/conftest.py (tmp_data_dir, isolate_working_directory).
- Keep changes localized to C:\Users\jmorrison\OneDrive - Juniper Networks, Inc\Code\MistHelper\MistHelper.py and tests under tests/unit/.

Generated-by: speckit.specify task generator
