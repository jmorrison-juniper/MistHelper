# addSiteMapImage

> addSiteMapImage

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/image`

## Description

Add image map is a multipart POST which has an file (Image) and an optional json parameter

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

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

`mistapi.api.v1.sites.maps.addSiteMapImage()`

## Usage Context

Uploads a floor plan image for a specific map. Replaces the existing image.

## Gotchas

- Image must be uploaded as multipart/form-data. Supported formats: PNG, JPG, PDF.

## Related Endpoints

- [DELETE_sites_site_id_maps_map_id_image.md](DELETE_sites_site_id_maps_map_id_image.md) — Delete map image
- [POST_sites_site_id_maps_map_id_replace.md](POST_sites_site_id_maps_map_id_replace.md) — Replace map

## MistHelper Notes

Not currently used by MistHelper directly.
