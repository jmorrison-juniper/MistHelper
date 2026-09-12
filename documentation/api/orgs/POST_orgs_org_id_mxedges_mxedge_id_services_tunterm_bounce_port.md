# bounceOrgMxEdgeDataPorts

> bounceOrgMxEdgeDataPorts

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/tunterm/bounce_port`

## Description

Bounce TunTerm Data Ports

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxedge_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "hold_time": {
      "type": "integer",
      "description": "In milli seconds, hold time between multiple port bounces",
      "contentEncoding": "int32"
    },
    "ports": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of ports to bounce"
    }
  },
  "required": [
    "ports"
  ]
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.mxedges.bounceOrgMxEdgeDataPorts()`

## Usage Context

Bounces (resets) a specific tunnel termination port on a Mist Edge.

## Gotchas

- Bouncing a port temporarily disconnects all APs using that port.

## Related Endpoints

- [POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_disconnect_aps.md](POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_disconnect_aps.md) — Disconnect APs
- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Get Mist Edge

## MistHelper Notes

Not currently used by MistHelper directly.
