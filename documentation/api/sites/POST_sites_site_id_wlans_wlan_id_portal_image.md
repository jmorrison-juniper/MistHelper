# uploadSiteWlanPortalImage

> uploadSiteWlanPortalImage

## HTTP

`POST /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_image`

## Description

WLAN Portal Image Upload

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| wlan_id | string | Yes |  |

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

`mistapi.api.v1.sites.wlans.uploadSiteWlanPortalImage()`

## Usage Context

Uploads a portal image (logo or background) for a specific WLAN captive portal.

## Gotchas

- Image must be uploaded as multipart/form-data. Max size limits apply.

## Related Endpoints

- [GET_sites_site_id_wlans_wlan_id.md](GET_sites_site_id_wlans_wlan_id.md) — WLAN details
- [PUT_sites_site_id_wlans_wlan_id.md](PUT_sites_site_id_wlans_wlan_id.md) — Update WLAN

## MistHelper Notes

Not currently used by MistHelper directly.
