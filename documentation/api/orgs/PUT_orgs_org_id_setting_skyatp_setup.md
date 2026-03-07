# udpateOrgAtpIntegration

> udpateOrgAtpIntegration

## HTTP

`PUT /api/v1/orgs/{org_id}/setting/skyatp/setup`

## Description

Update Sky ATP config

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
    "secintel": {
      "type": "object",
      "properties": {
        "third_party_threat_feeds": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        }
      },
      "description": "juniper secintel_feeds are enabled depending on your license tier: infected_host, geo_ip, attacker_ip, command_and_control.\nthird party:\n  * ip-based: block_list, threatfox_ip, feodo_tracker, dshield, tor\n  * url-based: threatfox_url, urlhaus, open_phish\n  * domain-based: threatfox_domains"
    },
    "secintel_allowlist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/secintel_allowlist/xxx..."
      ]
    },
    "secintel_blocklist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/secintel_blocklist/xxx..."
      ]
    }
  }
}
```

## Response

### 200

OK

```json
{
  "title": "account_skyatp_info",
  "type": "object",
  "properties": {
    "realm": {
      "type": "string",
      "examples": [
        "mist-team"
      ]
    },
    "username": {
      "type": "string",
      "examples": [
        "john@abc.com"
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

`mistapi.api.v1.orgs.integration_skyatp.udpateOrgAtpIntegration()`

## Usage Context

Updates the Juniper Sky ATP integration configuration.

## Gotchas

- Requires valid Sky ATP license.

## Related Endpoints

- [POST_orgs_org_id_setting_skyatp_setup.md](POST_orgs_org_id_setting_skyatp_setup.md) — Initial setup
- [GET_orgs_org_id_setting_skyatp.md](GET_orgs_org_id_setting_skyatp_setup.md) — Get Sky ATP config

## MistHelper Notes

Not currently used by MistHelper directly.
