# Contract: Terminal HTTP Routes

The routes belong to the WebSockets blueprint. Each route uses the error shape of the
blueprint: `{"error": "<plain reason>", "code": "<code>"}` with the HTTP status of the code.

The Flask-WTF CSRF protection covers each POST route. A POST without a valid
`X-CSRFToken` header gets 400 with the code `csrf_expired`.

## New error codes

| Code | Status | Meaning |
| - | - | - |
| `not_terminal` | 409 | The session is not a shell session or a screen command session. |
| `read_only` | 409 | The session is a screen command. It accepts no input and no resize. |
| `input_full` | 409 | The text before the first output is more than 4,096 characters. |
| `too_large` | 413 | The request holds more than 16 KiB of UTF-8 text. |
| `rate_limited` | 429 | The session received more than 60 requests in one second. |

The existing codes `not_found` (404), `not_open` (409), and `bad_request` (400) keep their
meaning.

## GET /api/websockets/sessions/{session_id}/terminal

Read the terminal bytes after one position.

Query values:

| Name | Type | Rule |
| - | - | - |
| `after` | integer | 0 or more. The default is 0. |
| `wait` | number | 0 to 25 seconds. The default is 0. |

Behavior:

1. If the history holds bytes after `after`, the route answers at once.
2. If the session ended, the route answers at once.
3. If 8 reads already wait in this portal process, the route answers at once with no data.
4. If not, the route waits for new bytes until `wait` ends.
5. Each read marks the session as read, so the idle reaper keeps the session.

Answer 200:

```json
{
  "data": "c2hvdyBhcnAK",
  "first": 0,
  "next": 9,
  "gap": 0,
  "state": "live",
  "reason": "",
  "input_ready": true,
  "read_only": false,
  "expires_at": "2026-10-01T09:30:00Z"
}
```

Refusals: `bad_request` for a bad `after` or `wait` value, `not_found`, and `not_terminal`.

Final states and reasons in the read answer:

| Event | `state` | `reason` |
| - | - | - |
| The operator or the reaper stops the session | `stopped` | The stop reason |
| The far side ends the connection before any output | `failed` | `The device sent no output before the Mist cloud closed the terminal. Start a new session after one minute.` |
| The device sends output, then a close frame | `finished` | The runner close reason. A shell uses `The device closed the shell.` A screen command uses `The device ended the screen command.` |
| A screen command reaches its time limit | `finished` | `The screen command reached its time limit of N seconds.` N is the total time limit of the command in the trigger table, in whole seconds. |
| The connection ends with no close frame, after output | `failed` | `The connection to the device dropped.` |

The second row is the server part of FR-019 and issue #3710. The page shows the 20-second
notice by itself. The read answer holds no notice field.

## POST /api/websockets/sessions/{session_id}/input

Send keys or pasted text to a shell session.

Body:

```json
{"data": "show arp\r"}
```

Rules:

- `data` is a text value with 1 to 16,384 bytes of UTF-8.
- The route sends the text without a change. The page already converted each line end.
- The route answers after the client sent the text to the device, or after the text went
  into the queue. The order of the requests is the order on the device.

Answer 202:

```json
{"accepted": 9, "queued": false}
```

`queued` is true when the text waits for the first output.

Refusals: `bad_request`, `not_found`, `not_terminal`, `read_only`, `not_open`,
`input_full`, `too_large`, and `rate_limited`.

## POST /api/websockets/sessions/{session_id}/resize

Send the terminal size to a shell session.

Body:

```json
{"cols": 120, "rows": 40}
```

Rules:

- `cols` is an integer from 20 to 500.
- `rows` is an integer from 5 to 200.
- A screen command always uses 80 columns and 40 rows.
- The page does not send a resize request for a screen command.
- If a resize request reaches a screen command, the route returns `read_only`.

Answer 202:

```json
{"cols": 120, "rows": 40}
```

Refusals: `bad_request`, `not_found`, `not_terminal`, `read_only`, `not_open`, and
`rate_limited`.

## Removed body shape

The input route no longer accepts `{"line": ...}` or `{"key": ...}`. A request with that
shape gets `bad_request`, because the `data` field is missing.

## Session payload

The session payload of the list route and the start route gets one more field.

| Field | Type | Meaning |
| - | - | - |
| `terminal` | boolean | True for a shell session and a screen command session |

The page uses this field to show the terminal panel instead of the message list.
The terminal read route tells the page whether the session is read-only.

No answer of these routes holds the shell address, the API token, or a cookie (FR-048).
The browser journey `test_review_fr048_page_gets_no_shell_address` scans each answer of a
shell session for them.

## Log rule

The routes log the session identifier, the byte count, and the result code. They never log
the text of a request or the bytes of an answer.
