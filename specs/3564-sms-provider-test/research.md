# Research: Test the guest portal SMS provider

## R1: Guest portal SMS use

Decision: The operation supports guest portal SMS code authorization for `Custom guest portal` WLANs.

Rationale: The Juniper Mist wireless skill states that the `Authorization` area of `Guest Portal Options` can enable SMS confirmation. It also states that SMS confirmation needs reliable reachability to the messaging channel before the guest has general network access. Source: `juniper-mist-wireless/07-guest-portal/02-custom-guest-portal-fields-text-layout-and-authorization.md`.

Alternatives considered: A generic guest portal health check was rejected because issue #3564 asks for provider credential tests only.

## R2: Guest failure repair context

Decision: The operation reports SMS provider status as one guest-portal failure input, not as proof that client association, DNS, redirect, VLAN, or firewall policy works.

Rationale: The Juniper Mist wireless skill says a guest WLAN failure can come from client association, DNS, redirect, portal reachability, authorization, VLAN assignment, or firewall policy. Source: `juniper-mist-wireless/07-guest-portal/04-guest-authorization-reconnect-and-failure-repair.md`.

Alternatives considered: A full guest-client repair flow was rejected because it would cross the issue boundary.

## R3: API call structure

Decision: The client uses the regional Mist API session and sends JSON to utility endpoints under `/api/v1/utils/`.

Rationale: The Juniper Mist automation skill states that Mist API calls use JSON and that every endpoint belongs to one regional cloud host. Source: `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`.

Alternatives considered: Direct `requests` calls were rejected because the existing `mistapi` session already owns the host and token.

## R4: OpenAPI operation shapes

Decision: The feature uses three `POST` endpoints with no path parameters and no query parameters.

Rationale: `documentation/mist-api-openapi3json.json` defines these operations:

| operationId | Method | Path | Required body fields | Responses |
| - | - | - | - | - |
| `testSiteWlanTwilioSetup` | `POST` | `/api/v1/utils/test_twilio` | `from`, `to`, `twilio_auth_token`, `twilio_sid` | `200`, `400`, `401`, `403`, `404`, `429` |
| `testSiteWlanSmsGlobal` | `POST` | `/api/v1/utils/test_smsglobal` | `smsglobal_api_key`, `smsglobal_api_secret`, `to` | `200`, `400`, `401`, `403`, `404`, `429` |
| `testSiteWlanTelstraSetup` | `POST` | `/api/v1/utils/test_telstra` | `telstra_client_id`, `telstra_client_secret`, `to` | `200`, `400`, `401`, `403`, `404`, `429` |

Alternatives considered: Site-scoped WLAN endpoints were rejected because the OpenAPI paths contain no site identifier.

## R5: Installed SDK availability

Decision: The client calls the installed SDK functions instead of raw `mist_post` paths.

Rationale: The installed SDK exposes these functions:

- `mistapi.api.v1.utils.test_twilio.testSiteWlanTwilioSetup`
- `mistapi.api.v1.utils.test_smsglobal.testSiteWlanSmsGlobal`
- `mistapi.api.v1.utils.test_telstra.testSiteWlanTelstraSetup`

Alternatives considered: A raw `apisession.mist_post` fallback was rejected for the primary path because the SDK functions exist.

## R6: Related skills outside the feature boundary

Decision: The feature does not implement switch utility, WAN onboarding, or NAC identity-provider changes.

Rationale: `juniper-mist-wired/09-wired-visibility-and-switch-management/03-switch-utilities-roles-remote-shell-and-replacement.md`, `juniper-mist-wan/08-wan-edge-device-operations/01-static-ssr-onboarding-and-secure-conductor.md`, and `juniper-access-assurance-nac/04-certificates-identity/02-public-idp-and-ldaps-integration.md` describe related troubleshooting domains, but they do not change SMS provider test requirements.

Alternatives considered: Adding cross-domain checks was rejected because issue #3564 is one guest portal SMS provider test.
