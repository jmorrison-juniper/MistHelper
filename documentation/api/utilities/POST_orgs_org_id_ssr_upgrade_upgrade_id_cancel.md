# cancelOrgSsrUpgrade

> cancelOrgSsrUpgrade

## HTTP

`POST /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`

## Description

Best effort to cancel an upgrade. Devices which are already upgraded wont be touched↵


## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| upgrade_id | string | Yes |  |

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

`mistapi.api.v1.utilities.upgrade.cancelOrgSsrUpgrade()`

## Usage Context

Cancels an in-progress org-level SSR firmware upgrade. Devices that have already completed the upgrade remain on the new version.

## Gotchas

- Cancellation is best-effort; devices mid-flash may complete the upgrade.

## Related Endpoints

- [GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) — Check upgrade status before cancelling
- [POST_orgs_org_id_ssr_upgrade.md](POST_orgs_org_id_ssr_upgrade.md) — Start a new upgrade

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) to cancel SSR upgrades.
