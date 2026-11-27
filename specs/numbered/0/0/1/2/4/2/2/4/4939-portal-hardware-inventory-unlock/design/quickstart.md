# Quickstart: Portal hardware inventory unlock without the free-form shell

## Reproduce the issue on main

1. Leave `PORTAL_WS_ENABLE_SHELL` and `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` unset.
2. Start the portal process.
3. Open the WebSockets tab and select the Multi Site tab.
4. Select "Collect EX hardware inventory" and request a preview.
5. Expected result on main: HTTP 403 with code `locked`. The message reads "This stream is locked by the portal settings." (`validation.py` line 59, RC-067). The refusal detail names `PORTAL_WS_ENABLE_SHELL`. The page text does not name it.

The live reproduction from the issue body is Unverified (U-1). No container run is part of this record.

## Verify the target behavior after implementation

1. Set `PORTAL_WS_ENABLE_HARDWARE_INVENTORY=true`. Leave `PORTAL_WS_ENABLE_SHELL` unset.
2. Restart the portal process.
3. Preview the hardware preset. Expected result: HTTP 200 with the EX target list.
4. Preview a generic shell batch with commands. Expected result: HTTP 403 with code `locked` and flag `PORTAL_WS_ENABLE_SHELL`.
5. Unset both flags and restart the portal process.
6. Preview the hardware preset. Expected result: HTTP 403 with code `locked` and flag `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.

## Run the verification commands

Run each command from the repository root. Each Tests gate command expects "All tests pass".

```powershell
python -m pytest tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py
python -m pytest tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py
python -m pytest tests/unit/websocket_streams/intake/test_ws_start_request.py
python -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py
python -m pytest tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py
python -m pytest tests/unit/ex_hardware_inventory/run/test_hardware_routing.py
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py
python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py
python -m ruff check .
```

The Lint gate expects "All checks passed".
