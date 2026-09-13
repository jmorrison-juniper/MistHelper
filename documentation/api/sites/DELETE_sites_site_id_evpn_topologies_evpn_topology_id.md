# deleteSiteEvpnTopology

> deleteSiteEvpnTopology

## HTTP

`DELETE /api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id}`

## Description

Delete the site EVPN Topology

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| evpn_topology_id | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.sites.evpn_topologies.deleteSiteEvpnTopology()`

## Usage Context

Deletes an EVPN topology configuration at a site. Removes EVPN-VXLAN fabric settings.

## Gotchas

- **DESTRUCTIVE**: Deleting an active EVPN topology disrupts the entire campus switching fabric.
- Ensure all devices are properly reconfigured before removal.

## Related Endpoints

- [GET_sites_site_id_evpn_topologies.md](GET_sites_site_id_evpn_topologies.md) — List EVPN topologies
- [POST_sites_site_id_evpn_topologies.md](POST_sites_site_id_evpn_topologies.md) — Create EVPN topology

## MistHelper Notes

Not currently used by MistHelper directly.
