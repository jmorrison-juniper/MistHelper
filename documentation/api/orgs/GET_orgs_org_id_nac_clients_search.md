# searchOrgNacClients

> searchOrgNacClients

## HTTP

`GET /api/v1/orgs/{org_id}/nac_clients/search`

## Description

Search Org NAC Clients

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
| ap | string | No |  |  | AP MAC connected to by client |
| auth_type | string | No |  |  | Authentication type, e.g. "eap-tls", "eap-peap", "eap-ttls", "eap-teap", "mab", "psk", "device-auth" |
| cert_expiry_duration | string | No |  |  | Filter by certificate expiry within a specific duration from now (e.g., "7d" for 7 days, "1m" for 1 month) |
| edr_managed | boolean | No |  |  | Filters NAC clients that are integrated with EDR providers |
| edr_provider | string | No |  |  | EDR provider of client's organization |
| edr_status | string | No |  |  | EDR Status of the NAC client |
| family | string | No |  |  | Client family, e.g. "Phone/Tablet/Wearable", "Access Point" |
| hostname | string | No |  |  | Client hostname, e.g. "my-laptop", "my-phone" |
| idp_id | string | No |  |  | SSO ID, if present and used |
| mac | string | No |  |  | MAC address |
| mdm_compliance | string | No |  |  | MDM compliance of client i.e "compliant", "not compliant" |
| mdm_provider | string | No |  |  | MDM provider of client’s organization eg "intune", "jamf" |
| mdm_managed | boolean | No |  |  | Filters NAC clients that are managed by MDM providers |
| mfg | string | No |  |  | Client manufacturer, e.g. "apple", "cisco", "juniper" |
| model | string | No |  |  | Client model, e.g. "iPhone 12", "MX100" |
| nacrule_name | string | No |  |  | NAC Policy Rule Name matched |
| nacrule_id | string | No |  |  | NAC Policy Rule ID, if matched |
| nacrule_matched | boolean | No |  |  | NAC Policy Rule Matched |
| nas_vendor | string | No |  |  | Vendor of NAS device |
| nas_ip | string | No |  |  | IP address of NAS device |
| ingress_vlan | string | No |  |  | Vendor specific Vlan ID in radius requests |
| os | string | No |  |  | Client OS, e.g. "iOS 18.1", "Android", "Windows", "Linux" |
| ssid | string | No |  |  | SSID |
| status | string | No |  |  | Connection status of client i.e "permitted", "denied, "session_stared", "session_ended" |
| text | string | No |  |  | partial / full MAC address, last_username, device_mac, nas_ip or last_ap |
| timestamp | number | No |  |  | Start time, in epoch |
| type | string | No |  |  | Client type i.e. "wireless", "wired" etc. |
| usermac_label | array | No |  |  | Labels derived from usermac entry |
| username | string | No |  |  | Username presented by the client |
| vlan | string | No |  |  | Vlan name or ID assigned to the client |
| site_id | string | No |  |  | Site id if assigned, null if not assigned |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | wxid |  | On which field the list should be sorted, -prefix represents DESC order. |
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
      "contentEncoding": "int32",
      "examples": [
        1513362753
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        3
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "client_nac",
        "type": "object",
        "properties": {
          "ap": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35bf16bb",
                "d4dc090041b4"
              ]
            ]
          },
          "auth_type": {
            "type": "string",
            "description": "enum: `cert`, `device-auth`, `eap-teap`, `eap-tls`, `eap-ttls`, `idp`, `mab`, `eap-peap`"
          },
          "cert_cn": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "When certificate based authentication is used, the CN from the certificates used for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "john@mycorp.net"
              ]
            ]
          },
          "cert_issuer": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "When certificate based authentication is used, the Issuer from the certificates used for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "/C=US/ST=CA/CN=MyCorp"
              ]
            ]
          },
          "cert_serial": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "When certificate based authentication is used, the Serial from the certificates used for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "2c63510123456789"
              ]
            ]
          },
          "cert_subject": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "When certificate based authentication is used, the Subject from the certificates used for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "/C=US/O=MyCorp/CN=john@mycorp.net/emailAddress=john@mycorp.net"
              ]
            ]
          },
          "client_ip": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "The known IP Addresses used by the client for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "10.100.0.157"
              ]
            ]
          },
          "device_mac": {
            "type": "string",
            "description": "MAC Address of the device (AP, Switch) the client is connected to",
            "readOnly": true,
            "examples": [
              "60c78d8c7f6f"
            ]
          },
          "edr_managed": {
            "type": "boolean"
          },
          "edr_provider": {
            "type": "string",
            "description": "`enum: `sentinelone`, `crowdstrike`"
          },
          "edr_status": {
            "type": "string",
            "description": "EDR Status of the NAC client. enum: `sentinelone_healthy`, `sentinelone_infected`, `crowdstrike_low`, `crowdstrike_medium`, `crowdstrike_high`, `crowdstrike_critical`, `crowdstrike_informational`"
          },
          "group": {
            "type": "string"
          },
          "idp_id": {
            "type": "string"
          },
          "idp_role": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "last_ap": {
            "type": "string",
            "description": "Latest AP where the client is/was connected to",
            "examples": [
              "a83a79a947ee"
            ]
          },
          "last_cert_cn": {
            "type": "string",
            "description": "When certificate based authentication is used, the CN from the latest certificate used",
            "examples": [
              "john@mycorp.net"
            ]
          },
          "last_cert_expiry": {
            "type": "number",
            "description": "When certificate based authentication is used, the expiration date from the latest certificate used",
            "examples": [
              1746711240
            ]
          },
          "last_cert_issuer": {
            "type": "string",
            "description": "When certificate based authentication is used, the Issuer from the latest certificate used",
            "examples": [
              "/C=US/ST=CA/CN=MyCorp"
            ]
          },
          "last_cert_serial": {
            "type": "string",
            "description": "When certificate based authentication is used, the Serial from the latest certificate used",
            "examples": [
              "2c63510123456789"
            ]
          },
          "last_cert_subject": {
            "type": "string",
            "description": "When certificate based authentication is used, the Subject from the latest certificate used",
            "examples": [
              "/C=US/O=MyCorp/CN=john@mycorp.net/emailAddress=john@mycorp.net"
            ]
          },
          "last_client_ip": {
            "type": "string",
            "description": "The last known IP Address for the client",
            "examples": [
              "10.100.0.157"
            ]
          },
          "last_nacrule_id": {
            "type": "string",
            "description": "ID of the latest NAC Rule used to authenticate the client",
            "examples": [
              "603b62db-d839-4152-9f7f-f2578443de8d"
            ]
          },
          "last_nacrule_name": {
            "type": "string",
            "description": "Name of the latest NAC Rule used to authenticate the client",
            "examples": [
              "Wireless Cert Auth"
            ]
          },
          "last_nas_vendor": {
            "type": "string",
            "description": "Vendor name of the NAS for the latest authentication",
            "examples": [
              "juniper-mist"
            ]
          },
          "last_port_id": {
            "type": "string",
            "description": "If Wired authentication, the latest Port-id the client was connected to",
            "examples": [
              "ge-0/0/17.0"
            ]
          },
          "last_ssid": {
            "type": "string",
            "description": "If Wireless authentication, the latest SSID the client was connected to",
            "examples": [
              "MyCorp-NAC"
            ]
          },
          "last_status": {
            "type": "string",
            "description": "Latest Authentication status of the client. enum: `denied`, `permitted`, `session_started`, `session_stopped`"
          },
          "last_username": {
            "type": "string",
            "description": "If dot1x authentication, the username used during the latest authentication. Otherwise, the MAC address of the client",
            "examples": [
              "john@mycorp.net"
            ]
          },
          "last_vlan": {
            "type": "integer",
            "description": "Latest VLAN ID assigned to the client",
            "contentEncoding": "int32",
            "examples": [
              10
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
          "nacrule_id": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "IDs of the NAC Rules used to authenticate the client for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "603b62db-d839-4152-9f7f-f2578443de8d"
              ]
            ]
          },
          "nacrule_matched": {
            "type": "boolean"
          },
          "nacrule_name": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Name of the NAC Rules used to authenticate the client for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "Wireless Cert Auth"
              ]
            ]
          },
          "nas_ip": {
            "type": "string"
          },
          "nas_vendor": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Vendor name of the NAS for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "juniper-mist"
              ]
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
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Port-ids the client was connected to  for the specified duration",
            "readOnly": true,
            "examples": [
              [
                "ge-0/0/17.0"
              ]
            ]
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
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "SSIDs the client was connected to  for the specified duration",
            "examples": [
              [
                "MyCorp-NAC"
              ]
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Type of network access. enum: `wireless`, `wired`, `vty`"
          },
          "usermac_label": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "username": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of usernames that have been assigned to the client",
            "readOnly": true
          },
          "vlan": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of vlans that have been assigned to the client",
            "readOnly": true
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1513276353
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        2
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

`mistapi.api.v1.orgs.clients_-_nac.searchOrgNacClients()`

## Usage Context

Searches NAC (Network Access Control) clients across the organization.

## Gotchas

- Supports filtering by MAC, username, auth type, and more.

## Related Endpoints

- [GET_orgs_org_id_nac_clients_count.md](GET_orgs_org_id_nac_clients_count.md) — Count clients
- [GET_orgs_org_id_nac_clients_events_search.md](GET_orgs_org_id_nac_clients_events_search.md) — NAC events

## MistHelper Notes

Not currently used by MistHelper directly.
