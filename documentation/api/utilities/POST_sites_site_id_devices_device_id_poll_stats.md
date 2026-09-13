# pollSiteSwitchStats

> pollSiteSwitchStats

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/poll_stats`

## Description

This API can be used to poll statistics from the Switch proactively once. After it is called, the statistics will be pushed back to the cloud within the statistics interval.

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

`mistapi.api.v1.utilities.lan.pollSiteSwitchStats()`

## Usage Context

Forces an immediate stats poll from a specific device. Instead of waiting for the next scheduled stats collection interval, this triggers on-demand statistics retrieval.

## Gotchas

- Frequent polling may increase cloud-to-device communication overhead.
- Stats retrieved are point-in-time snapshots, not continuous monitoring.

## Related Endpoints

- [../sites/GET_sites_site_id_stats_devices.md](../sites/GET_sites_site_id_stats_devices.md) — View collected device stats

## MistHelper Notes

Not currently used by MistHelper via REST API.
