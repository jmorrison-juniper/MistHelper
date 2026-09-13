# listSiteRssiZones

> listSiteRssiZones

## HTTP

`GET /api/v1/sites/{site_id}/rssizones`

## Description

Get List of Site RSSI Zone (RSSI-based)

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

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "rssi_zone",
    "required": [
      "devices"
    ],
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "devices": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "title": "rssi_zone_device",
          "required": [
            "device_id",
            "rssi"
          ],
          "type": "object",
          "properties": {
            "device_id": {
              "type": "string",
              "contentEncoding": "uuid",
              "readOnly": true,
              "examples": [
                "00000000-0000-0000-1000-d8695a0f9e61"
              ]
            },
            "rssi": {
              "type": "integer",
              "description": "RSSI threshold",
              "contentEncoding": "int32",
              "examples": [
                0
              ]
            }
          }
        },
        "description": "List of devices and the respective RSSI values to be considered in the zone"
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
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "description": "The name of the zone",
        "examples": [
          "zone name"
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
    "description": "RSSI Zone"
  },
  "description": ""
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

`mistapi.api.v1.sites.rssi_zones.listSiteRssiZones()`

## Usage Context

Lists RSSI zones at a site. RSSI zones use signal strength thresholds to define proximity-based areas.

## Gotchas

- RSSI zones differ from map-based zones. They use signal strength rather than floor plan coordinates.

## Related Endpoints

- [GET_sites_site_id_rssizones_rssizone_id.md](GET_sites_site_id_rssizones_rssizone_id.md) — Get specific RSSI zone
- [POST_sites_site_id_rssizones.md](POST_sites_site_id_rssizones.md) — Create RSSI zone

## MistHelper Notes

Not currently used by MistHelper directly.
