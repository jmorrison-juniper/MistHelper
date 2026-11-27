# Data model: Site read refusal

This repair changes no model and no schema. The entities below describe the state that the refusal path reads or protects.

## Entities

- **Selection**: The signed organization identifier `org_id` and the ordered site identifiers `site_ids`. The natural keys come from the Mist API. The active context reads them (`src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` line 487).
- **Site list read**: The site records of one organization from `listOrgSites`. Each record holds the site `id` as its natural key. The read returns records and partial reasons (`select.py` lines 1044 to 1080).
- **Options**: The validated operator choices in the signed browser session. The session keys are `OPTIONS_SESSION_KEY`, `OPTIONS_ORG_SESSION_KEY`, and `OPTIONS_NONCE_SESSION_KEY` (`org_upgrade.py` lines 1232 to 1234).
- **Plan**: The durable aggregate operation. Its identifier is `operation_id`. It binds to `org_id` and to `request_nonce` (`org_upgrade.py` lines 1290 to 1303). The save writes it with `_write_operation` (line 1301).
- **Refusal**: A response only. The refusal persists nothing. Its shape is in `design/contracts/refusal.md`.

## State transitions

| From | Event | To | Evidence |
| - | - | - | - |
| Plan absent | Save succeeds, and the site read is whole | Plan present, session bound | `org_upgrade.py` lines 1280 to 1305 |
| Plan absent | Save hits a transport fault at the site list read | Plan absent, session unchanged | The try block at line 1221 ends before the session writes at lines 1232 to 1234 |
| Plan present | Replacement save hits a transport fault | Plan present, session unchanged | The plan write at line 1301 does not run |
| Plan present | Options or confirmation page hits a transport fault | Plan present, session unchanged | The page handlers return before any write (lines 1147 to 1149, 1350 to 1352) |
| Site list read whole | The SDK converts a connection fault into a response with no status | Site list read partial | `capture/devices.py` lines 265 to 266 and `select.py` line 1072 |
| Site list read partial | Later fresh read is whole | Site list read whole | The cache keeps whole reads only (`select.py` lines 394 to 395) |

## Keys and invariants

- A refused save writes no plan, no nonce, and no saved option. The contract test checks the store and the session (contract lines 56 to 62).
- A cached site list read holds whole reads only, so a partial read never reappears from the cache.
