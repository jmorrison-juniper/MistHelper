# listInstallerSiteGroups

> listInstallerSiteGroups

## HTTP

`GET /api/v1/installer/orgs/{org_id}/sitegroups`

## Description

Get List of Site Groups

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

Installer List of Site Groups

```json
{
  "type": "array",
  "items": {
    "title": "installers_item",
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Entry #1"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "id": "581328b6-e382-f54e-c9dc-999983183a34",
        "name": "SiteGroup 1"
      }
    ]
  ]
}
```

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

`mistapi.api.v1.installer.installer.listInstallerSiteGroups()`

## Usage Context

Use this endpoint to list site groups available in the organization. Common use cases:

- Viewing site groupings to understand organizational structure during deployment
- Selecting the appropriate site group for device assignment

## Gotchas

- Read-only endpoint -- site groups cannot be created or modified through the installer API
- Site groups are used for bulk configuration management and are typically set up by admins before installation

## Related Endpoints

- [GET_installer_orgs_org_id_sites.md](GET_installer_orgs_org_id_sites.md) -- List sites (sites belong to site groups)
- [../orgs/GET_orgs_org_id_sitegroups.md](../orgs/GET_orgs_org_id_sitegroups.md) -- Full admin site groups list

## MistHelper Notes

Not currently used by MistHelper.
