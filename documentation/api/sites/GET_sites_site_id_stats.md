# getSiteStats

> getSiteStats

## HTTP

`GET /api/v1/sites/{site_id}/stats`

## Description

Get Sites Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "address": {
      "type": "string"
    },
    "alarmtemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "analyticEnabled": {
      "type": "boolean"
    },
    "aptemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "country_code": {
      "type": "string"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "engagementEnabled": {
      "type": "boolean"
    },
    "gatewaytemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
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
    "lat": {
      "type": "number"
    },
    "latlng": {
      "title": "lat_lng",
      "required": [
        "lat",
        "lng"
      ],
      "type": "object",
      "properties": {
        "lat": {
          "type": "number",
          "examples": [
            37.295833
          ]
        },
        "lng": {
          "type": "number",
          "examples": [
            -122.032946
          ]
        }
      }
    },
    "lng": {
      "type": "number"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "name": {
      "type": "string"
    },
    "networktemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "notes": {
      "type": "string"
    },
    "num_ap": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_ap_connected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_clients": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_devices": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_devices_connected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_gateway": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_gateway_connected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_switch": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_switch_connected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "rftemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "secpolicy_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "sitegroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    },
    "sitetemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "timezone": {
      "type": "string"
    },
    "tzoffset": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "country_code",
    "created_time",
    "id",
    "latlng",
    "modified_time",
    "name",
    "num_ap",
    "num_ap_connected",
    "num_clients",
    "num_devices",
    "num_devices_connected",
    "num_gateway",
    "num_gateway_connected",
    "num_switch",
    "num_switch_connected",
    "org_id",
    "timezone",
    "tzoffset"
  ],
  "description": "Site statistics"
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

`mistapi.api.v1.sites.stats.getSiteStats()`

## Usage Context

Retrieves aggregated site-level statistics including device counts, client counts, and overall health scores.

## Gotchas

- This is a summary endpoint. For device-level detail, use the specific stats endpoints.

## Related Endpoints

- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — Device stats
- [GET_sites_site_id_stats_clients.md](GET_sites_site_id_stats_clients.md) — Client stats

## MistHelper Notes

Not currently used by MistHelper directly.
