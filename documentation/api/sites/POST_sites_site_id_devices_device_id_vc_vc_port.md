# setSiteVcPort

> setSiteVcPort

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/vc/vc_port`

## Description

Set VC port

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "members": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "config_vc_port_member",
        "required": [
          "member"
        ],
        "type": "object",
        "properties": {
          "member": {
            "type": "number"
          },
          "vc_ports": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          }
        }
      },
      "description": ""
    },
    "op": {
      "type": "string",
      "description": "enum: `delete`, `set`"
    }
  },
  "required": [
    "members",
    "op"
  ]
}
```

## Response

### 200

OK

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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.setSiteVcPort()`

## Usage Context

Configures Virtual Chassis port settings on a switch member.

## Gotchas

- Port configuration changes can disrupt VC ring/chain connectivity.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — VC operations
- [POST_sites_site_id_devices_device_id_set_vc_port_mode.md](POST_sites_site_id_devices_device_id_set_vc_port_mode.md) — Set VC port mode

## MistHelper Notes

Used by Menus **94, 95, 96** (VC Conversion) for VC port configuration.
