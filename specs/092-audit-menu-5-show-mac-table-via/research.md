# Research: Audit Menu #5 — Show MAC Table via WebSocket

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Research Questions

This document resolves all NEEDS CLARIFICATION items and documents technology
decisions for the eight audit findings (AF-01 through AF-08).

---

## RQ-01: Can `apisession` Replace Raw `requests.post`? (AF-05)

**Decision**: Yes — use `apisession.mist_post()` for the show_mac_table REST call.

**Rationale**: The `apisession` object (mistapi SDK) provides a `mist_post(uri, body)`
method (defined in `mistapi/__api_request.py`, lines 279–301) that:

- Handles authentication automatically (stored token, no manual headers)
- Manages retry logic and rate-limit handling via `_request_with_retry()`
- Returns a typed `APIResponse` with `.status_code` and `.data` attributes
- Uses the session's connection pool and proxy configuration

The `WebSocketManager` already stores the session as `self.mist_session`
(line 3980), so the fix is straightforward:

```python
# Before (raw requests.post):
mac_table_url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table"
headers = {"Authorization": f"Token {mist_apitoken}", "Content-Type": "application/json"}
response = requests.post(mac_table_url, headers=headers, json=payload, timeout=30)

# After (apisession):
uri = f"/api/v1/sites/{site_id}/devices/{device_id}/show_mac_table"
response = apisession.mist_post(uri, body=payload)
```

**Alternatives Considered**:

1. *Keep raw `requests.post`*: Rejected — bypasses session retry logic,
   connection pooling, and proxy configuration. All other non-WebSocket API
   calls use mistapi methods. Consistency matters.
2. *Search for a dedicated `mistapi.api.v1.sites.devices.show_mac_table`
   SDK method*: Not found in the SDK. The generic `mist_post()` is the
   correct approach for endpoints without dedicated SDK wrappers.

**Impact**: All 6 device command POST calls in the codebase use raw
`requests.post` (ping, ARP, show_mac_table, forwarding table, show route,
ARP trigger). This audit fixes `show_mac_table` only — the others should be
addressed in their respective audit specs.

---

## RQ-02: Can WebSocket Subscription Be Confirmed? (AF-03, AF-04)

**Decision**: Yes — use the existing `wait_for_subscription_confirmation()`
method to replace the hardcoded `time.sleep(1)`.

**Rationale**: The infrastructure already exists and is proven:

1. **Server acknowledgment** (line 4691): The Mist WebSocket server sends
   `{"event": "channel_subscribed", "channel": "..."}` when a subscription
   is confirmed.
2. **`confirmed_subscriptions` set** (line 3991): Initialized in
   `WebSocketManager.__init__()`, populated in `_on_message()` (line 4698)
   when the acknowledgment arrives.
3. **`wait_for_subscription_confirmation()` method** (lines 4077–4113):
   Polls `confirmed_subscriptions` at 0.1-second intervals with a
   configurable timeout (default 10 seconds).
4. **Already used in 3 locations**: Packet capture (lines 6940, 7005) and
   service ping (line 16810) — all working correctly.

The `show_mac_table` method is one of ~11 locations that still use the
`time.sleep(1)` anti-pattern instead of proper confirmation.

**Alternatives Considered**:

1. *Increase sleep to 2–3 seconds*: Rejected — still a race condition,
   just less likely. Wastes time under normal conditions.
2. *Event-based confirmation (threading.Event)*: Rejected — would require
   refactoring `WebSocketManager` internals. The polling approach is already
   proven and the 0.1-second interval is efficient enough.

**Implementation**:
```python
# Before:
time.sleep(1)

# After:
if not websocket_manager.wait_for_subscription_confirmation(command_channel, timeout_seconds=10):
    print("! Subscription confirmation not received within timeout")
    print("! Proceeding anyway, but results may not be received")
else:
    print("-> Subscription confirmed")
```

---

## RQ-03: How to Improve Completion Detection? (AF-06)

**Decision**: Increase the MAC-table-specific idle timeout from 3 seconds to
5 seconds, and pass `activity_timeout_seconds=5` from `show_mac_table`.

**Rationale**: The `wait_for_command_result` method uses three MAC-specific
completion heuristics:

1. **Repeated messages** (line 4413): 5 identical consecutive messages →
   complete. This is reliable and should be kept.
2. **Idle timeout** (line 4437): 3 seconds idle + 10+ messages + 10+
   entries → complete. The 3-second threshold is too aggressive for large
   tables on busy switches — the spec requires tolerance for 5-second
   pauses (FR-008, SC-005).
3. **Generic activity timeout** (line 4528): Defaults to 2 seconds. This
   fires before the MAC-specific 3-second check and can cause premature
   completion for MAC tables.

The fix has two parts:
- Pass `activity_timeout_seconds=5` from `show_mac_table` to override the
  2-second default. This prevents the generic activity timeout from
  firing before MAC-specific logic runs.
- The MAC-specific idle timeout at line 4437 should also be raised to
  5 seconds to match FR-008, but since `wait_for_command_result` is
  shared infrastructure, this change should be parameterized rather than
  hardcoded. The simplest approach: use the `activity_timeout_seconds`
  parameter that's already being passed through.

**Alternatives Considered**:

1. *Count-based completion (wait for N entries)*: Rejected — entry count
   from the header ("44 entries") is unreliable because the header arrives
   before the data. We'd need to count actual lines, which varies by
   format.
2. *Protocol-level end-of-stream marker*: Not available — the Mist
   WebSocket API does not send an explicit end-of-command-output signal.
3. *Refactor `wait_for_command_result` to accept a completion strategy
   object*: Correct long-term solution but out of scope for this audit.
   The 493-line method needs its own dedicated refactoring spec.

**Impact**: Only `show_mac_table`'s call to `wait_for_command_result` changes.
Other commands (ping, ARP, routing) are unaffected because they don't pass
`activity_timeout_seconds`.

---

## RQ-04: How to Distinguish Empty MAC Table from Error? (AF-07)

**Decision**: Check for the "ethernet switching table : 0 entries" pattern
in the raw output. If found, display "MAC table is empty (0 entries learned)"
instead of the generic "No output data received."

**Rationale**: The MAC table header line always contains the entry count:
```
Ethernet switching table : 0 entries, 0 learned
```
The existing regex `r"ethernet switching table\s*:\s*(\d+)\s+entries"` can
extract this count. When `entry_count == 0`, the result is a valid empty
table, not an error.

**Implementation**:
```python
if not raw_output and not output_fields:
    # Check if header indicates zero entries
    all_content = str(mac_table_result)
    match = re.search(r"ethernet switching table\s*:\s*0\s+entries", all_content, re.IGNORECASE)
    if match:
        print("MAC table is empty (0 entries learned)")
        print("This is normal for a switch with no active hosts on its interfaces.")
    else:
        print("! No output data received — this may indicate a command failure")
        print(f"! Available result keys: {list(mac_table_result.keys())}")
```

**Alternatives Considered**:

1. *Return a dedicated `EmptyResult` type from `wait_for_command_result`*:
   Rejected — requires changing the shared method's return type, which
   affects all callers.
2. *Check `len(mac_table_result) == 0`*: Insufficient — the result dict
   may have keys but with empty string values.

---

## RQ-05: How to Fix the `locals().get()` Cleanup Pattern? (AF-02)

**Decision**: Initialize `websocket_manager = None` before the `try` block,
then use a simple `if websocket_manager is not None` check in `finally`.

**Rationale**: The `locals().get("websocket_manager")` pattern (line 16032)
exists because `websocket_manager` is assigned inside the `try` block
(line 15870). If an exception occurs before that assignment, the variable
doesn't exist and a bare `websocket_manager.disconnect()` would raise
`UnboundLocalError`. The `locals().get()` workaround avoids this but is
fragile — if the variable is renamed, the string literal won't be updated.

The standard Python pattern is:
```python
websocket_manager = None  # Initialize before try
try:
    websocket_manager = WebSocketManager(apisession)
    # ... rest of method ...
finally:
    if websocket_manager is not None:
        websocket_manager.disconnect()
```

This is explicit, refactoring-safe, and idiomatic.

**Alternatives Considered**:

1. *Context manager (`with WebSocketManager(...) as ws`)*: Ideal but
   requires adding `__enter__`/`__exit__` to `WebSocketManager`. Worth
   doing eventually but adds scope to this audit.
2. *Move all initialization outside try*: Rejected — connection/subscription
   can raise, and we want to catch those errors.

---

## RQ-06: How to Fix the Inline `import traceback`? (AF-08)

**Decision**: Remove the inline `import traceback` from the except block.
The module is already imported at the top of `MistHelper.py` (line 47:
`import traceback`).

**Rationale**: The inline import at line 16023 (`import traceback`) is
redundant — `traceback` is already in the module's top-level imports.
The inline import likely originated from a copy-paste from a standalone
script. Since the top-level import exists, the inline one can simply be
deleted.

**Alternatives Considered**: None — this is a straightforward deletion.

---

## RQ-07: Test Strategy for Zero Coverage (AF-01)

**Decision**: Create two new test files following the existing test patterns:

1. `tests/unit/test_show_mac_table.py` — Tests for the `show_mac_table`
   static method (mocked WebSocket and REST interactions)
2. `tests/unit/test_websocket_manager.py` — Tests for `WebSocketManager`
   methods used by `show_mac_table` (connect, subscribe, wait, disconnect)

**Rationale**: The existing test suite uses:

- Class-based test organization (`class TestFeatureName:`)
- `conftest.py` fixtures: `tmp_data_dir`, `tmp_jsonl_file`,
  `isolate_working_directory` (autouse — ensures no real data/ writes)
- Pure function duplication for testability (R1 pattern from
  `test_data_processing.py`)
- `monkeypatch` for dependency injection
- No network calls, no `.env` loading
- 30-second timeout for unit tests

**Test coverage targets** (from spec SC-004: ≥80% line coverage):

| Test | What It Covers | Priority |
|------|---------------|----------|
| Happy path — full MAC table | Site select → connect → subscribe → POST → stream → display | P1 |
| Connection failure | `connect()` returns False | P1 |
| Subscription failure | `subscribe_to_channel()` returns False | P1 |
| REST POST failure | Non-200 status from POST | P1 |
| Missing session ID | POST 200 but no `session` in response | P1 |
| Timeout | `wait_for_command_result()` returns None | P1 |
| Empty MAC table | Result with zero entries | P1 |
| Large table streaming | 5000+ entries with pauses | P2 |
| Cleanup on success | `disconnect()` called after success | P2 |
| Cleanup on error | `disconnect()` called after exception | P2 |
| Cleanup on interrupt | `disconnect()` called after KeyboardInterrupt | P2 |
| Completion: repeated messages | 5 identical messages → complete | P2 |
| Completion: idle timeout | 5s idle → complete | P2 |

**Alternatives Considered**:

1. *Integration tests with real WebSocket*: Rejected for unit test scope —
   would require Mist API credentials and a live switch.
2. *Single test file for everything*: Rejected — `WebSocketManager` tests
   are reusable across multiple command audits. Separate files promote
   reuse.

---

## RQ-08: Method Decomposition Strategy (Principle I Compliance)

**Decision**: Extract `show_mac_table` (227 lines) into ≤5 helper methods,
each under 25 lines. The helpers are private static methods within
`WebSocketCommands`.

**Rationale**: The current method has clear logical sections that map to
helper functions:

1. `_select_mac_table_target()` — site/device selection (return
   `(site_id, device_id)` or `None`)
2. `_setup_websocket_for_command()` — connect + subscribe + confirm
   (return `WebSocketManager` or `None`)
3. `_trigger_mac_table_command()` — POST via apisession, extract session ID
   (return `session_id` or `None`)
4. `_display_mac_table_result()` — format and print MAC table output,
   handle empty table
5. `show_mac_table()` — orchestrator that calls 1–4 in sequence, handles
   errors, cleans up in `finally`

Each helper takes ≤5 parameters and stays under 25 lines. The orchestrator
stays under 25 lines because it delegates all logic to helpers.

**Alternatives Considered**:

1. *Move to a separate class (`MacTableCommand`)*: Overkill for a single
   static method. `WebSocketCommands` already groups all WebSocket command
   methods.
2. *Don't decompose — just fix the bugs*: Violates Principle I (25-line
   limit). The audit must bring the method into compliance.
