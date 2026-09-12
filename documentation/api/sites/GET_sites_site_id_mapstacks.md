# listSiteMapStacks

> listSiteMapStacks

## HTTP

`GET /api/v1/sites/{site_id}/mapstacks`

## Description

Get List of Site Map Stacks

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
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |
| name | string | No |  |  | Filter by map stack name |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "mapstack_response",
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
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
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "description": "The name of the map stack",
        "examples": [
          "Board Room"
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
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      }
    },
    "description": "Map Stack response object"
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 0,
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "modified_time": 0,
        "name": "Board Room",
        "org_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "site_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1"
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

`mistapi.api.v1.sites.map_stacks.listSiteMapStacks()`

## Usage Context

Lists map stacks at a site. Map stacks group multiple floor plans into a single multi-floor building view.

## Gotchas

- Map stacks are for visualization grouping. Individual maps retain independent configuration.

## Related Endpoints

- [GET_sites_site_id_maps.md](GET_sites_site_id_maps.md) — List individual maps
- [POST_sites_site_id_maps.md](POST_sites_site_id_maps.md) — Create map

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
