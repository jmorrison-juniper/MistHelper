# listInstallerAlarmTemplates

> listInstallerAlarmTemplates

## HTTP

`GET /api/v1/installer/orgs/{org_id}/alarmtemplates`

## Description

Get List of alarm templates

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

Installer List of Alarm Templates

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
        "id": "684dfc5c-fe77-2290-eb1d-ef3d677fe168",
        "name": "AlarmTemplate 1"
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

`mistapi.api.v1.installer.installer.listInstallerAlarmTemplates()`

## Usage Context

Use this endpoint to list alarm templates available in the organization. Common use cases:

- Viewing alarm configuration templates during site setup
- Checking which alarm rules will apply to newly installed devices

## Gotchas

- Read-only endpoint -- alarm templates cannot be modified through the installer API
- Returns the same templates visible in the full admin API but with installer-scoped access

## Related Endpoints

- [../orgs/GET_orgs_org_id_alarmtemplates.md](../orgs/GET_orgs_org_id_alarmtemplates.md) -- Full admin alarm templates list
- [GET_installer_orgs_org_id_sites.md](GET_installer_orgs_org_id_sites.md) -- List sites (alarm templates are applied per-site)

## MistHelper Notes

Not currently used by MistHelper. MistHelper accesses alarm templates through the full admin API (Menu **1**).
