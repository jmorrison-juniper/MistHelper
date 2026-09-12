# zeroizeSiteFipsAllAps

> zeroizeSiteFipsAllAps

## HTTP

`POST /api/v1/sites/{site_id}/devices/zeroize`

## Description

Zeroize all FIPS APs in the Site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "password": {
      "type": "string",
      "description": "FIPS zeroize password"
    }
  },
  "required": [
    "password"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.utilities.wi-fi.zeroizeSiteFipsAllAps()`

## Usage Context

Zeroizes all FIPS APs at a site. Performs a factory reset that securely erases all configuration and cryptographic keys per FIPS 140-2 requirements.

## Gotchas

- **DESTRUCTIVE**: This operation cannot be undone. All device configuration and keys are permanently erased.
- Only applies to APs in FIPS mode.
- Devices must be re-provisioned from scratch after zeroization.

## Related Endpoints

- [POST_sites_site_id_devices_restart.md](POST_sites_site_id_devices_restart.md) — Less destructive restart option

## MistHelper Notes

Not currently used by MistHelper via REST API.
