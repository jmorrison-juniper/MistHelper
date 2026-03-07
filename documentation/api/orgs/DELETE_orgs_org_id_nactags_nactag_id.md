# deleteOrgNacTag

> deleteOrgNacTag

## HTTP

`DELETE /api/v1/orgs/{org_id}/nactags/{nactag_id}`

## Description

Delete Org NAC Tag

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| nactag_id | string | Yes |  |

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

`mistapi.api.v1.orgs.nac_tags.deleteOrgNacTag()`

## Usage Context

Deletes a NAC tag from the organization.

## Gotchas

- Ensure no NAC rules reference this tag before deleting.

## Related Endpoints

- [GET_orgs_org_id_nactags.md](GET_orgs_org_id_nactags.md) — List tags
- [POST_orgs_org_id_nactags.md](POST_orgs_org_id_nactags.md) — Create tag

## MistHelper Notes

Used by MistHelper via `listOrgNacTags` for NAC exports.
