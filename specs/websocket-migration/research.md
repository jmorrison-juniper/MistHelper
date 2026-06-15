# Research: WebSocket Migration

## R1: `mistapi.websockets.sites.DeviceCmdEvents` API Surface

**Decision**: Use `DeviceCmdEvents` as the sole SDK entry point for device command WebSocket streams.

**Rationale**: It subscribes to `/sites/{site_id}/devices/{device_id}/cmd` channels — exactly what custom `WebSocketManager` does manually. The SDK handles authentication, ping/pong keepalive, auto-reconnect, bounded queues, and thread-safe operation.

**Key API**:
- Constructor: `DeviceCmdEvents(mist_session, site_id, device_ids, auto_reconnect=True, queue_maxsize=100)`
- `connect(run_in_background=True)` → starts WS thread
- `receive()` → blocking generator yielding `dict` messages (cannot coexist with `on_message` callback)
- `disconnect()` → clean shutdown, sets `_finished` event
- `ready` → property, True when connected and subscribed

**Alternatives considered**:
- Raw `_MistWebsocket` base class: More flexibility but no channel auto-construction. Unnecessary complexity.
- Keep `websocket-client` with custom code: Defeats the purpose — we'd still maintain 3K lines.

## R2: Current `WebSocketManager` Interface

The adapter must match this interface consumed by menu operations:

| Method | Purpose |
| - | - |
| `connect()` → `bool` | Establish WS connection, return success |
| `subscribe_to_channel(channel)` | Subscribe to site/device/cmd channel |
| `send_command(site_id, device_id, command, timeout)` → `dict` | Send command, wait for result |
| `wait_for_command_result(session_id, timeout)` → `dict` | Block until result arrives for session |
| `disconnect()` | Clean shutdown |

Menu operations call: `connect()` → `subscribe_to_channel()` → POST command via REST API → `wait_for_command_result()` → process result → `disconnect()`.

The SDK simplifies this: constructor auto-subscribes, `receive()` yields results. The adapter hides this difference.

## R3: Overlap with `device-utils-adoption` Spec

`device-utils-adoption` covers the same menu operations (102-123) but via `mistapi.device_utils` which internally uses `UtilResponse` for automatic WebSocket polling. Operations successfully migrated to `device_utils` do NOT need direct WS migration.

**Decision**: This spec handles operations that `device_utils` does NOT cover (e.g., operations without a `device_utils` helper, custom show commands, service ping discovery). The cleanup phase (removing `src/websocket/`) depends on BOTH specs being complete.

**Migration decision per operation**: Check if `device_utils` has a matching helper first. If yes → `device-utils-adoption` handles it. If no → this spec handles it via the adapter.

## R4: Binary Frame Handling

**Decision**: `mistapi.websockets` (v0.61.1+) handles binary frames internally and delivers parsed dicts via `receive()`. No special handling needed in the adapter.

**Rationale**: Verified in SDK source — `_MistWebsocket.on_message` handles both text and binary frames, deserializes to dict before queuing.

## R5: Thread Safety

**Decision**: SDK uses internal locks (`_connected` event, `_finished` event, `_queue` with `queue.Queue`) for thread safety. The adapter does NOT need its own locking beyond what the SDK provides.

**Rationale**: `receive()` is thread-safe via `queue.Queue.get()`. The adapter runs `receive()` in the calling thread (blocking) — same as current `wait_for_command_result()`.

## R6: Version Gating

**Decision**: Check `mistapi.__version__ >= "0.61.0"` at adapter import time. Raise `ImportError` with clear message if older version detected.

**Rationale**: `mistapi.websockets` module doesn't exist before 0.61.0. Failing at import time prevents confusing runtime errors.
