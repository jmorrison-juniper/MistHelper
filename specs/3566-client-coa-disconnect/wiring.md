# Wiring Manifest: Client CoA Disconnect

## Summary

Menu 286 adds a destructive client session control operation for helpdesk use. The operation covers wireless reauthenticate, wired reauthenticate, disconnect, unauthorize guest, and deauth rogue clients.

## Owned Paths

- `specs/3566-client-coa-disconnect/**`
- Planned implementation package: `src/device/client_session_control/`
- Planned release note fragment: `changelog.d/issue-3566-client-coa-disconnect.md`

## Deferred Repository Wiring

Registration is deferred. This specification step must not edit repository wiring files.

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

## Safety Contract

- The operation sends no request until the operator types the exact normalized target again.
- The confirmation must match the target shown to the operator.
- A mismatch sends no request.
- `--dry-run` prints the request that would be sent and sends nothing.
- The operation is destructive and must be excluded from every automated test pass.

## Normalization Contract

- MAC and BSSID values normalize to lowercase colon-free form.
- Tests must cover colon separated, hyphen separated, and dotted input forms.

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

## Out of Scope For This Specification Step

- Editing repository wiring files
- Editing `.specify/feature.json`
- Creating the release note fragment outside the owned specification path
- Running destructive Mist requests
