# searchSiteWirelessClients

> searchSiteWirelessClients

## HTTP

`GET /api/v1/sites/{site_id}/clients/search`

## Description

Search Wireless Clients

**NOTE**: fuzzy logic can be used with ‘*’, supported filters: mac, hostname, device, os, model. E.g. /clients/search?device=Mac*&hostname=jerry

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
| mac | string | No |  |  | Partial / full MAC address |
| ip | string | No |  |  |  |
| hostname | string | No |  |  | Partial / full hostname |
| device | string | No |  |  | Device type, e.g. Mac, Nvidia, iPhone |
| os | string | No |  |  | OS, e.g. Sierra, Yosemite, Windows 10 |
| model | string | No |  |  | model, e.g. "MBP 15 late 2013", 6, 6s, "8+ GSM" |
| ap | string | No |  |  | AP mac where the client has connected to |
| ssid | string | No |  |  |  |
| text | string | No |  |  | Partial / full MAC address, hostname, username, psk_name or ip |
| nacrule_id | string | No |  |  | nacrule_id |
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
      "type": "number"
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
        "title": "client_wireless",
        "type": "object",
        "properties": {
          "ap": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of AP MAC Addresses the client was connected to",
            "examples": [
              [
                "a83a79a947ee",
                "003e73170b4c"
              ]
            ]
          },
          "app_version": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only when client has the Marvis Client app running. List of the versions of the Marvis Client",
            "examples": [
              [
                "0.100.3"
              ]
            ]
          },
          "band": {
            "type": "string",
            "description": "Wi-Fi Radio band",
            "examples": [
              "5"
            ]
          },
          "device": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only when client has the Marvis Client app running. List of the type of device type detected",
            "examples": [
              [
                "Mac"
              ]
            ]
          },
          "ftc": {
            "type": "boolean"
          },
          "hardware": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. Type of Wi-Fi adapter",
            "examples": [
              "Apple Wi-Fi adapter"
            ]
          },
          "hostname": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of hostname detected for this client",
            "examples": [
              [
                "hostname-a",
                "hostname-b"
              ]
            ]
          },
          "ip": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List if the ip addresses detected for this client",
            "examples": [
              [
                "10.5.23.43",
                "192.168.0.2"
              ]
            ]
          },
          "last_ap": {
            "type": "string",
            "description": "Latest AP where the client is/was connected to",
            "examples": [
              "a83a79a947ee"
            ]
          },
          "last_device": {
            "type": "string",
            "description": "Latest type of device we identified (e.g. iPhone, Mac, ...)",
            "examples": [
              "Zebra"
            ]
          },
          "last_firmware": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. Same as \"firmware\"",
            "examples": [
              "wl0: Jan 20 2024 04:08:41 version 20.103.12.0.8.7.171 FWID 01-e09d2675"
            ]
          },
          "last_hostname": {
            "type": "string",
            "description": "Latest hostname we detected for the client",
            "examples": [
              "hostname-a"
            ]
          },
          "last_ip": {
            "type": "string",
            "description": "The last known IP Address for the client",
            "examples": [
              "10.100.0.157"
            ]
          },
          "last_model": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. latest client hardware model we detected for the client",
            "examples": [
              "MBP 16\\\" M1 2021"
            ]
          },
          "last_os": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. Latest version of OS Type we detected for the client",
            "examples": [
              "Sonoma"
            ]
          },
          "last_os_version": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. Latest version of OS Version we detected for the client",
            "examples": [
              "14.4.1 (Build 23E224)"
            ]
          },
          "last_psk_id": {
            "type": "string",
            "description": "Only for PPSK authentication. Latest PPSK ID used by the client",
            "contentEncoding": "uuid",
            "examples": [
              "abf7dc5c-bb51-4bb7-93b6-5547400ffe11"
            ]
          },
          "last_psk_name": {
            "type": "string",
            "description": "Only for PPSK authentication. Latest PPSK Name used by the client",
            "examples": [
              "iot"
            ]
          },
          "last_ssid": {
            "type": "string",
            "description": "If dot1x authentication, the username used during the latest authentication. Otherwise, the MAC address of the client",
            "examples": [
              "john@mycorp.net"
            ]
          },
          "last_username": {
            "type": "string"
          },
          "last_vlan": {
            "type": "integer",
            "description": "Latest VLAN ID assigned to the client",
            "contentEncoding": "int32",
            "examples": [
              10
            ]
          },
          "last_wlan_id": {
            "type": "string",
            "description": "ID of the latest SSID (WLAN) the client is/was connected to",
            "contentEncoding": "uuid",
            "examples": [
              "e5d67b07-aae8-494b-8584-cbc20c8110aa"
            ]
          },
          "mac": {
            "type": "string",
            "description": "Client MAC Address",
            "examples": [
              "bcd074000000"
            ]
          },
          "mfg": {
            "type": "string",
            "description": "Manufacturer of the client hardware (MAC OUI based)",
            "examples": [
              "Apple"
            ]
          },
          "model": {
            "type": "string",
            "description": "Only when client has the Marvis Client app running. Client hardware model",
            "examples": [
              "MBP 16\\\" M1 2021"
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
          "os": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only when client is having the Marvis Client app running. List of OS detected for the client",
            "examples": [
              [
                "Sonoma"
              ]
            ]
          },
          "os_version": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only when client is having the Marvis Client app running. List of OS version detected for the client",
            "examples": [
              [
                "14.4.1 (Build 23E224)"
              ]
            ]
          },
          "protocol": {
            "type": "string",
            "description": "802.11 amendment",
            "examples": [
              "ax"
            ]
          },
          "psk_id": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of IDs of the PPSK used by the client",
            "examples": [
              [
                "abf7dc5c-bb51-4bb7-93b6-5547400ffe11"
              ]
            ]
          },
          "psk_name": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of names of the PPSK used by the client",
            "examples": [
              [
                "iot"
              ]
            ]
          },
          "random_mac": {
            "type": "boolean",
            "description": "Whether the client is using randomized MAC Address or not"
          },
          "sdk_version": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only when client has the Marvis Client app running. List of Marvis Client SDK version detected for the client",
            "examples": [
              [
                "0.100.3"
              ]
            ]
          },
          "site_id": {
            "type": "string",
            "description": "Mist Site ID where the client is connected",
            "contentEncoding": "uuid",
            "examples": [
              "25ff5219-9be7-4db9-907d-0c9b60445147"
            ]
          },
          "site_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of Mist Site IDs where the client was connected",
            "examples": [
              [
                "25ff5219-9be7-4db9-907d-0c9b60445147"
              ]
            ]
          },
          "ssid": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of the WLAN names the client was connected to",
            "examples": [
              [
                "IoT SSID"
              ]
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "username": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only for 802.1X authentication. List of usernames used by the client",
            "examples": [
              [
                "user@corp.com"
              ]
            ]
          },
          "vlan": {
            "type": "array",
            "items": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": "List of vlans that have been assigned to the client",
            "examples": [
              [
                10
              ]
            ]
          },
          "wlan_id": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "List of IDs of WLANs the client was connected to",
            "examples": [
              [
                "e5d67b07-aae8-494b-8584-cbc20c8110aa"
              ]
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number"
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

`mistapi.api.v1.sites.clients_-_wireless.searchSiteWirelessClients()`

## Usage Context

Searches wireless clients at a site with filtering by MAC, hostname, SSID, band, IP, OS, and more. Primary endpoint for client investigations.

## Gotchas

- Uses cursor-based pagination. Default returns current/recent clients.
- Specify `limit` for large result sets; max typically 1000.

## Related Endpoints

- [GET_sites_site_id_clients_count.md](GET_sites_site_id_clients_count.md) — Count clients
- [GET_sites_site_id_clients_events_search.md](GET_sites_site_id_clients_events_search.md) — Client events
- [GET_sites_site_id_clients_sessions_search.md](GET_sites_site_id_clients_sessions_search.md) — Client sessions

## MistHelper Notes

Used by Menu **30** (`searchSiteWirelessClients`), Menu **34**, and Menu **40** for wireless client data export.
