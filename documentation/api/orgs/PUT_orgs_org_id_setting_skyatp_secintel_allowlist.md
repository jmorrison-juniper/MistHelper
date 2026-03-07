# udpateOrgAtpAllowedList

> udpateOrgAtpAllowedList

## HTTP

`PUT /api/v1/orgs/{org_id}/setting/skyatp/secintel_allowlist`

## Description

Update Sky ATP Allowed List

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
    "domains": {
      "type": "array",
      "items": {
        "title": "skyatp_list_domain",
        "required": [
          "value"
        ],
        "type": "object",
        "properties": {
          "comment": {
            "type": "string",
            "examples": [
              "restricted"
            ]
          },
          "value": {
            "type": "string",
            "examples": [
              "unsafe.com"
            ]
          }
        }
      },
      "description": ""
    },
    "ip": {
      "type": "array",
      "items": {
        "title": "skyatp_list_ip",
        "required": [
          "value"
        ],
        "type": "object",
        "properties": {
          "comment": {
            "type": "string",
            "examples": [
              "nas"
            ]
          },
          "value": {
            "type": "string",
            "examples": [
              "10.1.3.5"
            ]
          }
        }
      },
      "description": ""
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "domains": {
      "type": "array",
      "items": {
        "title": "skyatp_list_domain",
        "required": [
          "value"
        ],
        "type": "object",
        "properties": {
          "comment": {
            "type": "string",
            "examples": [
              "restricted"
            ]
          },
          "value": {
            "type": "string",
            "examples": [
              "unsafe.com"
            ]
          }
        }
      },
      "description": ""
    },
    "ip": {
      "type": "array",
      "items": {
        "title": "skyatp_list_ip",
        "required": [
          "value"
        ],
        "type": "object",
        "properties": {
          "comment": {
            "type": "string",
            "examples": [
              "nas"
            ]
          },
          "value": {
            "type": "string",
            "examples": [
              "10.1.3.5"
            ]
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

`mistapi.api.v1.orgs.integration_skyatp.udpateOrgAtpAllowedList()`

## Usage Context

Updates the Sky ATP SecIntel allowlist (whitelisted domains/IPs).

## Gotchas

- Allowlisted entries bypass threat detection.

## Related Endpoints

- [PUT_orgs_org_id_setting_skyatp_secintel_blocklist.md](PUT_orgs_org_id_setting_skyatp_secintel_blocklist.md) — Blocklist
- [GET_orgs_org_id_setting_skyatp.md](GET_orgs_org_id_setting_skyatp.md) — Get Sky ATP config

## MistHelper Notes

Not currently used by MistHelper directly.
