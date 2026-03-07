# getOrgStats

> getOrgStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats`

## Description

Get Org Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "alarmtemplate_id": {
      "type": "string",
      "contentEncoding": "uuid"
    },
    "allow_mist": {
      "type": "boolean"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "name": {
      "type": "string"
    },
    "num_devices": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_devices_connected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_devices_disconnected": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_inventory": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "num_sites": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "orggroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    },
    "session_expiry": {
      "type": "integer",
      "contentEncoding": "int64"
    },
    "sle": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "stats_org_sle",
        "required": [
          "path"
        ],
        "type": "object",
        "properties": {
          "path": {
            "type": "string"
          },
          "user_minutes": {
            "title": "stats_org_sle_user_minutes",
            "required": [
              "ok",
              "total"
            ],
            "type": "object",
            "properties": {
              "ok": {
                "type": "number"
              },
              "total": {
                "type": "number"
              }
            }
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "alarmtemplate_id",
    "allow_mist",
    "created_time",
    "id",
    "modified_time",
    "msp_id",
    "name",
    "num_devices",
    "num_devices_connected",
    "num_devices_disconnected",
    "num_inventory",
    "num_sites",
    "orggroup_ids",
    "session_expiry",
    "sle"
  ],
  "description": "Org statistics"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.stats.getOrgStats()`

## Usage Context

Retrieves overall organization statistics summary.

## Gotchas

- Returns aggregated counts and health metrics across all sites.

## Related Endpoints

- [GET_orgs_org_id_stats_sites.md](GET_orgs_org_id_stats_sites.md) — Per-site stats
- [GET_orgs_org_id_stats_devices.md](GET_orgs_org_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
