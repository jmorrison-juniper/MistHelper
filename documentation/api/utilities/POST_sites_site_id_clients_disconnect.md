# disconnectSiteMultipleClients

> disconnectSiteMultipleClients

## HTTP

`POST /api/v1/sites/{site_id}/clients/disconnect`

## Description

To unauthorize multiple clients

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "type": "string"
  },
  "description": "Request Body",
  "examples": [
    [
      "5c5b350e0001",
      "5c5b350e0003"
    ]
  ]
}
```

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

`mistapi.api.v1.utilities.wi-fi.disconnectSiteMultipleClients()`

## Usage Context

Disconnects multiple wireless clients at a site simultaneously. Accepts a list of client MACs to disconnect in bulk.

## Gotchas

- Operates on a list of MACs — ensure the list is correct before calling.
- Clients with saved credentials will likely auto-reconnect.

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_disconnect.md](POST_sites_site_id_clients_client_mac_disconnect.md) — Disconnect a single client
- [POST_sites_site_id_clients_unauthorize.md](POST_sites_site_id_clients_unauthorize.md) — Unauthorize multiple clients

## MistHelper Notes

Not currently used by MistHelper directly.
