# upgradeDevice

> upgradeDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/upgrade`

## Description

Device Upgrade

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
  "type": "object",
  "properties": {
    "reboot": {
      "type": "boolean",
      "description": "For Switches and Gateways only (APs are automatically rebooted). Reboot device immediately after upgrade is completed",
      "default": false
    },
    "reboot_at": {
      "type": "integer",
      "description": "For Switches and Gateways only and if `reboot`==`true`. Reboot start time in epoch seconds, default is `start_time`",
      "contentEncoding": "int32"
    },
    "snapshot": {
      "type": "boolean",
      "description": "For Junos devices only. Perform recovery snapshot after device is rebooted",
      "default": false
    },
    "start_time": {
      "type": "integer",
      "description": "Firmware download start time in epoch",
      "contentEncoding": "int32"
    },
    "version": {
      "type": "string",
      "description": "Specific version / `stable`, default is to use the latest"
    }
  },
  "required": [
    "version"
  ]
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
      "type": "string",
      "description": "enum: `error`, `inprogress`, `scheduled`, `starting`, `success`"
    },
    "timestamp": {
      "type": "number",
      "description": "Epoch (seconds)",
      "readOnly": true
    }
  },
  "required": [
    "status",
    "timestamp"
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

`mistapi.api.v1.utilities.upgrade.upgradeDevice()`

## Usage Context

Upgrades firmware on a single specific device. Allows precise control over which device receives an upgrade, including version targeting.

## Gotchas

- Device reboots during upgrade and is offline briefly.
- Specify the exact target version — incorrect versions may cause compatibility issues.

## Related Endpoints

- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Site-level batch upgrade
- [POST_orgs_org_id_devices_upgrade.md](POST_orgs_org_id_devices_upgrade.md) — Org-level batch upgrade
- [GET_sites_site_id_devices_versions.md](GET_sites_site_id_devices_versions.md) — Available firmware versions

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) for individual device firmware upgrades.
