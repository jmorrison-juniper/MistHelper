# Contract: downloadSiteRfdiagRecording

## Identity

| Attribute | Value |
|-----------|-------|
| operationId | `downloadSiteRfdiagRecording` |
| HTTP method | `GET` |
| OpenAPI path | `/api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download` |
| Tag | `Sites Rfdiags` |
| Source doc | `documentation/api/sites/GET_sites_site_id_rfdiags_rfdiag_id_download.md` |
| Side effects on Mist Cloud | None (read-only) |
| Pagination | None |

## HTTP Contract

### Request line

```
GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download HTTP/1.1
Host: {MIST_HOST}            # e.g. api.mist.com, api.eu.mist.com, api.gc1.mist.com
Authorization: Token {MIST_API_TOKEN}
Accept: application/octet-stream, application/json
```

### Path parameters

| Name        | Type   | Required | Description |
|-------------|--------|----------|-------------|
| `site_id`   | string (UUID) | Yes | The Mist site UUID owning the recording |
| `rfdiag_id` | string (UUID) | Yes | The RF diagnostics recording UUID (site-scoped, opaque) |

### Query parameters

None.

### Request headers

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `Token {MIST_API_TOKEN}` | Loaded from `.env` by `mistapi.APISession`; never logged |
| `Accept` | `application/octet-stream, application/json` | The Mist backend returns a JSON envelope whose body is a base64-encoded string per the OpenAPI schema |
| `X-CSRFToken` | (cookie-based alternative) | Not used by MistHelper -- token auth is the only path |

### Request body

None.

## Response: 200 OK

### Schema (from OpenAPI 3.0)

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
}
```

That is, the response payload is a **base64-encoded string** representing
the binary `raw_events` recording blob. There is no nested object; the
string IS the response body.

### Decoding contract (MistHelper)

```python
encoded = response.data or ""                                # the base64 string from mistapi
decoded = base64.b64decode(encoded)                          # bytes, ready for file write
sha256 = hashlib.sha256(decoded).hexdigest()                 # 64-char hex content fingerprint
```

### Sample (illustrative, not real)

The on-disk artifact is opaque bytes; no sample is meaningful in
documentation. The ledger receipt row written via `DataExporter` is:

```json
{
  "site_id":       "11111111-2222-3333-4444-555555555555",
  "rfdiag_id":     "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "filename":      "data/rfdiags/11111111-2222-3333-4444-555555555555_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.raw",
  "byte_count":    1048576,
  "sha256":        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "downloaded_at": "2026-06-29T20:15:33Z",
  "org_id":        "01234567-89ab-cdef-0123-456789abcdef"
}
```

## Error Responses and MistHelper Handling

| Status | Source / Meaning | MistHelper Handling |
|--------|------------------|---------------------|
| `400 Bad Syntax` | Malformed `site_id` or `rfdiag_id`; should not occur if UUID validation runs first | Log `WARNING` with the offending field name (NOT the token); return early without writing any artifact |
| `401 Unauthorized` | API token missing, expired, or wrong cloud region | Log `ERROR` "Authentication failed -- check MIST_API_TOKEN and MIST_HOST"; return early |
| `403 Permission Denied` | Token lacks permission for the site / org | Log `ERROR` "Permission denied for site=%s -- check token role"; return early |
| `404 Not Found` | `site_id` or `rfdiag_id` does not exist, or the recording has been deleted upstream | Log `WARNING` "rfdiag not found site=%s rfdiag=%s -- nothing to download"; return early with exit code 0 (per spec edge case) |
| `429 Too Many Requests` | API token has crossed the 5000-calls-per-hour threshold | Surface to the adaptive delay system (`delay_metrics.json` + `tuning_data.json`); mistapi auto-retries with back-off; on persistent 429, log `ERROR` and return early |
| Network failure / timeout | Transport-level error before any HTTP status is received | Log `ERROR` via `logging.exception(...)` with full traceback; return early without writing any artifact |

In every error path the on-disk blob is NOT written and the ledger row
is NOT inserted -- partial state is the worst outcome a user can
encounter, so the contract is "all or nothing per invocation".

## Authentication

Same as every Mist API call in MistHelper:

- `mistapi.APISession` constructed from `MIST_HOST` and `MIST_API_TOKEN`
  environment variables (loaded via `python-dotenv`).
- The token is sent as `Authorization: Token {token}` by the underlying
  `requests` session.
- The token is never logged, never written to disk, never echoed to the
  user, and never embedded in any error message.

## Rate Limiting

Standard Mist API rate limits apply:

- 5000 API calls per hour per token.
- 429 responses are handled by the adaptive delay system (no caller-side
  manual sleep).
- The endpoint counts as one call per invocation; the typical user
  invokes this menu interactively a handful of times per session, so
  rate impact is negligible.

## Exact mistapi Python Call

```python
import mistapi
from mistapi.api.v1.sites.rfdiags.download import downloadSiteRfdiagRecording

apisession = mistapi.APISession()                                     # picks up MIST_HOST + MIST_API_TOKEN from .env
apisession.login()                                                    # validates auth before first call

response = downloadSiteRfdiagRecording(                               # the sole permitted call to this endpoint
    apisession,                                                       # arg 1: shared session (carries auth + retry config)
    site_id,                                                          # arg 2: Mist site UUID, required
    rfdiag_id,                                                        # arg 3: RF diagnostics recording UUID, required
)

# response.status_code -> int (200 on success)
# response.data        -> str (base64-encoded blob)
# response.headers     -> dict (HTTP response headers)
```

The function lives in the `mistapi.api.v1.sites.rfdiags.download`
module (matches the OpenAPI path -> module mapping convention used by
mistapi 0.59+). The call is positional-only at the SDK boundary
(`apisession`, `site_id`, `rfdiag_id`); no keyword arguments are
accepted.

## Idempotency

The endpoint itself is idempotent (multiple GETs return the same
payload as long as the upstream recording is unchanged). MistHelper
preserves that contract by:

- Overwriting the on-disk blob at the deterministic path
  `data/rfdiags/<site_id>_<rfdiag_id>.raw` on every successful
  invocation.
- Upserting the `site_rfdiag_downloads` SQLite row by composite PK
  `(site_id, rfdiag_id)`.
- Refreshing the `downloaded_at` and `sha256` columns on every run
  (so a drift in `sha256` over time is visible in the ledger).

## Acceptance test (per spec)

Given valid credentials and a known `(site_id, rfdiag_id)` pair, when
the user selects menu 96 and supplies the two IDs, then:

1. `data/rfdiags/<site_id>_<rfdiag_id>.raw` exists and is non-empty.
2. The SQLite table `site_rfdiag_downloads` contains exactly one row
   with that composite PK and a non-empty `sha256`.
3. The process exits 0.
4. Re-running with the same IDs leaves the row count unchanged
   (upsert, not insert) and the file size unchanged when the upstream
   recording has not changed.
