# deleteSiteBeacon

> deleteSiteBeacon

## HTTP

`DELETE /api/v1/sites/{site_id}/beacons/{beacon_id}`

## Description

Delete Site Beacon

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| beacon_id | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.sites.beacons.deleteSiteBeacon()`

## Usage Context

Deletes a BLE beacon record from a site. Removes the beacon's configuration and location assignment.

## Gotchas

- Any services depending on this beacon's signal (wayfinding, asset tracking) will be affected.

## Related Endpoints

- [GET_sites_site_id_beacons.md](GET_sites_site_id_beacons.md) — List all beacons
- [POST_sites_site_id_beacons.md](POST_sites_site_id_beacons.md) — Create new beacon

## MistHelper Notes

Not currently used by MistHelper directly. Menu **50** uses `listSiteBeacons` for export.
