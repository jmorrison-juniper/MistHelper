# uploadOrgPskPortalImage

> uploadOrgPskPortalImage

## HTTP

`POST /api/v1/orgs/{org_id}/pskportals/{pskportal_id}/portal_image`

## Description

Upload background image for PskPortal

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| pskportal_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "Binary file",
      "contentEncoding": "base64"
    },
    "json": {
      "type": "string",
      "description": "JSON string describing the upload"
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

`mistapi.api.v1.orgs.psk_portals.uploadOrgPskPortalImage()`

## Usage Context

Uploads a portal image for a specific PSK portal.

## Gotchas

- Image must meet size and format requirements.

## Related Endpoints

- [GET_orgs_org_id_pskportals_id.md](GET_orgs_org_id_pskportals_id.md) — Get PSK portal
- [GET_orgs_org_id_pskportals.md](GET_orgs_org_id_pskportals.md) — List PSK portals

## MistHelper Notes

Not currently used by MistHelper directly.
