# updateSdkClient

> updateSdkClient

## HTTP

`PUT /api/v1/orgs/{org_id}/sdkclients/{sdkclient_id}`

## Description

Update SDK Client

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sdkclient_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    }
  },
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

`mistapi.api.v1.orgs.clients_-_sdk.updateSdkClient()`

## Usage Context

Updates an existing SDK client entry.

## Gotchas

- SDK clients represent mobile devices using the Mist SDK.

## Related Endpoints

- [GET_orgs_org_id_sdkclients_search.md](GET_orgs_org_id_sdkclients_search.md) — Search SDK clients
- [PUT_orgs_org_id_sdkinvites_sdkinvite_id.md](PUT_orgs_org_id_sdkinvites_sdkinvite_id.md) — Update invite

## MistHelper Notes

Not currently used by MistHelper directly.
