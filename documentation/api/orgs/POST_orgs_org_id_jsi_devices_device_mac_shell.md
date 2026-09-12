# createOrgJsiDeviceShellSession

> createOrgJsiDeviceShellSession

## HTTP

`POST /api/v1/orgs/{org_id}/jsi/devices/{device_mac}/shell`

## Description

Create Shell Session

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "websocket_session_with_url",
  "required": [
    "session",
    "url"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ]
    },
    "url": {
      "type": "string",
      "examples": [
        "wss://api-ws.mist.com/ssh?jwt=xxxx"
      ]
    }
  }
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

`mistapi.api.v1.orgs.jsi.createOrgJsiDeviceShellSession()`

## Usage Context

Opens a shell session to a JSI (Juniper Support Insights) device.

## Gotchas

- Requires JSI-enabled devices.
- Shell access may be restricted by org permissions.

## Related Endpoints

- [GET_orgs_org_id_jsi_devices.md](GET_orgs_org_id_jsi_devices.md) — List JSI devices
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
