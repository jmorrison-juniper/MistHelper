# Data Model: Audit Menu #5 — Show MAC Table via WebSocket

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## Overview

This document defines the entities, states, and relationships involved in the
`show_mac_table` WebSocket command lifecycle. Since this is an audit of existing
code (no new persistence), the model describes runtime objects and their state
transitions rather than database tables.

---

## Entities

### E-01: WebSocketManager

The connection manager for Mist WebSocket streaming. Owns the WebSocket
connection, channel subscriptions, and command result storage.

| Field | Type | Description |
|-------|------|-------------|
| `mist_session` | `Any` (mistapi session) | Authenticated Mist API session; provides `host`, `apitoken`, `mist_post()` |
| `mist_host` | `str` | Mist API hostname (e.g., `api.mist.com`) |
| `websocket_url` | `str` | Derived WebSocket URL (`wss://api-ws.mist.com/api-ws/v1/stream`) |
| `websocket_connection` | `WebSocketApp \| None` | Active WebSocket connection or None |
| `websocket_thread` | `Thread` | Background thread running `run_forever()` |
| `connected` | `bool` | True when WebSocket handshake complete |
| `subscribed_channels` | `set[str]` | Channels with subscribe message sent |
| `confirmed_subscriptions` | `set[str]` | Channels with server acknowledgment received |
| `command_results` | `dict[str, list[dict]]` | Session ID → list of message payloads |
| `results_lock` | `threading.Lock` | Thread-safe access to `command_results` |

**Validation Rules**:
- `mist_host` must not be None (asserted in `__init__`)
- `mist_session` must provide `apitoken` attribute or `MIST_APITOKEN` env var
- `websocket_url` must use `wss://` scheme

**Key Methods**:
- `connect() → bool` — Establish authenticated WebSocket connection
- `subscribe_to_channel(channel_path) → bool` — Send subscription message
- `wait_for_subscription_confirmation(channel_path, timeout) → bool` — Poll for server ack
- `wait_for_command_result(session_id, timeout, activity_timeout) → dict | None` — Collect streaming results
- `disconnect() → None` — Close connection and clear state

---

### E-02: CommandSession

Represents a single show_mac_table command execution. Not a formal class
in the code — it's the logical entity formed by the combination of a REST
POST response and the corresponding WebSocket stream.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | UUID returned from REST POST; correlates WebSocket messages |
| `site_id` | `str` | Mist site UUID selected by operator |
| `device_id` | `str` | Mist switch device UUID selected by operator |
| `command_channel` | `str` | WebSocket channel path (`/sites/{site_id}/devices/{device_id}/cmd`) |
| `status_code` | `int` | HTTP status from REST POST |
| `result` | `dict \| None` | Collected command output or None on timeout |

**Validation Rules**:
- `session_id` must be a non-empty string extracted from `response.data.get("session")`
- `site_id` and `device_id` must be valid UUIDs (enforced by PromptUtils selection)
- `status_code` must be 200 for the command to proceed

---

### E-03: MACTableResult

The output of a successful show_mac_table command. This is the structured
data returned by `wait_for_command_result()` after message collection.

| Field | Type | Description |
|-------|------|-------------|
| `raw` | `str` | Raw text output from the device (Junos "ethernet switching table" format) |
| `Output` | `str` | Alternative output field (may duplicate `raw`) |
| `session` | `str` | Echo of the session ID |
| `[other fields]` | `Any` | Device-specific metadata fields |

**States**:
- **Complete with data**: `raw` is non-empty, contains "ethernet switching table : N entries" where N > 0
- **Empty table**: Contains "ethernet switching table : 0 entries" — valid result, zero learned MACs
- **No output**: Both `raw` and `Output` are empty — indicates command failure or unsupported device

---

## State Transitions

### WebSocket Command Lifecycle

```
┌───────────┐
│   IDLE    │  (no WebSocket connection)
└─────┬─────┘
      │ connect()
      ▼
┌───────────┐
│ CONNECTED │  (WebSocket handshake complete, connected=True)
└─────┬─────┘
      │ subscribe_to_channel()
      ▼
┌───────────┐
│SUBSCRIBED │  (subscribe message sent, in subscribed_channels)
└─────┬─────┘
      │ wait_for_subscription_confirmation()
      ▼
┌───────────┐
│ CONFIRMED │  (server ack received, in confirmed_subscriptions)
└─────┬─────┘
      │ REST POST → session_id
      ▼
┌───────────┐
│  WAITING  │  (wait_for_command_result polling loop)
└─────┬─────┘
      │ completion detected OR timeout
      ▼
┌───────────┐
│ COMPLETE  │  (result returned, WebSocket still open)
└─────┬─────┘
      │ disconnect()
      ▼
┌───────────┐
│   IDLE    │  (connection closed, state cleared)
└───────────┘
```

### Failure Transitions (any state → cleanup)

| From State | Failure | Error Message | Cleanup |
|------------|---------|---------------|---------|
| IDLE | No site selected | "No site selected. Operation cancelled." | None needed |
| IDLE | No device selected | "No switch device selected." | None needed |
| IDLE → CONNECTED | Connection fails | "Failed to establish WebSocket connection" | None (connect returns False) |
| CONNECTED | Subscribe fails | "Failed to subscribe to device command channel" | `disconnect()` |
| CONFIRMED | REST POST non-200 | "Failed to issue show MAC table command: {status}" | `disconnect()` |
| CONFIRMED | No session ID | "No session ID returned from show MAC table command" | `disconnect()` |
| WAITING | Timeout (60s) | "Timeout waiting for MAC table results" | `disconnect()` |
| WAITING | Circuit breaker | (returns partial results) | `disconnect()` |
| Any | Exception | "WebSocket show MAC table operation failed: {error}" | `disconnect()` via `finally` |
| Any | KeyboardInterrupt | (propagates) | `disconnect()` via `finally` |

---

## Completion Detection Model

The `wait_for_command_result` method uses a priority-ordered set of
heuristics to determine when the MAC table output is complete:

| Priority | Heuristic | Condition | Confidence |
|----------|-----------|-----------|------------|
| 1 | Generic indicators | Any of: "command completed", "operation complete", "finished" | High |
| 2 | Switch indicators | Any of: "learning table", "fdb entries", etc. (skipped for MAC tables) | Medium |
| 3 | Repeated messages | Last 5 messages are identical and non-empty | High |
| 4 | MAC idle timeout | 5+ seconds idle AND 10+ messages AND 10+ entries | Medium |
| 5 | Generic activity timeout | `activity_timeout_seconds` idle with collected data | Low |
| 6 | Absolute timeout | `timeout_seconds` exceeded | N/A (safety net) |
| 7 | Circuit breaker | 10,000 iterations exceeded | N/A (emergency) |

**Post-audit changes** (from research.md):
- Priority 4 idle timeout raised from 3s → 5s (via `activity_timeout_seconds=5`)
- Priority 5 activity timeout raised from 2s → 5s (via parameter)

---

## Relationships

```
Site (1) ──────────── (N) Switch Device
                              │
                              │ selected by operator
                              ▼
WebSocketManager (1) ── (1) CommandSession
        │                       │
        │ manages               │ produces
        │                       ▼
        └──────────── (N) WebSocket Messages → (1) MACTableResult
```

- One `WebSocketManager` per `show_mac_table` invocation
- One `CommandSession` per invocation (identified by `session_id`)
- Multiple WebSocket messages aggregate into one `MACTableResult`
- A Site contains many Switch Devices; operator selects one
