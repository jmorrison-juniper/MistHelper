# pingSiteWebhook

> pingSiteWebhook

## HTTP

`POST /api/v1/sites/{site_id}/webhooks/{webhook_id}/ping`

## Description

Send a Ping event to the webhook

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

`mistapi.api.v1.sites.webhooks.pingSiteWebhook()`

## Usage Context

Sends a test ping to a webhook endpoint to verify connectivity and configuration.

## Gotchas

- The webhook URL must be reachable from Mist cloud. Firewalled endpoints will fail.

## Related Endpoints

- [GET_sites_site_id_webhooks_webhook_id.md](GET_sites_site_id_webhooks_webhook_id.md) — Webhook details
- [POST_sites_site_id_webhooks.md](POST_sites_site_id_webhooks.md) — Create webhook

## MistHelper Notes

Used by MistHelper via `listSiteWebhooks` in Menu 57 (Webhooks).
