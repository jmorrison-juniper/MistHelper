# importOrgMapToSite

> importOrgMapToSite

## HTTP

`POST /api/v1/orgs/{org_id}/sites/{site_name}/maps/import`

## Description

Import data from files is a multipart POST which has a file, an optional json, and an optional csv, to create floorplan, assign matching inventory to specific site, place ap if name or mac matches

#### Request

```
"json": a JSON string describing your upload
"file": a binary file
```

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| site_name | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "auto_deviceprofile_assignment": {
      "type": "boolean",
      "description": "Whether to auto assign device to deviceprofile by name",
      "examples": [
        true
      ]
    },
    "csv": {
      "type": "string",
      "description": "CSV file for ap name mapping, optional",
      "contentEncoding": "base64"
    },
    "file": {
      "type": "string",
      "description": "Ekahau or ibwave file",
      "contentEncoding": "base64"
    },
    "json": {
      "title": "map_import_json",
      "required": [
        "vendor_name"
      ],
      "type": "object",
      "properties": {
        "import_all_floorplans": {
          "type": "boolean",
          "default": false
        },
        "import_height": {
          "type": "boolean",
          "default": true
        },
        "import_orientation": {
          "type": "boolean",
          "default": true
        },
        "vendor_name": {
          "type": "string",
          "description": "enum: `ekahau`, `ibwave`"
        }
      }
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "aps": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_map_import_ap",
        "required": [
          "action",
          "floorplan_id",
          "mac",
          "map_id",
          "orientation"
        ],
        "type": "object",
        "properties": {
          "action": {
            "type": "string",
            "description": "enum: `assigned-named-placed`, `assigned-placed`, `ignored`, `named-placed`, `placed`"
          },
          "floorplan_id": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "height": {
            "type": "number"
          },
          "mac": {
            "type": "string"
          },
          "map_id": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "orientation": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "reason": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "floorplans": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_map_import_floorplan",
        "required": [
          "action",
          "id",
          "map_id",
          "name"
        ],
        "type": "object",
        "properties": {
          "action": {
            "type": "string"
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
          "map_id": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "name": {
            "type": "string"
          },
          "reason": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "summary": {
      "title": "response_map_import_summary",
      "required": [
        "num_ap_assigned",
        "num_inv_assigned",
        "num_map_assigned"
      ],
      "type": "object",
      "properties": {
        "num_ap_assigned": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "num_inv_assigned": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "num_map_assigned": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
    }
  },
  "required": [
    "aps",
    "floorplans",
    "site_id",
    "summary"
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

`mistapi.api.v1.orgs.maps.importOrgMapToSite()`

## Usage Context

Imports floor plan maps into a site by site name.

## Gotchas

- Accepts image files for floor plans. Map format and dimensions must be correct.

## Related Endpoints

- [POST_orgs_org_id_sites.md](POST_orgs_org_id_sites.md) — Create site
- [GET_orgs_org_id_sites.md](GET_orgs_org_id_sites.md) — List sites

## MistHelper Notes

Not currently used by MistHelper directly. MistHelper uses the Maps Manager for map visualization.
