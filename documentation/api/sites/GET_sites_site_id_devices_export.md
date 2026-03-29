# exportSiteDevices

> exportSiteDevices

## HTTP

`GET /api/v1/sites/{site_id}/devices/export`

## Description

To download the exported device information

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.sites.devices.exportSiteDevices()`

## Usage Context

Exports site device inventory in CSV format. Useful for bulk operations and offline analysis.

## Gotchas

- Returns CSV text, not JSON. Parse accordingly.

## Related Endpoints

- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — List devices (JSON)
- [GET_sites_site_id_devices_search.md](GET_sites_site_id_devices_search.md) — Search devices

## MistHelper Notes

Not currently used by MistHelper directly. MistHelper generates its own CSV exports.
