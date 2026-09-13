# listOrgSiteTemplates

> listOrgSiteTemplates

## HTTP

`GET /api/v1/orgs/{org_id}/sitetemplates`

## Description

Get List of Org Site Templates

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "site_template",
    "type": "object",
    "properties": {
      "auto_upgrade": {
        "title": "site_template_auto_upgrade",
        "type": "object",
        "properties": {
          "day_of_week": {
            "type": "string",
            "description": "enum: `any`, `fri`, `mon`, `sat`, `sun`, `thu`, `tue`, `wed`"
          },
          "enabled": {
            "type": "boolean"
          },
          "time_of_day": {
            "type": "string"
          },
          "version": {
            "type": "string"
          }
        }
      },
      "name": {
        "type": "string"
      },
      "vars": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        },
        "description": "Dictionary of name->value, the vars can then be used in Wlans. This can overwrite those from Site Vars",
        "examples": [
          {
            "RADIUS_IP1": "172.31.2.5",
            "RADIUS_SECRET": "11s64632d"
          }
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "auto_upgrade": {
          "day_of_week": "mon",
          "enabled": true,
          "time_of_day": "string",
          "version": "string"
        },
        "name": "string",
        "vars": {
          "SSID_STR": "string",
          "VLAN_ID": "string"
        }
      }
    ]
  ]
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.site_templates.listOrgSiteTemplates()`

## Usage Context

Lists all site templates for the organization.

## Gotchas

- Site templates are different from WLAN templates and network templates.

## Related Endpoints

- [GET_orgs_org_id_sitetemplates_sitetemplate_id.md](GET_orgs_org_id_sitetemplates_sitetemplate_id.md) — Get specific template
- [POST_orgs_org_id_sitetemplates.md](POST_orgs_org_id_sitetemplates.md) — Create template

## MistHelper Notes

Used by MistHelper via `listOrgSiteTemplates` in Menu 35.
