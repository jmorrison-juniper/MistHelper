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
| `cols` | integer | 20 to 500. The start value is 80. |
| `rows` | integer | 5 to 200. The start value is 24. |
| `expires_mono` | float | The start time plus the session life limit |
| `expires_at` | text | The same time in UTC, for the page |

The session states do not change. A terminal session moves through these states.

```text
connecting --(socket open)--> live --(first output)--> live and input_ready
live --(operator stop or reaper)--> stopping --> stopped
live --(device closes, for example after exit)--> finished
connecting or live --(error)--> failed
```

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
| `times` | queue of floats | The request times of the newest second |

Rules:

- One request holds 16 KiB of UTF-8 text at most. A larger request gets `too_large` (413).
- One session accepts 60 requests each second. More requests get `rate_limited` (429).
- Before the first output, the text goes into `pending`. If `pending` then holds more than
  4,096 characters, the request gets `not_ready` (409), and the text does not go into
  `pending`.
- At the first output, the queue sends the pending text in order. Then it sends each new
  request at once.
- A session that is not live gets `not_open` (409).

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
| `fontSize` | integer | 14 | 10 to 24 |

If the stored value is not valid JSON, the page uses the defaults.
