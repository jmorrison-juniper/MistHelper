# Contracts: Audit Menu #7 — Show Routing Table via WebSocket

**Feature**: 094-audit-menu-7-show-routing-table-via
**Date**: 2025-07-24

> Menu #7 is an interactive CLI command with no public API. These contracts document the internal integration boundaries between the routing table pipeline and the Mist platform.

## Contract 1: Mist show_route REST API

**Used by**: `RoutingUtils._execute_routing_table_command()` (line 18386)

### Request

```text
POST https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_route

Headers:
  Authorization: Token {mist_apitoken}
  Content-Type: application/json

Body (all fields optional except protocol):
  {
    "prefix": "10.0.0.0/8",
    "protocol": "any",
    "vrf": "management",
    "neighbor": "192.168.1.1",
    "route": "received",
    "node": "node0"
  }
```

### Response

```text
Success (200):
  { "session": "abc123-def456-ghi789" }

Errors:
  400 Bad Request     — Invalid parameters (malformed prefix, unknown protocol)
  401 Unauthorized    — Invalid or expired API token
  404 Not Found       — Device or site not found
  500 Internal Error  — Device unreachable or backend failure
```

### Postconditions

- On 200: `session` field is a string UUID used to correlate WebSocket result messages
- On error: No session is created; no WebSocket messages will be received
- The session has an implicit server-side timeout (device-dependent, typically 30–120 seconds)

---

## Contract 2: WebSocket Command Channel

**Used by**: `RoutingUtils._connect_websocket()` (line 18018), `WebSocketManager` (line 3961)

### Subscription

```text
Channel: /sites/{site_id}/devices/{device_id}/cmd

Subscribe message (sent by client):
  { "subscribe": "/sites/{site_id}/devices/{device_id}/cmd" }

Confirmation (received from server):
  { "event": "channel_subscribed", "channel": "/sites/{site_id}/devices/{device_id}/cmd" }
```

### Command Result Messages

```text
Result message (received from server after show_route command executes):
  {
    "event": "data",
    "channel": "/sites/{site_id}/devices/{device_id}/cmd",
    "data": {
      "session": "abc123-def456-ghi789",
      "raw": "<routing table text output>",
      "Output": "<alternative/additional output>"
    }
  }
```

### Field Semantics

| Field | Description |
|-------|-------------|
| `session` | Matches the session ID from the REST API POST response |
| `raw` | Primary output — raw routing table text from the device CLI |
| `Output` | Secondary output — may contain the same data or additional formatted output |

### Timing

- Subscription confirmation: Typically arrives within 0.5–2 seconds
- Command result: Depends on device response time; timeout at 60 seconds
- Multiple messages may arrive for large routing tables (streaming)

---

## Contract 3: Parser Pipeline

**Used by**: `RoutingUtils._parse_routing_table()` (line 17273)

### Input

```text
raw_output: str
  - Raw text from CommandResult.raw or CommandResult.Output
  - May contain multiple lines separated by \n
  - Format varies by device type and vendor
```

### Output

```text
list[RouteEntry]: list of dicts
  - Each dict has keys: destination, next_hop, interface, protocol, metric, admin_distance
  - Juniper entries additionally have: table, active
  - Empty list on empty/None input
  - Malformed lines produce no entry (silently skipped)
```

### Parser Dispatch Rules

| Priority | Detection Pattern | Parser Method |
|----------|------------------|---------------|
| 1 (highest) | Input contains "inet.0:", "inet6.0:", or "Limit/Threshold:" | `_parse_juniper_routing()` |
| 2 | Line contains " via ", " dev ", or " proto " | `_parse_standard_route_line()` |
| 3 | Line contains protocol keyword (bgp, ospf, static, direct, connected) | `_parse_protocol_route_line()` |
| 4 | Line is valid single-line JSON object | `_normalize_json_route_entry()` |
| 5 (lowest) | Line has 3+ space-separated fields | `_parse_tabular_route_line()` |

### Invariants

- **Empty safety**: `_parse_routing_table(None)` and `_parse_routing_table("")` both return `[]`
- **Exception safety**: No parser method raises exceptions to the caller; all catch internally
- **Ordering**: Lines are processed top-to-bottom; the first matching pattern wins
- **Juniper override**: Juniper detection is checked once on the full input before per-line parsing
