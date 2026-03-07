# updateOrgSiteTemplate

> updateOrgSiteTemplate

## HTTP

`PUT /api/v1/orgs/{org_id}/sitetemplates/{sitetemplate_id}`

## Description

Update Org Site Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sitetemplate_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
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
}
```

## Response

### 200

Example response

```json
{
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

`mistapi.api.v1.orgs.site_templates.updateOrgSiteTemplate()`

## Usage Context

Updates an existing site template.

## Gotchas

- Changes affect the default attributes for newly created sites using this template.

## Related Endpoints

- [GET_orgs_org_id_sitetemplates_id.md](GET_orgs_org_id_sitetemplates_id.md) — Get template
- [POST_orgs_org_id_sitetemplates.md](POST_orgs_org_id_sitetemplates.md) — Create template

## MistHelper Notes

Site template listing uses Menu 35 (`listOrgSiteTemplates`). Update is not used directly.
