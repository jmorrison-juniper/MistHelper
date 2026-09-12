# updateSiteDevice

> updateSiteDevice

## HTTP

`PUT /api/v1/sites/{site_id}/devices/{device_id}`

## Description

Update Device Configuration

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
  "description": "Request Body"
}
```

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

`mistapi.api.v1.sites.devices.updateSiteDevice()`

## Usage Context

Updates a device's configuration (AP, switch, or gateway). This is the primary endpoint for device management.

## Gotchas

- Some changes trigger a configuration push and device reconnection. Use `type=all` when querying to see non-AP devices.

## Related Endpoints

- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device details
- [GET_sites_site_id_stats_devices_device_id.md](GET_sites_site_id_stats_devices_device_id.md) — Device stats

## MistHelper Notes

Used by MistHelper via `updateSiteDevice` in Menus 91-93 (AP reboots), Menu 112 (device updates).
