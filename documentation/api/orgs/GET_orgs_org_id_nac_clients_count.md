# countOrgNacClients

> countOrgNacClients

## HTTP

`GET /api/v1/orgs/{org_id}/nac_clients/count`

## Description

Count by Distinct Attributes of NAC Clients

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
| distinct | string | No |  |  | NAC Policy Rule ID, if matched |
| last_nacrule_id | string | No |  |  | NAC Policy Rule ID, if matched |
| nacrule_matched | boolean | No |  |  | NAC Policy Rule Matched |
| auth_type | string | No |  |  | Authentication type, e.g. "eap-tls", "eap-peap", "eap-ttls", "eap-teap", "mab", "psk", "device-auth" |
| last_vlan_id | string | No |  |  | Vlan ID |
| last_nas_vendor | string | No |  |  | Vendor of NAS device |
| idp_id | string | No |  |  | SSO ID, if present and used |
| last_ssid | string | No |  |  | SSID |
| last_username | string | No |  |  | Username presented by the client |
| timestamp | number | No |  |  | Start time, in epoch |
| site_id | string | No |  |  | Site id if assigned, null if not assigned |
| last_ap | string | No |  |  | AP MAC connected to by client |
| mac | string | No |  |  | MAC address |
| last_status | string | No |  |  | Connection status of client i.e "permitted", "denied, "session_ended" |
| type | string | No |  |  | Client type i.e. "wireless", "wired" etc. |
| mdm_compliance_status | string | No |  |  | MDM compliance of client i.e "compliant", "not compliant" |
| mdm_provider | string | No |  |  | MDM provider of client’s organization eg "intune", "jamf" |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": [
          "count"
        ],
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        },
        "additionalProperties": {
          "type": "string"
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
    "distinct",
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

`mistapi.api.v1.orgs.clients_-_nac.countOrgNacClients()`

## Usage Context

Returns the count of NAC clients grouped by specified fields.

## Gotchas

- Use `distinct` to group by auth type, VLAN, etc.

## Related Endpoints

- [GET_orgs_org_id_nac_clients_search.md](GET_orgs_org_id_nac_clients_search.md) — Search NAC clients
- [GET_orgs_org_id_nac_clients_events_search.md](GET_orgs_org_id_nac_clients_events_search.md) — NAC events

## MistHelper Notes

Not currently used by MistHelper directly.
