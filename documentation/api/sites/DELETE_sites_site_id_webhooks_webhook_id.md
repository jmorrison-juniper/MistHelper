# deleteSiteWebhook

> deleteSiteWebhook

## HTTP

`DELETE /api/v1/sites/{site_id}/webhooks/{webhook_id}`

## Description

Delete Site Webhook

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| webhook_id | string | Yes |  |

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

`mistapi.api.v1.sites.webhooks.deleteSiteWebhook()`

## Usage Context

Deletes a webhook from a site. Removes the event notification endpoint.

## Gotchas

- All events configured for this webhook will stop being delivered.

## Related Endpoints

- [GET_sites_site_id_webhooks.md](GET_sites_site_id_webhooks.md) — List webhooks
- [POST_sites_site_id_webhooks.md](POST_sites_site_id_webhooks.md) — Create webhook

## MistHelper Notes

Not currently used by MistHelper directly. Menu **55** uses `listOrgWebhooks` at org level.
