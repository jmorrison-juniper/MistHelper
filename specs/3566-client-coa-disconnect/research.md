# Research: Client CoA Disconnect

## Decision: Use site-scoped Mist endpoints for menu 286

**Rationale**: The feature flow starts with site selection.
The required actions all have site-scoped operation IDs in `documentation/mist-api-openapi3json.json` and in worktree `mistapi` 0.64.0.
The menu will use these calls:

| Action | OpenAPI operation ID | SDK module | Signature |
| - | - | - | - |
| Wireless reauthenticate | `reauthSiteDot1xWirelessClient` | `mistapi.api.v1.sites.clients` | `(mist_session, site_id, client_mac)` |
| Wired reauthenticate | `reauthSiteDot1xWiredClient` | `mistapi.api.v1.sites.wired_clients` | `(mist_session, site_id, client_mac)` |
| Disconnect wireless client | `disconnectSiteWirelessClient` | `mistapi.api.v1.sites.clients` | `(mist_session, site_id, client_mac)` |
| Unauthorize guest | `unauthorizeSiteWirelessClient` | `mistapi.api.v1.sites.clients` | `(mist_session, site_id, client_mac)` |
| Deauth rogue clients | `deauthSiteWirelessClientsConnectedToARogue` | `mistapi.api.v1.sites.rogues` | `(mist_session, site_id, rogue_bssid)` |

**Alternatives considered**:

- Use organization-scoped reauthentication calls.
  This does not match the site-first operator flow.
- Use direct HTTP calls.
  The constitution prohibits direct Mist HTTP when a `mistapi` method exists.

## Decision: Verify all requested operation IDs before implementation

**Rationale**: The worktree OpenAPI file contains all required operation IDs:

| Operation ID | Method and path |
| - | - |
| `reauthOrgDot1xWiredClient` | `POST /api/v1/orgs/{org_id}/wired_clients/{client_mac}/coa` |
| `reauthSiteDot1xWiredClient` | `POST /api/v1/sites/{site_id}/wired_clients/{client_mac}/coa` |
| `reauthOrgDot1xWirelessClient` | `POST /api/v1/orgs/{org_id}/clients/{client_mac}/coa` |
| `reauthSiteDot1xWirelessClient` | `POST /api/v1/sites/{site_id}/clients/{client_mac}/coa` |
| `disconnectSiteWirelessClient` | `POST /api/v1/sites/{site_id}/clients/{client_mac}/disconnect` |
| `unauthorizeSiteWirelessClient` | `POST /api/v1/sites/{site_id}/clients/{client_mac}/unauthorize` |
| `deauthSiteWirelessClientsConnectedToARogue` | `POST /api/v1/sites/{site_id}/rogues/{rogue_bssid}/deauth_clients` |

The worktree virtual environment reports `mistapi` 0.64.0 and contains all seven functions.
The ambient interpreter reports `mistapi` 0.63.3 and is not valid for this feature.
Implementation must use `.venv` or a bootstrapped worktree environment.

**Alternatives considered**:

- Trust documentation only.
  This risks a runtime failure when the installed SDK lacks a function.
- Trust the ambient interpreter.
  This conflicts with the worktree environment and found an older SDK.

## Decision: Normalize targets to lowercase colon-free form with strict validation

**Rationale**: The existing `src/device/prompt_utils.py` helper `_normalize_mac()` strips colons and hyphens, then lowercases the value.
The feature must also support dotted input.
Implementation must use a feature normalizer that accepts colon separated, hyphen separated, dotted, and bare forms, then rejects any value that does not produce exactly 12 hexadecimal characters.

**Alternatives considered**:

- Import the private `_normalize_mac()` helper directly.
  It does not support dotted input and its private name makes the contract weak.
- Accept Mist errors for invalid input.
  This would violate validate early and return early safety rules.

## Decision: Make `--dry-run` a dispatcher parameter

**Rationale**: MistHelper CLI builds a candidate keyword dictionary that includes `dry_run`.
Menu 161 shows the needed lambda shape with `handler=lambda dry_run=False: ...launch_convert_single(dry_run=dry_run)`.
Menu 207 shows the destructive menu pattern and typed confirmation pattern.
Menu 286 wiring must combine both patterns:

```text
handler=lambda dry_run=False: ClientSessionControl.run(
    MainEntrypoint.context.apisession,
    ConfigUtils.get_cached_or_prompted_org_id(),
    dry_run=dry_run,
)
```

**Alternatives considered**:

- Read the global `args.dry_run` inside the feature package.
  This couples the package to `MistHelper.py` globals.
- Use only typed `DRY-RUN` confirmation.
  The requirement states that `--dry-run` must work.

## Decision: Write one CSV audit row per request attempt

**Rationale**: The specification requires `data/ClientSessionControlLog.csv` with one row for each attempt.
The row must include at least action, target, and result.
Recommended fields add site, target type, dry run state, confirmation status, SDK operation ID, and timestamp.
The log must not include tokens, passwords, or unrelated personal data.

**Alternatives considered**:

- Use the standard data export backend.
  This feature is an audit trail for a destructive attempt, not an API export result.
- Log only successful requests.
  The spec requires confirmation failures and dry runs to be traceable.

## Decision: Use Juniper skill research for session control context

**Rationale**: The skill sources show why the action set is operationally destructive.
Mist dynamic authorization can reauthenticate or disconnect clients.
Guest reconnect and reauthorize workflows can change access state.
Rogue client deauth sends deauthentication frames to remove rogue clients.
Junos 802.1X CoA and Disconnect-Request can change or end live sessions.

Skill citations:

- `juniper-mist-wireless/05-wlan-security-radius-and-psk/04-radius-attributes-dynamic-vlan-and-coa.md`
- `juniper-mist-wireless/05-wlan-security-radius-and-psk/05-wlan-threat-client-and-pci-controls.md`
- `juniper-mist-wireless/07-guest-portal/04-guest-authorization-reconnect-and-failure-repair.md`
- `juniper-8021x-access-control/02-radius-attributes-and-dynamic-enforcement/05-coa-disconnect-and-port-bounce.md`

**Alternatives considered**:

- Treat these actions as routine API calls.
  This hides the access impact and weakens the confirmation design.
