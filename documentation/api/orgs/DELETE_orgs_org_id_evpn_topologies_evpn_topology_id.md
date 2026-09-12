# deleteOrgEvpnTopology

> deleteOrgEvpnTopology

## HTTP

`DELETE /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}`

## Description

Delete the Org EVPN Topology

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
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

`mistapi.api.v1.orgs.evpn_topologies.deleteOrgEvpnTopology()`

## Usage Context

Deletes an EVPN topology from the organization.

## Gotchas

- Active EVPN topologies must be decommissioned before deletion.

## Related Endpoints

- [GET_orgs_org_id_evpn_topologies.md](GET_orgs_org_id_evpn_topologies.md) — List topologies
- [POST_orgs_org_id_evpn_topologies.md](POST_orgs_org_id_evpn_topologies.md) — Create topology

## MistHelper Notes

Not currently used by MistHelper directly.
