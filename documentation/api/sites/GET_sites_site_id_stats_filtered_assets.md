# getSiteAssetsOfInterest

> getSiteAssetsOfInterest

## HTTP

`GET /api/v1/sites/{site_id}/stats/filtered_assets`

## Description

Get a list of BLE beacons that matches Asset or AssetFilter

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
| duration | string | No | 1d |  | Duration like 7d, 2w |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "asset_of_interest",
    "type": "object",
    "properties": {
      "ap_mac": {
        "minLength": 1,
        "type": "string"
      },
      "beam": {
        "type": "number"
      },
      "by": {
        "minLength": 1,
        "type": "string"
      },
      "curr_site": {
        "minLength": 1,
        "type": "string"
      },
      "device_name": {
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
      "last_seen": {
        "type": [
          "number",
          "null"
        ],
        "description": "Last seen timestamp",
        "readOnly": true,
        "examples": [
          1470417522
        ]
      },
      "mac": {
        "minLength": 1,
        "type": "string"
      },
      "manufacture": {
        "minLength": 1,
        "type": "string"
      },
      "map_id": {
        "minLength": 1,
        "type": "string"
      },
      "name": {
        "minLength": 1,
        "type": "string"
      },
      "rssi": {
        "type": "number"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "ap_mac": "string",
        "beam": 0,
        "by": "string",
        "curr_site": "string",
        "device_name": "string",
        "id": "string",
        "last_seen": 0,
        "mac": "string",
        "manufacture": "string",
        "map_id": "string",
        "name": "string",
        "rssi": 0
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

`mistapi.api.v1.sites.stats_-_assets.getSiteAssetsOfInterest()`

## Usage Context

Retrieves filtered BLE asset statistics at a site, applying asset filters to narrow down the asset list.

## Gotchas

- Requires asset filters to be configured at the site level.

## Related Endpoints

- [GET_sites_site_id_stats_assets.md](GET_sites_site_id_stats_assets.md) — All asset stats
- [GET_sites_site_id_stats_discovered_assets.md](GET_sites_site_id_stats_discovered_assets.md) — Discovered assets

## MistHelper Notes

Not currently used by MistHelper directly.
