# clearAllLearnedMacsFromPortOnSwitch

> clearAllLearnedMacsFromPortOnSwitch

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_macs`

## Description

Clear all learned MAC addresses, including persistent MAC addresses, on a port.

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
    "ports": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of ports on which to clear mac addresses. must include logical unit number"
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

`mistapi.api.v1.utilities.lan.clearAllLearnedMacsFromPortOnSwitch()`

## Usage Context

Clears specific learned MAC addresses from a switch. More targeted than `clear_mac_table` which clears all entries.

## Gotchas

- Requires specifying the MAC address(es) to clear.
- A cleared MAC will be re-learned when the device sends traffic again.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_mac_table.md](POST_sites_site_id_devices_device_id_clear_mac_table.md) — Clear entire MAC table
- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — View MAC table

## MistHelper Notes

Not currently used by MistHelper via REST API.
