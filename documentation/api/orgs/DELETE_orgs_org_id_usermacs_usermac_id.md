# deleteOrgUserMac

> deleteOrgUserMac

## HTTP

`DELETE /api/v1/orgs/{org_id}/usermacs/{usermac_id}`

## Description

Delete Org User MAC

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| usermac_id | string | Yes |  |

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

`mistapi.api.v1.orgs.user_macs.deleteOrgUserMac()`

## Usage Context

Deletes a user MAC address label from the organization.

## Gotchas

- The MAC address will no longer be labeled and may reappear as unknown.

## Related Endpoints

- [GET_orgs_org_id_usermacs.md](GET_orgs_org_id_usermacs_search.md) — List user MACs
- [POST_orgs_org_id_usermacs.md](POST_orgs_org_id_usermacs.md) — Create user MAC

## MistHelper Notes

Not currently used by MistHelper directly.
