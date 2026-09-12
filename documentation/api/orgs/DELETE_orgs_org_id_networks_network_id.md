# deleteOrgNetwork

> deleteOrgNetwork

## HTTP

`DELETE /api/v1/orgs/{org_id}/networks/{network_id}`

## Description

Delete Organization Network

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| network_id | string | Yes |  |

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

`mistapi.api.v1.orgs.networks.deleteOrgNetwork()`

## Usage Context

Deletes a network definition from the organization.

## Gotchas

- Ensure no VLANs or policies reference this network.

## Related Endpoints

- [GET_orgs_org_id_networks.md](GET_orgs_org_id_networks.md) — List networks
- [POST_orgs_org_id_networks.md](POST_orgs_org_id_networks.md) — Create network

## MistHelper Notes

Used by MistHelper via `listOrgNetworks` in Menu 4.
