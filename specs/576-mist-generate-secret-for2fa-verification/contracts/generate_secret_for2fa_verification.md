# Phase 1 Contract: generateSecretFor2faVerification

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data Model**: [../data-model.md](../data-model.md)

This contract is the authoritative reference for the HTTP call and the mistapi SDK
invocation that the new MistHelper menu item will issue. It is derived from
`documentation/api/self/GET_self_two_factor_token.md` (enriched per-endpoint doc
generated from the Mist OpenAPI 3 spec).

## HTTP Contract

| Field           | Value                                                                          |
|-----------------|--------------------------------------------------------------------------------|
| Method          | `GET`                                                                          |
| URL template    | `https://{MIST_HOST}/api/v1/self/two_factor/token`                             |
| Tag             | `Self MFA`                                                                     |
| operationId     | `generateSecretFor2faVerification`                                             |
| Path parameters | _None._                                                                        |
| Query parameters| `by` (optional, string). When `"qrcode"`, response is a PNG image. Omit -> JSON. |
| Required headers| `Authorization: Token <api_token>` (injected by `mistapi.APISession`)          |
| Request body    | _None._                                                                        |
| Pagination      | Not paginated.                                                                 |
| Rate limit      | Standard Mist API 5000 calls / hour per token.                                 |

### Example Raw Requests

JSON variant:

```http
GET /api/v1/self/two_factor/token HTTP/1.1
Host: api.mist.com
Authorization: Token <REDACTED>
Accept: application/json
```

QR code variant:

```http
GET /api/v1/self/two_factor/token?by=qrcode HTTP/1.1
Host: api.mist.com
Authorization: Token <REDACTED>
Accept: image/png
```

## Response Schema (200 Success)

### JSON Variant (default, `by` omitted)

`Content-Type: application/json`

```json
{
  "type": "object",
  "properties": {
    "two_factor_secret": {
      "type": "string",
      "examples": [
        "NRMTSTRWNBVECY3GJVYEY3DDJFRGSNCZGJUDO4RVN5FDM3DUMJSA"
      ]
    }
  }
}
```

- `two_factor_secret`: Base32-encoded TOTP seed (RFC 4648 alphabet `[A-Z2-7]`).
  Treat as sensitive -- write to data backend only, never to logs.

### QR Code Variant (`by=qrcode`)

`Content-Type: image/png` -- raw PNG bytes of a QR code that encodes the otpauth URL
for the same TOTP secret. MistHelper persists the bytes to
`data/self_two_factor_qrcode_<captured_at>.png` and stores the relative filename in the
`qrcode_path` column of the `self_two_factor_token` table; `two_factor_secret` is NULL
for qrcode rows.

## Error Responses and MistHelper Handling

| Status | Mist meaning                                          | MistHelper action                                                                                  |
|--------|-------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (e.g. unknown `by` value)                  | `logging.warning("Mist API rejected request: %s", response.status_code)`; menu method returns 0.   |
| 401    | Unauthorized (bad / expired token)                    | `logging.error("Mist API token unauthorized; check MIST_API_TOKEN in .env")`; menu method returns 0. No secret value can ever appear -- there is no 200 payload. |
| 403    | Permission Denied (token lacks 2FA scope)             | `logging.error("Mist API token lacks permission for /self/two_factor/token")`; menu method returns 0. |
| 404    | Endpoint not found (e.g. wrong region in `MIST_HOST`) | `logging.warning("Endpoint not found on host %s; verify MIST_HOST region", host)`; menu method returns 0. |
| 429    | Rate limit hit (5000 calls / hour exhausted)          | Adaptive delay system increases back-off; the call is retried per `delay_metrics.json`. If retries are exhausted, `logging.warning("Rate limited, deferring run")` and menu method returns 0. |

In every error case the operator sees a single ASCII WARNING or ERROR line, no
traceback, and no leakage of the API token or any partial secret. The menu method
returns control to the main loop with a non-failing exit so the test sweep can
continue.

## mistapi SDK Call Signature

The exact Python call the menu method issues:

```python
import mistapi
from mistapi.api.v1.self.mfa import generateSecretFor2faVerification

# self._mist_session is a mistapi.APISession built once at MistHelper startup from
# MIST_HOST and MIST_API_TOKEN in .env (per the existing session-init helper).
response = generateSecretFor2faVerification(
    self._mist_session,            # positional: APISession (required)
    by="qrcode" if output_mode == "qrcode" else None,  # only send param when needed
)

# JSON variant: response.data is dict {"two_factor_secret": "..."}.
# QR variant:   response.data is raw bytes (PNG). Detect via response.headers
#               "Content-Type" or via the output_mode the caller already chose.
```

The MistHelper menu method documented in `quickstart.md` wraps this call with prompt
collection (`safe_input()`), validation, flatten, persistence
(`DataExporter.write_with_format_selection`), and the seven required log statements
(four `INFO` before-action, three `DEBUG` after-action, redacted of the secret value).

## Test Cases the Contract Must Support

These scenarios are exercised by `tasks.md` -> implementation -> `python MistHelper.py
--test`:

1. **Default JSON happy path**: `by` omitted, 200 JSON returned, one row written, secret
   value present in backend but absent from logs.
2. **QR code happy path**: `by=qrcode`, 200 PNG returned, PNG file written to `data/`,
   row written with `two_factor_secret = NULL` and `qrcode_path` populated.
3. **EOF on prompt**: `safe_input()` raises `EOFError`, process exits 0 cleanly, no
   API call issued.
4. **401 unauthorized**: ERROR logged, menu method returns 0, no row written.
5. **429 rate limit**: adaptive delay engages, retry succeeds, single row written; if
   retries exhausted WARNING logged and method returns 0.
6. **Re-run idempotency**: second invocation within the same second triggers the
   `UNIQUE (captured_at)` constraint and is treated as a no-op upsert per the
   `auto_increment_with_unique` strategy.

## Cross-References

- Enriched OpenAPI doc: [`documentation/api/self/GET_self_two_factor_token.md`](../../../documentation/api/self/GET_self_two_factor_token.md)
- Related endpoint (verify step): [`documentation/api/self/POST_self_two_factor_verify.md`](../../../documentation/api/self/POST_self_two_factor_verify.md)
- Data model and PK strategy: [`../data-model.md`](../data-model.md)
- Local run guide and quality gates: [`../quickstart.md`](../quickstart.md)
