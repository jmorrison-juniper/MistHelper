# Endpoint Contract: getOrgWebhook

**Feature**: 653-mist-get-org-webhook
**Reference doc**:
`documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md`

## HTTP Contract

| Aspect          | Value                                                                             |
|-----------------|-----------------------------------------------------------------------------------|
| Method          | `GET`                                                                             |
| URL template    | `https://{MIST_HOST}/api/v1/orgs/{org_id}/webhooks/{webhook_id}`                   |
| operationId     | `getOrgWebhook`                                                                   |
| Tag             | `Orgs Webhooks`                                                                   |
| Authentication  | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie).         |
| Request body    | None.                                                                             |
| Query params    | None.                                                                             |
| Pagination      | Not paginated. One request returns one object.                                    |
| Rate limiting   | Standard Mist API rate limits (5000 calls/hour per token). Handled by `mistapi`.  |

### Required Headers

| Header          | Value                                                                              |
|-----------------|------------------------------------------------------------------------------------|
| Authorization   | `Token {MIST_API_TOKEN}` from `.env`. Never logged.                                |
| Accept          | `application/json` (added by `mistapi` by default).                                |
| User-Agent      | Set by `mistapi.APISession` (default `mistapi/{version}`).                         |

### Path Parameters

| Name         | Type   | Required | Description                                                               |
|--------------|--------|----------|---------------------------------------------------------------------------|
| `org_id`     | UUID   | Yes      | Organization UUID. Sourced from user prompt or `.env` `MIST_ORG_ID`.      |
| `webhook_id` | UUID   | Yes      | Webhook UUID. Sourced from user prompt (obtained from menu 47 output).    |

## Response: 200 OK

**Media type**: `application/json`
**Shape**: A single JSON object matching the schema in
`documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id.md` lines 33-186.

### Fields Returned

| Field                     | Type                | Notes                                                                       |
|---------------------------|---------------------|-----------------------------------------------------------------------------|
| `id`                      | UUID (string)       | Server-issued. Primary key for local storage. `readOnly`.                   |
| `org_id`                  | UUID (string)       | Owning org. `readOnly`.                                                     |
| `site_id`                 | UUID (string)       | Present when `for_site == true`. `readOnly`.                                |
| `for_site`                | boolean             | `readOnly`.                                                                 |
| `name`                    | string or null      | Human-readable name.                                                        |
| `enabled`                 | boolean             | Default `true`.                                                             |
| `type`                    | string              | Enum: `aws-sns`, `google-pubsub`, `http-post`, `oauth2`, `splunk`.          |
| `url`                     | string              | Target URL (types `http-post`, `oauth2`, `splunk`).                         |
| `verify_cert`             | boolean             | Default `true`. HTTPS-only.                                                 |
| `topics`                  | array of string     | Subscribed topic names.                                                     |
| `single_event_per_message`| boolean             | Default `false`.                                                            |
| `headers`                 | object or null      | Additional HTTP headers when `type == http-post`.                           |
| `secret`                  | string or null      | HMAC signing secret. **Sensitive.**                                         |
| `assetfilter_ids`         | array of UUID       | Only when `type == asset-raw-rssi`.                                         |
| `splunk_token`            | string or null      | HEC token when `type == splunk`. **Sensitive.**                             |
| `oauth2_grant_type`       | string              | Enum: `client_credentials`, `password`. Required when `type == oauth2`.     |
| `oauth2_token_url`        | string              | Required when `type == oauth2`.                                             |
| `oauth2_client_id`        | string              | Required when `oauth2_grant_type == client_credentials`.                    |
| `oauth2_client_secret`    | string              | Required when `oauth2_grant_type == client_credentials`. **Sensitive.**     |
| `oauth2_username`         | string              | Required when `oauth2_grant_type == password`.                              |
| `oauth2_password`         | string              | Required when `oauth2_grant_type == password`. **Sensitive.**               |
| `oauth2_scopes`           | array of string     | Token scopes.                                                               |
| `created_time`            | number (epoch s)    | Server timestamp. `readOnly`.                                               |
| `modified_time`           | number (epoch s)    | Server timestamp. `readOnly`.                                               |

### Example Success Payload

```json
{
    "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
    "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    "site_id": null,
    "for_site": false,
    "name": "noc-splunk-prod",
    "enabled": true,
    "type": "splunk",
    "url": "https://splunk.example.com:8088/services/collector/event",
    "verify_cert": true,
    "topics": ["alarms", "audits", "device-events"],
    "single_event_per_message": false,
    "splunk_token": "REDACTED-IN-LOGS",
    "created_time": 1717200000,
    "modified_time": 1719014400
}
```

## Error Responses

| Status | Reason                                | MistHelper Handling                                                                                          |
|--------|---------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (malformed UUID)           | Caught at pre-flight `_is_uuid` check; `logging.warning` + return code 1. Should not reach the API.          |
| 401    | Unauthorized (invalid / missing token)| `logging.error("Mist API rejected the token (401); check MIST_API_TOKEN in .env")`; return code 2.           |
| 403    | Permission Denied                     | `logging.error("Token lacks read permission on org %s (403)", org_id)`; return code 2.                       |
| 404    | Not Found (unknown org or webhook)    | `logging.warning("Webhook %s not found in org %s (404)", webhook_id, org_id)`; return code 1.                |
| 429    | Rate Limited (5000 calls/hour)        | Adaptive delay (delay_metrics.json / tuning_data.json) triggers back-off inside `mistapi`; caller retries.   |

Any unexpected exception is caught with `logging.exception("Unhandled error
in getOrgWebhook")` and returns code 3, matching the observability contract
in `.github/copilot-instructions.md`.

## mistapi Python Call Signature

```python
import mistapi                                                                              # Sole permitted Mist Cloud SDK per Principle II
from mistapi.api.v1.orgs import webhooks as _webhooks                                       # Endpoint module name matches the OpenAPI path

# self.session is an already-authenticated mistapi.APISession instance
# (constructed from MIST_HOST + MIST_API_TOKEN at MistHelper startup).
response = _webhooks.getOrgWebhook(                                                         # Function name matches operationId exactly
    self.session,                                                                           # Positional 1: authenticated session
    org_id,                                                                                 # Positional 2: path param org_id (UUID string)
    webhook_id,                                                                             # Positional 3: path param webhook_id (UUID string)
)                                                                                           # Returns mistapi.APIResponse

payload = response.data                                                                     # response.data is a dict (single webhook object)
```

### Return Value Shape

`response.data` is a Python `dict` with the fields tabulated above. It is
never a list, never `None` on 200, and never wrapped in an envelope. On a
non-2xx status the SDK raises `mistapi.MistAPIException` (or a request-level
exception), which the caller catches per the Error Responses table above.

### Do Not

- Do not call the underlying `response.raw` HTTP object directly -- the SDK
  handles pagination, retries, and adaptive delays. Bypassing it violates
  Constitution Principle II (Class-Based Architecture -- no wrappers) and
  Principle IV (Full Deployment Pipeline -- consistent transport layer).
- Do not log `response.data` verbatim. Route it through
  `self._redact_secrets(...)` before any `logging.debug` / `logging.info`
  call. Secrets are stored to the configured backend but never emitted to
  logs.
- Do not cache `response.data` across users or sessions -- webhook secrets
  are per-org sensitive material and must not persist in in-memory shared
  state.
