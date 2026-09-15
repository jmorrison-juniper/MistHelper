# countSiteMarvisConfigActions

> countSiteMarvisConfigActions

## HTTP

`GET /api/v1/sites/{site_id}/marvis_configs/count`

## Description

Count Marvis Config Actions for a site by a distinct field.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| distinct | string | No | mac |  | Field to count by. enum: `mac`, `type`, `src`, `admin_id`, `op`, `port_id`, `reason`, `vlan_ids` |
| mac | string | No |  |  | Filter by device MAC address |
| type | string | No |  |  | Filter by config type (e.g. wired) |
| src | string | No |  |  | Filter by source of the config action (e.g. marvis) |
| admin_id | string | No |  |  | Filter by admin ID |
| op | string | No |  |  | Filter by operation type (e.g. disable_port, enable_port, update_mtu, add_vlans_to_port) |
| port_id | string | No |  |  | Filter by port identifier (e.g. ge-0/0/13) |
| vlan_ids | integer | No |  |  | Filter by VLAN ID |
| reason | string | No |  |  | Filter by reason for the config action (e.g. rogue_dhcp_server_detected) |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Count result

```json
{
  "additionalProperties": false,
  "description": "Distinct count response for time-bounded search results",
  "properties": {
    "distinct": {
      "description": "Field used to group the count results",
      "type": "string"
    },
    "end": {
      "description": "Search window end timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of distinct count results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of count result rows",
      "items": {
        "additionalProperties": {
          "type": "string"
        },
        "description": "Count result row with the matching distinct field values",
        "properties": {
          "count": {
            "description": "Number of matching items for the distinct value or values in this result",
            "type": "integer"
          }
        },
        "required": [
          "count"
        ],
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Search window start timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "total": {
      "description": "Number of distinct result buckets returned",
      "type": "integer"
    }
  },
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
  ],
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

`mistapi.api.v1.sites.marvis_configs.countSiteMarvisConfigActions()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
