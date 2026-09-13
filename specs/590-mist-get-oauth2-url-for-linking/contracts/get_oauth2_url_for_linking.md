# Contract: GET /api/v1/self/oauth/{provider}

**operationId**: `getOauth2UrlForLinking`
**Mist API tag**: `Self OAuth2`
**Source doc**: `documentation/api/self/GET_self_oauth_provider.md`

---

## HTTP Contract

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/self/oauth/{provider}` |
| Authentication | `Authorization: Token {MIST_API_TOKEN}` header (alternatively `X-CSRFToken` cookie) |
| Idempotent | Yes |
| Paginated | No |
| Returns | Single JSON object (not a list) |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `provider` | string | yes | OAuth2 provider slug. Must match a Mist-supported provider name. MistHelper validates against an allow-list (`google`, `microsoft`, `azure`, `okta`) before issuing the call to avoid wasting rate-limit slots on certain 404s. |

### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `forward` | string | no | _(omitted)_ | Post-link redirect URL. When supplied, Mist embeds it into the returned `authorization_url`'s state so the browser returns there after the provider handshake. |

### Request Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Token {MIST_API_TOKEN}` | yes |
| `Accept` | `application/json` | recommended (the `mistapi` SDK sets this automatically) |

### Request Body

None. GET requests carry no payload.

---

## Response: 200 OK

```json
{
  "type": "object",
  "properties": {
    "authorization_url": { "type": "string" },
    "linked":            { "type": "boolean" }
  },
  "required": [
    "authorization_url",
    "linked"
  ]
}
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `authorization_url` | string | yes | Fully-qualified https URL the operator pastes into a browser. Carries a one-time CSRF / state token; treat as sensitive -- do NOT log the value. |
| `linked` | boolean | yes | `true` when the named provider is already linked to the authenticated admin account; `false` otherwise. |

MistHelper appends four columns at flatten time (`provider`, `forward`,
`fetched_at_utc`, `mist_host`) so the persisted row is six columns wide. See
`data-model.md` for the SQLite DDL.

---

## Error Responses & MistHelper Handling

| Status | Mist Meaning | MistHelper Action |
|--------|--------------|-------------------|
| 400 Bad Syntax | Malformed request | `logging.warning("OAuth2 link URL: 400 from Mist -- check provider / forward shape")`, early return, exit code 0. |
| 401 Unauthorized | Missing / invalid API token | `logging.error("OAuth2 link URL: 401 -- MIST_API_TOKEN missing or expired")`, early return, exit code 0. Operator must refresh the token in `.env`. |
| 403 Permission Denied | Token lacks the scope for self-account changes | `logging.warning("OAuth2 link URL: 403 -- token lacks permission for self/oauth scope")`, early return, exit code 0. |
| 404 Not Found | Unknown provider, or endpoint disabled on this Mist host | `logging.warning("OAuth2 link URL: 404 -- provider '%s' is not recognized by Mist", provider)`, early return, exit code 0. The provider allow-list reduces the chance of this firing in normal use. |
| 429 Too Many Requests | 5000-calls-per-hour threshold hit | The `mistapi` SDK's adaptive back-off (tuned by `delay_metrics.json` + `tuning_data.json`) handles this transparently; on persistent 429 MistHelper logs a `WARNING` and returns early without a traceback. |
| 5xx Server Errors | Mist Cloud incident | `logging.error("OAuth2 link URL: %d from Mist -- transient server error", status)`, early return, exit code 0. The operator retries later. |

Across all error paths MistHelper exits with code 0 (per Principle III -- no
traceback escapes to the operator's shell) and the row is NOT written to disk.

---

## Exact mistapi Python Call Signature

```python
import mistapi
from mistapi.api.v1.self import oauth2

apisession = mistapi.APISession(
    host="api.mist.com",                              # from .env -> MIST_HOST
    apitoken="abcdef...",                             # from .env -> MIST_API_TOKEN
)
apisession.login()                                    # validates token, populates session

response = oauth2.getOauth2UrlForLinking(             # SDK call, account-scoped (no org_id)
    apisession,
    "google",                                          # required path param: provider slug
    forward=None,                                      # optional query param: post-link redirect
)

# response is a mistapi.APIResponse object
url    = response.data["authorization_url"]            # str -- treat as sensitive
linked = bool(response.data["linked"])                 # bool -- True if already linked
```

Notes:

- The SDK function name and module path (`mistapi.api.v1.self.oauth2`) come from
  the enriched per-endpoint doc at
  `documentation/api/self/GET_self_oauth_provider.md`. If a future `mistapi`
  release re-shuffles the module layout, the task agent re-verifies against the
  installed package; this contract records the doc-canonical path as of
  2026-06-29.
- `response.data` is already a `dict`; no manual `json.loads` is required.
- `response.status_code` (if present in the SDK build) carries the HTTP status
  for the error-handling table above. Older `mistapi` builds raise an exception
  instead -- MistHelper catches both via the standard `try / except` pattern
  used by adjacent menu items.

---

## Curl Reference (for ad-hoc debugging only -- not used by MistHelper)

```bash
curl -sS -H "Authorization: Token $MIST_API_TOKEN" \
     "https://$MIST_HOST/api/v1/self/oauth/google?forward=https%3A%2F%2Flocalhost%3A8055%2Fpost-link"
```

The constitution forbids `requests`-based access from MistHelper code -- this
curl example is documentation only.

---

## Acceptance for this Contract

A correct implementation:

1. Imports `mistapi.api.v1.self.oauth2` (NOT `requests`).
2. Calls `getOauth2UrlForLinking(apisession, provider, forward=...)` exactly once
   per invocation.
3. Validates `provider` against the allow-list before the call.
4. Persists a six-column row via `DataExporter.write_with_format_selection`.
5. Logs the action pair before/after the call without exposing the
   `authorization_url` content.
6. Returns cleanly on any 4xx / 5xx without a traceback.
