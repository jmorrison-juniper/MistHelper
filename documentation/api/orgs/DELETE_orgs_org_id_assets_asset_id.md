# deleteOrgAsset

> deleteOrgAsset

## HTTP

`DELETE /api/v1/orgs/{org_id}/assets/{asset_id}`

## Description

Delete Org Asset

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| asset_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

### 201

Created

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

`mistapi.api.v1.orgs.assets.deleteOrgAsset()`

## Usage Context

Deletes a BLE asset definition from the organization.

## Gotchas

- Historical tracking data for the asset is retained.

## Related Endpoints

- [GET_orgs_org_id_assets.md](GET_orgs_org_id_assets.md) — List assets
- [POST_orgs_org_id_assets.md](POST_orgs_org_id_assets.md) — Create asset

## MistHelper Notes

Not currently used by MistHelper directly.
