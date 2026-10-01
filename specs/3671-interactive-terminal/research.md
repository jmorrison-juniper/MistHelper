# Research: Own Mist WebSocket Client and Interactive Terminal

This file records each design decision for issue #3671. Each entry gives the decision, the
reason, and the options that the design does not use.

## R1. Own WebSocket client for each live connection

**Decision**: The portal opens each Mist live connection with its own client. The client
uses the synchronous `create_connection` function of `websocket-client`. One reader thread
serves each connection. The Mist software kit stays for REST requests only.

**Reason**:

- The software kit sends the command request first and subscribes after that. Fast output
  arrives before the subscription, so the first lines disappear (issue #3660).
- The software kit feeds each screen message into a screen model one message at a time. A
  control sequence in two messages then shows stray characters (issue #3659).
- The software kit ends a command after a short quiet time. ARP uses 1 second. Routes and
  sessions use 2 seconds. A device that pauses longer loses the rest of the output.
- The shell class of the software kit holds each send for up to 10 seconds before the first
  output. It also changes the socket timeout for each read.

**Options not used**:

- A repair in the software kit. The fix takes a release cycle, and the portal needs the fix
  now. The team can still report the defects to the software kit project.
- A subclass of the software kit classes. The subclass depends on private callbacks and on
  the thread model of the software kit.
- The `WebSocketApp` callback loop. It is harder to stop from another thread and harder to
  test with a fake socket.
- The `websockets` package for asyncio. It is a new dependency, and the portal runs threads.

## R2. Protocol facts from the software kit version 0.64

| Fact | Value |
| - | - |
| Stream address | `wss://` + the cloud host with `api.` changed to `api-ws.` + `/api-ws/v1/stream` |
| Token sign-in | The header `Authorization: Token <token>` |
| Password sign-in | The session cookies. The client skips a cookie that holds a CR or an LF character. |
| TLS | The `verify` and `cert` values of the API session |
| Subscribe | The text frame `{"subscribe": "<channel>"}` |
| Subscribe answer | The event `channel_subscribed` with the channel, or `subscribe_failed` with a detail |
| Data event | `{"event": "data", "channel": "...", "data": ...}`. The data can be JSON text. |
| Command channel | `/sites/{site_id}/devices/{device_id}/cmd` |
| Capture channels | `/sites/{site_id}/pcaps` and `/orgs/{org_id}/pcaps` |
| Command filter | The `session` value of the trigger answer |
| Capture filter | The `id` value of the trigger answer, against `capture_id` in each event |
| Command text | The `raw` value of each event |
| Capture record | The `pcap_dict` value of each event |
| Shell and screen address | The `url` value of the trigger answer |
| Shell input | A binary frame: one NUL byte, then the UTF-8 text |
| Shell size | The text frame `{"resize": {"width": <cols>, "height": <rows>}}` |
| Binary output | The software kit removes NUL bytes. Text that is not JSON becomes `{"raw": text}`. |

The software kit reads 4 private attributes of the API session: `_cloud_uri`, `_apitoken`,
`_apitoken_index`, and `_session`. The own client reads the same attributes. The software
kit contract test pins them, so a new software kit version fails the test before a release.

## R3. Command order and end rules

**Decision**: The utility runner uses this order for a command with a channel.

1. Open the stream connection.
2. Send the subscribe frame, and wait for `channel_subscribed`. The wait is 10 seconds.
3. Send the REST trigger with `mist_post`.
4. Read the `session` value or the capture `id` from the trigger answer.
5. Keep the events that arrived before step 4, then filter all events by that value.

The end rules follow the software kit, with one change.

| Limit | Value | Source |
| - | - | - |
| First output | 30 seconds | The software kit value |
| Quiet time | The software kit value, but 5 seconds or more | Changed. ARP, routes, and sessions get 5 seconds. |
| Total time | 60 seconds | The software kit value. Captures use their own duration. |

**Reason**: A quiet time of 1 or 2 seconds cuts the output of a slow device. The live check
measures the largest pause of Show ARP and Show Route on the lab gateway. If a pause is
longer than 5 seconds, the table gets a longer value for that command.

**Options not used**: An end marker in the output. Mist sends no known end marker.

## R4. Trigger table and parity test

**Decision**: The `UtilityTriggerTable` class holds the method, the path, and the body for
each of the 52 catalog commands that use a REST trigger. A contract test calls each
software kit function with a recording API session. The test then compares the recorded
request with the table request.

**Reason**: FR-004 asks for the same request as the software kit. The recording method
already worked for this research. All 52 triggers use POST. 41 commands use the command
channel, 7 use a capture channel, and 4 screen commands use the `url` value.

## R5. Browser transport: long poll and short POST requests

**Decision**: The page reads terminal bytes with a long poll to
`GET /api/websockets/sessions/<id>/terminal`. The page sends keys and pasted text with
`POST .../input`, and the size with `POST .../resize`.

**Reason**:

- The content security policy allows `connect-src 'self'` only. The page cannot connect to
  Mist directly.
- A long poll answers as soon as new bytes arrive, so the added echo time stays small.
- Each wait holds a Gunicorn thread for 25 seconds at most. The portal allows 8 waiting
  polls. A poll above that limit gets an answer at once.

**Options not used**:

- Server-sent events. Each stream holds a thread for the full session life.
- A browser WebSocket to the portal. It needs a new package and a different Gunicorn worker.

## R6. Terminal emulator in the page

**Decision**: The page uses xterm.js 6.0.0 and the fit addon 0.11.0. The repository holds
a copy of each UMD build under `src/websocket_streams/web/static/vendor/xterm/`, with the MIT
license text.

**Reason**:

- The UMD build sets `window.Terminal` and `window.FitAddon`. A plain script tag loads it,
  and the page needs no build step.
- The policy allows scripts from the same origin and inline styles. xterm.js adds style
  elements, which the policy allows.
- The NOC network can block content delivery networks. A local copy always loads.
- xterm.js parses a split control sequence correctly, because it keeps its parser state
  between writes.

**Options not used**: A content delivery network. An own terminal emulator. The older
version 5.5.0.

## R7. Copy and paste

**Decision**:

- The key handler of the terminal decides each copy key and each paste key.
- Ctrl+C copies when the terminal holds a selection, and it sends no interrupt. With no
  selection, Ctrl+C sends the interrupt character.
- Ctrl+Shift+C and Ctrl+Insert copy. Ctrl+V, Ctrl+Shift+V, and Shift+Insert use the native
  paste event of the browser.
- Copy by selection runs on mouse up.
- The page uses `navigator.clipboard` when the page is a secure context. If not, the page
  uses a hidden text area and `document.execCommand('copy')`.
- The menu Paste and the Paste button read the clipboard on a secure page. On a page without
  TLS, they open a paste dialog, and the operator presses Ctrl+V in the dialog.
- The page sends pasted text through the `term.paste()` method of xterm.js. That method
  changes each line end to a carriage return. It also adds the bracketed paste markers when
  the device asks for them.

**Reason**: A browser blocks the clipboard API on a plain HTTP page from another computer.
The native paste event and `execCommand('copy')` work in that case.

## R8. Server byte history and input queue

**Decision**:

- The `ByteHistory` class keeps the newest output bytes. The default size is 1 MiB.
- Each byte has an absolute position. A reader asks for the bytes after a position.
- If the history no longer holds those bytes, the answer gives the count of lost bytes.
- The `TerminalInput` class keeps up to 4,096 characters that arrive before the first
  output. The class sends them in order when the first output arrives.
- Each session accepts 60 input requests each second and 16 KiB in each request.

**Reason**: The positions let the page continue after a break (FR-015). The queue keeps
fast typing after the session opens (FR-013). The limits protect the portal threads.

## R9. Shell address rule

**Decision**: The shell client accepts an address only when 2 conditions are true.

- The scheme is `wss`.
- The host is the base domain of the API cloud, or the host ends with a dot and that domain.

The base domain is the last 2 labels of the cloud host, for example `mist.com`.

**Reason**: The shell connection sends the token or the cookies. An address outside the
Mist domain can steal them (FR-008).

**Risk**: The live check records the shell host of the lab cloud. If the host is in a
different Mist domain, the rule gets that domain with the evidence in the pull request.

## R10. Keepalive and reconnection

**Decision**:

- Each connection reads with a 20-second timeout. On a timeout, the client sends a ping.
  After 2 silent intervals, the client closes the connection as dead.
- A channel stream connects again up to 3 times, after 1, 2, and 4 seconds. After the third
  failure, the session fails with a reason.
- A command, a capture, a screen command, and a shell do not connect again. A new
  connection starts a new device session.

## R11. Test server

**Decision**: The tests use a fake Mist cloud server that uses the Python standard library
only. The server speaks RFC 6455 with text frames, binary frames, ping, pong, and close. It
has fake devices for echo, commands, a split screen sequence, the interrupt character,
`exit`, and the bracketed paste mode. It records each frame that it receives.

**Reason**: The repository has no WebSocket server package. A small server keeps the tests
fast and offline.

## R12. History file

**Decision**: The page builds the history file from the xterm.js buffer. The file holds
plain text with no control codes.

**Reason**: The buffer holds the screen text after the control codes ran. The server
history holds raw bytes with control codes.
