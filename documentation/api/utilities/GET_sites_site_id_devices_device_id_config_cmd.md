# getSiteDeviceConfigCmd

> getSiteDeviceConfigCmd

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/config_cmd`

## Description

Get Config CLI Commands
For a brown-field switch deployment where we adopted the switch through Adoption Command, we do not wipe out / overwrite the existing config automatically. Instead, we generate CLI commands that we would have generated. The user can inspect, modify, and incorporate this into their existing config manually.

Once they feel comfortable about the config we generate, they can enable allow_mist_config where we will take full control of their config like a claimed switch

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| sort | boolean | No | False |  | Make output cmds sorted (for better readability) or not. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "cli": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "cli"
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

`mistapi.api.v1.utilities.common.getSiteDeviceConfigCmd()`

## Usage Context

Retrieves the rendered configuration commands for a specific device. Returns the actual CLI commands that will be applied to the device based on its template and site settings.

## Gotchas

- This returns the *rendered* configuration, not the template source — it includes all variable substitutions.
- Output format varies by device type (Junos CLI for switches/gateways, AP config for APs).

## Related Endpoints

- [../sites/GET_sites_site_id_devices_device_id.md](../sites/GET_sites_site_id_devices_device_id.md) — Full device details
- [POST_sites_site_id_devices_device_id_reprovision.md](POST_sites_site_id_devices_device_id_reprovision.md) — Push config to device

## MistHelper Notes

Not currently used by MistHelper directly.
