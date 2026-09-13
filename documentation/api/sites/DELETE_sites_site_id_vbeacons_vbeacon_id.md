# deleteSiteVBeacon

> deleteSiteVBeacon

## HTTP

`DELETE /api/v1/sites/{site_id}/vbeacons/{vbeacon_id}`

## Description

Delete Site Virtual Beacon

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| vbeacon_id | string | Yes |  |

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

`mistapi.api.v1.sites.vbeacons.deleteSiteVBeacon()`

## Usage Context

Deletes a virtual beacon from a site. Removes a software-defined BLE beacon used for proximity/wayfinding.

## Gotchas

- Wayfinding and proximity triggers referencing this vbeacon will stop working.

## Related Endpoints

- [GET_sites_site_id_vbeacons.md](GET_sites_site_id_vbeacons.md) — List virtual beacons
- [POST_sites_site_id_vbeacons.md](POST_sites_site_id_vbeacons.md) — Create virtual beacon

## MistHelper Notes

Used by Menu **50** and **112** (`MapsManagerLauncher`) for vbeacon management.
