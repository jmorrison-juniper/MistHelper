# deleteOrgGatewayTemplate

> deleteOrgGatewayTemplate

## HTTP

`DELETE /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}`

## Description

Delete Organization Gateway Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| gatewaytemplate_id | string | Yes |  |

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

`mistapi.api.v1.orgs.gateway_templates.deleteOrgGatewayTemplate()`

## Usage Context

Deletes a gateway template from the organization.

## Gotchas

- Sites using this template lose their gateway template assignment.

## Related Endpoints

- [GET_orgs_org_id_gatewaytemplates.md](GET_orgs_org_id_gatewaytemplates.md) — List templates
- [POST_orgs_org_id_gatewaytemplates.md](POST_orgs_org_id_gatewaytemplates.md) — Create template

## MistHelper Notes

Used by MistHelper via `listOrgGatewayTemplates` in Menus 4, 26, 28, 35, 111.
