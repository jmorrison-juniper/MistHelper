# deauthSiteWirelessClientsConnectedToARogue

> deauthSiteWirelessClientsConnectedToARogue

## HTTP

`POST /api/v1/sites/{site_id}/rogues/{rogue_bssid}/deauth_clients`

## Description

Send Deauth frame to clients connected to a Rogue AP

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| rogue_bssid | string | Yes |  |

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

`mistapi.api.v1.utilities.wi-fi.deauthSiteWirelessClientsConnectedToARogue()`

## Usage Context

Deauthenticates wireless clients that are connected to a rogue access point. Used to protect users from connecting to an unauthorized/malicious AP.

## Gotchas

- Only effective if the legitimate APs are within range to send deauth frames to the clients.
- Clients may reconnect to the rogue if the legitimate network signal is weaker.
- Requires rogue BSSID identification first.

## Related Endpoints

- [../sites/GET_sites_site_id_rogues.md](../sites/GET_sites_site_id_insights_rogues.md) — List detected rogues to find the BSSID

## MistHelper Notes

Not currently used by MistHelper via REST API.
