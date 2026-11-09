# Quickstart: Long packet capture

## Prerequisites

Use the worktree virtual environment. If it is absent, run
`uv sync --locked --extra dev`.

Do not configure production credentials for these tests. The test suite uses
local fake Mist services.

## Validate the feature

Run the focused unit and contract tests:

```sh
python -m pytest \
  tests/unit/websocket_streams/catalog/test_ws_utility_catalog.py \
  tests/unit/websocket_streams/intake/test_ws_field_checker.py \
  tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py \
  tests/unit/websocket_streams/live/runners/utility/test_ws_utility_filters.py \
  tests/unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py \
  tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py \
  tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py \
  tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py \
  tests/unit/websocket_streams/web/test_ws_web_services.py \
  tests/contract/websocket_streams/test_ws_utility_trigger_parity.py
```

Run the browser journey with the repository's local Playwright fixture:

```sh
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py
```

The feature passes when the tests verify both duration bounds, quiet-period
retention, matching end events, subscribe-before-start order, conditional stop,
and local-only service use.
