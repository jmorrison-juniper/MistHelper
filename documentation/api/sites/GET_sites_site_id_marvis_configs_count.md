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

Use this endpoint to read the resource at
`/api/v1/sites/{site_id}/marvis_configs/count`.
Common use cases:

- Use it when you need to count Marvis Config Actions for a site by a distinct field.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `countSiteMarvisConfigActions(mist_session: mistapi.__api_session.APISession, site_id: str, distinct: str | None = None, mac: str | None = None, type: str | None = None, src: str | None = None, admin_id: str | None = None, op: str | None = None, port_id: str | None = None, vlan_ids: int | None = None, reason: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- Query parameters include `distinct`, `mac`, `type`, `src`, `admin_id`. Keep filters narrow for repeatable results.
- Count endpoints return totals, not records. Use the matching search endpoint for details.

## Related Endpoints

- [DELETE_sites_site_id_marvis_configs_id.md](DELETE_sites_site_id_marvis_configs_id.md) -- deleteSiteMarvisConfigAction uses `DELETE /api/v1/sites/{site_id}/marvis_configs/{id}`.
- [GET_sites_site_id_marvis_configs_search.md](GET_sites_site_id_marvis_configs_search.md) -- searchSiteMarvisConfigActions uses `GET /api/v1/sites/{site_id}/marvis_configs/search`.
- [POST_sites_site_id_marvis_configs_id_feedback.md](POST_sites_site_id_marvis_configs_id_feedback.md) -- submitSiteMarvisConfigFeedback uses `POST /api/v1/sites/{site_id}/marvis_configs/{id}/feedback`.

## MistHelper Notes

Menu Operation **236** offers this site count endpoint.
Verification source: `git grep -n "countSiteMarvisConfigActions" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
