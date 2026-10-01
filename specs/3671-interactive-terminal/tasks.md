---
description: "Task list for the own Mist WebSocket client and the interactive terminal"
---

# Tasks: Own Mist WebSocket Client and Interactive Terminal

**Input**: The design documents in `specs/3671-interactive-terminal/`.

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, and
quickstart.md.

**Tests**: The spec asks for tests. SC-001 to SC-008 need unit tests, contract tests, and
browser journeys with screenshots. Each story phase starts with its tests.

**Organization**: The tasks are in a group for each user story. Each story has its own test.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It changes other files, and it needs no open task.
- **[Story]**: The user story of the task, for example US1.
- Each task names the exact file paths.
- Tick a task only after you verify the delivered file. Add an evidence note in this form:
  `(delivered: path/to/file.py)`.
- If a task needs a live system or a human decision, keep the box clear. State the
  condition in the task text.

## Builder lanes

The fleet uses five lanes. No two lanes change the same file.

| Lane | Owner | Tasks |
| - | - | - |
| A. Transport and fake cloud | Builder A | T006 to T015 |
| B. Trigger table and parity | Builder B | T034 to T037 |
| C. Page and vendored terminal | Builder C | T003, T029, T031, T042, and T048 |
| D. Terminal core | Builder D | T016 to T020, T022, T026, and T033 |
| E. Runners, routes, and journeys | The lead agent | All other tasks |

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Make the package layout and the shared values before the lanes start.

- [ ] T001 Move `src/websocket_streams/live/runners/utility.py` to
  `src/websocket_streams/live/runners/utility/runner.py` with `git mv`. Add an `__init__.py`
  that holds a docstring only. Change each import to
  `src.websocket_streams.live.runners.utility.runner`. Move
  `tests/unit/websocket_streams/live/runners/test_ws_utility_runner.py` to
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py` with an
  `__init__.py`. Run the moved tests.
- [ ] T002 Create each new package with an `__init__.py` that holds a docstring only:
  `src/websocket_streams/live/transport/`, `src/websocket_streams/live/terminal/`,
  `tests/unit/websocket_streams/live/transport/`,
  `tests/unit/websocket_streams/live/terminal/`, and `tests/support/fake_mist_cloud/`.
- [ ] T003 [P] Copy xterm.js 6.0.0 and the fit addon 0.11.0 into
  `src/websocket_streams/web/static/vendor/xterm/`. Copy `lib/xterm.js` as `xterm.min.js`,
  `lib/addon-fit.js` as `addon-fit.min.js`, and `css/xterm.css`. Put the MIT license text of
  both packages in `LICENSE`. Add `README.md` with the versions, the source address, and the
  SHA-256 value of each file.
- [ ] T004 [P] Add the codes `not_terminal` (409), `read_only` (409), `input_full` (409),
  `too_large` (413), and `rate_limited` (429) to `StreamRequestError.STATUS_BY_CODE` in
  `src/websocket_streams/intake/fields.py`. Test each code in
  `tests/unit/websocket_streams/intake/test_ws_field_checker.py`.
- [ ] T005 [P] Add `terminal_history_bytes` to `StreamSettings` in
  `src/websocket_streams/live/sessions/settings.py`. Read `PORTAL_WS_TERMINAL_HISTORY_KB`.
  The range is 256 to 8,192, and the default is 1,024. Document the setting in
  `deploy/.env.example`. Test the default, the range, and a bad value in
  `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the connection classes, the fake Mist cloud, and the terminal core.

**Critical**: No story work starts before this phase ends.

- [ ] T006 [P] Build the fake Mist cloud server in
  `tests/support/fake_mist_cloud/server.py`. Use the standard library only. Speak RFC 6455:
  the opening handshake, masked client frames, text, binary, continuation, ping, pong, and
  close. Serve `ws://127.0.0.1` on a free port. Record each received frame with its type
  and its bytes. Send each path to a device handler.
- [ ] T007 [P] Build the fake devices in `tests/support/fake_mist_cloud/devices.py`. The
  stream device sends subscribe answers, data events, `subscribe_failed`, and a dropped
  connection. The command device sends events with a `session` value, also before the
  trigger answer. The capture device sends events with `capture_id` and `pcap_dict`. The
  shell device echoes text, shows a prompt, and handles `\x03` and `exit`. It also turns
  on the bracketed paste mode and draws a full-screen color program. The screen device
  breaks screen updates inside a control sequence.
- [ ] T008 [P] Build the fake API session in `tests/support/fake_mist_cloud/api.py`. Give
  it `_cloud_uri`, `_apitoken`, `_apitoken_index`, and `_session`. Record each `mist_post`,
  `mist_get`, and `mist_delete` call. Answer a trigger with a command `session`, a capture
  `id`, or a shell `url` on the fake server.
- [ ] T009 [P] Write the endpoint tests in
  `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`. Cover the stream
  address of each cloud region, the token header, and the cookie text. Cover a cookie with
  CR or LF, the TLS options, and the host label. Cover the policy for `wss` in the Mist domain, for
  `ws`, for another domain, and for a look-alike domain such as `mist.com.example.net`.
- [ ] T010 [P] Write the frame tests in
  `tests/unit/websocket_streams/live/transport/test_ws_frames.py`. Cover the NUL removal,
  text that is not JSON, JSON text inside `data`, and a binary frame that holds JSON.
- [ ] T011 [P] Write the client tests against the fake server in
  `tests/unit/websocket_streams/live/transport/test_ws_stream_client.py` and
  `tests/unit/websocket_streams/live/transport/test_ws_shell_client.py`. Cover the
  subscribe wait for each channel, `subscribe_failed`, the ping after a quiet interval, and
  the close after 2 silent intervals. Cover a close from another thread, the NUL input
  prefix, the resize frame, and a send from a second thread.
- [ ] T012 Implement `MistStreamEndpoint` and `ShellAddressPolicy` in
  `src/websocket_streams/live/transport/endpoint.py` per `contracts/transport.md`.
- [ ] T013 [P] Implement `FrameDecoder` in `src/websocket_streams/live/transport/frames.py`
  per `contracts/transport.md`.
- [ ] T014 Implement `StreamClient` in
  `src/websocket_streams/live/transport/stream_client.py` and `ShellClient` in
  `src/websocket_streams/live/transport/shell_client.py`. Use `websocket.create_connection`
  with `enable_multithread=True`. Take the socket factory and the clock as constructor
  values.
- [ ] T015 [P] Pin the private API session attributes `_cloud_uri`, `_apitoken`,
  `_apitoken_index`, and `_session` in
  `tests/contract/websocket_streams/test_ws_sdk_contract.py`.
- [ ] T016 [P] Write the history tests and the input tests in
  `tests/unit/websocket_streams/live/terminal/test_ws_byte_history.py` and
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_input.py`. Cover the trim,
  the gap, a bad position, the wait, the close, and the 512 KiB answer limit. Cover the
  queue limit, the release order, the 16 KiB limit, and the rate limit.
- [ ] T017 [P] Implement `ByteHistory` in
  `src/websocket_streams/live/terminal/byte_history.py` per `data-model.md`.
- [ ] T018 [P] Implement `TerminalInput` in
  `src/websocket_streams/live/terminal/input_queue.py` per `data-model.md`.
- [ ] T019 Implement `TerminalState` and `TerminalChunk` in
  `src/websocket_streams/live/terminal/state.py` per `data-model.md`.
- [ ] T020 Change `StreamSession` in `src/websocket_streams/live/sessions/record.py`. Add
  the `terminal` value and the `add_bytes(data)` method to the record and to the
  `SessionSink` protocol. Release the input queue in `mark_input_ready`. Close the history
  and the input in `finish`. Add the payload field `terminal`. Test the change in
  `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`.

**Checkpoint**: The connection classes, the fake cloud, and the terminal core pass their
tests.

---

## Phase 3: User Story 1 - Work in a device shell like a desktop terminal (Priority: P1) MVP

**Goal**: An operator types in a real terminal. Each key goes to the device in order.

**Independent Test**: Open a shell against the fake shell device. Type text and special
keys, and resize the panel. The fake device receives each byte in order.

### Tests for User Story 1

- [ ] T021 [P] [US1] Write the shell runner tests in
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Use the fake API
  session and the fake shell device. Cover the trigger request, the address check, the
  start size, the first output, the queued keys, and the resize. Cover the device close,
  the operator stop, and a refused address.
- [ ] T022 [P] [US1] Write the gateway tests in
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`. Cover a read
  with no wait, a read that waits, the limit of 8 waiting reads, and an ended session.
  Cover `not_terminal`, `read_only`, a queued send, `too_large`, `rate_limited`, and the
  resize range.
- [ ] T023 [P] [US1] Write the route tests in
  `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. Cover the terminal read
  route, the input route, and the resize route. Cover the refused `line` and `key` body
  shapes, the error shape, and a POST without the form token.

### Implementation for User Story 1

- [ ] T024 [US1] Rewrite `ShellRunner` in `src/websocket_streams/live/runners/shell.py`.
  Send the shell trigger with `mist_post`, check the address, and open `ShellClient` with
  the stored size. Append each output to the history. Remove the import of the software
  kit shell.
- [ ] T025 [US1] Remove `MessageShaper.clean_shell_text` from
  `src/websocket_streams/live/runners/text.py`, and remove its test from
  `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`. Keep
  `ShellAddressFilter`, because the REST layer of the software kit can log the address.
- [ ] T026 [US1] Implement `TerminalGateway` in
  `src/websocket_streams/live/terminal/gateway.py` per `contracts/terminal-http.md`.
- [ ] T027 [US1] Change `src/websocket_streams/live/sessions/manager.py`. Build a
  `TerminalState` for each shell session and each screen session, and bind the input
  sender. Replace `send_input`, `_input_text`, `_key_text`, and `KEY_INPUTS` with a public
  `session(session_id)` method. Give `RunnerFactory` an optional transport profile for the
  tests. Update `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
- [ ] T028 [US1] Add `terminal_read`, `terminal_input`, and `terminal_resize` to
  `WebSocketsServices` in `src/websocket_streams/web/services.py`, and remove the old
  `send_input`. Add the three routes to `src/websocket_streams/web/blueprint.py`. Update
  `tests/unit/websocket_streams/web/test_ws_web_services.py`.
- [ ] T029 [US1] Add `TerminalController` in
  `src/websocket_streams/web/static/websockets_terminal.js` per
  `contracts/terminal-page.md`. It starts xterm.js and the fit addon, runs the read loop,
  and sends the keys and the size. It shows the status line, the warning, the time notice,
  and the gap notice. Load the vendored files and add the panel in
  `src/websocket_streams/web/templates/websockets_page.html`. Give each session with
  `terminal: true` to the controller in `src/websocket_streams/web/static/websockets.js`,
  and remove the old shell line field. Add the panel styles to
  `src/websocket_streams/web/static/websockets.css`.
- [ ] T030 [US1] Write the journeys J1 to J8 in `tests/e2e/test_websockets_terminal.py`.
  Use the real services, the real manager, the real runners, and the fake Mist cloud.
  Cover the banner, typed text, each special key, Ctrl+C with no selection, the resize,
  early keys, the device close, and a full-screen color program. Save a screenshot for
  each journey in `test-artifacts/websockets-terminal/`, and read each screenshot.

**Checkpoint**: The shell works as a terminal in the browser.

---

## Phase 4: User Story 2 - Copy and paste like a desktop terminal (Priority: P1)

**Goal**: The clipboard works like SecureCRT and Windows Terminal.

**Independent Test**: Select text and read the system clipboard. Paste with each paste
command, and compare the bytes that the fake device receives.

- [ ] T031 [US2] Add the clipboard classes to
  `src/websocket_streams/web/static/websockets_terminal.js`. The class `TerminalClipboard`
  copies on a secure page and on an HTTP page. The class `PasteFlow` applies the limit, the
  confirmation, parts of 4 KiB with one request in flight, and the progress. The class
  `TerminalKeys` applies the copy and paste key rules. The class `TerminalMenu` holds Copy,
  Paste, Select all, and Clear. The class `TerminalPreferences` keeps the settings in local
  storage. Add the dialog, the menu, the settings, and the notice to
  `src/websocket_streams/web/templates/websockets_page.html`.
- [ ] T032 [US2] Write the journeys J9 to J18 in `tests/e2e/test_websockets_terminal.py`.
  Cover copy by selection on and off, each copy key, and Ctrl+C with a selection. Cover
  each paste key with the exact bytes, the confirmation Cancel and Paste, bracketed paste,
  and a 2,000-line paste. Cover copy on an HTTP page from a host name that is not local,
  the paste limit, and the kept settings.
- [ ] T033 [P] [US2] Add a paste test with 100 runs to
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`. Send 2,000
  lines in parts of 4 KiB through the gateway to the fake shell device. Compare the
  received bytes in each run (SC-002).

**Checkpoint**: Each copy action and each paste action passes in the browser.

---

## Phase 5: User Story 3 - Get the full output of each device command (Priority: P1)

**Goal**: Each device command gives its full output in each run.

**Independent Test**: Run Show ARP 100 times against a fake device that answers at once.
Each run shows the full output.

- [ ] T034 [P] [US3] Write the parity contract test in
  `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py`. Call each software
  kit utility with a recording API session. Compare the method, the path, and the body
  with the trigger table for each of the 52 commands and for the shell trigger.
- [ ] T035 [P] [US3] Write the trigger tests and the filter tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py` and
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_filters.py`.
- [ ] T036 [P] [US3] Implement `UtilityTriggerTable` and `UtilityRequest` in
  `src/websocket_streams/live/runners/utility/triggers.py`. Hold the quiet time of each
  command, with 5 seconds or more.
- [ ] T037 [P] [US3] Implement `UtilityMessageFilter` in
  `src/websocket_streams/live/runners/utility/filters.py`. Keep the early events. Filter
  command events by `session` and capture events by `capture_id`.
- [ ] T038 [US3] Rewrite `UtilityRunner` in
  `src/websocket_streams/live/runners/utility/runner.py`. Open `StreamClient`, wait for the
  subscription, send the trigger with `mist_post`, and filter the events. Apply the first
  output limit, the quiet time, and the total limit. Stop within 3 seconds. Keep
  `CaptureStopper`.
- [ ] T039 [US3] Update the runner tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`. Add the
  order test, the early event test, the three limit tests, and the stop test. Add 100 runs
  of Show ARP against a fake device that answers at once (SC-003).

**Checkpoint**: Each command keeps its first output lines.

---

## Phase 6: User Story 4 - See a correct live screen for Top and Monitor Traffic (Priority: P2)

**Goal**: The screen commands show no stray characters.

**Independent Test**: Send screen updates that break inside a control sequence. The page
shows the correct screen.

- [ ] T040 [P] [US4] Write the screen runner tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_screen_runner.py`.
- [ ] T041 [US4] Implement `ScreenRunner` in
  `src/websocket_streams/live/runners/utility/screen.py`. Send the trigger, check the
  address, and append the raw bytes to the history. Build it in `RunnerFactory` for Top
  and Monitor Traffic.
- [ ] T042 [US4] Show each screen session in a read-only terminal in
  `src/websocket_streams/web/static/websockets_terminal.js` and
  `src/websocket_streams/web/static/websockets.js`. Remove the old screen view.
- [ ] T043 [US4] Write the journeys J19 and J20 in `tests/e2e/test_websockets_terminal.py`.
  Send 100 screen updates with split control sequences, and check the screen text
  (SC-008). Check that typed keys send nothing.

**Checkpoint**: Top and Monitor Traffic show a clean screen.

---

## Phase 7: User Story 5 - Keep the live streams and captures that work today (Priority: P2)

**Goal**: The channel streams and the captures use the own client with the same behavior.

**Independent Test**: Run each channel stream and each capture against the fake cloud.
Compare the messages, the states, and the end reasons.

- [ ] T044 [P] [US5] Update the channel runner tests in
  `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`. Cover 3 new
  connections after 1, 2, and 4 seconds, and the failure after the third attempt. Cover a
  refused channel and the source map.
- [ ] T045 [US5] Rewrite `ChannelStreamRunner` in
  `src/websocket_streams/live/runners/channel.py` to use `StreamClient`. Remove the import
  of the private `_MistWebsocket` class.
- [ ] T046 [US5] Test the capture path in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`. Cover the
  capture filter, the packet summary, and the stop request.
- [ ] T047 [US5] Update `tests/contract/websocket_streams/test_ws_channel_parity.py` and
  `tests/e2e/test_websockets_page.py` for the own client and the terminal panel.

**Checkpoint**: The streams and the captures pass their old tests and their new tests.

---

## Phase 8: User Story 6 - Save the terminal history as text (Priority: P3)

**Goal**: An operator saves the terminal history as a text file.

**Independent Test**: Run commands, select Download, and compare the file with the screen.

- [ ] T048 [US6] Add the history file to
  `src/websocket_streams/web/static/websockets_terminal.js`. Build the text from the
  xterm.js buffer with no control codes, and save it as a file.
- [ ] T049 [US6] Write the journey J21 in `tests/e2e/test_websockets_terminal.py`. Compare
  the file text with the screen text.

**Checkpoint**: All stories work on their own.

---

## Phase 9: Polish and Cross-Cutting Concerns

**Purpose**: Prove the performance, the log safety, and the delivery.

- [ ] T050 Write the performance journeys in
  `tests/e2e/test_websockets_terminal_performance.py`. Measure the echo time for 200 keys
  (SC-001), 1 MB of output (SC-007), and 5 busy shells with page loads (SC-005). Record
  each number.
- [ ] T051 Write the log scan journey J22 in `tests/e2e/test_websockets_terminal.py`
  (SC-006).
- [ ] T052 [P] Update `documentation/operator-guide.md` and
  `documentation/wiki/Web-Portal.md` for the terminal, the copy keys, the paste keys, and
  the new setting.
- [ ] T053 [P] Add the release note `changelog.d/issue-3671-interactive-terminal.md`.
- [ ] T054 Run the quality gates per `quickstart.md`. Also run mypy with `MYPY_PATHS`,
  Bandit, Vulture, pydocstyle, and the complexity gate. Fix each finding.
- [ ] T055 Run the live checks per `quickstart.md` section 5. Record the shell host, the
  NUL prefix result, and the longest pause of Show ARP and Show Route. If a pause is longer
  than 5 seconds, change the quiet time in the trigger table.
- [ ] T056 Run speckit-analyze. Then open the pull request with `Closes #3671`,
  `Closes #3659`, and `Closes #3660`.

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependency. T001 and T002 run first, because the lanes need the folders.
- Phase 2 depends on Phase 1. It blocks each story.
- Phase 3 to Phase 8 depend on Phase 2.
- Phase 9 depends on each story that the release holds.

### User Story Dependencies

- US1 needs the terminal core and `ShellClient`.
- US2 needs the US1 panel.
- US3 needs `StreamClient` and the trigger table.
- US4 needs `ShellClient`, the trigger table, and the US1 panel.
- US5 needs `StreamClient`.
- US6 needs the US1 panel.

### Within Each User Story

- Write the tests first, and see them fail.
- Build the classes, then the routes, then the page.
- End the story at its checkpoint.

### Parallel Opportunities

- Lanes A, B, C, and D run at the same time after T001 and T002.
- Each task with `[P]` in one phase can run at the same time as the other `[P]` tasks.
- The lead agent writes T004, T005, T023, T027, and T028 while the lanes build.

---

## Parallel Example: Phase 2

```text
Builder A: T006 to T015 (transport and fake cloud)
Builder B: T034 to T037 (trigger table, filters, and parity)
Builder C: T003 and T029 (vendored terminal and panel)
Builder D: T016 to T020 and T022 (terminal core and gateway tests)
Lead:      T004, T005, T023, T027, and T028
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Finish Phase 1 and Phase 2.
2. Finish Phase 3.
3. Stop and check the shell journeys with screenshots.

### Incremental Delivery

1. Add US2, because copy and paste are part of a usable terminal.
2. Add US3, because it repairs issue #3660.
3. Add US4, because it repairs issue #3659.
4. Add US5, because it removes the last live connection of the software kit.
5. Add US6.
6. Deliver all stories in one pull request, because the shell, the commands, and the
   streams share the new client.

## Notes

- Each executable line gets an inline comment. Each action logs before and after.
- No log holds a token, a cookie, an address path, a key, pasted text, or output.
- Commit after each lane merges into the feature branch.
