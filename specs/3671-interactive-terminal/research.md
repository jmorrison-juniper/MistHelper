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

The table also holds the shell trigger. The software kit sends
`POST /api/v1/sites/{site_id}/devices/{device_id}/shell` with the body `{}`. The answer holds
the shell address in `url`. The EX shell and the SRX shell use the same request.

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
- Ctrl+Shift+C and Ctrl+Insert copy.
- Ctrl+V and Cmd+V without Shift use the native paste event of the browser when the
  `ctrlVBehavior` preference is `paste`. That value is the default.
- Ctrl+Shift+V and Shift+Insert read the clipboard on a secure page. On a page without TLS,
  or when the browser refuses the read, these keys open the paste dialog.
- Copy by selection runs on mouse up.
- The page uses `navigator.clipboard` when the page is a secure context. If not, the page
  uses a hidden text area and `document.execCommand('copy')`.
- The menu Paste and the Paste button read the clipboard on a secure page. On a page without
  TLS, they open a paste dialog, and the operator presses Ctrl+V in the dialog.
- The page sends pasted text through the `term.paste()` method of xterm.js. That method
  changes each line end to a carriage return. It also adds the bracketed paste markers when
  the device asks for them.

**Reason**: A browser blocks the clipboard API on a plain HTTP page from another computer.
The native paste event, the paste dialog, and `execCommand('copy')` work in that case.

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
- A channel stream does not connect again after an HTTP 4xx refusal of the WebSocket
  handshake, because a retry cannot heal it. The session fails at once with the refusal
  reason. HTTP 408 and HTTP 429 are the exceptions, because a wait can heal them. They use
  the normal retry rule.
- The `ConnectFailure` class in `transport/endpoint.py` changes each open error to a plain
  reason. The reasons name an HTTP refusal with its status, a timeout, a TLS failure, a name
  lookup failure, or a network failure. If the last attempt fails to open, the final session
  reason names that open failure.
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

## R13. Live check results (task T055)

The live checks ran on 2026-10-01 against the lab organization. They used Morrison-Switch
and SRX-1500, read-only commands, a host portal, and the test container
`misthelper-tmp-issue3671-live`.

| Question | Result |
| - | - |
| Shell host | `api-ws.mist.com`. The host is inside the `mist.com` base domain, so the R9 rule needs no change. |
| NUL prefix | Each shell and screen output frame starts with one NUL byte. The shell client removes that byte. After `exit`, the Mist cloud sends a close frame with no payload. The reader reports that frame as code 1005. |
| Show ARP pause | The first message arrives after about 7.4 seconds on SRX-1500. All rows then arrive within 1 second. The rows from Morrison-Switch also arrive within 1 second. |
| Show Route pause | With no protocol, SRX-1500 sends one table message, so the output has no pause. The table holds 0 rows, and the page shows "The device sent an empty table." A read-only probe on 2026-10-02 showed that the Mist cloud itself sends that empty table for an empty body, for Protocol `any`, and for VRF `default`. The request body equals the SDK body. Issue #3716 asks for a hint on the form. |
| Show Route with a protocol | Protocol `direct` gave 5 of 5 full runs through the browser on 2026-10-02. Each run held 5,269 characters and 102 lines. With the digits masked, the 5 texts are equal, because only the route ages change. The cloud split the text into 39 to 65 messages, and each run took 7.8 to 9.1 seconds. |
| Message rows | The page shows each cloud message as one row, and the cloud splits the text at random points. A word can start in one row and end in the next row. Issue #3723 records this defect, which also exists on `main`. |
| Show ARP runs | SRX-1500 gave 5 of 5 finished runs, and each run took 8.7 to 9.8 seconds. The view held 134 to 162 lines. That count includes the header line of each message row, so it changes with the message count. |
| Test device runs | ARP and Route each gave 100 of 100 full runs against a fake device that answers at once. The 100 ARP runs took 6.84 seconds, and the 100 Route runs took 6.64 seconds. |
| Quiet time | No pause is longer than 5 seconds, so the trigger table keeps a quiet time of 5 seconds. |
| Screen size | Top and Monitor Traffic open at 80 x 40 and fill all 40 rows. |
| Silent shell | A quick fourth shell on the switch can stay silent. The page shows a notice after 20 seconds. The Mist cloud closes the terminal after about 90 seconds, and the page shows the no-answer reason (issue #3710). |
| Echo time | The host portal measured a median of 212 ms and a 95th percentile of 239 ms. The test container measured a median of about 212 ms over 80 samples. One sample took 530 ms. |

### Browser measurements against the fake device (task T050)

The measurements ran on 2026-10-02 on the Windows workstation. They used headless Chromium,
the real portal routes, and the fake Mist cloud. The live echo time above includes the
round trip to the Mist cloud, so it does not measure the portal part.

| Criterion | Target | Result |
| - | - | - |
| SC-001 echo | The portal adds less than 50 ms for 95 percent of keys | 200 keys: median 15.3 ms, 95th percentile 28.9 ms. The test fails above 500 ms, because a Windows test run can pause for a long time. |
| SC-007 output | 1 MiB shows in less than 3 seconds | 0.29 seconds. The test waits until the counter shows 1,048,640 bytes and the prompt shows after the output. |
| SC-005 load | A page loads in less than 2 seconds while 5 shells send output | 0.24 seconds |
| Paste split | A 256 KiB paste splits in less than 50 ms | 0.50 ms for 64 parts of 4,096 characters |

