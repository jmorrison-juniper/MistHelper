# bulkAssignSiteApsToMap

> bulkAssignSiteApsToMap

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/set_map`

## Description

This API can be used to assign a list of AP Macs associated with site_id to the specified map_id. Note that map_id must be associated with corresponding site_id. This API obeys the following rules 
1. if AP is unassigned to any Map, it gets associated with map_id 
2. Any moved APs are returned in the response 
3. If the AP is considered a locked AP, no action will be taken

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "locked": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "moved": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
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

`mistapi.api.v1.sites.maps.bulkAssignSiteApsToMap()`

## Usage Context

Sets map properties such as scale, origin coordinates, and orientation.

## Gotchas

- Setting incorrect scale will affect all location calculations on this map.

## Related Endpoints

- [GET_sites_site_id_maps_map_id.md](GET_sites_site_id_maps_map_id.md) — Map details
- [PUT_sites_site_id_maps_map_id.md](PUT_sites_site_id_maps_map_id.md) — Update map

## MistHelper Notes

Not currently used by MistHelper directly.
