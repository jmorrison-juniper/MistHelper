# Contract: Refusals for the hardware preset and free-form shells

| Case | HTTP status | Code | Flag in detail | Message |
|------|-------------|------|----------------|---------|
| Hardware preset with both flags false | 403 | `locked` | `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` | "This stream is locked by the portal settings." (`validation.py` line 59, RC-067) |
| Free-form shell with only the hardware flag true | 403 | `locked` | `PORTAL_WS_ENABLE_SHELL` | Same message |
| Flag changed after preview, at admission | 403 | `locked` | Flag of the stored operation | Same message |
| Browser field outside the allowed set | 400 | `bad_request` | None | "The preview request has an unknown field." (`sessions.py` line 135, RC-126) |

The HTTP status of each code comes from `error.py`. Code `locked` maps to 403 on line 16 (RC-073). Code `bad_request` maps to 400 on line 14 (RC-072).

## Accepted browser fields for the hardware preset

The preset accepts the fields `preset`, `format`, `scope_revision`, and `sites` (`hardware_xml.py` line 344, RC-097). A browser cannot send commands or set the lock scope.
