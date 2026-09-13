# attachSiteAssetImage

> attachSiteAssetImage

## HTTP

`POST /api/v1/sites/{site_id}/assets/{asset_id}/image`

## Description

Attach Image to Site Asset

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| asset_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "required": [
    "file"
  ],
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "Binary file",
      "contentEncoding": "base64"
    },
    "json": {
      "type": "string"
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

`mistapi.api.v1.sites.assets.attachSiteAssetImage()`

## Usage Context

Uploads an image for a specific BLE asset. Images are used for visual identification in the dashboard.

## Gotchas

- Image file must be uploaded as multipart/form-data.

## Related Endpoints

- [DELETE_sites_site_id_assets_asset_id_image.md](DELETE_sites_site_id_assets_asset_id_image.md) — Delete asset image
- [POST_sites_site_id_assets.md](POST_sites_site_id_assets.md) — Create asset

## MistHelper Notes

Not currently used by MistHelper directly.
