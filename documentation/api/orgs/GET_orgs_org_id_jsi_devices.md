# listOrgJsiDevices

> listOrgJsiDevices

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/devices`

## Description

Get List of Org devices that connected to JSI

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
| model | string | No |  |  | Device model |
| serial | string | No |  |  | Device serial |
| mac | string | No |  |  | Device MAC Address |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "jse_device",
    "type": "object",
    "properties": {
      "ext_ip": {
        "type": "string",
        "description": "When available"
      },
      "last_seen": {
        "type": [
          "number",
          "null"
        ],
        "description": "Last seen timestamp",
        "readOnly": true,
        "examples": [
          1470417522
        ]
      },
      "mac": {
        "type": "string"
      },
      "model": {
        "type": "string"
      },
      "serial": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "ext_ip": "73.92.124.103",
        "last_seen": 1654636867,
        "mac": "c15353123096",
        "model": "EX2300-C-12P",
        "serial": "DGCOO0015"
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

`mistapi.api.v1.orgs.jsi.listOrgJsiDevices()`

## Usage Context

Lists JSI (Juniper Secure Infrastructure) devices in the organization.

## Gotchas

- JSI devices are managed through a separate workflow from standard Mist devices.

## Related Endpoints

- [GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md](GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md) — SSH command
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
