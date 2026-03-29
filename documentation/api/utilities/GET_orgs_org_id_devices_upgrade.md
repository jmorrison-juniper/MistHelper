# listOrgDeviceUpgrades

> listOrgDeviceUpgrades

## HTTP

`GET /api/v1/orgs/{org_id}/devices/upgrade`

## Description

Get List of Org multiple devices upgrades

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

OK

```json
{
  "type": "array",
  "items": {
    "title": "upgrade_org_devices_item",
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
      "site_upgrades": {
        "type": "array",
        "items": {
          "title": "upgrade_org_devices_item_site_upgrade",
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
            "upgrade_id": {
              "type": "string",
              "contentEncoding": "uuid",
              "examples": [
                "ebbdbd0b-1bcf-4e55-8a6a-3416049a52b1"
              ]
            }
          }
        },
        "description": ""
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "id": "466f6eca-6276-4993-bfeb-53cbbbba6f88",
        "site_upgrades": [
          {
            "site_id": "72771e6a-6f5e-4de4-a5b9-1266c4197811",
            "upgrade_id": "174bda0-06a3-40ee-b918-d9cbde303690"
          }
        ]
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

`mistapi.api.v1.utilities.upgrade.listOrgDeviceUpgrades()`

## Usage Context

Lists all device firmware upgrade records for the organization, including status, target version, device counts, and completion percentage. Use this to monitor upgrade progress and review upgrade history.

## Gotchas

- Includes both active and completed upgrades — filter by status for active-only.
- Results are paginated for orgs with extensive upgrade history.

## Related Endpoints

- [GET_orgs_org_id_devices_upgrade_upgrade_id.md](GET_orgs_org_id_devices_upgrade_upgrade_id.md) — Get details of a specific upgrade
- [POST_orgs_org_id_devices_upgrade.md](POST_orgs_org_id_devices_upgrade.md) — Start a new upgrade
- [POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md) — Cancel an in-progress upgrade

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to check upgrade status and history.
