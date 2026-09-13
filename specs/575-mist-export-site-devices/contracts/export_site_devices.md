# Endpoint Contract: exportSiteDevices

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_devices_export.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                       |
|-----------------|-------------------------------------------------------------|
| **Method**      | `GET`                                                       |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/devices/export` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Devices`                                             |
| **operationId** | `exportSiteDevices`                                         |

### Path Parameters

| Name      | Type           | Required | Description                                          |
|-----------|----------------|----------|------------------------------------------------------|
| `site_id` | string (UUID)  | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. The endpoint accepts no query parameters.

### Request Headers

| Header           | Value                                  | Notes |
|------------------|----------------------------------------|-------|
| `Authorization`  | `Token <api_token>`                    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`                     | Default for mistapi SDK. The wrapper response is JSON; the embedded payload is base64-encoded CSV text. |
| `User-Agent`     | `mistapi/<version>`                    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

The response is a single JSON wrapper around a base64-encoded CSV file. Per
the OpenAPI schema in `documentation/api/sites/GET_sites_site_id_devices_export.md`:

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
}
```

In practice, `response.data` from the mistapi SDK is the base64 string itself
(the SDK unwraps the schema envelope). MistHelper handles both shapes
defensively: if `response.data` is a `dict`, it pulls the scalar payload from
the documented wrapper; otherwise it treats `response.data` as the base64
string directly.

The decoded CSV has the following minimum guaranteed columns (Mist may emit
additional columns; `DataExporter` widens the SQLite table on first write to
absorb them):

| Column     | Type   | Description |
|------------|--------|-------------|
| `mac`      | string | Device factory MAC address (12 lowercase hex chars, no separators). |
| `name`     | string | Operator-assigned device name (often hostname). May be empty. |
| `serial`   | string | Device serial number. Stable across reboots. |
| `model`    | string | Device model code (e.g., `AP43`, `EX4400-48P`, `SRX320`). |
| `type`     | string | Device class enum: `ap`, `switch`, `gateway`. |
| `hw_rev`   | string | Hardware revision string. May be empty for some models. |
| `version`  | string | Firmware version currently reported by the device. |
| `status`   | string | Connection status: `connected`, `disconnected`, `unassigned`. |

Example decoded CSV (after base64 decode + UTF-8 decode):

```csv
mac,name,serial,model,type,hw_rev,version,status
5c5b350abc01,branch-ap-01,XYZ1234567,AP43,ap,A04,0.14.29498,connected
5c5b350abc02,branch-ap-02,XYZ1234568,AP43,ap,A04,0.14.29498,disconnected
8896adef0001,branch-switch-01,EX1234567,EX4400-48P,switch,REV4,23.4R2-S2.5,connected
```

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check site_id format"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No device export available for site %s", site_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The base64 payload and
its decoded CSV content are never logged -- only the byte length and the
resulting row count appear in the log stream.

## mistapi Python SDK Call Signature

```python
import os
import base64
import csv
import io
import binascii
from datetime import datetime, timezone

import mistapi
from mistapi.api.v1.sites.devices import export as site_devices_export

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = site_devices_export.exportSiteDevices(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the wrapper payload:
payload = response.data           # base64 string (or dict wrapper -- handle both)
http_status = response.status_code

# Decode + parse into device rows:
if isinstance(payload, dict):
    payload = payload.get("data") or payload.get("file") or ""
decoded_bytes = base64.b64decode(payload, validate=True)
decoded_text = decoded_bytes.decode("utf-8", errors="replace")
device_rows = list(csv.DictReader(io.StringIO(decoded_text)))
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/sites/{site_id}/devices/export` ->
  `mistapi.api.v1.sites.devices.export`). The enriched per-endpoint doc lists
  the SDK as `mistapi.api.v1.sites.devices.exportSiteDevices()`. Final
  verification happens at implementation via
  `python -c "from mistapi.api.v1.sites.devices import export; help(export)"`.
- `response.data` may be `None` (rare -- empty body) or an empty string when
  the site has zero devices. MistHelper normalizes both to "no rows parsed"
  and exits cleanly without writing.
- `base64.b64decode(..., validate=True)` raises `binascii.Error` on a
  malformed payload. MistHelper catches this, logs `ERROR` with a full
  traceback via `logging.exception`, and returns an empty row list so the
  caller can exit cleanly.
- The decoded CSV is treated as UTF-8 (`errors="replace"` to avoid raising on
  the rare exotic byte). Replacement characters are visible in any downstream
  field that contained them.

## Pagination

Not paginated. The endpoint returns a single CSV file per call. No
`limit`/`page` parameters apply. The CSV file size is bounded by the number
of devices in the site (typical sites: <= a few thousand rows, decoded size
<= a few hundred KB).

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
