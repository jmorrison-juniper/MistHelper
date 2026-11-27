# Contract: Portal Registration

## Scope

Tasks T009 and T010 only. This contract defines the registration order and the navigation shape. It adds no route.

## Order inside `WebPortalApp.create_app`

1. `_apply_security` installs CSRFProtect. Source: `web_portal/app.py` line 52, and `web_portal/services/config.py` lines 297 to 304.
2. The factory sets `app.request_class` to `ConverterRequest`. Task T009 adds this line before `web_portal/app.py` line 53.
3. `_register_blueprints` registers the converter blueprint. Source: `web_portal/app.py` line 182. Task T009 adds the call after line 207.

Caution: registering the blueprint before the request class exists stops the portal start with `ValueError`. Fix the order, and the start succeeds again.

## Preconditions that the blueprint checks

- `app.request_class` is a subclass of `ConverterRequest` (`src/interfaces/portals/cisco_config_converter/routes.py` line 105).
- `"csrf"` appears in `app.extensions`, and `WTF_CSRF_ENABLED` is true (routes.py line 107).

## Approved route set

| Method | Rule | Endpoint |
| - | - | - |
| GET | `/cisco-config-converter/` | `cisco_converter.page` |
| POST | `/cisco-config-converter/preview` | `cisco_converter.preview` |
| POST | `/cisco-config-converter/review` | `cisco_converter.review` |
| POST | `/cisco-config-converter/export` | `cisco_converter.export` |
| GET | `/cisco-config-converter/assets/<path:filename>` | `cisco_converter.static` |

Source: `routes.py` lines 49 to 66. The blueprint sets the prefix at line 54 and the static path `/assets` in its constructor.

## Navigation entry

- **Position**: After the licensing comparison anchor in `web_portal/templates/base.html`, which starts at line 79.
- **Attributes**: `href` from `url_for('cisco_converter.page')`, `data-testid="nav-cisco-converter"`, and the visible label "Cisco Converter".
- **Count**: One converter anchor in the navigation bar.

## Forbidden changes under this integration

- Any other route under `/cisco-config-converter/`.
- Any change to `wsgi.py`, `compose.yml`, or `web_portal/services/config.py`.
- Any converter-specific CSRF handler (decision D-6).

## Failure evidence

- Missing request class: `ValueError` with the message "Set the portal request class to ConverterRequest before registration." (routes.py line 106).
- Missing CSRF: `ValueError` with the message "Enable CSRFProtect before converter registration." (routes.py line 108).
