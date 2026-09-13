# unassignInstallerRecentlyClaimedDevice

> unassignInstallerRecentlyClaimedDevice

## HTTP

`DELETE /api/v1/installer/orgs/{org_id}/devices/{device_mac}`

## Description

Unassign recently claimed devices

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

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

`mistapi.api.v1.installer.installer.unassignInstallerRecentlyClaimedDevice()`

## Usage Context

Use this endpoint to unassign a recently claimed device from the organization. Common use cases:

- Removing a device that was claimed by mistake
- Releasing a device so it can be claimed by a different organization

## Gotchas

- Only works on recently claimed devices visible to the installer scope
- Does not physically disconnect the device -- it only removes the cloud assignment
- The device may need a factory reset before it can be claimed by another organization

## Related Endpoints

- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List devices to find the one to unassign
- [POST_installer_orgs_org_id_devices.md](POST_installer_orgs_org_id_devices.md) -- Claim a device back

## MistHelper Notes

Not currently used by MistHelper.
