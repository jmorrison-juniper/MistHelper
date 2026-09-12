# Endpoint Contract: getOrgSsrUpgrade

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/utilities/GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                        |
|-----------------|------------------------------------------------------------------------------|
| **Method**      | `GET`                                                                        |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`   |
| **Auth**        | `Authorization: Token {api_token}` header (injected automatically by `mistapi.APISession`) |
| **Tag**         | `Utilities Upgrade`                                                          |
| **operationId** | `getOrgSsrUpgrade`                                                           |

**Gotcha (critical)**: Despite the `/cancel` URL suffix, this is a GET that
returns upgrade status. The actual cancel operation is `POST` on the same URL
and lives in a separate OpenAPI file (`POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md`),
covered by a future spec if needed. This spec is strictly read-only.

### Path Parameters

| Name         | Type          | Required | Description                                                                    |
|--------------|---------------|----------|--------------------------------------------------------------------------------|
| `org_id`     | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()`.  |
| `upgrade_id` | string (UUID) | Yes      | SSR upgrade job UUID. Validated client-side by MistHelper via `is_valid_uuid()`. |

### Query Parameters

None.

### Request Headers

| Header          | Value                | Notes                                                        |
|-----------------|----------------------|--------------------------------------------------------------|
| `Authorization` | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`   | Default for the mistapi SDK.                                 |
| `User-Agent`    | `mistapi/<version>`  | Set by the SDK.                                              |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "channel": "stable",
  "device_type": "ssr",
  "status": "upgrading",
  "targets": {
    "failed":    ["aa:bb:cc:dd:ee:01"],
    "queued":    ["aa:bb:cc:dd:ee:02", "aa:bb:cc:dd:ee:03"],
    "success":   ["aa:bb:cc:dd:ee:04", "aa:bb:cc:dd:ee:05"],
    "upgrading": ["aa:bb:cc:dd:ee:06"]
  },
  "versions": {
    "aa:bb:cc:dd:ee:01": "6.1.4-1",
    "aa:bb:cc:dd:ee:02": "6.1.4-1",
    "aa:bb:cc:dd:ee:03": "6.1.4-1",
    "aa:bb:cc:dd:ee:04": "6.1.4-1",
    "aa:bb:cc:dd:ee:05": "6.1.4-1",
    "aa:bb:cc:dd:ee:06": "6.1.4-1"
  }
}
```

| Field                 | Type            | Required | Description |
|-----------------------|-----------------|----------|-------------|
| `id`                  | string (UUID)   | Yes      | Unique identifier of the upgrade job. `readOnly` in the schema. Used as MistHelper's natural primary key on the summary table. |
| `channel`             | string (min 1)  | Yes      | SSR release channel (e.g., `alpha`, `beta`, `stable`, build-specific string). |
| `device_type`         | string          | No       | Target device type identifier (SSR family). |
| `status`              | string (min 1)  | Yes      | Job status. Observed values: `created`, `queued`, `upgrading`, `done`, `failed`, `cancelled`. |
| `targets`             | object          | Yes      | Per-bucket arrays of unique device MAC strings. See sub-schema below. |
| `targets.failed`      | array of string | Yes      | Devices that failed to upgrade. `uniqueItems: true`. |
| `targets.queued`      | array of string | Yes      | Devices queued for upgrade. `uniqueItems: true`. |
| `targets.success`     | array of string | Yes      | Devices successfully upgraded. `uniqueItems: true`. |
| `targets.upgrading`   | array of string | Yes      | Devices currently upgrading. `uniqueItems: true`. |
| `versions`            | object          | Yes      | Free-form map of target -> intended version string. MistHelper stores the raw JSON in `versions_json` on the summary table and best-effort joins into per-target rows. |

### Error Responses

| Status | Mist Description                                                          | MistHelper Handling |
|--------|---------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                | Log `WARNING` ("Mist returned 400 -- check org_id and upgrade_id format"); no traceback; return early. In practice caught by `is_valid_uuid()` before the call. |
| 401    | Unauthorized                                                              | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                         | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. The API endpoint doesn't exist or resource doesn't exist       | Log `WARNING` ("No SSR upgrade %s for org %s", upgrade_id, org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests. The API Token used for the request reached the 5000 API Calls per hour threshold | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses surface as ASCII log lines. The API token is never
included in any log message, even at `DEBUG`. Full request URLs are not
logged above `DEBUG` because the URL contains the `upgrade_id` UUID.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.ssr.upgrade import cancel as ssr_upgrade_status_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Fetch a single SSR upgrade job's status (GET despite /cancel URL suffix):
response = ssr_upgrade_status_module.getOrgSsrUpgrade(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    upgrade_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body:
body = response.data              # dict matching the 200 OK schema above
http_status = response.status_code  # int, e.g. 200 / 404 / 429
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` ->
  `mistapi.api.v1.orgs.ssr.upgrade.cancel`). The enriched per-endpoint doc
  suggests `mistapi.api.v1.utilities.upgrade.getOrgSsrUpgrade()` (tag-based
  hint), but MistHelper's existing SSR caller
  (`FirmwareManager._fetch_ssr_upgrades_payload` at MistHelper.py line
  19106) confirms the URL-based path is canonical -- it calls
  `mistapi.api.v1.orgs.ssr.listOrgSsrUpgrades`. Final verification runs at
  implementation time via
  `python -c "from mistapi.api.v1.orgs.ssr.upgrade import cancel; help(cancel)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- The `targets` object is documented as `required` with all four bucket
  arrays required, but MistHelper still defensively defaults each missing
  key to `[]` before length calculations so a partial response cannot raise.
- No query parameters; no pagination knobs. The endpoint returns exactly one
  JSON object per call.

## Pagination

Not paginated. The endpoint returns a single JSON object describing one
upgrade job. No `limit` / `page` / cursor parameters apply.

## Rate Limiting

Standard Mist API rate limit: **5000 calls per token per hour**. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning across runs) governs back-off automatically. No
endpoint-specific tuning is required for this contract. Under `--fast`
(`FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8`), retries cap is respected and
concurrency is raised.
