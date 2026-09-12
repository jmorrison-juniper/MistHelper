# Endpoint Contract: getAdminRegistrationInfo

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/admins/GET_register_recaptcha.md`

## HTTP contract

| Field           | Value                                                  |
|-----------------|--------------------------------------------------------|
| **Method**      | `GET`                                                  |
| **URL template**| `https://{MIST_HOST}/api/v1/register/recaptcha`        |
| **OperationId** | `getAdminRegistrationInfo`                             |
| **Tag**         | `Admins`                                               |
| **Auth**        | Public endpoint -- no `Authorization` header required. `mistapi.APISession` still passes the token if present; the API ignores it. |
| **Pagination**  | None.                                                  |
| **Rate limits** | Standard Mist limits (5000 calls / hour per token).    |

### Path parameters

_None._

### Query parameters

| Name               | Type    | Required | Default | Enum                | Description                                            |
|--------------------|---------|----------|---------|---------------------|--------------------------------------------------------|
| `recaptcha_flavor` | string  | No       | (none)  | `google`, `hcaptcha`| Optional override -- ask the API for a specific provider's sitekey. |

### Request headers

| Header           | Required | Notes                                                          |
|------------------|----------|----------------------------------------------------------------|
| `Accept`         | No       | `mistapi` defaults to `application/json`.                      |
| `Authorization`  | No       | Sent if `MIST_API_TOKEN` is set; ignored by this endpoint.     |

### Request body

None. `GET` request.

## Response

### 200 OK -- success

```json
{
  "flavor": "google",
  "required": true,
  "sitekey": "6Lc-aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
}
```

### Response schema

```jsonc
{
  "type": "object",
  "properties": {
    "flavor":   { "type": "string",  "description": "reCAPTCHA provider. Enum: google, hcaptcha." },
    "required": { "type": "boolean", "description": "Whether reCAPTCHA must be solved before registration is accepted." },
    "sitekey":  { "type": "string",  "description": "Public client-side key passed to the reCAPTCHA widget." }
  }
}
```

All three properties are returned on every successful call. The response is a single
object, not an array; the MistHelper menu method wraps it in a one-element list before
handing it to `DataExporter`.

## Error responses

| Status | Mist meaning                                            | MistHelper handling                                                                              |
|--------|---------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (malformed `recaptcha_flavor`)               | `WARNING` log line; method returns without writing. The user prompt already validates the enum, so a 400 is unexpected. |
| 401    | Unauthorized -- token rejected                          | `WARNING` log. Endpoint is public, so a 401 usually means the token itself is malformed; surfaces the message and exits 0. |
| 403    | Permission Denied                                       | `WARNING` log. Same handling as 401 -- not fatal because no data was modified.                   |
| 404    | Endpoint or resource not found                          | `WARNING` log; method returns. Indicates the Mist region URL is wrong or the endpoint was renamed -- check `MIST_HOST`. |
| 429    | Too Many Requests (5000 / hour threshold hit)           | Caught by the existing `mistapi` retry / `delay_metrics.json` adaptive back-off. The menu method does not see 429 directly; the SDK either succeeds after back-off or raises after the configured retry budget. |
| 5xx    | Upstream error                                          | `logging.exception(...)` with full traceback; method returns non-zero from the menu dispatcher. |

In every error case, no partial data is written. The SQLite table and CSV file are left
untouched. The existing `delay_metrics.json` and `tuning_data.json` files continue to
absorb timing data even on failure so the adaptive limiter can learn.

## mistapi Python call signature

```python
import mistapi
from mistapi.api.v1.admins import admins as admins_module

# self.api_session is an authenticated mistapi.APISession instance held by OrgExportUtils.
response = admins_module.getAdminRegistrationInfo(
    self.api_session,                       # First positional -- the session object.
    recaptcha_flavor=flavor or None,        # Optional query arg; omit when blank.
)

# Standard mistapi response wrapper exposes .data for the parsed JSON body.
payload = response.data                     # dict with keys: flavor, required, sitekey.
```

**Function module path**: `mistapi.api.v1.admins.admins.getAdminRegistrationInfo`
(grouped by OpenAPI tag, not URL path -- see research.md Task 1).

**Return value**: `mistapi`'s response wrapper object. The `.data` attribute holds the
parsed JSON dict. The `.status_code` attribute holds the HTTP status. The
`.proxy_error` attribute is set on transport-level failures.

## Contract test (suggested)

```python
# tests/e2e/test_menu_59_admin_registration_info.py (proposed location).
def test_menu_59_writes_one_row(tmp_path, mock_mistapi_response):
    mock_mistapi_response(
        "GET", "/api/v1/register/recaptcha",
        json={"flavor": "google", "required": True, "sitekey": "test_sitekey_abc"},
    )
    exit_code = run_menu(59, env={"MIST_HOST": "api.mist.com"})
    assert exit_code == 0
    rows = read_csv(tmp_path / "data" / "admin_registration_info.csv")
    assert len(rows) == 1
    assert rows[0]["sitekey"] == "test_sitekey_abc"
    assert rows[0]["flavor"] == "google"
```

A second test runs the menu twice and asserts the SQLite row count stays at 1 to verify
the `natural_pk` upsert works.
