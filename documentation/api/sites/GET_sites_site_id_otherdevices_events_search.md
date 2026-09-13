# searchSiteOtherDeviceEvents

> searchSiteOtherDeviceEvents

## HTTP

`GET /api/v1/sites/{site_id}/otherdevices/events/search`

## Description

Search Site OtherDevices Events

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
| mac | string | No |  |  | MAC |
| device_mac | string | No |  |  | MAC of attached device |
| vendor | string | No |  |  | Vendor name |
| type | string | No |  |  | See  [List Device Events Definitions]($e/Constants%20Events/listOtherDeviceEventsDefinitions) |
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

Example response

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
      "title": "event_otherdevice",
      "type": "object",
      "properties": {
        "device_mac": {
          "type": "string"
        },
        "mac": {
          "type": "string",
          "examples": [
            "5c5b351e13b5"
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
        },
        "text": {
          "type": "string",
          "examples": [
            "Plugged: The Internal 5GB (SIM1) has been inserted into Internal 1."
          ]
        },
        "timestamp": {
          "type": "number",
          "description": "Epoch (seconds)",
          "readOnly": true
        },
        "type": {
          "type": "string",
          "examples": [
            "CELLULAR_EDGE_MODEM_WAN_PLUGGED"
          ]
        },
        "vendor": {
          "type": "string",
          "examples": [
            "cradlepoint"
          ]
        }
      }
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.devices_-_others.searchSiteOtherDeviceEvents()`

## Usage Context

Searches events for non-Juniper devices (other devices) at a site.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_sites_site_id_otherdevices_events_count.md](GET_sites_site_id_otherdevices_events_count.md) — Events count
- [GET_sites_site_id_otherdevices.md](GET_sites_site_id_otherdevices.md) — List other devices

## MistHelper Notes

Not currently used by MistHelper directly.
