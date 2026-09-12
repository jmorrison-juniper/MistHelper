# deleteOrgTemplate

> deleteOrgTemplate

## HTTP

`DELETE /api/v1/orgs/{org_id}/templates/{template_id}`

## Description

Delete Org Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| template_id | string | Yes |  |

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

`mistapi.api.v1.orgs.wlan_templates.deleteOrgTemplate()`

## Usage Context

Deletes a WLAN template from the organization.

## Gotchas

- WLANs associated with this template will lose their template configuration.

## Related Endpoints

- [GET_orgs_org_id_templates.md](GET_orgs_org_id_templates.md) — List templates
- [POST_orgs_org_id_templates.md](POST_orgs_org_id_templates.md) — Create template

## MistHelper Notes

Used by MistHelper via `listOrgWlanTemplates` in Menu 35.
