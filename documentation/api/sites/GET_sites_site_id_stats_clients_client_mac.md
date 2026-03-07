# getSiteWirelessClientStats

> getSiteWirelessClientStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/clients/{client_mac}`

## Description

Get Site Client Stats Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| client_mac | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| wired | boolean | No | False |  |  |

## Request Body

None.

## Response

### 200

Example response

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

`mistapi.api.v1.sites.stats_-_clients_wireless.getSiteWirelessClientStats()`

## Usage Context

Retrieves detailed statistics for a specific wireless client identified by MAC address.

## Gotchas

- Only returns data if the client is currently connected or was recently seen.

## Related Endpoints

- [GET_sites_site_id_stats_clients.md](GET_sites_site_id_stats_clients.md) — All client stats
- [GET_sites_site_id_insights_client_client_mac.md](GET_sites_site_id_insights_client_client_mac.md) — Client insights

## MistHelper Notes

Not currently used by MistHelper directly.
