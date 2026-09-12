# unauthorizeSiteWirelessClient

> unauthorizeSiteWirelessClient

## HTTP

`POST /api/v1/sites/{site_id}/clients/{client_mac}/unauthorize`

## Description

This unauthorize a client (if it’s a guest) and disconnect it. From the guest’s perspective, s/he will see the splash page again and go through the flow (e.g. Terms of Use) again.

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

`mistapi.api.v1.utilities.wi-fi.unauthorizeSiteWirelessClient()`

## Usage Context

Revokes authorization for a specific wireless client (typically a guest) at a site. The client is disconnected and its guest portal authorization is invalidated.

## Gotchas

- Primarily relevant for guest WLANs using portal-based authentication.
- For 802.1X clients, use CoA instead.

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_disconnect.md](POST_sites_site_id_clients_client_mac_disconnect.md) — Simple disconnect
- [POST_sites_site_id_clients_unauthorize.md](POST_sites_site_id_clients_unauthorize.md) — Unauthorize multiple clients
- [POST_sites_site_id_clients_client_mac_coa.md](POST_sites_site_id_clients_client_mac_coa.md) — CoA re-authentication

## MistHelper Notes

Not currently used by MistHelper directly.
