# getOrgEdgeconnectRegisterCmd

> getOrgEdgeconnectRegisterCmd

## HTTP

`GET /api/v1/orgs/{org_id}/edgeconnect/register_cmd`

## Description

Returns a registration code for adopting an EdgeConnect device into Mist.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

EdgeConnect Registration Command

```json
{
  "additionalProperties": false,
  "description": "EdgeConnect device registration command response",
  "properties": {
    "registration_code": {
      "description": "Registration code used to adopt an EdgeConnect device into Mist",
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

`mistapi.api.v1.orgs.devices_-_edgeconnect.getOrgEdgeconnectRegisterCmd()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
