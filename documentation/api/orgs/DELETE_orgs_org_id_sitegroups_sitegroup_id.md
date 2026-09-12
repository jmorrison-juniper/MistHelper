# deleteOrgSiteGroup

> deleteOrgSiteGroup

## HTTP

`DELETE /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}`

## Description

Delete Org Site Group

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sitegroup_id | string | Yes |  |

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

`mistapi.api.v1.orgs.sitegroups.deleteOrgSiteGroup()`

## Usage Context

Deletes a site group from the organization.

## Gotchas

- Sites in the group are not affected; they simply lose the group association.

## Related Endpoints

- [GET_orgs_org_id_sitegroups.md](GET_orgs_org_id_sitegroups.md) — List groups
- [POST_orgs_org_id_sitegroups.md](POST_orgs_org_id_sitegroups.md) — Create group

## MistHelper Notes

Not currently used by MistHelper directly.
