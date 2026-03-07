# deleteOrgPsk

> deleteOrgPsk

## HTTP

`DELETE /api/v1/orgs/{org_id}/psks/{psk_id}`

## Description

Delete Org PSK

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| psk_id | string | Yes | PSK ID |

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

`mistapi.api.v1.orgs.psks.deleteOrgPsk()`

## Usage Context

Deletes a Pre-Shared Key (PSK) from the organization.

## Gotchas

- Devices using this PSK lose network access immediately.

## Related Endpoints

- [GET_orgs_org_id_psks.md](GET_orgs_org_id_psks.md) — List PSKs
- [POST_orgs_org_id_psks.md](POST_orgs_org_id_psks.md) — Create PSK

## MistHelper Notes

Used by MistHelper via `listOrgPsks` in Menu 46.
