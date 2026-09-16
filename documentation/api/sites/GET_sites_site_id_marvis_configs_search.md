# searchSiteMarvisConfigActions

> searchSiteMarvisConfigActions

## HTTP

`GET /api/v1/sites/{site_id}/marvis_configs/search`

## Description

Search Marvis Config Actions for a site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
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

Paginated Marvis Config Actions search results

```json
{
  "additionalProperties": false,
  "description": "Paginated list of Marvis config actions",
  "properties": {
    "end": {
      "description": "Search window end timestamp, in epoch seconds",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of Marvis config actions",
      "items": {
        "additionalProperties": false,
        "description": "A Marvis-injected config action record",
        "properties": {
          "admin_id": {
            "description": "Admin UUID associated with the config action",
            "format": "uuid",
            "type": "string"
          },
          "id": {
            "description": "UUID of the config action",
            "format": "uuid",
            "type": "string"
          },
          "mac": {
            "description": "Device MAC address",
            "type": "string"
          },
          "op": {
            "description": "Operation type (e.g. disable_port, enable_port, update_mtu, add_vlans_to_port)",
            "type": "string"
          },
          "org_id": {
            "description": "Organization UUID",
            "format": "uuid",
            "type": "string"
          },
          "port_id": {
            "description": "Port identifier (e.g. ge-0/0/13)",
            "type": "string"
          },
          "reason": {
            "description": "Reason for the config action (e.g. rogue_dhcp_server_detected)",
            "type": "string"
          },
          "site_id": {
            "description": "Site UUID",
            "format": "uuid",
            "type": "string"
          },
          "src": {
            "description": "Source of the config action (e.g. marvis)",
            "type": "string"
          },
          "timestamp": {
            "description": "Timestamp when the config action was recorded, in epoch seconds",
            "type": "number"
          },
          "type": {
            "description": "Config type (e.g. wired)",
            "type": "string"
          },
          "vlan_ids": {
            "description": "List of VLAN IDs involved in the config action",
            "items": {
              "type": "integer"
            },
            "type": "array"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "start": {
      "description": "Search window start timestamp, in epoch seconds",
      "type": "integer"
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

`mistapi.api.v1.sites.marvis_configs.searchSiteMarvisConfigActions()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/sites/{site_id}/marvis_configs/search`.
Common use cases:

- Use it when you need to search Marvis Config Actions for a site.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `searchSiteMarvisConfigActions(mist_session: mistapi.__api_session.APISession, site_id: str, mac: str | None = None, type: str | None = None, src: str | None = None, admin_id: str | None = None, op: str | None = None, port_id: str | None = None, vlan_ids: int | None = None, reason: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- Query parameters include `mac`, `type`, `src`, `admin_id`, `op`. Keep filters narrow for repeatable results.
- Search results can be large. Set a time range and page through all required results.

## Related Endpoints

- [DELETE_sites_site_id_marvis_configs_id.md](DELETE_sites_site_id_marvis_configs_id.md) -- deleteSiteMarvisConfigAction uses `DELETE /api/v1/sites/{site_id}/marvis_configs/{id}`.
- [GET_sites_site_id_marvis_configs_count.md](GET_sites_site_id_marvis_configs_count.md) -- countSiteMarvisConfigActions uses `GET /api/v1/sites/{site_id}/marvis_configs/count`.
- [POST_sites_site_id_marvis_configs_id_feedback.md](POST_sites_site_id_marvis_configs_id_feedback.md) -- submitSiteMarvisConfigFeedback uses `POST /api/v1/sites/{site_id}/marvis_configs/{id}/feedback`.

## MistHelper Notes

MistHelper does not currently call `searchSiteMarvisConfigActions`.
Verification source: `git grep -n "searchSiteMarvisConfigActions" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
