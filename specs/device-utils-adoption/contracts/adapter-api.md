# Contract: DeviceUtilsAdapter API

**Date**: 2026-06-11 | **Plan**: [../plan.md](../plan.md)

## DeviceUtilsAdapter.execute()

### Input

```python
def execute(
    self,
    command: str,        # e.g., "show_mac_table", "ping", "bounce_port"
    device_type: str,    # "switch", "gateway", "ap"
    site_id: str,        # UUID string
    device_id: str,      # UUID string
    **params             # Command-specific params (e.g., host="8.8.8.8" for ping)
) -> list[dict]:
```

### Output

Returns `list[dict]` — flattened records matching current CSV/SQLite output format.

Example for `show_mac_table`:
```python
[
    {"mac_address": "aa:bb:cc:dd:ee:ff", "port": "ge-0/0/1", "vlan": 10, "type": "dynamic"},
    {"mac_address": "11:22:33:44:55:66", "port": "ge-0/0/2", "vlan": 20, "type": "static"},
]
```

Column names, types, and order MUST match current output exactly.

### Errors

| Condition | Behavior |
| - | - |
| device_utils not available | Falls back to raw API; logs `info` "device_utils not available, using raw API" |
| Command not in device_utils | Falls back to raw API; logs `info` "command {cmd} not in device_utils for {type}" |
| Device offline | Raises same exception as current implementation; user sees same error message |
| API 429 rate limit | SDK handles internally; MistHelper's adaptive delay not involved |
| API auth failure | Raises same exception as current implementation |
| Timeout | Same timeout behavior as current WebSocket polling |

### Behavioral Contract

1. User-facing print statements (prompts, progress, results) MUST be identical
2. CSV column names and order MUST be identical
3. SQLite table schema MUST be unchanged (same `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries)
4. Error messages shown to user MUST be identical
5. Destructive command confirmation prompts MUST be identical
