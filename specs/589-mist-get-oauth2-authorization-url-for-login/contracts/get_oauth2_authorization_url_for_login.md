# Endpoint Contract: getOauth2AuthorizationUrlForLogin

**Feature**: 589 -- Mist API GET endpoint `getOauth2AuthorizationUrlForLogin`
**Source doc**: `documentation/api/admins/GET_login_oauth_provider.md`
**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)

## HTTP Contract

| Aspect | Value |
|--------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/login/oauth/{provider}` |
| OpenAPI operationId | `getOauth2AuthorizationUrlForLogin` |
| OpenAPI tag | `Admins Login - OAuth2` |
| Auth header | `Authorization: Token {api_token}` (alternative: `X-CSRFToken` cookie) |
| Other required headers | `Accept: application/json` |
| Request body | None (GET) |
| Pagination | Not paginated |
| Rate limiting | Standard Mist API rate limits (5000 calls per hour per token); 429 triggers MistHelper adaptive delay |

### Path parameters

| Name | Type | Required | Description | MistHelper validation |
|------|------|----------|-------------|-----------------------|
| `provider` | string | Yes | OAuth2 identity provider name (for example `google`, `azure`). Free-form string in the OpenAPI spec; the Mist back end accepts the providers configured for the tenant. | `^[a-z0-9_-]{1,32}$` after `.strip().lower()`. On regex failure: `logging.warning(...)` and return without calling the API. |

### Query parameters

| Name | Type | Required | Default | Description | MistHelper handling |
|------|------|----------|---------|-------------|---------------------|
| `forward` | string | No | None | Callback URL the Mist back end will redirect the browser to after the OAuth2 flow completes. | Pass through after `.strip()`. Empty string -> `None` (parameter omitted). If non-empty and not starting with `http://` or `https://`, log a warning and pass `None`. |

### Example resolved URL

```text
GET https://api.mist.com/api/v1/login/oauth/google?forward=https%3A%2F%2Fmy.example.com%2Fcallback
Authorization: Token <redacted>
Accept: application/json
```

## Response Contract

### 200 OK

The response is a single JSON object with two required scalar fields.

#### Schema (from `documentation/api/admins/GET_login_oauth_provider.md`)

```json
{
  "type": "object",
  "properties": {
    "authorization_url": { "type": "string" },
    "client_id":         { "type": "string" }
  },
  "required": ["authorization_url", "client_id"]
}
```

#### Sample response body

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=1234567890-abc.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Fapi.mist.com%2Fapi%2Fv1%2Flogin%2Foauth%2Fgoogle&response_type=code&scope=openid+email+profile&state=eyJ...&access_type=online",
  "client_id": "1234567890-abc.apps.googleusercontent.com"
}
```

#### MistHelper flattening

The response is flattened into one row matching the SQLite DDL in
[../data-model.md](../data-model.md). The row carries the operator-supplied `provider`
and `forward` plus a synthesized `fetched_at` ISO-8601 UTC timestamp.

### Error responses

| Status | Meaning | MistHelper handling |
|--------|---------|---------------------|
| 400 | Bad Syntax | `logging.warning("OAuth2 400: malformed request for provider %s", provider)` then return. Most commonly a malformed `forward` URL the local regex did not catch. |
| 401 | Unauthorized | `logging.warning("OAuth2 401: API token rejected; check MIST_API_TOKEN in .env")` then return. No retry -- the token is wrong and re-trying will only count against the rate limit. |
| 403 | Permission Denied | `logging.warning("OAuth2 403: account lacks permission for OAuth2 provider %s", provider)` then return. The Mist tenant is gated from this endpoint. |
| 404 | Provider not found | `logging.warning("OAuth2 404: provider %s is not configured for this tenant", provider)` then return. Surfaced as a soft failure, never a traceback. |
| 429 | Too Many Requests | Defer to the shared adaptive delay loop (`delay_metrics.json` + `tuning_data.json`). `mistapi` raises a retry-eligible exception which MistHelper's existing back-off catches; after the configured retry budget is exhausted, `logging.warning("OAuth2 429: rate limited; back-off exhausted")` and return. |

Any other 5xx response or unexpected exception falls through to
`logging.exception("OAuth2 unexpected error for provider %s", provider)` and the menu
method returns cleanly so the parent menu loop is not killed.

## mistapi SDK Call Signature

The SDK-generated module name contains a literal `-` character that is not legal in a
Python identifier, so the implementation imports the module through `importlib`:

```python
import importlib                                            # std lib; already imported in MistHelper.py
# ...
oauth_mod = importlib.import_module(                        # SDK module name from the enriched doc
    "mistapi.api.v1.admins.login_-_oauth2"
)
response = oauth_mod.getOauth2AuthorizationUrlForLogin(     # exact SDK function name (camelCase)
    self.api,                                               # the active mistapi.APISession
    provider,                                               # required path parameter
    forward=forward,                                        # optional query parameter; None -> omitted
)
```

`response` is an `mistapi.APIResponse`-shaped object with the following attributes used
by MistHelper:

| Attribute | Type | Notes |
|-----------|------|-------|
| `response.status_code` | int | Expect `200` on success. |
| `response.data` | dict | `{"authorization_url": str, "client_id": str}` per the schema above. |
| `response.headers` | Mapping | Not consumed by MistHelper for this endpoint. |
| `response.url` | str | Resolved URL; logged at DEBUG only with the token redacted by `mistapi`. |

## Side Effects

None. The endpoint is HTTP GET and read-only on the server. MistHelper persists one row
through `DataExporter.write_with_format_selection()`; that write is the only durable
effect of invoking the menu.

## Idempotency

Each call re-uses the same `provider` primary key, so the row is upserted (`INSERT OR
REPLACE` in SQLite, document `_key` update in ArangoDB, row overwrite in CSV mode). The
Mist back end returns a fresh `state` token inside `authorization_url` on every call, so
the row content changes even though the key does not -- this is the intended,
documented behavior.

## Backward Compatibility

This is a new operationId never previously catalogued in MistHelper. No existing menu
items, tables, or CSV files are affected. The only schema-level addition is the new
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry and the new `login_oauth_authorization_url`
SQLite table created automatically by `DataExporter` on first run.
