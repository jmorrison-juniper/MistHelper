# Feature Specification: Own Mist Live Connections and an Interactive Shell Terminal

**Feature Branch**: `feat/3671-interactive-terminal`

**Created**: 2026-09-29

**Status**: Implementation complete, validation pending

**Input**: User description: "Use our own code for the Mist live connections instead of the
Mist software kit. Give the WebSockets tab a terminal that works like SecureCRT. The terminal
will be our most popular feature. Test it end to end in a real browser. Test typing, paste
into the terminal, and copy of highlighted text to the clipboard. Test copy by command and
copy by selection."

This feature closes issue #3671. It also closes issue #3659 (broken screen output) and issue
#3660 (lost command output).

## Background

The WebSockets tab (issue #3551) uses the Mist software kit for each live connection. Two
defects in that kit affect operators.

1. Issue #3660: `mistapi.device_utils.__tools.__ws_wrapper.WebSocketWrapper.start_with_trigger`
   sends the device command first and opens the output channel second. A fast device can
   answer before the channel opens. The operator then sees no output, or only partial output.
2. Issue #3659: the same SDK WebSocket wrapper reads each screen update alone. If one control
   sequence arrives in two parts, the screen shows stray characters.

The shell view is a line box today. The operator cannot use the arrow keys, Tab completion,
full-screen programs, or the clipboard in a normal way.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Work in a device shell like a desktop terminal (Priority: P1)

An operator opens a shell session on a switch or a gateway. The operator works in a
terminal that acts like a desktop terminal program. Each key goes to the device. The
terminal shows colors, cursor movement, and full-screen programs correctly.

**Why this priority**: The shell is the most used tool for a NOC engineer. A line box
cannot run Tab completion, command history, or a full-screen program.

**Independent Test**: Open a shell session against a test device. Type commands, use the
control keys, and resize the panel. Confirm that the test device receives each key in order
and that the terminal shows the device output correctly.

**Acceptance Scenarios**:

1. **Given** an unlocked shell and a typed device name, **When** the session opens,
   **Then** the terminal shows the device banner and the prompt.
2. **Given** an open shell, **When** the operator types `show version` and presses Enter,
   **Then** the device receives each character in order, and the terminal shows the output.
3. **Given** an open shell, **When** the operator presses a special key, **Then** the
   device receives the standard terminal code for that key. The special keys are the arrow
   keys, Tab, Backspace, Delete, Home, End, Page Up, Page Down, Esc, and F1 through F12.
4. **Given** an open shell with no text selected, **When** the operator presses Ctrl+C,
   **Then** the device receives the interrupt character.
5. **Given** an open shell, **When** the operator changes the window size, **Then** the
   device receives the new column count and row count.
6. **Given** a shell with no output yet, **When** the operator types, **Then** the portal
   keeps the keys. The portal sends them in order after the first output.
7. **Given** an open shell, **When** the device closes the shell, **Then** the terminal
   stops input and shows the reason that the session ended.
8. **Given** an open shell, **When** the device draws a full-screen program with colors,
   **Then** each character shows at the correct position and color.

---

### User Story 2 - Copy and paste like a desktop terminal (Priority: P1)

An operator copies text out of the terminal and pastes text into the terminal. The
clipboard behavior matches SecureCRT and Windows Terminal. Copy by selection is on by
default.

**Why this priority**: Operators copy output into tickets and paste configuration into the
device all day. A terminal without a correct clipboard is not usable for NOC work.

**Independent Test**: In a real browser, select terminal text with the mouse and read the
system clipboard. Put text on the clipboard, and paste it with each paste command. Confirm
the exact bytes that the test device receives.

**Acceptance Scenarios**:

1. **Given** copy by selection is on, **When** the operator selects text with the mouse,
   **Then** the clipboard holds the selected text. A notice states the character count.
2. **Given** copy by selection is off, **When** the operator selects text, **Then** the
   clipboard does not change.
3. **Given** selected text, **When** the operator presses Ctrl+Shift+C, Ctrl+Insert, or
   Ctrl+C, or uses the menu Copy, **Then** the clipboard holds the selected text.
4. **Given** selected text, **When** the operator presses Ctrl+C, **Then** the device does
   not receive the interrupt character.
5. **Given** one line on the clipboard, **When** the operator uses any paste command,
   **Then** the device receives the exact text. The paste commands are Ctrl+V,
   Ctrl+Shift+V, Shift+Insert, and the menu Paste.
6. **Given** a clipboard text with more than one line, **When** the operator pastes,
   **Then** a confirmation shows the line count and the first lines.
7. **Given** the paste confirmation, **When** the operator selects Cancel, **Then** the
   device receives nothing.
8. **Given** the paste confirmation, **When** the operator selects Paste, **Then** the
   device receives all lines in order, and each line end is a carriage return.
9. **Given** a device that turned on bracketed paste mode, **When** the operator pastes,
   **Then** the device receives the text between the bracketed paste markers.
10. **Given** 2,000 lines of configuration on the clipboard, **When** the operator pastes
    and confirms, **Then** the device receives every line once and in order.
11. **Given** a page that the browser opened over plain HTTP from another computer,
    **When** the operator copies, **Then** the copy still works.
12. **Given** the operator changed a clipboard setting, **When** the operator loads the
    page again, **Then** the page keeps the setting.

---

### User Story 3 - Get the full output of each device command (Priority: P1)

An operator runs a device command, such as Show ARP or Show Route, and gets the full output
each time. The fast answer of a device no longer causes a loss of output.

**Why this priority**: Issue #3660 makes device commands fail at random. A NOC engineer
cannot trust a tool that loses output.

**Independent Test**: Run each catalog command against a test device that answers at once.
Confirm that the page shows the full output in every run. Confirm that each command sends
the same request that the Mist software kit sends today.

**Acceptance Scenarios**:

1. **Given** a device that answers at once, **When** the operator runs Show ARP five times,
   **Then** the page shows the full output five times.
2. **Given** any catalog command, **When** the portal sends it, **Then** the request path
   and body match the request of the Mist software kit.
3. **Given** a command with no output, **When** the first-output limit ends, **Then** the
   session ends with the reason "No output arrived in time".
4. **Given** a running command, **When** the operator selects Stop, **Then** the session
   stops within 3 seconds.

---

### User Story 4 - See a correct live screen for Top and Monitor Traffic (Priority: P2)

An operator runs a screen command, such as Top or Monitor Traffic. The page shows the
screen as the device draws it, with no stray characters.

**Why this priority**: Issue #3659 makes the screen commands hard to read. The screen
commands are less frequent than the shell and the line commands.

**Independent Test**: Send a screen update that breaks inside a control sequence from a
test device. Confirm that the page shows the correct screen.

**Acceptance Scenarios**:

1. **Given** a control sequence that arrives in two parts, **When** the page shows the
   screen, **Then** the screen holds no stray characters.
2. **Given** a running screen command, **When** a new screen update arrives, **Then** the
   page draws the update over the old screen at the same position.
3. **Given** a screen command, **When** the operator types in the view, **Then** the
   device receives nothing, because the view is read-only.

---

### User Story 5 - Keep the live streams and captures that work today (Priority: P2)

The channel streams and the packet captures move to the new connection code. The operator
sees the same behavior as today.

**Why this priority**: The streams work today. The move removes the dependency on the kit
for live connections, but the operator gains no new function.

**Independent Test**: Run each channel stream and each capture type against a test server.
Confirm the same messages, states, and end reasons as today.

**Acceptance Scenarios**:

1. **Given** a channel stream, **When** the connection drops, **Then** the portal connects
   again up to 3 times before it reports a failure.
2. **Given** a channel that the cloud refuses, **When** the operator starts the stream,
   **Then** the session fails with the refusal reason.
3. **Given** a packet capture, **When** the capture runs, **Then** the page shows each
   packet summary of that capture only.
4. **Given** a packet capture, **When** the operator selects Stop, **Then** the portal asks
   the cloud to stop the capture.

---

### User Story 6 - Save the terminal history as text (Priority: P3)

An operator saves the terminal history as a plain text file for a ticket.

**Why this priority**: Operators can copy text today. A file is faster for long output.

**Independent Test**: Run commands in a shell, select Download, and compare the file with
the screen text.

**Acceptance Scenarios**:

1. **Given** a shell with history, **When** the operator selects Download, **Then** the
   browser saves a text file with the terminal history and no control codes.

### Edge Cases

- The network between the browser and the portal breaks for a short time. The terminal
  continues from the last byte that it received. If the portal no longer holds some bytes,
  the terminal shows a notice with the count of bytes that it cannot show.
- The device sends output faster than the browser reads it. The portal keeps the newest
  output up to its limit. The terminal shows a notice for the bytes that it lost.
- The pasted text is larger than the paste limit. The page refuses the paste and states
  the limit. The device receives nothing.
- The pasted text holds characters outside ASCII. The device receives the characters as
  UTF-8.
- The browser refuses clipboard read access for the menu Paste. The page tells the
  operator to press Ctrl+V.
- Two browser tabs show the same shell. Both tabs show the output, and both tabs can type.
- The operator closes the page. The portal ends the shell after the idle time.
- The session time limit nears its end. The terminal shows a notice two minutes before
  the end.
- The cloud gives a shell address without TLS or outside the Mist cloud domain. The portal
  refuses the address and ends the session with a reason.
- The operator switches between sessions in the session list. Each terminal shows its
  history again.
- The device opens the shell but sends no output. After 20 seconds, the terminal shows a
  notice that the device sent no output. If the cloud then closes the shell before any
  output, the session fails with a reason (issue #3710).

## Requirements *(mandatory)*

### Functional Requirements

**Live connections**

- **FR-001**: The portal MUST open each Mist live connection with its own connection code.
  This includes channel streams, device command output, packet capture output, and the
  device shell. The portal MUST use the Mist software kit only for REST requests.
- **FR-002**: For a device command, the portal MUST subscribe to the output channel and
  receive the subscription confirmation before it sends the command request.
- **FR-003**: The portal MUST keep the output messages that arrive before it knows the
  command session identifier. It MUST then show only the messages of that session.
- **FR-004**: Each catalog command MUST send the same request path and body as the Mist
  software kit. An automatic test MUST compare the two requests for every catalog command.
- **FR-005**: The connection code MUST support each Mist cloud region, token sign-in, and
  password sign-in. It MUST use the TLS settings of the API session and the proxy settings
  of the host.
- **FR-006**: Each channel, utility, shell, and screen connection MUST send a ping after
  20 seconds without a received frame. It MUST close after 40 seconds without a received
  frame. A check can differ from either boundary by one 100-millisecond socket-read slice.
- **FR-007**: The portal MUST connect a dropped channel stream again up to 3 times. After
  the third failure, the session MUST fail with a reason. If reconnect output remains in
  the message buffer, the page MUST continue without a gap warning. If the buffer dropped
  reconnect output, the page MUST show a gap warning.
- **FR-008**: The portal MUST refuse a shell address that does not use TLS. It MUST also
  refuse a shell address outside the Mist cloud domain of the API session.
- **FR-009**: Logs MUST NOT hold API tokens, cookies, the path of a shell address,
  keystrokes, pasted text, or terminal output. Logs can hold host names, byte counts, and
  session states.

**Terminal**

- **FR-010**: The shell view MUST interpret the standard terminal control sequences. This
  includes cursor movement, erase, colors, and the alternate screen.
- **FR-011**: Each key that the operator presses in the terminal MUST go to the device in
  the order typed. This includes control keys, Esc, arrows, function keys, Tab, Backspace,
  Delete, Home, End, Page Up, and Page Down.
- **FR-012**: The shell terminal MUST send its size when the session starts and each time
  the panel size changes. The column count MUST be 20 to 500. The row count MUST be 5 to
  200. A screen command MUST send 80 columns and 40 rows once when it starts. It MUST
  ignore later panel-size changes (see FR-035).
- **FR-013**: The portal MUST keep up to 4,096 characters that the operator types before
  the first output. It MUST send them in order when the first output arrives.
- **FR-014**: The terminal MUST keep at least 5,000 lines of history.
- **FR-015**: After a break, the terminal MUST continue from the last byte that it
  received. If the portal no longer holds those bytes, the terminal MUST show the count of
  bytes that it cannot show.
- **FR-016**: When the session ends, the terminal MUST stop input and show the end reason.
- **FR-017**: When less than two minutes of the session time limit remain, the terminal
  MUST show a notice.
- **FR-018**: When the operator returns to a session in the session list, the terminal
  MUST show the history that the portal holds for that session.
- **FR-019**: If a shell sends no output for 20 seconds after it opens, the terminal MUST
  show a notice. The shell MUST continue until the cloud closes it. If the cloud closes the
  shell before output, the session MUST fail with a reason. If the device closes after
  output, the session MUST finish. For a utility command, the fixed server first-output
  limit MUST be 30 seconds. Its supported range MUST be exactly 30 seconds, with no
  environment override. The source MUST be
  `UtilityTriggerDefinitions.FIRST_OUTPUT_SECONDS`.

**Copy and paste**

- **FR-020**: Copy by selection MUST be on by default. The operator MUST be able to turn it
  off. The browser MUST keep the setting.
- **FR-021**: These actions MUST copy the selected text: Ctrl+Shift+C, Ctrl+Insert, Ctrl+C
  with a selection, Cmd+C on macOS, and the menu Copy.
- **FR-022**: Ctrl+C with no selection MUST send the interrupt character to the device.
  Ctrl+C with a selection MUST NOT send the interrupt character.
- **FR-023**: These actions MUST paste: Ctrl+V, Ctrl+Shift+V, Shift+Insert, Cmd+V on
  macOS, the menu Paste, and the Paste button.
- **FR-024**: The browser page MUST change each line end in pasted text to a carriage
  return. If xterm.js detects bracketed paste mode, the page MUST put the text between the
  bracketed paste markers. The server MUST preserve the resulting UTF-8 bytes.
- **FR-025**: Before it sends pasted text with more than one line, the page MUST show a
  confirmation. The confirmation MUST show the line count and the first five lines. The
  operator MUST be able to turn the confirmation off. The browser MUST keep the setting.
- **FR-026**: The page MUST refuse pasted text larger than 256 KiB and state the limit.
- **FR-027**: The device MUST receive large pasted text complete and in order. For pasted
  text larger than 16 KiB, the page MUST show the progress.
- **FR-028**: Copy MUST work when the browser opened the page over plain HTTP from another
  computer.
- **FR-029**: After each copy, the page MUST show a notice with the character count. A
  screen reader MUST announce the notice.
- **FR-030**: A right-click in the terminal MUST open a menu with Copy, Paste, Select all,
  and Clear. Clear MUST remove the local history only.
- **FR-031**: The terminal font MUST start at 14 pixels. The A- and A+ controls MUST use
  one-pixel steps from 10 through 28 pixels. The browser MUST keep the value in
  `misthelper.wsTerminal.prefs` and restore it after a reload.

**Screen commands**

- **FR-035**: Top and Monitor Traffic MUST show in a read-only terminal view. The view MUST
  send a fixed size of 80 columns and 40 rows when it starts. It MUST ignore later panel
  changes. The view MUST interpret control sequences that arrive in more than one part.

**History file**

- **FR-040**: The operator MUST be able to save the terminal history as a plain text file
  with no control codes.

**Safety**

- **FR-045**: The shell MUST stay locked until the portal setting turns it on. Each shell
  session MUST need the typed device name. These rules exist today, and they MUST stay.
- **FR-046**: Each input or resize request MUST carry the form token. An input request
  MUST hold at most 16 KiB of UTF-8 text. Input before first output MUST hold at most 4,096
  characters. A resize MUST use 20 through 500 columns and 5 through 200 rows. Input and
  resize MUST share a limit of 60 requests in each monotonic one-second window per session.
- **FR-047**: The shell view MUST show the warning that each command runs on the live
  device.
- **FR-048**: The page MUST NOT receive the shell address or any sign-in secret.

### Key Entities

- **Terminal session**: A shell session or a screen command session. It holds the device,
  the state, the byte history, the terminal size, the keys typed before the first output,
  and the end reason.
- **Byte history**: The newest output bytes of one terminal session, up to a limit. Each
  byte has a fixed position number. A reader asks for the bytes after a position.
- **Command request**: The request path and the request body for one catalog command.
- **Live connection**: One connection to the Mist cloud. It has a kind (channel, command,
  capture, or shell), a state, and a count of connection attempts.
- **Terminal preferences**: The browser settings for copy by selection, the paste
  confirmation, and the font size.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 95 percent of keys, the portal adds less than 50 milliseconds to the echo
  time between the browser and the test device.
- **SC-002**: A paste of 2,000 lines arrives complete and in order in 100 of 100 test runs.
- **SC-003**: Show ARP and Show Route give the full output in 5 of 5 runs on the lab
  gateway. They also give the full output in 100 of 100 runs against a test device that
  answers at once.
- **SC-004**: The browser test suite passes each copy action, each paste action, and each
  key in this specification.
- **SC-005**: Start one 1 MiB output burst in each of five shell sessions. Hold all five
  bursts open across the measurement. Each stream MUST send bytes during each measured
  load and MUST complete exactly 1 MiB. Alternate five visible loads of `/websockets` with
  five visible loads of `/operations`. The nearest-rank p95 selects rank 10 from the 10
  complete loads and MUST be less than 1 second. The test permits no failed load.
- **SC-006**: A scan of the logs from the test suite finds no token, cookie, shell address
  path, keystroke, pasted text, or terminal output.
- **SC-007**: The terminal shows 1 MiB of device output within 3 seconds on the local test
  path.
- **SC-008**: The screen commands show no stray characters across 100 consecutive updates
  with split control sequences in one session.

## Assumptions

- The Mist shell protocol and the Mist stream protocol work as the Mist software kit
  version 0.64 shows them.
- The lab switch "Morrison-Switch" and the lab gateway "SRX-1500" are available for the
  live checks. The live checks use read-only commands only.
- An owner-approved destructive port-bounce journey can provide separate safety evidence.
  It is not part of the read-only live-check scope.
- Each browser tab that shows a session can type into that session.
- The current session limits stay: five sessions, two minutes of idle time, and a 30-minute
  life. The existing settings can change these limits.
- Out of scope: a direct SSH connection to a device, file transfer, split panes, and a
  history file on the portal disk.
- The terminal supports Chrome 120 or newer and Edge 120 or newer. The automated browser
  gate uses the current Playwright Chromium release. Firefox support is outside this feature.
