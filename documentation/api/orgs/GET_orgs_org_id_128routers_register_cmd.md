# getOrg128TRegistrationCommands

> **DEPRECATED** -- This endpoint is deprecated and may be removed in a future release.

> getOrg128TRegistrationCommands

## HTTP

`GET /api/v1/orgs/{org_id}/128routers/register_cmd`

## Description

128T devices can be managed/adopted by Mist.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| ttl | integer | No |  |  | Token validity duration in seconds. Defaults to 1 year (31536000 seconds) |
| asset_ids | array | No |  |  | When specified restricts registration to listed assets only. Prefer HTTP body over headers for this parameter, especially with long lists to avoid header size limits. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "conductor_cmd": {
      "type": "string"
    },
    "registration_code": {
      "type": "string"
    },
    "router_shell_cmd": {
      "type": "string"
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

`mistapi.api.v1.orgs.devices_-_ssr.getOrg128TRegistrationCommands()`

## Usage Context

Retrieves the registration command for 128T/SSR routers to onboard them into the Mist organization.

## Gotchas

- The command is time-sensitive and may expire.

## Related Endpoints

- [GET_orgs_org_id_ssr_register_cmd.md](GET_orgs_org_id_ssr_register_cmd.md) — SSR register command
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Org inventory

## MistHelper Notes

Not currently used by MistHelper directly.
