# Implementation Plan: WebSocket Dialog Target Wording

**Branch**: `jmorrison-juniper-fix-3890-websocket-dialog-wording` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary

Add utility-key purpose sentences to `UtilityText`, in the same pattern as the existing `_UTILITY_HINTS` table.
Pass the utility key from `UtilityDiscovery.entry` to `UtilityText.sentence`.
The text changes only. Execution logic stays unchanged.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, Flask, Playwright for the browser test

**Storage**: None

**Testing**: pytest unit tests and one independent Playwright module

**Constraints**: No live Mist API call. No click on Start. No edit to files that PR #3814 owns.

## Constitution Check

- Class-based design: the change stays inside `UtilityText`. No wrapper function.
- Safety: the `change` safety class, the `PORTAL_WS_ENABLE_CHANGES` lock, and the warning stay unchanged.
- STE: each sentence is 25 words or fewer.

## SDK Evidence

`mistapi/device_utils/__tools/dhcp.py:release_dhcp_leases` (0.64.0) states:

- EX: network + macs, network + port_id, port_id.
- SRX / SSR: network, network + macs, network + port_id, port_id, port_id + macs.

`mistapi/device_utils/__tools/mac.py:retrieve_mac_table` (0.64.0) states that `mac_address`, `port_id`, and `vlan_id` are optional filters.

## Project Structure

```text
src/mist/realtime/websocket_streams/catalog/utility_text.py                    # Add _UTILITY_SENTENCES
src/mist/realtime/websocket_streams/catalog/utilities/utility_discovery.py     # Pass the utility key
tests/unit/websocket_streams/catalog/test_ws_utility_text_3890.py              # Unit and SDK contract tests
tests/e2e/websockets_tab/test_3890_dialog_wording.py                           # Browser proof
changelog.d/issue-3890-websocket-dialog-wording.md                             # Release note
```

## Risks

- A sentence keyed by name alone would give SRX text to EX. The key includes the family, so each family gets its own text.
