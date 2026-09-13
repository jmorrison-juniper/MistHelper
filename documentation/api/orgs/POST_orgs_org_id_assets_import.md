# importOrgAssets

> importOrgAssets

## HTTP

`POST /api/v1/orgs/{org_id}/assets/import`

## Description

Import Org Assets. 

It can be done via a CSV file or a JSON payload.

#### CSV File Format
```csv
name,mac
"asset_name",5c5b53010101
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
    "file": {
      "type": "string",
      "description": "CSV file",
      "contentEncoding": "base64"
    }
  }
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

`mistapi.api.v1.orgs.assets.importOrgAssets()`

## Usage Context

Imports assets in bulk from a CSV or JSON payload.

## Gotchas

- Import format must match the expected schema exactly.

## Related Endpoints

- [POST_orgs_org_id_assets.md](POST_orgs_org_id_assets.md) — Create single asset
- [GET_orgs_org_id_assets.md](GET_orgs_org_id_assets.md) — List assets

## MistHelper Notes

Not currently used by MistHelper directly.
