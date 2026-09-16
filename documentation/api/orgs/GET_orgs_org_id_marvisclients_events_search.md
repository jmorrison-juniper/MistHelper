# searchOrgMarvisClientEvents

> searchOrgMarvisClientEvents

## HTTP

`GET /api/v1/orgs/{org_id}/marvisclients/events/search`

## Description

Search Marvis Client events across the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | Filter by event type |
| device_id | string | No |  |  | Filter by Marvis Client installation device UUID |
| wifi_mac | string | No |  |  | Filter by device Wi-Fi MAC address |
| wifi_ip | string | No |  |  | Filter by device Wi-Fi IP address |
| hostname | string | No |  |  | Filter by device hostname |
| ssid | string | No |  |  | Filter by SSID involved in roam events |
| bssid | string | No |  |  | Filter by BSSID the client roamed to |
| channel | string | No |  |  | Filter by channel the client roamed to |
| pre_bssid | string | No |  |  | Filter by BSSID the client roamed from |
| pre_channel | string | No |  |  | Filter by channel the client roamed from |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Paginated Marvis Client events search results

```json
{
  "additionalProperties": false,
  "description": "Paginated list of Marvis Client events",
  "properties": {
    "limit": {
      "description": "Maximum number of results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of Marvis Client events",
      "items": {
        "additionalProperties": false,
        "description": "A Marvis Client event record",
        "properties": {
          "band": {
            "description": "Wi-Fi band at the time of the event",
            "type": "string"
          },
          "bssid": {
            "description": "BSSID the client roamed to (for roam events)",
            "type": "string"
          },
          "channel": {
            "description": "Channel the client roamed to (for roam events)",
            "type": "integer"
          },
          "device_id": {
            "description": "UUID of the device the Marvis Client is installed on",
            "format": "uuid",
            "type": "string"
          },
          "hostname": {
            "description": "Device hostname",
            "type": "string"
          },
          "location": {
            "additionalProperties": false,
            "description": "Last known location fix for a Marvis Client device",
            "properties": {
              "map_id": {
                "description": "UUID of the floor-plan map",
                "format": "uuid",
                "type": "string"
              },
              "site_id": {
                "description": "UUID of the site the device was located in",
                "format": "uuid",
                "type": "string"
              },
              "timestamp": {
                "description": "Timestamp of the location fix, in epoch seconds",
                "type": "integer"
              },
              "x": {
                "description": "X coordinate on the floor-plan map, in pixels",
                "type": "number"
              },
              "y": {
                "description": "Y coordinate on the floor-plan map, in pixels",
                "type": "number"
              }
            },
            "type": "object"
          },
          "neighbor_ap_report": {
            "description": "List of neighboring APs observed at the time of the event",
            "items": {
              "additionalProperties": false,
              "description": "A neighboring AP observed in a Marvis Client event",
              "properties": {
                "band": {
                  "description": "Wi-Fi band the AP is operating on",
                  "type": "string"
                },
                "bssid": {
                  "description": "BSSID of the neighboring AP",
                  "type": "string"
                },
                "channel": {
                  "description": "Channel the neighboring AP is on",
                  "type": "integer"
                },
                "rssi": {
                  "description": "RSSI of the neighboring AP signal, in dBm",
                  "type": "integer"
                }
              },
              "type": "object"
            },
            "type": "array"
          },
          "org_id": {
            "description": "Organization UUID",
            "format": "uuid",
            "type": "string"
          },
          "percent": {
            "description": "Battery level percentage at the time of the event (for battery events)",
            "type": "integer"
          },
          "pre_bssid": {
            "description": "BSSID the client roamed from (for roam events)",
            "type": "string"
          },
          "pre_channel": {
            "description": "Channel the client roamed from (for roam events)",
            "type": "integer"
          },
          "pre_rssi": {
            "description": "RSSI before the roam event, in dBm",
            "type": "integer"
          },
          "rssi": {
            "description": "Wi-Fi RSSI at the time of the event, in dBm",
            "type": "integer"
          },
          "ssid": {
            "description": "SSID the client was connected to",
            "type": "string"
          },
          "timestamp": {
            "description": "Event timestamp, in epoch seconds",
            "type": "integer"
          },
          "type": {
            "description": "Event type",
            "type": "string"
          },
          "wifi_ip": {
            "description": "Device Wi-Fi IP address at the time of the event",
            "type": "string"
          },
          "wifi_mac": {
            "description": "Device Wi-Fi MAC address",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "total": {
      "description": "Total number of matching results",
      "type": "integer"
    }
  },
  "type": "object"
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

`mistapi.api.v1.orgs.marvisclients.searchOrgMarvisClientEvents()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/orgs/{org_id}/marvisclients/events/search`.
Common use cases:

- Use it when you need to search Marvis Client events across the organization.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `searchOrgMarvisClientEvents(mist_session: mistapi.__api_session.APISession, org_id: str, type: str | None = None, device_id: str | None = None, wifi_mac: str | None = None, wifi_ip: str | None = None, hostname: str | None = None, ssid: str | None = None, bssid: str | None = None, channel: str | None = None, pre_bssid: str | None = None, pre_channel: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- Query parameters include `type`, `device_id`, `wifi_mac`, `wifi_ip`, `hostname`. Keep filters narrow for repeatable results.
- Search results can be large. Set a time range and page through all required results.

## Related Endpoints

- [GET_orgs_org_id_marvisclients_events_count.md](GET_orgs_org_id_marvisclients_events_count.md) -- countOrgMarvisClientEvents uses `GET /api/v1/orgs/{org_id}/marvisclients/events/count`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.
- [DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md](DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md) -- deleteOrgAAMWProfile uses `DELETE /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`.

## MistHelper Notes

MistHelper does not currently call `searchOrgMarvisClientEvents`.
Verification source: `git grep -n "searchOrgMarvisClientEvents" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
