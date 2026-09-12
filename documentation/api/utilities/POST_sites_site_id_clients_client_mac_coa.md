# reauthSiteDot1xWirelessClient

> reauthSiteDot1xWirelessClient

## HTTP

`POST /api/v1/sites/{site_id}/clients/{client_mac}/coa`

## Description

Trigger a CoA (change of authorization) against a Wireless client

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

`mistapi.api.v1.utilities.wi-fi.reauthSiteDot1xWirelessClient()`

## Usage Context

Triggers a RADIUS Change of Authorization (CoA) for a wireless client at a specific site. More targeted than the org-level variant.

## Gotchas

- Requires RADIUS infrastructure to be properly configured.
- Client MAC must be URL-encoded and in colon-separated format.

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_disconnect.md](POST_sites_site_id_clients_client_mac_disconnect.md) — Force disconnect the client
- [POST_sites_site_id_clients_client_mac_unauthorize.md](POST_sites_site_id_clients_client_mac_unauthorize.md) — Unauthorize the client
- [POST_orgs_org_id_clients_client_mac_coa.md](POST_orgs_org_id_clients_client_mac_coa.md) — Org-level CoA

## MistHelper Notes

Not currently used by MistHelper directly.
