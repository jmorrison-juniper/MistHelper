# deleteSiteRfdiagRecording

> deleteSiteRfdiagRecording

## HTTP

`DELETE /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}`

## Description

Delete Recording

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| rfdiag_id | string | Yes |  |

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

`mistapi.api.v1.sites.rfdiags.deleteSiteRfdiagRecording()`

## Usage Context

Deletes an RF diagnostics recording from a site. Removes the stored radio diagnostics capture.

## Gotchas

- Diagnostic data is permanently lost after deletion.

## Related Endpoints

- [GET_sites_site_id_rfdiags.md](GET_sites_site_id_rfdiags.md) — List RF diagnostics
- [POST_sites_site_id_rfdiags.md](POST_sites_site_id_rfdiags.md) — Start new RF diagnostics

## MistHelper Notes

Not currently used by MistHelper directly.
