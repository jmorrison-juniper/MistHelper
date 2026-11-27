# Contract: Converter test host

The test host is the fixture that builds the portal app for the converter journeys. It lives in the class `TestCiscoConverterJourneys` in `tests/e2e/web_portal/test_portal_smoke.py`.

## Build order

1. Import `WebPortalApp` from `web_portal.app` and `build_static_menu_actions` from `web_portal.menu_registry`. The E2E fixture uses the same imports (RC-44).
2. Call `WebPortalApp.create_app` with `apisession=None`, the static menu actions, and organization ID `test-org-id` (RC-44).
3. Set `app.request_class` to `ConverterRequest` before any request (RC-101).
4. Register `ConverterRoutes.blueprint()` with the app. The app must not have served a request yet (RC-73).
5. Serve the app with `werkzeug.serving.make_server` on `127.0.0.1` and port 0, in a daemon thread.
6. Yield the loopback base URL to the tests.
7. After the class, stop the server, join the thread, close the server, and call `WebPortalApp.shutdown_app` (RC-45).

## Constraints

- The harness edits no shared file. `web_portal/app.py`, `web_portal/templates/base.html`, and the theme files stay unchanged (RC-30, RC-31).
- The harness reads no environment value and sets no secret. It uses the host fallback secret (RC-41, D-13).
- CSRF protection stays on. The harness never sets `WTF_CSRF_ENABLED` to false.
- `InputInterceptor.install` returns early on a repeated call (RC-43). The factory may run once for each class.
- The harness logs an info line before it starts the server and a debug line after it stops the server (constitution Principle VII, RC-83, U-2).
- The browser context is new for each test, so no cookie or storage value carries over between tests.

## Production check

`test_production_host_serves_no_converter_route` builds the production app with `create_app` only. It does not register the converter. A request to `/cisco-config-converter/` must return 404 (RC-30).
