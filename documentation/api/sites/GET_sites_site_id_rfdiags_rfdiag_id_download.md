# downloadSiteRfdiagRecording

> downloadSiteRfdiagRecording

## HTTP

`GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download`

## Description

Download Recording
Download raw_events blob

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

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
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

`mistapi.api.v1.sites.rfdiags.downloadSiteRfdiagRecording()`

## Usage Context

Downloads RF diagnostics recording data as a file. Used for offline analysis of RF environment.

## Gotchas

- Returns binary file data, not JSON. Handle the response as a file download.

## Related Endpoints

- [GET_sites_site_id_rfdiags_rfdiag_id.md](GET_sites_site_id_rfdiags_rfdiag_id.md) — Recording metadata
- [GET_sites_site_id_rfdiags.md](GET_sites_site_id_rfdiags.md) — List recordings

## MistHelper Notes

Not currently used by MistHelper directly.
