# listSiteBeaconsStats

> listSiteBeaconsStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/beacons`

## Description

Get List of Site Beacons Stats

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
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "stats_beacon",
    "required": [
      "mac",
      "map_id",
      "name",
      "power",
      "type",
      "x",
      "y"
    ],
    "type": "object",
    "properties": {
      "battery_voltage": {
        "type": "number",
        "description": "Battery voltage, in mV"
      },
      "eddystone_instance": {
        "type": "string"
      },
      "eddystone_namespace": {
        "type": "string"
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
        "type": "string"
      },
      "map_id": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "name": {
        "type": "string"
      },
      "power": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "type": {
        "type": "string"
      },
      "x": {
        "type": "number"
      },
      "y": {
        "type": "number"
      }
    }
  },
  "description": "Beacon statistics"
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

`mistapi.api.v1.sites.stats_-_beacons.listSiteBeaconsStats()`

## Usage Context

Retrieves statistics for BLE beacons at a site, including battery levels and last-seen timestamps.

## Gotchas

- Beacon stats depend on APs with BLE enabled scanning for the beacons.

## Related Endpoints

- [GET_sites_site_id_beacons.md](GET_sites_site_id_beacons.md) — List beacons
- [GET_sites_site_id_stats_assets.md](GET_sites_site_id_stats_assets.md) — Asset stats

## MistHelper Notes

Not currently used by MistHelper directly.
