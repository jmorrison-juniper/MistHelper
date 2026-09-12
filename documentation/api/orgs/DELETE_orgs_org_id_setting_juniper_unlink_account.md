# unlinkOrgFromJuniperCustomerId

> unlinkOrgFromJuniperCustomerId

## HTTP

`DELETE /api/v1/orgs/{org_id}/setting/juniper/unlink_account`

## Description

Unlink Juniper Customer ID
`linked_by` field is only required if there are duplicate account_names.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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

`mistapi.api.v1.orgs.integration_juniper.unlinkOrgFromJuniperCustomerId()`

## Usage Context

Unlinks the Juniper account from the Mist organization.

## Gotchas

- Unlinking may affect license management and support integrations.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings
- [PUT_orgs_org_id_setting.md](PUT_orgs_org_id_setting.md) — Update settings

## MistHelper Notes

Not currently used by MistHelper directly.
