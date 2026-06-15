# Data Model: WebSocket Migration

## Entities

### MistWebSocketAdapter

Wraps `mistapi.websockets.sites.DeviceCmdEvents` to match `WebSocketManager` interface.

| Field | Type | Purpose |
| - | - | - |
| `mist_session` | `APISession` | Authenticated Mist API session |
| `site_id` | `str` | Current site UUID |
| `device_id` | `str` | Target device UUID |
| `_ws_client` | `DeviceCmdEvents \| None` | SDK WebSocket client instance |
| `_connected` | `bool` | Connection state |
| `_logger` | `logging.Logger` | Module logger |

### Message Flow

```
Menu Operation
  │
  ├─ (current) WebSocketManager.connect() → subscribe → REST POST → wait_for_result → disconnect
  │
  └─ (new)     MistWebSocketAdapter.connect() → REST POST → receive() generator → disconnect
                    │                                            │
                    └─ DeviceCmdEvents(session, site, [device])  └─ yields dict messages
                       .connect(run_in_background=True)              filtered by session_id
```

### Result Format (unchanged)

Menu operations expect results as:
```python
{
    "session_id": "abc-123",
    "status": "completed",  # or "failed", "timeout"
    "data": { ... },        # command output payload
    "raw": [ ... ]          # raw message list (for debugging)
}
```

The adapter collects messages from `receive()`, matches by `session_id` field in the message, and assembles the same result dict.

## State Transitions

```
DISCONNECTED → connect() → CONNECTING → ready==True → CONNECTED
CONNECTED → disconnect() → DISCONNECTED
CONNECTED → error/timeout → DISCONNECTED (auto_reconnect may retry)
```

## Validation Rules

- `site_id` must be valid UUID (validated by SDK constructor)
- `device_id` must be valid UUID (validated by SDK constructor)
- `mist_session` must have valid `apitoken` (SDK raises on connect)
- `mistapi >= 0.61.0` checked at import time
