# optimizeInstallerRrm

> optimizeInstallerRrm

## HTTP

`GET /api/v1/installer/sites/{site_name}/optimize`

## Description

After installation is considered complete (APs are placed on maps, all powered up), you can trigger an optimize operation where RRM will kick in (and maybe other things in the future) before it’s automatically scheduled.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_name | string | Yes |  |

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

`mistapi.api.v1.installer.installer.optimizeInstallerRrm()`

## Usage Context

Use this endpoint to trigger RRM (Radio Resource Management) optimization after AP installation is complete. Common use cases:

- Running RF optimization after all APs are placed on maps and powered up
- Optimizing channel and power assignments based on actual RF environment

## Gotchas

- Should only be triggered after all APs at the site are installed, placed on maps, and powered on
- Optimization takes time to complete and results are not immediate
- Running optimization prematurely (before all APs are up) may produce suboptimal results
- Uses `{site_name}` instead of site ID (installer API convention)

## Related Endpoints

- [GET_installer_orgs_org_id_sites.md](GET_installer_orgs_org_id_sites.md) -- List sites to find the site name
- [GET_installer_orgs_org_id_sites_site_name_maps.md](GET_installer_orgs_org_id_sites_site_name_maps.md) -- Verify maps and AP placement before optimization
- [../sites/POST_sites_site_id_rrm_optimize.md](../sites/POST_sites_site_id_rrm_optimize.md) -- Full admin RRM optimization

## MistHelper Notes

Not currently used by MistHelper.
