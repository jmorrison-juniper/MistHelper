# stopOrgPacketCapture

> stopOrgPacketCapture

## HTTP

`DELETE /api/v1/orgs/{org_id}/pcaps/capture`

## Description

Stop current Org capture

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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

`mistapi.api.v1.utilities.pcaps.stopOrgPacketCapture()`

## Usage Context

Stops an active org-level packet capture. The captured data up to the stop point is saved and becomes available in the captures list.

## Gotchas

- Stopping a capture that is not running returns an error.
- The capture file may take a moment to finalize after stopping.

## Related Endpoints

- [GET_orgs_org_id_pcaps_capture.md](GET_orgs_org_id_pcaps_capture.md) — Verify a capture is running before stopping
- [GET_orgs_org_id_pcaps.md](GET_orgs_org_id_pcaps.md) — Find the stopped capture in the list

## MistHelper Notes

Used by Menu **10** (`PacketCaptureManager.start_org_packet_capture`) to stop active captures.
