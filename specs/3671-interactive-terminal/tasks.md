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

- **[P]**: The task can run in parallel with another ready task only after all listed
  prerequisites finish. It changes a different file set.
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

- [X] T001 Move `src/mist/realtime/websocket_streams/live/runners/utility.py` to
  `src/mist/realtime/websocket_streams/live/runners/utility/runner.py` with `git mv`. Add an `__init__.py`
  that holds a docstring only. Change each import to
  `src.mist.realtime.websocket_streams.live.runners.utility.runner`. Move
  `tests/unit/websocket_streams/live/runners/test_ws_utility_runner.py` to
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py` with an
  `__init__.py`. Run the moved tests.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/utility/runner.py`, `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`)
- [X] T002 Create each new package with an `__init__.py` that holds a docstring only:
  `src/mist/realtime/websocket_streams/live/transport/`, `src/mist/realtime/websocket_streams/live/terminal/`,
  `tests/unit/websocket_streams/live/transport/`,
  `tests/unit/websocket_streams/live/terminal/`, and `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`.
  T062 moved the fake cloud package to this path.
  (delivered: `src/mist/realtime/websocket_streams/live/transport/`, `src/mist/realtime/websocket_streams/live/terminal/`, `tests/unit/websocket_streams/live/transport/`, `tests/unit/websocket_streams/live/terminal/`, `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`)
- [X] T003 [P] Copy xterm.js 6.0.0 and the fit addon 0.11.0 into
  `src/mist/realtime/websocket_streams/web/static/vendor/xterm/`. Copy `lib/xterm.js` as `xterm.min.js`,
  `lib/addon-fit.js` as `addon-fit.min.js`, and `css/xterm.css`. Put the MIT license text of
  both packages in `LICENSE`. Add `README.md` with the versions, the source address, and the
  SHA-256 value of each file.
  (delivered: `src/mist/realtime/websocket_streams/web/static/vendor/xterm/`)
- [X] T004 [P] Add the codes `not_terminal` (409), `read_only` (409), `input_full` (409),
  `too_large` (413), and `rate_limited` (429) to `StreamRequestError.STATUS_BY_CODE` in
  `src/mist/realtime/websocket_streams/intake/fields.py`. Test each code in
  `tests/unit/websocket_streams/intake/test_ws_field_checker.py`.
  (delivered: `src/mist/realtime/websocket_streams/intake/fields.py`, `tests/unit/websocket_streams/intake/test_ws_field_checker.py`)
- [X] T005 [P] Add `terminal_history_bytes` to `StreamSettings` in
  `src/mist/realtime/websocket_streams/live/sessions/settings.py`. Read `PORTAL_WS_TERMINAL_HISTORY_KB`.
  The range is 256 to 8,192, and the default is 1,024. Document the setting in
  `deploy/.env.example`. Test the default, the range, and a bad value in
  `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`.
  (delivered: `src/mist/realtime/websocket_streams/live/sessions/settings.py`, `deploy/.env.example`, `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`)

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
  `src/mist/realtime/websocket_streams/live/transport/endpoint.py` per `contracts/transport.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/transport/endpoint.py`)
- [X] T013 [P] Implement `FrameDecoder` in `src/mist/realtime/websocket_streams/live/transport/frames.py`
  per `contracts/transport.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/transport/frames.py`)
- [X] T014 Implement `StreamClient` in
  `src/mist/realtime/websocket_streams/live/transport/stream_client.py` and `ShellClient` in
  `src/mist/realtime/websocket_streams/live/transport/shell_client.py`. Use `websocket.create_connection`
  with `enable_multithread=True`. Take the socket factory and the clock as constructor
  values. T014 depends on T009 through T013, including the tests and both transport
  components.
  (delivered: `src/mist/realtime/websocket_streams/live/transport/stream_client.py`, `src/mist/realtime/websocket_streams/live/transport/shell_client.py`)
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
  `src/mist/realtime/websocket_streams/live/terminal/byte_history.py` per `data-model.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/terminal/byte_history.py`)
- [X] T018 [P] Implement `TerminalInput` in
  `src/mist/realtime/websocket_streams/live/terminal/input_queue.py` per `data-model.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/terminal/input_queue.py`)
- [X] T019 Implement `TerminalState` and `TerminalChunk` in
  `src/mist/realtime/websocket_streams/live/terminal/state.py` per `data-model.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/terminal/state.py`)
- [X] T020 Change `StreamSession` in `src/mist/realtime/websocket_streams/live/sessions/record.py`. Add
  the `terminal` value and the `add_bytes(data)` method to the record and to the
  `SessionSink` protocol. Release the input queue in `mark_input_ready`. Close the history
  and the input in `finish`. Add the payload field `terminal`. Test the change in
  `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`. T020 depends on
  T016 through T019, including the core tests and all three terminal components.
  (delivered: `src/mist/realtime/websocket_streams/live/sessions/record.py`, `tests/unit/websocket_streams/live/sessions/test_ws_session_record.py`)
- [x] T063 [P] Prove the proxy part of FR-005 in
  `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`. The client
  gives no proxy option to websocket-client. The library then reads `https_proxy` and
  `no_proxy` from the host.
  (delivered: `tests/unit/websocket_streams/live/transport/clients/test_ws_shell_client.py`)
- [x] T064 Add `ConnectFailure` to `src/mist/realtime/websocket_streams/live/transport/endpoint.py`. It
  changes each open error to a plain reason. In
  `src/mist/realtime/websocket_streams/live/runners/channel.py`, a channel stream does not connect again
  after an HTTP 4xx refusal, except 408 and 429 (finding M1). Test the reasons in
  `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py` and the rule in
  `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`.
  (delivered: `src/mist/realtime/websocket_streams/live/transport/endpoint.py`, `src/mist/realtime/websocket_streams/live/runners/channel.py`, `tests/unit/websocket_streams/live/transport/test_ws_endpoint.py`, `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`)

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
  resize range. Prove that input and resize share one monotonic request window. Accept
  request 60, refuse request 61, and refuse request 61 after a clock rollback.
  (delivered: `tests/unit/websocket_streams/live/terminal/test_ws_terminal_gateway.py`)
- [X] T023 [P] [US1] Write the route tests in
  `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`. Cover the terminal read
  route, the input route, and the resize route. Cover the refused `line` and `key` body
  shapes, the error shape, and a POST without the form token.
  (delivered: `tests/unit/websocket_streams/web/test_ws_blueprint_routes.py`)

### Implementation for User Story 1

- [X] T024 [US1] Rewrite `ShellRunner` in `src/mist/realtime/websocket_streams/live/runners/shell.py`.
  Send the shell trigger with `mist_post`, check the address, and open `ShellClient` with
  the stored size. Append each output to the history. Remove the import of the software
  kit shell.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/shell.py`)
- [X] T025 [US1] Remove `MessageShaper.clean_shell_text` from
  `src/mist/realtime/websocket_streams/live/runners/text.py`, and remove its test from
  `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`. Keep
  `ShellAddressFilter`, because the REST layer of the software kit can log the address.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/text.py`, `tests/unit/websocket_streams/live/runners/test_ws_message_text.py`)
- [X] T026 [US1] Implement `TerminalGateway` in
  `src/mist/realtime/websocket_streams/live/terminal/gateway.py` per `contracts/terminal-http.md`.
  (delivered: `src/mist/realtime/websocket_streams/live/terminal/gateway.py`)
- [X] T027 [US1] Change `src/mist/realtime/websocket_streams/live/sessions/manager.py`. Build a
  `TerminalState` for each shell session and each screen session, and bind the input
  sender. Replace `send_input`, `_input_text`, `_key_text`, and `KEY_INPUTS` with a public
  `session(session_id)` method. Give `RunnerFactory` an optional transport profile for the
  tests. Update `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
  (delivered: `src/mist/realtime/websocket_streams/live/sessions/manager.py`, `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`)
- [X] T028 [US1] Add `terminal_read`, `terminal_input`, and `terminal_resize` to
  `WebSocketsServices` in `src/mist/realtime/websocket_streams/web/services.py`, and remove the old
  `send_input`. Add the three routes to `src/mist/realtime/websocket_streams/web/blueprint.py`. Update
  `tests/unit/websocket_streams/web/test_ws_web_services.py`.
  (delivered: `src/mist/realtime/websocket_streams/web/services.py`, `src/mist/realtime/websocket_streams/web/blueprint.py`, `tests/unit/websocket_streams/web/test_ws_web_services.py`)
- [x] T029 [US1] Add `TerminalController` in
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js` per
  `contracts/terminal-page.md`. It starts xterm.js and the fit addon, runs the read loop,
  and sends the keys and the size. It shows the status line, the warning, the time notice,
  and the gap notice. Load the vendored files and add the panel in
  `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`. Give each session with
  `terminal: true` to the controller in `src/mist/realtime/websocket_streams/web/static/websockets.js`,
  and remove the old shell line field. Add the panel styles to
  `src/mist/realtime/websocket_streams/web/static/websockets.css`.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`, `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`, `src/mist/realtime/websocket_streams/web/static/websockets.js`, `src/mist/realtime/websocket_streams/web/static/websockets.css`)
- [x] T030 [US1] Write the journeys J1 to J8 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Use the real services, the real manager, the real runners, and the fake Mist cloud.
  Cover the banner, typed text, each special key, Ctrl+C with no selection, the resize,
  early keys, the device close, and a full-screen color program. Test F1 through F12 and
  assert `ESC OP`, `ESC OQ`, `ESC OR`, `ESC OS`, `ESC [15~`, `ESC [17~`, `ESC [18~`,
  `ESC [19~`, `ESC [20~`, `ESC [21~`, `ESC [23~`, and `ESC [24~`, respectively. Assert
  that `Warning: Each command runs on the live device.` shows before the first input. Test
  the expiry notice at exactly 120,000 milliseconds and at 119,999 milliseconds before
  expiry. Save a screenshot for each journey in `test-artifacts/websockets-terminal/`, and
  read each screenshot. The CI
  workflow uploads no test artifacts, so the screenshots are local evidence. The pull
  request body lists each screenshot.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`, `test-artifacts/websockets-terminal/`)
- [x] T065 [US1] Keep 5,000 lines of scrollback in
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js` (FR-014). Prove it with the
  journey `test_review_fr014_history_keeps_five_thousand_lines` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`, `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [x] T066 [US1] Show the full history again when the operator returns to a session
  (FR-018). Prove it with the journey `test_review_17_session_switch_drops_stale_read` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`. Use
  `test_review_two_pages_type_into_one_shell` to prove that two pages can type into one
  shell. Use `test_page_close_leaves_shared_shell_for_idle_cleanup` to prove that closing
  both pages does not send an operator Stop request. Use
  `test_reaper_stops_idle_and_prunes_old_ended` with its controlled clock to prove that the
  idle limit stops the shell after page reads end.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`, `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`)
- [x] T067 [US1] Show the 20-second notice for a silent shell in
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`. If the far side closes the
  shell before any output, end the session as failed with `NO_ANSWER_REASON` in
  `src/mist/realtime/websocket_streams/live/runners/shell.py` (FR-019, issue #3710). Test the runner in
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Test the page with
  the journey `test_review_3710_silent_device_shows_notice_and_failed_reason` in
  `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`, `src/mist/realtime/websocket_streams/live/runners/shell.py`, `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`, `tests/e2e/websockets_tab/test_websockets_terminal.py`)
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
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`. The class `TerminalClipboard`
  copies on a secure page and on an HTTP page. The class `PasteFlow` applies the limit, the
  confirmation, parts of 4 KiB with one request in flight, and the progress. The class
  `TerminalKeys` applies the copy and paste key rules. The class `TerminalMenu` holds Copy,
  Paste, Select all, and Clear. The class `TerminalPreferences` keeps the settings in local
  storage. Add the dialog, the menu, the settings, and the notice to
  `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`, `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`)
- [x] T032 [US2] Write the journeys J9 to J18 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Cover copy by selection on and off, each copy key, and Ctrl+C with a selection. Cover
  each paste key with exact bytes, UTF-8 text, line-end conversion, bracketed markers,
  confirmation Cancel and Paste, and a 2,000-line paste. Cover copy on an HTTP page from
  a host name that is not local, the paste limit, and settings. Check the 10-through-28
  font range and persistence after reload. Verify the copied-character count and its
  `aria-live="polite"` announcement. Test menu Copy, Paste, Select all, and Clear. Prove
  that Clear removes local display text without changing the server history.
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
  `src/mist/realtime/websocket_streams/live/runners/utility/triggers.py`. Hold the quiet time of each
  command, with 5 seconds or more.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/utility/triggers.py`)
- [X] T037 [P] [US3] Implement `UtilityMessageFilter` in
  `src/mist/realtime/websocket_streams/live/runners/utility/filters.py`. Keep the early events. Filter
  command events by `session` and capture events by `capture_id`.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/utility/filters.py`)
- [X] T038 [US3] Rewrite `UtilityRunner` in
  `src/mist/realtime/websocket_streams/live/runners/utility/runner.py`. Open `StreamClient`, wait for the
  subscription, send the trigger with `mist_post`, and filter the events. Apply the first
  output limit, the quiet time, and the total limit. Stop within 3 seconds. Keep
  `CaptureStopper`.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/utility/runner.py`)
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
  `tests/unit/websocket_streams/live/runners/utility/test_ws_screen_runner.py`. Prove that
  each screen sends one 80-column by 40-row start size. Attempt a later resize and prove
  that no second size frame reaches the device.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_screen_runner.py`)
- [X] T041 [US4] Implement `ScreenRunner` in
  `src/mist/realtime/websocket_streams/live/runners/utility/screen.py`. Send the trigger, check the
  address, and append the raw bytes to the history. Build it in `RunnerFactory` for Top
  and Monitor Traffic.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/utility/screen.py`)
- [x] T042 [US4] Show each screen session in a read-only terminal in
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js` and
  `src/mist/realtime/websocket_streams/web/static/websockets.js`. Remove the old screen view.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`, `src/mist/realtime/websocket_streams/web/static/websockets.js`)
- [x] T043 [US4] Write the journeys J19 and J20 in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
  Send 100 consecutive screen updates with split control sequences in one session. Check
  the complete screen text after all 100 updates (SC-008). Check that typed keys send nothing. Show row 1 and row 40 at a fixed 80 by 40
  size after a browser panel change.
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
  `src/mist/realtime/websocket_streams/live/runners/channel.py` to use `StreamClient`. Remove the import
  of the private `_MistWebsocket` class.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/channel.py`)
- [X] T046 [US5] Test the capture path in
  `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`. Cover the
  capture filter, the packet summary, and the stop request.
  (delivered: `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`)
- [x] T047 [US5] Update `tests/contract/websocket_streams/test_ws_channel_parity.py` and
  `tests/e2e/websockets_tab/test_websockets_page.py` for the owned client and terminal
  panel. Check no warning after a reconnect with complete buffered output. Check a visible
  warning when the bounded buffer dropped reconnect output.
  (delivered: `tests/contract/websocket_streams/test_ws_channel_parity.py`, `tests/e2e/websockets_tab/test_websockets_page.py`)

**Checkpoint**: The streams and the captures pass their old tests and their new tests.

---

## Phase 8: User Story 6 - Save the terminal history as text (Priority: P3)

**Goal**: An operator saves the terminal history as a text file.

**Independent Test**: Run commands, select Download, and compare the file with the screen.

- [x] T048 [US6] Add the history file to
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`. Build the text from the
  xterm.js buffer with no control codes, and save it as a file.
  (delivered: `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js`)
- [x] T049 [US6] Write the journey J21 in `tests/e2e/websockets_tab/test_websockets_terminal.py`. Compare
  the file text with the screen text.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)

**Checkpoint**: All stories work on their own.

---

## Phase 9: Polish and Cross-Cutting Concerns

**Purpose**: Prove the performance, the log safety, and the delivery.

- [x] T050 Write the performance journeys in
  `tests/e2e/websockets_tab/test_websockets_terminal_performance.py`. Measure 200-key echo
  time (SC-001) and 1 MiB output (SC-007). For SC-005, start a 1 MiB burst in each of 5
  shells. Use a barrier to keep all five bursts active during 5 visible `/websockets` loads
  and 5 visible `/operations` loads. Require each stream to send bytes during each load and
  complete exactly 1 MiB. Require all 10 loads. Use nearest-rank p95, which selects rank 10
  from 10 samples. Require it below 1 second. Record each number.
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal_performance.py`)
- [x] T051 Write the log scan journey J22 in `tests/e2e/websockets_tab/test_websockets_terminal.py`
  (SC-006).
  (delivered: `tests/e2e/websockets_tab/test_websockets_terminal.py`)
- [X] T052 [P] Update `README.md`, `documentation/operator-guide.md`, and
  `documentation/wiki/Web-Portal.md` for live streams, utilities, captures, terminal keys,
  paste behavior, and the new setting.
  (delivered: `README.md`, `documentation/operator-guide.md`, `documentation/wiki/Web-Portal.md`)
- [X] T053 [P] Add the release note `changelog.d/issue-3671-interactive-terminal.md`.
  (delivered: `changelog.d/issue-3671-interactive-terminal.md`)
- [x] T054 Run the feature gates per `quickstart.md`. Also run mypy with `MYPY_PATHS`,
  Bandit, Vulture, pydocstyle, interrogate, Radon, and Pylint. Record the results in
  `research.md` section R14. The feature gates pass. The separate local test-quality scope
  test has 48 failures and 34 passes on this branch and clean `main`. Issue #3742 tracks
  that baseline defect.
  (delivered: `specs/3671-interactive-terminal/research.md`, section R14)
- [x] T055 Run the read-only live checks per `quickstart.md` section 5. Record the shell
  host, the NUL prefix result, and the longest pause of Show ARP and Show Route. Run Show
  ARP five times and Show Route with protocol `direct` five times. Require all 10 runs to
  finish with complete output. If a pause is longer than 5 seconds, change the quiet time
  in the trigger table. The separate owner-approved port-bounce journey is not T055
  evidence. Research R13 records 5 of 5 complete runs for each command.
  (delivered: `specs/3671-interactive-terminal/research.md`, section R13)
- [x] T056 Confirm that the executable T083 analysis loop finishes. Keep this rollup open
  until T083 reports no actionable feature finding. The final bounded analysis checked 45
  requirements and 92 tasks. It reported no actionable finding. Research R19 records the
  result. (delivered: `specs/3671-interactive-terminal/research.md`)
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
- [x] T070 Fix issue #3740. Consume the retry budget after immediate post-subscription
  drops. Reset it only after one event or 5 stable seconds. Prove exhaustion and reset
  behavior with channel runner unit tests.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/channel.py`,
  `tests/unit/websocket_streams/live/runners/test_ws_channel_runner.py`)
- [x] T071 Fix issue #3741. Report failed local input and live resize writes as failed
  sessions with `WRITE_FAILED_REASON`. Return the transport refusal to the HTTP route.
  Preserve deferred resize before the connection opens and explicit operator-stop behavior.
  (delivered: `src/mist/realtime/websocket_streams/live/runners/shell.py`,
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`)

### Delivery pipeline (constitution Principle IV)

T057 to T061 hold the 12 pipeline steps. T059 to T061 run after the push, so their boxes
stay clear in the merged file. The pull request and issue #3671 record their results.

- [x] T057 After T084 and T092 pass, build the manifest, stage all final evidence, and
  commit any remaining files. Verify every correction is in the committed branch history.
  Rebased commit `e5e25b98` holds the 23-file final convergence manifest. The history check found
  26 valid feature subjects and 26 required Copilot trailers. Write each commit subject in
  the constitution step 4 format
  `version YY.MM.DD.HH.MM - description`, with the time in UTC. The pull request title
  keeps Conventional Commits, because the title guard reads the title (issue #3720).
  (delivered: committed branch history)
- [x] T058 Fetch and rebase onto `origin/main`. Run the affected gates again. The rebase
  applied 27 commits without a conflict. The post-rebase checks passed Ruff, Black, compile,
  363 Python tests, and 63 browser tests. (delivered: rebased branch history)
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
| FR-007 | T044, T045, T047, T064 |
| FR-008 | T009, T012, T021, T024, T041, T055 |
| FR-009 | T009, T012, T025, T051 |
| FR-010 | T003, T025, T029, T030 |
| FR-011 | T011, T014, T023, T026, T027, T028, T029, T030, T055 |
| FR-012 | T011, T014, T021, T022, T023, T024, T026, T028, T029, T030 |
| FR-013 | T004, T016, T018, T020, T021, T022, T026, T030 |
| FR-014 | T065 |
| FR-015 | T005, T016, T017, T019, T022, T026, T028, T029 |
| FR-016 | T019, T020, T021, T022, T026, T029, T030, T040, T064, T067 |
| FR-017 | T029, T030 |
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
| FR-029 | T031, T032 |
| FR-030 | T031, T032 |
| FR-031 | T031, T032 |
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

### Convergence Task Coverage

This table maps each correction task to the behavior that it preserves or proves.

| Task | Requirement or rule |
| --- | --- |
| T070 | FR-007 and channel retry exhaustion |
| T071 | FR-011 through FR-019 and terminal write failures |
| T072 | Constitution I, V, and VII, FR-009, and SC-006 |
| T073 | Constitution I, II, V, and VII, and FR-001 through FR-009 |
| T074 | Constitution I, II, V, and VII, FR-011 through FR-019, and FR-046 |
| T075 | Constitution I, II, V, and VII, and FR-002 through FR-004 |
| T076 | Constitution I, II, V, and VII, and US1 |
| T077 | Constitution I and II, US1, and US2 |
| T078 | Constitution I and II structural enforcement |
| T079 | Owned-WebSocket exception, FR-001 through FR-003, and SC-008 |
| T085 | Constitution I, II, V, and VII, and catalog discovery and lock behavior |
| T086 | Constitution I, II, V, and VII, and intake validation and identifiers |
| T087 | Constitution I, II, V, and VII, FR-007, FR-009, and T070 |
| T088 | Constitution I, II, V, and VII, and FR-013 through FR-019 |
| T089 | Constitution I, II, V, and VII, and FR-012 through FR-019 |
| T090 | Constitution I, II, V, and VII, and FR-046 through FR-048 |

---

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependency. T001 and T002 run first, because the lanes need the folders.
- Phase 2 depends on Phase 1. It blocks each story.
- In Phase 2, T014 depends on T009 through T013. T020 depends on T016 through T019.
- Test tasks must finish and fail for the expected reason before their implementation starts.
- Phase 3 to Phase 8 depend on Phase 2.
- Phase 9 depends on each story that the release holds.
- Phase 10 depends on Phase 9 and on the issue repairs in T070 and T071.
- Phase 11 depends on T072 through T079. Its internal dependencies are stated in each task.
- T083 depends on T082 and T091. T084 depends on T083.
- T092 is the final pre-commit convergence checkpoint. It depends on T083 and T084.
- T057 commits the analyzed and validated tree only after T092 passes.

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

- A lane starts only when the listed prerequisites for its next task are complete.
- Ready `[P]` tasks can run together only when their file sets do not overlap.
- A builder does not start a later-phase task before the earlier phase completes.

---

## Parallel Example: Phase 2

```text
After T001 and T002:
Builder A: T006 (fake cloud server)
Builder B: T009 (transport endpoint tests)
Builder C: T016 (terminal history and input tests)

Start each next task only after its listed prerequisite finishes.
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

## Phase 10: Convergence

- [X] T072 [P] CRITICAL: Replace
  `src/mist/realtime/websocket_streams/live/transport/frames.py` with the package
  `src/mist/realtime/websocket_streams/live/transport/runtime/`, and keep its `__init__.py`
  docstring-only.
  Put frame reading, frame decoding, and shared structured logging in separate leaf modules.
  The logger MUST write each record as ASCII JSON, permit only bounded safe fields, and
  redact secrets at the boundary. Replace
  `tests/unit/websocket_streams/live/transport/test_ws_frames.py` with focused tests under
  `tests/unit/websocket_streams/live/transport/runtime/`. The tests MUST parse each record,
  check field bounds, and test redaction for tokens, cookies, shell paths, keys, pasted
  text, and terminal output. Preserve the frame and keepalive behavior that Constitution
  I, V, and VII, FR-009, and SC-006 require (contradicts).

- [X] T073 CRITICAL: After T072, decompose every noncompliant class and function in
  `src/mist/realtime/websocket_streams/live/transport/endpoint.py`,
  `src/mist/realtime/websocket_streams/live/transport/stream_client.py`, and
  `src/mist/realtime/websocket_streams/live/transport/shell_client.py`. Use named collaborator classes,
  not wrappers, and keep each hierarchy within the five-item limits. Use the shared
  structured logger from T072, and update the endpoint and client tests under
  `tests/unit/websocket_streams/live/transport/`. Preserve authentication, TLS, proxy,
  keepalive, reconnect, close, input, and resize. Constitution I, II, V, and VII and
  FR-001 through FR-009 require this behavior (contradicts).

- [X] T074 [P] CRITICAL: After T072, decompose every noncompliant class and function in
  `src/mist/realtime/websocket_streams/live/terminal/byte_history.py`,
  `src/mist/realtime/websocket_streams/live/terminal/input_queue.py`, and
  `src/mist/realtime/websocket_streams/live/terminal/gateway.py`. Use named collaborator classes, not
  wrappers, and keep `src/mist/realtime/websocket_streams/live/terminal/state.py` compliant. Use the
  shared structured logger from T072, and update the matching tests under
  `tests/unit/websocket_streams/live/terminal/`. Preserve history, queue order, rate, read,
  input, and resize. Constitution I, II, V, and VII, FR-011 through FR-019, and FR-046
  require this behavior (contradicts).

- [X] T075 [P] CRITICAL: After T072, replace each noncompliant utility module with a
  compliant package at `src/mist/realtime/websocket_streams/live/runners/utility/filters/`,
  `src/mist/realtime/websocket_streams/live/runners/utility/runner/`, and
  `src/mist/realtime/websocket_streams/live/runners/utility/triggers/`. Keep each `__init__.py`
  docstring-only, and move behavior into named leaf classes. Do not add a wrapper or a
  compatibility export. Use the shared structured logger from T072, and update imports
  and tests under `tests/unit/websocket_streams/live/runners/utility/` and
  `tests/contract/websocket_streams/`. Preserve trigger parity, early output, capture,
  filtering, time limits, and stop. Constitution I, II, V, and VII and FR-002 through
  FR-004 require this behavior (contradicts).

- [X] T076 [P] CRITICAL: After T072, replace
  `src/mist/realtime/websocket_streams/live/runners/shell.py` with the compliant package
  `src/mist/realtime/websocket_streams/live/runners/shell/`, and keep its `__init__.py` docstring-only.
  Split terminal opening, reading, outcomes, input, and screen behavior into named classes.
  Do not add wrappers or compatibility exports. Use the shared structured logger from T072,
  and update imports and
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. Preserve the behavior
  for shell safety, first output, deferred input, resize, close, time limits, and failed
  writes. Constitution I, II, V, and VII and US1 require this behavior (contradicts).

- [X] T077 [P] CRITICAL: Replace
  `src/mist/realtime/websocket_streams/web/static/websockets_terminal.js` with compliant leaf modules
  under `src/mist/realtime/websocket_streams/web/static/terminal/`. Group controller, input, clipboard,
  menu, paste, and preference behavior into nested folders with five entries or fewer.
  Keep each class at five methods or fewer. Remove the pass-through wrapper, and load each
  leaf script in dependency order from
  `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`. Update
  `src/mist/realtime/websocket_streams/web/static/websockets.js` and the tests under
  `tests/e2e/websockets_tab/`. Preserve every journey for the terminal and clipboard as
  required by Constitution I and II, US1, and US2 (contradicts).

- [X] T078 After T073 through T077, add the structural contract test
  `tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py`.
  Check every feature source path named in `plan.md`. Fail when a hierarchy has over five
  child items, parameters, blocks, operations, or methods, or when a function exceeds 25
  lines. Print the count of checked modules, classes, and functions. Prove failure against
  one bounded bad fixture. Then run the test against the implementation that Constitution
  I and II require (missing).

- [X] T079 [P] CRITICAL: Extend
  `tests/contract/websocket_streams/test_ws_sdk_contract.py` with deterministic SDK
  limitation contracts. For `WebSocketWrapper.start_with_trigger`, emit one event while
  the REST trigger runs. Prove that the SDK retains 0 of 1 events and that the owned
  subscribe-first path retains 1 of 1 events. Split one screen control sequence across
  two SDK updates. Prove that the SDK discards the first part and draws the second part as
  text. Send the same frames through the owned transport. Prove that it preserves the
  complete byte stream for xterm.js. Use no network and state both checked counts. These
  proofs qualify the bounded exception under the Technology Constraints, FR-001 through
  FR-003, and US3/AC1 (missing).

- [X] T080 CRITICAL: After all source tasks, reword every feature commit subject to
  `version YY.MM.DD.HH.MM - description` with its UTC time. Preserve each commit content.
  Verify every subject in the feature range and fail if one subject does not match.
  Record the checked commit count in `specs/3671-interactive-terminal/research.md` per
  Constitution IV. The history check found 23 valid subjects and 23 required trailers.
  A tree comparison against the pre-rewrite backup found no content difference. (delivered)

- [X] T081 After T072 through T079, correct
  `specs/3671-interactive-terminal/plan.md` and
  `specs/3671-interactive-terminal/tasks.md`. Mark the observability gate PASS only after
  the JSON parsing, ASCII, field-bound, and redaction tests pass. Mark the WebSocket gate
  PASS only after T079 passes. Replace the standard-logging decision with the shared
  structured-logging decision, and add exact test names and result counts to the evidence.
  Keep T056 open until T083 passes. This proves compliance with Principle V, the exception
  for an owned WebSocket, and the Constitution Check in the plan (partial).
  (delivered: `specs/3671-interactive-terminal/plan.md` and
  `specs/3671-interactive-terminal/tasks.md`. Evidence: the T081 evidence table below.)

- [X] T082 After T072 through T081, run every command in
  `specs/3671-interactive-terminal/quickstart.md`. Run the repository syntax, Ruff, Black,
  mypy, Bandit, Vulture, pydocstyle, interrogate, Radon, Pylint, unit, contract, guardrail,
  integration, and browser gates. Run the focused structural, logging, secret-redaction,
  and SDK-exception tests separately. Record each exact command, result, count, and
  measurement in `specs/3671-interactive-terminal/research.md` per T054 and Constitution
  IV. The feature gates passed. Research R16 records the existing repository and Windows
  exceptions separately. (delivered)

- [x] T083 After T082 and T091, run `speckit.analyze` against the specification, plan,
  and tasks. This read-only task confirms the final artifact consistency. Record the
  analysis result in `specs/3671-interactive-terminal/research.md`. If the analysis finds
  an actionable item, complete the applicable implementation or test task before a new
  analysis. Run the analysis until no actionable finding remains. Then add the result to
  T056 and the Constitution Check in the plan. Research R19 records zero actionable
  findings after the traceability correction. (delivered)

- [x] T084 After T083, rerun every gate from T082 against the final analyzed tree. If a
  gate fails, fix the cause and rerun the complete affected gate set. Record the final
  commands, results, counts, and measurements in
  `specs/3671-interactive-terminal/research.md` per Constitution IV, T054, and T056.
  Research R20 records the complete passing gate set. (delivered)

## Phase 11: Convergence Correction

- [X] T085 [P] CRITICAL: After T072, replace
  `src/mist/realtime/websocket_streams/catalog/registry.py` and
  `src/mist/realtime/websocket_streams/catalog/utilities.py` with compliant packages. Keep each
  `__init__.py` docstring-only, and move behavior into named leaf classes without wrappers.
  Use the shared structured logger from T072. Update imports and tests under
  `tests/unit/websocket_streams/catalog/`. Preserve catalog discovery, lock flags, fields,
  safety classes, and page payloads as required by Constitution I, II, V, and VII
  (contradicts).

- [X] T086 [P] CRITICAL: After T072, replace
  `src/mist/realtime/websocket_streams/intake/fields.py`,
  `src/mist/realtime/websocket_streams/intake/identifiers.py`,
  `src/mist/realtime/websocket_streams/intake/pickers.py`, and
  `src/mist/realtime/websocket_streams/intake/start_request.py` with compliant packages. Keep each
  `__init__.py` docstring-only, and move behavior into named leaf classes without wrappers.
  Use the shared structured logger from T072. Update imports and tests under
  `tests/unit/websocket_streams/intake/`. Preserve validation, identifiers, picker caches,
  locks, targets, parameters, and request errors as required by Constitution I, II, V, and
  VII (contradicts).

- [X] T087 [P] CRITICAL: After T073, replace
  `src/mist/realtime/websocket_streams/live/runners/channel.py` and
  `src/mist/realtime/websocket_streams/live/runners/text.py` with compliant packages. Keep each
  `__init__.py` docstring-only, and move behavior into named leaf classes without wrappers.
  Use the shared structured logger from T072. Update imports and tests under
  `tests/unit/websocket_streams/live/runners/`. Preserve retry budgets, healthy resets,
  event routing, message shaping, packet summaries, and address redaction. Constitution I,
  II, V, and VII, FR-007, FR-009, and T070 require this behavior (contradicts).

- [X] T088 CRITICAL: After T074 through T076 and T085 through T087, replace
  `src/mist/realtime/websocket_streams/live/sessions/buffer.py`,
  `src/mist/realtime/websocket_streams/live/sessions/manager.py`, and
  `src/mist/realtime/websocket_streams/live/sessions/record.py` with compliant packages. Keep each
  `__init__.py` docstring-only. Move behavior into named leaf classes without wrappers.
  Use the shared structured logger from T072. Update imports and tests under
  `tests/unit/websocket_streams/live/sessions/`. Preserve buffer limits, session states,
  runner creation, terminal binding, cleanup, payloads, and failure behavior. Constitution
  I, II, V, and VII and FR-013 through FR-019 require this behavior (contradicts).

- [X] T089 [P] CRITICAL: After T074, replace
  `src/mist/realtime/websocket_streams/live/terminal/state.py` with the compliant package
  `src/mist/realtime/websocket_streams/live/terminal/state/`. Keep its `__init__.py` docstring-only.
  Split size, status, state, and chunk payload behavior into named leaf classes without
  wrappers. Use the shared structured logger from T072. Update imports and tests under
  `tests/unit/websocket_streams/live/terminal/`. Preserve terminal state, size, close, and
  payload behavior as required by Constitution I, II, V, and VII and FR-012 through FR-019
  (contradicts).

- [X] T090 CRITICAL: After T085 through T089, replace
  `src/mist/realtime/websocket_streams/web/blueprint.py` and
  `src/mist/realtime/websocket_streams/web/services.py` with compliant packages. Keep each `__init__.py`
  docstring-only, and move route, request, service, and picker behavior into named leaf
  classes without wrappers. Use the shared structured logger from T072. Update all imports,
  route tests, service tests, and browser journeys under `tests/unit/websocket_streams/web/`
  and `tests/e2e/websockets_tab/`. Preserve routes, CSRF checks, errors, limits, downloads,
  pickers, and terminal service behavior. Constitution I, II, V, and VII and FR-046 through
  FR-048 require this behavior (contradicts).

- [X] T091 After T078 and T085 through T090, extend
  `tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py`.
  Include all 25 Python modules from the final analysis and each replacement leaf module.
  Prove that every original path is compliant or became a compliant package. Target the
  28 classes and 19 functions that the analysis reported. Recursively scan every target
  package to prevent a violation in a new leaf. Print the direct target counts and the
  recursive path, module, class, and function counts. Rerun the bounded failure proof and
  the compliant-tree proof per Constitution I and II (partial). The last run scanned 25
  paths, 145 modules, 204 classes, and 619 functions.

### T081 evidence for completed convergence tasks

All commands used `.venv\Scripts\python.exe`. Each command ran in the issue #3671
worktree on 2026-10-02.

| Task | Exact tests and command | Count and result |
| - | - | - |
| T072 | `test_records_are_ascii_json_with_only_bounded_safe_fields`, `test_sensitive_fields_are_redacted_at_boundary`, and `test_safe_text_values_redact_embedded_secrets`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\runtime\test_frame_decoder.py tests\unit\websocket_streams\live\transport\runtime\test_frame_reader.py tests\unit\websocket_streams\live\transport\runtime\test_structured_logging.py -q`. | PASS. 30 passed. The focused logging file contributes 15 passed tests. |
| T073 | `test_endpoint_records_are_json_and_exclude_secrets`, `test_stream_records_are_json_and_exclude_channel_paths`, and `test_shell_records_are_json_and_exclude_input`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\test_ws_endpoint.py tests\unit\websocket_streams\live\transport\clients -q`. | PASS. 62 passed. |
| T074 | `test_trim_reports_gap_and_keeps_newest_bytes`, `test_queued_send_then_release_preserves_order`, `test_input_size_and_rate_limits_preserve_contract_codes`, and `test_payload_logs_only_bounded_metadata`. Command: `python -m pytest tests\unit\websocket_streams\live\terminal -q`. | PASS. 25 passed. |
| T075 | `test_trigger_posts_only_after_channel_subscribed`, `test_early_command_output_before_post_return_is_kept`, `test_show_command_runs_one_hundred_times_with_full_output`, and `test_utility_trigger_table_matches_sdk_requests`. Command: `python -m pytest tests\unit\websocket_streams\live\runners\utility tests\contract\websocket_streams\test_ws_utility_trigger_parity.py -q`. | PASS. 42 passed. |
| T076 | `test_shell_first_output_marks_live_and_releases_queued_input`, `test_shell_logs_do_not_hold_address_input_or_output`, and `test_shell_history_preserves_raw_control_and_split_utf8_bytes`. Command: `python -m pytest tests\unit\websocket_streams\live\runners\test_ws_shell_runner.py -q`. | PASS. 18 passed. |
| T077 | `test_j2_typed_text`, `test_j13_paste_keys`, `test_j19_split_screen_updates`, `test_j22_log_safety`, and `test_review_fr048_page_gets_no_shell_address`. Command: `python -m pytest tests\e2e\websockets_tab -q`. | PASS. 57 passed. |
| T078 | `test_bounded_bad_fixture_fails`, `test_unreadable_input_fails`, and `test_current_feature_obeys_structural_limits`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\runtime\test_ws_feature_structure.py -q -s`. | PASS. 3 passed. The red fixture failed at 6 module children. |
| T079 | `test_trigger_order_controls_early_command_event_retention` and `test_split_screen_sequence_requires_owned_byte_retention`. Command: `python -m pytest tests\contract\websocket_streams\test_ws_sdk_contract.py -q`. | PASS. 8 passed. The ordering proof checks 1 event. The screen proof checks 2 frames. |
| T085 | `test_stream_catalog_payload_hides_paths_and_marks_locks`, `test_stream_catalog_logs_bounded_json_without_catalog_keys`, and `test_utility_catalog_counts_match_contract`. Command: `python -m pytest tests\unit\websocket_streams\catalog -q`. | PASS. 18 passed. |
| T086 | `test_identifier_logs_use_bounded_json_without_identifier_text`, `test_start_request_locks_shell_and_checks_confirmation`, and `test_picker_failure_returns_reason`. Command: `python -m pytest tests\unit\websocket_streams\intake -q`. | PASS. 32 passed. |
| T087 | `test_post_subscription_flapping_consumes_retry_budget`, `test_stable_quiet_connections_receive_fresh_retry_budgets`, and `test_shell_address_filter_redacts_wss_address`. Command: `python -m pytest tests\unit\websocket_streams\live\runners\test_ws_channel_runner.py tests\unit\websocket_streams\live\runners\test_ws_message_text.py -q`. | PASS. 24 passed. |
| T088 | `test_shell_audit_and_terminal_input_queue`, `test_terminal_payload_and_bytes`, and `test_runner_factory_builds_each_runner_kind`. Command: `python -m pytest tests\unit\websocket_streams\live\sessions -q`. | PASS. 46 passed. |
| T089 | `test_size_and_close_logs_are_bounded_json`, `test_payload_matches_contract_fields`, and `test_payload_logs_only_bounded_metadata`. Command: `python -m pytest tests\unit\websocket_streams\live\terminal\test_ws_terminal_state.py -q`. | PASS. 6 passed. |
| T090 | `test_post_without_the_form_token_is_refused`, `test_websocket_routes_do_not_leak_secrets`, `test_ready_terminal_gateway_reaches_the_manager`, and the 57 browser journeys. Commands: `python -m pytest tests\unit\websocket_streams\web -q` and `python -m pytest tests\e2e\websockets_tab -q`. | PASS. 49 unit tests and 57 browser tests passed. |
| T091 | `test_bounded_bad_fixture_fails`, `test_unreadable_input_fails`, and `test_current_feature_obeys_structural_limits`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\runtime\test_ws_feature_structure.py -q -s`. | PASS. 3 passed. The guard checked 27 mappings, 25 analyzed paths, 145 modules, 204 classes, and 619 functions. |

- [x] T092 After T083 and T084, complete the final pre-commit convergence checkpoint.
  Confirm that the final analysis has no actionable finding and that all T084 gates pass.
  Do not treat the earlier T082 results as final evidence. Record the final task-audit and
  STE results in `specs/3671-interactive-terminal/research.md` per Constitution IV, T054,
  and T056. Research R20 records zero actionable findings, the passing final gates, four
  passing STE scores, and six open tasks before this checkpoint closed. (delivered)
