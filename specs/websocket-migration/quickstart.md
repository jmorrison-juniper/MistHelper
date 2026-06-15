# Quickstart: WebSocket Migration

## Prerequisites

- `mistapi >= 0.61.0` (check: `python -c "import mistapi; print(mistapi.__version__)"`)
- Authenticated Mist API session
- Working device for testing (any AP, switch, or gateway)

## Migrating a Single Menu Operation

### Step 1: Capture baseline output

Run the operation with current `WebSocketManager`, save output to file:
```bash
python MistHelper.py --menu 102 > baseline_102.txt 2>&1
```

### Step 2: Swap to adapter

In the menu operation code, replace:
```python
websocket_manager = WebSocketManager(apisession)
websocket_manager.connect()
websocket_manager.subscribe_to_channel(f"/sites/{site_id}/devices/{device_id}/cmd")
# ... POST command ...
result = websocket_manager.wait_for_command_result(session_id, timeout=60)
websocket_manager.disconnect()
```

With:
```python
from src.websocket.adapter import MistWebSocketAdapter

ws_adapter = MistWebSocketAdapter(apisession, site_id, device_id)
ws_adapter.connect()
# ... POST command (unchanged) ...
result = ws_adapter.send_and_wait(session_id, timeout=60)
ws_adapter.disconnect()
```

### Step 3: Verify

Run same operation, diff output:
```bash
python MistHelper.py --menu 102 > migrated_102.txt 2>&1
diff baseline_102.txt migrated_102.txt
```

No diff = migration successful for that operation.

### Step 4: Repeat for each operation

One PR per operation or small batch. Never migrate all 22 at once.

## Decision: Which Spec Handles Which Operation?

Before migrating an operation, check:
1. Does `mistapi.device_utils` have a helper for this command? → `device-utils-adoption` spec handles it
2. No `device_utils` helper? → This spec handles it via `MistWebSocketAdapter`

## Rollback

Revert the import to `WebSocketManager`. No database changes, no config changes, no side effects.
