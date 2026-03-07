# syncOrgCradlepointRouters

> syncOrgCradlepointRouters

## HTTP

`POST /api/v1/orgs/{org_id}/setting/cradlepoint/sync`

## Description

This syncs cradlepoint devices with Mist. We’ll also attempt to use the LLDP data from cradlepoint to identify the linkage against Mist Site / Device

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

`mistapi.api.v1.orgs.integration_cradlepoint.syncOrgCradlepointRouters()`

## Usage Context

Triggers a sync with the Cradlepoint integration.

## Gotchas

- Cradlepoint setup must be configured before syncing.

## Related Endpoints

- [POST_orgs_org_id_setting_cradlepoint_setup.md](POST_orgs_org_id_setting_cradlepoint_setup.md) — Setup
- [GET_orgs_org_id_setting_cradlepoint.md](GET_orgs_org_id_setting_cradlepoint.md) — Get config

## MistHelper Notes

Not currently used by MistHelper directly.
