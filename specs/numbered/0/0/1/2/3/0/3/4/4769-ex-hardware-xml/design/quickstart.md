# Quickstart: EX Hardware XML Collection

**Feature**: [spec.md](../spec.md)

## Prerequisites

- Use the isolated issue #4769 worktree.
- Install Python 3.15.2 and create its virtual environment with `scripts/bootstrap_worktree.py`.
- Use only mock Mist responses for development and automated tests.
- Do not read the main checkout `.env`. Use mocked responses for automated tests.
- For authorized live acceptance, check current running status before either fixed native command.

## Automated Validation

Run the focused WebSockets service and page tests from the active Python 3.15.2 environment:

```powershell
python -B -m pytest tests/unit/websocket_streams/web/test_ws_web_services.py -q
python -B -m pytest tests/e2e/websockets_tab/test_websockets_page.py -q
```

The service tests must cover XML, JSON, and BOTH output, repeated XML elements, namespace and attribute preservation, malformed and oversized output, unsafe names, per-device setup failures, and cancellation. The browser test must show the dedicated action, default XML selection, the format choices, target preview, and completed archive link.

Run the existing WebSockets contract tests after the feature tests:

```powershell
python -B -m pytest tests/contract/websocket_streams/test_ws_sdk_contract.py tests/contract/websocket_streams/test_ws_utility_trigger_parity.py -q
```

These tests must pass without production credentials. They do not execute device commands.

## Local UI Validation

Start the portal with the repository's existing development procedure and mock WebSockets service. Confirm the preset remains unavailable when `PORTAL_WS_ENABLE_SHELL` is false. With the fake enabled, preview all sites, run each format choice, and inspect only generated fixture files under test temporary storage.

## Parent Live Validation

After local deployment, the parent may perform the authorized read-only validation against the configured organization. Check XML and JSON output quality, file names, manifest outcomes, and the archive. Keep the live-validation task incomplete until the parent records that evidence.

See [the API contract](contracts/ex-hardware-xml.md) and [the data model](data-model.md) for request and output details.
