# createSiteZone

> createSiteZone

## HTTP

`POST /api/v1/sites/{site_id}/zones`

## Description

Create Site Zone

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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
    "for_site": {
      "type": "boolean",
      "readOnly": true
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
      "description": "Map where this zone is defined",
      "contentEncoding": "uuid",
      "readOnly": true
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "The name of the zone"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "vertices": {
      "type": "array",
      "items": {
        "title": "zone_vertex",
        "required": [
          "x",
          "y"
        ],
        "type": "object",
        "properties": {
          "x": {
            "type": "number",
            "description": "X in pixel"
          },
          "y": {
            "type": "number",
            "description": "Y in pixel"
          }
        }
      },
      "description": "Vertices used to define an area. It\u2019s assumed that the last point connects to the first point and forms an closed area",
      "examples": [
        [
          {
            "x": 732,
            "y": 1821
          },
          {
            "x": 732.5,
            "y": 1731
          },
          {
            "x": 837.5,
            "y": 1731.5
          },
          {
            "x": 839,
            "y": 1821
          }
        ]
      ]
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
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
      "description": "Map where this zone is defined",
      "contentEncoding": "uuid",
      "readOnly": true
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "The name of the zone"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "vertices": {
      "type": "array",
      "items": {
        "title": "zone_vertex",
        "required": [
          "x",
          "y"
        ],
        "type": "object",
        "properties": {
          "x": {
            "type": "number",
            "description": "X in pixel"
          },
          "y": {
            "type": "number",
            "description": "Y in pixel"
          }
        }
      },
      "description": "Vertices used to define an area. It\u2019s assumed that the last point connects to the first point and forms an closed area",
      "examples": [
        [
          {
            "x": 732,
            "y": 1821
          },
          {
            "x": 732.5,
            "y": 1731
          },
          {
            "x": 837.5,
            "y": 1731.5
          },
          {
            "x": 839,
            "y": 1821
          }
        ]
      ]
    }
  },
  "description": "Zone"
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

`mistapi.api.v1.sites.zones.createSiteZone()`

## Usage Context

Creates a new zone at a site. Zones define logical areas for tracking client occupancy and location.

## Gotchas

- Zone vertices must form a valid polygon on the map.

## Related Endpoints

- [GET_sites_site_id_zones.md](GET_sites_site_id_zones.md) — List zones
- [GET_sites_site_id_stats_zones.md](GET_sites_site_id_stats_zones.md) — Zone stats

## MistHelper Notes

Not currently used by MistHelper directly.
