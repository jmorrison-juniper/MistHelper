# getOrgJuniperDevicesCommand

> getOrgJuniperDevicesCommand

## HTTP

`GET /api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd`

## Description

Get Org Juniper Devices command

Juniper devices can be managed/adopted by Mist. Currently outbound-ssh + netconf is used.
A few lines of CLI commands are generated per-Org, allowing the Juniper devices to phone home to Mist.

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
| site_id | string | No |  |  | Site_id would be used for proxy config check of the site and automatic site assignment |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "cmd": {
      "type": "string"
    }
  },
  "required": [
    "cmd"
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

`mistapi.api.v1.orgs.devices.getOrgJuniperDevicesCommand()`

## Usage Context

Retrieves the outbound SSH command for OC (OpenConfig) devices.

## Gotchas

- Used for establishing reverse SSH tunnels from OC managed devices.

## Related Endpoints

- [GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md](GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md) — JSI SSH command
- [GET_orgs_org_id_otherdevices.md](GET_orgs_org_id_otherdevices.md) — Other devices

## MistHelper Notes

Not currently used by MistHelper directly.
