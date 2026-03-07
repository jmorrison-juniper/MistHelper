# stopSitePacketCapture

> stopSitePacketCapture

## HTTP

`DELETE /api/v1/sites/{site_id}/pcaps/capture`

## Description

Stop current capture

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.utilities.pcaps.stopSitePacketCapture()`

## Usage Context

Stops an active site-level packet capture. The captured data is saved and becomes available for download from the captures list.

## Gotchas

- Stopping a capture that is not running returns an error.

## Related Endpoints

- [GET_sites_site_id_pcaps_capture.md](GET_sites_site_id_pcaps_capture.md) — Verify a capture is running
- [GET_sites_site_id_pcaps.md](GET_sites_site_id_pcaps.md) — Find the saved capture

## MistHelper Notes

Used by Menu **9** (`PacketCaptureManager.start_site_packet_capture`) to stop active captures.
