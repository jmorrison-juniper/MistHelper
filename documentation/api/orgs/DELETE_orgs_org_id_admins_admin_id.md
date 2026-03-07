# revokeOrgAdmin

> revokeOrgAdmin

## HTTP

`DELETE /api/v1/orgs/{org_id}/admins/{admin_id}`

## Description

This removes all privileges this admin has against the org

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
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

`mistapi.api.v1.orgs.admins.revokeOrgAdmin()`

## Usage Context

Removes an administrator from an organization.

## Gotchas

- Cannot delete the last remaining admin. Verify admin permissions before removal.

## Related Endpoints

- [GET_orgs_org_id_admins.md](GET_orgs_org_id_admins.md) — List admins
- [POST_orgs_org_id_admins.md](POST_orgs_org_id_admins.md) — Invite admin

## MistHelper Notes

Used by MistHelper via `listOrgAdmins` in Menu 55 (Admins export).
