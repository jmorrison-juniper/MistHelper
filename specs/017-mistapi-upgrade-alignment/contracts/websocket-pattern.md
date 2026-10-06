# Contract: WebSocket Migration Pattern

**Purpose**: Define the standard pattern for migrating from raw `websocket.WebSocketApp` to `mistapi.websockets.*`.

## Owned Transport Exception

MistHelper uses `mistapi` for every Mist REST request.
MistHelper MAY own the WebSocket transport only while the matching SDK path
loses the first output or a split control sequence.
The contract test `tests/contract/websocket_streams/test_ws_sdk_contract.py`
proves this limitation and pins the four private `APISession` fields that the
owned transport reads: `_apitoken`, `_apitoken_index`, `_session`, and
`_cloud_uri`.
When a mistapi release preserves the first output and split control sequences,
replace the owned transport with the matching SDK WebSocket path.

## Current Pattern (Raw WebSocket)

```python
# WebSocketManager.__init__():
self.websocket_connection = websocket.WebSocketApp(
    self.websocket_url,
    header=headers,
    on_message=self._on_message,
    on_error=self._on_error,
    on_close=self._on_close,
    on_open=self._on_open,
)
self.websocket_thread = threading.Thread(target=connection.run_forever, daemon=True)
self.websocket_thread.start()

# Manual subscription:
self.websocket_connection.send(json.dumps(subscription_message))
```

## Target Pattern (mistapi.websockets)

```python
from mistapi.websockets.sites import DeviceCmdEvents, PcapEvents

# Device command events channel:
channel = DeviceCmdEvents(
    apisession,
    site_id,
    on_message=callback_function,
    auto_reconnect=True,
    queue_maxsize=1000,
)
channel.start()
# ... use channel ...
channel.stop()
```

## Channel Mapping

| Current Subscription | Target Channel Class |
| - | - |
| `/sites/{site_id}/device_cmd` | `sites.DeviceCmdEvents` |
| `/sites/{site_id}/pcap` | `sites.PcapEvents` |
| `/sites/{site_id}/stats` | `sites.DeviceStatsEvents` |
| `/sites/{site_id}/events` | `sites.DeviceEvents` |

## Migration Rules

1. Replace `websocket.WebSocketApp(url, header=...)` with channel class constructor
2. Replace manual `send(json.dumps(subscription))` with channel class `.start()`
3. Replace `on_message` callback parsing with channel's built-in message queue
4. Add `auto_reconnect=True` for production reliability
5. Add `queue_maxsize=1000` to prevent memory leaks from unbounded queues
6. Replace `threading.Thread(target=run_forever)` with channel's internal threading
