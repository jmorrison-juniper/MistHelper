# Contract: WebSockets tab HTTP interface

**Feature**: [../spec.md](../spec.md) | **Blueprint**: `websockets_bp` in `src/websocket_streams/web/blueprint.py`

Every route answers with JSON, except the page route and the download route. Every POST route and every DELETE route needs the `X-CSRFToken` header. No answer holds the API token, a channel path, or a Mist WebSocket address.

## Common error answer

```json
{"error": "Plain reason for the operator.", "code": "limit_reached"}
```

| Code | HTTP status | Meaning |
| - | - | - |
| `not_ready` | 503 | The portal holds no Mist session or no organization. |
| `bad_request` | 400 | A field failed a check. The `field` key names the field. |
| `unknown_key` | 404 | The key names no catalog entry. |
| `locked` | 403 | The flag of the safety class is off. The `flag` key names the variable. |
| `confirmation` | 403 | The typed device name does not match. |
| `limit_reached` | 429 | The live sessions reached the limit. The `live` key lists the session titles. |
| `not_found` | 404 | The session identifier names no session. |
| `not_open` | 409 | The shell is not ready for input, or the session has ended. |

## Page

### `GET /websockets`

Returns the WebSockets page. The page reads the catalog and the session list from the routes below.

## Catalog

### `GET /api/websockets/catalog`

```json
{
  "ready": true,
  "reason": null,
  "flags": {
    "changes": {"enabled": false, "variable": "PORTAL_WS_ENABLE_CHANGES"},
    "shell": {"enabled": false, "variable": "PORTAL_WS_ENABLE_SHELL"}
  },
  "limits": {"max_sessions": 5, "idle_seconds": 120, "capture_seconds": 60},
  "channels": [
    {
      "key": "site.stats.devices",
      "scope": "site",
      "name": "Device statistics",
      "description": "Live statistics for each device at the site.",
      "identifiers": [{"name": "site_id", "label": "Site", "kind": "uuid", "picker": "sites"}],
      "repeatable": null
    }
  ],
  "utilities": [
    {
      "key": "ex.ping",
      "family": "ex",
      "name": "Ping",
      "description": "Send ICMP echo requests from the switch.",
      "safety": "read",
      "locked": false,
      "output": "lines",
      "fields": [{"name": "host", "label": "Host", "kind": "host", "required": true}]
    }
  ]
}
```

## Sessions

### `GET /api/websockets/sessions`

Lists every session that the manager holds, live and ended.

```json
{"sessions": [{"session_id": "a1b2c3d4e5f6a7b8", "kind": "channel", "key": "site.stats.devices",
  "title": "Device statistics - HQ", "state": "live", "reason": "", "started_at": "2026-09-29T20:00:00Z",
  "ended_at": null, "counters": {"received": 42, "dropped": 0, "shortened": 0, "bytes": 81234},
  "rate_per_second": 1.4, "last_seq": 42, "live": true}],
  "limits": {"max_sessions": 5, "live_count": 1}}
```

### `POST /api/websockets/sessions`

Starts a session. The body holds only keys and values. It never holds a path.

```json
{"kind": "utility", "key": "ex.ping",
 "targets": {"site_id": "<uuid>", "device_id": "<uuid>"},
 "parameters": {"host": "8.8.8.8", "count": 5},
 "confirmation": null}
```

Returns 201 with the session object from the list route. The server checks the whole request before it sends a request to Mist.

### `GET /api/websockets/sessions/<session_id>/messages?after=<seq>&limit=<n>`

Returns the messages with a sequence number above `after`. The default limit is 200 and the maximum is 500. The route marks the session as read.

```json
{"session": {"session_id": "a1b2c3d4e5f6a7b8", "state": "live"},
 "messages": [{"seq": 43, "received_at": "2026-09-29T20:00:01Z", "kind": "json",
   "content": {"mac": "5c5b35000001"}, "summary": null, "size": 812, "shortened": false}],
 "next_after": 43, "first_seq": 1, "gap": false}
```

`gap` is true when the buffer dropped messages that the page did not read.

### `POST /api/websockets/sessions/<session_id>/stop`

Asks the session to stop. Returns 202 with the session object. A second stop request returns the same answer.

### `POST /api/websockets/sessions/<session_id>/input`

Shell sessions only. The body holds one of two forms:

```json
{"line": "show version"}
{"key": "interrupt"}
```

The keys are `interrupt`, `tab`, `space`, `q`, and `enter`. A line holds 512 characters or fewer, with no control characters. Returns 202.

### `DELETE /api/websockets/sessions/<session_id>`

Removes an ended session from the list. Returns 409 for a live session.

### `GET /api/websockets/sessions/<session_id>/download`

Returns the buffer as JSON Lines, with the `application/x-ndjson` type. The file name holds the catalog key and the start time.

## Pickers

Each picker answers with this form:

```json
{"rows": [{"id": "<uuid>", "label": "HQ-SW-01", "family": "ex", "detail": "EX4100-48P"}],
 "total_count": 1, "reason": null}
```

| Route | Rows |
| - | - |
| `GET /api/websockets/sites/<site_id>/devices` | The devices at the site, with a family for each device |
| `GET /api/websockets/sites/<site_id>/maps` | The maps at the site |
| `GET /api/websockets/sites/<site_id>/assets` | The BLE assets at the site |
| `GET /api/websockets/sites/<site_id>/maps/<map_id>/sdkclients` | The SDK clients on the map |
| `GET /api/websockets/mxedges?site_id=<uuid>` | The Mist Edges of the organization, or of one site |

The site picker is `GET /api/operations/sites`, which already exists.
