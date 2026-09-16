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

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
