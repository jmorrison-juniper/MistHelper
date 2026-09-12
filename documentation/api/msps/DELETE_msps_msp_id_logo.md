# deleteMspLogo

> deleteMspLogo

## HTTP

`DELETE /api/v1/msps/{msp_id}/logo`

## Description

Delete MSP Logo

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

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

`mistapi.api.v1.msps.logo.deleteMspLogo()`

## Usage Context

Removes the MSP branding logo, reverting to the default Juniper/Mist branding. Use this when rebranding or removing white-label customization.

## Gotchas

- Deletion is immediate; cached versions of the logo may still appear briefly in browser sessions.

## Related Endpoints

- [POST_msps_msp_id_logo.md](POST_msps_msp_id_logo.md) — Upload a new logo
- [PUT_msps_msp_id.md](PUT_msps_msp_id.md) — Update other MSP branding settings

## MistHelper Notes

Not currently used by MistHelper directly.
