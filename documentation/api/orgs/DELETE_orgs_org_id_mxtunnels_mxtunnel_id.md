# deleteOrgMxTunnel

> deleteOrgMxTunnel

## HTTP

`DELETE /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}`

## Description

Delete Org MxTunnel

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxtunnel_id | string | Yes |  |

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

`mistapi.api.v1.orgs.mxtunnels.deleteOrgMxTunnel()`

## Usage Context

Deletes a Mist tunnel configuration from the organization.

## Gotchas

- Active tunnels are terminated immediately.

## Related Endpoints

- [GET_orgs_org_id_mxtunnels.md](GET_orgs_org_id_mxtunnels.md) — List tunnels
- [POST_orgs_org_id_mxtunnels.md](POST_orgs_org_id_mxtunnels.md) — Create tunnel

## MistHelper Notes

Not currently used by MistHelper directly.
