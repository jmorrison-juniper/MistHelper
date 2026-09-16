# sendSiteNacClientCoA

> sendSiteNacClientCoA

## HTTP

`POST /api/v1/sites/{site_id}/nac_clients/{client_mac}/coa`

## Description

Sends CoA (Change of Authorization) command to a NAC client.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Change of Authorization request for a NAC client",
  "properties": {
    "coa_type": {
      "default": "reauth",
      "description": "CoA type to send. enum: `reauth`, `disconnect`",
      "enum": [
        "reauth",
        "disconnect"
      ],
      "type": "string"
    }
  },
  "type": "object"
}
```

## Response

### 200

Example response

```json
{
  "additionalProperties": false,
  "description": "Response returned after sending a NAC client CoA command",
  "properties": {
    "device_mac": {
      "description": "Target AP or switch MAC address for the CoA command",
      "type": "string"
    },
    "device_type": {
      "description": "enum: `ap`, `gateway`, `switch`",
      "enum": [
        "ap",
        "gateway",
        "switch"
      ],
      "type": "string"
    }
  },
  "type": "object"
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

`mistapi.api.v1.sites.nac_clients.sendSiteNacClientCoA()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/nac_clients/{client_mac}/coa`.
Common use cases:

- Use it when you need to sends CoA (Change of Authorization) command to a NAC client.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `sendSiteNacClientCoA(mist_session: mistapi.__api_session.APISession, site_id: str, client_mac: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `client_mac`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.
- A CoA request changes a client session. Confirm the target client before you send it.

## Related Endpoints

- [GET_sites_site_id_nac_clients_count.md](GET_sites_site_id_nac_clients_count.md) -- countSiteNacClients uses `GET /api/v1/sites/{site_id}/nac_clients/count`.
- [GET_sites_site_id_nac_clients_events_count.md](GET_sites_site_id_nac_clients_events_count.md) -- countSiteNacClientEvents uses `GET /api/v1/sites/{site_id}/nac_clients/events/count`.
- [GET_sites_site_id_nac_clients_events_search.md](GET_sites_site_id_nac_clients_events_search.md) -- searchSiteNacClientEvents uses `GET /api/v1/sites/{site_id}/nac_clients/events/search`.

## MistHelper Notes

MistHelper does not currently call `sendSiteNacClientCoA`.
Verification source: `git grep -n "sendSiteNacClientCoA" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
