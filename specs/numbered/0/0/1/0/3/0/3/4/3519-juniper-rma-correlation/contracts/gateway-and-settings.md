# Contract: Gateway Rules and Settings

## Settings

Values come from the environment or from the `.env` file. The `.env` file is git-ignored. `deploy/.env.example` lists the names with comments and no values.

| Name | Required | Secret | Default | Purpose |
| - | - | - | - | - |
| `JUNIPER_APP_ID` | Yes | Yes | None | Application identifier from onboarding |
| `JUNIPER_CLIENT_ID` | Yes | Yes | None | OAuth 2.0 client ID from onboarding |
| `JUNIPER_CLIENT_SECRET` | Yes | Yes | None | OAuth 2.0 client secret from onboarding |
| `JUNIPER_TOKEN_URL` | No | No | `https://apigw.juniper.net/invoke/pub.apigateway.oauth2/getAccessToken` | OAuth 2.0 token endpoint from the endpoints document |
| `JUNIPER_USER_ID` | Yes | No. Masked in logs. | None | Registered portal user |
| `JUNIPER_ACCOUNT_ID` | Yes | No | None | Account identifier |
| `JUNIPER_CONTACT_EMAIL` | Yes for case calls | No. Masked in logs. | None | Contact linked to the account |
| `JUNIPER_CUSTOMER_SOURCE_ID` | Yes | No | None | Source identifier from onboarding |
| `JUNIPER_TICKET_KEY_FIELD` | No | No | `case_number` | Mist ticket field that holds the customer case number. Allowed values: `case_number` or `id` (O-1). |
| `JUNIPER_CASE_BASE_URL` | No | No | `https://apigw.juniper.net/css-caseapi/1.0` | Case API base address. The export lists this server (O-9). |
| `JUNIPER_ASSET_BASE_URL` | No | No | `https://apigw.juniper.net/css-asset/1.0` | Asset API base address. The export lists this server (O-9). |
| `JUNIPER_ALLOWED_HOSTS` | No | No | `apigw.juniper.net` | Comma-separated host allowlist |
| `JUNIPER_MAX_REQUESTS_PER_SECOND` | No | No | `2` | Allowed range 0.5 to 10 (R-10) |
| `JUNIPER_MAX_RETRY_ATTEMPTS` | No | No | `3` | Allowed range 1 to 5 (R-11) |
| `JUNIPER_CA_BUNDLE` | No | No | Unset | CA bundle path for TLS inspection (R-13) |
| `JUNIPER_PII_RETENTION_DAYS` | No | No | `180` | Allowed range 1 to 730 (R-14) |
| `JUNIPER_LIVE_TESTS` | No | No | Unset | Set to `1` to allow live calls under test modes (R-17) |

Settings rules:

- A missing required name stops the action. The message lists the names only.
- The loader never prints a value. A secret value never reaches a log line or an export.
- An invalid number, such as a rate of zero, stops the action and names the setting.
- A ticket key field other than `case_number` or `id` stops the action and names the setting.
- A base address that is not HTTPS stops the action.
- An empty value counts as unset.

## Gateway Rules

`JuniperGatewayClient` enforces these rules for every request.

1. Use only HTTPS base addresses. The host must appear in `JUNIPER_ALLOWED_HOSTS`.
2. Send the bearer token only to an allowed host. Request tokens only from the token endpoint. Never log a token or a secret.
3. Disable redirects. A `3xx` reply is an unexpected result. It is never followed.
4. Use a connect timeout of 10 seconds and a read timeout of 60 seconds.
5. Limit each response to 16 MB. Enforce the limit while the body streams.
6. Limit the request rate with a token bucket. The default is 2 requests per second.
7. Retry connection errors, timeouts, and HTTP 429, 502, 503, and 504. Allow `JUNIPER_MAX_RETRY_ATTEMPTS` attempts. Wait 2 seconds, then 4 seconds. Use a new transaction identifier for each attempt.
8. Verify TLS. When `JUNIPER_CA_BUNDLE` is set, pass it as the `verify` value.
9. Never log a body. Log keys, counts, and status codes only.

## Log Line Format

Each line uses ASCII only. Each line shows the endpoint name and the outcome.

```text
juniper.request endpoint=querysrlist attempt=1 http_status=200 body_status=200 elapsed_ms=812 transaction=<32 hex characters>
juniper.response endpoint=querysrdetails body_status=400 fault_count=1 fault_codes=763
juniper.retry endpoint=querysrlist attempt=2 reason=http_503 wait_seconds=2
juniper.redirect_refused endpoint=querysrlist http_status=302
```

The transaction identifier is a request identifier, not a secret. The log never shows the key, the app identifier, a full email address, or a full telephone number.
