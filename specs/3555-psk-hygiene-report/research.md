# Research: PSK Hygiene Report

## Decision: use installed `mistapi` organization endpoints

Use a client module that wraps these installed SDK objects:

- `mistapi.api.v1.orgs.psks.listOrgPsks`
- `mistapi.api.v1.orgs.wlans.listOrgWlans`
- `mistapi.api.v1.orgs.templates.listOrgTemplates`

The OpenAPI facts are:

- `listOrgPsks`: `GET /api/v1/orgs/{org_id}/psks`. It has path parameter `org_id`, query parameters `name`, `ssid`, `role`, `limit`, and `page`, and returns an array of `psk`.
- `listOrgWlans`: `GET /api/v1/orgs/{org_id}/wlans`. It has path parameter `org_id`, query parameters `limit` and `page`, and returns an array of `wlan`.
- `listOrgTemplates`: `GET /api/v1/orgs/{org_id}/templates`. It has path parameter `org_id`, query parameters `limit` and `page`, and returns an array of `template`.

Rationale: The constitution requires `mistapi` when an installed SDK method exists. The coordinator confirmed all three SDK objects exist.

Alternatives considered: Direct HTTP calls were rejected because the SDK covers these endpoints. Reusing menu `44` directly was rejected because menu `274` must score rows, avoid prompts, and preserve a separate report boundary.

## Decision: keep Mist calls inside a client module

Create a client module under `src/mist/intelligence/reports/psk_hygiene/` that fetches PSKs, organization WLANs, and organization templates.

Rationale: The client boundary makes network access easy to fake in unit tests. It also keeps `PskHygieneReport.run()` focused on dependency resolution, logging, model calls, and export.

Alternatives considered: Calling `mistapi` from the model was rejected because the model must stay pure. Calling `mistapi` directly from `run()` was rejected because it makes tests harder and spreads pagination logic into the operation layer.

## Decision: keep scoring in pure model functions and dataclasses

Use a model module with dataclasses for raw PSK facts, WLAN references, report rows, and summary counts. Use pure functions to normalize SSIDs, detect findings, compute days remaining, and aggregate summary counts.

Rationale: Pure functions let tests cover expired keys, soon-to-expire keys, uncapped multi-use keys, pending rotations, and orphan SSIDs without the network.

Alternatives considered: A model class with mutable state was rejected because the scoring has no side effects. A dictionary-only model was rejected because dataclasses make field handling explicit and safer.

## Decision: detect PSK rotation by presence only

The report records `old_passphrase_present` as a Boolean. It never writes the old passphrase value.

Rationale: Mist PSK rotation preserves user connectivity while the key changes, but a pending old key can explain failed client authentication after a rotation. The report needs the state, not the secret. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-wireless\05-wlan-security-radius-and-psk\02-security-types-psk-and-personal-wlans.md` and `C:\Users\jmorrison\.copilot\skills\juniper-mist-aiops\10-troubleshooting-examples\02-authorization-dhcp-psk-and-radius-failures-with-the-assistant.md`.

Alternatives considered: Exporting the old passphrase was rejected because the specification forbids it. Hashing the old passphrase was rejected because it still creates secret-derived output.

## Decision: treat organization WLANs and organization templates as the WLAN scope

Build the SSID match set from organization WLAN records and WLAN definitions found in organization templates. Do not read site-level WLANs for this report.

Rationale: The feature scope is organization-level PSK hygiene. Self-provisioning PSK portals use organization-level WLANs for SSID selection and `Max Usage`. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-wireless\05-wlan-security-radius-and-psk\06-self-provisioning-roles-and-roaming-controls.md`.

Alternatives considered: Reading site-level WLANs was rejected because the specification states site-level WLANs are outside scope. Treating templates as out of scope was rejected because the required API list includes `listOrgTemplates`.

## Decision: report uncapped multi-use keys when no MAC binding and no maximum usage exists

Mark `uncapped_multi_use` when `mac`, `macs`, and `max_usage` are absent or empty.

Rationale: Mist supports limits on the number of devices that use a PSK. The `Max Usage` value is also a PSK portal control. A key with no binding and no cap can spread beyond its intended device set. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-wireless\05-wlan-security-radius-and-psk\02-security-types-psk-and-personal-wlans.md` and `C:\Users\jmorrison\.copilot\skills\juniper-mist-wireless\05-wlan-security-radius-and-psk\06-self-provisioning-roles-and-roaming-controls.md`.

Alternatives considered: Marking all keys without `mac` as risky was rejected because `max_usage` can provide the cap.

## Decision: use least-scope and read-only token guidance in documentation

Document that the operation reads configuration that can include secret fields, so operators must use the least required token scope and protect token files.

Rationale: Mist user and organization tokens should use the minimum scope needed. A read can still return PSKs, RADIUS secrets, and SNMP credentials. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-management\05-account-app-alerts-api-and-webhooks\02-user-tokens-alert-notifications-and-webhooks.md` and `C:\Users\jmorrison\.copilot\skills\juniper-mist-aiops\09-teams-app-and-mcp-server\03-mist-mcp-server-security-rules-and-prerequisites.md`.

Alternatives considered: Adding new token handling was rejected because the operation should use existing MistHelper session handling.

## Decision: do not weaken certificate or password controls

The report must not suggest changes to SSO, certificate, local password, or RadSec controls as part of PSK cleanup.

Rationale: Certificate and password controls protect authentication paths and must not be weakened to repair local access problems. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-management\03-security-and-access\02-password-policy-saml-and-certificates.md`.

Alternatives considered: Adding remediation advice for identity controls was rejected because this report only scores PSK hygiene.

## Decision: keep site variables outside scope

Do not inspect Mist site variables. State that site variables are outside PSK hygiene scope.

Rationale: Site variables render WAN and template values for sites. They do not define organization PSK hygiene findings. See `C:\Users\jmorrison\.copilot\skills\juniper-mist-wan\02-sites-templates-and-onboarding\01-site-variables-and-deployment-order.md`.

Alternatives considered: Searching site variables for SSID text was rejected because it would mix deployment variables with PSK state.
