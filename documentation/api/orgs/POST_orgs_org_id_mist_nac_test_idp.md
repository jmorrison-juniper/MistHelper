# validateOrgIdpCredential

> validateOrgIdpCredential

## HTTP

`POST /api/v1/orgs/{org_id}/mist_nac/test_idp`

## Description

IDP Credential Validation. The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

``` json
{
    "subscribe": "orgs/{org_id}/mist_nac/test_idp"
}

 ```

### Response (no idp can be found)

``` json
{
    "event": "data",
    "channel": "/orgs/{org_id}/mist_nac/test_idp",
    "status": 
    "data": {
        "status": "failure",
        "error": "No matching IDP found"
    }
}

 ```

### Response OK

``` json
{
    "event": "data",
    "channel": "/orgs/{org_id}/mist_nac/test_idp",
    "status": 
    "data": {
        "status": "success",
        "idp_id": "915793c0-1355-4e98-b1c0-23df2227b357",
        "idp_type": "ldap",
        // more attributes will be added later
    }
}

 ```

### Response Invalid Credentials

``` json
{
    "event": "data",
    "channel": "/orgs/{org_id}/mist_nac/test_idp",
    "status": 
    "data": {
        "status": "failure",
        "error": "Invalid Credentials",
        "idp_id": "915793c0-1355-4e98-b1c0-23df2227b357",
        "idp_type": "ldap",
    }
}

 ```

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
    "password": {
      "type": "string"
    },
    "username": {
      "type": "string"
    }
  }
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session",
  "required": [
    "session"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
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

`mistapi.api.v1.orgs.nac_idp.validateOrgIdpCredential()`

## Usage Context

Tests IdP (Identity Provider) connectivity for Mist NAC.

## Gotchas

- Tests RADIUS/LDAP/OAuth connectivity without affecting production.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings
- [GET_orgs_org_id_nacrules.md](GET_orgs_org_id_nacrules.md) — NAC rules

## MistHelper Notes

Not currently used by MistHelper directly.
