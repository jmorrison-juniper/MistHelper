# exportOrgSsrIdTokens

> exportOrgSsrIdTokens

## HTTP

`POST /api/v1/orgs/{org_id}/ssr/export_idtokens`

## Description

Export IDTokens from Mist to import into Conductor to securely allow SSR devices during onboarding

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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

Example response

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "title": "response_ssr_export_id_tokens_results_item",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          },
          "token": {
            "type": "string"
          }
        }
      },
      "description": ""
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

`mistapi.api.v1.orgs.devices_-_ssr.exportOrgSsrIdTokens()`

## Usage Context

Exports ID tokens for SSR (Session Smart Router) registration.

## Gotchas

- Tokens are used for SSR onboarding into the Mist cloud.

## Related Endpoints

- [GET_orgs_org_id_ssr_register_cmd.md](GET_orgs_org_id_ssr_register_cmd.md) — Get SSR register command

## MistHelper Notes

Not currently used by MistHelper directly.
