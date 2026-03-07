# listOrgTemplates

> listOrgTemplates

## HTTP

`GET /api/v1/orgs/{org_id}/templates`

## Description

Get List of Org WLAN Templates

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

OK

```json
{
  "type": "array",
  "items": {
    "title": "template",
    "required": [
      "name"
    ],
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
    "description": "Template"
  },
  "description": "",
  "examples": [
    [
      {
        "applies": {
          "org_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
          "site_ids": [
            "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
          ],
          "sitegroup_ids": [
            "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
          ]
        },
        "created_time": 0,
        "deviceprofile_ids": [
          "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
        ],
        "exceptions": {
          "site_ids": [
            "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
          ],
          "sitegroup_ids": [
            "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
          ]
        },
        "filter_by_deviceprofile": true,
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "modified_time": 0,
        "name": "string",
        "org_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
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

`mistapi.api.v1.orgs.wlan_templates.listOrgTemplates()`

## Usage Context

Lists all WLAN templates for the organization.

## Gotchas

- These are WLAN templates (also called "templates" in the UI) that bundle WLANs and policies.

## Related Endpoints

- [GET_orgs_org_id_templates_template_id.md](GET_orgs_org_id_templates_template_id.md) — Get specific template
- [POST_orgs_org_id_templates.md](POST_orgs_org_id_templates.md) — Create template

## MistHelper Notes

Not currently used by MistHelper directly.
