# getOrgDeviceUpgrade

> getOrgDeviceUpgrade

## HTTP

`GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}`

## Description

Get Multiple Devices Upgrade

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| upgrade_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "enable_p2p": {
      "type": "boolean",
      "description": "Whether to allow local AP-to-AP FW upgrade"
    },
    "force": {
      "type": "boolean",
      "description": "Whether to force upgrade when requested version is same as running version"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "strategy": {
      "type": "string",
      "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
    },
    "target_version": {
      "type": "string",
      "description": "Version to upgrade to",
      "examples": [
        "0.14.29411"
      ]
    },
    "upgrades": {
      "type": "array",
      "items": {
        "title": "upgrade_org_devices_upgrade",
        "type": "object",
        "properties": {
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "upgrade": {
            "title": "upgrade_org_devices_upgrade_info",
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
              "start_time": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1717658765
                ]
              },
              "status": {
                "type": "string",
                "description": "status upgrade is in. enum: `cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`, `upgrading`, `queued`"
              },
              "targets": {
                "type": "object",
                "properties": {
                  "download_requested": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which cloud has requested to download firmware"
                  },
                  "downloaded": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which have the firmware downloaded"
                  },
                  "downloading": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which are currently downloading the firmware"
                  },
                  "failed": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which have failed to upgrade"
                  },
                  "reboot_in_progress": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which are rebooting"
                  },
                  "rebooted": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which have rebooted successfully"
                  },
                  "scheduled": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which cloud has scheduled an upgrade for"
                  },
                  "skipped": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of devices MAC Addresses which skipped upgrade since requested version was same as running version. Use force to always upgrade"
                  },
                  "total": {
                    "type": "integer",
                    "description": "Count of devices part of this upgrade",
                    "contentEncoding": "int32"
                  },
                  "upgraded": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Count of devices which have upgraded successfully"
                  }
                },
                "readOnly": true
              }
            }
          }
        }
      },
      "description": ""
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

`mistapi.api.v1.utilities.upgrade.getOrgDeviceUpgrade()`

## Usage Context

Retrieves detailed status of a specific device firmware upgrade, including per-device progress, success/failure counts, and any error messages.

## Gotchas

- The upgrade may take significant time for large device fleets; poll periodically rather than continuously.

## Related Endpoints

- [GET_orgs_org_id_devices_upgrade.md](GET_orgs_org_id_devices_upgrade.md) — List all upgrades to find the upgrade_id
- [POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md) — Cancel this upgrade

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to track individual upgrade progress.
