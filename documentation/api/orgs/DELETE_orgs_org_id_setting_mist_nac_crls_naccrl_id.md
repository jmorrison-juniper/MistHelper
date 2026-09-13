# deleteOrgNacCrl

> deleteOrgNacCrl

## HTTP

`DELETE /api/v1/orgs/{org_id}/setting/mist_nac_crls/{naccrl_id}`

## Description

Delete NAC Org CRL file is a DELETE request to delete CRL file identified by its ID (ID assigned on file upload/creation)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| naccrl_id | string | Yes |  |

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

`mistapi.api.v1.orgs.nac_crl.deleteOrgNacCrl()`

## Usage Context

Deletes a Certificate Revocation List (CRL) from the Mist NAC configuration.

## Gotchas

- Revoked certificates in this CRL will no longer be checked.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings
- [POST_orgs_org_id_setting_mist_nac_crls.md](POST_orgs_org_id_setting_mist_nac_crls.md) — Upload CRL

## MistHelper Notes

Not currently used by MistHelper directly.
