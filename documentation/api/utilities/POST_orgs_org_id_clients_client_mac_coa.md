# reauthOrgDot1xWirelessClient

> reauthOrgDot1xWirelessClient

## HTTP

`POST /api/v1/orgs/{org_id}/clients/{client_mac}/coa`

## Description

Trigger a CoA (change of authorization) against a client

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
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

`mistapi.api.v1.utilities.wi-fi.reauthOrgDot1xWirelessClient()`

## Usage Context

Triggers a RADIUS Change of Authorization (CoA) for a wireless client at the org level. Used to force re-authentication or disconnect a misbehaving wireless client.

## Gotchas

- CoA requires RADIUS infrastructure to be properly configured.
- Client MAC must be URL-encoded and in colon-separated format.
- Effect depends on CoA action type (reauthenticate vs disconnect).

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_coa.md](POST_sites_site_id_clients_client_mac_coa.md) — Site-level CoA (preferred for targeted operations)
- [POST_orgs_org_id_wired_clients_client_mac_coa.md](POST_orgs_org_id_wired_clients_client_mac_coa.md) — Org-level wired client CoA

## MistHelper Notes

Not currently used by MistHelper directly.
