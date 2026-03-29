# disconnectOrgMxEdgeTuntermAps

> disconnectOrgMxEdgeTuntermAps

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/tunterm/disconnect_aps`

## Description

Disconnect AP’s from TunTerm

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
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
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

`mistapi.api.v1.orgs.mxedges.disconnectOrgMxEdgeTuntermAps()`

## Usage Context

Disconnects APs from the tunnel termination service on a Mist Edge.

## Gotchas

- APs will reconnect automatically after disconnection.
- Useful for troubleshooting tunnel issues.

## Related Endpoints

- [POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_bounce_port.md](POST_orgs_org_id_mxedges_mxedge_id_services_tunterm_bounce_port.md) — Bounce port
- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Get Mist Edge

## MistHelper Notes

Not currently used by MistHelper directly.
