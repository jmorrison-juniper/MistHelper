# listWebhookTopics

> listWebhookTopics

## HTTP

`GET /api/v1/const/webhook_topics`

## Description

Get List of the available Webhook Topics.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Webhook Topics

```json
{
  "type": "array",
  "items": {
    "title": "const_webhook_topic",
    "type": "object",
    "properties": {
      "allows_single_event_per_message": {
        "type": "boolean",
        "description": "supports single event per message results"
      },
      "for_org": {
        "type": "boolean",
        "description": "Can be used in org webhooks, optional"
      },
      "has_delivery_results": {
        "type": "boolean",
        "description": "Supports webhook delivery results /api/v1/:scope/:scope_id/webhooks/:webhook_id/events/search"
      },
      "internal": {
        "type": "boolean",
        "description": "Internal topic (not selectable in site/org webhooks)"
      },
      "key": {
        "type": "string",
        "description": "Webhook topic name",
        "examples": [
          "alarms"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "for_org": true,
        "has_delivery_results": true,
        "key": "alarms"
      },
      {
        "key": "asset-raw-rssi"
      },
      {
        "for_org": true,
        "has_delivery_results": true,
        "key": "audits"
      },
      {
        "for_org": true,
        "key": "client-info"
      },
      {
        "for_org": true,
        "key": "client-join"
      },
      {
        "key": "client-latency"
      },
      {
        "for_org": true,
        "key": "client-sessions"
      },
      {
        "allows_single_event_per_message": true,
        "for_org": true,
        "key": "device-events"
      },
      {
        "for_org": true,
        "has_delivery_results": true,
        "key": "device-updowns"
      },
      {
        "for_org": true,
        "key": "minis-reachability"
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

`mistapi.api.v1.constants.definitions.listWebhookTopics()`

## Usage Context

Returns the list of available webhook topic strings (e.g., `device-events`, `alarms`, `audits`, `client-sessions`) that can be subscribed to when creating webhook configurations. Use this to discover all available webhook event types when setting up real-time event notifications.

## Gotchas

- Webhook topics can be org-level or site-level — not all topics are available at both scopes.
- Subscribing to high-volume topics (e.g., `client-sessions`) can generate significant traffic to your webhook receiver.

## Related Endpoints

- [../orgs/GET_orgs_org_id_webhooks.md](../orgs/GET_orgs_org_id_webhooks.md) — List configured org webhooks
- [../orgs/POST_orgs_org_id_webhooks.md](../orgs/POST_orgs_org_id_webhooks.md) — Create a webhook subscription
- [../sites/GET_sites_site_id_webhooks.md](../sites/GET_sites_site_id_webhooks.md) — List site-level webhooks

## MistHelper Notes

Not currently used by MistHelper directly. Menu **52** (`OrgConfigExporter.webhooks`) exports webhook configurations that reference these topic values.
