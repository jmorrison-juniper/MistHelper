# preemptSitesMxTunnel

> preemptSitesMxTunnel

## HTTP

`POST /api/v1/sites/{site_id}/mxtunnels/{mxtunnel_id}/preempt_aps`

## Description

To preempt AP’s which are not connected to preferred peer to the preferred peer

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| mxtunnel_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "response_mxtunnels_preempt_aps",
  "required": [
    "preempted_aps"
  ],
  "type": "object",
  "properties": {
    "preempted_aps": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.mxedge.preemptSitesMxTunnel()`

## Usage Context

Preempts APs connected to a Mist Tunnel cluster, forcing them to reconnect to their preferred tunnel endpoint. Used during maintenance or after HA failover recovery.

## Gotchas

- APs briefly disconnect from the tunnel during preemption and reconnect to the preferred endpoint.
- Only relevant for sites using Mist Edge / Mist Tunnel architecture.

## Related Endpoints

- [GET_orgs_org_id_mxtunnels.md](../orgs/GET_orgs_org_id_mxtunnels.md) — List org tunnels

## MistHelper Notes

Not currently used by MistHelper via REST API.
