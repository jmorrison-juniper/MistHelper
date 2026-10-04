# Wiring Manifest: Client CoA Disconnect

## Summary

Menu 286 adds a destructive client session control operation for helpdesk use.
The operation covers wireless reauthenticate, wired reauthenticate, disconnect, unauthorize guest, and deauth rogue clients.
Repository wiring is deferred to the integration pull request.

## Owned Paths

- `specs/3566-client-coa-disconnect/**`
- `src/mist/resources/device/client_session_control/**`
- `tests/unit/device/client_session_control/**`
- `changelog.d/issue-3566-client-coa-disconnect.md`

## Deferred Repository Wiring

Registration is deferred to the integration pull request.
This feature branch must not edit repository wiring files.
README, menu documentation, and primary-key strategy handling are also deferred to the integration pull request.
The primary-key strategy item is expected to be recorded as not applicable unless the integration review requires a registry policy entry, because this feature sends destructive control requests and does not export or collect Mist API data.

Deferred files named by the contract:

- `MistHelper.py`
- `src/foundation/support/utils/operation_registry.py`
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
- `README.md`
- `.github/copilot-instructions.md`
- `agents.md`
- `documentation/menu_reference.md`
- `documentation/wiki/**`
- `documentation/operator-guide.md`
- `web_portal/**`
- `scripts/**`
- `tests/guardrails/**`
- `CHANGELOG.md`
- `.specify/feature.json`

Integration pull request responsibilities:

- Register menu 286 in the appropriate repository wiring file.
- Mark menu 286 as destructive.
- Exclude menu 286 from safe, interactive safe, and fast automated tests.
- Update README and menu documentation.
- Record primary-key strategy handling as not applicable or add the required registry policy entry.

## Menu Registration

- Menu number: 286
- Name: Client CoA, reauthentication, and disconnect
- Category: `destructive`
- Destructive flag: `true`
- Supports fast: `false`
- Handler import: `from src.mist.resources.device.client_session_control.handler import ClientSessionControl`
- Handler attribute: `ClientSessionControl.run`
- Handler package: `src/mist/resources/device/client_session_control/`
- Handler class: `ClientSessionControl`
- Entry point: static `run()`
- Skip reason: Destructive client session control requires typed target confirmation and must not run in automated safe or fast tests.

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 286 | Client CoA, reauthentication, and disconnect | `src.mist.resources.device.client_session_control.handler` | `ClientSessionControl.run` | destructive | Destructive client session control requires typed target confirmation and must not run in automated safe or fast tests. | True | False |

## OperationRegistry comment

One `# WHY:` paragraph for the registry entry:

```python
# WHY: Client CoA, reauthentication, disconnect, guest unauthorize, and rogue client deauth can drop live sessions, so menu 286 is destructive and requires typed target confirmation plus dry-run support.
```

Registration is deferred to the integration pull request.

## Primary key strategies

Not applicable.
Menu 286 sends destructive client session control requests and writes a local audit CSV.
It does not export Mist API collection data and does not require a primary-key strategy.

```python
# No ENDPOINT_PRIMARY_KEY_STRATEGIES entry is required for menu 286.
```

## copilot-instructions category table

The `destructive` category row gains menu `286`.
The destructive count increases by one.
The menu list adds `286` to the existing destructive set.

## Import line for MistHelper.py

```python
from src.mist.resources.device.client_session_control.handler import ClientSessionControl  # Menu 286 (issue #3566) -- destructive client session control handler.
```

## Dry Run Wiring Contract

The menu handler lambda must pass the global CLI dry run value to the handler.
This follows the menu 161 pattern that accepts `dry_run=False` in the lambda.
It also keeps the menu 207 destructive confirmation pattern.

Required handler lambda pattern:

```text
handler=lambda dry_run=False: ClientSessionControl.run(
    MainEntrypoint.context.apisession,
    ConfigUtils.get_cached_or_prompted_org_id(),
    dry_run=dry_run,
)
```

Implementation must adjust imports and dependency names to match the final package.
The handler must not read MistHelper global arguments directly.
The dry run value must reach `ClientSessionControl.run()` as the `dry_run` argument.

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

The implementation verified these organization operation IDs before code used client control helpers:

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
- Tests must cover colon separated, hyphen separated, dotted, and bare input forms.
- Invalid target input must stop before confirmation.

## Existing Helper Review Contract

Implementation read `src/mist/resources/device/prompt_utils.py` before coding.
That file contains `_normalize_mac()` and device lookup patterns that compare normalized MAC values.
The feature normalizer adds dotted input support because the existing helper does not remove dots.
Implementation searched `src/mist/resources/device/` for any newer client lookup helper before coding.

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
- Bare MAC input normalizes to lowercase colon-free form.
- One CSV row is written per request attempt.
- Destructive registration is excluded from every automated test pass.

## Release Note Contract

Implementation must add `changelog.d/issue-3566-client-coa-disconnect.md`.
The release note fragment must use one `### Added` heading and one bullet that names issue #3566.

## Out of Scope For This Feature Branch

- Editing repository wiring files
- Editing `.specify/feature.json`
- Running destructive Mist requests
