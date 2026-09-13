# listInstallerRfTemplatesNames

> listInstallerRfTemplatesNames

## HTTP

`GET /api/v1/installer/orgs/{org_id}/rftemplates`

## Description

Get List of RF Templates

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

Installer List of RF Templates

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
        "id": "bb8a9017-1e36-5d6c-6f2b-551abe8a76a2",
        "name": "RFTemplate 1"
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

`mistapi.api.v1.installer.installer.listInstallerRfTemplatesNames()`

## Usage Context

Use this endpoint to list RF (radio frequency) templates available in the organization. Common use cases:

- Viewing radio configuration templates during site RF planning
- Checking band, channel, and power settings available for site assignment

## Gotchas

- Read-only endpoint -- RF templates cannot be modified through the installer API
- RF templates control radio parameters (band, channel width, power levels, etc.)

## Related Endpoints

- [../orgs/GET_orgs_org_id_rftemplates.md](../orgs/GET_orgs_org_id_rftemplates.md) -- Full admin RF templates list
- [GET_installer_orgs_org_id_sites.md](GET_installer_orgs_org_id_sites.md) -- List sites (RF templates are applied per-site)

## MistHelper Notes

Not currently used by MistHelper. MistHelper accesses RF templates through the full admin API (Menu **37**, **108**).
