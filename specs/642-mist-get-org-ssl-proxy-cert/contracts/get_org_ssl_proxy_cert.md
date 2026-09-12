# Contract: getOrgSslProxyCert

Authoritative reference:
`documentation/api/orgs/GET_orgs_org_id_ssl_proxy_cert.md`.

## HTTP contract

| Attribute       | Value |
|-----------------|-------|
| Method          | `GET` |
| URL template    | `https://{MIST_HOST}/api/v1/orgs/{org_id}/ssl_proxy_cert` |
| Path parameters | `org_id` (string, UUID, **required**) -- the Mist organisation identifier. |
| Query parameters | _None._ |
| Request body    | _None._ |
| Required headers | `Authorization: Token {MIST_API_TOKEN}` (or the equivalent `X-CSRFToken` cookie when using session auth). `Accept: application/json` is set by mistapi. |
| Idempotent      | Yes (safe read). |
| Paginated       | No. |
| Rate limit      | Standard Mist API limits: 5000 requests / hour / token. |

### `MIST_HOST` values

| Region                 | Host             |
|------------------------|------------------|
| Global                 | `api.mist.com`   |
| EMEA                   | `api.eu.mist.com`|
| GovCloud               | `api.gc1.mist.com` |
| APAC                   | `api.ac2.mist.com` |

## Success response (200)

Content-Type: `application/json`. Body is a single JSON object:

```json
{
  "cert": "-----BEGIN CERTIFICATE-----\nMIIowDQYJKoZIhvcNAQELBQE...\n-----END CERTIFICATE-----"
}
```

### Response schema

| Field  | Type   | Nullable | Description |
|--------|--------|----------|-------------|
| `cert` | string | Yes      | PEM-encoded X.509 SSL proxy certificate used by SRX gateways for SSL inspection. May be absent or empty when no cert is configured for the org. |

MistHelper enriches the row with `org_id` (path parameter echoed), `cert_len`
(derived byte length), and `fetched_at` (UTC ISO-8601 timestamp) before
persistence -- see `../data-model.md`.

## Error responses

| Status | Meaning | MistHelper handling |
|--------|---------|---------------------|
| 400    | Bad Syntax -- malformed request line. Almost never reached from mistapi since the SDK constructs the URL. | Log at `ERROR`; the exception from `mistapi` is caught, message logged (no token, no full URL), method returns without writing output. |
| 401    | Unauthorized -- missing or invalid API token. | Log at `ERROR` with `logging.exception`; the caller sees a clear "check MIST_API_TOKEN in .env" message; method returns without writing output. Token itself is never included in the log line. |
| 403    | Permission Denied -- the token principal lacks read access to the org. | Log at `WARNING` with the org_id only; method returns without writing output. This is normal in MSP contexts where the token cannot see every child org. |
| 404    | Not found -- the org does not exist or the org has no SSL proxy cert configured. | Log at `WARNING` "SSL proxy cert not found for org %s" and return an empty rows list -- do not raise. DataExporter is *not* called for zero-row results; the menu reports "no data returned" and exits cleanly per the spec's Edge Cases section. |
| 429    | Too Many Requests -- 5000/hour throttle hit. | Adaptive-delay path already in `mistapi` / `APICoreFetchUtils` handles back-off using `delay_metrics.json` and `tuning_data.json`. The user sees no traceback; the call is retried per the existing retry budget. |
| 5xx    | Mist Cloud transient. | Existing retry logic applies (retry with exponential back-off up to the configured cap); on final failure, log at `ERROR` and return without writing output. |

## Exact mistapi Python call signature

```python
import mistapi
from mistapi.api.v1.orgs.cert import getOrgSslProxyCert

session: mistapi.APISession   # Built once from .env by ConfigUtils.get_shared_mist_session()
org_id:  str                  # Validated UUID string

response: mistapi.APIResponse = getOrgSslProxyCert(session, org_id)

# response.status_code -> int (200 on success)
# response.data        -> dict; expected shape {"cert": "<PEM string>"} or {} when absent
# response.headers     -> dict of response headers
# response.url         -> str; do NOT log (contains org_id path segment; low-sensitivity but consistent with policy of not logging full URLs)
```

### Notes on the SDK import path

- The enriched endpoint doc names the SDK module
  `mistapi.api.v1.orgs.cert.getOrgSslProxyCert()`. This is authoritative.
- The feature spec header lists the module as
  `mistapi.api.v1.orgs.ssl_proxy_cert`. That path does not exist in
  `mistapi` 0.59+ -- org-level certificate operations
  (`getOrgCert`, `getOrgSslProxyCert`) live under a shared `cert`
  sub-package. Use the `cert` module and ignore the spec header on this
  point (documented in `../research.md`, Research Task 1).

## Preconditions

- `.env` provides `MIST_HOST` and `MIST_API_TOKEN`.
- The token principal has at least `read` scope on
  `orgs/{org_id}/ssl_proxy_cert`.
- `org_id` is a well-formed Mist UUID (validated locally via
  `ValidationUtils.is_valid_uuid` before the call).

## Postconditions on success

- Exactly one row persisted per org queried, keyed on `org_id`
  (`INSERT OR REPLACE` upsert).
- No Mist Cloud state has changed (read-only endpoint).
- No secrets logged; no PEM body logged.

## Postconditions on failure

- No partial row is written (DataExporter is only invoked when the
  flattened row list is non-empty and the response was 200).
- The exit code from `python MistHelper.py --menu 195` remains `0`
  (soft failure -- log and continue), consistent with other read-only
  export operations.
