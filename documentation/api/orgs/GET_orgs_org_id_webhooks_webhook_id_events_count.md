# countOrgWebhooksDeliveries

> countOrgWebhooksDeliveries

## HTTP

`GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count`

## Description

Count Org Webhooks deliveries


Topics Supported:
- alarms
- audits
- device-updowns
- occupancy-alerts
- ping

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| webhook_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| error | string | No |  |  |  |
| status_code | integer | No |  |  |  |
| status | string | No |  |  | Webhook delivery status |
| topic | string | No |  |  | Webhook topic |
| distinct | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": [
          "count"
        ],
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        },
        "additionalProperties": {
          "type": "string"
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.webhooks.countOrgWebhooksDeliveries()`

## Usage Context

Returns the count of events for a specific webhook.

## Gotchas

- Useful for monitoring webhook delivery health.

## Related Endpoints

- [GET_orgs_org_id_webhooks_webhook_id_events_search.md](GET_orgs_org_id_webhooks_webhook_id_events_search.md) — Search webhook events
- [GET_orgs_org_id_webhooks_webhook_id.md](GET_orgs_org_id_webhooks_webhook_id.md) — Get webhook

## MistHelper Notes

Used by MistHelper via `listOrgWebhooks` in Menu 47.
