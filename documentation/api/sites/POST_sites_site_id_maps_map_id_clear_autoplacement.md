# clearSiteApAutoplacement

> clearSiteApAutoplacement

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/clear_autoplacement`

## Description

This API is used to destroy the cached autoplacement locations of a map or subset of APs on a map.

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
  "title": "mac_addresses",
  "required": [
    "macs"
  ],
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
  }
}
```

## Response

### 200

OK

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

`mistapi.api.v1.sites.maps_-_auto-placement.clearSiteApAutoplacement()`

## Usage Context

Clears auto-placement data for a specific map, removing automatically positioned AP locations.

## Gotchas

- APs will lose their map positions. Manual re-placement may be needed.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_placement.md](POST_sites_site_id_maps_map_id_auto_placement.md) — Trigger auto-placement
- [POST_sites_site_id_maps_map_id_use_auto_ap_values.md](POST_sites_site_id_maps_map_id_use_auto_ap_values.md) — Accept auto-placement

## MistHelper Notes

Not currently used by MistHelper directly.
