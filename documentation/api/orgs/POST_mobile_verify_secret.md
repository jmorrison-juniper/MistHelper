# activateSdkInvite

> activateSdkInvite

## HTTP

`POST /api/v1/mobile/verify/{secret}`

## Description

Verify secret

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| secret | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "device_id": {
      "type": "string",
      "contentEncoding": "uuid"
    }
  },
  "required": [
    "device_id"
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "secret": {
      "type": "string"
    }
  },
  "required": [
    "name",
    "org_id",
    "secret"
  ]
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

`mistapi.api.v1.orgs.sdk_invites.activateSdkInvite()`

## Usage Context

Verifies a mobile device secret for SDK integration.

## Gotchas

- This is a global endpoint, not org-scoped.

## Related Endpoints

- [GET_orgs_org_id_sdkinvites.md](GET_orgs_org_id_sdkinvites.md) — List SDK invites
- [POST_orgs_org_id_sdkinvites.md](POST_orgs_org_id_sdkinvites.md) — Create SDK invite

## MistHelper Notes

Not currently used by MistHelper directly.
