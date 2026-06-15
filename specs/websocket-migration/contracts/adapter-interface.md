# Adapter Interface Contract

## `MistWebSocketAdapter`

### Constructor

```python
MistWebSocketAdapter(
    mist_session: APISession,
    site_id: str,
    device_id: str,
    timeout: int = 60,
    auto_reconnect: bool = True,
)
```

### Methods

#### `connect() -> bool`
Establish WebSocket connection via `DeviceCmdEvents`.
Returns `True` on success, `False` on failure.
Logs `info` before, `debug` after.

#### `send_and_wait(session_id: str, timeout: int | None = None) -> dict`
Wait for command result matching `session_id` from the `receive()` generator.
The REST POST that triggers the command is done by the caller (menu operation) — the adapter only collects results.

Returns:
```python
{
    "session_id": str,
    "status": "completed" | "failed" | "timeout",
    "data": dict,         # Command output payload
    "raw": list[dict],    # All messages for this session_id
}
```

Raises: `TimeoutError` if no result within timeout.

#### `disconnect() -> None`
Clean shutdown. Idempotent — safe to call multiple times.

### Drop-In Compatibility

Menu operations currently do:
```python
ws = WebSocketManager(apisession)
ws.connect()
ws.subscribe_to_channel(f"/sites/{site_id}/devices/{device_id}/cmd")
# ... POST command via REST API, get session_id ...
result = ws.wait_for_command_result(session_id, timeout=60)
ws.disconnect()
```

With adapter:
```python
ws = MistWebSocketAdapter(apisession, site_id, device_id)
ws.connect()
# ... POST command via REST API, get session_id ...
result = ws.send_and_wait(session_id, timeout=60)
ws.disconnect()
```

The `subscribe_to_channel()` call is eliminated — `DeviceCmdEvents` auto-subscribes in its constructor.
