# Contract: getOrgDeviceProfile

**Feature**: 604-mist-get-org-device-profile
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_deviceprofiles_deviceprofile_id.md`
**Tag**: `Orgs Device Profiles`

## HTTP Contract

| Item | Value |
|------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` |
| Authentication | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie) -- injected by `mistapi.APISession`. Never logged. |
| Request body | None. |
| Pagination | Not paginated (single object response). |
| Idempotent | Yes (safe GET). |
| Rate limit | Standard Mist 5000 calls / hour / token. |

### Path Parameters

| Name | Type | Required | Description | Validation |
|------|------|----------|-------------|------------|
| `org_id` | string (UUID) | Yes | Owning Mist organization. | Mist UUID regex (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`); MistHelper validates locally before the call. |
| `deviceprofile_id` | string (UUID) | Yes | Target device profile UUID. | Same Mist UUID regex. |

### Query Parameters

None.

### Request Headers

| Header | Set By | Value |
|--------|--------|-------|
| `Authorization` | mistapi | `Token <MIST_API_TOKEN>` |
| `Accept` | mistapi | `application/json` |
| `User-Agent` | mistapi | `mistapi/<sdk-version>` |

## Response Schema (200 OK)

The OpenAPI spec declares the response only as `{"type": "object"}`. The
runtime shape is the standard Mist device-profile envelope, identical to a
single element of the `listOrgDeviceProfiles` array. See `data-model.md` for
the full field table. Top-level keys observed in production:

```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "org_id": "abcd1234-abcd-1234-abcd-1234abcd5678",
  "name": "Lobby-AP-Profile",
  "type": "ap",
  "created_time": 1700000000.0,
  "modified_time": 1701234567.0,
  "for_site": true,
  "site_id": null,
  "ap_port_config": { "...": "..." },
  "radio_config":   { "...": "..." },
  "mesh":           { "...": "..." },
  "port_usages":    null,
  "networks":       null,
  "dhcpd_config":   null,
  "oob_ip_config":  { "...": "..." },
  "ntp_servers":    ["time.cloudflare.com"],
  "dns_servers":    ["1.1.1.1", "8.8.8.8"],
  "additional_config_cmds": []
}
```

Profile type drives which sub-objects are populated:

| `type` value | Populated sub-objects (typical) |
|--------------|---------------------------------|
| `ap` | `ap_port_config`, `radio_config`, `mesh` |
| `switch` | `port_usages`, `networks`, `dhcpd_config` |
| `gateway` | `networks`, `dhcpd_config`, `oob_ip_config` |

## Error Responses

| Status | Meaning | MistHelper Handling |
|--------|---------|---------------------|
| 400 | Bad Syntax | mistapi raises; menu method catches via outer `try`; `logging.warning("Bad request: %s", err)`; returns to menu. |
| 401 | Unauthorized | Token missing / invalid / expired. `logging.error("Auth failure -- check MIST_API_TOKEN in .env")`; returns to menu. Token value never logged. |
| 403 | Permission Denied | Token lacks scope for this org. `logging.warning("Token has no access to org %s", org_id)`; returns to menu. |
| 404 | Not Found | Org or device profile UUID does not exist. `logging.warning("Device profile %s not found in org %s", deviceprofile_id, org_id)`; returns to menu. Exits 0. |
| 429 | Too Many Requests | Per-token 5000/hour cap. The adaptive delay system (`delay_metrics.json` + `tuning_data.json`) records the event and backs off automatically; mistapi retries; no user action needed. |
| 5xx | Server error | mistapi raises; `logging.exception("Unexpected server error")` captures the full traceback; returns to menu. |

In every error case the menu method completes with no traceback printed to
stdout, no partial CSV / SQLite write, and exit code 0 -- consistent with
Principle III (Safety-First).

## mistapi Python Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import deviceprofiles

# self.apisession is created once at startup via mistapi.APISession() and
# auto-loads MIST_HOST + MIST_API_TOKEN from .env.
response = deviceprofiles.getOrgDeviceProfile(
    self.apisession,           # Authenticated session
    org_id,                    # First path param (validated UUID string)
    deviceprofile_id,          # Second path param (validated UUID string)
)

profile_dict = response.data or {}   # mistapi.APIResponse exposes .data
http_status  = response.status_code  # For optional fine-grained handling
```

### Argument summary

| Position | Name | Type | Notes |
|---------:|------|------|-------|
| 1 | `apisession` | `mistapi.APISession` | Constructed at MistHelper startup; never re-built per call. |
| 2 | `org_id` | `str` | Path parameter; UUID. |
| 3 | `deviceprofile_id` | `str` | Path parameter; UUID. |

### Return value

`mistapi.APIResponse` with attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `.data` | `dict` | Parsed JSON body -- the single device profile object. |
| `.status_code` | `int` | HTTP status (200 on success). |
| `.headers` | `dict` | Response headers (rarely needed). |
| `.url` | `str` | Resolved URL; never logged. |

### Verifying the SDK call path at task time

Before implementation, confirm the import path on the installed mistapi
version:

```powershell
python -c "from mistapi.api.v1.orgs import deviceprofiles; print(deviceprofiles.getOrgDeviceProfile)"
```

Expected output (mistapi 0.59+):

```text
<function getOrgDeviceProfile at 0x...>
```

If the import fails, upgrade with `pip install --upgrade mistapi` and re-run.
The enriched per-endpoint doc shows the module spelled `device_profiles`
(snake_case) -- that is a doc artifact; the runtime package is
`deviceprofiles` (no underscore), matching the URL slug.
