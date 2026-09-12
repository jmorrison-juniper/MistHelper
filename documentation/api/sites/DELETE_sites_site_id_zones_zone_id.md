# deleteSiteZone

> deleteSiteZone

## HTTP

`DELETE /api/v1/sites/{site_id}/zones/{zone_id}`

## Description

Delete Site Zone

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| zone_id | string | Yes |  |

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

`mistapi.api.v1.sites.zones.deleteSiteZone()`

## Usage Context

Deletes a zone from a site. Removes a logical grouping used for location analytics and occupancy tracking.

## Gotchas

- Zone-based occupancy and dwell-time analytics are lost.
- Wayfinding destinations referencing this zone become invalid.

## Related Endpoints

- [GET_sites_site_id_zones.md](GET_sites_site_id_zones.md) — List zones
- [POST_sites_site_id_zones.md](POST_sites_site_id_zones.md) — Create zone

## MistHelper Notes

Used by Menu **50**, **51**, **52**, **112** (`MapsManagerLauncher`), **119**, and **120** for zone management and analytics.
