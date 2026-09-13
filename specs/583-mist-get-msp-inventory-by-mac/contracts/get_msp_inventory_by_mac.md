# Contract: getMspInventoryByMac

**Feature**: 583-mist-get-msp-inventory-by-mac
**Authoritative source**: `documentation/api/msps/GET_msps_msp_id_inventory_device_mac.md`

This document is the implementation contract for the new MistHelper menu item. The
upstream Mist OpenAPI spec is the ultimate source of truth; this file captures the
shape the implementer must code against today.

---

## 1. HTTP Contract

| Field            | Value                                               |
|------------------|-----------------------------------------------------|
| Method           | `GET`                                               |
| URL template     | `https://{MIST_HOST}/api/v1/msps/{msp_id}/inventory/{device_mac}` |
| Host (`{MIST_HOST}`) | e.g. `api.mist.com`, `api.eu.mist.com` -- from `.env` |
| Auth header      | `Authorization: Token {MIST_API_TOKEN}` (from `.env`) |
| Content-Type req | none (no request body)                              |
| Accept           | `application/json` (SDK default)                    |
| Request body     | none                                                |
| Idempotent       | yes (safe to retry)                                 |
| Cacheable        | yes (no `Cache-Control: no-store` directive)        |

### Path Parameters (both REQUIRED)

| Name         | Type   | Format                                  | Validation in MistHelper        |
|--------------|--------|-----------------------------------------|---------------------------------|
| `msp_id`     | string | UUID (8-4-4-4-12 hex)                   | `UUID_REGEX.match()` before call |
| `device_mac` | string | 12 hex digits, colon-separated lowercase (`aa:bb:cc:dd:ee:ff`) | Normalize (strip non-hex, lowercase, re-insert colons every 2 chars), then `MAC_REGEX.match()` |

### Query Parameters

None.

### Request Headers Sent by `mistapi` SDK

```
Authorization: Token <redacted>
User-Agent: mistapi/0.59+ python/3.13
Accept: application/json
```

No additional headers are required by this endpoint.

---

## 2. Successful Response (HTTP 200)

### Schema

```json
{
  "type": "object",
  "properties": {
    "for_site": { "type": "boolean", "readOnly": true },
    "mac":      { "type": "string",  "readOnly": true },
    "model":    { "type": "string",  "readOnly": true },
    "org_id":   { "type": "string",  "contentEncoding": "uuid", "readOnly": true },
    "serial":   { "type": "string",  "readOnly": true },
    "site_id":  { "type": "string",  "contentEncoding": "uuid", "readOnly": true },
    "type":     { "type": "string",  "readOnly": true }
  },
  "required": ["mac", "model", "org_id", "serial", "site_id", "type"]
}
```

### Example Payload

```json
{
  "for_site": true,
  "mac":      "aa:bb:cc:dd:ee:ff",
  "model":    "AP43",
  "org_id":   "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "serial":   "ABC123XYZ",
  "site_id":  "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "type":     "ap"
}
```

### Pagination

None. The response is always a single object describing exactly one device.

---

## 3. Error Responses

| Status | Mist meaning                                                    | MistHelper behavior |
|--------|-----------------------------------------------------------------|---------------------|
| 400    | Bad Syntax (malformed MAC or msp_id reached the API)            | `logging.warning("Mist API 400 -- check MAC / MSP ID format: %s", error_body)`. Return `None`. Exit 0. |
| 401    | Unauthorized (bad / missing API token)                          | `logging.error("Mist API 401 -- check MIST_API_TOKEN in .env")`. Return `None`. Exit 0. Do NOT log the token. |
| 403    | Permission Denied (token lacks MSP-scope read access)           | `logging.error("Mist API 403 -- API token lacks MSP read permission for %s", msp_id)`. Return `None`. Exit 0. |
| 404    | Not found (MAC not claimed in this MSP, or MSP does not exist)  | `logging.warning("MAC %s not found in MSP %s inventory (HTTP 404)", mac_normalized, msp_id)`. Return `None`. Exit 0. This is the common "no match" path, NOT an error condition. |
| 429    | Rate limit (5000 calls/hour exceeded)                           | Adaptive delay system in `delay_metrics.json` handles back-off via the SDK retry layer. `logging.warning("Mist API 429 -- adaptive delay engaged")`. Eventually returns the eventual 200/404 response. |
| 5xx    | Mist Cloud server error                                         | `logging.exception(...)`. Return `None`. Exit 0. The user can re-run. |

In all cases the MistHelper menu method returns cleanly (exit code 0) and never
raises a traceback to the user. This matches Constitution Principle III (Safety-First).

---

## 4. mistapi SDK Call Signature

```python
import mistapi
from mistapi.api.v1.msps.inventory import getMspInventoryByMac

response = getMspInventoryByMac(
    mist_session=self.apisession,    # mistapi.APISession instance, holds host + token
    msp_id="00000000-0000-0000-0000-000000000000",   # UUID-validated path param
    device_mac="aa:bb:cc:dd:ee:ff",                  # normalized MAC path param
)

# response is a mistapi.APIResponse object:
#   response.status_code -> int (200 / 4xx / 5xx)
#   response.data        -> dict (matches the 200 schema above; empty dict on 404)
#   response.headers     -> dict of HTTP response headers
#   response.url         -> full URL (DO NOT log -- contains path params)
```

The SDK function name, parameter order, and module path are taken from
`mistapi.api.v1.msps.inventory` per the enriched endpoint documentation. If a future
version of `mistapi` renames the function or reorders parameters, this contract MUST
be regenerated from the SDK introspection before code is changed.

### Minimum Viable Call (Implementer Reference)

```python
# Establish session once at MistHelper startup -- already done by the main loop
apisession = mistapi.APISession(env_file=".env")
apisession.login()                                   # token from MIST_API_TOKEN

# Per-invocation call:
resp = mistapi.api.v1.msps.inventory.getMspInventoryByMac(
    apisession, msp_id, mac_normalized)              # ordered positional args

if resp.status_code == 200 and resp.data:
    row = build_inventory_row(msp_id, resp.data)     # synthesize msp_id into the row
    DataExporter.write_with_format_selection(
        [row], "msp_inventory_by_mac",
        api_function_name="getMspInventoryByMac")    # PK strategy lookup uses this
elif resp.status_code == 404:
    logging.warning("MAC %s not found in MSP %s inventory (HTTP 404)",
                    mac_normalized, msp_id)
else:
    logging.error("Mist API returned %d for MSP %s MAC %s",
                  resp.status_code, msp_id, mac_normalized)
```

---

## 5. Conformance Checklist

- [ ] MAC normalized to lowercase colon-separated before SDK call.
- [ ] `msp_id` UUID validation runs BEFORE the SDK call.
- [ ] All four error classes (400/401/403/404) handled without traceback.
- [ ] 429 path delegates to the existing adaptive delay system; no custom sleep added.
- [ ] `ENDPOINT_PRIMARY_KEY_STRATEGIES['getMspInventoryByMac']` registered with
      composite PK `(msp_id, mac)`.
- [ ] `DataExporter.write_with_format_selection(...)` is the sole output path; no
      direct CSV or sqlite3 calls.
- [ ] `safe_input()` (not bare `input()`) collects both prompts with explicit
      `context=` strings.
- [ ] No API token, no `Authorization` header, no full URL, no `response.url` is
      logged at any level.
