# deleteMspSsoRole

> deleteMspSsoRole

## HTTP

`DELETE /api/v1/msps/{msp_id}/ssoroles/{ssorole_id}`

## Description

Delete MSP SSO Roles

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| ssorole_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.msps.sso_roles.deleteMspSsoRole()`

## Usage Context

Deletes an SSO role mapping. Administrators matching this role will no longer receive automatic privilege assignment via SSO and may lose access or fall back to a default role.

## Gotchas

- Ensure a fallback role exists or re-invite admins with explicit roles before removing SSO role mappings.

## Related Endpoints

- [GET_msps_msp_id_ssoroles.md](GET_msps_msp_id_ssoroles.md) — List remaining role mappings
- [POST_msps_msp_id_ssoroles.md](POST_msps_msp_id_ssoroles.md) — Create a replacement role mapping

## MistHelper Notes

Not currently used by MistHelper directly.
