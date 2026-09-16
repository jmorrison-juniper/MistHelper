# getSiteAutoMapAssignmentStatus

> getSiteAutoMapAssignmentStatus

## HTTP

`GET /api/v1/sites/{site_id}/auto_map_assignment`

## Description

Get the current status of auto map assignment for the site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Auto map assignment status response",
  "properties": {
    "est_time_left": {
      "description": "Only when `status`==`in_progress`, estimated seconds remaining",
      "type": "number"
    },
    "start_time": {
      "description": "Unix timestamp when auto map assignment was started",
      "type": "number"
    },
    "status": {
      "description": "The status of auto map assignment for a given site. enum:\n  * `not_started`: Auto map assignment has not been requested\n  * `in_progress`: Auto map assignment is currently processing\n  * `completed`: The auto map assignment process has completed\n  * `error`: There was an error in the auto map assignment process",
      "enum": [
        "not_started",
        "in_progress",
        "completed",
        "error"
      ],
      "type": "string"
    },
    "stop_time": {
      "description": "Only when `status`==`completed`, Unix timestamp when auto map assignment stopped",
      "type": "number"
    },
    "time_updated": {
      "description": "Unix timestamp when status was last updated",
      "type": "number"
    }
  },
  "required": [
    "status"
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

`mistapi.api.v1.sites.auto_map_assignment.getSiteAutoMapAssignmentStatus()`

## Usage Context

Use this endpoint to read the resource at `/api/v1/sites/{site_id}/auto_map_assignment`.
Common use cases:

- Use it when you need to get the current status of auto map assignment for the site.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `getSiteAutoMapAssignmentStatus(mist_session: mistapi.__api_session.APISession, site_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.

## Related Endpoints

- [DELETE_sites_site_id_auto_map_assignment.md](DELETE_sites_site_id_auto_map_assignment.md) -- cancelSiteAutoMapAssignment uses `DELETE /api/v1/sites/{site_id}/auto_map_assignment`.
- [POST_sites_site_id_auto_map_assignment.md](POST_sites_site_id_auto_map_assignment.md) -- startSiteAutoMapAssignment uses `POST /api/v1/sites/{site_id}/auto_map_assignment`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

Menu Operation **72** exports auto-map assignment status for a selected site.
Verification source: `git grep -n "getSiteAutoMapAssignmentStatus" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
