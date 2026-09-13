# deleteOrgNacRule

> deleteOrgNacRule

## HTTP

`DELETE /api/v1/orgs/{org_id}/nacrules/{nacrule_id}`

## Description

Delete Org NAC Rule

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| nacrule_id | string | Yes |  |

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

`mistapi.api.v1.orgs.nac_rules.deleteOrgNacRule()`

## Usage Context

Deletes a NAC rule from the organization.

## Gotchas

- Removing a rule may change network access behavior for matching clients.

## Related Endpoints

- [GET_orgs_org_id_nacrules.md](GET_orgs_org_id_nacrules.md) — List rules
- [POST_orgs_org_id_nacrules.md](POST_orgs_org_id_nacrules.md) — Create rule

## MistHelper Notes

Used by MistHelper via `listOrgNacRules` for NAC exports.
