# searchSiteWebhooksDeliveries

> searchSiteWebhooksDeliveries

## HTTP

`GET /api/v1/sites/{site_id}/webhooks/{webhook_id}/events/search`

## Description

Search Site Webhooks deliveries


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
| site_id | string | Yes |  |
| webhook_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| error | string | No |  |  |  |
| status_code | integer | No |  |  |  |
| status | string | No |  |  | Webhook delivery status |
| topic | string | No |  |  | Webhook topic |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1688035193
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "webhook_delivery",
        "type": "object",
        "properties": {
          "error": {
            "type": "string",
            "description": "Error message, if there is one"
          },
          "id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "req_headers": {
            "type": "string",
            "description": "HTTP request headers",
            "examples": [
              "{\\\"Content-Type\\\":[\\\"application/json\\\"],\\\"User-Agent\\\":[\\\"Mist-webhook\\\"]}"
            ]
          },
          "req_payload": {
            "type": "string",
            "description": "HTTP request payload",
            "examples": [
              "{\\\"topic\\\":\\\"audits\\\",\\\"events\\\":[{\\\"admin_name\\\":\\\"John Doe john.doe@juniper.net\\\",\\\"after\\\":\\\"{\\\\\"radio_config\\\\\": {\\\\\"band_24\\\\\": {\\\\\"disabled\\\\\": false, \\\\\"allow_rrm_disable\\\\\": false, \\\\\"power_min\\\\\": null, \\\\\"power_max\\\\\": null, \\\\\"power\\\\\": 10, \\\\\"preamble\\\\\": \\\\\"short\\\\\", \\\\\"channels\\\\\": [1, 10], \\\\\"bandwidth\\\\\": 20}}}\\\",\\\"before\\\":\\\"{\\\\\"radio_config\\\\\": {\\\\\"band_24\\\\\": {\\\\\"disabled\\\\\": false, \\\\\"allow_rrm_disable\\\\\": false, \\\\\"power_min\\\\\": 8, \\\\\"power_max\\\\\": 18, \\\\\"power\\\\\": null, \\\\\"preamble\\\\\": \\\\\"long\\\\\", \\\\\"channels\\\\\": [1, 10], \\\\\"bandwidth\\\\\": 20}}}\\\",\\\"id\\\":\\\"737909a2-04ff-4aeb-b9da-cc924e74a4dd\\\",\\\"message\\\":\\\"Update Site Settings\\\",\\\"org_id\\\":\\\"fc7e2967-e7ef-41e6-b007-1217713de05a\\\",\\\"site_id\\\":\\\"256c3a35-9cb7-436e-bc6d-314972645d95\\\",\\\"site_name\\\":\\\"Test Site\\\",\\\"src_ip\\\":\\\"1.2.3.4\\\",\\\"timestamp\\\":1685956576.923601,\\\"user_agent\\\":\\\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36\\\"}]}"
            ]
          },
          "req_url": {
            "type": "string",
            "description": "HTTP request URL",
            "examples": [
              "https://example.com"
            ]
          },
          "resp_body": {
            "type": "string",
            "description": "HTTP response body",
            "examples": [
              "Ok"
            ]
          },
          "resp_headers": {
            "type": "string",
            "description": "HTTP response headers"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "status": {
            "type": "string",
            "description": "webhook delivery status. enum: `failure`, `success`"
          },
          "status_code": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              200
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "topic": {
            "type": "string",
            "description": "webhook topic. enum: `alarms`, `audits`, `device-updowns`, `occupancy-alerts`, `ping`"
          },
          "webhook_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "examples": [
              "7a11b901-f719-4c91-8aef-deb8699a6364"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1687948793
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  }
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

`mistapi.api.v1.sites.webhooks.searchSiteWebhooksDeliveries()`

## Usage Context

Searches events delivered to a specific webhook at a site. Supports filtering by status, time range.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_sites_site_id_webhooks_webhook_id_events_count.md](GET_sites_site_id_webhooks_webhook_id_events_count.md) — Events count
- [GET_sites_site_id_webhooks_webhook_id.md](GET_sites_site_id_webhooks_webhook_id.md) — Webhook details

## MistHelper Notes

Used by MistHelper via `listSiteWebhooks` in Menu 57 (Webhooks).
