# Contract: Menu 13 Dispatch, MSP Branch

This contract defines what menu 13 prints and which callback it runs when the grant list is empty. Console text is ASCII and uses plain words for a junior NOC engineer. The contract covers `OrgDeviceInventoryMSPOrchestrator.dispatch` in `src/mist/resources/inventory/org_device_inventory_msp.py`, and the facade `OrgDeviceInventorySummary.dispatch` that calls it.

## Identity

- Method: `OrgDeviceInventoryMSPOrchestrator.dispatch(single_org_fn, select_org_fn, batch_fn) -> None` (RC-11).
- Facade: `OrgDeviceInventorySummary.dispatch()` builds the orchestrator and calls `dispatch` (RC-13).
- Private helper: `_confirm_no_msp_access() -> bool`. It runs the live lookup and prints the failure text.
- Module constants:
  - `_LOOKUP_FAILED_MSG`
  - `_RESTART_FOR_GRANTS_MSG`
- Registry category of menu 13: `safe` (RC-62).

## Decision Table

| Grant list | Live lookup | Console output | Callbacks called |
| - | - | - | - |
| Holds one or more MSP grants | Not made | The dispatch menu, as before | The callback that the chosen mode selects, as before |
| Empty | Failed lookup | `_LOOKUP_FAILED_MSG` | None |
| Empty | Valid profile with zero MSP grants | None from the helper | `single_org_fn` once |
| Empty | Valid profile with one or more MSP grants | `_RESTART_FOR_GRANTS_MSG` | None |
| Empty, and the session is None | Failed lookup, no API call | `_LOOKUP_FAILED_MSG` | None |

## Operator Messages

These strings are exact. ASCII only.

- `_LOOKUP_FAILED_MSG`: `X Cannot confirm MSP access because the profile lookup failed. Inventory did not run.`
- `_RESTART_FOR_GRANTS_MSG`: `X MSP access was found, but this session did not load it. Restart MistHelper, then run this operation again.`

## Log Lines

1. Info before the live lookup: `Confirming MSP access with a live profile lookup before the single-organization inventory.`
2. Debug after the live lookup: `Live MSP lookup finished: succeeded=%s, grant count=%d.` The arguments are the boolean and the count.
3. The lookup itself writes its own warning when it fails (see `profile-lookup.md`).

## Rules

1. `dispatch` returns None in every branch.
2. `dispatch` calls no callback unless the decision table allows it.
3. A non-empty grant list makes no profile lookup (FR-008).
4. The live lookup uses the module global `apisession`. The facade sets it from `mh.apisession` before each call (RC-12).
5. No log line or message contains a token, a password, a response body, or an exception message (FR-013).

## Caution

Caution: a failed lookup blocks menu 13 only for the run that failed. Run the operation again after the access recovers.
