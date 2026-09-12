# searchSiteNacClientEvents

> searchSiteNacClientEvents

## HTTP

`GET /api/v1/sites/{site_id}/nac_clients/events/search`

## Description

Search NAC Client Events

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
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listNacEventsDefinitions) |
| nacrule_id | string | No |  |  | NAC Policy Rule ID, if matched |
| nacrule_matched | boolean | No |  |  | NAC Policy Rule Matched |
| dryrun_nacrule_id | string | No |  |  | NAC Policy Dry Run Rule ID, if present and matched |
| dryrun_nacrule_matched | boolean | No |  |  | True - if dryrun rule present and matched with priority, False - if not matched or not present |
| auth_type | string | No |  |  | Authentication type, e.g. "eap-tls", "eap-peap", "eap-ttls", "eap-teap", "mab", "psk", "device-auth" |
| vlan | integer | No |  |  | Vlan ID |
| nas_vendor | string | No |  |  | Vendor of NAS device |
| bssid | string | No |  |  | BSSID |
| idp_id | string | No |  |  | SSO ID, if present and used |
| idp_role | string | No |  |  | IDP returned roles/groups for the user |
| idp_username | string | No |  |  | Username presented to the Identity Provider |
| resp_attrs | array | No |  |  | Radius attributes returned by NAC to NAS Devive |
| ssid | string | No |  |  | SSID |
| username | string | No |  |  | Username presented by the client |
| ap | string | No |  |  | AP MAC |
| random_mac | boolean | No |  |  | AP random macMAC |
| mac | string | No |  |  | MAC address |
| timestamp | number | No |  |  | Time, in epoch |
| usermac_label | string | No |  |  | Labels derived from usermac entry |
| text | string | No |  |  | Partial / full MAC address, username, device_mac or ap |
| nas_ip | string | No |  |  | IP address of NAS device |
| ingress_vlan | string | No |  |  | Vendor specific Vlan ID in radius requests |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| sort | string | No | wxid |  | On which field the list should be sorted, -prefix represents DESC order. |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

NAC Client Events

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1513176951
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "nac_client_event",
        "type": "object",
        "properties": {
          "ap": {
            "type": "string",
            "description": "AP mac",
            "examples": [
              "5c5b35513227"
            ]
          },
          "auth_type": {
            "type": "string",
            "description": "enum: `cert`, `device-auth`, `eap-teap`, `eap-tls`, `eap-ttls`, `idp`, `mab`, `eap-peap`"
          },
          "bssid": {
            "type": "string",
            "description": "BSSID",
            "examples": [
              "5c5b355fafcc"
            ]
          },
          "client_type": {
            "type": "string",
            "description": "Type of network access. enum: `wireless`, `wired`, `vty`"
          },
          "device_mac": {
            "type": "string",
            "description": "MAC Address of the device (AP, Switch) the client is connected to",
            "readOnly": true,
            "examples": [
              "60c78d8c7f6f"
            ]
          },
          "dryrun_nacrule_id": {
            "type": "string",
            "description": "NAC Policy Dry Run Rule ID, if present and matched",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "32f27e7d-ff26-4a9b-b3d1-ff9bcb264012"
            ]
          },
          "dryrun_nacrule_matched": {
            "type": "boolean",
            "description": "`true` if dryrun rule present and matched with priority, `false` if not matched or not present",
            "readOnly": true
          },
          "idp_id": {
            "type": "string",
            "description": "If IDP is used, the id of the IDP configuration used",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "912ef72e-2239-4996-b81e-469e87a27cd6"
            ]
          },
          "idp_role": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "itsuperusers",
                "vip"
              ]
            ]
          },
          "idp_username": {
            "type": "string",
            "description": "If IDP is used, the username presented to the Identity Provider",
            "readOnly": true,
            "examples": [
              "user@deaflyz.net"
            ]
          },
          "mac": {
            "type": "string",
            "description": "Client MAC address",
            "readOnly": true,
            "examples": [
              "ac3eb179e535"
            ]
          },
          "mxedge_id": {
            "type": "string",
            "description": "Mist Edge ID used to connect to cloud"
          },
          "nacrule_id": {
            "type": "string",
            "description": "NAC Policy Rule ID, if matched",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "32f27e7d-ff26-4a9b-b3d1-ff9bcb264c62"
            ]
          },
          "nacrule_matched": {
            "type": "boolean",
            "description": "NAC Policy Rule Matched",
            "readOnly": true
          },
          "nas_vendor": {
            "type": "string",
            "description": "Vendor name of the NAS",
            "readOnly": true,
            "examples": [
              "juniper-mist"
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
          "port_id": {
            "type": "string",
            "description": "Port ID where the NAC client event occurred",
            "readOnly": true,
            "examples": [
              "ge-0/0/17.0"
            ]
          },
          "port_type": {
            "type": "string",
            "description": "Type of network access. enum: `wireless`, `wired`, `vty`"
          },
          "random_mac": {
            "type": "string",
            "description": "Whether the client is using randomized MAC Address or not"
          },
          "resp_attrs": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of Radius AVP returned by the Authentication Server",
            "examples": [
              [
                "Tunnel-Type=VLAN",
                "Tunnel-Medium-Type=IEEE-802",
                "Tunnel-Private-Group-Id=750",
                "User-Name=anonymous"
              ]
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
          "ssid": {
            "type": "string",
            "description": "SSIDs the client was connecting to",
            "readOnly": true,
            "examples": [
              "MyCorp-NAC"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Event type, e.g. NAC_CLIENT_PERMIT. Use the [List NAC Events Definitions]($e/Constants%20Events/listNacEventsDefinitions) endpoint to get the full list of available values.",
            "readOnly": true,
            "examples": [
              "NAC_CLIENT_PERMIT"
            ]
          },
          "usermac_label": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Labels derived from usermac entry",
            "examples": [
              [
                "bldg5",
                "printer"
              ]
            ]
          },
          "username": {
            "type": "string",
            "description": "username assigned to the client",
            "readOnly": true
          },
          "vlan": {
            "type": "string",
            "description": "vlan that assigned to the client",
            "readOnly": true
          },
          "vlan_source": {
            "type": "string",
            "description": "Vlan source, e.g. \"nactag\", \"usermac\"",
            "examples": [
              "nactag"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1512572151
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
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

`mistapi.api.v1.sites.clients_-_nac.searchSiteNacClientEvents()`

## Usage Context

Searches NAC client events at a site. Supports filtering by MAC, username, VLAN, auth type, and time range.

## Gotchas

- Large time ranges may return paginated results.

## Related Endpoints

- [GET_sites_site_id_nac_clients_events_count.md](GET_sites_site_id_nac_clients_events_count.md) — Events count
- [GET_sites_site_id_nac_clients_search.md](GET_sites_site_id_nac_clients_search.md) — Search clients

## MistHelper Notes

Not currently used by MistHelper directly.
