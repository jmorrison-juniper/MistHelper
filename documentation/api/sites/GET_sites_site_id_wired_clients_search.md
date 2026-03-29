# searchSiteWiredClients

> searchSiteWiredClients

## HTTP

`GET /api/v1/sites/{site_id}/wired_clients/search`

## Description

Search Wired Clients

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
| device_mac | string | No |  |  | Device mac |
| mac | string | No |  |  | Client mac |
| ip | string | No |  |  | Client ip |
| port_id | string | No |  |  | Port id |
| source | string | No |  |  | source from where the client was learned (lldp, mac) |
| vlan | string | No |  |  | VLAN |
| manufacture | string | No |  |  | Manufacture |
| text | string | No |  |  | Single entry of hostname/mac |
| nacrule_id | string | No |  |  | nacrule_id |
| dhcp_hostname | string | No |  |  | DHCP Hostname |
| dhcp_fqdn | string | No |  |  | DHCP FQDN |
| dhcp_client_identifier | string | No |  |  | DHCP Client Identifier |
| dhcp_vendor_class_identifier | string | No |  |  | DHCP Vendor Class Identifier |
| dhcp_request_params | string | No |  |  | DHCP Request Parameters |
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
        "title": "wired_client_response",
        "type": "object",
        "properties": {
          "auth_method": {
            "type": "string",
            "examples": [
              "mac_auth"
            ]
          },
          "auth_state": {
            "type": "string",
            "examples": [
              "authenticated"
            ]
          },
          "device_mac": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "MAC Address of the switch the client is connected to",
            "readOnly": true
          },
          "device_mac_port": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "wired_client_response_device_mac_port_item",
              "type": "object",
              "properties": {
                "device_mac": {
                  "minLength": 1,
                  "type": "string"
                },
                "ip": {
                  "type": "string",
                  "readOnly": true
                },
                "port_id": {
                  "type": "string",
                  "readOnly": true
                },
                "port_parent": {
                  "type": "string"
                },
                "start": {
                  "type": "string",
                  "readOnly": true
                },
                "vlan": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "when": {
                  "type": "string",
                  "readOnly": true
                }
              }
            },
            "description": "",
            "readOnly": true
          },
          "dhcp_client_identifier": {
            "type": "string",
            "examples": [
              "MAC address 00155df6d500"
            ]
          },
          "dhcp_client_options": {
            "type": "array",
            "items": {
              "title": "dhcp_client_option",
              "type": "object",
              "properties": {
                "code": {
                  "type": "string",
                  "examples": [
                    "DHO_DHCP_MESSAGE_TYPE(53)"
                  ]
                },
                "data": {
                  "type": "string",
                  "examples": [
                    "DHCPREQUEST"
                  ]
                }
              }
            },
            "description": ""
          },
          "dhcp_fqdn": {
            "type": "string",
            "examples": [
              "ITS-VMMT0-D1N02.mgthub.local"
            ]
          },
          "dhcp_hostname": {
            "type": "string",
            "examples": [
              "ITS-VMMT0-D1N02"
            ]
          },
          "dhcp_request_params": {
            "type": "string",
            "examples": [
              "1 3 6 15 31 33 43 44 46 47 119 121 249 252"
            ]
          },
          "dhcp_vendor_class_identifier": {
            "type": "string",
            "examples": [
              "MSFT 5.0"
            ]
          },
          "ip": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "mac": {
            "type": "string",
            "readOnly": true
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
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "vlan": {
            "type": "array",
            "items": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": "",
            "readOnly": true
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

`mistapi.api.v1.sites.clients_-_wired.searchSiteWiredClients()`

## Usage Context

Searches wired (Ethernet) clients at a site. Returns MAC, IP, VLAN, switch port, and authentication status.

## Gotchas

- Wired client data comes from managed switches. Clients on unmanaged switches are not visible.

## Related Endpoints

- [GET_sites_site_id_wired_clients_count.md](GET_sites_site_id_wired_clients_count.md) — Wired client count
- [GET_sites_site_id_stats_ports_search.md](GET_sites_site_id_stats_ports_search.md) — Port stats

## MistHelper Notes

Used by Menus **69, 84** via `searchSiteWiredClients` for wired client data export.
