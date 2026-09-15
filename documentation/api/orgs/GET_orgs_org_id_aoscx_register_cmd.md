# getOrgAoscxRegisterCmd

> getOrgAoscxRegisterCmd

## HTTP

`GET /api/v1/orgs/{org_id}/aoscx/register_cmd`

## Description

Generates a registration challenge token for TPM-based brownfield registration of AOSCX devices. The returned command string can be copied and pasted directly into an AOSCX device to register it with Mist.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

AOSCX Brownfield Registration Commands

```json
{
  "additionalProperties": false,
  "description": "AOSCX Brownfield Registration Commands",
  "properties": {
    "cli_commands": {
      "description": "AOSCX-specific CLI commands that can be copied and pasted directly into an AOSCX device to register it with Mist",
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

`mistapi.api.v1.orgs.devices_-_aoscx.getOrgAoscxRegisterCmd()`

## Usage Context

Retrieves the registration command for AOSCX devices to onboard into Mist.

## Gotchas

- The registration command is time-sensitive.

## Related Endpoints

- [GET_orgs_org_id_128routers_register_cmd.md](GET_orgs_org_id_128routers_register_cmd.md) - 128T register command
- [GET_orgs_org_id_ssr_register_cmd.md](GET_orgs_org_id_ssr_register_cmd.md) - SSR register command

## MistHelper Notes

Used by MistHelper through `getOrgAoscxRegisterCmd`.
