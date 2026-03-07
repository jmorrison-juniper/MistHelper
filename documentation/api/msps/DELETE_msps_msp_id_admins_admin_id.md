# revokeMspAdmin

> revokeMspAdmin

## HTTP

`DELETE /api/v1/msps/{msp_id}/admins/{admin_id}`

## Description

This removes all privileges this admin has against the MSP. This goes deep all the way to the sites

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| admin_id | string | Yes |  |

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

`mistapi.api.v1.msps.admins.revokeMspAdmin()`

## Usage Context

Revokes an MSP administrator's access. The admin loses all MSP-level management capabilities immediately. Use this when offboarding personnel or revoking compromised accounts.

## Gotchas

- Cannot revoke the last remaining super-admin — at least one super-admin must exist.
- Revocation is immediate; the admin's active sessions may be terminated.

## Related Endpoints

- [GET_msps_msp_id_admins.md](GET_msps_msp_id_admins.md) — List all admins to verify before deletion
- [POST_msps_msp_id_invites.md](POST_msps_msp_id_invites.md) — Re-invite if needed

## MistHelper Notes

Not currently used by MistHelper directly.
