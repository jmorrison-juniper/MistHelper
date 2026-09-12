# clearSiteDevicePolicyHitCount

> clearSiteDevicePolicyHitCount

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_policy_hit_count`

## Description

Clear application policy hit counts for all the policies

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

`mistapi.api.v1.utilities.common.clearSiteDevicePolicyHitCount()`

## Usage Context

Resets the policy hit counters on a gateway device. Useful for verifying which firewall/security policies are matched after a configuration change.

## Gotchas

- Only works on gateways (SRX/SSR) with security policies configured.
- Counters reset to zero immediately and cannot be recovered.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_session.md](POST_sites_site_id_devices_device_id_show_session.md) — View active sessions affected by policies

## MistHelper Notes

Not currently used by MistHelper via REST API.
