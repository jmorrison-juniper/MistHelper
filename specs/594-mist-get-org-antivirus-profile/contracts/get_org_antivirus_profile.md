# Contract: getOrgAntivirusProfile

**Branch**: `594-mist-get-org-antivirus-profile` | **Date**: 2026-06-29
**Plan**: [../plan.md](../plan.md) |
**Data model**: [../data-model.md](../data-model.md) |
**Source enriched doc**: `documentation/api/orgs/GET_orgs_org_id_avprofiles_avprofile_id.md`

This contract is the binding HTTP + SDK interface for menu 96. Any change
to the upstream Mist API that breaks this contract requires a new spec.

---

## HTTP Contract

| Field                | Value                                                       |
|----------------------|-------------------------------------------------------------|
| **Method**           | `GET`                                                       |
| **URL template**     | `https://{MIST_HOST}/api/v1/orgs/{org_id}/avprofiles/{avprofile_id}` |
| **Required headers** | `Authorization: Token {MIST_API_TOKEN}` (added automatically by `mistapi.APISession`); `Content-Type: application/json` (request body is empty -- header technically optional). |
| **Path parameters**  | `org_id` (string, UUID, required); `avprofile_id` (string, UUID, required). |
| **Query parameters** | _None._                                                     |
| **Request body**     | _None._                                                     |
| **Pagination**       | _None._ Endpoint returns a single object.                   |
| **Idempotent**       | Yes. Repeated reads have no side effect on the server.      |

### Authentication

- Token-based via the `Authorization: Token <token>` header. MistHelper
  loads the token from `MIST_API_TOKEN` in `.env` at startup and binds it
  to the long-lived `mistapi.APISession` -- never logged, never echoed.
- Alternatively, `X-CSRFToken` cookie is accepted by Mist Cloud (used by
  the web UI); MistHelper does not use the cookie path.

### Concrete Example URL

```
GET https://api.mist.com/api/v1/orgs/a97c1b22-a4e9-411e-9bfd-d8695a0f9e61/avprofiles/53f10664-3ce8-4c27-b382-0ef66432349f
Authorization: Token <redacted>
```

---

## Response: 200 OK

Single JSON object. Schema (from
`documentation/api/orgs/GET_orgs_org_id_avprofiles_avprofile_id.md`):

| Field             | JSON Type | Required | Constraints / Enum                                                |
|-------------------|-----------|----------|-------------------------------------------------------------------|
| `id`              | string    | Yes      | UUID. Read-only. Stable per profile.                              |
| `org_id`          | string    | No (returned) | UUID. Read-only.                                              |
| `site_id`         | string    | No       | UUID. Present when profile is site-scoped.                        |
| `name`            | string    | Yes      | Operator-supplied name.                                           |
| `fallback_action` | string    | No       | Enum: `block`, `log-and-permit`, `permit`.                        |
| `max_filesize`    | integer   | No       | KB. Range 20 <= n <= 40000. Default 10000.                         |
| `mime_whitelist`  | array     | No       | Unique-item array of strings. May be empty / absent.              |
| `url_whitelist`   | array     | No       | Unique-item array of strings. May be empty / absent.              |
| `protocols`       | array     | No       | At least one of `ftp`, `http`, `imap`, `pop3`, `smtp`. (`minItems: 1` when present.) |
| `created_time`    | number    | No       | Epoch seconds. Read-only.                                         |
| `modified_time`   | number    | No       | Epoch seconds. Read-only.                                         |

### Concrete Example Response

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name": "default-avprofile",
  "fallback_action": "log-and-permit",
  "max_filesize": 10000,
  "mime_whitelist": [],
  "url_whitelist": ["trusted.example.com"],
  "protocols": ["http", "smtp"],
  "created_time": 1700000000.123,
  "modified_time": 1700050000.987
}
```

---

## Error Responses

MistHelper handles every documented error class without surfacing a
traceback to the operator. Each case logs a single ASCII line and exits
the menu method with return value `None`.

| Status | Meaning                                                       | MistHelper Response                                                                                       |
|--------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (malformed UUID, etc.)                             | `WARNING Bad request for avprofile <id> -- check UUID format`. Pre-call UUID validation makes this rare. |
| 401    | Unauthorized (token missing / wrong / expired)                | `ERROR Unauthorized -- check MIST_API_TOKEN in .env`. Method returns; no retry.                          |
| 403    | Permission Denied (token lacks org/profile read scope)        | `ERROR Permission denied -- operator role cannot read AV profiles in org <org_id>`. Method returns.       |
| 404    | Not Found (UUID does not exist in this org)                   | `WARNING Avprofile <avprofile_id> not found in org <org_id>`. Method returns 0; the run is not a failure.  |
| 429    | Too Many Requests (5000/hour threshold)                       | Adaptive delay layer in `delay_metrics.json` catches this, sleeps per current back-off, retries up to the configured cap. If retries exhaust: `WARNING Rate limit persists -- giving up on avprofile <id>`. |
| 5xx    | Server-side outage / partial failure                          | `ERROR Mist API server error <code> -- transient, retry later`. Method returns.                           |

For all non-2xx paths the `.env` token is never echoed in the log line.
Full HTTP details are visible at `DEBUG` level when
`MISTHELPER_LOG_LEVEL=DEBUG`.

---

## mistapi SDK Call (Python)

The single permitted Python invocation:

```python
import mistapi
from mistapi.api.v1.orgs import avprofiles as _avprofiles_api  # SDK module alias

# `self.mist_session` is the long-lived mistapi.APISession created at
# MistHelper startup from MIST_HOST + MIST_API_TOKEN in .env.

response = _avprofiles_api.getOrgAntivirusProfile(
    self.mist_session,    # APISession; carries token, host, retry policy
    org_id,               # str, UUID, pre-validated by MistHelper
    avprofile_id,         # str, UUID, pre-validated by MistHelper
)
# response is mistapi.APIResponse; .data holds the decoded JSON dict.
profile_record = response.data or {}
```

### Function Signature (canonical reference)

```
getOrgAntivirusProfile(
    mist_session: mistapi.APISession,
    org_id: str,
    avprofile_id: str,
) -> mistapi.APIResponse
```

Notes:
- `mistapi` 0.59+ is the minimum tested version. Older versions may
  expose this under `mistapi.api.v1.orgs.antivirus_profiles` (slugged
  module name); MistHelper pins to the `avprofiles` slug per the OpenAPI
  source path. If `pip` installs an older mistapi that lacks the module,
  the deployment pipeline fails at `py_compile` -- caught BEFORE the
  container is built.
- The SDK call does **not** accept any query parameters for this
  endpoint; the function signature is fixed at the two path parameters.

---

## Contract Test Hooks (for `/speckit.tasks` Phase 2)

| Test                                         | Expected Result                                                       |
|----------------------------------------------|-----------------------------------------------------------------------|
| Valid org + valid avprofile                  | Single dict returned with at minimum `id` and `name`.                 |
| Valid org + bogus avprofile UUID             | 404; MistHelper logs `WARNING`, returns; no SQLite row written.       |
| Bogus org UUID                               | 404; MistHelper logs `WARNING`, returns.                              |
| Missing token in `.env`                      | mistapi raises auth error before HTTP; MistHelper logs `ERROR`.       |
| Repeated successful runs                     | SQLite row count for the profile id stays at exactly 1 (upsert proof).|
| `safe_input` EOF mid-prompt                  | Process exits 0; no traceback, no partial file write.                 |
