# deleteOrgAptemplate

> deleteOrgAptemplate

## HTTP

`DELETE /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id}`

## Description

Delete existing AP Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| aptemplate_id | string | Yes |  |

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

`mistapi.api.v1.orgs.ap_templates.deleteOrgAptemplate()`

## Usage Context

Deletes an AP template from the organization.

## Gotchas

- Sites using this template lose their AP template assignment.

## Related Endpoints

- [GET_orgs_org_id_aptemplates.md](GET_orgs_org_id_aptemplates.md) — List AP templates
- [POST_orgs_org_id_aptemplates.md](POST_orgs_org_id_aptemplates.md) — Create template

## MistHelper Notes

Used by MistHelper via `listOrgAptemplates` in Menu 38 (AP templates export).
