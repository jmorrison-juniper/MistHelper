# upgradeDeviceBios

> upgradeDeviceBios

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/upgrade_bios`

## Description

Upgrade device bios

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
  "title": "upgrade_bios",
  "type": "object",
  "properties": {
    "reboot": {
      "type": "boolean",
      "description": "Reboot device immediately after upgrade is completed",
      "default": false
    },
    "version": {
      "type": "string",
      "description": "Specific bios version",
      "examples": [
        "CDEN_P_EX1_00.20.01.00"
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

`mistapi.api.v1.utilities.lan.upgradeDeviceBios()`

## Usage Context

Upgrades the BIOS firmware on a specific device. BIOS updates are separate from the main device firmware and typically address hardware-level issues.

## Gotchas

- BIOS upgrade requires a device reboot.
- Never interrupt a BIOS upgrade — power loss during BIOS flash can brick the device.
- Only needed when explicitly recommended by Juniper TAC or release notes.

## Related Endpoints

- [POST_sites_site_id_devices_upgrade_bios.md](POST_sites_site_id_devices_upgrade_bios.md) — Bulk BIOS upgrade for site devices
- [POST_sites_site_id_devices_device_id_upgrade_fpga.md](POST_sites_site_id_devices_device_id_upgrade_fpga.md) — FPGA upgrade (hardware companion)

## MistHelper Notes

Not currently used by MistHelper via REST API.
