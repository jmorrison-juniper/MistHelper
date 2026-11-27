# Data model: Portal hardware inventory unlock without the free-form shell

The change stores no data. The entities below exist as environment values, catalog fields, and preview memory.

## Entities

| Entity | Natural key | Values | Source |
|--------|-------------|--------|--------|
| Hardware flag | `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` | true or false. Default false. | New field after `settings.py` line 43 |
| Shell flag | `PORTAL_WS_ENABLE_SHELL` | true or false. Default false. | `settings.py` line 59 (RC-053) and field default on line 36 (RC-051) |
| Lock scope | `lock_scope` with server value `hardware_preset` | `hardware_preset` or absent | Set in the hardware branch of `sessions.py` (T013) |
| Lock refusal | Code `locked` | HTTP 403 with a flag name and the standard message | `validation.py` line 59 (RC-067), `error.py` line 16 (RC-073) |
| Catalog flags | Key `flags` | Keys `changes`, `shell`, and `hardware_inventory` | `stream_catalog.py` lines 73 to 75 (RC-061) |
| Preview record | Preview identifier | Stores the preset and the operation snapshot. Lives 300 seconds. | `sessions.py` line 77 (RC-080) and line 628 (RC-089) |

## State transitions

- Flag: unset, then false by default. An operator sets true and restarts the portal. The portal reads flags at start (spec assumption).
- Preview: created with the flags checked for each target. The preview then moves to one of three states:
  - Admitted, when the start re-check passes.
  - Refused with code `locked`, when the flag is false at admission.
  - Refused as expired or unknown, after 300 seconds or when the identifier is not known (`sessions.py` line 610, RC-127).

## Keys and uniqueness

- The flag names are unique environment variable names.
- The lock scope has one server value. Browser fields cannot set it (RC-097 lists the accepted browser fields).
