# rejoinSiteIotEndpointZigbee

> rejoinSiteIotEndpointZigbee

## HTTP

`POST /api/v1/sites/{site_id}/iotendpoints/{id}/zigbee_rejoin`

## Description

Trigger a Zigbee endpoint to rejoin the network

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

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

`mistapi.api.v1.sites.iotendpoints.rejoinSiteIotEndpointZigbee()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/iotendpoints/{id}/zigbee_rejoin`.
Common use cases:

- Use it when you need to trigger a Zigbee endpoint to rejoin the network.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `rejoinSiteIotEndpointZigbee(mist_session: mistapi.__api_session.APISession, site_id: str, id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [GET_sites_site_id_iotendpoints_count.md](GET_sites_site_id_iotendpoints_count.md) -- countSiteIotEndpoints uses `GET /api/v1/sites/{site_id}/iotendpoints/count`.
- [GET_sites_site_id_iotendpoints_search.md](GET_sites_site_id_iotendpoints_search.md) -- searchSiteIotEndpoints uses `GET /api/v1/sites/{site_id}/iotendpoints/search`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

MistHelper does not currently call `rejoinSiteIotEndpointZigbee`.
Verification source: `git grep -n "rejoinSiteIotEndpointZigbee" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
