# unauthorizeSiteMultipleClients

> unauthorizeSiteMultipleClients

## HTTP

`POST /api/v1/sites/{site_id}/clients/unauthorize`

## Description

This unauthorize clients (if they are guest) and disconnect them. From the guest’s perspective, they will see the splash page again and go through the flow (e.g. Terms of Use) again.

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
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.utilities.wi-fi.unauthorizeSiteMultipleClients()`

## Usage Context

Revokes authorization for multiple wireless clients (typically guests) at a site simultaneously. Accepts a list of client MACs.

## Gotchas

- Primarily relevant for guest WLANs — 802.1X clients should use CoA.
- Ensure the MAC list is correct; this action is immediate and cannot be undone.

## Related Endpoints

- [POST_sites_site_id_clients_client_mac_unauthorize.md](POST_sites_site_id_clients_client_mac_unauthorize.md) — Unauthorize a single client
- [POST_sites_site_id_clients_disconnect.md](POST_sites_site_id_clients_disconnect.md) — Disconnect multiple clients

## MistHelper Notes

Not currently used by MistHelper directly.
