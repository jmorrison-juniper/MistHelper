# upgradeSiteDevicesBios

> upgradeSiteDevicesBios

## HTTP

`POST /api/v1/sites/{site_id}/devices/upgrade_bios`

## Description

Upgrade Bios on Multiple Device

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "upgrade_bios_multi",
  "type": "object",
  "properties": {
    "device_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of device id to upgrade bios"
    },
    "models": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of device model to upgrade bios"
    },
    "reboot": {
      "type": "boolean",
      "description": "Reboot device immediately after upgrade is completed",
      "default": false
    },
    "version": {
      "type": "string",
      "description": "Specific bios version",
      "examples": [
        "CDEN_P_EX1_00.15.01.00"
      ]
    }
  }
}
```

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

`mistapi.api.v1.utilities.lan.upgradeSiteDevicesBios()`

## Usage Context

Upgrades BIOS firmware across multiple devices at a site. Targets all eligible devices or a subset by model.

## Gotchas

- Devices reboot as part of the BIOS upgrade.
- Never interrupt a BIOS upgrade — power loss during flash can brick devices.
- Schedule during maintenance windows only.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_upgrade_bios.md](POST_sites_site_id_devices_device_id_upgrade_bios.md) — Single-device BIOS upgrade
- [POST_sites_site_id_devices_upgrade_fpga.md](POST_sites_site_id_devices_upgrade_fpga.md) — Site-level FPGA upgrade

## MistHelper Notes

Not currently used by MistHelper via REST API.
