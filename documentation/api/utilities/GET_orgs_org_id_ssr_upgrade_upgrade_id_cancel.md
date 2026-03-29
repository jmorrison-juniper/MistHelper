# getOrgSsrUpgrade

> getOrgSsrUpgrade

## HTTP

`GET /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`

## Description

Get Specific Org SSR Upgrade

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
    "channel": {
      "minLength": 1,
      "type": "string"
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
    "targets": {
      "title": "response_ssr_upgrade_status_targets",
      "required": [
        "failed",
        "queued",
        "success",
        "upgrading"
      ],
      "type": "object",
      "properties": {
        "failed": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "queued": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "success": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "upgrading": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        }
      }
    },
    "versions": {
      "type": "object"
    }
  },
  "required": [
    "channel",
    "id",
    "status",
    "targets",
    "versions"
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

`mistapi.api.v1.utilities.upgrade.getOrgSsrUpgrade()`

## Usage Context

Retrieves detailed status of a specific SSR firmware upgrade including per-device progress, success/failure counts, and error details.

## Gotchas

- Despite the URL containing 'cancel', this is a GET endpoint that retrieves upgrade status.

## Related Endpoints

- [GET_orgs_org_id_ssr_upgrade.md](GET_orgs_org_id_ssr_upgrade.md) — List all SSR upgrades
- [POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) — Actually cancel the upgrade (POST)

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) to track individual SSR upgrade status.
