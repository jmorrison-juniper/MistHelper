# countOrgDevices

> countOrgDevices

## HTTP

`GET /api/v1/orgs/{org_id}/devices/count`

## Description

Count by Distinct Attributes of Org Devices

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
| hostname | string | No |  |  | Partial / full hostname |
| site_id | string | No |  |  | Site id |
| model | string | No |  |  | Device model |
| managed | string | No |  |  | for switches and gateways, to filter on managed/unmanaged devices. Deprecated in favour of mist_configured. enum: `true`, `false` |
| mac | string | No |  |  | AP mac |
| version | string | No |  |  | Version |
| ip | string | No |  |  |  |
| mxtunnel_status | string | No |  |  | MxTunnel status, enum: `up`, `down` |
| mxedge_id | string | No |  |  | Mist Edge id, if AP is connecting to a Mist Edge |
| lldp_system_name | string | No |  |  | LLDP system name |
| lldp_system_desc | string | No |  |  | LLDP system description |
| lldp_port_id | string | No |  |  | LLDP port id |
| lldp_mgmt_addr | string | No |  |  | LLDP management ip address |
| type | string | No |  |  |  |
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

`mistapi.api.v1.orgs.devices.countOrgDevices()`

## Usage Context

Returns the count of devices in the organization grouped by specified fields.

## Gotchas

- Use `distinct` parameter to group by model, type, version, etc.

## Related Endpoints

- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices
- [GET_orgs_org_id_devices_summary.md](GET_orgs_org_id_devices_summary.md) — Device summary

## MistHelper Notes

Used by MistHelper via `searchOrgDevices` in Menu 16 and related menus.
