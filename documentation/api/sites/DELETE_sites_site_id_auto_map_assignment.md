# cancelSiteAutoMapAssignment

> cancelSiteAutoMapAssignment

## HTTP

`DELETE /api/v1/sites/{site_id}/auto_map_assignment`

## Description

Cancel an in-progress auto map assignment operation for the site. Validates that auto map assignment is currently running, notifies all APs to fetch new configuration, and sends a cancel command to the orchestration service.

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
| 400 | Auto map assignment not in progress |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.auto_map_assignment.cancelSiteAutoMapAssignment()`

## Usage Context

Use this endpoint to remove or stop the resource at
`/api/v1/sites/{site_id}/auto_map_assignment`.
Common use cases:

- Use it when you need to cancel an in-progress auto map assignment operation for the site.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `cancelSiteAutoMapAssignment(mist_session: mistapi.__api_session.APISession, site_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [GET_sites_site_id_auto_map_assignment.md](GET_sites_site_id_auto_map_assignment.md) -- getSiteAutoMapAssignmentStatus uses `GET /api/v1/sites/{site_id}/auto_map_assignment`.
- [POST_sites_site_id_auto_map_assignment.md](POST_sites_site_id_auto_map_assignment.md) -- startSiteAutoMapAssignment uses `POST /api/v1/sites/{site_id}/auto_map_assignment`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

MistHelper does not currently call `cancelSiteAutoMapAssignment`.
Verification source: `git grep -n "cancelSiteAutoMapAssignment" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
