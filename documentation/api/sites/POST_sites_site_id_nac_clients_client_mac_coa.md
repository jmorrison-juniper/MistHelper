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

`mistapi.api.v1.sites.clients_-_nac.sendSiteNacClientCoA()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
