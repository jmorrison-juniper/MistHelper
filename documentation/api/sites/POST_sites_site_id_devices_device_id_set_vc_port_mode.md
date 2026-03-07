# changeSiteSwitchVcPortMode

> changeSiteSwitchVcPortMode

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/set_vc_port_mode`

## Description

Change VCP port mode


Some switch model allows changing VCP port behaviors, e.g. - use them as regular network ports - change vcp protocol Note, this command will reboot the switch

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
    "mode": {
      "type": "string",
      "description": "enum: `network`, `vcp-higig`, `vcp-hgoe`"
    }
  },
  "description": "Request Body"
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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.changeSiteSwitchVcPortMode()`

## Usage Context

Sets the Virtual Chassis port mode on a switch. Configures ports for VC interconnection.

## Gotchas

- Changing VC port mode can disrupt Virtual Chassis connectivity. Requires careful planning.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — VC operations
- [POST_sites_site_id_devices_device_id_vc_vc_port.md](POST_sites_site_id_devices_device_id_vc_vc_port.md) — VC port config

## MistHelper Notes

Used by Menu **94** (VC Conversion) for setting VC port modes during virtual chassis operations.
