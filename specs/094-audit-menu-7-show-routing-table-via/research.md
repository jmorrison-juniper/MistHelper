# Research: Audit Menu #7 — Show Routing Table via WebSocket

**Feature**: 094-audit-menu-7-show-routing-table-via
**Date**: 2025-07-24
**Status**: Complete

## Research Summary

Five research tasks were investigated to resolve unknowns from the Technical Context and Constitution Check. All NEEDS CLARIFICATION items have been resolved.

---

## Task 1: Test Pattern for Monolith Pure Functions (R1 Pattern)

### Question

How should tests be structured for methods inside the 18,700-line `MistHelper.py` monolith, given that importing the module triggers side effects?

### Findings

The project has an established R1 pattern across all existing unit tests:

- **`test_offline_device_reporter.py`**: Duplicates `process_devices()` and `display_summary()` as standalone functions. Tests run without any MistHelper import.
- **`test_data_processing.py`**: Duplicates `validate_threshold()` and data processing functions. Uses class-based test organization.
- **`test_telemetry.py`**: Duplicates `TelemetryEmitter` class entirely. Tests file I/O without module-level dependencies.

**Import side effects in MistHelper.py**:
- Module-level `apisession` global variable (requires mistapi)
- Module-level `logging.basicConfig()` configuration
- Global state for `is_debug_mode()` function
- Environment variable reads at import time

### Decision

Use R1 pattern: duplicate all pure functions (`_parse_routing_table`, `_parse_standard_route_line`, `_parse_protocol_route_line`, `_parse_tabular_route_line`, `_normalize_json_route_entry`, `_display_routing_summary`) into the test file as standalone functions. For methods that interact with external state (WebSocket, API), test the logic boundaries using mock objects without importing from MistHelper.

### Alternatives Rejected

| Alternative | Why Rejected |
|-------------|-------------|
| Direct import with mock | MistHelper.py executes module-level code on import; mocking all side effects is fragile and would break when new globals are added |
| `importlib` selective import | Static methods on classes cannot be selectively imported; method signatures depend on class context |
| Refactor to modules first | Out of scope for this audit; test coverage must exist before safe refactoring is possible |

---

## Task 2: WebSocket Subscription Confirmation Pattern

### Question

How should the hardcoded `time.sleep(1)` subscription wait (line 18044) be replaced, and does the codebase already have the needed infrastructure?

### Findings

**`WebSocketManager.wait_for_subscription_confirmation()`** (line 4077) already exists and implements the correct pattern:

```python
def wait_for_subscription_confirmation(self, channel_path, timeout_seconds=10):
    # Polls confirmed_subscriptions set at 0.1s intervals
    # Returns True when channel appears in set, False on timeout
```

**Subscription confirmation flow**:
1. `subscribe_to_channel(channel)` sends `{"subscribe": channel}` to server
2. Server responds with `{"event": "channel_subscribed", "channel": "..."}`
3. `_on_message()` handler (line 4698) detects the event and adds channel to `confirmed_subscriptions` set
4. `wait_for_subscription_confirmation()` polls the set until found or timeout

**Current broken flow in `_connect_websocket`** (line 18018):
1. `subscribe_to_channel()` sends the subscription request
2. `time.sleep(1)` waits a fixed 1 second
3. No check that subscription was actually confirmed
4. Proceeds to send command (may fail if subscription not yet active)

### Decision

Replace `time.sleep(1)` with `wait_for_subscription_confirmation(command_channel, timeout_seconds=5)`. Use 5-second timeout (not the 10-second default) since subscription confirmation is typically fast. If confirmation fails, return `None` with an error message.

### Alternatives Rejected

| Alternative | Why Rejected |
|-------------|-------------|
| Increase sleep to 3s | Still a race condition; masks the real problem |
| `threading.Event` wait | Would require modifying `WebSocketManager._on_message()` to set the event; more invasive than using the existing method |
| Remove wait entirely | Commands sent before subscription is active may be silently dropped |

---

## Task 3: Prefix Validation Approach

### Question

How should user-entered route prefixes be validated before being sent to the Mist API?

### Findings

**Valid prefix formats accepted by the Mist show_route API**:
- IPv4 CIDR: `10.0.0.0/8`, `192.168.1.0/24`, `0.0.0.0/0`
- IPv6 CIDR: `2001:db8::/32`, `::/0`
- Single IP (host route): `10.1.1.1` (interpreted as /32)

**Python stdlib support**: `ipaddress.ip_network(prefix, strict=False)` handles all of the above. Setting `strict=False` allows host bits to be set (e.g., `10.0.0.1/24` is accepted and normalized to `10.0.0.0/24`).

**Edge cases**:
- Empty string: Skip validation (no filter applied)
- Hostname-style input: `ipaddress` raises `ValueError` — caught and reported
- Vendor-specific formats: Some operators may use non-standard notation; warn but allow

### Decision

Validate with `ipaddress.ip_network(prefix, strict=False)`. On validation failure, print a warning with the specific error and ask the user to confirm or re-enter. This follows the Constitution Principle III pattern: validate early, but respect operator expertise.

```python
import ipaddress

def validate_prefix(prefix_input):
    if not prefix_input:
        return prefix_input  # Empty is valid (no filter)
    try:
        ipaddress.ip_network(prefix_input, strict=False)
        return prefix_input
    except ValueError as error:
        print(f"-> Warning: '{prefix_input}' may not be a valid prefix: {error}")
        confirm = InputUtils.safe_input(
            "Send anyway? (y/N): ",
            context="prefix_validation", default_value="n"
        )
        return prefix_input if confirm.lower() in ["y", "yes"] else ""
```

### Alternatives Rejected

| Alternative | Why Rejected |
|-------------|-------------|
| Regex validation | Cannot handle IPv6, leading zeros, or CIDR range edge cases reliably |
| Hard reject | Operators may need vendor-specific prefix formats the API accepts but `ipaddress` does not recognize |
| No validation | Violates Constitution Principle III; confusing API errors on invalid input |

---

## Task 4: Connection Leak Edge Case Analysis

### Question

Is spec finding #10 (WebSocket connection leak on subscription failure) still present, and what is the exact fix needed?

### Findings

**Current code in `_connect_websocket` (lines 18018–18045)**:

```python
websocket_manager = WebSocketManager(apisession)
if not websocket_manager.connect():
    return None  # No leak — connection never established

if not websocket_manager.subscribe_to_channel(command_channel):
    websocket_manager.disconnect()  # Cleanup IS here (line 18037)
    return None
```

**Status**: The explicit `False` return path is handled — `disconnect()` is called. The spec finding was **partially inaccurate** for the normal failure path.

**Remaining leak**: If `subscribe_to_channel()` raises an **exception** (e.g., `WebSocketConnectionClosedException`, `BrokenPipeError`), the exception propagates up. In the orchestrator:

```python
websocket_manager = RoutingUtils._connect_websocket(...)  # Assignment never completes
```

The orchestrator's `finally` block sees `websocket_manager = None` (the initial value) and skips cleanup. But inside `_connect_websocket`, a connected `WebSocketManager` exists as a local variable that becomes unreferenced — Python's garbage collector will eventually clean it up, but the WebSocket thread may keep running until the process exits.

### Decision

Add try/except inside `_connect_websocket` to ensure `disconnect()` is called on any exception after `connect()` succeeds:

```python
websocket_manager = WebSocketManager(apisession)
if not websocket_manager.connect():
    return None

try:
    if not websocket_manager.subscribe_to_channel(command_channel):
        websocket_manager.disconnect()
        return None
    # ... subscription confirmation ...
    return websocket_manager
except Exception:
    websocket_manager.disconnect()
    raise  # Re-raise so orchestrator's except block handles it
```

### Alternatives Rejected

| Alternative | Why Rejected |
|-------------|-------------|
| Context manager (`__enter__`/`__exit__`) | Requires modifying `WebSocketManager` shared infrastructure; out of audit scope |
| Catch only in orchestrator | Cannot clean up `_connect_websocket`'s local reference from outside |
| Ignore (rely on GC) | WebSocket daemon thread may keep running; violates Constitution Principle III (safety-first) |

---

## Task 5: safe_input() Migration Scope

### Question

Which `input()` calls must be migrated to `safe_input()`, and what parameters should each use?

### Findings

**Constitution Principle III requirement**: "All input handling MUST use the `safe_input()` pattern with EOF handling and context logging."

**`InputUtils.safe_input()` signature** (line 2244):
```python
@staticmethod
def safe_input(prompt, default_value="", allow_empty=True, context="unknown"):
```

**Behavior**:
- Normal input: Returns stripped user input
- Empty input with default: Returns `default_value`
- EOF (Ctrl+D, broken pipe): Prints notice, returns `default_value`
- KeyboardInterrupt (Ctrl+C): Prints notice, returns `""`

**All `input()` calls in routing table scope**:

| # | File Line | Method | Current Code | Impact of EOF |
|---|-----------|--------|-------------|---------------|
| 1 | 18350 | `_get_routing_table_params` | `input("\nEnter route prefix...")` | Unhandled EOFError crash |
| 2 | 18353 | `_get_routing_table_params` | `input("Enter protocol filter...")` | Unhandled EOFError crash |
| 3 | 18355 | `_get_routing_table_params` | `input("Enter VRF name...")` | Unhandled EOFError crash |
| 4 | 18356 | `_get_routing_table_params` | `input("Enter BGP neighbor IP...")` | Unhandled EOFError crash |
| 5 | 18361 | `_get_routing_table_params` | `input("Enter route direction...")` | Unhandled EOFError crash |
| 6 | 18363 | `_get_routing_table_params` | `input("Enter node...")` | Unhandled EOFError crash |
| 7 | 18336 | `_display_routing_device_guidance` | `input("Continue with switch routing...y/N")` | Unhandled EOFError crash |

**Risk**: In SSH/container environments (the primary deployment target), EOF conditions are common when sessions disconnect. All 7 calls will crash with `EOFError` instead of gracefully returning defaults.

### Decision

Replace all 7 `input()` calls with `InputUtils.safe_input()`. Each call gets a descriptive `context` parameter for logging and a sensible `default_value` for EOF fallback. The continuation prompt (line 18336) defaults to `"n"` (safe default = do not proceed on EOF).

### Alternatives Rejected

| Alternative | Why Rejected |
|-------------|-------------|
| Wrap in try/except EOFError | Would need 7 separate try/except blocks; `safe_input()` already handles this cleanly |
| Keep `input()` in non-SSH contexts | MistHelper runs in both local and container contexts; all paths must be safe |
| Add a global input wrapper | `safe_input()` already exists and is the project standard |
