# searchSiteDeviceConfigHistory

> searchSiteDeviceConfigHistory

## HTTP

`GET /api/v1/sites/{site_id}/devices/config_history/search`

## Description

Search for entries in device config history

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
| type | string | No |  |  |  |
| mac | string | No |  |  | Device MAC Address |
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
        "title": "response_config_history_search_item",
        "required": [
          "channel_24",
          "channel_5",
          "secpolicy_violated",
          "timestamp",
          "version"
        ],
        "type": "object",
        "properties": {
          "channel_24": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "channel_5": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "radio_macs": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "radios": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "response_config_history_search_item_radio",
              "required": [
                "band",
                "channel"
              ],
              "type": "object",
              "properties": {
                "band": {
                  "type": "string"
                },
                "channel": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "description": ""
          },
          "secpolicy_violated": {
            "type": "boolean"
          },
          "ssids": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "ssids_24": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "ssids_5": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "version": {
            "type": "string"
          },
          "wlans": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "response_config_history_search_item_wlan",
              "required": [
                "auth",
                "id",
                "ssid"
              ],
              "type": "object",
              "properties": {
                "auth": {
                  "type": "string"
                },
                "bands": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
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
                "ssid": {
                  "type": "string"
                },
                "vlan_ids": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            },
            "description": ""
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

`mistapi.api.v1.sites.devices.searchSiteDeviceConfigHistory()`

## Usage Context

Searches device configuration change history at a site. Shows who changed what and when.

## Gotchas

- Uses cursor-based pagination. Config history can be extensive for sites with frequent changes.

## Related Endpoints

- [GET_sites_site_id_devices_config_history_count.md](GET_sites_site_id_devices_config_history_count.md) — Count config changes
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Current device config

## MistHelper Notes

Not currently used by MistHelper directly.
