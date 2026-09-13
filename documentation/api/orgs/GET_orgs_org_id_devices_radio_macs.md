# listOrgApsMacs

> listOrgApsMacs

## HTTP

`GET /api/v1/orgs/{org_id}/devices/radio_macs`

## Description

For some scenarios like E911 or security systems, the BSSIDs are required to identify which AP the client is connecting to. Then the location of the AP can be used as the approximate location of the client.

Each radio MAC can have 16 BSSIDs (enumerate the last octet from 0-F)

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
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "minItems": 1,
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "ap_radio_mac",
    "required": [
      "mac",
      "radio_macs"
    ],
    "type": "object",
    "properties": {
      "mac": {
        "minLength": 1,
        "type": "string",
        "examples": [
          "5c5b350001a0"
        ]
      },
      "radio_macs": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "5c5b350001a0",
            "5c5b350001a1"
          ]
        ]
      }
    },
    "examples": [
      {
        "mac": "5c5b350001a0",
        "radio_macs": [
          "5c5b350001a0",
          "5c5b350001a1"
        ]
      }
    ]
  },
  "description": "",
  "examples": [
    [
      {
        "mac": "5c5b35000001",
        "radio_macs": [
          "5c5b35000040",
          "5c5b35000050",
          "5c5b35000060"
        ]
      },
      {
        "mac": "5c5b45000001",
        "radio_macs": [
          "5c5b45000040",
          "5c5b45000050",
          "5c5b45000060"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.devices.listOrgApsMacs()`

## Usage Context

Retrieves the radio MAC addresses for all APs in the organization.

## Gotchas

- Each AP has multiple radio MACs (one per radio band).

## Related Endpoints

- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices
- [GET_orgs_org_id_devices.md](GET_orgs_org_id_devices.md) — List devices

## MistHelper Notes

Not currently used by MistHelper directly.
