# postMspLogo

> postMspLogo

## HTTP

`POST /api/v1/msps/{msp_id}/logo`

## Description

Upload Logo (only for advanced msp tier)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "msp_logo",
  "type": "object",
  "properties": {
    "logo_url": {
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

`mistapi.api.v1.msps.logo.postMspLogo()`

## Usage Context

Uploads a logo image for MSP branding on the Mist dashboard and guest portals. The logo is displayed in the MSP management interface and can be inherited by child organizations for white-label deployments.

## Gotchas

- The request body is `multipart/form-data` with the image file, not JSON.
- Image format and size constraints apply (typically PNG/JPEG, reasonable file size).

## Related Endpoints

- [DELETE_msps_msp_id_logo.md](DELETE_msps_msp_id_logo.md) — Remove the uploaded logo
- [PUT_msps_msp_id.md](PUT_msps_msp_id.md) — Update other MSP settings

## MistHelper Notes

Not currently used by MistHelper directly.
