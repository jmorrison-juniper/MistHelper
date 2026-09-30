# Wiring Manifest: Client CoA Disconnect

## Summary

Menu 286 adds a destructive client session control operation for helpdesk use.
The operation covers wireless reauthenticate, wired reauthenticate, disconnect, unauthorize guest, and deauth rogue clients.

## Owned Paths

- `specs/3566-client-coa-disconnect/**`
- Planned implementation package: `src/device/client_session_control/`
- Planned tests: `tests/unit/device/client_session_control/`
- Planned release note fragment: `changelog.d/issue-3566-client-coa-disconnect.md`

## Deferred Repository Wiring

Registration is deferred.
This planning step must not edit repository wiring files.

Deferred files named by the contract:

- `MistHelper.py`
- `operation_registry.py`
- `endpoint_primary_key_strategies.py`
- `README.md`
- `copilot-instructions.md`
- `menu_reference.md`
- `web_portal`

## Menu Registration

- Menu number: 286
- Category: destructive
- Handler package: `src/device/client_session_control/`
- Handler class: `ClientSessionControl`
- Entry point: static `run()`

## Dry Run Wiring Contract

The menu handler lambda must pass the global CLI dry run value to the handler.
This follows the menu 161 pattern that accepts `dry_run=False` in the lambda.
It also keeps the menu 207 destructive confirmation pattern.

Required wiring shape for implementation:

```text
handler=lambda dry_run=False: ClientSessionControl.run(
    MainEntrypoint.context.apisession,
    ConfigUtils.get_cached_or_prompted_org_id(),
    dry_run=dry_run,
)
```

Implementation must adjust imports and dependency names to match the final package.
The handler must not read MistHelper global arguments directly.

## Operation Contract

The operation asks for these values:

1. Site
2. Action
3. Client MAC or rogue BSSID
4. Exact confirmation by typing the normalized target again

Supported actions:

- Wireless reauthenticate
- Wired reauthenticate
- Disconnect
- Unauthorize guest
- Deauth rogue clients

## Mist API Contract

| Action | Operation ID | SDK module |
| - | - | - |
| Wireless reauthenticate | `reauthSiteDot1xWirelessClient` | `mistapi.api.v1.sites.clients` |
| Wired reauthenticate | `reauthSiteDot1xWiredClient` | `mistapi.api.v1.sites.wired_clients` |
| Disconnect | `disconnectSiteWirelessClient` | `mistapi.api.v1.sites.clients` |
| Unauthorize guest | `unauthorizeSiteWirelessClient` | `mistapi.api.v1.sites.clients` |
| Deauth rogue clients | `deauthSiteWirelessClientsConnectedToARogue` | `mistapi.api.v1.sites.rogues` |

The implementation must verify these organization operation IDs before code uses client control helpers:

- `reauthOrgDot1xWirelessClient`
- `reauthOrgDot1xWiredClient`

## Safety Contract

- The operation sends no request until the operator types the exact normalized target again.
- The confirmation must match the target shown to the operator.
- A mismatch sends no request.
- `--dry-run` prints the request that would be sent and sends nothing.
- The operation is destructive and must be excluded from every automated test pass.

## Normalization Contract

- MAC and BSSID values normalize to lowercase colon-free form.
- Tests must cover colon separated, hyphen separated, and dotted input forms.
- Invalid target input must stop before confirmation.

## Existing Helper Review Contract

Implementation must read `src/device/prompt_utils.py` before coding.
That file contains `_normalize_mac()` and device lookup patterns that compare normalized MAC values.
The feature normalizer must add dotted input support because the existing helper does not remove dots.
Implementation must search `src/device/` for any newer client lookup helper before coding.

## Logging Contract

- The operation writes `data/ClientSessionControlLog.csv`.
- The file has one row per request attempt.
- Each row includes the action, target, and result.
- The log must not include API tokens, passwords, or unrelated personal data.

## Test Contract

Required proof:

- No request is sent before exact confirmation.
- Dry run sends no request and prints the request preview.
- Three common MAC input forms normalize to lowercase colon-free form.
- One CSV row is written per request attempt.
- Destructive registration is excluded from every automated test pass.

## Release Note Contract

Implementation must add `changelog.d/issue-3566-client-coa-disconnect.md`.
This planning step must not create it because it is outside the owned path.

## Out of Scope For This Planning Step

- Editing repository wiring files
- Editing `.specify/feature.json`
- Creating the release note fragment outside the owned specification path
- Running destructive Mist requests
