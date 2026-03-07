# searchOrgDeviceEvents

> searchOrgDeviceEvents

## HTTP

`GET /api/v1/orgs/{org_id}/devices/events/search`

## Description

Search Org Devices Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  | Device mac |
| model | string | No |  |  | Device model |
| device_type | string | No | ap |  |  |
| text | string | No |  |  | Event message |
| timestamp | string | No |  |  | Event time |
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listDeviceEventsDefinitions) |
| last_by | string | No |  |  | Return last/recent event for passed in field |
| includes | string | No |  |  | Keyword to include events from additional indices (e.g. ext_tunnel for prisma events) |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "device_event",
        "required": [
          "org_id",
          "timestamp",
          "type"
        ],
        "type": "object",
        "properties": {
          "ap": {
            "type": "string",
            "description": "(will be deprecated soon; please use mac instead) ap mac"
          },
          "ap_name": {
            "type": "string",
            "description": "(will be deprecated soon; please use device_name instead) ap name"
          },
          "apfw": {
            "type": "string"
          },
          "audit_id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "bandwidth": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "channel": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "chassis_mac": {
            "type": "string"
          },
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "device_name": {
            "type": "string",
            "description": "Device name"
          },
          "device_type": {
            "type": "string",
            "description": "enum: `ap`, `gateway`, `switch`"
          },
          "ev_type": {
            "type": "string",
            "description": "(optional) event advisory. enum: `notice`, `warn`"
          },
          "ext_ip": {
            "type": "string"
          },
          "mac": {
            "type": "string",
            "description": "Device mac"
          },
          "model": {
            "type": "string"
          },
          "node": {
            "type": "string"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "port_id": {
            "type": "string"
          },
          "power": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "pre_bandwidth": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "pre_channel": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "pre_power": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "pre_usage": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "reason": {
            "type": "string",
            "description": "(optional) event reason"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "site_name": {
            "type": "string",
            "description": "Site name"
          },
          "text": {
            "type": "string",
            "description": "(optional) event description"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Event type"
          },
          "usage": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "version": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

`mistapi.api.v1.orgs.devices.searchOrgDeviceEvents()`

## Usage Context

Searches device events across the organization with filtering by type, device, time range.

## Gotchas

- Time range defaults to last hour if not specified.
- Use `type` to filter AP, switch, or gateway events.

## Related Endpoints

- [GET_orgs_org_id_devices_events_count.md](GET_orgs_org_id_devices_events_count.md) — Count events
- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices

## MistHelper Notes

Used by MistHelper via `searchOrgDeviceEvents` in Menus 13, 15, 83.
