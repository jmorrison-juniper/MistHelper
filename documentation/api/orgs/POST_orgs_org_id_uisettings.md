# createOrgUiSettings

> createOrgUiSettings

## HTTP

`POST /api/v1/orgs/{org_id}/uisettings`

## Description

Create an Org UI settings/databoard

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "description": {
      "type": "string",
      "examples": [
        "This databoard shows AP stats"
      ]
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true,
      "examples": [
        false
      ]
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
    "isCustomDataboard": {
      "type": "boolean",
      "description": "Whether this is a custom databoard or not"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name of the databoard",
      "examples": [
        "AP Stats"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "purpose": {
      "type": "string",
      "description": "enum: `marvisdashboard`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "tiles": {
      "type": "array",
      "items": {
        "title": "org_ui_settings_tile",
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "Description of the tile",
            "examples": [
              "This tile shows the top 10 APs by bandwidth"
            ]
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
          "isAutoTitle": {
            "type": "boolean",
            "description": "Whether the tile title is auto generated or not"
          },
          "name": {
            "type": "string",
            "description": "Name of the tile",
            "examples": [
              "Top 10 APs by Bandwidth"
            ]
          },
          "nl_query": {
            "type": "string",
            "description": "Natural Language query for the tile",
            "examples": [
              "List top 10 APs by bandwidth"
            ]
          },
          "position": {
            "title": "org_ui_settings_tile_position",
            "type": "object",
            "properties": {
              "col": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1
                ]
              },
              "colSpan": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  5
                ]
              },
              "row": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1
                ]
              },
              "rowSpan": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  2
                ]
              }
            }
          }
        }
      },
      "description": "List of tiles in the databoard"
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "description": {
      "type": "string",
      "examples": [
        "This databoard shows AP stats"
      ]
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true,
      "examples": [
        false
      ]
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
    "isCustomDataboard": {
      "type": "boolean",
      "description": "Whether this is a custom databoard or not"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name of the databoard",
      "examples": [
        "AP Stats"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "purpose": {
      "type": "string",
      "description": "enum: `marvisdashboard`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "tiles": {
      "type": "array",
      "items": {
        "title": "org_ui_settings_tile",
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "Description of the tile",
            "examples": [
              "This tile shows the top 10 APs by bandwidth"
            ]
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
          "isAutoTitle": {
            "type": "boolean",
            "description": "Whether the tile title is auto generated or not"
          },
          "name": {
            "type": "string",
            "description": "Name of the tile",
            "examples": [
              "Top 10 APs by Bandwidth"
            ]
          },
          "nl_query": {
            "type": "string",
            "description": "Natural Language query for the tile",
            "examples": [
              "List top 10 APs by bandwidth"
            ]
          },
          "position": {
            "title": "org_ui_settings_tile_position",
            "type": "object",
            "properties": {
              "col": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1
                ]
              },
              "colSpan": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  5
                ]
              },
              "row": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1
                ]
              },
              "rowSpan": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  2
                ]
              }
            }
          }
        }
      },
      "description": "List of tiles in the databoard"
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

`mistapi.api.v1.orgs.ui_settings.createOrgUiSettings()`

## Usage Context

Creates a new UI setting entry for the organization.

## Gotchas

- UI settings persist dashboard preferences.

## Related Endpoints

- [GET_orgs_org_id_uisettings.md](GET_orgs_org_id_uisettings.md) — List UI settings
- [GET_orgs_org_id_uisettings_id.md](GET_orgs_org_id_uisettings_id.md) — Get UI setting

## MistHelper Notes

Not currently used by MistHelper directly.
