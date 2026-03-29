# getSiteDevice

> getSiteDevice

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}`

## Description

Get Device Configuration

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
  "type": "object"
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

`mistapi.api.v1.sites.devices.getSiteDevice()`

## Usage Context

Retrieves the full configuration and details of a specific device at a site. Returns model, firmware version, IP, name, config, and status.

## Gotchas

- Returns configuration state, not real-time stats. Use device stats endpoints for live data.

## Related Endpoints

- [PUT_sites_site_id_devices_device_id.md](PUT_sites_site_id_devices_device_id.md) — Update device
- [GET_sites_site_id_stats_devices_device_id.md](GET_sites_site_id_stats_devices_device_id.md) — Device stats
- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — List all devices

## MistHelper Notes

Used by Menus **8, 29, 62, 71, 72, 73, 74, 91, 104** via `getSiteDevice` for detailed device retrieval.
