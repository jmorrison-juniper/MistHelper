# confirmSiteApLocalizationData

> confirmSiteApLocalizationData

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values`

## Description

This API is used to accept or reject the cached autoplacement and auto-orientation values of a map or subset of APs on a map. Any APs that have autoplacement values are stored in cache for up to 7 days while awaiting acceptance or rejection.

```
Accepting the autoplacement values overwrites the existing X, Y, and orientation of the accepted APs with their cached autoplacement values.
Rejecting the autoplacement values causes the APs to retain their current X, Y, and orientation.
```

Once a decision (accept or reject) is made, or the 7-day time-to-live (TTL) expires, the cached values are deleted.

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
    "accept": {
      "type": "boolean",
      "description": "If accept is true, accepts placement for devices in list otherwise. If false, reject for devices in list.",
      "default": false
    },
    "for": {
      "type": "string",
      "description": "The selector to choose auto placement or auto orientation. enum: `orientation`, `placement`"
    },
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "A list of macs to accept/reject. If a list is not provided the API will accept/reject for the full map."
    }
  }
}
```

## Response

### 200

Success

## Errors

| Status | Description |
|--------|-------------|
| 400 | Map does not exist or belong to specified site / Invalid localization service. Expected [placement, orientation] |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.maps_-_auto-placement.confirmSiteApLocalizationData()`

## Usage Context

Accepts auto-placement AP positions, applying them as the official AP locations on the map.

## Gotchas

- This overwrites manually placed AP positions with auto-detected ones.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_placement.md](POST_sites_site_id_maps_map_id_auto_placement.md) — Trigger auto-placement
- [POST_sites_site_id_maps_map_id_clear_autoplacement.md](POST_sites_site_id_maps_map_id_clear_autoplacement.md) — Clear auto-placement

## MistHelper Notes

Not currently used by MistHelper directly.
