# Contract: device_utils Migration Pattern

**Purpose**: Define the standard pattern for migrating DeviceUtilityCommands from raw API calls to `mistapi.device_utils.*`.

## Current Pattern (Raw API)

```python
# DeviceUtilityCommands._execute_device_command() pattern:
body = {"type": command_type, "node": node, ...params}
response = mistapi.api.v1.sites.devices.someFunction(apisession, site_id, device_id, body)
# Then manually poll WebSocket for result via WebSocketManager
```

## Target Pattern (device_utils)

```python
# device_utils returns UtilResponse with .ws_data, .done, .wait(), .receive()
from mistapi.device_utils import ap, ex, srx, ssr

# Example: traceroute from an AP
result = ap.traceroute(apisession, site_id, device_id, host="8.8.8.8")
result.wait(timeout=30)  # Block until done or timeout
output = result.ws_data   # List of WebSocket messages received

# Example: retrieve ARP table from a switch
result = ex.retrieveArpTable(apisession, site_id, device_id)
result.wait(timeout=30)
arp_entries = result.ws_data
```

## Device Type Routing Contract

The `DeviceUtilityCommands.DEVICE_TYPE_COMPATIBILITY_MAP` already maps commands to device types. The migration must preserve this mapping:

```python
# Router: command_name -> {device_type -> device_utils_function}
DEVICE_UTILS_DISPATCH = {
    "traceroute": {
        "ap": ap.traceroute,
        "switch": ex.traceroute,
        "srx": srx.traceroute,
        "ssr": ssr.traceroute,
    },
    "ospf_neighbors": {
        "srx": srx.retrieveOspfNeighbors,
        "ssr": ssr.retrieveOspfNeighbors,
    },
    # ... etc
}
```

## Response Handling Contract

**Current**: Raw API returns `mistapi.APIResponse` with `.data` containing the result.
**Target**: `device_utils` returns `UtilResponse` with:
- `.ws_data`: list of WebSocket messages (the actual command output)
- `.done`: bool indicating if the command completed
- `.wait(timeout)`: blocks until `.done` or timeout
- `.receive()`: gets next message (non-blocking)

**Migration Rule**: Replace `response.data` access with `result.wait(timeout=30); result.ws_data`.

## Error Handling Contract

```python
try:
    result = ex.retrieveArpTable(apisession, site_id, device_id)
    result.wait(timeout=30)
    if not result.done:
        logging.warning("Command timed out for device %s", device_id)
        return []
    return result.ws_data
except ConnectionError as error:
    logging.error("Connection failed: %s", error)
    return []
except ValueError as error:
    logging.error("Authentication failed: %s", error)
    return []
```
