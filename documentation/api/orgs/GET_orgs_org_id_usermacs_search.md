# searchOrgUserMacs

> searchOrgUserMacs

## HTTP

`GET /api/v1/orgs/{org_id}/usermacs/search`

## Description

Search Org User MACs

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
| mac | string | No |  |  | Partial/full MAC address |
| labels | array | No |  |  | Optional, array of strings of labels |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |

## Request Body

None.

## Response

### 200

OK

```json
{
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
  "description": "",
  "examples": [
    [
      {
        "id": "111cafd2-ba1b-5169-bfcb-9cdf1d473ddb",
        "labels": [
          "flor1",
          "bld4"
        ],
        "mac": "921b638445cd",
        "notes": "mac address refers to Canon printers",
        "vlan": "30"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.user_macs.searchOrgUserMacs()`

## Usage Context

Searches for user MAC addresses across the organization.

## Gotchas

- Returns paginated results; use `limit` and `page` parameters.

## Related Endpoints

- [GET_orgs_org_id_usermacs_count.md](GET_orgs_org_id_usermacs_count.md) — Count user MACs
- [GET_orgs_org_id_usermacs_usermac_id.md](GET_orgs_org_id_usermacs_usermac_id.md) — Get specific user MAC

## MistHelper Notes

Not currently used by MistHelper directly.
