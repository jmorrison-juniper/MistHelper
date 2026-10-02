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
| D. Terminal core | Builder D | T016 to T020, T022, and T026 |
| E. Runners, routes, and journeys | The lead agent | All other tasks |

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Make the package layout and the shared values before the lanes start.

- [X] T001 Move `src/websocket_streams/live/runners/utility.py` to
  `src/websocket_streams/live/runners/utility/runner.py` with `git mv`. Add an `__init__.py`
  that holds a docstring only. Change each import to
  `src.websocket_streams.live.runners.utility.runner`. Move
  `tests/unit/websocket_streams/live/runners/test_ws_utility_runner.py` to
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py` with an
  `__init__.py`. Run the moved tests.
  (delivered: `src/websocket_streams/live/runners/utility/runner.py`, `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`)
- [X] T002 Create each new package with an `__init__.py` that holds a docstring only:
  `src/websocket_streams/live/transport/`, `src/websocket_streams/live/terminal/`,
  `tests/unit/websocket_streams/live/transport/`,
  `tests/unit/websocket_streams/live/terminal/`, and `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`.
  T062 moved the fake cloud package to this path.
  (delivered: `src/websocket_streams/live/transport/`, `src/websocket_streams/live/terminal/`, `tests/unit/websocket_streams/live/transport/`, `tests/unit/websocket_streams/live/terminal/`, `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`)
- [X] T003 [P] Copy xterm.js 6.0.0 and the fit addon 0.11.0 into
  `src/websocket_streams/web/static/vendor/xterm/`. Copy `lib/xterm.js` as `xterm.min.js`,
  `lib/addon-fit.js` as `addon-fit.min.js`, and `css/xterm.css`. Put the MIT license text of
  both packages in `LICENSE`. Add `README.md` with the versions, the source address, and the
  SHA-256 value of each file.
  (delivered: `src/websocket_streams/web/static/vendor/xterm/`)
- [X] T004 [P] Add the codes `not_terminal` (409), `read_only` (409), `input_full` (409),
  `too_large` (413), and `rate_limited` (429) to `StreamRequestError.STATUS_BY_CODE` in
  `src/websocket_streams/intake/fields.py`. Test each code in
  `tests/unit/websocket_streams/intake/test_ws_field_checker.py`.
  (delivered: `src/websocket_streams/intake/fields.py`, `tests/unit/websocket_streams/intake/test_ws_field_checker.py`)
- [X] T005 [P] Add `terminal_history_bytes` to `StreamSettings` in
  `src/websocket_streams/live/sessions/settings.py`. Read `PORTAL_WS_TERMINAL_HISTORY_KB`.
  The range is 256 to 8,192, and the default is 1,024. Document the setting in
  `deploy/.env.example`. Test the default, the range, and a bad value in
  `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`.
  (delivered: `src/websocket_streams/live/sessions/settings.py`, `deploy/.env.example`, `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the connection classes, the fake Mist cloud, and the terminal core.

**Critical**: No story work starts before this phase ends.

- [X] T006 [P] Build the fake Mist cloud server in
  `tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py`. Use the standard library only. Speak RFC 6455:
  the opening handshake, masked client frames, text, binary, continuation, ping, pong, and
  close. Serve `ws://127.0.0.1` on a free port. Record each received frame with its type
  and its bytes. Send each path to a device handler.
  (delivered: `tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py`)
- [X] T007 [P] Build the fake devices in `tests/unit/websocket_streams/live/transport/fake_mist_cloud/devices.py`. The
  stream device sends subscribe answers, data events, `subscribe_failed`, and a dropped
  connection. The command device sends events with a `session` value, also before the
  trigger answer. The capture device sends events with `capture_id` and `pcap_dict`. The
  shell device echoes text, shows a prompt, and handles `\x03` and `exit`. It also turns
  on the bracketed paste mode and draws a full-screen color program. The screen device
  breaks screen updates inside a control sequence.
  (delivered: `tests/unit/websocket_streams/live/transport/fake_mist_cloud/devices.py`)
- [X] T008 [P] Build the fake API session in `tests/unit/websocket_streams/live/transport/fake_mist_cloud/api.py`. Give
  it `_cloud_uri`, `_apitoken`, `_apitoken_index`, and `_session`. Record each `mist_post`,
  `mist_get`, and `mist_delete` call. Answer a trigger with a command `session`, a capture
  `id`, or a shell `url` on the fake server.
  (delivered: `tests/unit/websocket_streams/live/transport/fake_mist_cloud/api.py`)
- [X] T009 [P] Write the endpoint tests in
  `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`. Cover the stream
  address of each cloud region, the token header, and the cookie text. Cover a cookie with
  CR or LF, the TLS options, and the host label. Cover the policy for `wss` in the Mist domain, for
  `ws`, for another domain, and for a look-alike domain such as `mist.com.example.net`.
  (delivered: `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`)
- [X] T010 [P] Write the frame tests in
  `tests/unit/websocket_streams/live/transport/test_ws_frames.py`. Cover the NUL removal,
  text that is not JSON, JSON text inside `data`, and a binary frame that holds JSON.
  (delivered: `tests/unit/websocket_streams/live/transport/test_ws_frames.py`)
- [X] T011 [P] Write the client tests against the fake server in
  `tests/unit/websocket_streams/live/transport/clients/test_ws_stream_client.py` and
  `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`. Cover the
  subscribe wait for each channel, `subscribe_failed`, the ping after a quiet interval, and
  the close after 2 silent intervals. Cover a close from another thread, the NUL input
  prefix, the resize frame, and a send from a second thread.
  (delivered: `tests/unit/websocket_streams/live/transport/clients/test_ws_stream_client.py`, `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`)
- [X] T012 Implement `MistStreamEndpoint` and `ShellAddressPolicy` in
  `src/websocket_streams/live/transport/endpoint.py` per `contracts/transport.md`.
  (delivered: `src/websocket_streams/live/transport/endpoint.py`)
- [X] T013 [P] Implement `FrameDecoder` in `src/websocket_streams/live/transport/frames.py`
  per `contracts/transport.md`.
  (delivered: `src/websocket_streams/live/transport/frames.py`)
- [X] T014 Implement `StreamClient` in
  `src/websocket_streams/live/transport/stream_client.py` and `ShellClient` in
  `src/websocket_streams/live/transport/shell_client.py`. Use `websocket.create_connection`
  with `enable_multithread=True`. Take the socket factory and the clock as constructor
  values.
  (delivered: `src/websocket_streams/live/transport/stream_client.py`, `src/websocket_streams/live/transport/shell_client.py`)
- [X] T015 [P] Pin the private API session attributes `_cloud_uri`, `_apitoken`,
  `_apitoken_index`, and `_session` in
  `tests/contract/websocket_streams/test_ws_sdk_contract.py`.
  (delivered: `tests/contract/websocket_streams/test_ws_sdk_contract.py`)
- [X] T016 [P] Write the history tests and the input tests in
  `tests/unit/websocket_streams/live/terminal/test_ws_byte_history.py` and
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_input.py`. Cover the trim,
  the gap, a bad position, the wait, the close, and the 512 KiB answer limit. Cover the
  queue limit, the release order, the 16 KiB limit, and the rate limit.
  (delivered: `tests/unit/websocket_streams/live/terminal/test_ws_byte_history.py`, `tests/unit/websocket_streams/live/terminal/test_ws_terminal_input.py`)
- [X] T017 [P] Implement `ByteHistory` in
  `src/websocket_streams/live/terminal/byte_history.py` per `data-model.md`.
  (delivered: `src/websocket_streams/live/terminal/byte_history.py`)
- [X] T018 [P] Implement `TerminalInput` in
  `src/websocket_streams/live/terminal/input_queue.py` per `data-model.md`.
  (delivered: `src/websocket_streams/live/terminal/input_queue.py`)
- [X] T019 Implement `TerminalState` and `TerminalChunk` in
  `src/websocket_streams/live/terminal/state.py` per `data-model.md`.
  (delivered: `src/websocket_streams/live/terminal/state.py`)
- [X] T020 Change `StreamSession` in `src/websocket_streams/live/sessions/record.py`. Add
  the `terminal` value and the `add_bytes(data)` method to the record and to the
  `SessionSink` protocol. Release the input queue in `mark_input_ready`. Close the history
  and the input in `finish`. Add the payload field `terminal`. Test the change in
  `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`.
  (delivered: `src/websocket_streams/live/sessions/record.py`, `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`)
- [x] T063 [P] Prove the proxy part of FR-005 in
  `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`. The client
  gives no proxy option to websocket-client. The library then reads `https_proxy` and
  `no_proxy` from the host.
  (delivered: `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`)
- [x] T064 Add `ConnectFailure` to `src/websocket_streams/live/transport/endpoint.py`. It
  changes each open error to a plain reason. In
  `src/websocket_streams/live/runners/channel.py`, a channel stream does not connect again
  after an HTTP 4xx refusal, except 408 and 429 (finding M1). Test the reasons in
  `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py` and the rule in
  `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`.
  (delivered: `src/websocket_streams/live/transport/endpoint.py`, `src/websocket_streams/live/runners/channel.py`, `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`, `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`)

**Checkpoint**: The connection classes, the fake cloud, and the terminal core pass their
tests.

---

## Phase 3: User Story 1 - Work in a device shell like a desktop terminal (Priority: P1) MVP

**Goal**: An operator types in a real terminal. Each key goes to the device in order.

**Independent Test**: Open a shell against the fake shell device. Type text and special
keys, and resize the panel. The fake device receives each byte in order.

### Tests for User Story 1

- [X] T021 [P] [US1] Write the shell runner tests in
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Use the fake API
  session and the fake shell device. Cover the trigger request, the address check, the
  start size, the first output, the queued keys, and the resize. Cover the device close,
  the operator stop, and a refused address.
  (delivered: `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`)
- [X] T022 [P] [US1] Write the gateway tests in
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`. Cover a read
  with no wait, a read that waits, the limit of 8 waiting reads, and an ended session.
  Cover `not_terminal`, `read_only`, a queued send, `too_large`, `rate_limited`, and the
  resize range.
  (delivered: `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`)
- [X] T023 [P] [US1] Write the route tests in
  `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. Cover the terminal read
  route, the input route, and the resize route. Cover the refused `line` and `key` body
  shapes, the error shape, and a POST without the form token.
  (delivered: `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`)

### Implementation for User Story 1

- [X] T024 [US1] Rewrite `ShellRunner` in `src/websocket_streams/live/runners/shell.py`.
  Send the shell trigger with `mist_post`, check the address, and open `ShellClient` with
  the stored size. Append each output to the history. Remove the import of the software
  kit shell.
  (delivered: `src/websocket_streams/live/runners/shell.py`)
- [X] T025 [US1] Remove `MessageShaper.clean_shell_text` from
  `src/websocket_streams/live/runners/text.py`, and remove its test from
  `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`. Keep
  `ShellAddressFilter`, because the REST layer of the software kit can log the address.
  (delivered: `src/websocket_streams/live/runners/text.py`, `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`)
- [X] T026 [US1] Implement `TerminalGateway` in
  `src/websocket_streams/live/terminal/gateway.py` per `contracts/terminal-http.md`.
  (delivered: `src/websocket_streams/live/terminal/gateway.py`)
- [X] T027 [US1] Change `src/websocket_streams/live/sessions/manager.py`. Build a
  `TerminalState` for each shell session and each screen session, and bind the input
  sender. Replace `send_input`, `_input_text`, `_key_text`, and `KEY_INPUTS` with a public
  `session(session_id)` method. Give `RunnerFactory` an optional transport profile for the
  tests. Update `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
  (delivered: `src/websocket_streams/live/sessions/manager.py`, `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`)
- [X] T028 [US1] Add `terminal_read`, `terminal_input`, and `terminal_resize` to
  `WebSocketsServices` in `src/websocket_streams/web/services.py`, and remove the old
  `send_input`. Add the three routes to `src/websocket_streams/web/blueprint.py`. Update
  `tests/unit/websocket_streams/web/test_ws_web_services.py`.
  (delivered: `src/websocket_streams/web/services.py`, `src/websocket_streams/web/blueprint.py`, `tests/unit/websocket_streams/web/test_ws_web_services.py`)
- [x] T029 [US1] Add `TerminalController` in
  `src/websocket_streams/web/static/websockets_terminal.js` per
  `contracts/terminal-page.md`. It starts xterm.js and the fit addon, runs the read loop,
  and sends the keys and the size. It shows the status line, the warning, the time notice,
  and the gap notice. Load the vendored files and add the panel in
  `src/websocket_streams/web/templates/websockets_page.html`. Give each session with
  `terminal: true` to the controller in `src/websocket_streams/web/static/websockets.js`,
  and remove the old shell line field. Add the panel styles to
  `src/websocket_streams/web/static/websockets.css`.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`, `src/websocket_streams/web/templates/websockets_page.html`, `src/websocket_streams/web/static/websockets.js`, `src/websocket_streams/web/static/websockets.css`)
- [x] T030 [US1] Write the journeys J1 to J8 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Use the real services, the real manager, the real runners, and the fake Mist cloud.
  Cover the banner, typed text, each special key, Ctrl+C with no selection, the resize,
  early keys, the device close, and a full-screen color program. Save a screenshot for
  each journey in `test-artifacts/websockets-terminal/`, and read each screenshot. The CI
  workflow uploads no test artifacts, so the screenshots are local evidence. The pull
  request body lists each screenshot.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`, `test-artifacts/websockets-terminal/`)
- [x] T065 [US1] Keep 5,000 lines of scrollback in
  `src/websocket_streams/web/static/websockets_terminal.js` (FR-014). Prove it with the
  journey `test_review_fr014_history_keeps_five_thousand_lines` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`, `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T066 [US1] Show the full history again when the operator returns to a session
  (FR-018). Prove it with the journey `test_review_17_session_switch_drops_stale_read` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T067 [US1] Show the 20-second notice for a silent shell in
  `src/websocket_streams/web/static/websockets_terminal.js`. If the far side closes the
  shell before any output, end the session as failed with `NO_ANSWER_REASON` in
  `src/websocket_streams/live/runners/shell.py` (FR-019, issue #3710). Test the runner in
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Test the page with
  the journey `test_review_3710_silent_device_shows_notice_and_failed_reason` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`, `src/websocket_streams/live/runners/shell.py`, `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`, `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T068 [US1] Keep the shell lock and the typed device name (FR-045). Prove both rules
  with `test_start_request_locks_shell_and_checks_confirmation` in
  `tests/unit/websocket_streams/intake/test_ws_start_request.py`.
  (delivered: `tests/unit/websocket_streams/intake/test_ws_start_request.py`)

**Checkpoint**: The shell works as a terminal in the browser.

---

## Phase 4: User Story 2 - Copy and paste like a desktop terminal (Priority: P1)

**Goal**: The clipboard works like SecureCRT and Windows Terminal.

**Independent Test**: Select text and read the system clipboard. Paste with each paste
command, and compare the bytes that the fake device receives.

- [x] T031 [US2] Add the clipboard classes to
  `src/websocket_streams/web/static/websockets_terminal.js`. The class `TerminalClipboard`
  copies on a secure page and on an HTTP page. The class `PasteFlow` applies the limit, the
  confirmation, parts of 4 KiB with one request in flight, and the progress. The class
  `TerminalKeys` applies the copy and paste key rules. The class `TerminalMenu` holds Copy,
  Paste, Select all, and Clear. The class `TerminalPreferences` keeps the settings in local
  storage. Add the dialog, the menu, the settings, and the notice to
  `src/websocket_streams/web/templates/websockets_page.html`.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`, `src/websocket_streams/web/templates/websockets_page.html`)
- [x] T032 [US2] Write the journeys J9 to J18 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Cover copy by selection on and off, each copy key, and Ctrl+C with a selection. Cover
  each paste key with the exact bytes, the confirmation Cancel and Paste, bracketed paste,
  and a 2,000-line paste. Cover copy on an HTTP page from a host name that is not local,
  the paste limit, and the kept settings.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [X] T033 [US2] Add a paste test with 100 runs to
  `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`. Send 2,000
  lines in parts of 4 KiB through the gateway to the fake shell device. Compare the
  received bytes in each run (SC-002).
  (delivered: `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`)

**Checkpoint**: Each copy action and each paste action passes in the browser.

---

## Phase 5: User Story 3 - Get the full output of each device command (Priority: P1)

**Goal**: Each device command gives its full output in each run.

**Independent Test**: Run Show ARP 100 times against a fake device that answers at once.
Each run shows the full output.

- [X] T034 [P] [US3] Write the parity contract test in
  `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py`. Call each software
  kit utility with a recording API session. Compare the method, the path, and the body
  with the trigger table for each of the 52 commands and for the shell trigger.
  (delivered: `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py`)
- [X] T035 [P] [US3] Write the trigger tests and the filter tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py` and
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_filters.py`.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py`, `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_filters.py`)
- [X] T036 [P] [US3] Implement `UtilityTriggerTable` and `UtilityRequest` in
  `src/websocket_streams/live/runners/utility/triggers.py`. Hold the quiet time of each
  command, with 5 seconds or more.
  (delivered: `src/websocket_streams/live/runners/utility/triggers.py`)
- [X] T037 [P] [US3] Implement `UtilityMessageFilter` in
  `src/websocket_streams/live/runners/utility/filters.py`. Keep the early events. Filter
  command events by `session` and capture events by `capture_id`.
  (delivered: `src/websocket_streams/live/runners/utility/filters.py`)
- [X] T038 [US3] Rewrite `UtilityRunner` in
  `src/websocket_streams/live/runners/utility/runner.py`. Open `StreamClient`, wait for the
  subscription, send the trigger with `mist_post`, and filter the events. Apply the first
  output limit, the quiet time, and the total limit. Stop within 3 seconds. Keep
  `CaptureStopper`.
  (delivered: `src/websocket_streams/live/runners/utility/runner.py`)
- [X] T039 [US3] Update the runner tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`. Add the
  order test, the early event test, the three limit tests, and the stop test. Add 100 runs
  of Show ARP against a fake device that answers at once. Add 100 runs of Show Route
  against the same fake device (SC-003). The test
  `test_show_command_runs_one_hundred_times_with_full_output` holds one case for
  `ex.retrieveArpTable` and one case for `srx.retrieveRoutes`.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`)

**Checkpoint**: Each command keeps its first output lines.

---

## Phase 6: User Story 4 - See a correct live screen for Top and Monitor Traffic (Priority: P2)

**Goal**: The screen commands show no stray characters.

**Independent Test**: Send screen updates that break inside a control sequence. The page
shows the correct screen.

- [X] T040 [P] [US4] Write the screen runner tests in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_screen_runner.py`.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_screen_runner.py`)
- [X] T041 [US4] Implement `ScreenRunner` in
  `src/websocket_streams/live/runners/utility/screen.py`. Send the trigger, check the
  address, and append the raw bytes to the history. Build it in `RunnerFactory` for Top
  and Monitor Traffic.
  (delivered: `src/websocket_streams/live/runners/utility/screen.py`)
- [x] T042 [US4] Show each screen session in a read-only terminal in
  `src/websocket_streams/web/static/websockets_terminal.js` and
  `src/websocket_streams/web/static/websockets.js`. Remove the old screen view.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`, `src/websocket_streams/web/static/websockets.js`)
- [x] T043 [US4] Write the journeys J19 and J20 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Send 100 screen updates with split control sequences, and check the screen text
  (SC-008). Check that typed keys send nothing.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)

**Checkpoint**: Top and Monitor Traffic show a clean screen.

---

## Phase 7: User Story 5 - Keep the live streams and captures that work today (Priority: P2)

**Goal**: The channel streams and the captures use the own client with the same behavior.

**Independent Test**: Run each channel stream and each capture against the fake cloud.
Compare the messages, the states, and the end reasons.

- [X] T044 [P] [US5] Update the channel runner tests in
  `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`. Cover 3 new
  connections after 1, 2, and 4 seconds, and the failure after the third attempt. Cover a
  refused channel and the source map.
  (delivered: `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`)
- [X] T045 [US5] Rewrite `ChannelStreamRunner` in
  `src/websocket_streams/live/runners/channel.py` to use `StreamClient`. Remove the import
  of the private `_MistWebsocket` class.
  (delivered: `src/websocket_streams/live/runners/channel.py`)
- [X] T046 [US5] Test the capture path in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`. Cover the
  capture filter, the packet summary, and the stop request.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`)
- [x] T047 [US5] Update `tests/contract/websocket_streams/test_ws_channel_parity.py` and
  `tests/e2e/websockets_tab/test_websockets_page.py` for the own client and the terminal panel.
  (delivered: `tests/contract/websocket_streams/test_ws_channel_parity.py`, `tests/e2e/websockets_tab/test_websockets_page.py`)

**Checkpoint**: The streams and the captures pass their old tests and their new tests.

---

## Phase 8: User Story 6 - Save the terminal history as text (Priority: P3)

**Goal**: An operator saves the terminal history as a text file.

**Independent Test**: Run commands, select Download, and compare the file with the screen.

- [x] T048 [US6] Add the history file to
  `src/websocket_streams/web/static/websockets_terminal.js`. Build the text from the
  xterm.js buffer with no control codes, and save it as a file.
  (delivered: `src/websocket_streams/web/static/websockets_terminal.js`)
- [x] T049 [US6] Write the journey J21 in `tests/e2e/websockets_tab/test_websockets_terminal.py`. Compare
  the file text with the screen text.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)

**Checkpoint**: All stories work on their own.

---

## Phase 9: Polish and Cross-Cutting Concerns

**Purpose**: Prove the performance, the log safety, and the delivery.

- [x] T050 Write the performance journeys in
  `tests/e2e/websockets_tab/test_websockets_terminal_performance.py`. Measure the echo time for 200 keys
  (SC-001), 1 MB of output (SC-007), and 5 busy shells with page loads (SC-005). Record
  each number.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal_performance.py`)
- [x] T051 Write the log scan journey J22 in `tests/e2e/websockets_tab/test_websockets_terminal.py`
  (SC-006).
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [X] T052 [P] Update `documentation/operator-guide.md` and
  `documentation/wiki/Web-Portal.md` for the terminal, the copy keys, the paste keys, and
  the new setting.
  (delivered: `documentation/operator-guide.md`, `documentation/wiki/Web-Portal.md`)
- [X] T053 [P] Add the release note `changelog.d/issue-3671-interactive-terminal.md`.
  (delivered: `changelog.d/issue-3671-interactive-terminal.md`)
- [x] T054 Run the quality gates per `quickstart.md`. Also run mypy with `MYPY_PATHS`,
  Bandit, Vulture, pydocstyle, and the complexity gate. Fix each finding. Record the
  results in `research.md` section R14. The pull request body copies the same results.
  (delivered: `specs/3671-interactive-terminal/research.md`, section R14)
- [x] T055 Run the live checks per `quickstart.md` section 5. Record the shell host, the
  NUL prefix result, and the longest pause of Show ARP and Show Route. If a pause is longer
  than 5 seconds, change the quiet time in the trigger table.
  (delivered: `specs/3671-interactive-terminal/research.md`, section R13)
- [ ] T056 Run speckit-analyze. Fix each CRITICAL finding and each HIGH finding, then run
  the analysis again.
- [x] T062 Move the browser tests into `tests/e2e/websockets_tab/`, the fake Mist cloud
  into `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`, and the client tests
  into `tests/unit/websocket_streams/live/transport/clients/` (finding C1). The three
  folders below are the evidence.
  (delivered: `tests/e2e/websockets_tab/`, `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`, `tests/unit/websocket_streams/live/transport/clients/`)
- [x] T069 Prove that no portal answer gives the shell address or a secret to the page
  (FR-048). Use the journey `test_review_fr048_page_gets_no_shell_address` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py` and the route scan in
  `tests/unit/websocket_streams/web/test_ws_secret_guard.py`.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`, `tests/unit/websocket_streams/web/test_ws_secret_guard.py`)

### Delivery pipeline (constitution Principle IV)

T057 to T061 hold the 12 pipeline steps. T059 to T061 run after the push, so their boxes
stay clear in the merged file. The pull request and issue #3671 record their results.

- [ ] T057 Run the local gates, build the manifest, stage the feature files, and commit.
  Write each commit subject in the constitution step 4 format
  `version YY.MM.DD.HH.MM - description`, with the time in UTC. The pull request title
  keeps Conventional Commits, because the title guard reads the title (issue #3720).
- [ ] T058 Fetch and rebase onto `origin/main`. Run the affected gates again.
- [ ] T059 Push the branch. Open the pull request with `Closes #3671`, `Closes #3659`,
  `Closes #3660`, and `Closes #3710`. The body also holds the changed-file summary, the
  local gate results from R14, the CI status, and the deployment and rollback notes.
- [ ] T060 Wait for each required check, CodeQL included. Squash-merge with a subject that
  you write. Issues #3718 and #3721 stay open and do not block the merge. The owner gave
  a standing instruction to merge the work that is ready, and the final report names
  both issues for an owner decision.
- [ ] T061 Wait for `.github/workflows/container-build.yml` on the merged revision. Make
  sure that the image revision label equals the merge SHA. Deploy with
  `.\scripts\compose.ps1 up -d --no-deps misthelper`, and check the container health and
  the portal health.

---

## Requirement Coverage

This table maps each functional requirement and each success criterion in `spec.md` to
the tasks that deliver it or prove it. The second speckit-analyze pass built the map.

| Requirement | Tasks |
| --- | --- |
| FR-001 | T009, T010, T011, T012, T013, T014, T021, T024, T038, T041, T045, T046, T047 |
| FR-002 | T011, T014, T038, T039 |
| FR-003 | T035, T037, T038, T039, T046 |
| FR-004 | T034, T035, T036 |
| FR-005 | T009, T012, T014, T015, T063 |
| FR-006 | T011, T014 |
| FR-007 | T044, T045, T064 |
| FR-008 | T009, T012, T021, T024, T041, T055 |
| FR-009 | T009, T012, T025, T051 |
| FR-010 | T003, T025, T029, T030 |
| FR-011 | T011, T014, T023, T026, T027, T028, T029, T030, T055 |
| FR-012 | T011, T014, T021, T022, T023, T024, T026, T028, T029, T030 |
| FR-013 | T004, T016, T018, T020, T021, T022, T026, T030 |
| FR-014 | T065 |
| FR-015 | T005, T016, T017, T019, T022, T026, T028, T029 |
| FR-016 | T019, T020, T021, T022, T026, T029, T030, T040, T064, T067 |
| FR-017 | T029 |
| FR-018 | T017, T027, T029, T066 |
| FR-019 | T021, T030, T067 |
| FR-020 | T031, T032 |
| FR-021 | T031, T032 |
| FR-022 | T030, T031, T032 |
| FR-023 | T031, T032 |
| FR-024 | T031, T032 |
| FR-025 | T031, T032 |
| FR-026 | T031, T032 |
| FR-027 | T031, T032, T033 |
| FR-028 | T031, T032 |
| FR-029 | T031 |
| FR-030 | T031, T032 |
| FR-035 | T003, T004, T022, T026, T027, T040, T041, T042, T043, T055 |
| FR-040 | T048, T049 |
| FR-045 | T068 |
| FR-046 | T004, T016, T018, T022, T023, T026, T028 |
| FR-047 | T029 |
| FR-048 | T069 |
| SC-001 | T050 |
| SC-002 | T032, T033 |
| SC-003 | T036, T038, T039, T055 |
| SC-004 | T030, T032 |
| SC-005 | T050 |
| SC-006 | T051 |
| SC-007 | T050 |
| SC-008 | T040, T043 |

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
