# getOrgAosRegisterCmd

> getOrgAosRegisterCmd

## HTTP

`GET /api/v1/orgs/{org_id}/aos/register_cmd`

## Description

Generates a registration challenge token and AOS-specific CLI commands for TPM-based brownfield registration of AOS devices. The returned command string can be copied and pasted directly into an AOS device to register it with Mist.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

AOS Brownfield Registration Commands

```json
{
  "type": "object",
  "properties": {
    "cli_commands": {
      "type": "string",
      "description": "AOS-specific CLI commands that can be copied and pasted directly into an AOS device to register it with Mist. Includes registration code and configuration commands."
    }
  },
  "description": "AOS Brownfield Registration Commands"
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

`mistapi.api.v1.orgs.devices_-_aos.getOrgAosRegisterCmd()`

## Usage Context

Retrieves the registration command for AOS (Aruba OS) devices to onboard into Mist.

## Gotchas

- The registration command is time-sensitive.

## Related Endpoints

- [GET_orgs_org_id_128routers_register_cmd.md](GET_orgs_org_id_128routers_register_cmd.md) — 128T register command
- [GET_orgs_org_id_ssr_register_cmd.md](GET_orgs_org_id_ssr_register_cmd.md) — SSR register command

## MistHelper Notes

Not currently used by MistHelper directly.
