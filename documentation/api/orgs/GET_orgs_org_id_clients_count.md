# countOrgWirelessClients

> countOrgWirelessClients

## HTTP

`GET /api/v1/orgs/{org_id}/clients/count`

## Description

Count by Distinct Attributes of Org Wireless Clients

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
| distinct | string | No |  |  |  |
| mac | string | No |  |  | Partial / full MAC address |
| hostname | string | No |  |  | Partial / full hostname |
| device | string | No |  |  | Device type, e.g. Mac, Nvidia, iPhone |
| os | string | No |  |  | OS, e.g. Sierra, Yosemite, Windows 10 |
| model | string | No |  |  | Model, e.g. "MBP 15 late 2013", 6, 6s, "8+ GSM" |
| ap | string | No |  |  | AP mac where the client has connected to |
| vlan | string | No |  |  | VLAN |
| ssid | string | No |  |  | SSID |
| ip | string | No |  |  |  |
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

`mistapi.api.v1.orgs.clients_-_wireless.countOrgWirelessClients()`

## Usage Context

Returns the count of wireless clients for the organization, grouped by specified fields.

## Gotchas

- Use `distinct` parameter to group by SSID, band, OS, etc.

## Related Endpoints

- [GET_orgs_org_id_clients_search.md](GET_orgs_org_id_clients_search.md) — Search clients
- [GET_orgs_org_id_clients_sessions_count.md](GET_orgs_org_id_clients_sessions_count.md) — Session counts

## MistHelper Notes

Used by MistHelper via `searchOrgWirelessClients` supporting Menus 66-72.
