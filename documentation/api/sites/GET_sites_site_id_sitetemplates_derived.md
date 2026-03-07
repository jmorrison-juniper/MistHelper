# listSiteSiteTemplatesDerived

> listSiteSiteTemplatesDerived

## HTTP

`GET /api/v1/sites/{site_id}/sitetemplates/derived`

## Description

Get the list of derived Site Templates for Site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| resolve | boolean | No |  |  | Whether resolve the site variables |

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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.site_templates.listSiteSiteTemplatesDerived()`

## Usage Context

Retrieves the effective (derived/resolved) site template settings, showing merged org-level template attributes.

## Gotchas

- Site templates define site-wide defaults like timezone, country, and address. Derived shows the resolved values.

## Related Endpoints

- [../orgs/GET_orgs_org_id_sitetemplates.md](../orgs/GET_orgs_org_id_sitetemplates.md) — Org site templates
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Not currently used by MistHelper directly.
