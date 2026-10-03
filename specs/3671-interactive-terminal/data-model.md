# Data Model: Own Mist WebSocket Client and Interactive Terminal

All data stays in memory. The portal writes no terminal data to a disk. The browser keeps
the terminal preferences in local storage.

## Terminal state

The `StreamSession` record of a shell session or a screen command session holds one
`TerminalState` value. Other sessions hold `None`.

| Field | Type | Rule |
| - | - | - |
| `history` | `ByteHistory` | One history for each session |
| `input` | `TerminalInput` or `None` | `None` for a screen command, because its view is read-only |
| `cols` | integer | Shell range is 20 to 500. A screen command is fixed at 80. |
| `rows` | integer | Shell range is 5 to 200. A screen command is fixed at 40. |
| `expires_mono` | float | The start time plus the session life limit |
| `expires_at` | text | The same time in UTC, for the page |

A shell session starts with a terminal size from the browser. It can resize.
Top and Monitor Traffic use a terminal of exactly 80 columns and 40 rows. The
page does not fit a screen command to the panel, and it sends no resize request.

The session states do not change. A terminal session moves through these states.

```text
connecting --(socket open)--> live --(first output)--> live and input_ready
live --(operator stop or reaper)--> stopping --> stopped
live and input_ready --(device sends a close frame, for example after exit)--> finished
live and input_ready --(local input or resize write fails)--> failed
live --(a screen command reaches its time limit)--> finished
live and input_ready --(connection lost with no close frame)--> failed
live without output --(far side ends the connection)--> failed
connecting or live --(error)--> failed
```

The `_outcome()` method of the terminal runner selects the final state when the connection
ends. Each terminal session uses this order of rules.

1. If the operator or the reaper closed the connection, the state is `stopped`.
2. If the device sent no output before the far side ended the connection, the state is
   `failed`. The reason is `NO_ANSWER_REASON` (issue #3710, FR-019).
3. If a local input or resize write closes the connection after output, the state is
   `failed`. The reason is `WRITE_FAILED_REASON`:
   `The terminal could not send data to the device.` (issue #3741).
4. If the device sent output and then a close frame, the state is `finished`. The reason is
   `CLOSED_REASON`.
5. If the connection ended with no close frame, the state is `failed`. The reason is
   `DROPPED_REASON`.

A screen command checks one rule before these rules. If its time limit closed the
connection and no stop is in progress, the state is `finished`. The reason is
`The screen command reached its time limit of N seconds.` N is the total time limit of the
command in the trigger table, in whole seconds. The screen runner in
`src/websocket_streams/live/runners/utility/screen.py` applies this rule.

The page shows a notice when a shell sends no output for 20 seconds. The notice is a page
value only. It does not change the session state.

When the session leaves the live states, the history closes. Each waiting read then gets an
answer at once.

## ByteHistory

`ByteHistory` keeps the newest output bytes of one terminal session.

| Field | Type | Rule |
| - | - | - |
| `limit` | integer | The size limit in bytes. The default is 1,048,576. |
| `first` | integer | The absolute position of the oldest kept byte |
| `next` | integer | The absolute position after the newest byte |
| `closed` | boolean | True after the session ends |

Rules:

- `next - first` is never more than `limit`.
- An append adds the bytes at `next`. If the history is then too large, the history removes
  the oldest bytes and moves `first`.
- A read after position `after` returns the bytes from `max(after, first)` to `next`. One
  answer holds 512 KiB at most.
- If `after` is less than `first`, the answer reports `gap = first - after`.
- If `after` is more than `next`, the history refuses the read with `bad_request`.
- A wait blocks on a condition until `next` is more than `after`, the history closes, or
  the wait time ends.

The setting `PORTAL_WS_TERMINAL_HISTORY_KB` changes the limit. The range is 256 to 8,192.
The default is 1,024.

## TerminalChunk

The terminal read route returns one `TerminalChunk`.

| Field | Type | Meaning |
| - | - | - |
| `data` | text | The new bytes in base64 |
| `first` | integer | The oldest kept position |
| `next` | integer | The position for the next read |
| `gap` | integer | The count of bytes that the history no longer holds |
| `state` | text | The session state |
| `reason` | text | The end reason, or an empty text |
| `input_ready` | boolean | True after the first output |
| `read_only` | boolean | True for a screen command |
| `expires_at` | text | The time of the session life limit, in UTC |

## TerminalInput

`TerminalInput` controls the keys and the pasted text of one shell session.

| Field | Type | Rule |
| - | - | - |
| `pending` | list of text | The text that arrived before the first output |
| `pending_chars` | integer | 4,096 at most |
| `ready` | boolean | True after the first output |
| `rate` | `RequestRateLimiter` | One session-scoped monotonic window for input and resize |

Rules:

- One request holds 16 KiB of UTF-8 text at most. A larger request gets `too_large` (413).
- Input and resize share one session-scoped limit of 60 requests in each monotonic second.
- Request 61 gets `rate_limited` (429), including after the clock moves backward.
- Before the first output, the text goes into `pending`. If `pending` then holds more than
  4,096 characters, the request gets `input_full` (409), and the text does not go into
  `pending`.
- At the first output, the queue sends the pending text in order. Then it sends each new
  request at once.
- A session that is not live gets `not_open` (409).
- If a local input write fails, the request gets `not_open` (409). The reader then ends the
  session as `failed` with `WRITE_FAILED_REASON`.
- If a live resize write fails, the request gets `not_open` (409). The reader then ends the
  session as `failed` with `WRITE_FAILED_REASON`. A resize before the socket opens stays
  deferred and does not fail the session.

## UtilityRequest

`UtilityRequest` holds the request of one catalog command.

| Field | Type | Rule |
| - | - | - |
| `key` | text | The catalog key, for example `srx.retrieveArpTable` |
| `method` | text | `POST` for each of the 52 commands |
| `path` | text | The path with the site, the organization, and the device values filled in |
| `body` | object | The same body as the Mist software kit |
| `channel` | text | `cmd`, `site_pcaps`, `org_pcaps`, or `url` |
| `first_output_seconds` | float | 30 |
| `quiet_seconds` | float | The software kit value, but 5 or more |
| `total_seconds` | float | 60, or the capture duration plus 10 |

## LiveConnection

The `StreamClient` class and the `ShellClient` class each hold one Mist connection.

| Field | Type | Rule |
| - | - | - |
| `kind` | text | `channel`, `command`, `capture`, `shell`, or `screen` |
| `state` | text | `connecting`, `open`, `closing`, `closed`, or `failed` |
| `attempts` | integer | 4 at most for a channel stream, and 1 for all other kinds |
| `host` | text | The host name only. Logs can hold it. |
| `bytes_in` | integer | The count of received bytes |
| `bytes_out` | integer | The count of sent bytes |

The address path, the token, and the cookies never leave the client object.

## TerminalPreferences

The page keeps the preferences under the local storage key `misthelper.wsTerminal.prefs`.

| Field | Type | Default | Rule |
| - | - | - | - |
| `copyOnSelect` | boolean | true | Copy by selection |
| `confirmPaste` | boolean | true | The paste confirmation for text with more than one line |
| `ctrlVBehavior` | text | paste | Ctrl+V and Cmd+V use the native paste event when the value is `paste` |
| `fontSize` | integer | 14 | The A+ and A- buttons keep the value from 10 through 28 |
| `rightClickAction` | text | menu | Right-click opens the terminal menu. If the value is `paste`, right-click on a shell reads the clipboard. A read-only screen still opens the menu. |

If the stored value is not valid JSON, the page uses the defaults.

The visible settings show `copyOnSelect`, `confirmPaste`, and `fontSize`. The
other settings can exist in local storage for browser behavior.
