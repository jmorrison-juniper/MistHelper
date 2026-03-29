# upgradeDeviceFPGA

> upgradeDeviceFPGA

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/upgrade_fpga`

## Description

Upgrade device fpga

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "upgrade_fpga",
  "type": "object",
  "properties": {
    "reboot": {
      "type": "boolean",
      "description": "Reboot device immediately after upgrade is completed",
      "default": false
    },
    "version": {
      "type": "string",
      "description": "Specific fpga version",
      "examples": [
        "REV37"
      ]
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string"
    },
    "timestamp": {
      "type": "number",
      "description": "Epoch (seconds)",
      "readOnly": true
    }
  }
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

`mistapi.api.v1.utilities.lan.upgradeDeviceFPGA()`

## Usage Context

Upgrades the FPGA firmware on a specific device. FPGA updates address hardware-level radio or switching logic.

## Gotchas

- FPGA upgrade requires a device reboot.
- Never interrupt an FPGA upgrade — power loss can brick the device.
- Only needed when explicitly recommended by Juniper TAC or release notes.

## Related Endpoints

- [POST_sites_site_id_devices_upgrade_fpga.md](POST_sites_site_id_devices_upgrade_fpga.md) — Bulk FPGA upgrade for site devices
- [POST_sites_site_id_devices_device_id_upgrade_bios.md](POST_sites_site_id_devices_device_id_upgrade_bios.md) — BIOS upgrade (hardware companion)

## MistHelper Notes

Not currently used by MistHelper via REST API.
