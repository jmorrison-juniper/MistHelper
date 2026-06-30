# Endpoint Contract: getOrgMxEdgeUpgradeInfo

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_mxedges_versions.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                  |
|-----------------|------------------------------------------------------------------------|
| **Method**      | `GET`                                                                  |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/mxedges/versions`            |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs MxEdges`                                                         |
| **operationId** | `getOrgMxEdgeUpgradeInfo`                                              |

### Path Parameters

| Name     | Type          | Required | Description                                                                                       |
|----------|---------------|----------|---------------------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the SDK call. |

### Query Parameters

| Name      | Type   | Required | Default      | Enum                       | Description                                                                                                 |
|-----------|--------|----------|--------------|----------------------------|-------------------------------------------------------------------------------------------------------------|
| `channel` | string | No       | `stable`     | `stable`, `beta`, `alpha`  | Upgrade channel to follow. MistHelper prompts the user with default `stable`; values normalized to lowercase. |
| `distro`  | string | No       | (absent)     | (free-form)                | Distro code name (e.g. `bullseye`, `buster`). MistHelper omits the parameter entirely when the user leaves the prompt empty. |

### Request Headers

| Header           | Value                                  | Notes                                                                  |
|------------------|----------------------------------------|------------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`                    | Injected by `mistapi.APISession` from `.env`. Never logged.            |
| `Accept`         | `application/json`                     | Default for the mistapi SDK.                                           |
| `User-Agent`     | `mistapi/<version>`                    | Set by SDK.                                                            |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

JSON array (`uniqueItems: true`) of upgrade-info objects. Per the enriched
OpenAPI doc, the schema's `required` set is `{package, version}`; `distro` and
`default` are optional.

```json
[
  {
    "default": true,
    "distro": "bullseye",
    "package": "mxagent",
    "version": "2.4.100"
  },
  {
    "distro": "bullseye",
    "package": "tunterm",
    "version": "1.0.0"
  }
]
```

| Field     | Type    | Required | Description                                                                                    |
|-----------|---------|----------|------------------------------------------------------------------------------------------------|
| `package` | string  | Yes      | Debian package name (e.g. `mxagent`, `tunterm`).                                               |
| `version` | string  | Yes      | Semantic version string (e.g. `2.4.100`).                                                      |
| `distro`  | string  | No       | Distro code name (e.g. `bullseye`, `buster`). Omitted when the package is distro-agnostic.     |
| `default` | boolean | No       | `true` when this package+version is the current default for the requested channel and distro. |

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling                                                                                              |
|--------|-------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check channel/distro values"). No traceback. Return early with zero rows.   |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early.                            |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early.                             |
| 404    | Not found. Endpoint or resource does not exist                    | Log `WARNING` ("No Mist Edge upgrade info for org %s", org_id). Treat as empty result and write zero rows.       |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)      | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.mxedges import versions as mxedges_versions_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# No filters (Mist defaults to channel=stable, all distros):
response = mxedges_versions_module.getOrgMxEdgeUpgradeInfo(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Channel-only filter:
response = mxedges_versions_module.getOrgMxEdgeUpgradeInfo(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    channel="beta",
)

# Channel + distro filters:
response = mxedges_versions_module.getOrgMxEdgeUpgradeInfo(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    channel="stable",
    distro="bullseye",
)

# Access the parsed body:
rows = response.data            # list[dict] matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/mxedges/versions` ->
  `mistapi.api.v1.orgs.mxedges.versions`). The enriched per-endpoint doc lists
  the SDK as `mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgradeInfo()` (parent
  module). Both typically work because mistapi re-exports endpoint functions
  at the parent package level; the URL-mirroring path is the canonical one and
  is the form the spec.md uses. Final verification happens at implementation
  via
  `python -c "from mistapi.api.v1.orgs.mxedges import versions; help(versions)"`.
- `response.data` is `None` only when the HTTP response had no body (rare for
  this endpoint). MistHelper normalizes this to `[]` before flattening.
- The `channel` parameter is passed as a Python `str` and serialized into the
  query string by the SDK. The `distro` parameter is passed as `None` (which
  the SDK omits from the URL) when the user supplied an empty filter, or as a
  `str` otherwise.

## Pagination

Not paginated. The endpoint returns a single JSON array per call. No
`limit` / `page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning is required for this contract -- the response is
small and the call is light.
