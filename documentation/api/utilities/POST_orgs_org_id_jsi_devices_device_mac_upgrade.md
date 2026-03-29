# upgradeOrgJsiDevice

> upgradeOrgJsiDevice

## HTTP

`POST /api/v1/orgs/{org_id}/jsi/devices/{device_mac}/upgrade`

## Description

Upgrade

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "version": {
      "type": "string"
    }
  }
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

`mistapi.api.v1.utilities.upgrade.upgradeOrgJsiDevice()`

## Usage Context

Upgrades a Juniper Sky Integration (JSI) device's firmware. JSI devices are Juniper devices managed through the Mist cloud via the Sky Enterprise integration, typically EX or SRX devices adopted through Juniper's classic management.

## Gotchas

- JSI devices have a different upgrade workflow than native Mist-managed devices.
- The device must be reachable and connected to the Mist cloud for the upgrade to proceed.

## Related Endpoints

- [POST_orgs_org_id_devices_upgrade.md](POST_orgs_org_id_devices_upgrade.md) — Standard device firmware upgrade
- [GET_orgs_org_id_devices_versions.md](GET_orgs_org_id_devices_versions.md) — Available firmware versions

## MistHelper Notes

Not currently used by MistHelper directly.
