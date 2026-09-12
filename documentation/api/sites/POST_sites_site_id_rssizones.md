# createSiteRssiZone

> createSiteRssiZone

## HTTP

`POST /api/v1/sites/{site_id}/rssizones`

## Description

Create RSSI Zone

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
  "required": [
    "devices"
  ],
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
  "required": [
    "devices"
  ],
  "description": "RSSI Zone"
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

`mistapi.api.v1.sites.rssi_zones.createSiteRssiZone()`

## Usage Context

Creates a new RSSI zone at a site. RSSI zones define areas based on signal strength thresholds for location services.

## Gotchas

- Zone names must be unique within the site.

## Related Endpoints

- [GET_sites_site_id_rssizones.md](GET_sites_site_id_rssizones.md) — List RSSI zones
- [GET_sites_site_id_stats_rssizones.md](GET_sites_site_id_stats_rssizones.md) — Zone stats

## MistHelper Notes

Not currently used by MistHelper directly.
