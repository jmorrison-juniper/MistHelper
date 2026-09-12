# getSiteDeviceStats

> getSiteDeviceStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/devices/{device_id}`

## Description

Get Site Device Stats Details

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
| fields | string | No |  |  | List of additional fields requests, comma separated, or `fields=*` for all of them |

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

`mistapi.api.v1.sites.stats_-_devices.getSiteDeviceStats()`

## Usage Context

Retrieves detailed statistics for a specific device by device ID, including CPU, memory, uptime, and interface stats.

## Gotchas

- Response structure varies by device type (AP vs switch vs gateway).

## Related Endpoints

- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — All device stats
- [GET_sites_site_id_stats_devices_device_id_clients.md](GET_sites_site_id_stats_devices_device_id_clients.md) — Clients on device

## MistHelper Notes

Not currently used by MistHelper directly (uses `listSiteDevicesStats` for bulk collection).
