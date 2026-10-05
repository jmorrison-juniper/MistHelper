# Quickstart: Client Selection Validation

This guide records local validation for issue #3889.
It uses mocked SDK responses and intercepted browser requests.
Do not use credentials or live Mist operations.

## Prerequisites

1. Use Python 3.13 or newer.
2. Install the repository's pinned `mistapi>=0.64.0,<0.65` dependency.
3. Use the worktree's `.venv` for every Python command.
4. Do not run a utility, capture, shell call, or DHCP release.

## Regression Suite

Run the focused unit tests, isolated dialog-audit tests, and existing page tests:

```bash
rtk proxy .venv/bin/python -m pytest -q tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py tests/unit/websocket_streams/catalog/test_ws_client_field_modes_3889.py tests/e2e/websockets_tab/dialog_audit tests/e2e/websockets_tab/test_websockets_page.py
```

Result on 2026-10-05: **141 passed**.

The browser policy blocks requests that are not explicitly listed.
The tests do not send a utility request.

## Scenarios

- EX client results match the selected site and device MAC.
- SRX and SSR show manual entry because gateway association is unproven.
- Empty, 4xx, 5xx, network, timeout, malformed, and incomplete results remain distinct.
- Site, device, and operation changes reject stale results.
- Manual input stays available during lookup and after errors.
- Multiple selected and manual DHCP MAC addresses retain the `macs` payload.
- A selected MAC table client fills the editable `mac_address` field.
- Empty optional values remain omitted.
- Selection does not start a utility.
- Confirmation, locks, cancellation, and target review remain unchanged.

Partial and wildcard MAC table filters remain outside this feature.
The pinned SDK documentation does not prove that it supports those forms.

## Safety Boundary

All client records and responses are synthetic.
Do not run live API discovery, device utilities, captures, shell commands, or DHCP releases.
DHCP release changes require explicit human review.
Do not enable auto-merge or merge this change before approval.
