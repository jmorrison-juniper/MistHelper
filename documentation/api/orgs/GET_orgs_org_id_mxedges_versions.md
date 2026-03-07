# getOrgMxEdgeUpgradeInfo

> getOrgMxEdgeUpgradeInfo

## HTTP

`GET /api/v1/orgs/{org_id}/mxedges/versions`

## Description

Get Mist Edge Upgrade Information

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
| channel | string | No |  |  | Upgrade channel to follow, stable (default) / beta / alpha |
| distro | string | No |  |  | Distro code name (e.g. `buster`, `bullseye`, ...) |

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
    "title": "mxedge_upgrade_info_items",
    "required": [
      "package",
      "version"
    ],
    "type": "object",
    "properties": {
      "default": {
        "type": "boolean"
      },
      "distro": {
        "type": "string"
      },
      "package": {
        "type": "string"
      },
      "version": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "default": true,
        "distro": "bullseye",
        "package": "mxagent",
        "version": "2.4.100"
      },
      {
        "distro": "bullseye",
        "package": "tunterm",
        "version": "1.0.0"
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

`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgradeInfo()`

## Usage Context

Retrieves available firmware versions for Mist Edge appliances.

## Gotchas

- Lists stable, beta, and development versions.

## Related Endpoints

- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List edges
- [POST_orgs_org_id_mxedges_mxedge_id_upgrade.md](POST_orgs_org_id_mxedges_mxedge_id_upgrade.md) — Upgrade edge

## MistHelper Notes

Not currently used by MistHelper directly.
