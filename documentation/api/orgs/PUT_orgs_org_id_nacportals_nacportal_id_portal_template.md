# updateOrgNacPortalTemplate

> updateOrgNacPortalTemplate

## HTTP

`PUT /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/portal_template`

## Description

Update Org NAC Portal Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| nacportal_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "nac_portal_template",
  "type": "object",
  "properties": {
    "alignment": {
      "type": "string",
      "description": "defines alignment on portal. enum: `center`, `left`, `right`"
    },
    "color": {
      "type": "string",
      "default": "#1074bc"
    },
    "logo": {
      "type": "string",
      "description": "Custom logo custom logo with \"data:image/png;base64,\" format. default null, uses Juniper Mist Logo."
    },
    "poweredBy": {
      "type": "boolean",
      "description": "Whether to hide \"Powered by Juniper Mist\" and email footers",
      "default": false
    }
  }
}
```

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

`mistapi.api.v1.orgs.nac_portals.updateOrgNacPortalTemplate()`

## Usage Context

Updates the portal template for a specific NAC portal.

## Gotchas

- Portal templates define the look and feel of the NAC captive portal.

## Related Endpoints

- [GET_orgs_org_id_nacportals_nacportal_id.md](GET_orgs_org_id_nacportals_nacportal_id.md) — Get NAC portal
- [PUT_orgs_org_id_nacportals_nacportal_id.md](PUT_orgs_org_id_nacportals_nacportal_id.md) — Update NAC portal

## MistHelper Notes

Not currently used by MistHelper directly.
