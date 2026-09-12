# listOrgSsrUpgrades

> listOrgSsrUpgrades

## HTTP

`GET /api/v1/orgs/{org_id}/ssr/upgrade`

## Description

Get List of Org SSR Upgrades

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

Example response

```json
{
  "type": "array",
  "items": {
    "title": "response_ssr_upgrade",
    "required": [
      "channel",
      "counts",
      "device_type",
      "id",
      "status",
      "strategy",
      "versions"
    ],
    "type": "object",
    "properties": {
      "channel": {
        "minLength": 1,
        "type": "string"
      },
      "counts": {
        "title": "response_ssr_upgrade_counts",
        "required": [
          "failed",
          "queued",
          "success",
          "upgrading"
        ],
        "type": "object",
        "properties": {
          "failed": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "queued": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "success": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "upgrading": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        }
      },
      "device_type": {
        "type": "string"
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
      "status": {
        "minLength": 1,
        "type": "string"
      },
      "strategy": {
        "minLength": 1,
        "type": "string"
      },
      "versions": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        }
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "channel": "stable",
        "counts": {
          "failed": 0,
          "queued": 1,
          "success": 0,
          "upgrading": 1
        },
        "device_type": "gateway",
        "id": "ceef2c8a-e2e6-447a-8b27-cb4f3ec1adae",
        "status": "upgrading",
        "strategy": "serial",
        "versions": {}
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

`mistapi.api.v1.utilities.upgrade.listOrgSsrUpgrades()`

## Usage Context

Lists all SSR firmware upgrade records for the organization, including status, target version, and device progress.

## Gotchas

- SSR upgrades can take longer than AP upgrades due to the complexity of routing software.

## Related Endpoints

- [GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) — Get specific upgrade details
- [POST_orgs_org_id_ssr_upgrade.md](POST_orgs_org_id_ssr_upgrade.md) — Start a new SSR upgrade
- [POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) — Cancel an in-progress upgrade

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) to monitor SSR upgrade progress.
