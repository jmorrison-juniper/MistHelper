# listOrgAvailableSsrVersions

> listOrgAvailableSsrVersions

## HTTP

`GET /api/v1/orgs/{org_id}/ssr/versions`

## Description

Get available version for SSR

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
| channel | string | No |  |  | SSR version channel |
| mac | string | No |  |  | Optional. MAC address, or comma separated MAC address list. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "ssr_version",
    "required": [
      "package",
      "version"
    ],
    "type": "object",
    "properties": {
      "default": {
        "type": "boolean",
        "readOnly": true
      },
      "package": {
        "type": "string",
        "readOnly": true
      },
      "tags": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": ""
      },
      "version": {
        "type": "string",
        "readOnly": true
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "default": true,
        "package": "SSR",
        "version": "5.3.1-17"
      }
    ]
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

`mistapi.api.v1.utilities.upgrade.listOrgAvailableSsrVersions()`

## Usage Context

Returns the list of available SSR (Session Smart Router) firmware versions for the organization. Use this to determine which SSR software versions are available before initiating an upgrade.

## Gotchas

- SSR versions are distinct from AP/switch firmware versions — use the SSR-specific endpoints.
- Available versions may include release candidates alongside stable releases.

## Related Endpoints

- [POST_orgs_org_id_ssr_upgrade.md](POST_orgs_org_id_ssr_upgrade.md) — Start an SSR upgrade
- [GET_orgs_org_id_ssr_upgrade.md](GET_orgs_org_id_ssr_upgrade.md) — List SSR upgrade history

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) to present available SSR firmware versions.
