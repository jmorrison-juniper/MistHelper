# uninviteMspAdmin

> uninviteMspAdmin

## HTTP

`DELETE /api/v1/msps/{msp_id}/invites/{invite_id}`

## Description

Delete admin invite

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| invite_id | string | Yes |  |

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

`mistapi.api.v1.msps.admins.uninviteMspAdmin()`

## Usage Context

Cancels a pending MSP admin invitation before it is accepted. Use this to revoke invitations sent to incorrect email addresses or when access is no longer needed.

## Gotchas

- Only pending (unaccepted) invitations can be cancelled. Use the admin revoke endpoint for active admins.

## Related Endpoints

- [POST_msps_msp_id_invites.md](POST_msps_msp_id_invites.md) — Create an invitation
- [PUT_msps_msp_id_invites_invite_id.md](PUT_msps_msp_id_invites_invite_id.md) — Update a pending invitation
- [GET_msps_msp_id_admins.md](GET_msps_msp_id_admins.md) — List all admins and invitations

## MistHelper Notes

Not currently used by MistHelper directly.
