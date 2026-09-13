# getSiteRssiZone

> getSiteRssiZone

## HTTP

`GET /api/v1/sites/{site_id}/rssizones/{rssizone_id}`

## Description

Get Site RSSI Zone details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| rssizone_id | string | Yes |  |

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
  "description": "",
  "examples": [
    [
      {
        "created_time": 0,
        "devices": [
          {
            "device_id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
            "rssi": 0
          }
        ],
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "modified_time": 0,
        "name": "string",
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.rssi_zones.getSiteRssiZone()`

## Usage Context

Retrieves details of a specific RSSI zone, including signal strength thresholds and AP assignments.

## Gotchas

- No known gotchas.

## Related Endpoints

- [PUT_sites_site_id_rssizones_rssizone_id.md](PUT_sites_site_id_rssizones_rssizone_id.md) — Update RSSI zone
- [DELETE_sites_site_id_rssizones_rssizone_id.md](DELETE_sites_site_id_rssizones_rssizone_id.md) — Delete RSSI zone

## MistHelper Notes

Not currently used by MistHelper directly.
