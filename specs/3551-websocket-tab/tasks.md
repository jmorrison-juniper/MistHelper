---

description: "Task list for the WebSockets tab in the Operations portal"
---

# Tasks: WebSockets tab in the Operations portal

**Input**: The design documents in `specs/3551-websocket-tab/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [websockets-api.md](./contracts/websockets-api.md), and [quickstart.md](./quickstart.md)

**Tests**: The spec asks for tests. Each user story has an independent test. SC-003, SC-006, and SC-008 each need an automated test. The tests use fakes, so no test opens a Mist connection.

**Organization**: The tasks are grouped by user story. Each story is a complete increment that you can test alone.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It changes a different file and needs no open task.
- **[Story]**: The user story of the task, such as US1.
- Tick a task only after you verify the delivered file. Add an evidence note in this form: `(delivered: path/to/file.py)`.
- If a task needs a live system or a human decision, keep the box unchecked. Explain the condition in the task text.

## Rules for each source file

- Every executable line carries an inline comment that states the reason.
- Every action logs one `info` line before it and one `debug` line after it. Log text uses ASCII characters only.
- A function takes 5 parameters or fewer. It holds 5 blocks or fewer and 25 lines or fewer.
- A module holds 5 top-level constructs or fewer. A package holds 5 children or fewer, and `__init__.py` counts as a child.
- Every behavior lives in a named class. Do not add a wrapper function.
- Each test file name is unique in the repository, because pytest uses the default import mode.

## Phase 1: Setup

**Purpose**: Create the package tree and the configuration entries.

- [X] T001 Create the package tree in `src/websocket_streams/`. Put a docstring in each `__init__.py`. The folders are `catalog/`, `intake/`, `live/`, `live/sessions/`, `live/runners/`, and `web/`.
- [X] T002 [P] Create the test tree in `tests/unit/websocket_streams/`. Put an `__init__.py` in each folder. The folders are `catalog/`, `intake/`, `live/`, `live/sessions/`, `live/runners/`, and `web/`. Also create `tests/contract/websocket_streams/__init__.py`.
- [X] T003 [P] Add the 7 `PORTAL_WS_*` variables to `deploy/.env.example`. Give each variable its default, its range, and one plain comment.

---

## Phase 2: Foundational

**Purpose**: Build the shared types, the settings, the buffer, the session record, and the value checks. Every user story needs them.

**Checkpoint**: The foundational unit tests pass. Story work starts only after this point.

- [X] T004 Define the `FieldKind` and `Safety` enums in `src/websocket_streams/catalog/model.py`. Also define the `FieldSpec`, `ChannelDefinition`, and `UtilityDefinition` dataclasses. Follow data-model.md.
- [X] T005 [P] Implement `StreamSettings` in `src/websocket_streams/live/sessions/settings.py`. Read the 7 variables. A bad value gives the default and one warning with the variable name.
- [X] T006 [P] Implement `MessageBuffer` in `src/websocket_streams/live/sessions/buffer.py`. Enforce the message cap and the byte cap. Drop the oldest messages first and count them. Shorten a message above 256 KB and mark it.
- [X] T007 Implement `SessionState`, `SessionCounters`, and `StreamSession` in `src/websocket_streams/live/sessions/record.py`. Enforce the state machine of data-model.md. Give a page payload that holds no path and no token.
- [X] T008 [P] Implement `IdentifierRules` in `src/websocket_streams/intake/identifiers.py`. Check a UUID, a MAC address, a host, an IP address, and a prefix. Also check a Junos port name, a plain name, and a capture filter.
- [X] T009 Implement `FieldValueChecker` in `src/websocket_streams/intake/fields.py`. Check one value against one `FieldSpec`, and convert the value to the SDK type.
- [X] T010 [P] Write the unit tests for T004 in `tests/unit/websocket_streams/catalog/test_ws_catalog_model.py`.
- [X] T011 [P] Write the unit tests for T005 in `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`.
- [X] T012 [P] Write the unit tests for T006 in `tests/unit/websocket_streams/live/sessions/test_ws_message_buffer.py`.
- [X] T013 [P] Write the unit tests for T007 in `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`.
- [X] T014 [P] Write the unit tests for T008 in `tests/unit/websocket_streams/intake/test_ws_identifier_rules.py`.
- [X] T015 [P] Write the unit tests for T009 in `tests/unit/websocket_streams/intake/test_ws_field_checker.py`.

---

## Phase 3: User Story 1 - Watch a live channel stream (Priority: P1) MVP

**Goal**: An operator starts one of the 18 channels, reads each message, and uses the view controls.

**Independent Test**: Start a site device statistics stream with a fake SDK client. Confirm the messages and each control.

### Tests for User Story 1

- [X] T016 [P] [US1] Write the channel parity contract test in `tests/contract/websocket_streams/test_ws_channel_parity.py`. Create each public SDK channel class with test identifiers. Compare its channel list with the path that the catalog builds.
- [X] T017 [P] [US1] Write the SDK client contract test in `tests/contract/websocket_streams/test_ws_sdk_contract.py`. Pin the `_MistWebsocket` constructor parameters and the callback methods.
- [X] T018 [P] [US1] Write the channel catalog tests in `tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py`. Cover the 18 keys, the scopes, the path build, and the repeatable identifier.
- [X] T019 [P] [US1] Write the catalog registry tests in `tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py`. Prove that the page payload holds no path template.
- [X] T020 [P] [US1] Write the channel start request tests in `tests/unit/websocket_streams/intake/test_ws_start_request.py`. Refuse an unknown key, a raw path, an unknown field, and a bad identifier.
- [X] T021 [P] [US1] Write the message shaper tests in `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`. Cover a nested data string, plain text, and a large message.
- [X] T022 [P] [US1] Write the channel runner tests with a fake client in `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`. Cover a message, an error, a close, and a stop during the connection.
- [X] T023 [P] [US1] Write the manager tests for start, read, stop, delete, and download in `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
- [X] T024 [P] [US1] Write the blueprint tests in `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. Cover the page, the catalog, a start, a read, a stop, a delete, a download, and each error code.

### Implementation for User Story 1

- [X] T025 [US1] Implement `ChannelCatalog` with the 18 channels in `src/websocket_streams/catalog/channels.py`. Build a path only from a key and checked identifiers.
- [X] T026 [US1] Implement `StreamCatalog` in `src/websocket_streams/catalog/registry.py`. Give a lookup by kind and key, the flag state, and the page payload.
- [X] T027 [US1] Implement `StartRequest` and `StartRequestChecker` for a channel request in `src/websocket_streams/intake/start_request.py`.
- [X] T028 [P] [US1] Implement `MessageShaper` and `ShellAddressFilter` in `src/websocket_streams/live/runners/text.py`.
- [X] T029 [US1] Implement `ChannelStreamRunner` in `src/websocket_streams/live/runners/channel.py`. Use `_MistWebsocket` with the settings of research.md R-02.
- [X] T030 [US1] Implement `StreamSessionManager` in `src/websocket_streams/live/sessions/manager.py`. Give start, list, get, read after a sequence number, stop, delete, and download.
- [X] T031 [US1] Implement the site and map pickers of `StreamPickerService` in `src/websocket_streams/intake/pickers.py`.
- [X] T032 [US1] Implement `WebSocketsServices` in `src/websocket_streams/web/services.py`. Build the catalog, the checker, the pickers, and the manager one time for each app.
- [X] T033 [US1] Implement the blueprint routes of the contract in `src/websocket_streams/web/blueprint.py`. Each view calls one class method.
- [X] T034 [P] [US1] Write the page in `src/websocket_streams/web/templates/websockets_page.html`. Extend `base.html`, and give each control a `data-testid`.
- [X] T035 [P] [US1] Write `src/websocket_streams/web/static/websockets.js` and `websockets.css`. Render the catalog, fill the pickers, and start a stream. Poll each second. Give pause, resume, clear, filter, download, and stop.
- [X] T036 [US1] Register the blueprint in `web_portal/app.py`. Add the `nav-websockets` item after Maps in `web_portal/templates/base.html`.

**Checkpoint**: User Story 1 works alone. This is the MVP.

---

## Phase 4: User Story 2 - Run a read-only device utility (Priority: P1)

**Goal**: An operator chooses a device and runs a read-only utility, such as a ping.

**Independent Test**: Run a ping with a fake SDK utility that sends output lines. Confirm each line and the end state.

### Tests for User Story 2

- [X] T037 [P] [US2] Write the utility catalog tests in `tests/unit/websocket_streams/catalog/test_ws_utility_catalog.py`. Prove the count for each family and the safety classes.
- [X] T038 [P] [US2] Write the catalog coverage contract test in `tests/contract/websocket_streams/test_ws_catalog_coverage.py`. Compare the catalog with the facade `__all__` of each `mistapi.device_utils` module, less the named exclusions (SC-003).
- [X] T039 [P] [US2] Add the utility request tests to `tests/unit/websocket_streams/intake/test_ws_start_request.py`. Refuse a bad host, a count out of range, and a utility of another family.
- [X] T040 [P] [US2] Write the utility runner tests with a fake `UtilResponse` in `tests/unit/websocket_streams/live/runners/test_ws_utility_runner.py`. Cover each end state and a stop before the connection starts.
- [X] T041 [P] [US2] Write the device picker tests in `tests/unit/websocket_streams/intake/test_ws_stream_pickers.py`. Cover the family rules and an empty list.

### Implementation for User Story 2

- [X] T042 [US2] Implement `UtilityCatalog` in `src/websocket_streams/catalog/utilities.py`. Build the fields from each SDK signature and the field table of research.md.
- [X] T043 [US2] Add the utility request checks to `src/websocket_streams/intake/start_request.py`. Compare the device family with the utility family.
- [X] T044 [US2] Implement `UtilityRunner` in `src/websocket_streams/live/runners/utility.py`. Map the SDK result to the end states of research.md R-03.
- [X] T045 [US2] Add the device picker and the family rules to `src/websocket_streams/intake/pickers.py`.
- [X] T046 [US2] Add the device picker, the utility list, the parameter form, and the line and screen views to `src/websocket_streams/web/static/websockets.js`.

**Checkpoint**: User Stories 1 and 2 work alone.

---

## Phase 5: User Story 3 - Run a remote packet capture (Priority: P2)

**Goal**: An operator runs a capture of 60 seconds at most and reads one summary line for each packet.

**Independent Test**: Start a capture with a fake SDK utility that sends packet records. Confirm the summaries, the early stop, and the download.

### Tests for User Story 3

- [X] T047 [P] [US3] Add the capture tests to `tests/unit/websocket_streams/live/runners/test_ws_utility_runner.py`. Prove that an early stop ends only the capture of the session.
- [X] T048 [P] [US3] Add the packet summary tests to `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`. Cover a wired record, a wireless record, and a record with missing fields.
- [X] T049 [P] [US3] Add the capture range tests to `test_ws_start_request.py` in `tests/unit/websocket_streams/intake/`. Add the Mist Edge picker tests to `test_ws_stream_pickers.py` in the same folder.

### Implementation for User Story 3

- [X] T050 [US3] Add the capture fields to `src/websocket_streams/catalog/utilities.py`. Add the `device_interfaces` build to `src/websocket_streams/live/runners/utility.py`.
- [X] T051 [US3] Implement `CaptureStopper` in `src/websocket_streams/live/runners/utility.py`. Stop the capture only when the capture identifier matches.
- [X] T052 [P] [US3] Implement `PacketSummary` in `src/websocket_streams/live/runners/text.py`.
- [X] T053 [US3] Add the Mist Edge picker to `src/websocket_streams/intake/pickers.py`.
- [X] T054 [US3] Add the packet view to `src/websocket_streams/web/static/websockets.js`.

**Checkpoint**: User Stories 1 to 3 work alone.

---

## Phase 6: User Story 4 - Manage several sessions (Priority: P2)

**Goal**: The server enforces the session limit, stops idle and old sessions, and closes all sessions at shutdown.

**Independent Test**: Start sessions to the limit and read the refusal. Stop the reads of one session and confirm the idle stop.

### Tests for User Story 4

- [X] T055 [P] [US4] Add the limit, idle, life, and retention tests to `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`. Use a fake clock.
- [X] T056 [P] [US4] Write the shutdown tests in `tests/unit/websocket_streams/web/test_ws_web_services.py`. Prove that the portal shutdown stops every session.

### Implementation for User Story 4

- [X] T057 [US4] Add the session limit, the reaper, and the ended-session retention to `src/websocket_streams/live/sessions/manager.py`.
- [X] T058 [US4] Add the stop of every session to `src/websocket_streams/web/services.py`. Call it from `shutdown_app` in `web_portal/app.py`.
- [X] T059 [US4] Add the session list after a reload and the limit message to `src/websocket_streams/web/static/websockets.js`.

**Checkpoint**: User Stories 1 to 4 work alone.

---

## Phase 7: User Story 5 - Run a utility that changes device state (Priority: P3)

**Goal**: The change flag unlocks the 9 state-changing utilities. Each run needs the typed device name.

**Independent Test**: With the flag off, confirm each refusal. With the flag on, confirm that a wrong name is refused and a correct name runs.

### Tests for User Story 5

- [X] T060 [P] [US5] Add the lock tests to `tests/unit/websocket_streams/intake/test_ws_start_request.py`. Prove that no `change` entry starts while the flag is off (SC-008). Prove the confirmation check while the flag is on.
- [X] T061 [P] [US5] Add the audit log test to `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`. Prove that the log names the command, the device, and the site.

### Implementation for User Story 5

- [X] T062 [US5] Add the flag check and the device name check to `src/websocket_streams/intake/start_request.py`. Read the device name with `StreamPickerService`.
- [X] T063 [US5] Add the audit log line for each `change` run to `src/websocket_streams/live/sessions/manager.py`.
- [X] T064 [US5] Add the lock mark and the confirmation field to `src/websocket_streams/web/static/websockets.js`.

**Checkpoint**: User Stories 1 to 5 work alone.

---

## Phase 8: User Story 6 - Use the remote shell (Priority: P3)

**Goal**: The shell flag unlocks the EX and SRX shells. The operator sends lines and keys and reads the output.

**Independent Test**: With the flag off, confirm the refusal. With the flag on, open a shell with a fake SDK shell. Send a line, read the output, and close the shell.

### Tests for User Story 6

- [X] T065 [P] [US6] Write the shell runner tests in `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Cover the first-output gate, the keys, the ANSI removal, and the close.
- [X] T066 [P] [US6] Add the shell input route tests to `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. Prove that the log never holds the sent text.

### Implementation for User Story 6

- [X] T067 [US6] Implement `ShellRunner` in `src/websocket_streams/live/runners/shell.py`.
- [X] T068 [US6] Add the input route to `src/websocket_streams/web/blueprint.py`. Add the input method to `src/websocket_streams/live/sessions/manager.py`.
- [X] T069 [US6] Add the terminal view, the line field, and the key buttons to `src/websocket_streams/web/static/websockets.js`.

**Checkpoint**: All six user stories work alone.

---

## Phase 9: Polish and cross-cutting concerns

**Purpose**: Prove the security criteria, run the gates, and check the page in a live browser.

- [X] T070 [P] Write the secret test in `tests/unit/websocket_streams/web/test_ws_secret_guard.py`. Prove that no response holds the token or a `wss://` address (SC-006).
- [X] T071 [P] Write the browser journey in `tests/e2e/test_websockets_page.py`. Use a fake engine, and take one screenshot for each story.
- [X] T072 [P] Add the release note `changelog.d/issue-3551-websocket-tab.md`.
- [X] T073 Run the gates and repair each finding. The gates are py_compile, `ruff check .`, `black --check .`, mypy with `MYPY_PATHS`, pytest with coverage, Vulture, pydocstyle, interrogate, Bandit, Radon, and Pylint.
- [X] T074 Run the live check of quickstart.md against the real organization. Use read-only entries only. Take screenshots and read them.
- [X] T075 Run the load check of SC-004 and SC-005 with 5 fake sessions at 10 messages each second. Record the results in the pull request.
- [X] T076 Run the STE check on each changed Markdown file and on the pull request body. Each text must score 80 or more with 0 errors.
- [X] T077 Update data-model.md, the contract, and quickstart.md where the code differs from the design.

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: No dependency. Start at once.
- **Foundational (Phase 2)**: It needs Phase 1. It blocks every user story.
- **User Story 1 (Phase 3)**: It needs Phase 2. It builds the manager, the blueprint, and the page that the later stories extend.
- **User Stories 2 to 6 (Phases 4 to 8)**: Each one needs Phase 3. They change the same files, so do them in priority order.
- **Polish (Phase 9)**: It needs every story that you want to ship.

### Order inside a story

- Write the tests first, and confirm that they fail.
- Build the catalog entries, then the checks, then the runner, then the routes, then the page.
- Finish the story, and pass its independent test, before the next story starts.

### Parallel opportunities

- T002 and T003 run in parallel with T001.
- T005, T006, and T008 run in parallel after T004.
- The six foundational test files T010 to T015 run in parallel.
- In each story, the test tasks marked [P] run in parallel.
- T028, T034, and T035 run in parallel with the catalog and manager tasks of US1.
- T070, T071, and T072 run in parallel.

## Parallel example: User Story 1

```text
Task: "T016 channel parity contract test in tests/contract/websocket_streams/test_ws_channel_parity.py"
Task: "T017 SDK client contract test in tests/contract/websocket_streams/test_ws_sdk_contract.py"
Task: "T018 channel catalog tests in tests/unit/websocket_streams/catalog/test_ws_channel_catalog.py"
Task: "T021 message shaper tests in tests/unit/websocket_streams/live/runners/test_ws_message_text.py"
Task: "T034 page template in src/websocket_streams/web/templates/websockets_page.html"
```

## Implementation strategy

### MVP first

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3, User Story 1.
3. Stop and run the independent test of User Story 1.
4. If the test passes, the channel streams are ready.

### Incremental delivery

1. Add User Story 2, the read-only utilities, and test it alone.
2. Add User Story 3, the captures, and test it alone.
3. Add User Story 4, the session limits, and test it alone.
4. Add User Stories 5 and 6. Both stay locked by default.
5. Ship all stories in one pull request for issue #3551.

### Team strategy with agents

1. One agent builds Phase 2 and the catalog, the checks, and the sessions of each story.
2. After that work is ready, one agent builds the runners, and one agent builds the pickers, the blueprint, and the page.
3. The lead agent joins the parts, runs the gates, and runs the live check.
