# reauthSiteDot1xWiredClient

> reauthSiteDot1xWiredClient

## HTTP

`POST /api/v1/sites/{site_id}/wired_clients/{client_mac}/coa`

## Description

Trigger a CoA (change of authorization) against a Wired client

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

Reauth Wired Client

```json
{
  "type": "object",
  "properties": {
    "device_mac": {
      "type": "string",
      "examples": [
        "5c5b35000002"
      ]
    },
    "port_id": {
      "type": "string",
      "examples": [
        "ge-0/0/0"
      ]
    },
    "session": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "0a2a11b8-4b30-40d8-a6d1-e91ea540d86f"
      ]
    }
  }
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

`mistapi.api.v1.utilities.lan.reauthSiteDot1xWiredClient()`

## Usage Context

Triggers a RADIUS Change of Authorization (CoA) for a wired 802.1X client at a specific site. Forces re-authentication at the switch port level.

## Gotchas

- Only affects 802.1X-authenticated wired clients.
- The switch must support RADIUS CoA (RFC 5176) and be managed by Mist.

## Related Endpoints

- [POST_orgs_org_id_wired_clients_client_mac_coa.md](POST_orgs_org_id_wired_clients_client_mac_coa.md) — Org-level wired CoA
- [POST_sites_site_id_clients_client_mac_coa.md](POST_sites_site_id_clients_client_mac_coa.md) — Wireless client CoA

## MistHelper Notes

Not currently used by MistHelper directly.
