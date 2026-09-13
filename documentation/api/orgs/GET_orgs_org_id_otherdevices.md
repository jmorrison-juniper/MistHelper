# listOrgOtherDevices

> listOrgOtherDevices

## HTTP

`GET /api/v1/orgs/{org_id}/otherdevices`

## Description

Get List of Org other devices (3rd party devices)

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
| vendor | string | No |  |  |  |
| mac | string | No |  |  |  |
| serial | string | No |  |  |  |
| model | string | No |  |  |  |
| name | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "device_other",
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "device_mac": {
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
      "mac": {
        "type": "string"
      },
      "model": {
        "type": "string"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "serial": {
        "type": "string"
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      },
      "state": {
        "type": "string"
      },
      "vendor": {
        "type": "string"
      },
      "vendor_api_id": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 1676983730,
        "device_mac": "001122334455",
        "id": "ae9dee49-69e7-4710-a114-5b827a777738",
        "mac": "5c5b35000018",
        "model": "AP41",
        "modified_time": 1676983730,
        "name": "hallway",
        "org_id": "2818e386-8dec-2562-9ede-5b8a0fbbdc71",
        "serial": "FXLH2015150025",
        "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
        "vendor": "cradlepoint"
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

`mistapi.api.v1.orgs.devices_-_others.listOrgOtherDevices()`

## Usage Context

Lists all non-Juniper (third-party) devices in the organization.

## Gotchas

- Includes devices managed via SNMP or other protocols.

## Related Endpoints

- [GET_orgs_org_id_otherdevices_device_mac.md](GET_orgs_org_id_otherdevices_device_mac.md) — Get specific device
- [GET_orgs_org_id_otherdevices_events_search.md](GET_orgs_org_id_otherdevices_events_search.md) — Events

## MistHelper Notes

Not currently used by MistHelper directly.
