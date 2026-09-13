# deleteMspSso

> deleteMspSso

## HTTP

`DELETE /api/v1/msps/{msp_id}/ssos/{sso_id}`

## Description

Delete MSP SSO Config

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| sso_id | string | Yes |  |

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

`mistapi.api.v1.msps.sso.deleteMspSso()`

## Usage Context

Deletes an MSP SSO configuration, removing SAML-based authentication for MSP administrators. Admins who were using SSO will need to use local credentials or be re-invited.

## Gotchas

- Deleting the SSO config immediately prevents SSO-based login. Ensure admins have alternative access.
- If SSO was the only authentication method, admins may be locked out.

## Related Endpoints

- [GET_msps_msp_id_ssos.md](GET_msps_msp_id_ssos.md) — List remaining SSO configs
- [POST_msps_msp_id_ssos.md](POST_msps_msp_id_ssos.md) — Create a replacement SSO config
- [POST_msps_msp_id_invites.md](POST_msps_msp_id_invites.md) — Re-invite admins with local credentials if needed

## MistHelper Notes

Not currently used by MistHelper directly.
