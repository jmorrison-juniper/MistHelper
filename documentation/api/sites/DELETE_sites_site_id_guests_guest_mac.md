# deleteSiteGuestAuthorization

> deleteSiteGuestAuthorization

## HTTP

`DELETE /api/v1/sites/{site_id}/guests/{guest_mac}`

## Description

Delete Guest Authorization

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| guest_mac | string | Yes |  |

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

`mistapi.api.v1.sites.guests.deleteSiteGuestAuthorization()`

## Usage Context

Deletes a guest authorization by MAC address. Revokes the guest's access to the network.

## Gotchas

- Guest is immediately disconnected and must re-authenticate through the portal.

## Related Endpoints

- [GET_sites_site_id_guests.md](GET_sites_site_id_guests.md) — List current guests
- [GET_sites_site_id_guests_guest_mac.md](GET_sites_site_id_guests_guest_mac.md) — Get specific guest details

## MistHelper Notes

Not currently used by MistHelper directly. Menu **23** uses `searchOrgGuestAuthorization` for guest exports.
