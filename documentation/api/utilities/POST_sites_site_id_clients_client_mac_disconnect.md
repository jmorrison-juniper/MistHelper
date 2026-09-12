# disconnectSiteWirelessClient

> disconnectSiteWirelessClient

## HTTP

`POST /api/v1/sites/{site_id}/clients/{client_mac}/disconnect`

## Description

This disconnect a client (and it’s likely to connect back)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| client_mac | string | Yes |  |

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

`mistapi.api.v1.utilities.wi-fi.disconnectSiteWirelessClient()`

## Usage Context

Forces disconnection of a specific wireless client from the network at a site. The client must reconnect and re-authenticate.

## Gotchas

- The client will likely auto-reconnect immediately if credentials are saved.
- Use `unauthorize` instead of `disconnect` to permanently block a guest client.

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_coa.md](POST_sites_site_id_clients_client_mac_coa.md) — CoA (softer re-auth)
- [POST_sites_site_id_clients_client_mac_unauthorize.md](POST_sites_site_id_clients_client_mac_unauthorize.md) — Unauthorize the client
- [POST_sites_site_id_clients_disconnect.md](POST_sites_site_id_clients_disconnect.md) — Disconnect multiple clients

## MistHelper Notes

Not currently used by MistHelper directly.
