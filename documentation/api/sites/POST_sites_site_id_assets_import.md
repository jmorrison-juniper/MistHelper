# importSiteAssets

> importSiteAssets

## HTTP

`POST /api/v1/sites/{site_id}/assets/import`

## Description

Import Site Assets. 

It can be done via a CSV file or a JSON payload.

## CSV File Format
```csv
name,mac
"asset_name",5c5b53010101
```

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| upsert | string | No |  |  | API will replace the assets with same mac if provided `upsert`==`True`, otherwise will report in errors in response. |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "CSV file",
      "contentEncoding": "base64"
    }
  }
}
```

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

`mistapi.api.v1.sites.assets.importSiteAssets()`

## Usage Context

Bulk imports BLE assets from a CSV file. Enables mass registration of asset beacons.

## Gotchas

- CSV format must match expected schema. Duplicate MAC addresses are rejected.

## Related Endpoints

- [POST_sites_site_id_assets.md](POST_sites_site_id_assets.md) — Create single asset
- [GET_sites_site_id_assets.md](GET_sites_site_id_assets.md) — List assets

## MistHelper Notes

Not currently used by MistHelper directly.
