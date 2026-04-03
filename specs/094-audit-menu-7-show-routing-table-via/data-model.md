# Data Model: Audit Menu #7 — Show Routing Table via WebSocket

**Feature**: 094-audit-menu-7-show-routing-table-via
**Date**: 2025-07-24
**Source**: `MistHelper.py` lines 17095–18723 (`RoutingUtils` class)

## Entities

### 1. RouteEntry

A parsed routing table record extracted from raw device output by the parser pipeline.

```text
RouteEntry (dict):
  destination    : str     # Route prefix or "default" (always present)
  next_hop       : str     # Next-hop IP address or gateway (may be empty)
  interface      : str     # Egress interface name (may be empty)
  protocol       : str     # Source protocol: BGP, OSPF, STATIC, DIRECT, etc. (may be empty)
  metric         : str     # Route metric / cost (may be empty)
  admin_distance : str     # Administrative distance (may be empty)
  table          : str     # Routing table name, e.g., "inet.0" (Juniper only, may be empty)
  active         : bool    # True if route is active (Juniper ">" marker; default: False)
```

**Produced by**: `_parse_routing_table()`, `_parse_standard_route_line()`, `_parse_protocol_route_line()`, `_parse_tabular_route_line()`, `_normalize_json_route_entry()`, `_parse_juniper_routing()`

**Consumed by**: `_display_routing_summary()`, `_display_routing_details()`

**Invariants**:
- `destination` is never `None` or empty; defaults to `"default"` for wildcard routes
- All string fields default to `""` (empty string) when not parsed
- `active` defaults to `False`; only set to `True` by the Juniper parser
- Returned as a plain `dict`, not a dataclass (matches existing codebase pattern)

**Validation rules**: None at the entity level. Parsing methods return `None` for unparseable lines, and callers skip `None` entries.

### 2. QueryParameters

User-provided filter parameters collected by `_get_routing_table_params()` and sent as the HTTP POST body to the Mist show_route API.

```text
QueryParameters (dict):
  prefix   : str     # CIDR prefix filter, e.g., "192.168.1.0/24" (optional key)
  protocol : str     # Protocol filter (always present, default: "any")
  vrf      : str     # VRF instance name (optional key)
  neighbor : str     # BGP neighbor IP address (optional key)
  route    : str     # Route direction: "received" or "advertised" (optional, requires neighbor)
  node     : str     # HA node: "node0" or "node1" (optional key)
```

**Produced by**: `_get_routing_table_params()`

**Consumed by**: `_execute_routing_table_command()`, `_display_routing_summary()` (for context), `_display_routing_table_output()`

**Validation rules** (to be implemented):
- `prefix`: Validated via `ipaddress.ip_network(value, strict=False)`; warn-and-confirm on failure
- `protocol`: Must be in `{"bgp", "ospf", "static", "direct", "evpn", "any"}`; unrecognized input triggers user notification before defaulting to `"any"`
- `vrf`: No validation (free-form string)
- `neighbor`: No validation (free-form IP string)
- `route`: Must be in `{"received", "advertised"}` or omitted
- `node`: Must be in `{"node0", "node1"}` or omitted

**Key behavior**: Optional keys are only added to the dict when the user provides non-empty input. The `protocol` key is always present.

### 3. WebSocketSession

The connection lifecycle state managed across the 5-step orchestrator pipeline.

```text
WebSocketSession (implicit — spread across local variables in execute_show_routing_table):
  websocket_manager : WebSocketManager | None  # Connection instance (initially None)
  site_id           : str                      # Selected site UUID
  device_id         : str                      # Selected device UUID
  device_info       : dict | None              # Device metadata from API
  command_channel   : str                      # "/sites/{site_id}/devices/{device_id}/cmd"
  session_id        : str                      # Correlation ID from API POST response
  timeout_seconds   : int                      # Result wait timeout (hardcoded: 60)
```

**Note**: This is not a formal class — it represents the implicit state threaded through the orchestrator's local variables. Documenting it here clarifies the lifecycle and cleanup responsibilities.

**Lifecycle states**:

```text
  [start] -> site/device selected -> websocket connected -> params collected
          -> command sent (session_id obtained) -> results received -> [cleanup]
          
  Any step can fail, at which point:
  - Steps 1-2 failures: return early (no cleanup needed if WS not connected)
  - Step 2 failure after connect: _connect_websocket must disconnect internally
  - Steps 3-5 failures: caught by orchestrator's except block
  - Always: finally block calls _cleanup_websocket(websocket_manager)
```

### 4. CommandResult

The WebSocket response received after sending a show_route command.

```text
CommandResult (dict — from WebSocketManager.wait_for_command_result):
  session  : str     # Correlation session ID (matches the one from API POST)
  raw      : str     # Primary output field — raw routing table text
  Output   : str     # Alternative/additional output field (may duplicate raw)
  [other]  : Any     # Additional fields vary by device type
```

**Produced by**: `WebSocketManager.wait_for_command_result()`

**Consumed by**: `_display_routing_table_output()`

**Key behavior**:
- `raw` is the primary field checked first for routing table data
- `Output` is checked as a secondary source if it differs from `raw`
- If both are empty, the user sees "No routing table data received"
- Returns `None` on timeout (60 seconds)

## Relationships

```text
QueryParameters --[sent to]--> Mist show_route API --[returns]--> session_id
session_id --[correlates]--> CommandResult (via WebSocket)
CommandResult.raw --[parsed by]--> _parse_routing_table() --[produces]--> list[RouteEntry]
list[RouteEntry] --[displayed by]--> _display_routing_summary() + _display_routing_details()
QueryParameters --[context for]--> _display_routing_summary() (shows applied filters)
```

## State Transitions

### Parser Dispatch (in _parse_routing_table)

```text
raw_output
  |
  +-- empty/None --------------------------> return []
  |
  +-- contains "inet.0:" / "inet6.0:" -----> _parse_juniper_routing()
  |   or "Limit/Threshold:"
  |
  +-- (per line):
      |
      +-- empty / starts with # / "show" --> skip
      |
      +-- contains " via " / " dev " / -----> _parse_standard_route_line()
      |   " proto "
      |
      +-- contains protocol keyword --------> _parse_protocol_route_line()
      |   (bgp/ospf/static/direct/connected)
      |
      +-- starts with { and ends with } ----> json.loads() + _normalize_json_route_entry()
      |
      +-- 3+ space-separated fields --------> _parse_tabular_route_line()
      |
      +-- (no match) -----------------------> skip
```

### Orchestrator Pipeline (in execute_show_routing_table)

```text
[entry] --> _select_routing_table_device()
              |-- fail: return (no cleanup)
              |-- ok: site_id, device_id, device_info
         --> _connect_websocket()
              |-- fail: return (internally disconnects if needed)
              |-- ok: websocket_manager
         --> _get_routing_table_params()
              |-- always succeeds: payload dict
         --> _execute_routing_table_command()
              |-- fail: disconnect, return
              |-- ok: session_id
         --> _process_routing_table_results()
              |-- timeout: print timeout message
              |-- ok: _display_routing_table_output()
         --> [finally] _cleanup_websocket()
```
