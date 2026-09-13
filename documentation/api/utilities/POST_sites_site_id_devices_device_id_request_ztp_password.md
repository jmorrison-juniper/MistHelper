# getSiteDeviceZtpPassword

> getSiteDeviceZtpPassword

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/request_ztp_password`

## Description

In the case where something happens during/after ZTP, the root-password is modified (required for ZTP to set up outbound-ssh) but the user-defined password config has not be configured. This API can be used to retrieve the temporary password.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "root_password": {
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "root_password"
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

`mistapi.api.v1.utilities.common.getSiteDeviceZtpPassword()`

## Usage Context

Retrieves the ZTP (Zero Touch Provisioning) password for a specific device. Used during initial device setup when root password is needed for out-of-band access.

## Gotchas

- Contains sensitive credential information — handle securely.
- Password is device-specific and generated during ZTP provisioning.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_readopt.md](POST_sites_site_id_devices_device_id_readopt.md) — Re-adopt if ZTP had issues

## MistHelper Notes

Not currently used by MistHelper via REST API.
