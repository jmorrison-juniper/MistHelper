# Research: SSR registration commands

## Mist API operation

OpenAPI operation `getOrg128TRegistrationCommands` uses `GET /api/v1/orgs/{org_id}/128routers/register_cmd`.

Path parameters:

- `org_id`: required string with UUID format.

Query parameters:

- `ttl`: optional integer. It is the duration, in days, for the token to stay valid. The documented range is `1` through `365`. The default is `365`.

Successful response shape:

```json
{
  "conductor_cmd": "register mist ******",
  "registration_code": "******",
  "router_shell_cmd": "128agent register --registration-code ******"
}
```

The installed `mistapi` package has no `getOrg128TRegistrationCommands` helper under `mistapi.api.v1.orgs`. The client will call `apisession.mist_get("/api/v1/orgs/{org_id}/128routers/register_cmd")`.

## Skill citations

- `juniper-mist-wan/08-wan-edge-device-operations/01-static-ssr-onboarding-and-secure-conductor.md`: static-only WAN Edge onboarding can need local console commands before the device reaches Mist. Secure Conductor Onboarding uses Mist-side onboarding values and verification.
- `juniper-ssr-wan-edge/02-mist-objects/02-onboarding-assignment-and-ztp-workflow.md`: SSR onboarding starts with claim and assignment. Manual onboarding can use local access when DHCP-based ZTP is not enough.
- `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`: Mist API calls use `/api/v1/{scope}/{scope_id}/...` with token authentication.
- `juniper-mist-automation/02-tokens-and-response-codes/02-http-response-codes-and-the-first-call.md`: status codes `200`, `400`, `401`, `403`, `404`, and `429` direct error handling.

## Decision

The operation keeps the registration code on the console and out of logs. It writes a file only after explicit consent. This matches the ZTP password pattern in `src/mist/resources/device/_utility_commands_action.py`, where the code logs render state but excludes the credential value.
