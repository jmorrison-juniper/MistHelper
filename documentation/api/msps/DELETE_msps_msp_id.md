# deleteMsp

> deleteMsp

## HTTP

`DELETE /api/v1/msps/{msp_id}`

## Description

Deleting MSP removes the MSP and OrgGroup under the MSP as well as all privileges associated with them. It does not remove any Org or Admins

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

`mistapi.api.v1.msps.msps.deleteMsp()`

## Usage Context

Deletes an MSP tenant. This is a destructive operation that removes the MSP management layer. Organizations under the MSP may need to be reassigned or will lose MSP-level management.

## Gotchas

- This is irreversible. Ensure all child organizations are handled before deletion.
- Only MSP super-admins can delete an MSP.
- Active licenses pooled under the MSP may be affected.

## Related Endpoints

- [GET_msps_msp_id.md](GET_msps_msp_id.md) — Verify MSP details before deletion
- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — Check for child organizations first
- [GET_msps_msp_id_licenses.md](GET_msps_msp_id_licenses.md) — Check license state before deleting

## MistHelper Notes

Not currently used by MistHelper directly.
