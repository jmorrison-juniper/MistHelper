# createOrgWebhook

> createOrgWebhook

## HTTP

`POST /api/v1/orgs/{org_id}/webhooks`

## Description

**N.B**. For org webhooks, only alarms/audits/client-info/client-join/client-sessions/device_events/device-updowns/mxedge_events Infrastructure topics are supported.


Webhook defines a webhook, modeled after [github\u2019s model](https://developer.github.com/webhooks/).


There is two types of webhooks:
* webhooks ([examples](https://www.postman.com/juniper-mist/workspace/mist-systems-s-public-workspace/folder/224925-be01e694-7253-4195-8563-78e2a745e114))        
* raw data webhooks ([examples](https://www.postman.com/juniper-mist/workspace/mist-systems-s-public-workspace/folder/224925-e2d5d5f8-4bdb-4efc-93e4-90f4b33d0b2b))


##### Webhooks
Webhooks can be configured at the org level (subset of topics only) and at the site level. It is possible to have multiple topics in the same webhook configuration and/or to have multiple webhooks configured at the same time.


## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "assetfilter_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Only if `type`==`asset-raw-rssi`. List of ids to associated asset filters. These filters will be applied to messages routed to a filtered-asset-rssi webhook"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "enabled": {
      "type": "boolean",
      "description": "Whether webhook is enabled",
      "default": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "headers": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": {
        "type": "string"
      },
      "description": "If `type`=`http-post`, additional custom HTTP headers to add. The headers name and value must be string, total bytes of headers name and value must be less than 1000",
      "examples": [
        {
          "x-custom-1": "your_custom_header_value1",
          "x-custom-2": "your_custom_header_value2"
        }
      ]
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": [
        "string",
        "null"
      ],
      "description": "Name of the webhook"
    },
    "oauth2_client_id": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`client_credentials`"
    },
    "oauth2_client_secret": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`client_credentials`"
    },
    "oauth2_grant_type": {
      "type": "string",
      "description": "required when `type`==`oauth2`. enum: `client_credentials`, `password`"
    },
    "oauth2_password": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`password`"
    },
    "oauth2_scopes": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required when `type`==`oauth2`, if provided, will be used in the token request"
    },
    "oauth2_token_url": {
      "type": "string",
      "description": "Required when `type`==`oauth2`"
    },
    "oauth2_username": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`password`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "secret": {
      "type": [
        "string",
        "null"
      ],
      "description": "Only if `type`=`http-post` \n\nwhen `secret` is provided, two  HTTP headers will be added: \n  * X-Mist-Signature-v2: HMAC_SHA256(secret, body)\n  * X-Mist-Signature: HMAC_SHA1(secret, body)"
    },
    "single_event_per_message": {
      "type": "boolean",
      "description": "Some solutions may not be able to parse multiple events from a single message (e.g. IBM Qradar, DSM). When set to `true`, only a single event will be sent per message. this feature is only available on certain topics (see [List Webhook Topics]($e/Constants%20Definitions/listWebhookTopics))",
      "default": false
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "splunk_token": {
      "type": [
        "string",
        "null"
      ],
      "description": "Required if `type`=`splunk`. If splunk_token is not defined for a type Splunk webhook, it will not send, regardless if the webhook receiver is configured to accept it."
    },
    "topics": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of supported webhook topics available with the API Call [List Webhook Topics]($e/Constants%20Definitions/listWebhookTopics)"
    },
    "type": {
      "type": "string",
      "description": "enum: `aws-sns`, `google-pubsub`, `http-post`, `oauth2`, `splunk`"
    },
    "url": {
      "type": "string"
    },
    "verify_cert": {
      "type": "boolean",
      "description": "When url uses HTTPS, whether to verify the certificate",
      "default": true
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "assetfilter_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Only if `type`==`asset-raw-rssi`. List of ids to associated asset filters. These filters will be applied to messages routed to a filtered-asset-rssi webhook"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "enabled": {
      "type": "boolean",
      "description": "Whether webhook is enabled",
      "default": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "headers": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": {
        "type": "string"
      },
      "description": "If `type`=`http-post`, additional custom HTTP headers to add. The headers name and value must be string, total bytes of headers name and value must be less than 1000",
      "examples": [
        {
          "x-custom-1": "your_custom_header_value1",
          "x-custom-2": "your_custom_header_value2"
        }
      ]
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": [
        "string",
        "null"
      ],
      "description": "Name of the webhook"
    },
    "oauth2_client_id": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`client_credentials`"
    },
    "oauth2_client_secret": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`client_credentials`"
    },
    "oauth2_grant_type": {
      "type": "string",
      "description": "required when `type`==`oauth2`. enum: `client_credentials`, `password`"
    },
    "oauth2_password": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`password`"
    },
    "oauth2_scopes": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Required when `type`==`oauth2`, if provided, will be used in the token request"
    },
    "oauth2_token_url": {
      "type": "string",
      "description": "Required when `type`==`oauth2`"
    },
    "oauth2_username": {
      "type": "string",
      "description": "Required when `oauth2_grant_type`==`password`"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "secret": {
      "type": [
        "string",
        "null"
      ],
      "description": "Only if `type`=`http-post` \n\nwhen `secret` is provided, two  HTTP headers will be added: \n  * X-Mist-Signature-v2: HMAC_SHA256(secret, body)\n  * X-Mist-Signature: HMAC_SHA1(secret, body)"
    },
    "single_event_per_message": {
      "type": "boolean",
      "description": "Some solutions may not be able to parse multiple events from a single message (e.g. IBM Qradar, DSM). When set to `true`, only a single event will be sent per message. this feature is only available on certain topics (see [List Webhook Topics]($e/Constants%20Definitions/listWebhookTopics))",
      "default": false
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "splunk_token": {
      "type": [
        "string",
        "null"
      ],
      "description": "Required if `type`=`splunk`. If splunk_token is not defined for a type Splunk webhook, it will not send, regardless if the webhook receiver is configured to accept it."
    },
    "topics": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of supported webhook topics available with the API Call [List Webhook Topics]($e/Constants%20Definitions/listWebhookTopics)"
    },
    "type": {
      "type": "string",
      "description": "enum: `aws-sns`, `google-pubsub`, `http-post`, `oauth2`, `splunk`"
    },
    "url": {
      "type": "string"
    },
    "verify_cert": {
      "type": "boolean",
      "description": "When url uses HTTPS, whether to verify the certificate",
      "default": true
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.webhooks.createOrgWebhook()`

## Usage Context

Creates a new webhook for real-time event notifications.

## Gotchas

- Webhooks push events to external URLs. Ensure the endpoint is reachable.
- Supports topics like `device-events`, `alarms`, `audits`.

## Related Endpoints

- [GET_orgs_org_id_webhooks.md](GET_orgs_org_id_webhooks.md) — List webhooks
- [POST_orgs_org_id_webhooks_webhook_id_ping.md](POST_orgs_org_id_webhooks_webhook_id_ping.md) — Test ping

## MistHelper Notes

Webhook listing uses Menu 47 (`listOrgWebhooks`). Creation is not used directly.
