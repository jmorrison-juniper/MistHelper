# deleteInstallerMap

> deleteInstallerMap

## HTTP

`DELETE /api/v1/installer/orgs/{org_id}/sites/{site_name}/maps/{map_id}`

## Description

Delete Map

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| site_name | string | Yes |  |
| map_id | string | Yes |  |

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

`mistapi.api.v1.installer.installer.deleteInstallerMap()`

## Usage Context

Use this endpoint to delete a floor map from a site. Common use cases:

- Removing an incorrect or outdated map
- Cleaning up duplicate maps during site reconfiguration

## Gotchas

- Deleting a map also removes all AP placement data associated with it
- This operation is irreversible -- ensure the correct map is targeted
- APs on the deleted map will become unplaced

## Related Endpoints

- [GET_installer_orgs_org_id_sites_site_name_maps.md](GET_installer_orgs_org_id_sites_site_name_maps.md) -- List maps to find the one to delete
- [POST_installer_orgs_org_id_sites_site_name_maps_map_id.md](POST_installer_orgs_org_id_sites_site_name_maps_map_id.md) -- Create a replacement map

## MistHelper Notes

Not currently used by MistHelper.
