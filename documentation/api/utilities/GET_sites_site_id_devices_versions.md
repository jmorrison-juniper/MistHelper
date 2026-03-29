# listSiteAvailableDeviceVersions

> listSiteAvailableDeviceVersions

## HTTP

`GET /api/v1/sites/{site_id}/devices/versions`

## Description

Get List of Available Device Versions

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  |  |
| model | string | No |  |  | Fetch version for device model, use/combine with `type` as needed (for switch and gateway devices) |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "device_version_item",
    "required": [
      "model",
      "version"
    ],
    "type": "object",
    "properties": {
      "model": {
        "type": "string",
        "description": "Device model (as seen in the device stats)"
      },
      "tag": {
        "type": "string",
        "description": "Annotation, stable / beta / alpha. Or it can be empty or nothing which is likely a dev build"
      },
      "version": {
        "type": "string",
        "description": "Firmware version"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "model": "AP41",
        "tag": "stable",
        "version": "v0.1.543"
      },
      {
        "model": "AP21",
        "version": "v0.1.545"
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

`mistapi.api.v1.utilities.upgrade.listSiteAvailableDeviceVersions()`

## Usage Context

Returns available firmware versions for devices at a specific site, filtered by the device types present at that site.

## Gotchas

- Results are filtered to models actually present at the site, unlike the org-level endpoint which shows all models.

## Related Endpoints

- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Start a site-level firmware upgrade
- [GET_orgs_org_id_devices_versions.md](GET_orgs_org_id_devices_versions.md) — Org-level available versions (all models)

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to present available versions for site-specific upgrades.
