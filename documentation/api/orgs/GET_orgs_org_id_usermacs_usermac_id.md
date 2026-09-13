# getOrgUserMac

> getOrgUserMac

## HTTP

`GET /api/v1/orgs/{org_id}/usermacs/{usermac_id}`

## Description

Get Org User MAC

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| usermac_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
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
  },
  "required": [
    "mac"
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

`mistapi.api.v1.orgs.user_macs.getOrgUserMac()`

## Usage Context

Retrieves a specific user MAC address entry by ID.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_usermacs_search.md](GET_orgs_org_id_usermacs_search.md) — Search user MACs
- [PUT_orgs_org_id_usermacs_usermac_id.md](PUT_orgs_org_id_usermacs_usermac_id.md) — Update user MAC

## MistHelper Notes

Not currently used by MistHelper directly.
