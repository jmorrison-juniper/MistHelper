# countOrgUserMacs

> countOrgUserMacs

## HTTP

`GET /api/v1/orgs/{org_id}/usermacs/count`

## Description

Count by Distinct Attributes of User MACs

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
| distinct | string | Yes |  |  | Attribute to count by. enum: `mac`, `name`, `labels`, `org_id` |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "description": "End timestamp",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "description": "Number of results to return",
      "contentEncoding": "int32"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "user_mac",
        "required": [
          "mac"
        ],
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
          "labels": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "byod",
                "flr1"
              ]
            ]
          },
          "mac": {
            "type": "string",
            "description": "Only non-local-admin MAC is accepted",
            "examples": [
              "5684dae9ac8b"
            ]
          },
          "name": {
            "type": "string",
            "examples": [
              "Printer2"
            ]
          },
          "notes": {
            "type": "string",
            "examples": [
              "mac address refers to Canon printers"
            ]
          },
          "radius_group": {
            "type": "string",
            "examples": [
              "VIP"
            ]
          },
          "vlan": {
            "type": "string",
            "examples": [
              "30"
            ]
          }
        }
      },
      "description": "List of user MAC entries"
    },
    "start": {
      "type": "integer",
      "description": "Start timestamp",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "description": "Total number of results",
      "contentEncoding": "int32"
    }
  },
  "description": "User MACs count response"
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

`mistapi.api.v1.orgs.user_macs.countOrgUserMacs()`

## Usage Context

Returns the count of user MAC addresses matching the specified filters.

## Gotchas

- User MACs are MAC addresses labeled with user identities.

## Related Endpoints

- [GET_orgs_org_id_usermacs_search.md](GET_orgs_org_id_usermacs_search.md) — Search user MACs
- [GET_orgs_org_id_usermacs_usermac_id.md](GET_orgs_org_id_usermacs_usermac_id.md) — Get specific user MAC

## MistHelper Notes

Not currently used by MistHelper directly.
