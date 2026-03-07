# updateOrgPskPortalTemplate

> updateOrgPskPortalTemplate

## HTTP

`PUT /api/v1/orgs/{org_id}/pskportals/{pskportal_id}/portal_template`

## Description

Update Org Psk Portal Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| pskportal_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "psk_portal_template",
  "type": "object",
  "properties": {
    "portal_template": {
      "title": "psk_portal_template_setting",
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
          "type": [
            "string",
            "null"
          ],
          "description": "Custom logo with \"data:image/png;base64,\" format.  default null, uses Juniper Mist Logo"
        },
        "poweredBy": {
          "type": "boolean",
          "description": "Whether to hide \"Powered by Juniper Mist\" and email footers",
          "default": false
        },
        "tos": {
          "type": "boolean",
          "description": "Whether to show Terms of Service"
        },
        "tosAcceptLabel": {
          "type": "string",
          "description": "Terms of Service accept button label",
          "default": "I accept the Terms of Service"
        },
        "tosError": {
          "type": "string",
          "description": "Terror message for not accepting tos",
          "default": "Please review and accept the Terms of Service"
        },
        "tosLink": {
          "type": "string",
          "default": "Terms of Service"
        },
        "tosText": {
          "type": "string",
          "description": "terms and service text displayed in footer if tos is enabled",
          "default": "<< provide your Terms of Service here >>"
        },
        "tosUrl": {
          "type": "string",
          "description": "customized url for defining terms of service",
          "examples": [
            "https://company.com/wifi-policy"
          ]
        }
      }
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

`mistapi.api.v1.orgs.psk_portals.updateOrgPskPortalTemplate()`

## Usage Context

Updates the portal template for a specific PSK portal.

## Gotchas

- Portal templates define the self-service PSK provisioning UI.

## Related Endpoints

- [GET_orgs_org_id_pskportals_id.md](GET_orgs_org_id_pskportals_id.md) — Get PSK portal
- [PUT_orgs_org_id_pskportals_pskportal_id.md](PUT_orgs_org_id_pskportals_pskportal_id.md) — Update PSK portal

## MistHelper Notes

Not currently used by MistHelper directly.
