# Contract: Client Session Control

## Handler contract

The handler class is `ClientSessionControl`.
The entry point is static `run()`.
The implementation package is `src/device/client_session_control/`.

Recommended callable shape:

```text
ClientSessionControl.run(apisession, org_id, dry_run=False)
```

The method must keep the parameter count at five or fewer.
The method must not read MistHelper global arguments directly.

## Menu contract

This branch supplies the handler package and wiring manifest for menu 286.
Menu 286 must be registered as destructive in the integration pull request.
The operation must be excluded from safe, interactive safe, and fast automated test passes after wiring lands.
Repository registration is deferred to `wiring.md` for this branch.
README, menu documentation, and primary-key strategy handling are also deferred to the integration pull request.

## Dry run contract

The MistHelper handler lambda must accept `dry_run=False`.
It must pass `dry_run` to `ClientSessionControl.run()`.
This follows the menu 161 pattern and keeps the global `--dry-run` flag effective.
The operation must also keep a typed destructive confirmation pattern like menu 207.

Required wiring shape:

```text
handler=lambda dry_run=False: ClientSessionControl.run(
    MainEntrypoint.context.apisession,
    ConfigUtils.get_cached_or_prompted_org_id(),
    dry_run=dry_run,
)
```

When `dry_run` is true, the operation must not call a Mist SDK function.
It must print the SDK operation ID, site, action, and target that it would call.
It must write one CSV row with result `dry_run`.

## Input contract

The operation must ask for inputs in this order:

1. Site
2. Action
3. Client MAC or rogue BSSID
4. Exact confirmation by typing the normalized target again

The target must normalize to lowercase colon-free form.
The target must have exactly 12 hexadecimal characters after normalization.
The confirmation must normalize with the same rule.
The confirmation must match the normalized target exactly.

## Action contract

| Action key | Target | Mist operation ID | SDK function |
| - | - | - | - |
| `wireless_reauthenticate` | Client MAC | `reauthSiteDot1xWirelessClient` | `mistapi.api.v1.sites.clients.reauthSiteDot1xWirelessClient` |
| `wired_reauthenticate` | Client MAC | `reauthSiteDot1xWiredClient` | `mistapi.api.v1.sites.wired_clients.reauthSiteDot1xWiredClient` |
| `disconnect` | Client MAC | `disconnectSiteWirelessClient` | `mistapi.api.v1.sites.clients.disconnectSiteWirelessClient` |
| `unauthorize_guest` | Client MAC | `unauthorizeSiteWirelessClient` | `mistapi.api.v1.sites.clients.unauthorizeSiteWirelessClient` |
| `deauth_rogue_clients` | Rogue BSSID | `deauthSiteWirelessClientsConnectedToARogue` | `mistapi.api.v1.sites.rogues.deauthSiteWirelessClientsConnectedToARogue` |

## Output contract

The operation must print one clear final result:

- Success
- Dry run
- Confirmation failed
- Validation failed
- Mist failure

The operation must write one row to `data/ClientSessionControlLog.csv` for each attempt.
The row must include action, target, and result.
The row must not include secrets.

## Test contract

Unit tests must prove these rules:

1. No Mist request is sent before exact confirmation.
2. Confirmation mismatch sends no Mist request.
3. `--dry-run` sends no Mist request.
4. Colon separated input normalizes correctly.
5. Hyphen separated input normalizes correctly.
6. Dotted input normalizes correctly.
7. Invalid input stops early.
8. One CSV row is written per attempt.
9. The wiring manifest marks menu 286 as destructive and excluded from automated safe tests.
