# Contract: countSiteNacClients

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Source doc**: `documentation/api/sites/GET_sites_site_id_nac_clients_count.md`

This is the binding HTTP + SDK contract MistHelper implements for menu 89. Any
deviation from this contract is a defect.

---

## HTTP Contract

| Field           | Value                                                |
|-----------------|------------------------------------------------------|
| Method          | `GET`                                                |
| URL template    | `https://{MIST_HOST}/api/v1/sites/{site_id}/nac_clients/count` |
| Authentication  | `Authorization: Token {MIST_API_TOKEN}` request header |
| Accept          | `application/json`                                   |
| Request body    | None                                                 |
| Idempotent      | Yes (safe to retry; read-only)                       |
| Pagination      | `limit` query parameter (default 100, max 1000)      |
| Rate limit      | 5000 calls/hour per token (Mist global)              |

### Required path parameters

| Name      | Type   | Description                                                       |
|-----------|--------|-------------------------------------------------------------------|
| site_id   | string | Mist Site UUID. Required. Must be a valid UUID v4 shape.          |

### Query parameters (all optional)

| Name                  | Type    | Default | Description                                                                                          |
|-----------------------|---------|---------|------------------------------------------------------------------------------------------------------|
| distinct              | string  |         | Field to group by. Common values: `type`, `auth_type`, `last_vlan_id`, `last_ssid`, `last_nacrule_id`, `mdm_compliance_status`, `mdm_provider`, `last_status`, `last_nas_vendor`, `idp_id`, `last_ap`, `mac`, `last_username`. |
| last_nacrule_id       | string  |         | Filter: NAC Policy Rule ID, if matched.                                                              |
| nacrule_matched       | boolean |         | Filter: only rows where a NAC rule matched.                                                          |
| auth_type             | string  |         | Filter: `eap-tls`, `eap-peap`, `eap-ttls`, `eap-teap`, `mab`, `psk`, `device-auth`.                  |
| last_vlan_id          | string  |         | Filter: VLAN ID.                                                                                     |
| last_nas_vendor       | string  |         | Filter: NAS device vendor.                                                                           |
| idp_id                | string  |         | Filter: SSO IdP ID.                                                                                  |
| last_ssid             | string  |         | Filter: SSID.                                                                                        |
| last_username         | string  |         | Filter: username presented by client.                                                                |
| timestamp             | number  |         | Filter: epoch seconds.                                                                               |
| last_ap               | string  |         | Filter: AP MAC the client last associated to.                                                        |
| mac                   | string  |         | Filter: client MAC.                                                                                  |
| last_status           | string  |         | Filter: `permitted`, `denied`, `session_ended`.                                                      |
| type                  | string  |         | Filter: `wireless`, `wired`.                                                                         |
| mdm_compliance_status | string  |         | Filter: `compliant`, `not compliant`.                                                                |
| mdm_provider          | string  |         | Filter: `intune`, `jamf`, etc.                                                                       |
| start                 | string  |         | Window start. Epoch seconds or relative (`-1d`, `-1w`).                                              |
| end                   | string  |         | Window end. Epoch seconds or relative (`now`, `-1h`).                                                |
| duration              | string  | `1d`    | Window duration (`1h`, `7d`, `2w`).                                                                  |
| limit                 | integer | `100`   | Max bucket rows returned.                                                                            |

MistHelper menu 89 only prompts for `site_id`, `distinct`, and `duration`. The other
sixteen filters are accepted by the SDK call but not exposed at the prompt -- see
`research.md` Task 1 for the rationale.

### Required request headers

| Header          | Value                                  |
|-----------------|----------------------------------------|
| Authorization   | `Token {MIST_API_TOKEN}`               |
| Accept          | `application/json`                     |
| User-Agent      | Set by `mistapi`; do not override.     |

---

## Response Contract (HTTP 200)

### Schema (verbatim from enriched doc)

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": { "type": "string" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": ["count"],
        "type": "object",
        "properties": {
          "count": { "type": "integer", "contentEncoding": "int32" }
        },
        "additionalProperties": { "type": "string" }
      }
    },
    "start": { "type": "integer", "contentEncoding": "int32" },
    "total": { "type": "integer", "contentEncoding": "int32" }
  }
}
```

### Example 200 body

```json
{
  "distinct": "auth_type",
  "start":    1719600000,
  "end":      1720204800,
  "limit":    100,
  "total":    1234,
  "results": [
    { "count": 900, "auth_type": "eap-tls" },
    { "count": 200, "auth_type": "mab" },
    { "count": 134, "auth_type": "psk" }
  ]
}
```

The `additionalProperties` mechanism means the key inside each `results[*]` object is
dynamic -- it matches the value of the top-level `distinct` field. The MistHelper
flattener (`_flatten_nac_count`) collapses this into a fixed `distinct_value` column
(see `data-model.md`).

---

## Error responses

| HTTP | Cause                                       | MistHelper handling                                                                                       |
|------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 400  | Bad syntax (invalid query param value)      | `logging.warning("400 bad request for countSiteNacClients: %s", err)`; return early, no file written.     |
| 401  | Invalid / expired `MIST_API_TOKEN`          | `logging.error("401 unauthorized -- check MIST_API_TOKEN in .env")`; sys.exit(1) -- token is global.      |
| 403  | Token valid but lacks read scope for site   | `logging.warning("403 forbidden for site %s -- token lacks scope", site_id)`; return early, exit 0.       |
| 404  | Site UUID does not exist                    | `logging.warning("404 not found for site %s", site_id)`; return early, exit 0 (per spec edge case).       |
| 429  | Rate limit exceeded (5000/hr per token)     | Adaptive delay (`delay_metrics.json`) + retry per Mist API doc; no manual intervention. After max retries, log `ERROR` and return early. |
| 5xx  | Mist Cloud transient failure                | mistapi's built-in retry; on exhaustion `logging.exception("Upstream Mist API failure")` and return early.|

All error paths return without raising past the menu boundary, so the main menu
loop stays alive and the user sees a clean prompt afterward.

---

## mistapi Python call signature

```python
from mistapi import APISession
from mistapi.api.v1.sites.nac_clients import count as nac_count

session = APISession(env_file=".env")          # Loads MIST_HOST + MIST_API_TOKEN
session.login()                                # No-op for token-based auth, but called for parity

response = nac_count.countSiteNacClients(
    mist_session=session,                      # APISession instance
    site_id="11111111-2222-3333-4444-555555555555",  # required, UUID
    distinct="auth_type",                      # optional, default "type" in MistHelper
    start=None,                                # optional, epoch seconds or relative string
    end=None,                                  # optional, epoch seconds or relative string
    duration="1d",                             # optional, default "1d"
    limit=100,                                 # optional, default 100
)

payload = response.data                        # dict matching the 200 schema above
status  = response.status_code                 # int -- MistHelper switches on this for error handling
```

The `mistapi` package handles:
- URL construction from `MIST_HOST` + path template
- Header injection (`Authorization`, `Accept`, `User-Agent`)
- Retry on transient failures
- 429 back-off coordination via MistHelper's adaptive delay metrics

MistHelper must NOT bypass `mistapi` by calling `requests.get(...)` directly --
that would violate Principle II of the Constitution.
