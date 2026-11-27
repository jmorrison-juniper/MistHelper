# Contract: Catalog flags payload

The page receives lock flags under the key `flags` in the catalog payload. The builder for the payload is in `stream_catalog.py` lines 73 to 75 (RC-061).

```json
{
  "flags": {
    "changes": {"enabled": false, "variable": "PORTAL_WS_ENABLE_CHANGES"},
    "shell": {"enabled": false, "variable": "PORTAL_WS_ENABLE_SHELL"},
    "hardware_inventory": {"enabled": false, "variable": "PORTAL_WS_ENABLE_HARDWARE_INVENTORY"}
  }
}
```

## Rules

- `changes` and `shell` keep their current form (spec FR-007).
- `hardware_inventory.enabled` reports the value of the hardware flag.
- `hardware_inventory.variable` names `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- The page reads `hardware_inventory` only when the key exists. The page test fixture on line 159 sends `"flags": {}` (RC-119).
- When both flags are false, the page shows the hint that names `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` (T017).
