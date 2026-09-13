# deleteOrgSso

> deleteOrgSso

## HTTP

`DELETE /api/v1/orgs/{org_id}/ssos/{sso_id}`

## Description

Delete Org SSO Configuration

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sso_id | string | Yes |  |

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

`mistapi.api.v1.orgs.sso.deleteOrgSso()`

## Usage Context

Deletes an SSO configuration from the organization.

## Gotchas

- SSO users lose access until a new SSO is configured.

## Related Endpoints

- [GET_orgs_org_id_ssos.md](GET_orgs_org_id_ssos.md) — List SSOs
- [POST_orgs_org_id_ssos.md](POST_orgs_org_id_ssos.md) — Create SSO

## MistHelper Notes

Used by MistHelper via `listOrgSsos` in Menu 57.
