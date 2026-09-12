# getOrgTemplate

> getOrgTemplate

## HTTP

`GET /api/v1/orgs/{org_id}/templates/{template_id}`

## Description

Get Org Template Details

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

```json
{
  "type": "object",
  "properties": {
    "applies": {
      "type": "object",
      "properties": {
        "org_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "readOnly": true,
          "examples": [
            "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
          ]
        },
        "site_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of site ids"
        },
        "sitegroup_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of sitegroup ids"
        }
      },
      "description": "Where this template should be applied to, can be org_id, site_ids, sitegroup_ids"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "deviceprofile_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of Device Profile ids"
    },
    "exceptions": {
      "type": "object",
      "properties": {
        "site_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of site ids"
        },
        "sitegroup_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of sitegroup ids"
        }
      },
      "description": "Where this template should not be applied to (takes precedence)"
    },
    "filter_by_deviceprofile": {
      "type": "boolean",
      "description": "Whether to further filter by Device Profile"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Template"
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

`mistapi.api.v1.orgs.wlan_templates.getOrgTemplate()`

## Usage Context

Retrieves a specific WLAN template by ID.

## Gotchas

- WLAN templates bundle WLANs, tunneling policies, and WxLAN rules.
- Not the same as site templates or network templates.

## Related Endpoints

- [GET_orgs_org_id_templates.md](GET_orgs_org_id_templates.md) — List templates
- [PUT_orgs_org_id_templates_template_id.md](PUT_orgs_org_id_templates_template_id.md) — Update template

## MistHelper Notes

Not currently used by MistHelper directly.
